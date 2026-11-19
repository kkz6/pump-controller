"""Measure service USB trace centerlines between actual KiCad pad landings."""
from collections import defaultdict
from heapq import heappop, heappush
from itertools import count
import math
import pcbnew as k


def walk(graph, start, targets):
    serial = count()
    queue = [(0.,0,next(serial),start)]
    best = {start:(0.,0)}
    came = {}
    while queue:
        length, vias, _, node = heappop(queue)
        if best[node] != (length,vias):
            continue
        if node in targets:
            path, nodes = [], {node}
            while node != start:
                node, label = came[node]
                path.append(label)
                nodes.add(node)
            return length, vias, list(reversed(path)), nodes
        for other, distance, nvias, label in graph[node]:
            new = (length+distance,vias+nvias)
            if other not in best or new<best[other]:
                best[other] = new
                came[other] = (node,label)
                heappush(queue, (*new,next(serial),other))
    raise ValueError(f"No routed copper from {start} to requested pad(s)")


def network(board, net):
    graph = defaultdict(list)
    vertices = defaultdict(set)
    radius = defaultdict(int)
    segments, vias, pads = [], [], []
    def edge(a,b,length,via,label):
        graph[a].append((b,length,via,label))
        back = (label[0],label[1],label[3],label[2]) if label[0] in ("trace","land","overlap") else label
        graph[b].append((a,length,via,back))
    for track in board.GetTracks():
        if track.GetNetname()!=net:
            continue
        if isinstance(track,k.PCB_VIA):
            vias.append(track)
            continue
        if track.GetClass()!="PCB_TRACK":
            raise ValueError("USB measurement requires explicit arc-length handling for curved traces")
        layer = track.GetLayer()
        a, b = tuple(track.GetStart()), tuple(track.GetEnd())
        vertices[layer].update((a,b))
        halfwidth=track.GetWidth()/2
        for xy in (a,b):
            radius[layer,xy]=max(radius[layer,xy],halfwidth)
        segments.append((a,b,layer,halfwidth))
    for via in vias:
        xy = tuple(via.GetPosition())
        landings = [(layer,xy) for layer in vertices if via.IsOnLayer(layer)]
        for layer,_ in landings:
            vertices[layer].add(xy)
            radius[layer,xy]=max(radius[layer,xy],via.GetWidth(layer)/2)
        for i,first in enumerate(landings):
            for second in landings[i+1:]:
                edge(first,second,0.,1,("via",xy))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname()!=net:
                continue
            name = fp.GetReference()+"."+pad.GetNumber()
            xy = tuple(pad.GetPosition())
            for layer in vertices:
                if pad.IsOnLayer(layer):
                    vertices[layer].add(xy)
                    pads.append((name,pad,layer,xy))
    for a,b,layer,halfwidth in segments:
        dx,dy=b[0]-a[0],b[1]-a[1]
        sq=dx*dx+dy*dy
        if not sq:
            continue
        # Pads and tracks can be conductive when their centre points differ.
        # Include the closest point along the centerline whenever the actual
        # same-layer endpoint/via copper disk intersects this track capsule.
        pts = set()
        for pt in vertices[layer]:
            x,y=pt[0]-a[0],pt[1]-a[1]
            t=max(0.,min(1.,(x*dx+y*dy)/sq))
            intercept = (round(a[0]+t*dx),round(a[1]+t*dy))
            offset = math.dist(pt,intercept)
            if offset <= halfwidth+radius[layer,pt]:
                pts.add((t,intercept))
                if pt != intercept:
                    edge((layer,pt),(layer,intercept),offset/1e6,0,("overlap",layer,pt,intercept))
        pts=sorted(pts)
        for (_,left),(_,right) in zip(pts,pts[1:]):
            edge((layer,left),(layer,right),math.dist(left,right)/1e6,0,("trace",layer,left,right))
    for name,pad,layer,xy in pads:
        copper = pad.GetEffectiveShape(layer)
        lands = [pt for pt in vertices[layer] if copper.Collide(k.VECTOR2I(*pt))]
        # Signal lands used here are convex. Keep mid-route land crossings
        # distinct from track segments and include pad-center offsets.
        for i,pt in enumerate(lands):
            edge(name,(layer,pt),math.dist(xy,pt)/1e6,0,("land",layer,xy,pt))
            for other in lands[i+1:]:
                edge((layer,pt),(layer,other),math.dist(pt,other)/1e6,0,("land",layer,pt,other))
    return graph


