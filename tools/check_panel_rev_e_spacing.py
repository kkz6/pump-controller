#!/usr/bin/env python3
"""Read-only independent conservative copper-spacing check for panel Rev E.

Complements native ERC/DRC, source/interface checks and exported-mask review.
Run with KiCad Python. No CAD, project rules or exported CAM is modified.
"""
from collections import Counter
import json
from pathlib import Path

import check_main_rev_e_geometry as g

p = g.p
BASE = Path(__file__).resolve().parents[1]
path = BASE / 'hardware/panel-rev-e/pump-panel-rev-e.kicad_pcb'
before = g.sha(path)
b = p.LoadBoard(str(path))
objects, violations, annuli, holes = [], [], [], []
measured = Counter()


def add(item, kind, layer, name, mask=False):
    shape = item.GetEffectiveShape(layer)
    objects.append({'id': name, 'kind': kind, 'net': item.GetNetname(), 'domain': 'SELV',
                    'layer': layer, 'mask': mask, 'shape': shape, 'bbox': g.bbox(shape)})


def fail(rule, actual, required, **items):
    if actual + g.EPS < required:
        violations.append({'rule': rule, 'actual_mm': actual, 'required_mm': required, **items})


for track in b.GetTracks():
    via = isinstance(track, p.PCB_VIA)
    uid = str(track.m_Uuid.AsString())
    for layer in [p.F_Cu, p.B_Cu] if via else [track.GetLayer()]:
        add(track, 'via' if via else 'track', layer, uid)
    if via:
        drill, diameter = p.ToMM(track.GetDrillValue()), p.ToMM(track.GetWidth(p.F_Cu))
        annuli.append(((diameter - drill) / 2, 'via'))
        fail('via_diameter', diameter, .65, item=uid)
        fail('via_drill', drill, .30, item=uid)
        holes.append((uid, track.GetPosition(), drill, track.GetNetname(), 'via'))
    else:
        fail('track_width', p.ToMM(track.GetWidth()), .15, item=uid)

for footprint in b.GetFootprints():
    for pad in footprint.Pads():
        uid = footprint.GetReference() + '.' + pad.GetNumber()
        drill = pad.GetDrillSize()
        npth = pad.GetAttribute() == p.PAD_ATTRIB_NPTH
        if drill.x:
            if drill.x != drill.y:
                raise ValueError('Non-round hole requires a separate shape audit: ' + uid)
            holes.append((uid, pad.GetPosition(), p.ToMM(drill.x), pad.GetNetname(), 'npth' if npth else 'pth'))
        if npth:
            continue
        for layer, mask in [(p.F_Cu, p.F_Mask), (p.B_Cu, p.B_Mask)]:
            if not pad.IsOnLayer(layer):
                continue
            kind = 'pth_pad' if drill.x else 'smd_pad'
            add(pad, kind, layer, uid, pad.IsOnLayer(mask))
            if pad.IsOnLayer(mask):
                margin = p.ToMM(pad.GetSolderMaskExpansion(mask))
                if abs(margin - .05) > g.EPS:
                    violations.append({'rule': 'mask_expansion', 'item': uid, 'actual_mm': margin, 'required_mm': .05})
            if kind == 'pth_pad':
                poly = pad.GetEffectivePolygon(layer)
                contours = [poly.COutline(i) for i in range(poly.OutlineCount())]
                contours += [poly.CHole(i, j) for i in range(poly.OutlineCount()) for j in range(poly.HoleCount(i))]
                ring = min(p.ToMM(c.Distance(pad.GetPosition(), True)) for c in contours) - p.ToMM(drill.x) / 2
                annuli.append((ring, 'component'))
                fail('pth_pad_size', min(p.ToMM(pad.GetSize().x), p.ToMM(pad.GetSize().y)), 1, item=uid)

for index, a in enumerate(objects):
    fail('copper_edge', min(a['bbox'][0], a['bbox'][1], 60-a['bbox'][2], 45-a['bbox'][3]), .30, item=a['id'])
    for other in objects[index + 1:]:
        if a['layer'] != other['layer'] or a['id'] == other['id']:
            continue
        rule = g.required_clearance(a, other)
        if rule and g.boxgap(a['bbox'], other['bbox']) <= rule[1] + g.EPS:
            measured[rule[0]] += 1
            fail(rule[0], p.ToMM(a['shape'].GetClearance(other['shape'])), rule[1], a=a['id'], b=other['id'])
for index, (uid, position, drill, net, kind) in enumerate(holes):
    for other_id, other_pos, other_drill, other_net, other_kind in holes[index+1:]:
        gap = p.ToMM((position-other_pos).EuclideanNorm()) - (drill+other_drill)/2
        if not net or net != other_net:
            fail('different_net_hole_spacing', gap, .50, a=uid, b=other_id)
        elif kind == other_kind == 'via':
            fail('same_net_via_hole_spacing', gap, .254, a=uid, b=other_id)
    for track in [x for x in objects if x['kind'] == 'track' and (not net or x['net'] != net)]:
        fail('hole_track_spacing', p.ToMM(track['shape'].Distance(position)) - drill/2,
             .33 if kind == 'pth' else .254, hole=uid, track=track['id'])
for value, kind in annuli:
    fail('annulus', value, .15 if kind == 'via' else .30, kind=kind)
project = json.loads(path.with_suffix('.kicad_pro').read_text())
exclusions = project['board']['design_settings'].get('drc_exclusions', [])
if g.sha(path) != before:
    raise SystemExit('Native PCB changed during validation; discard and rerun.')
report = {'pcb_sha256': before, 'rules_sha256': g.sha(path.with_suffix('.kicad_dru')),
          'method': 'Native effective copper shape clearances, nominal round-hole edges and merged pad contour annuli.',
          'copper_clearance_and_geometry_violations': violations, 'close_pairs_measured': dict(measured),
          'minimum_via_annulus_mm': min(x for x, kind in annuli if kind == 'via'),
          'minimum_component_pth_annulus_mm': min(x for x, kind in annuli if kind == 'component'),
          'project_drc_exclusions': exclusions, 'nominal_copper_checks_passed': not (violations or exclusions),
          'hardware_tested': False, 'release_ready': False}
(path.parent / 'checks/independent-spacing-review.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['nominal_copper_checks_passed'], 'violations': violations}, indent=2))
raise SystemExit(0 if report['nominal_copper_checks_passed'] else 1)
