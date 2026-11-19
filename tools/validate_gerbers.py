#!/usr/bin/env python3
"""Parse the review CAM files independently and compare drills/nets to source.

Requires Python >=3.10 and gerbonara==0.13.0. Does not alter native PCB, CAM data, or rules.
This is a serialization/registration check, not conductive CAM extraction.
"""
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import warnings

from gerbonara import ExcellonFile, GerberFile
from gerbonara.graphic_objects import Flash, Line
from gerbonara.ipc356 import Netlist
from gerbonara.layers import LayerStack
from gerbonara.utils import MM

if sys.version_info < (3, 10):
    raise SystemExit('Use Python 3.10 or newer for Gerbonara SVG generation.')

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'hardware/fabrication/rev-c'
PREVIEW = BASE / 'output/gerber/previews'
NAME = 'pump-controller-rev-c'
BOARD = BASE / 'hardware/pump-controller-rev-b.kicad_pcb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(BOARD)
native = json.loads((OUT / 'checks/source-and-drills.json').read_text())
if native['pcb_sha256'] != before:
    raise SystemExit('Native inventory is stale; regenerate the review export.')

errors, parser_warnings = [], []
functions = {
    'GTL': ('Copper,L1,Top', ('top', 'copper')),
    'G2L': ('Copper,L2,Inr', ('inner1', 'copper')),
    'G3L': ('Copper,L3,Inr', ('inner2', 'copper')),
    'GBL': ('Copper,L4,Bot', ('bottom', 'copper')),
    'GTS': ('Soldermask,Top', ('top', 'mask')),
    'GBS': ('Soldermask,Bot', ('bottom', 'mask')),
    'GTO': ('Legend,Top', ('top', 'silk')),
    'GBO': ('Legend,Bot', ('bottom', 'silk')),
    'GKO': ('Profile,NP', ('mechanical', 'outline')),
    'GTP': ('Paste,Top', ('top', 'paste')),
    'GBP': ('Paste,Bot', ('bottom', 'paste')),
}
parsed, layers, files = {}, {}, {}
for ext, (function, key) in functions.items():
    path = OUT / ('stencil' if ext in ('GTP', 'GBP') else 'board') / (NAME + '.' + ext)
    contents = path.read_text()
    if '%TF.FileFunction,' + function + '*%' not in contents:
        errors.append('Unexpected X2 layer role: ' + ext)
    if '%MOMM*%' not in contents:
        errors.append('Gerber units are not mm: ' + ext)
    if '%FSLAX46Y46*%' not in contents:
        errors.append('Unexpected Gerber coordinate format: ' + ext)
    if not contents.rstrip().endswith('M02*'):
        errors.append('Gerber missing end marker: ' + ext)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        warnings.simplefilter('ignore', DeprecationWarning)
        gerber = GerberFile.open(path)
    parser_warnings.extend({'file': path.name, 'message': str(w.message)} for w in caught)
    parsed[ext] = gerber
    layers[key] = gerber
    files[str(path.relative_to(OUT))] = {
        'sha256': sha(path), 'objects': len(gerber.objects),
        'bounds_mm': gerber.bounding_box(unit=MM), 'layer_function': function,
    }

# Edge.Cuts stroke width is not part of finished board size. Compare line
# centerlines and verify a single closed rectangular contour.
outline = parsed['GKO']
ends = []
for obj in outline.objects:
    if not isinstance(obj, Line):
        errors.append('Unexpected non-line object in rectangular outline')
        continue
    ends.extend([(MM(obj.x1, obj.unit), MM(obj.y1, obj.unit)),
                 (MM(obj.x2, obj.unit), MM(obj.y2, obj.unit))])
if not ends:
    raise SystemExit('No outline endpoints found.')
x0, x1 = min(p[0] for p in ends), max(p[0] for p in ends)
y0, y1 = min(p[1] for p in ends), max(p[1] for p in ends)
size = [round(x1 - x0, 6), round(y1 - y0, 6)]
corners = Counter((round(x, 6), round(y, 6)) for x, y in ends)
if size != [90, 70] or len(corners) != 4 or set(corners.values()) != {2}:
    errors.append('Outline is not the expected closed 90 x 70 mm rectangle')
