#!/usr/bin/env python3
"""Add Schmitt conditioning to the Rev E ARM clear input, preserving other CAD.

Use --source once (idempotent) and --board PATH on a placed/routed board.
The board patch removes only SAFE_CLEAR_N routing, which must be reconnected
with the new ARM_CLEAR_N net. It does not claim a finished or checked layout.
"""
from pathlib import Path
import argparse
import copy
import json
import re
import os
import generate_cad as cad
from patch_main_rev_e_bias import expression_ranges

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'hardware/main-rev-e'
PROJECT = 'pump-controller-main-rev-e'


def additions():
    return [
        {'ref': 'U36', 'value': 'SN74LVC1G17DBVR', 'mpn': 'SN74LVC1G17DBVR',
         'kind': 'ic', 'footprint': 'Package_TO_SOT_SMD:SOT-23-5',
         'description': 'Schmitt buffer converts the slow wired-OR clear release into a clean U31 CLR edge; input SAFE_CLEAR_N, output ARM_CLEAR_N.',
         'datasheet': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf',
         'placement': {'x': 82, 'y': 37.5, 'rotation': 0, 'side': 'B'},
         'pins': [{'num': '1', 'name': 'NC', 'net': None, 'type': 'no_connect'},
                  {'num': '2', 'name': 'A', 'net': 'SAFE_CLEAR_N', 'type': 'input'},
                  {'num': '3', 'name': 'GND', 'net': 'GND', 'type': 'power_in'},
                  {'num': '4', 'name': 'Y', 'net': 'ARM_CLEAR_N', 'type': 'output'},
                  {'num': '5', 'name': 'VCC', 'net': '+3V3', 'type': 'power_in'}]},
        {'ref': 'C77', 'value': '100nF', 'mpn': 'SPEC: 100nF X7R, 10%, 16V',
         'kind': 'capacitor', 'footprint': 'Capacitor_SMD:C_0603_1608Metric',
         'description': 'Local bypass for U36; connect directly between pins 5 and 3.',
         'datasheet': '',
         'placement': {'x': 85.5, 'y': 37.5, 'rotation': 90, 'side': 'B'},
         'pins': [{'num': '1', 'name': '1', 'net': '+3V3', 'type': 'passive'},
                  {'num': '2', 'name': '2', 'net': 'GND', 'type': 'passive'}]},
    ]


def apply_source(data):
    sheets = {sheet['id']: sheet for sheet in data['sheets']}
    parts = {c['ref']: c for s in data['sheets'] for c in s['components']}
    pin = next(pin for pin in parts['U31']['pins'] if str(pin['num']) == '6')
    if pin['net'] not in ('SAFE_CLEAR_N', 'ARM_CLEAR_N'):
        raise ValueError('Unexpected U31 CLR net')
    pin['net'] = 'ARM_CLEAR_N'
    for component in additions():
        if component['ref'] not in parts:
            sheets['relay_protection_2']['components'].append(component)
        elif parts[component['ref']] != component:
            raise ValueError('Conflicting existing safe-clear component ' + component['ref'])


def update_source_files():
    source = BASE / 'design/main-rev-e.json'
    data = json.loads(source.read_text())
    apply_source(data)
    source.write_text(json.dumps(data, indent=2) + '\n')
    sheet1 = OUT / 'relay_protection_1.kicad_sch'
    text = sheet1.read_text()
    uid = cad.uid('label:U31:5')
    matches = [(a, b) for a, b in expression_ranges(text)
               if text[a:b].startswith('(global_label ') and f'(uuid "{uid}")' in text[a:b]]
    assert len(matches) == 1
    a, b = matches[0]
    block = text[a:b]
    assert block.startswith('(global_label "SAFE_CLEAR_N"') or block.startswith('(global_label "ARM_CLEAR_N"')
    text = text[:a] + block.replace('(global_label "SAFE_CLEAR_N"', '(global_label "ARM_CLEAR_N"', 1) + text[b:]
    sheet1.write_text(text)
    sheet2 = next(sheet for sheet in data['sheets'] if sheet['id'] == 'relay_protection_2')
    root_id = cad.uid(PROJECT + ':root')
    hierarchy = '/' + root_id + '/' + cad.uid(PROJECT + ':sheet:relay_protection_2')
    file = OUT / 'relay_protection_2.kicad_sch'
    text = file.read_text()
    for component, x, y in cad.page_layout(sheet2['components']):
        if component['ref'] not in {'U36', 'C77'} or f'(lib_id "Pump:{component["ref"]}")' in text:
            continue
        start, end = next((a, b) for a, b in expression_ranges(text) if text[a:b].startswith('(lib_symbols'))
        text = text[:end - 1] + cad.symbol_definition(component) + '\n' + text[end - 1:]
        end = text.rfind(')')
        text = text[:end] + cad.instance(component, x, y, PROJECT, hierarchy) + '\n' + text[end:]
    file.write_text(text)
    library = OUT / 'Pump.kicad_sym'
    text = library.read_text()
    for component in additions():
        if f'(symbol "{component["ref"]}"' not in text:
            end = text.rfind(')')
            text = text[:end] + cad.symbol_definition(component, False) + '\n' + text[end:]
    library.write_text(text)
    cad.write_bom(data, OUT)
    project = OUT / (PROJECT + '.kicad_pro')
    settings = json.loads(project.read_text())
    patterns = settings['net_settings']['netclass_patterns']
    for name in ['ARM_CLEAR_N', 'unconnected-(U36-NC-Pad1)']:
        rule = {'netclass': 'SELV', 'pattern': name}
        if rule not in patterns:
            patterns.append(rule)
    project.write_text(json.dumps(settings, indent=2) + '\n')


