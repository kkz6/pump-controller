#!/usr/bin/env python3
"""Export current checked PCB bodies, rebuild enclosure and seal fit evidence.

The native PCB/project are read-only. --expected-board-sha256 is required so
this command cannot silently adopt a later board revision during release work.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'output/enclosure-rev-e'
MAIN = ROOT / 'hardware/main-rev-e'
BOARD = MAIN / 'pump-controller-main-rev-e.kicad_pcb'
PROVENANCE = ROOT / 'hardware/3d/rev-e-export-manifest.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def checked_sources(expected):
    if sha(BOARD) != expected:
        raise ValueError('Main PCB differs from the explicitly selected final revision')
    path = MAIN / 'checks/independent-summary.json'
    evidence = read(path)
    if not (evidence['independent_native_checks_passed'] is True
            and evidence['native_sources_unchanged'] is True
            and evidence['geometry_and_source_passed'] is True
            and evidence['isolation_negative_tests_passed'] is True
            and not evidence['critical_checks_ignored']
            and evidence['native_violation_counts'] == dict(erc=0, drc=0, unconnected=0, schematic_parity=0)):
        raise ValueError('Final independent native checks have not passed')
    frozen = dict(evidence['source_sha256'])
    expected_sources = {str(p.relative_to(ROOT)) for p in
                        [BOARD, BOARD.with_suffix('.kicad_pro'), BOARD.with_suffix('.kicad_dru'),
                         ROOT / 'design/main-rev-e.json', *MAIN.glob('*.kicad_sch')]}
    if set(frozen) != expected_sources:
        raise ValueError('Native evidence source inventory is incomplete')
    if set(evidence['report_sha256']) != {'independent-erc.json', 'independent-drc.json',
                                         'independent-netlist.xml', 'independent-geometry.json',
                                         'isolation-negative-tests.json'}:
        raise ValueError('Native evidence report inventory is incomplete')
    for filename, digest in evidence['report_sha256'].items():
        frozen[str((path.parent / filename).relative_to(ROOT))] = digest
    frozen[str(path.relative_to(ROOT))] = sha(path)
    panel = ROOT / 'hardware/panel-rev-e'
    panel_hash = sha(panel / 'pump-panel-rev-e.kicad_pcb')
    for name in ['connector-mechanical-interface.json', 'checks/model-coverage.json']:
        if read(panel / name)['pcb_sha256'] != panel_hash:
            raise ValueError('Panel model/interface evidence is stale')
    for filename in ['pump-panel-rev-e.kicad_pcb', 'connector-mechanical-interface.json',
                     'checks/model-coverage.json', 'exports/pump-panel-rev-e.step',
                     'exports/pump-panel-rev-e.glb']:
        p = panel / filename
        frozen[str(p.relative_to(ROOT))] = sha(p)
    generators = [*HERE.glob('*.py'), HERE / 'parameters.json', HERE / 'README.rst',
                  ROOT / 'tools/prepare_3d_board.py', ROOT / 'hardware/3d/approximate-bodies.json',
                  ROOT / 'hardware/3d/C1-envelope-provenance.json',
                  *sorted((ROOT / 'hardware/3d/models').glob('*.step'))]
    for path in generators:
        frozen[str(path.relative_to(ROOT))] = sha(path)
    unchanged(frozen)
    return frozen


def unchanged(frozen):
    for name, digest in frozen.items():
        if sha(ROOT / name) != digest:
            raise ValueError('Source or evidence changed: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-board-sha256', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    frozen = checked_sources(args.expected_board_sha256)
    if args.check_only:
        print('Current native and panel source evidence matches the selected PCB.')
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ['enclosure-rev-e-mechanical-prototype.zip', 'package-manifest.json',
                 'final-output-verification.json']:
        (OUT / name).unlink(missing_ok=True)
    PROVENANCE.unlink(missing_ok=True)
    logs = OUT / 'build-logs'
    logs.mkdir(exist_ok=True)

    def run(name, command):
        unchanged(frozen)
        result = subprocess.run([str(x) for x in command], cwd=ROOT, capture_output=True, text=True)
        (logs / (name + '.txt')).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(name + ' failed; see its build log')
        unchanged(frozen)
        print(name + ' complete', flush=True)

    run('prepare-main-model', [ROOT / '.tools/kicad-python', ROOT / 'tools/prepare_3d_board.py',
                               '--board', BOARD.relative_to(ROOT), '--tag', 'rev-e'])
    visual = ROOT / 'tmp/3d/pump-controller-rev-e-visualization.kicad_pcb'
    coverage = ROOT / 'hardware/3d/model-coverage-rev-e.json'
    if read(coverage)['source_board_sha256'] != args.expected_board_sha256:
        raise ValueError('Prepared main model source differs from selected PCB')
    outputs = {}
    for kind in ['step', 'glb']:
        destination = MAIN / 'exports' / ('pump-controller-main-rev-e.' + kind)
        run('export-main-' + kind, [ROOT / '.tools/kicad-cli', 'pcb', 'export', kind,
                                    '--force', '--subst-models', '--user-origin', '0x0mm',
                                    '-o', destination, visual])
        outputs[str(destination.relative_to(ROOT))] = sha(destination)
    model_record = {'source_board': str(BOARD.relative_to(ROOT)),
                    'source_board_sha256': args.expected_board_sha256,
                    'native_independent_checks_sha256': sha(MAIN / 'checks/independent-summary.json'),
                    'visualization_copy_sha256': sha(visual),
                    'coverage_sha256': sha(coverage), 'output_sha256': outputs,
                    'native_sources_modified': False,
                    'origin': 'Absolute 0,0; KiCad STEP millimetres; GLB metres',
                    'scope': 'Component-body geometry; approximate bodies and unverified mating parts remain'}
    PROVENANCE.write_text(json.dumps(model_record, indent=2) + '\n')
    frozen[str(PROVENANCE.relative_to(ROOT))] = sha(PROVENANCE)
    frozen[str(coverage.relative_to(ROOT))] = sha(coverage)
    frozen.update(outputs)
    for script in ['build_enclosure.py', 'render_previews.py', 'build_label_template.py',
                   'build_viewer.py', 'package_outputs.py']:
        run(script.removesuffix('.py'), [sys.executable, HERE / script])
    checks = read(OUT / 'fit-checks.json')
    if checks['main_pcb_sha256'] != args.expected_board_sha256:
        raise ValueError('Enclosure fit checks do not use the selected native PCB')
    output_paths = [p for p in OUT.iterdir() if p.is_file()]
    final_record = {'source_sha256': frozen, 'native_sources_modified': False,
                    'main_model_and_enclosure_current': True,
                    'printed_parts': len(read(OUT / 'manifest.json')['parts']),
                    'reference_component_interferences': checks['reference_component_interferences'],
                    'printed_part_collisions': checks['printed_part_collisions'],
                    'provisional_panel_plug_reservation_interferences': checks['provisional_panel_plug_reservation_interferences'],
                    'physical_fit_tested': False, 'material_or_electrical_enclosure_qualified': False,
                    'output_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(output_paths)}}
    unchanged(frozen)
    (OUT / 'final-output-verification.json').write_text(json.dumps(final_record, indent=2) + '\n')
    print('Final model, fit checks and mechanical prototype package match PCB ' + args.expected_board_sha256)


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, RuntimeError, OSError) as error:
        if '--check-only' not in sys.argv:
            for name in ['enclosure-rev-e-mechanical-prototype.zip', 'package-manifest.json',
                         'final-output-verification.json']:
                (OUT / name).unlink(missing_ok=True)
        raise SystemExit('Final mechanical export refused: ' + str(error))
