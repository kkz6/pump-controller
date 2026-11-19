#!/usr/bin/env python3
"""Read-only Rev E geometry, domains and electrical-source audit.

Run with KiCad 10 Python bindings. This checks conservative project rules,
not a manufacturer's acceptance. It never saves/refills the source PCB.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pcbnew as p

BASE = Path(__file__).resolve().parents[1]
LIMITS = {
    'track_width': .15, 'track_track': .15, 'pad_track': .20,
    'via_track_copper': .254, 'pth_track_copper': .33,
    'via_track_hole': .254, 'pth_track_hole': .33, 'npth_track_hole': .254,
    'pth_pad_pad': .50, 'different_net_holes': .50, 'same_net_via_holes': .254,
    'via_drill': .30, 'via_diameter': .65, 'via_annulus': .15,
    'pth_annulus': .30, 'pth_pad_min_size': 1.0, 'smt_pad_gap': .20,
    'mask_expansion': .05, 'mask_web': .10,
    'silk_height': 1.0, 'silk_stroke': .16, 'silk_pad_gap': .15,
    'copper_edge': .30, 'live_selv': 8.0,
}
EPS = .00001  # ten native integer units: rounding only, not a DFM allowance
FIELD_CONTACTS = frozenset({'CTRL_A_COM', 'CTRL_A_NO', 'CTRL_B_COM', 'CTRL_B_NO'})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm(value):
    return p.ToMM(value)


def bbox(shape):
    b = shape.BBox()
    return (mm(b.GetX()), mm(b.GetY()), mm(b.GetX() + b.GetWidth()),
            mm(b.GetY() + b.GetHeight()))


def boxgap(a, b):
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0),
                      max(a[1] - b[3], b[1] - a[3], 0))


def polygon_contours(poly):
    """Export merged pad contours for independent final-mask registration."""
    def points(chain):
        return [[mm(chain.CPoint(i).x), mm(chain.CPoint(i).y)]
                for i in range(chain.PointCount())]
    return [{'outline': points(poly.COutline(i)),
             'holes': [points(poly.CHole(i, j)) for j in range(poly.HoleCount(i))]}
            for i in range(poly.OutlineCount())]


def label(record):
    return {k: record[k] for k in ['id', 'uuid', 'kind', 'net', 'domain', 'layer']
            if k in record}



def closest_groups(first, second, first_label, second_label):
    """Find the minimum planar copper gap, including curved lands and filled zones."""
    live = sorted(first, key=lambda obj: -obj['_bbox'][2])
    isolated = sorted(second, key=lambda obj: obj['_bbox'][0])
    if not live or not isolated:
        raise ValueError('Missing copper domain during separation measurement')
    minimum = math.inf
    result = None
    for a in live:
        # Each subsequent live object has a right edge no farther right.
        if isolated[0]['_bbox'][0] - a['_bbox'][2] >= minimum:
            break
        for b in isolated:
            if b['_bbox'][0] - a['_bbox'][2] >= minimum:
                break
            if boxgap(a['_bbox'], b['_bbox']) >= minimum:
                continue
            gap = mm(a['_shape'].GetClearance(b['_shape']))
            if gap < minimum:
                minimum = gap
                result = {'gap_mm': gap, first_label: label(a), second_label: label(b)}
    return result


def closest_domains(objects):
    return closest_groups((o for o in objects if o['domain'] == 'LIVE'),
                          (o for o in objects if o['domain'] == 'SELV'), 'live', 'isolated')


def required_clearance(a, b):
    """Conservative process clearances plus preserved voltage-domain rules."""
    if a['net'] and a['net'] == b['net']:
        return None
    kinds = {a['kind'], b['kind']}
    rule, gap = 'general_copper', .15
    if kinds == {'track'}:
        rule, gap = 'track_track', LIMITS['track_track']
    elif 'track' in kinds:
        if 'via' in kinds:
            rule, gap = 'via_track_copper', LIMITS['via_track_copper']
        elif 'pth_pad' in kinds:
            rule, gap = 'pth_track_copper', LIMITS['pth_track_copper']
        elif 'smd_pad' in kinds:
            rule, gap = 'pad_track', LIMITS['pad_track']
    elif kinds == {'pth_pad'}:
        rule, gap = 'pth_pad_pad', LIMITS['pth_pad_pad']
    elif kinds == {'smd_pad'} and a.get('mask') and b.get('mask'):
        rule, gap = 'smt_pad_gap', LIMITS['smt_pad_gap']
    nets = {a['net'], b['net']}
    domains = {a['domain'], b['domain']}
    voltage_gap = 0
    if domains == {'LIVE', 'SELV'}:
        rule, gap = 'live_selv', LIMITS['live_selv']
    elif domains == {'LIVE'}:
        if nets & FIELD_CONTACTS:
            if not nets <= FIELD_CONTACTS:
                return 'starter_field_to_board_mains', LIMITS['live_selv']
            return 'starter_field_differential', 2.0
        if nets & {'MAINS_L', 'L_FUSED', 'L_PROTECTED', 'CTRL_IN', 'CTRL_MID', 'CTRL_OUT'}:
            voltage_gap = 2.0
        elif 'M_VDIV_0' in nets:
            voltage_gap = 1.8
        elif 'M_VDIV_1' in nets:
            voltage_gap = 1.2
        elif 'M_VDIV_2' in nets:
            voltage_gap = .6
        if nets in ({'L_PROTECTED', 'M_VDIV_0'}, {'M_VDIV_0', 'M_VDIV_1'},
                    {'M_VDIV_1', 'M_VDIV_2'}):
            voltage_gap = .6
        elif nets == {'M_VDIV_0', 'M_VDIV_2'}:
            voltage_gap = 1.2
        if voltage_gap > gap:
            rule, gap = 'live_differential_voltage', voltage_gap
    return rule, gap


def audit(args):
    board_path = args.board.resolve()
    source_path = args.source.resolve()
    before = sha(board_path)
    b = p.LoadBoard(str(board_path))
    source = json.loads(source_path.read_text())
    components = {c['ref']: c for sheet in source['sheets'] for c in sheet['components']
                  if c.get('on_board', True)}
    variant = source['board'].get('variant')
    dual = variant == 'compact-dual'
    has_indicators = variant in ('compact-led', 'compact-dual')
    compact = variant == 'compact' or has_indicators
    original = json.loads((BASE / 'design/circuit.json').read_text())
    original_parts = {c['ref']: c for sheet in original['sheets'] for c in sheet['components']
                      if c.get('on_board', True) and c['ref'] not in {'SW3', 'SW4', 'J33', 'J34'}}
    footprints = {f.GetReference(): f for f in b.GetFootprints()}
    violations, source_issues, unqualified = [], [], []
    if dual:
        for ref in ('SW1', 'SW2'):
            del original_parts[ref]
        for ref in set(components) | set(footprints):
            if ref.startswith('SW'):
                source_issues.append({'ref': ref, 'issue': 'all buttons must be on the OLED panel'})
    inventory = {'tracks': [], 'vias': [], 'pth_pads': [], 'npth_pads': [], 'mask_pads': [],
                 'silk': [], 'zones': [], 'copper_graphics': []}
    all_holes, copper, smd = [], [], []
    layers = [layer for layer in b.GetEnabledLayers().Seq() if p.IsCopperLayer(layer)]

    def issue(rule, actual, minimum, **data):
        violations.append({'rule': rule, 'actual_mm': actual, 'minimum_mm': minimum, **data})

    if b.GetCopperLayerCount() != 6:
        violations.append({'rule': 'copper_layer_count', 'actual': b.GetCopperLayerCount(), 'expected': 6})

    # Preserve electrical connections independently of layout, footprint and
    # service-header changes. SW3/SW4 have moved to the separate Rev D panel.
    for ref, old in original_parts.items():
        new = components.get(ref)
        if not new:
            source_issues.append({'ref': ref, 'issue': 'original electrical component missing'})
            continue
        old_pins = {str(x['num']): x.get('net') or '' for x in old['pins']}
        conditioner_raw_pins = {'R80': ('2','STOP_SENSE_RAW'), 'R81': ('1','STOP_SENSE_RAW'), 'C80': ('1','STOP_SENSE_RAW'),
                                'R82': ('2','MAN_SENSE_RAW'), 'R83': ('1','MAN_SENSE_RAW'), 'C82': ('1','MAN_SENSE_RAW'),
                                'R84': ('2','AUTO_SENSE_RAW'), 'R85': ('1','AUTO_SENSE_RAW'), 'C84': ('1','AUTO_SENSE_RAW')}
        if ref in conditioner_raw_pins:
            pin, raw_net = conditioner_raw_pins[ref]
            old_pins[pin] = raw_net
        conditioner_values = {'R80':'10k','R82':'10k','R84':'10k','R81':'33k','R83':'33k','R85':'33k','C80':'10nF','C82':'10nF','C84':'10nF'}
        if ref in conditioner_values and new['value'] != conditioner_values[ref]:
            source_issues.append({'ref': ref, 'issue': 'conditioner divider/filter value mismatch', 'expected': conditioner_values[ref], 'actual': new['value']})
        if ref == 'U31':
            old_pins['6'] = 'ARM_CLEAR_N'
        if compact and ref == 'U33':
            old_pins.update({'8': '', '21': 'SPARE_B7'})
            if has_indicators:
                old_pins.update({'8': 'START_CMD_LED', '28': 'STOP_CMD_LED'})
            if dual:
                old_pins.update({'24': 'HOST_SENSE_N', '23': 'LOCAL_SENSE_N'})
            pin_types = {str(pin['num']): pin['type'] for pin in new['pins']}
            if new['mpn'] != 'MCP23017-E/SS' or any(pin_types.get(i) != 'output' for i in ['8', '28']):
                message = 'compact key requires two unconnected output-only pins on the MCP23017'
                if has_indicators:
                    message = 'command indicators require GPB7 and GPA7 as output-only MCP23017 pins'
                source_issues.append({'ref': ref, 'issue': message})
        if ref == 'J32':
            # Rev E consolidates the three previous panel/expansion headers
            # into one connector matching Rev D panel J1 cavity-for-cavity.
            old_pins = dict(zip([str(i) for i in range(1, 13)],
                               ['+5V', 'STOP_RETURN', 'MAN_RETURN', 'AUTO_RETURN',
                                'START_N', 'RESET_N', 'GND', '+3V3', 'I2C_SDA',
                                'I2C_SCL', 'SPARE_B6', 'SPARE_B7']))
            old_pins['MP'] = 'GND'
        if dual and ref == 'K1':
            old_pins.update({'2': 'CTRL_A_COM', '3': 'CTRL_A_NO'})
        if dual and ref == 'K2':
            old_pins.update({'2': 'CTRL_B_COM', '3': 'CTRL_B_NO'})
        if dual and ref == 'J30':
            old_pins = {'1': 'CTRL_A_COM', '2': 'CTRL_A_NO'}
        new_pins = {str(x['num']): x.get('net') or '' for x in new['pins']}
        if old_pins != new_pins:
            source_issues.append({'ref': ref, 'issue': 'functional pin/net map changed',
                                  'original': old_pins, 'new': new_pins})
    expected_additions = {
        'U36': {'1': '', '2': 'SAFE_CLEAR_N', '3': 'GND', '4': 'ARM_CLEAR_N', '5': '+3V3'},
        'C77': {'1': '+3V3', '2': 'GND'},
        'U37': {'1':'STOP_SENSE_RAW','2':'AUTO_SENSE','3':'MAN_SENSE_RAW','4':'GND',
                '5':'MAN_SENSE','6':'AUTO_SENSE_RAW','7':'STOP_SENSE','8':'+3V3'},
        'C78': {'1': '+3V3', '2': 'GND'},
    }
    if dual:
        expected_additions.update({
            'J35': {'1': 'CTRL_B_COM', '2': 'CTRL_B_NO'},
            'J36': {'1': 'GND', '2': 'HOST_AUX_N', '3': 'LOCAL_AUX_N', '4': 'HB_MON', '5': 'PANEL_OK_MON', 'MP': 'GND'},
            'R192': {'1': 'HOST_AUX_N', '2': 'HOST_SENSE_N'},
            'R193': {'1': 'LOCAL_AUX_N', '2': 'LOCAL_SENSE_N'},
            'R194': {'1': '+3V3', '2': 'HOST_SENSE_N'},
            'R195': {'1': '+3V3', '2': 'LOCAL_SENSE_N'},
            'R196': {'1': 'HEARTBEAT', '2': 'HB_MON'},
            'R197': {'1': 'STOP_RETURN', '2': 'PANEL_OK_MON'},
        })
        for ref, value in {'R192':'1k', 'R193':'1k', 'R194':'10k', 'R195':'10k', 'R196':'1k', 'R197':'1k'}.items():
            if components.get(ref, {}).get('value') != value:
                source_issues.append({'ref': ref, 'issue': 'transfer input resistor mismatch', 'expected': value})
    if has_indicators:
        expected_additions.update({
            'R190': {'1': 'START_CMD_LED', '2': 'START_LED_A'},
            'D40': {'1': 'GND', '2': 'START_LED_A'},
            'R191': {'1': 'STOP_CMD_LED', '2': 'STOP_LED_A'},
            'D41': {'1': 'GND', '2': 'STOP_LED_A'},
        })
        indicator_parts = {
            'R190': ('1k', 'RC0603FR-071KL'),
            'D40': ('START CMD GREEN', 'APTD1608LCGCK'),
            'R191': ('1k', 'RC0603FR-071KL'),
            'D41': ('STOP CMD RED', 'APT1608LSECK/J3-PRV'),
        }
        for ref, (value, mpn) in indicator_parts.items():
            part = components.get(ref, {})
            if (part.get('value'), part.get('mpn')) != (value, mpn):
                source_issues.append({'ref': ref, 'issue': 'command indicator part mismatch',
                                      'expected_value': value, 'expected_mpn': mpn})
    for ref, value in {'U37':'SN74LVC3G17DCUR','C78':'100nF'}.items():
        if components.get(ref,{}).get('value') != value:
            source_issues.append({'ref': ref, 'issue': 'conditioner part/value mismatch', 'expected': value})
    for ref, expected in expected_additions.items():
        actual = {str(x['num']): x.get('net') or '' for x in components.get(ref, {}).get('pins', [])}
        if actual != expected:
            message = 'safety buffer pin/net map mismatch'
            if has_indicators and ref in indicator_parts:
                message = 'command indicator pin/net map mismatch'
            if dual and ref == 'J35':
                message = 'output B pin/net map mismatch'
            source_issues.append({'ref': ref, 'issue': message, 'expected': expected, 'actual': actual})
    for ref, c in components.items():
        if ref not in original_parts and ref not in expected_additions and c.get('pins'):
            source_issues.append({'ref': ref, 'issue': 'unexpected new electrical component'})
    for removed in ('SW3', 'SW4', 'J33', 'J34'):
        if removed in footprints:
            source_issues.append({'ref': removed, 'issue': 'superseded control/header still present in CAD'})

    sch_nets = None
    if args.netlist:
        xml = ET.parse(args.netlist).getroot()
        sch_nets = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                    for net in xml.findall('./nets/net') for n in net.findall('node')}
    connected_pins = 0
    source_pins = []
    for ref, c in components.items():
        f = footprints.get(ref)
        if f is None:
            source_issues.append({'ref': ref, 'issue': 'missing native footprint'})
            continue
        if compact:
            placement = c['placement']
            point = f.GetPosition()
            angle_error = (f.GetOrientationDegrees() - placement['rotation'] + 180) % 360 - 180
            if (abs(mm(point.x) - placement['x']) > EPS or abs(mm(point.y) - placement['y']) > EPS
                    or abs(angle_error) > EPS or f.IsFlipped() != (placement.get('side', 'F') == 'B')):
                source_issues.append({'ref': ref, 'issue': 'native placement differs from compact source'})
        fid = str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
        if fid != c['footprint'] or f.GetValue() != c['value']:
            source_issues.append({'ref': ref, 'issue': 'native footprint/value mismatch'})
        expected = {str(x['num']): x.get('net') or '' for x in c['pins']}
        for pin, net in expected.items():
            pads = [pad for pad in f.Pads() if pad.GetNumber() == pin]
            actual = {pad.GetNetname() for pad in pads}
            nc_ok = not net and all(not n or n.startswith('unconnected-(') for n in actual)
            if not pads or (actual != {net} and not nc_ok):
                source_issues.append({'ref': ref, 'pin': pin, 'issue': 'native pad/net mismatch',
                                      'expected': net, 'actual': sorted(actual)})
            if net:
                connected_pins += 1
            if sch_nets is not None:
                sn = sch_nets.get((ref, pin), '')
                if (net and sn != net) or (not net and sn and not sn.startswith('unconnected-(')):
                    source_issues.append({'ref': ref, 'pin': pin, 'issue': 'schematic/source mismatch',
                                          'expected': net, 'actual': sn})
            source_pins.append({'ref': ref, 'pin': pin, 'net': net})
        for pad in f.Pads():
            if pad.GetNumber() and pad.GetNumber() not in expected:
                source_issues.append({'ref': ref, 'pin': pad.GetNumber(), 'issue': 'unmapped native pad'})
    for ref, f in footprints.items():
        if ref not in components and not (re.fullmatch(r'H\d+', ref)
                                          and all(q.GetAttribute() == p.PAD_ATTRIB_NPTH for q in f.Pads())):
            source_issues.append({'ref': ref, 'issue': 'unexpected native footprint'})

    old_project = json.loads((BASE / 'hardware/pump-controller-rev-b.kicad_pro').read_text())
    domains = {x['pattern']: x['netclass'] for x in old_project['net_settings']['netclass_patterns']
               if x['netclass'] in {'LIVE', 'SELV'}}
    domains.update({net: 'SELV' for net in ('ARM_CLEAR_N','STOP_SENSE_RAW','MAN_SENSE_RAW','AUTO_SENSE_RAW')})
    if dual:
        domains.update(dict.fromkeys(FIELD_CONTACTS, 'LIVE'))
        domains.update(dict.fromkeys(('HOST_AUX_N','LOCAL_AUX_N','HOST_SENSE_N','LOCAL_SENSE_N','HB_MON','PANEL_OK_MON'), 'SELV'))
    if has_indicators:
        domains.update({net: 'SELV' for net in ('START_CMD_LED', 'START_LED_A', 'STOP_CMD_LED', 'STOP_LED_A')})
    domain_issues = []

    def domain(net, ref=None, pin=None):
        expected = domains.get(net)
        if expected is None and ref in components:
            known = {domains.get(x.get('net')) for x in components[ref]['pins'] if x.get('net')}
            known.discard(None)
            if len(known) == 1:
                expected = next(iter(known))
            elif ref == 'U11' and pin and pin.isdigit():
                expected = 'SELV' if int(pin) <= 14 else 'LIVE'
        if expected:
            n = b.FindNet(net) if net else None
            classes = {x.strip() for x in str(n.GetNetClassName()).split(',')} if n else set()
            if classes & {'LIVE', 'SELV'} != {expected}:
                domain_issues.append({'net': net, 'ref': ref, 'pin': pin,
                                      'expected': expected, 'native_classes': sorted(classes)})
            return expected
        unqualified.append({'issue': 'copper isolation domain not established',
                            'net': net, 'ref': ref, 'pin': pin})
        return 'UNKNOWN'

    def record(item, kind, layer, ref=None, pin=None, mask=False):
        net = item.GetNetname()
        shape = item.GetEffectiveShape(layer)
        return {'id': (ref + '.' + pin) if ref is not None else str(item.m_Uuid.AsString()),
                'uuid': str(item.m_Uuid.AsString()), 'kind': kind, 'net': net,
                'domain': domain(net, ref, pin), 'layer': b.GetLayerName(layer),
                '_shape': shape, '_bbox': bbox(shape), 'mask': mask}

    def hole_record(item, kind, drill, ref=None, pin=None):
        pos = item.GetPosition()
        return {'kind': kind, 'uuid': str(item.m_Uuid.AsString()), 'ref': ref, 'pin': pin,
                'net': item.GetNetname(), 'plated': kind != 'npth',
                'xy_mm': [mm(pos.x), mm(pos.y)], 'drill_mm': [mm(drill.x), mm(drill.y)],
                '_pos': pos}

    for t in b.GetTracks():
        if isinstance(t, p.PCB_VIA):
            drill, diameter = mm(t.GetDrillValue()), mm(t.GetWidth(p.F_Cu))
            annulus = (diameter - drill) / 2
            inv = {'uuid': str(t.m_Uuid.AsString()), 'net': t.GetNetname(),
                   'xy_mm': [mm(t.GetPosition().x), mm(t.GetPosition().y)],
                   'diameter_mm': diameter, 'drill_mm': drill, 'annulus_mm': annulus}
            inventory['vias'].append(inv)
            for name, actual in [('via_drill', drill), ('via_diameter', diameter), ('via_annulus', annulus)]:
                if actual + EPS < LIMITS[name]:
                    issue(name, actual, LIMITS[name], item=inv)
            if t.TopLayer() != p.F_Cu or t.BottomLayer() != p.B_Cu:
                unqualified.append({'issue': 'blind/buried via is not supported', 'item': inv})
            all_holes.append(hole_record(t, 'via', p.VECTOR2I(t.GetDrillValue(), t.GetDrillValue())))
            for layer in layers:
                if t.IsOnLayer(layer):
                    copper.append(record(t, 'via', layer))
        else:
            width = mm(t.GetWidth())
            inv = {'uuid': str(t.m_Uuid.AsString()), 'net': t.GetNetname(),
                   'width_mm': width, 'layer': b.GetLayerName(t.GetLayer())}
            inventory['tracks'].append(inv)
            if t.GetLayer() in (p.In1_Cu, p.In4_Cu):
                violations.append({'rule': 'reference_plane_must_not_contain_tracks', 'item': inv})
            if width + EPS < LIMITS['track_width']:
                issue('track_width', width, LIMITS['track_width'], item=inv)
            copper.append(record(t, 'track', t.GetLayer()))

    for ref, f in footprints.items():
        for pad in f.Pads():
            number = pad.GetNumber()
            drill = pad.GetDrillSize()
            npth = pad.GetAttribute() == p.PAD_ATTRIB_NPTH
            drilled = drill.x > 0
            pad_kind = 'pth_pad' if drilled else 'smd_pad'
            if drilled:
                h = hole_record(pad, 'npth' if npth else 'pth', drill, ref, number)
                all_holes.append(h)
                inv = {k: v for k, v in h.items() if not k.startswith('_')}
                if drill.x != drill.y:
                    unqualified.append({'issue': 'non-round drill requires explicit audit', 'item': inv})
                if not npth:
                    annuli = []
                    for layer in layers:
                        if pad.IsOnLayer(layer):
                            # EffectiveShape may be a union of overlapping
                            # primitives. Its primitive boundaries are not the
                            # outer land boundary, so use the merged polygon's
                            # actual closed contours for the annular ring.
                            poly = pad.GetEffectivePolygon(layer)
                            contours = [poly.COutline(i) for i in range(poly.OutlineCount())]
                            contours += [poly.CHole(i, j) for i in range(poly.OutlineCount())
                                         for j in range(poly.HoleCount(i))]
                            distance = min(mm(c.Distance(pad.GetPosition(), True)) for c in contours)
                            annuli.append(distance - mm(drill.x) / 2 if poly.Collide(pad.GetPosition()) else -mm(drill.x) / 2)
                    ring = min(annuli) if annuli else -1
                    inv['minimum_annulus_mm'] = ring
                    inv['pad_size_mm'] = [mm(pad.GetSize().x), mm(pad.GetSize().y)]
                    if ring + EPS < LIMITS['pth_annulus']:
                        issue('pth_annulus', ring, LIMITS['pth_annulus'], item=inv)
                    if min(inv['pad_size_mm']) + EPS < LIMITS['pth_pad_min_size']:
                        issue('pth_pad_min_size', min(inv['pad_size_mm']), LIMITS['pth_pad_min_size'], item=inv)
                inventory['npth_pads' if npth else 'pth_pads'].append(inv)
            for cu_layer, mask_layer in [(p.F_Cu, p.F_Mask), (p.B_Cu, p.B_Mask)]:
                if pad.IsOnLayer(mask_layer):
                    expansion = mm(pad.GetSolderMaskExpansion(mask_layer))
                    inv = {'ref': ref, 'pin': number, 'side': b.GetLayerName(mask_layer),
                           'expansion_mm': expansion, 'uuid': str(pad.m_Uuid.AsString()),
                           'smd': pad.GetAttribute() == p.PAD_ATTRIB_SMD,
                           'xy_mm': [mm(pad.GetPosition().x), mm(pad.GetPosition().y)],
                           'copper_contours_mm': polygon_contours(pad.GetEffectivePolygon(cu_layer))}
                    inventory['mask_pads'].append(inv)
                    if abs(expansion - LIMITS['mask_expansion']) > EPS:
                        issue('mask_expansion', expansion, LIMITS['mask_expansion'], item=inv)
            if npth:
                continue
            for layer in layers:
                if not pad.IsOnLayer(layer):
                    continue
                mask_layer = p.F_Mask if layer == p.F_Cu else p.B_Mask if layer == p.B_Cu else None
                has_mask = mask_layer is not None and pad.IsOnLayer(mask_layer)
                rec = record(pad, pad_kind, layer, ref, number, has_mask)
                rec['mask_expansion'] = mm(pad.GetSolderMaskExpansion(mask_layer)) if has_mask else 0
                copper.append(rec)
                if pad.GetAttribute() == p.PAD_ATTRIB_SMD and layer in (p.F_Cu, p.B_Cu):
                    smd.append(rec)

    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for layer in layers:
            if not z.IsOnLayer(layer):
                continue
            inv = {'uuid': str(z.m_Uuid.AsString()), 'net': z.GetNetname(),
                   'layer': b.GetLayerName(layer), 'filled': z.HasFilledPolysForLayer(layer),
                   'zone_marked_filled': z.IsFilled(), 'zone_needs_refill': z.NeedRefill()}
            inventory['zones'].append(inv)
            if not inv['zone_marked_filled'] or inv['zone_needs_refill']:
                unqualified.append({'issue': 'stored zone fill requires refresh', 'item': inv})
            if not inv['filled']:
                unqualified.append({'issue': 'zone has no stored filled geometry', 'item': inv})
                continue
            shape = z.GetFilledPolysList(layer)
            copper.append({'id': inv['uuid'], 'uuid': inv['uuid'], 'kind': 'zone',
                           'net': z.GetNetname(), 'domain': domain(z.GetNetname()),
                           'layer': inv['layer'], '_shape': shape, '_bbox': bbox(shape), 'mask': False})

    # Count only the reserved bottom-side heat spreaders immediately beside
    # R2. Remote planes and copper linked by long traces are not credited.
    r2_spreaders = []
    r2 = footprints.get('R2')
    if r2:
        center = r2.GetPosition()
        reserved = [mm(center.x) - 11, mm(center.y) - 8,
                    mm(center.x) + 11, mm(center.y) + 8]
        for pad in r2.Pads():
            for zone in b.Zones():
                if (zone.GetIsRuleArea() or zone.GetNetname() != pad.GetNetname()
                        or not zone.IsOnLayer(p.B_Cu) or not zone.HasFilledPolysForLayer(p.B_Cu)):
                    continue
                shape = zone.GetFilledPolysList(p.B_Cu)
                bb = bbox(shape)
                if not shape.Collide(pad.GetPosition()):
                    continue
                if any(bb[i] < reserved[i] - EPS for i in (0, 1)) or any(bb[i] > reserved[i] + EPS for i in (2, 3)):
                    continue
                override = pad.GetLocalZoneConnection()
                connection = zone.GetPadConnection() if override == p.ZONE_CONNECTION_INHERITED else override
                solid = connection == p.ZONE_CONNECTION_FULL
                record = {'pin': pad.GetNumber(), 'net': pad.GetNetname(),
                          'zone_uuid': str(zone.m_Uuid.AsString()), 'layer': 'B.Cu',
                          'bounds_mm': bb, 'filled_area_mm2': shape.Area() / 1e12,
                          'filled_outer_components': shape.OutlineCount(), 'solid_pad_connection': solid}
                r2_spreaders.append(record)
                if not solid or shape.OutlineCount() != 1:
                    unqualified.append({'issue': 'R2 local spreader needs one connected fill and solid pad connection', 'item': record})
        if len(r2_spreaders) != 2 or {s['pin'] for s in r2_spreaders} != {'1', '2'}:
            unqualified.append({'issue': 'R2 two local heat-spreader fills are not identified', 'spreader_count': len(r2_spreaders)})
    r2_area = sum(s['filled_area_mm2'] for s in r2_spreaders)
    if r2_area + EPS < 300:
        unqualified.append({'issue': 'R2 local heat-spreader area below 300 mm2', 'actual_mm2': r2_area})

    # Audit every drill against actual pad copper and its expanded mask opening.
    # This includes drilled footprint pads, which are not PCB_VIA objects.
    overlaps = {'copper': [], 'mask_opening': []}
    for hole in all_holes:
        radius = max(hole['drill_mm']) / 2
        for pad in smd:
            for category, margin in [('copper', 0), ('mask_opening', pad['mask_expansion'])]:
                if category == 'mask_opening' and not pad['mask']:
                    continue
                if pad['_shape'].Collide(hole['_pos'], p.FromMM(radius + margin)):
                    overlaps[category].append({'hole': {k: v for k, v in hole.items() if not k.startswith('_')},
                                               'pad': label(pad)})

    layer_gaps = {b.GetLayerName(layer): closest_domains(
        [item for item in copper if item['layer'] == b.GetLayerName(layer)])
        for layer in layers}
    projected_gap = closest_domains(copper)
    if projected_gap['gap_mm'] + EPS < LIMITS['live_selv']:
        issue('all_layer_projected_live_selv', projected_gap['gap_mm'], LIMITS['live_selv'],
              a=projected_gap['live'], b=projected_gap['isolated'])

    if dual:
        field = [o for o in copper if o['net'] in FIELD_CONTACTS]
        board_mains = [o for o in copper if o['domain'] == 'LIVE' and o['net'] not in FIELD_CONTACTS]
        field_gap = closest_groups(field, board_mains, 'starter_contact', 'board_mains')
        if field_gap['gap_mm'] + EPS < LIMITS['live_selv']:
            issue('all_layer_projected_starter_field_to_board_mains', field_gap['gap_mm'],
                  LIMITS['live_selv'], a=field_gap['starter_contact'], b=field_gap['board_mains'])

    # Bounded sweep: every skipped pair has a bounding-box separation already
    # larger than the applicable rule. Detailed shape clearance covers curves,
    # rounded rectangles and stored filled zones using KiCad native geometry.
    pair_counts = Counter()
    for layer in layers:
        objects = sorted([o for o in copper if o['layer'] == b.GetLayerName(layer)], key=lambda o: o['_bbox'][0])
        for i, a in enumerate(objects):
            for other in objects[i + 1:]:
                if other['_bbox'][0] > a['_bbox'][2] + LIMITS['live_selv']:
                    break
                if a['uuid'] == other['uuid']:
                    continue
                requirement = required_clearance(a, other)
                if requirement:
                    rule, gap = requirement
                    if boxgap(a['_bbox'], other['_bbox']) <= gap + EPS:
                        actual = mm(a['_shape'].GetClearance(other['_shape']))
                        pair_counts[rule] += 1
                        if actual + EPS < gap:
                            issue(rule, actual, gap, a=label(a), b=label(other))
                if a['kind'] == other['kind'] == 'smd_pad' and a['mask'] and other['mask']:
                    # Multiple primitives for the same physical pin may be a
                    # single intentional land. All other merged openings are
                    # surfaced, including same-net but distinct terminals.
                    if a['id'] != other['id']:
                        needed = a['mask_expansion'] + other['mask_expansion'] + LIMITS['mask_web']
                        if boxgap(a['_bbox'], other['_bbox']) <= needed + EPS:
                            copper_gap = mm(a['_shape'].GetClearance(other['_shape']))
                            web = copper_gap - a['mask_expansion'] - other['mask_expansion']
                            pair_counts['mask_web'] += 1
                            if web + EPS < LIMITS['mask_web']:
                                issue('mask_web', web, LIMITS['mask_web'], a=label(a), b=label(other))

    for i, a in enumerate(all_holes):
        for other in all_holes[i + 1:]:
            distance = math.dist(a['xy_mm'], other['xy_mm']) - max(a['drill_mm']) / 2 - max(other['drill_mm']) / 2
            gap, rule = None, None
            if a['net'] != other['net'] or not a['net'] or not other['net']:
                gap, rule = LIMITS['different_net_holes'], 'different_net_holes'
            elif a['kind'] == other['kind'] == 'via':
                gap, rule = LIMITS['same_net_via_holes'], 'same_net_via_holes'
            if gap is not None and distance + EPS < gap:
                issue(rule, distance, gap, a={k: v for k, v in a.items() if not k.startswith('_')},
                      b={k: v for k, v in other.items() if not k.startswith('_')})
        key = {'via': 'via_track_hole', 'pth': 'pth_track_hole', 'npth': 'npth_track_hole'}[a['kind']]
        for tr in (c for c in copper if c['kind'] == 'track'):
            if a['net'] and a['net'] == tr['net']:
                continue
            hx, hy = a['xy_mm']
            radius = max(a['drill_mm']) / 2
            if boxgap((hx, hy, hx, hy), tr['_bbox']) > radius + LIMITS[key] + EPS:
                continue
            clearance = mm(tr['_shape'].Distance(a['_pos'])) - radius
            if clearance + EPS < LIMITS[key]:
                issue(key, clearance, LIMITS[key], hole={k: v for k, v in a.items() if not k.startswith('_')},
                      track=label(tr))

    expected_reference_domains = {'In1.Cu': {'GND', 'M_GND'}, 'In4.Cu': {'+3V3', 'M_GND'}}
    for layer, expected_nets in expected_reference_domains.items():
        actual_nets = {z['net'] for z in inventory['zones'] if z['layer'] == layer and z['filled']}
        if actual_nets != expected_nets:
            violations.append({'rule': 'reference_plane_net_domains', 'layer': layer,
                               'expected_nets': sorted(expected_nets), 'actual_nets': sorted(actual_nets)})

    mounting_targets = {(4.0, 4.0), (96.0, 4.0), (96.0, 76.0), (4.0, 76.0)}
    if compact:
        mounting_targets = {(16.0, 8.8), (96.0, 8.8), (96.0, 76.0), (4.0, 76.0)}
    if dual:
        mounting_targets = {(4.0, -13.0), (50.0, -12.8), (96.0, -13.0),
                            (96.0, 76.0), (4.0, 76.0)}
    mounting = [h for h in all_holes if h.get('ref') and re.fullmatch(r'H\d+', h['ref'])]
    actual_mounting = {tuple(h['xy_mm']) for h in mounting}
    if actual_mounting != mounting_targets:
        source_issues.append({'issue': 'Rev E mounting-hole centers differ',
                              'expected_mm': sorted(mounting_targets), 'actual_mm': sorted(actual_mounting)})
    for hole in mounting:
        if hole['plated'] or any(abs(d - 3.2) > EPS for d in hole['drill_mm']):
            source_issues.append({'issue': 'Rev E mounting hole must be 3.2 mm NPTH',
                                  'ref': hole['ref']})
        for item in copper:
            clearance = mm(item['_shape'].Distance(hole['_pos']))
            if clearance + EPS < 4.2:
                issue('mounting_copper_keepout_radius', clearance, 4.2,
                      mounting_hole=hole['ref'], item=label(item))

    # Outline and edge checks are for a closed axis-aligned rectangular board;
    # a future nonrectangular profile is explicitly rejected, not approximated.
    ends = []
    for g in b.GetDrawings():
        if g.GetLayer() == p.Edge_Cuts:
            if not isinstance(g, p.PCB_SHAPE) or g.GetShape() != p.SHAPE_T_SEGMENT:
                unqualified.append({'issue': 'nonrectangular outline requires explicit audit'})
                continue
            ends += [(mm(g.GetStart().x), mm(g.GetStart().y)), (mm(g.GetEnd().x), mm(g.GetEnd().y))]
    outline = None
    if ends:
        counts = Counter(ends)
        xs, ys = {x[0] for x in ends}, {x[1] for x in ends}
        if len(xs) == len(ys) == 2 and len(counts) == 4 and set(counts.values()) == {2}:
            outline = [min(xs), min(ys), max(xs), max(ys)]
            source_board = source.get('board', {})
            source_size = [source_board.get('width'), source_board.get('height')]
            actual_size = [outline[2] - outline[0], outline[3] - outline[1]]
            if None not in source_size and source_size != actual_size:
                source_issues.append({'issue': 'outline dimensions differ from source',
                                      'expected_mm': source_size, 'actual_mm': actual_size})
            for obj in copper:
                bb = obj['_bbox']
                edge = min(bb[0] - outline[0], bb[1] - outline[1], outline[2] - bb[2], outline[3] - bb[3])
                if edge + EPS < LIMITS['copper_edge']:
                    issue('copper_edge', edge, LIMITS['copper_edge'], item=label(obj))
        else:
            unqualified.append({'issue': 'outline is not a closed rectangle'})
    else:
        unqualified.append({'issue': 'outline absent'})

    graphics = list(b.GetDrawings())
    for f in footprints.values():
        graphics.extend(f.GraphicalItems())
        graphics.extend(f.GetFields())
    seen_graphics = set()
    for g in graphics:
        uuid = str(g.m_Uuid.AsString())
        if uuid in seen_graphics:
            continue
        seen_graphics.add(uuid)
        layer = g.GetLayer()
        if p.IsCopperLayer(layer):
            inventory['copper_graphics'].append({'uuid': uuid, 'layer': b.GetLayerName(layer)})
            unqualified.append({'issue': 'copper graphic/text needs explicit domain and connectivity review', 'uuid': uuid})
        if layer not in (p.F_SilkS, p.B_SilkS):
            continue
        if isinstance(g, p.PCB_TEXT):
            if not g.IsVisible():
                continue
            inv = {'uuid': uuid, 'text': g.GetText(), 'side': b.GetLayerName(layer),
                   'height_mm': mm(g.GetTextSize().y), 'stroke_mm': mm(g.GetTextThickness())}
            inventory['silk'].append(inv)
            if inv['height_mm'] + EPS < LIMITS['silk_height']:
                issue('silk_height', inv['height_mm'], LIMITS['silk_height'], item=inv)
            if inv['stroke_mm'] + EPS < LIMITS['silk_stroke']:
                issue('silk_stroke', inv['stroke_mm'], LIMITS['silk_stroke'], item=inv)
        elif isinstance(g, p.PCB_SHAPE):
            inv = {'uuid': uuid, 'side': b.GetLayerName(layer), 'stroke_mm': mm(g.GetWidth())}
            inventory['silk'].append(inv)
            if inv['stroke_mm'] + EPS < LIMITS['silk_stroke']:
                issue('silk_stroke', inv['stroke_mm'], LIMITS['silk_stroke'], item=inv)

    # Silkscreen-to-mask registration is also checked by native DRC and final
    # CAM review. This geometry audit does not replace the font outline engine.
    domain_issues = list({json.dumps(x, sort_keys=True): x for x in domain_issues}.values())
    unqualified = list({json.dumps(x, sort_keys=True): x for x in unqualified}.values())
    project = json.loads(board_path.with_suffix('.kicad_pro').read_text())
    exclusions = project.get('board', {}).get('design_settings', {}).get('drc_exclusions', [])
    if exclusions:
        unqualified.append({'issue': 'project contains DRC exclusions', 'count': len(exclusions)})
    if sha(board_path) != before:
        raise SystemExit('Board changed while reading it; discard this audit and rerun.')
    result = {
        'pcb_sha256': before, 'source_sha256': sha(source_path),
        'project_sha256': sha(board_path.with_suffix('.kicad_pro')),
        'rules_sha256': sha(board_path.with_suffix('.kicad_dru')),
        'limits_mm': LIMITS, 'rounding_epsilon_mm': EPS,
        'method': 'Native effective copper geometry and drill disks; read-only; no source refill/save.',
        'outline_bounds_mm': outline,
        'outline_size_mm': [outline[2] - outline[0], outline[3] - outline[1]] if outline else None,
        'copper_layers': [b.GetLayerName(layer) for layer in layers],
        'source_component_count': len(components), 'connected_source_pins_checked': connected_pins,
        'source_pins': source_pins, 'source_issues': source_issues,
        'source_and_native_netlist_compared': sch_nets is not None,
        'isolation_domain_issues': domain_issues, 'unqualified_geometry': unqualified,
        'inventory': inventory,
        'r2_local_heat_spreader': {'combined_filled_area_mm2': r2_area,
                                   'minimum_required_mm2': 300, 'spreaders': r2_spreaders,
                                   'remote_plane_area_counted': False,
                                   'thermal_performance_verified': False},
        'holes': [{k: v for k, v in h.items() if not k.startswith('_')} for h in all_holes],
        'smt_drill_overlaps': overlaps,
        'live_to_isolated_nominal_copper': {
            'same_layer': layer_gaps, 'all_layers_projected_to_xy': projected_gap,
            'scope': 'Native copper, filled planes, pads and vias. The XY projection ignores layer depth. '
                     'Measurements exclude populated component bodies, screws, wires, air paths around '
                     'the board edge, material ratings, production tolerances and contamination.'},
        'clearance_pairs_measured': dict(pair_counts), 'violations': violations,
        'geometry_and_source_passed': not (violations or source_issues or domain_issues or unqualified
                                          or overlaps['copper'] or overlaps['mask_opening']),
        'manufacturer_accepted': False, 'hardware_tested': False, 'release_ready': False,
        'limitations': [
            'Dimensions are nominal; drill/registration/material tolerances need manufacturer acceptance.',
            'Final Gerber mask-opening merges and font clearance are checked separately.',
            'No simulation, functional hardware, thermal, EMC or installation test is implied.',
        ],
    }
    if dual:
        result['starter_field_to_board_mains_projected'] = field_gap
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['geometry_and_source_passed'],
                      'violations': dict(Counter(v['rule'] for v in violations)),
                      'source_issues': len(source_issues), 'domain_issues': len(domain_issues),
                      'unqualified_geometry': len(unqualified),
                      'drill_smt_copper_overlaps': len(overlaps['copper']),
                      'drill_smt_mask_overlaps': len(overlaps['mask_opening'])}, indent=2))
    return 0 if result['geometry_and_source_passed'] else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=BASE / 'hardware/main-rev-e/pump-controller-main-rev-e.kicad_pcb')
    ap.add_argument('--source', type=Path, default=BASE / 'design/main-rev-e.json')
    ap.add_argument('--netlist', type=Path)
    ap.add_argument('--output', type=Path, default=BASE / 'hardware/main-rev-e/checks/independent-geometry.json')
    raise SystemExit(audit(ap.parse_args()))