def reference_sample(board, trace, planes):
    _, layer, start, end = trace
    # Identify the adjacent designated plane. In3/B.Cu reference In4; In2/F.Cu
    # reference In1. Measuring projected copper is not an impedance calculation.
    refs = {k.F_Cu:k.In1_Cu,k.In2_Cu:k.In1_Cu,k.In3_Cu:k.In4_Cu,k.B_Cu:k.In4_Cu}
    ref = refs[layer]
    length = math.dist(start,end)/1e6
    steps = max(1,math.ceil(length/.1))
    intervals = []
    for i in range(steps):
        t=(i+.5)/steps
        pos=k.VECTOR2I(*(round(a+t*(b-a)) for a,b in zip(start,end)))
        copper = [net for net,poly in planes[ref] if poly.Collide(pos)]
        key = board.GetLayerName(layer)+" over "+board.GetLayerName(ref)+" "+(",".join(sorted(copper)) or "void")
        intervals.append((key,length/steps))
    return intervals


def measure(board):
    planes = defaultdict(list)
    for zone in board.Zones():
        if not zone.GetIsRuleArea() and zone.GetLayer() in (k.In1_Cu,k.In4_Cu):
            planes[zone.GetLayer()].append((zone.GetNetname(),zone.GetFilledPolysList(zone.GetLayer())))
    report = {}
    totals = defaultdict(dict)
    for signal, pin, jack_letter, upin, rp, mpin, entry, exit_pin in (
        ("DP","6","P","4","28","18","6","1"),("DM","7","M","6","27","17","4","3")):
        prefix="USB_D"+jack_letter
        conn=network(board,"USB_CONN_D"+jack_letter)
        protected=network(board,"USB_PROT_D"+jack_letter)
        side=network(board,prefix)
        mcu=network(board,prefix+"_MCU")
        mux_out="2" if signal=="DP" else "8"
        sub=[(protected,"D42."+exit_pin,"U41."+upin),(side,"U41."+mux_out,"R"+rp+".2"),(mcu,"R"+rp+".1","U3."+mpin)]
        for orientation,other in (("A","B"),("B","A")):
            pathsets=[(conn,"J40."+orientation+pin,"D42."+entry),*sub]
            sections, refs = [], defaultdict(float)
            total = via_count = 0
            longest_void = 0.
            for graph,start,end in pathsets:
                length,vias,path,nodes=walk(graph,start,{end})
                total+=length
                via_count+=vias
                layers=defaultdict(float)
                void_run=0.
                for step in path:
                    if step[0] not in ("trace","land","overlap"):
                        void_run=0.
                        continue
                    for ref,length_interval in reference_sample(board,step,planes):
                        void_run = void_run + length_interval if ref.endswith(" void") else 0.
                        longest_void = max(longest_void,void_run)
                        refs[ref] += length_interval
                        layers[ref.split(" over ")[0]]+=length_interval
                item = {"from":start,"to":end,"centerline_mm":round(length,3),"vias":vias,
                        "layers_mm":{layer:round(mm,3) for layer,mm in layers.items()}}
                if graph is conn:
                    aux=["J40."+other+pin]
                    item["branch_distance_to_primary_path_mm"]={p:round(walk(graph,p,nodes)[0],3) for p in aux}
                sections.append(item)
            totals[orientation][signal] = total
            report[orientation+"_"+signal]=dict(total_centerline_mm=round(total,3),via_transitions=via_count,
                          longest_contiguous_adjacent_plane_void_mm=round(longest_void,3),
                          sections=sections,adjacent_reference_mm={ref:round(mm,3) for ref,mm in sorted(refs.items())})
    skew = {ori:round(abs(pair["DP"]-pair["DM"]),3) for ori,pair in totals.items()}
    longest = max(r["longest_contiguous_adjacent_plane_void_mm"] for r in report.values())
    branches = [mm for r in report.values() for mm in r["sections"][0]["branch_distance_to_primary_path_mm"].values()]
    layers = {layer for path in report.values() for section in path["sections"] for layer in section["layers_mm"]}
    notes = [f"Longest unused orientation branch to its first main-path junction: {max(branches):.3f} mm.",
             f"Worst planar D+/D− mismatch: {max(skew.values()):.3f} mm. Both through-pin launches and internal package delays are uncharacterized.",
             f"Longest contiguous trace projection outside its adjacent plane: {longest:.3f} mm. Signal layers: {', '.join(sorted(layers))}."]
    return {"paths":report,"absolute_planar_skew_mm":skew,"engineering_observations":notes,
            "method":"Shortest native copper path between pad centers, layer-aware with via transitions and centerline links across overlapping same-net endpoint/track or via copper. Each R27/R28, D42 feed-through (6 to 1 or 4 to 3) and selected U41 DGS channel is excluded from planar length. Opposite receptacle contacts are measured to the closest point on the primary path. Plane projection sampled every 0.1 mm.",
            "limitations":"Trace skew excludes via-barrel and package propagation. Plane projection shows copper beneath selected route layers; it does not establish return continuity or 90-ohm impedance. Confirm the stackup and both orientations on assembled USB full-speed hardware."}
