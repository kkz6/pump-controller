#!/usr/bin/env python3
"""Update selected compact-main symbols from the component source without rearranging sheets.

Run from any directory. Pass references as positional arguments. For a new
instance, also pass --place REF X Y in schematic millimetres.
"""
import argparse
import json
from pathlib import Path
import re

import generate_cad as cad

BASE = Path(__file__).resolve().parents[1]
BOARD = BASE / 'hardware/main-compact-dual'
SOURCE = BASE / 'design/main-compact-dual.json'


def replace_definition(content, name, definition):
    start = re.search(r'^\(symbol ' + re.escape(cad.q(name)) + r'\n', content, re.MULTILINE)
    if start is None:
        return None
    end = content.index('\n)', start.end()) + 2
    return content[:start.start()] + definition + content[end:]


def update_component(sheet, library, component, project, coordinates):
    ref = component['ref']
    name = 'Pump:' + ref
    definition = cad.symbol_definition(component)
    updated = replace_definition(sheet, name, definition)
    symbol = re.compile(r'^\(symbol \(lib_id ' + re.escape(cad.q(name)) + r'\) \(at ([\d.-]+) ([\d.-]+) 0\)', re.MULTILINE)
    original = symbol.search(sheet)
    hierarchy = re.search(r'\(instances \(project ' + re.escape(cad.q(project)) + r' \(path "([^"]+)"', sheet)[1]
    if original:
        assert updated is not None
        sheet = updated
        original = symbol.search(sheet)
        x, y = coordinates or map(float, original.groups())
        marker = sheet.index('(instances (project ', original.end())
        end = sheet.index('\n', marker) + 1
        while sheet.startswith(('(wire ', '(global_label ', '(no_connect '), end):
            end = sheet.index('\n', end) + 1
        sheet = sheet[:original.start()] + cad.instance(component, x, y, project, hierarchy) + '\n' + sheet[end:]
    else:
        if updated or coordinates is None:
            raise ValueError(f'New symbol {ref} requires an explicit --place REF X Y')
        assert sheet.count('(lib_symbols\n') == 1
        sheet = sheet.replace('(lib_symbols\n', '(lib_symbols\n' + definition + '\n', 1)
        sheet = sheet.rstrip().removesuffix(')') + cad.instance(component, *coordinates, project, hierarchy) + '\n)\n'
    definition = cad.symbol_definition(component, False)
    library = replace_definition(library, ref, definition) or (library.rstrip().removesuffix(')') + definition + '\n)\n')
    return sheet, library


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('references', nargs='+')
    args.add_argument('--place', action='append', nargs=3, default=[], metavar=('REF', 'X', 'Y'))
    opts = args.parse_args()
    coordinates = {ref: (float(x), float(y)) for ref, x, y in opts.place}
    data = json.loads(SOURCE.read_text())
    owners = {c['ref']: (s['id'], c) for s in data['sheets'] for c in s['components']}
    libpath = BOARD / 'Pump.kicad_sym'
    library = libpath.read_text()
    for ref in opts.references:
        sheet_name, component = owners[ref]
        path = BOARD / (sheet_name + '.kicad_sch')
        sheet, library = update_component(path.read_text(), library, component, data['project'], coordinates.get(ref))
        path.write_text(sheet)
    libpath.write_text(library)
    cad.write_bom(data, BOARD)


if __name__ == '__main__':
    main()
