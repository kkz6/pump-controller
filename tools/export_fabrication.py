#!/usr/bin/env python3
"""Export the frozen Rev C board for Robu CAM review, without editing CAD.

This creates review data, never a production release or manufacturing order.
KiCad 10, its Python bindings, and the checked-in project libraries are required.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'hardware/fabrication/rev-c'
BOARD = BASE / 'hardware/pump-controller-rev-b.kicad_pcb'
SCHEMATIC = BOARD.with_suffix('.kicad_sch')
CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or str(BASE / '.tools/kicad-cli')
PYTHON = os.environ.get('KICAD_PYTHON') or str(BASE / '.tools/kicad-python')
NAME = 'pump-controller-rev-c'
LAYER_MAP = {
    'F_Cu': ('GTL', 'Copper,L1,Top'),
    'In1_Cu': ('G2L', 'Copper,L2,Inr'),
    'In2_Cu': ('G3L', 'Copper,L3,Inr'),
    'B_Cu': ('GBL', 'Copper,L4,Bot'),
    'F_Mask': ('GTS', 'Soldermask,Top'),
    'B_Mask': ('GBS', 'Soldermask,Bot'),
    'F_Silkscreen': ('GTO', 'Legend,Top'),
    'B_Silkscreen': ('GBO', 'Legend,Bot'),
    'Edge_Cuts': ('GKO', 'Profile,NP'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args, allowed=(0,)):
    result = subprocess.run([str(x) for x in args], cwd=BASE, capture_output=True, text=True)
    if result.returncode not in allowed:
        raise RuntimeError(result.stdout + result.stderr)
    print(result.stdout.strip())
    return result.returncode


sources = [BOARD, SCHEMATIC, BOARD.with_suffix('.kicad_pro'), BOARD.with_suffix('.kicad_dru'),
           BASE / 'design/circuit.json']
before = {str(p.relative_to(BASE)): sha(p) for p in sources}
for directory in ['board', 'stencil', 'drill-maps', 'checks']:
    (OUT / directory).mkdir(parents=True, exist_ok=True)

run(CLI, 'sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations',
    '-o', OUT / 'checks/erc.json', SCHEMATIC)
run(CLI, 'pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors',
    '--schematic-parity', '--exit-code-violations',
    '-o', OUT / 'checks/drc-with-parity.json', BOARD, allowed=(0, 5))
drc = json.loads((OUT / 'checks/drc-with-parity.json').read_text())
if drc['violations'] or drc['unconnected_items']:
    raise SystemExit('Native layout DRC failed; no new Gerbers exported.')
run(CLI, 'sch', 'export', 'netlist', '--format', 'kicadxml',
    '-o', OUT / 'checks/schematic-netlist.xml', SCHEMATIC)
run(PYTHON, BASE / 'tools/inspect_fabrication_source.py',
    '--netlist', OUT / 'checks/schematic-netlist.xml',
    '--output', OUT / 'checks/source-and-drills.json')
native = json.loads((OUT / 'checks/source-and-drills.json').read_text())

# The raw parity result is retained in full. Do not suppress metadata or
# no-connect findings simply to present an unqualified pass.
parity_counts = Counter(v['type'] for v in drc['schematic_parity'])
check_summary = {
    'source_sha256': before,
    'erc_violations': sum(len(sheet['violations']) for sheet in
                          json.loads((OUT / 'checks/erc.json').read_text())['sheets']),
    'layout_drc_violations': len(drc['violations']),
    'unconnected_items': len(drc['unconnected_items']),
    'native_schematic_parity_issue_count': len(drc['schematic_parity']),
    'native_schematic_parity_issue_types': dict(parity_counts),
    'native_schematic_parity_passed': not drc['schematic_parity'],
    'source_connectivity_passed': native['board_and_schematic_match_source'],
    'component_count': native['component_count'],
    'connected_schematic_pins_checked': native['connected_schematic_pins_checked'],
    'release_ready': False,
}
(OUT / 'checks/summary.json').write_text(json.dumps(check_summary, indent=2) + '\n')

with tempfile.TemporaryDirectory(prefix='pump-gerber-') as temp:
    raw = Path(temp)
    run(CLI, 'pcb', 'export', 'gerbers', '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',
        '--subtract-soldermask', '--precision', '6', '-o', str(raw / 'board') + '/', BOARD)
    rename = {}
    for layer, (ext, function) in LAYER_MAP.items():
        candidates = [p for p in (raw / 'board').iterdir() if p.stem.endswith('-' + layer)]
        if len(candidates) != 1:
            raise RuntimeError('Cannot identify exported layer ' + layer)
        source = candidates[0]
        data = source.read_text()
        if f'%TF.FileFunction,{function}*%' not in data:
            raise RuntimeError('Wrong X2 layer function for ' + layer)
        dest = OUT / 'board' / (NAME + '.' + ext)
        shutil.copyfile(source, dest)
        rename[source.name] = dest.name
    job = json.loads(next((raw / 'board').glob('*.gbrjob')).read_text())
    for item in job['FilesAttributes']:
        item['Path'] = rename[item['Path']]
    (OUT / 'board' / (NAME + '.gbrjob')).write_text(json.dumps(job, indent=2) + '\n')
    run(CLI, 'pcb', 'export', 'gerbers', '--layers', 'F.Paste,B.Paste',
        '--precision', '6', '-o', str(raw / 'stencil') + '/', BOARD)
    for layer, ext in [('F_Paste', 'GTP'), ('B_Paste', 'GBP')]:
        source = next(p for p in (raw / 'stencil').iterdir() if p.stem.endswith('-' + layer))
        shutil.copyfile(source, OUT / 'stencil' / (NAME + '.' + ext))
    run(CLI, 'pcb', 'export', 'drill', '--format', 'excellon',
        '--drill-origin', 'absolute', '--excellon-units', 'mm',
        '--excellon-zeros-format', 'decimal', '--excellon-separate-th',
        '--generate-map', '--map-format', 'svg', '--generate-report',
        '--report-path', OUT / 'drill-maps/drill-report.txt',
        '-o', str(raw / 'drills') + '/', BOARD)
    for source in (raw / 'drills').iterdir():
        if source.suffix == '.drl':
            kind = 'NPTH' if 'NPTH' in source.stem else 'PTH'
            shutil.copyfile(source, OUT / 'board' / (NAME + '-' + kind + '.XLN'))
        elif source.suffix == '.svg':
            shutil.copyfile(source, OUT / 'drill-maps' / source.name.replace(BOARD.stem, NAME))
    run(CLI, 'pcb', 'export', 'ipcd356', '-o', OUT / 'board' / (NAME + '.d356'), BOARD)

after = {str(p.relative_to(BASE)): sha(p) for p in sources}
if after != before:
    raise SystemExit('Source files changed during export; discard this package and review.')
manifest = {
    'revision': 'C', 'purpose': 'Robu CAM review only', 'release_ready': False,
    'native_board_unchanged': True, 'source_sha256': before,
    'units': 'mm', 'gerber_coordinate_precision': '4.6',
    'origin': 'absolute KiCad board origin, identical for Gerbers and Excellon',
    'mirrored': False, 'copper_layer_order': ['GTL', 'G2L', 'G3L', 'GBL'],
    'outline_size_mm': [90, 70], 'board_thickness_mm': native['board_thickness_mm'],
    'plated_holes': native['plated_holes'], 'nonplated_holes': native['nonplated_holes'],
    'source_has_explicit_stackup': False,
    'requested_outer_copper_oz': 1, 'requested_inner_copper_oz': 0.5,
    'requested_finish': 'ENIG', 'requested_material': 'FR4 Tg155',
    'stackup_material_and_finish_accepted': False,
    'via_in_pad_process_confirmed': False,
    'output_sha256': {str(p.relative_to(OUT)): sha(p) for directory in ['board', 'stencil', 'drill-maps']
                      for p in sorted((OUT / directory).iterdir()) if p.is_file()},
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Review export complete. Source unchanged. Manufacturer compatibility is not approved.')