def patch_board(path):
    import wx
    app = wx.GetApp() or wx.App(False)
    import pcbnew as p
    board = p.LoadBoard(str(path))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    added, removed = [], 0
    def net(name):
        found = board.FindNet(name)
        if found is None or found.GetNetCode() < 0:
            found = p.NETINFO_ITEM(board, name)
            board.Add(found)
        return found
    pin = next(pad for pad in footprints['U31'].Pads() if pad.GetNumber() == '6')
    changing_net = pin.GetNetname() != 'ARM_CLEAR_N'
    if changing_net:
        if pin.GetNetname() != 'SAFE_CLEAR_N':
            raise ValueError('Unexpected PCB U31 CLR net')
        for track in list(board.GetTracks()):
            if track.GetNetname() == 'SAFE_CLEAR_N':
                board.Remove(track)
                removed += 1
        pin.SetNet(net('ARM_CLEAR_N'))
    library_root = Path(os.environ['KICAD10_FOOTPRINT_DIR'])
    hierarchy = '/' + cad.uid(PROJECT + ':root') + '/' + cad.uid(PROJECT + ':sheet:relay_protection_2')
    for component in additions():
        ref = component['ref']
        if ref in footprints:
            continue
        lib, name = component['footprint'].split(':')
        footprint = p.FootprintLoad(str(library_root / (lib + '.pretty')), name)
        footprint.SetReference(ref)
        footprint.SetValue(component['value'])
        footprint.SetFPID(p.LIB_ID(lib, name))
        footprint.SetPath(p.KIID_PATH(hierarchy + '/' + cad.uid('component:' + ref)))
        for key in ['MPN', 'Description', 'Datasheet']:
            footprint.SetField(key, component.get(key.lower(), ''))
            footprint.GetField(key).SetVisible(False)
        board.Add(footprint)
        placement = component['placement']
        footprint.SetPosition(p.VECTOR2I(p.FromMM(placement['x']), p.FromMM(placement['y'])))
        footprint.Flip(footprint.GetPosition(), False)
        footprint.SetOrientationDegrees(placement['rotation'])
        mapping = {str(pin['num']): pin['net'] for pin in component['pins']}
        for pad in footprint.Pads():
            name = mapping[pad.GetNumber()] or f'unconnected-({ref}-NC-Pad{pad.GetNumber()})'
            pad.SetNet(net(name))
        footprint.Reference().SetVisible(False)
        footprint.Value().SetVisible(False)
        for graphic in footprint.GraphicalItems():
            if isinstance(graphic, p.PCB_SHAPE) and graphic.GetLayer() in [p.F_SilkS, p.B_SilkS]:
                graphic.SetLayer(p.B_Fab)
        added.append(ref)
        footprints[ref] = footprint
    board.SynchronizeNetsAndNetClasses(False)
    p.SaveBoard(str(path), board)
    return {'board': str(path), 'added': added, 'removed_raw_clear_tracks_or_vias': removed,
            'route_required': ['SAFE_CLEAR_N', 'ARM_CLEAR_N', '+3V3', 'GND'],
            'pins': {ref: {pad.GetNumber(): {'net': pad.GetNetname(),
                      'x': p.ToMM(pad.GetPosition().x), 'y': p.ToMM(pad.GetPosition().y)}
                      for pad in footprints[ref].Pads()} for ref in ['U36', 'C77', 'U31']}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--board', type=Path, action='append', default=[])
    args = parser.parse_args()
    if not args.source and not args.board:
        parser.error('Select --source and/or --board PATH')
    if args.source:
        update_source_files()
    print(json.dumps([patch_board(path.resolve()) for path in args.board], indent=2))
