#!/usr/bin/env python3
"""Read-only native-board/source comparison and complete drill inventory.

Run with KiCad's Python interpreter; never refills or saves the board.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pcbnew as p

BASE = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--netlist', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
args = ap.parse_args()
board_path = BASE / 'hardware/pump-controller-rev-b.kicad_pcb'
source_path = BASE / 'design/circuit.json'
b = p.LoadBoard(str(board_path))
source = json.loads(source_path.read_text())
parts = {c['ref']: c for s in source['sheets'] for c in s['components']
         if c.get('on_board', True)}
footprints = {f.GetReference(): f for f in b.GetFootprints()}
xml = ET.parse(args.netlist).getroot()
schematic_nets = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                  for net in xml.findall('./nets/net') for n in net.findall('node')}
differences = []
connected_pins = 0
unconnected_pins = []
for ref, component in parts.items():
    if ref not in footprints:
        differences.append({'ref': ref, 'issue': 'missing footprint'})
        continue
    f = footprints[ref]
    fid = str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
    if fid != component['footprint']:
        differences.append({'ref': ref, 'issue': 'footprint identifier mismatch'})
    if f.GetValue() != component['value']:
        differences.append({'ref': ref, 'issue': 'value mismatch'})
    pinmap = {str(pin['num']): pin.get('net') or '' for pin in component['pins']}
    actual = {}
    for pad in f.Pads():
        num = pad.GetNumber()
        if not num:
            continue
        actual.setdefault(num, []).append(pad.GetNetname())
        if num not in pinmap or pad.GetNetname() != pinmap[num]:
            differences.append({'ref': ref, 'pin': num, 'issue': 'board net mismatch',
                                'actual': pad.GetNetname(), 'expected': pinmap.get(num)})
    for pin, net in pinmap.items():
        if pin not in actual:
            differences.append({'ref': ref, 'pin': pin, 'issue': 'missing physical pad'})
        sch_net = schematic_nets.get((ref, pin), '')
        if net:
            connected_pins += 1
            if sch_net != net:
                differences.append({'ref': ref, 'pin': pin, 'issue': 'schematic net mismatch',
                                    'actual': sch_net, 'expected': net})
        else:
            unconnected_pins.append({'ref': ref, 'pin': pin, 'schematic_net': sch_net})
            if sch_net and not sch_net.startswith('unconnected-('):
                differences.append({'ref': ref, 'pin': pin, 'issue': 'unexpected schematic connection'})
for ref in set(footprints) - set(parts) - {'H1', 'H2'}:
    differences.append({'ref': ref, 'issue': 'unexpected footprint'})

holes = []
for track in b.GetTracks():
    if isinstance(track, p.PCB_VIA):
        pos = track.GetPosition()
        holes.append({'kind': 'via', 'plated': True, 'net': track.GetNetname(),
                      'uuid': track.m_Uuid.AsString(),
                      'xy_mm': [p.ToMM(pos.x), p.ToMM(pos.y)],
                      'drill_mm': [p.ToMM(track.GetDrillValue())] * 2,
                      'diameter_mm': p.ToMM(track.GetWidth(p.F_Cu))})
for f in b.GetFootprints():
    for pad in f.Pads():
        drill = pad.GetDrillSize()
        if drill.x <= 0:
            continue
        pos = pad.GetPosition()
        holes.append({'kind': 'pad', 'ref': f.GetReference(), 'pad': pad.GetNumber(),
                      'plated': pad.GetAttribute() != p.PAD_ATTRIB_NPTH,
                      'net': pad.GetNetname(),
                      'xy_mm': [p.ToMM(pos.x), p.ToMM(pos.y)],
                      'drill_mm': [p.ToMM(drill.x), p.ToMM(drill.y)]})

overlaps = []
for track in b.GetTracks():
    if not isinstance(track, p.PCB_VIA):
        continue
    for f in b.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute() != p.PAD_ATTRIB_SMD:
                continue
            for layer in (p.F_Cu, p.B_Cu):
                if pad.IsOnLayer(layer) and pad.GetEffectiveShape(layer).Collide(
                        track.GetPosition(), int(track.GetDrillValue() / 2)):
                    overlaps.append({'ref': f.GetReference(), 'pad': pad.GetNumber(),
                                     'via_uuid': track.m_Uuid.AsString(),
                                     'xy_mm': [p.ToMM(track.GetPosition().x),
                                               p.ToMM(track.GetPosition().y)]})
                    break

result = {
    'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
    'circuit_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
    'read_only': True,
    'component_count': len(parts), 'connected_schematic_pins_checked': connected_pins,
    'unconnected_source_pins': unconnected_pins,
    'board_and_schematic_match_source': not differences, 'differences': differences,
    'copper_layers': b.GetCopperLayerCount(),
    'board_thickness_mm': p.ToMM(b.GetDesignSettings().GetBoardThickness()),
    'plated_holes': sum(h['plated'] for h in holes),
    'nonplated_holes': sum(not h['plated'] for h in holes),
    'holes': holes,
    'via_in_smt_pad_overlaps': overlaps,
    'via_in_smt_pad_unique_vias': len({x['via_uuid'] for x in overlaps}),
    'additional_exposed_pad_holes': [h for h in holes if h.get('ref') == 'U2' and h.get('pad') == '9'],
    'release_ready': False,
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['component_count', 'connected_schematic_pins_checked',
                 'board_and_schematic_match_source', 'plated_holes', 'nonplated_holes']}))
if differences:
    raise SystemExit('Source connectivity mismatch: inspect ' + str(args.output))
