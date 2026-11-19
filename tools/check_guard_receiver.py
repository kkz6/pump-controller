"""Independently audit receiver drills, mask openings, net parity and projected domain spacing."""
from collections import defaultdict
from heapq import heappop, heappush
import math
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as k
from build_guard_receiver import ISO, OUT, P, PCB, pcb_design


def mm(v):
    return round(k.ToMM(v),6)


def shortest_front_route(board, source_ref, source_pin):
    """Length from a pad centre along front copper to the filled back plane."""
    pad=board.FindFootprintByReference(source_ref).FindPadByNumber(str(source_pin))
    net=pad.GetNetname()
    def xy(point):
        return point.x,point.y
    origin=xy(pad.GetPosition())
    front=defaultdict(list)
    destinations={}
    planes=[zone.GetFilledPolysList(k.B_Cu) for zone in board.Zones()
            if not zone.GetIsRuleArea() and zone.GetNetname()==net and zone.IsOnLayer(k.B_Cu)]
    def touches_plane(item):
        return any(shape.GetClearance(item.GetEffectiveShape(k.B_Cu))==0 for shape in planes)
    if pad.GetAttribute()==k.PAD_ATTRIB_PTH and touches_plane(pad):
        return 0.0
    for t in board.GetTracks():
        if t.GetNetname()!=net:
            continue
        if isinstance(t,k.PCB_VIA):
            if touches_plane(t):
                destinations[xy(t.GetPosition())]=0
        elif t.GetLayer()==k.F_Cu:
            a,b=xy(t.GetStart()),xy(t.GetEnd())
            distance=math.dist(a,b)/1e6
            front[a].append((b,distance))
            front[b].append((a,distance))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname()!=net or p.GetAttribute()!=k.PAD_ATTRIB_PTH or not touches_plane(p):
                continue
            for vertex in front:
                if p.HitTest(k.VECTOR2I(*vertex)):
                    destinations[vertex]=math.dist(vertex,xy(p.GetPosition()))/1e6
    heap=[]
    for vertex in front:
        if pad.HitTest(k.VECTOR2I(*vertex)):
            heappush(heap,(math.dist(origin,vertex)/1e6,vertex))
    seen=set()
    best=math.inf
    while heap:
        travelled,vertex=heappop(heap)
        if travelled>=best:
            break
        if vertex in seen:
            continue
        seen.add(vertex)
        if vertex in destinations:
            best=min(best,travelled+destinations[vertex])
        for neighbor,length in front[vertex]:
            if neighbor not in seen:
                heappush(heap,(travelled+length,neighbor))
    return round(best,4) if math.isfinite(best) else None


def positive_route(board, start, end):
    """Shortest XY copper centreline path, also reporting its through-board transitions."""
    def node(p):
        return p.x,p.y
    src=board.FindFootprintByReference(start[0]).FindPadByNumber(str(start[1]))
    dst=board.FindFootprintByReference(end[0]).FindPadByNumber(str(end[1]))
    assert src.GetNetname()==dst.GetNetname()
    net=src.GetNetname()
    graph=defaultdict(list)
    def connect(a,b,distance,cross=0):
        graph[a].append((b,distance,cross))
        graph[b].append((a,distance,cross))
    for t in board.GetTracks():
        if t.GetNetname()!=net:
            continue
        a,b=node(t.GetStart()),node(t.GetEnd())
        if isinstance(t,k.PCB_VIA):
            connect((k.F_Cu,a),(k.B_Cu,a),0,1)
        else:
            connect((t.GetLayer(),a),(t.GetLayer(),b),math.dist(a,b)/1e6)
    traces=list(graph)
    def land(p):
        return (p.GetParentFootprint().GetReference(),p.GetNumber())
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname()!=net:
                continue
            for layer,pt in traces:
                if pad.IsOnLayer(layer) and pad.HitTest(k.VECTOR2I(*pt)):
                    connect(land(pad),(layer,pt),math.dist(pt,node(pad.GetPosition()))/1e6)
    queue=[(0,0,0,land(src))]
    seen=set()
    serial=0
    while queue:
        length,cross,_,u=heappop(queue)
        if u==land(dst):
            return {"xy_mm":round(length,4),"routed_vias":cross}
        if u in seen:
            continue
        seen.add(u)
        for v,w,c in graph[u]:
            if v not in seen:
                serial+=1
                heappush(queue,(length+w,cross+c,serial,v))
    raise ValueError(f"No positive trace path for {start} to {end}")


def local_returns(board):
    connections=(("U1",4),("C1",2),("D7",2),("D3",2),("D6",2),
                 ("C5",2),("C6",2),("J4",2))
    returns={f"{r}.{p}":shortest_front_route(board,r,p) for r,p in connections}
    power={f"{r}.{p} to {target[0]}.{target[1]}":positive_route(board,(r,p),target)
           for r,p,target in (("U1",8,("C1",1)),("J4",1,("D7",1)),
                              ("J4",1,("C5",1)),("J4",1,("C6",1)))}
    assert all(distance is not None for distance in returns.values()), returns
    # Catch lost plane stitching or a reintroduced detour after component moves.
    assert max(returns.values())<=2.0, returns
    for pair,maximum in (("U1.8 to C1.1",3.5),("J4.1 to D7.1",5.0)):
        assert power[pair]["routed_vias"]==0 and power[pair]["xy_mm"]<=maximum, power[pair]
    return {"method":"Pad-centre front-layer trace length to the first via or PTH touching an actual filled back-plane polygon. Positive legs report explicit two-layer XY trace length and routed via count; vertical barrel length is excluded.",
            "return_to_plane_mm":returns,"positive_traces":power}


