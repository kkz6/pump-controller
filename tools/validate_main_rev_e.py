#!/usr/bin/env python3
"""Fresh native checks and adversarial isolation checks for the final Rev E PCB.

The native board is read-only. Deliberately invalid test boards exist only in
temporary directories and are never part of a fabrication package.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, allowed=(0, 5)):
    result = subprocess.run([str(x) for x in command], cwd=BASE, capture_output=True, text=True)
    if result.returncode not in allowed:
        raise RuntimeError(result.stdout + result.stderr)
    return result


def make_test_copy(args):
    """Only this subprocess requires KiCad Python; the main launcher does not."""
    import pcbnew as p
    dest = args.inject_copy
    dest.mkdir(parents=True, exist_ok=True)
    b = p.LoadBoard(str(args.board))
    edge = b.GetBoardEdgesBoundingBox()
    x = p.ToMM(edge.GetX()) + 10
    y = p.ToMM(edge.GetY() + edge.GetHeight()) + 20
    layers = [layer for layer in b.GetEnabledLayers().Seq() if p.IsCopperLayer(layer)]
    records = []
    for i, layer in enumerate(layers):
        pair = []
        for net, y_offset in [('M_GND', 0), ('GND', args.test_gap + .25)]:
            track = p.PCB_TRACK(b)
            track.SetLayer(layer)
            track.SetStart(p.VECTOR2I(p.FromMM(x + i * 20), p.FromMM(y + y_offset)))
            track.SetEnd(p.VECTOR2I(p.FromMM(x + i * 20 + 1), p.FromMM(y + y_offset)))
            track.SetWidth(p.FromMM(.25))
            track.SetNetCode(b.FindNet(net).GetNetCode())
            b.Add(track)
            pair.append(str(track.m_Uuid.AsString()))
        records.append({'layer': b.GetLayerName(layer), 'pair_uuids': pair,
                        'copper_edge_gap_mm': args.test_gap})
    copy_path = dest / args.board.name
    p.SaveBoard(str(copy_path), b)
    # SaveBoard can rewrite project settings. The negative test must use the
    # frozen project's exact rules and net-class patterns after that save.
    for suffix in ['.kicad_pro', '.kicad_dru']:
        shutil.copyfile(args.board.with_suffix(suffix), dest / args.board.with_suffix(suffix).name)
    (dest / 'injections.json').write_text(json.dumps(records, indent=2) + '\n')


def validate(args):
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or str(BASE / '.tools/kicad-cli')
    python = os.environ.get('KICAD_PYTHON') or str(BASE / '.tools/kicad-python')
    board = args.board.resolve()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    inputs = [board, board.with_suffix('.kicad_pro'), board.with_suffix('.kicad_dru'), source]
    inputs += sorted(board.parent.glob('*.kicad_sch'))
    frozen = {str(path.relative_to(BASE)): sha(path) for path in inputs}
    erc_path, drc_path = output / 'independent-erc.json', output / 'independent-drc.json'
    run([cli, 'sch', 'erc', '--format', 'json', '--severity-all', '--exit-code-violations',
         '-o', erc_path, board.with_suffix('.kicad_sch')])
    run([cli, 'pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors',
         '--schematic-parity', '--exit-code-violations', '-o', drc_path, board])
    netlist_path = output / 'independent-netlist.xml'
    run([cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', netlist_path,
         board.with_suffix('.kicad_sch')], allowed=(0,))
    geometry_path = output / 'independent-geometry.json'
    run([python, BASE / 'tools/check_main_rev_e_geometry.py', '--board', board,
         '--source', source, '--netlist', netlist_path, '--output', geometry_path], allowed=(0, 1))
    geometry = json.loads(geometry_path.read_text())
    erc, drc = json.loads(erc_path.read_text()), json.loads(drc_path.read_text())

    isolation = []
    with tempfile.TemporaryDirectory(prefix='pump-rev-e-isolation-') as temp:
        for gap, should_fail in [(7.9, True), (8.1, False)]:
            dest = Path(temp) / ('below' if should_fail else 'above')
            run([python, Path(__file__).resolve(), '--board', board, '--inject-copy', dest,
                 '--test-gap', str(gap)], allowed=(0,))
            report = dest / 'drc.json'
            run([cli, 'pcb', 'drc', '--format', 'json', '--units', 'mm', '--severity-all',
                 '--all-track-errors', '-o', report, dest / board.name])
            result = json.loads(report.read_text())
            for pair in json.loads((dest / 'injections.json').read_text()):
                ids = set(pair['pair_uuids'])
                found = [v for v in result['violations'] if v['type'] == 'clearance'
                         and ids.issubset({item['uuid'] for item in v['items']})]
                limits = []
                for v in found:
                    match = re.search(r'clearance\s+([0-9.]+)\s+mm', v['description'])
                    if match:
                        limits.append(float(match.group(1)))
                passed = (8.0 in limits) if should_fail else not found
                isolation.append({**pair, 'expected_8mm_violation': should_fail,
                                  'reported_clearances_mm': limits,
                                  'matching_findings': found, 'passed': passed})
    negative_report = {'source_sha256': frozen, 'cases': isolation,
                       'expected_cases': 12,
                       'passed': len(isolation) == 12 and all(x['passed'] for x in isolation),
                       'method': 'Injected pairs 7.9 and 8.1 mm apart on every copper layer in copies of the actual board/project/rules. Only findings identifying both injected UUIDs determine the result. Other outside-outline/unconnected test artifacts are not interpreted as isolation evidence.',
                       'test_copies_retained': False, 'native_board_changed': False}
    (output / 'isolation-negative-tests.json').write_text(json.dumps(negative_report, indent=2) + '\n')

    critical = {'clearance', 'shorting_items', 'tracks_crossing', 'unconnected_items',
                'track_width', 'via_diameter', 'annular_width', 'drill_out_of_range',
                'hole_clearance', 'holes_co_located', 'hole_near_hole', 'copper_edge_clearance',
                'silk_over_copper', 'silk_overlap', 'solder_mask_bridge'}
    ignored = [x for x in drc.get('ignored_checks', []) if x['key'] in critical]
    counts = {
        'erc': sum(len(sheet.get('violations', [])) for sheet in erc.get('sheets', [])),
        'drc': len(drc['violations']), 'unconnected': len(drc['unconnected_items']),
        'schematic_parity': len(drc['schematic_parity']),
    }
    unchanged = frozen == {str(path.relative_to(BASE)): sha(path) for path in inputs}
    passed = (unchanged and not any(counts.values()) and not ignored
              and geometry['geometry_and_source_passed'] and negative_report['passed'])
    summary = {
        'source_sha256': frozen, 'native_sources_unchanged': unchanged,
        'native_violation_counts': counts, 'critical_checks_ignored': ignored,
        'geometry_and_source_passed': geometry['geometry_and_source_passed'],
        'isolation_negative_tests_passed': negative_report['passed'],
        'independent_native_checks_passed': passed,
        'report_sha256': {p.name: sha(p) for p in [erc_path, drc_path, netlist_path, geometry_path,
                                                  output / 'isolation-negative-tests.json']},
        'manufacturer_accepted': False, 'hardware_tested': False, 'release_ready': False,
    }
    (output / 'independent-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'native_counts': counts,
                      'geometry_passed': geometry['geometry_and_source_passed'],
                      'isolation_tests_passed': negative_report['passed']}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=BASE / 'hardware/main-rev-e/pump-controller-main-rev-e.kicad_pcb')
    ap.add_argument('--source', type=Path, default=BASE / 'design/main-rev-e.json')
    ap.add_argument('--output', type=Path, default=BASE / 'hardware/main-rev-e/checks')
    ap.add_argument('--inject-copy', type=Path, help=argparse.SUPPRESS)
    ap.add_argument('--test-gap', type=float, default=7.9, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.inject_copy:
        make_test_copy(args)
    else:
        raise SystemExit(validate(args))