bounds = ((x0, y0), (x1, y1))

# Both files use the absolute origin. KiCad page Y is down; Gerber/Excellon
# Cartesian Y is up. This known sign conversion is applied, never fitted.
drills, drill_checks = [], {}
for kind, plated in [('PTH', True), ('NPTH', False)]:
    path = OUT / 'board' / (NAME + '-' + kind + '.XLN')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        warnings.simplefilter('ignore', DeprecationWarning)
        drill = ExcellonFile.open(path, plated=plated)
    parser_warnings.extend({'file': path.name, 'message': str(w.message)} for w in caught)
    actual = []
    for obj in drill.objects:
        if not isinstance(obj, Flash):
            errors.append('Unexpected slot/route in round-hole-only drill file ' + kind)
            continue
        actual.append((MM(obj.x, obj.unit), MM(obj.y, obj.unit),
                       MM(obj.aperture.diameter, obj.aperture.unit)))
    expected = [(h['xy_mm'][0], -h['xy_mm'][1], h['drill_mm'][0])
                for h in native['holes'] if h['plated'] == plated]
    # KiCad's decimal Excellon writer emits 0.001 mm coordinates. Match each
    # hit once, within half a quantization step plus floating-point epsilon.
    remaining = actual.copy()
    missing, max_coordinate_error = [], 0.0
    for expected_hit in expected:
        match = next((i for i, hit in enumerate(remaining)
                      if abs(hit[0] - expected_hit[0]) <= 0.000501
                      and abs(hit[1] - expected_hit[1]) <= 0.000501
                      and abs(hit[2] - expected_hit[2]) <= 0.000001), None)
        if match is None:
            missing.append(expected_hit)
        else:
            hit = remaining.pop(match)
            max_coordinate_error = max(max_coordinate_error,
                                       abs(hit[0] - expected_hit[0]),
                                       abs(hit[1] - expected_hit[1]))
    extra = remaining
    if missing or extra:
        errors.append('Drill coordinates/diameters differ from native inventory: ' + kind)
    drill_checks[kind] = {'count': len(actual), 'expected': len(expected),
                          'missing': missing, 'extra': extra,
                          'coordinate_tolerance_mm': 0.000501,
                          'max_coordinate_rounding_error_mm': round(max_coordinate_error, 9),
                          'nominal_diameters_mm': sorted({p[2] for p in actual})}
    drills.append(drill)
    files[str(path.relative_to(OUT))] = {'sha256': sha(path), 'hits': len(drill.objects)}

ipc_path = OUT / 'board' / (NAME + '.d356')
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    warnings.simplefilter('ignore', DeprecationWarning)
    ipc = Netlist.open(ipc_path)
parser_warnings.extend({'file': ipc_path.name, 'message': str(w.message)} for w in caught)
aliases = dict(re.findall(r'^P\s+NNAME(\S+)\s+(\S+)\s*$', ipc_path.read_text(), re.MULTILINE))
source = json.loads((BASE / 'design/circuit.json').read_text())
expected_pins = {(c['ref'], str(pin['num'])): pin.get('net') or ''
                 for sheet in source['sheets'] for c in sheet['components']
                 if c.get('on_board', True) for pin in c['pins']}
ipc_pins = {}
for record in ipc.test_records:
    if record.ref_des and record.ref_des not in ('H1', 'H2'):
        # gerbonara 0.13 parser stores the decoded field in .pin.
        pin = str(getattr(record, 'pin', record.pin_num))
        net = aliases.get(record.net_name, record.net_name) or ''
        ipc_pins.setdefault((record.ref_des, pin), set()).add(net)
