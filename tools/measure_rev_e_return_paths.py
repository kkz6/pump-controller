"""Measure routed length and reference copper at 0.1 mm intervals on critical nets."""
from pathlib import Path
import argparse, hashlib, json, math
import pcbnew as p

def measure(board_path):
    b = p.LoadBoard(str(board_path))
    planes = {}
    for zone in b.Zones():
        if zone.GetIsRuleArea() or zone.GetLayer() not in (p.In1_Cu, p.In4_Cu):
            continue
        key = (zone.GetLayer(), zone.GetNetname())
        if key in planes:
            raise ValueError(f'Duplicate reference plane: {key}')
        planes[key] = zone.GetFilledPolysList(zone.GetLayer())
    expected = {(p.In1_Cu, 'GND'), (p.In1_Cu, 'M_GND'),
                (p.In4_Cu, '+3V3'), (p.In4_Cu, 'M_GND')}
    if set(planes) != expected:
        raise ValueError('Unexpected plane assignment')
    nets = {n: {'length_mm':0., 'signal_vias':0, 'samples':0,
                'reference_copper_samples':0, 'longest_gap_on_one_segment_mm':0.}
            for n in ['USB_DM_MCU','USB_DP_MCU','USB_DM','USB_DP','M_XIN','M_XOUT']}
    if b.FindNet('USB_CONN_DP') is not None:
        for name in ('USB_CONN_DP', 'USB_CONN_DM', 'USB_PROT_DP', 'USB_PROT_DM'):
            nets[name] = dict.fromkeys(nets['USB_DP'], 0)
    signal_reference_layers = {p.F_Cu: p.In1_Cu, p.In2_Cu: p.In1_Cu,
                               p.In3_Cu: p.In4_Cu, p.B_Cu: p.In4_Cu}
    plane_tracks = []
    for t in b.GetTracks():
        via = isinstance(t, p.PCB_VIA)
        net = t.GetNetname()
        if not via and t.GetLayer() in (p.In1_Cu,p.In4_Cu):
            plane_tracks.append(net)
        if net not in nets:
            continue
        rec = nets[net]
        if via:
            rec['signal_vias'] += 1
            continue
        length = p.ToMM(t.GetLength())
        rec['length_mm'] += length
        start, end = t.GetStart(), t.GetEnd()
        layer = signal_reference_layers.get(t.GetLayer())
        if layer is None:
            raise ValueError(f'Signal {net} on reserved layer {b.GetLayerName(t.GetLayer())}')
        ref = 'M_GND' if net.startswith('M_') else ('GND' if layer == p.In1_Cu else '+3V3')
        poly = planes[layer, ref]
        steps = max(1, math.ceil(length / .1))
        gap = 0
        for k in range(steps):
            frac = (k + .5) / steps
            pt = p.VECTOR2I(round(start.x + frac*(end.x-start.x)),
                            round(start.y + frac*(end.y-start.y)))
            covered = bool(poly.Collide(pt))
            rec['samples'] += 1
            rec['reference_copper_samples'] += covered
            gap = 0 if covered else gap + 1
            rec['longest_gap_on_one_segment_mm'] = max(
                rec['longest_gap_on_one_segment_mm'], gap * length / steps)
    for r in nets.values():
        r['length_mm'] = round(r['length_mm'],3)
        r['longest_gap_on_one_segment_mm'] = round(r['longest_gap_on_one_segment_mm'],3)
    return {
        'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
        'reference_planes': [{'layer':b.GetLayerName(layer),'net':net,
                              'connected_polygons':poly.OutlineCount(),
                              'area_mm2':round(poly.Area()/1e12,2)}
                             for (layer,net),poly in sorted(planes.items())],
        'tracks_on_reserved_plane_layers':plane_tracks,
        'routed_signals':nets,
        'usb_total_length_difference_mm':round(abs(
          nets['USB_DP']['length_mm']+nets['USB_DP_MCU']['length_mm']-
          nets['USB_DM']['length_mm']-nets['USB_DM_MCU']['length_mm']+
          nets.get('USB_CONN_DP', {}).get('length_mm', 0)-nets.get('USB_CONN_DM', {}).get('length_mm', 0)+
          nets.get('USB_PROT_DP', {}).get('length_mm', 0)-nets.get('USB_PROT_DM', {}).get('length_mm', 0)),3),
        'scope':'Trace centres project onto the adjacent reserved plane. SELV traces reference In1 GND from F.Cu/In2 and In4 +3V3 from In3/B.Cu. Metering traces reference the corresponding M_GND plane. Via antipads and clearance around through holes create local voids. Lengths sum routed copper including receptacle and ESD branches when fitted. They exclude vertical travel, contact pins and cable. Geometry does not measure return current, differential impedance, oscillator margin, emissions or immunity.'
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args()
    result=measure(args.board)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    if result['tracks_on_reserved_plane_layers'] or any(
        plane['connected_polygons'] != 1 for plane in result['reference_planes']):
        raise SystemExit('Reserved plane interrupted or used for a signal')