def check():
    b=k.LoadBoard(str(PCB))
    data=pcb_design()
    source=ET.parse(OUT/"checks/source.xml")
    sourcepins={(n.get("ref"),n.get("pin")):net.get("name") for net in source.findall(".//nets/net") for n in net.findall("node")}
    actual={}
    objects={True:[],False:[]}
    maskpads=[]
    holes=[]
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            ref,num=fp.GetReference(),pad.GetNumber()
            name=pad.GetNetname()
            if num:
                actual[ref,num]=name
            if pad.GetDrillSize().x:
                holes.append((ref+"."+num,pad.GetEffectiveHoleShape()))
            if name:
                isolated=name in ISO or name.startswith("unconnected-")
                for layer in (k.F_Cu,k.B_Cu):
                    if pad.IsOnLayer(layer):
                        objects[isolated].append((ref+"."+num, pad.GetEffectiveShape(layer)))
            if pad.GetAttribute()==k.PAD_ATTRIB_SMD:
                maskpads.append((ref+"."+num,pad,pad.GetEffectiveShape(k.F_Cu)))
    assert actual==sourcepins,(actual.items()-sourcepins.items(),sourcepins.items()-actual.items())
    vias=[]
    widths=set()
    for t in b.GetTracks():
        name=t.GetNetname()
        objects[name in ISO].append((name,t.GetEffectiveShape(t.GetLayer())))
        if isinstance(t,k.PCB_VIA):
            holes.append(("via "+name,t.GetEffectiveHoleShape()))
            vias.append((mm(t.GetWidth(k.F_Cu)),mm(t.GetDrillValue())))
        else:
            widths.add(mm(t.GetWidth()))
    plane_areas={}
    for z in b.Zones():
        if not z.GetIsRuleArea():
            shape=z.GetFilledPolysList(k.B_Cu)
            assert shape.OutlineCount()>0
            plane_areas[z.GetNetname()]=round(abs(z.GetFilledArea())/1e12,2)
            objects[z.GetNetname() in ISO].append((z.GetNetname()+" plane",shape))
    assert set(plane_areas)=={"ISO_0","CAB_0"}
    nearest=(float("inf"),"","")
    for left,ls in objects[True]:
        for right,rs in objects[False]:
            nearest=min(nearest,(mm(ls.GetClearance(rs)),left,right))
    overlaps=[]
    for ref,shape in holes:
        for padref,pad,copper in maskpads:
            if copper.Collide(shape,pad.GetSolderMaskExpansion(k.F_Mask)):
                overlaps.append((ref,padref))
    assert not overlaps,overlaps
    assert nearest[0]>=2.5,nearest
    assert min(widths)>=.25 and min(v[1] for v in vias)>=.30
    assert all(abs(mm(p.GetSolderMaskExpansion(k.F_Mask))-.05)<.00001 for _,p,_ in maskpads)
    mount={f.GetReference():[mm(f.GetPosition().x),mm(f.GetPosition().y)] for f in b.GetFootprints() if f.GetReference().startswith("H")}
    assert mount=={"H1":[3,3],"H2":[65,3],"H3":[3,45],"H4":[65,45]}
    erc=json.loads((OUT/"checks/erc.json").read_text())
    drc=json.loads((OUT/"checks/drc.json").read_text())
    assert not drc["violations"] and not drc["unconnected_items"] and not drc["schematic_parity"],{k:len(drc[k]) for k in ("violations","unconnected_items","schematic_parity")}
    assert not any(s["violations"] for s in erc["sheets"])
    report={"board_sha256":hashlib.sha256(PCB.read_bytes()).hexdigest(),
            "kicad_version":k.GetBuildVersion(), "board_revision":b.GetTitleBlock().GetRevision(),
            "dimensions_mm":[68,48], "layers":b.GetCopperLayerCount(),
            "populated_components":len([p for s in data["sheets"] for p in s["components"] if not p["ref"].startswith("H")]),
            "mount_centres_mm":mount,"netlist_pads_including_nc":len(actual),
            "erc_violations":0,"drc_violations":0,"unconnected_items":0,"schematic_parity_findings":0,
            "minimum_projected_copper_gap_mm":nearest[0],"closest_items":nearest[1:],
            "measured_track_widths_mm":sorted(widths),"vias":len(vias),"via_diameter_drill_mm":sorted(set(vias)),
            "local_returns":local_returns(b),"return_plane_area_mm2":plane_areas,"drilled_features":len(holes),"all_drill_to_smt_mask_overlaps":overlaps,
            "smt_mask_expansion_mm":.05,"assembled_and_tested":False}
    (OUT/"checks/geometry.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    check()