pin_differences = []
for key, expected in expected_pins.items():
    actual = ipc_pins.get(key, set())
    if expected:
        if actual != {expected}:
            pin_differences.append({'ref': key[0], 'pin': key[1],
                                    'expected': expected, 'actual': sorted(actual)})
    elif actual - {'', 'N/C'}:
        pin_differences.append({'ref': key[0], 'pin': key[1],
                                'expected': 'unconnected', 'actual': sorted(actual)})
unexpected = sorted(set(ipc_pins) - set(expected_pins))
if pin_differences or unexpected:
    errors.append('IPC-D-356 pin/net assignments differ from electrical source')
files[str(ipc_path.relative_to(OUT))] = {'sha256': sha(ipc_path), 'records': len(ipc.test_records)}

job_path = OUT / 'board' / (NAME + '.gbrjob')
job = json.loads(job_path.read_text())
job_paths = [entry['Path'] for entry in job['FilesAttributes']]
expected_job_paths = [NAME + '.' + e for e in functions if e not in ('GTP', 'GBP')]
if sorted(job_paths) != sorted(expected_job_paths):
    errors.append('Gerber job file does not identify exactly the nine board Gerbers')
files[str(job_path.relative_to(OUT))] = {'sha256': sha(job_path)}

PREVIEW.mkdir(parents=True, exist_ok=True)
stack = LayerStack(layers, drills, netlist=ipc, board_name=NAME)
for side in ['top', 'bottom']:
    # Keep both sides in common manufacturing coordinates; do not mirror.
    svg = stack.to_pretty_svg(side=side, margin=1, force_bounds=bounds)
    (PREVIEW / (side + '-registration.svg')).write_text(str(svg))
for ext, name in [('GTL', 'copper-L1'), ('G2L', 'copper-L2'),
                  ('G3L', 'copper-L3'), ('GBL', 'copper-L4')]:
    (PREVIEW / (name + '.svg')).write_text(str(parsed[ext].to_svg(
        margin=1, force_bounds=bounds, fg='#8a4b08', bg='#ffffff')))

if sha(BOARD) != before:
    errors.append('Native board changed during validation')
result = {
    'pcb_sha256': before,
    'parser': 'gerbonara', 'parser_version': importlib.metadata.version('gerbonara'),
    'python_version': sys.version.split()[0],
    'gerber_files_parsed': len(parsed), 'outline_centerline_size_mm': size,
    'outline_bounds_mm': bounds, 'outline_endpoint_degrees': list(corners.values()),
    'drills': drill_checks,
    'ipc_d356': {'records': len(ipc.test_records),
                 'long_net_name_aliases_resolved': aliases,
                 'connected_source_pins_checked': sum(bool(v) for v in expected_pins.values()),
                 'pin_net_differences': pin_differences, 'unexpected_pins': unexpected},
    'file_checks': files,
    'parser_warnings': [{**w, 'message': w['message'].replace(str(BASE) + '/', '')}
                       for w in parser_warnings],
    'parser_warning_review': 'Two KiCad Excellon G90 commands occur after the header; all 383 drill hits still parse and register against native coordinates.',
    'preview_svg_sha256': {p.name: sha(p) for p in sorted(PREVIEW.glob('*.svg'))},
    'serialization_and_registration_passed': not errors, 'errors': errors,
    'gerber_conductive_netlist_extracted': False,
    'fabricated_board_electrical_tested': False, 'manufacturer_dfm_accepted': False,
    'release_ready': False,
    'limitations': [
        'IPC-D-356 is generated from the native board; it does not independently prove Gerber conductive connectivity.',
        'No manufactured board has been electrically tested.',
        'Robu process/spacing/annular-ring/via-in-pad requirements remain unresolved.',
        'Preview SVGs use common unmirrored manufacturing coordinates on both sides.',
    ],
}
(OUT / 'checks/gerber-validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'passed': not errors, 'errors': errors, 'warnings': len(parser_warnings),
                  'gerbers': len(parsed),
                  'drill_counts': {k: v['count'] for k, v in drill_checks.items()},
                  'ipc_source_pin_differences': len(pin_differences)}, indent=2))
if errors:
    raise SystemExit(1)
