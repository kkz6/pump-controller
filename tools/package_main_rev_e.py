#!/usr/bin/env python3
"""Package current, independently checked Rev E CAM for a bare-PCB prototype.

No CAD, CAM or check results are changed. Supplier acceptance, assembly and
finished-product qualification are outside this gate.
"""
from pathlib import Path
import hashlib
import json
import tempfile
import zipfile

BASE = Path(__file__).resolve().parents[1]
NAME = 'pump-controller-main-rev-e'
SUFFIXES = ('-gerber-prototype.zip', '-stencil-prototype.zip')
BOARD_EXTENSIONS = ('GTL', 'G2L', 'G3L', 'G4L', 'G5L', 'GBL', 'GTS', 'GBS', 'GTO', 'GBO', 'GKO')
REPORTS = {'independent-erc.json', 'independent-drc.json', 'independent-netlist.xml',
           'independent-geometry.json', 'isolation-negative-tests.json'}
SETTINGS = {'outline_mm': [100, 80], 'layer_order': ['GTL', 'G2L', 'G3L', 'G4L', 'G5L', 'GBL'],
            'thickness_mm': 1.6, 'solder_mask': 'green', 'outer_copper_oz': 1,
            'inner_copper_oz': .5, 'finish': 'ENIG',
            'material': 'FR4 Tg155 or vendor-confirmed equivalent',
            'through_vias_only': True, 'via_in_pad': False,
            'exact_dielectric_stackup_vendor_confirmation_required': True,
            'controlled_impedance_specified': False}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def invalidate_packages(output):
    for suffix in SUFFIXES:
        (output / (NAME + suffix)).unlink(missing_ok=True)
    (output / 'package-manifest.json').unlink(missing_ok=True)


def package(base=BASE):
    output = base / 'hardware/main-rev-e'
    invalidate_packages(output)
    board = output / (NAME + '.kicad_pcb')
    checks = output / 'checks'
    tracked = {}

    def watch(path):
        path = path.resolve()
        require(path.is_relative_to(base.resolve()), 'Evidence path leaves project')
        digest = sha(path)
        require(path not in tracked or tracked[path] == digest, 'Evidence changed while reading: ' + str(path))
        tracked[path] = digest
        return path

    def read(path):
        return json.loads(watch(path).read_text())

    inputs = [board, board.with_suffix('.kicad_pro'), board.with_suffix('.kicad_dru'),
              base / 'design/main-rev-e.json'] + sorted(output.glob('*.kicad_sch'))
    frozen = {str(path.relative_to(base)): sha(watch(path)) for path in inputs}
    pcb_hash = frozen[str(board.relative_to(base))]
    source_hash = frozen['design/main-rev-e.json']
    native = read(checks / 'independent-summary.json')
    require(native['source_sha256'] == frozen, 'Native checks refer to stale sources')
    require(native['independent_native_checks_passed'] is True
            and native['native_sources_unchanged'] is True
            and native['geometry_and_source_passed'] is True
            and native['isolation_negative_tests_passed'] is True
            and not native['critical_checks_ignored']
            and native['native_violation_counts'] == dict(erc=0, drc=0, unconnected=0, schematic_parity=0),
            'Independent native checks failed')
    require(set(native['report_sha256']) == REPORTS, 'Native report inventory is incomplete')
    for filename, digest in native['report_sha256'].items():
        require(sha(watch(checks / filename)) == digest, 'Native report changed: ' + filename)
    geometry = read(checks / 'independent-geometry.json')
    require(geometry['pcb_sha256'] == pcb_hash and geometry['source_sha256'] == source_hash
            and geometry['geometry_and_source_passed'] is True
            and set(geometry['copper_layers']) == {'F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'},
            'Native geometry is stale or failed')
    export = read(output / 'fabrication-manifest.json')
    require(export['source_sha256'] == frozen, 'CAM export refers to stale sources')
    require(all(export[key] == value for key, value in SETTINGS.items()),
            'Fabrication settings changed; review package notes and process assumptions')
    expected_board = {NAME + '.' + ext for ext in BOARD_EXTENSIONS}
    expected_board |= {NAME + ext for ext in ('.gbrjob', '-PTH.XLN', '-NPTH.XLN', '.d356')}
    expected_paste = {NAME + '.GTP', NAME + '.GBP'}
    cam = output / 'gerber'
    paste = output / 'exports/stencil'
    require({p.name for p in cam.iterdir()} == expected_board, 'Unexpected/missing bare-board CAM file')
    require({p.name for p in paste.iterdir()} == expected_paste, 'Unexpected/missing stencil file')
    expected_paths = {str((cam / n).relative_to(base)) for n in expected_board}
    expected_paths |= {str((paste / n).relative_to(base)) for n in expected_paste}
    for relative, digest in export['output_sha256'].items():
        path = watch(output / relative)
        require(path.is_relative_to(output.resolve()), 'Export path leaves board directory')
        require(sha(path) == digest, 'Export artifact changed: ' + relative)
    require(expected_paths <= {str((output / p).relative_to(base)) for p in export['output_sha256']},
            'Export manifest omits CAM artifacts')
    drill_report = output / 'exports/drill-maps/drill-report.txt'
    require(str(drill_report.relative_to(output)) in export['output_sha256'], 'Drill report is not bound to export')
    parsed = read(checks / 'independent-gerbers.json')
    require(parsed['pcb_sha256'] == pcb_hash and parsed['source_sha256'] == source_hash
            and parsed['native_inventory_sha256'] == sha(checks / 'independent-geometry.json'),
            'Parsed CAM evidence refers to stale sources/inventory')
    require(parsed['serialization_registration_and_mask_passed'] is True and not parsed['errors']
            and parsed['gerber_files_parsed'] == 13 and parsed['outline_centerline_size_mm'] == [100, 80]
            and set(parsed['mask_geometry']) == {'F.Mask', 'B.Mask'}
            and all(x['passed'] is True for x in parsed['mask_geometry'].values()),
            'Parsed CAM checks failed or are incomplete')
    require(set(parsed['file_checks']) == expected_paths, 'Parsed CAM file inventory differs from package')
    for relative, details in parsed['file_checks'].items():
        require(sha(watch(base / relative)) == details['sha256'], 'Parsed CAM artifact changed: ' + relative)
    require(parsed['gerber_conductive_netlist_extracted'] is False,
            'Unexpected connectivity validation scope; review packaging gate')

    notes = (
        'BARE-PCB ENGINEERING PROTOTYPE — MAIN REV E\n'
        '100 x 80 mm, 6 layers, 1.6 mm FR-4 Tg155 or vendor-confirmed equivalent.\n'
        'Layer order: GTL / G2L / G3L / G4L / G5L / GBL. Outer copper 1 oz; inner copper 0.5 oz.\n'
        'Green solder mask, white legend, ENIG. No controlled impedance stackup specified.\n'
        'Exact dielectric ply schedule and the six-layer construction require vendor confirmation.\n'
        'Standard plated through vias; no filled/capped via-in-pad process required.\n'
        'Metric absolute unmirrored CAM. Keep PTH and NPTH drills separate.\n'
        'Finished dimensions follow the profile centreline. Do not scale the files.\n'
        'Request bare-board electrical testing against the supplied IPC-D-356 netlist.\n'
        'Confirm proposed material/stackup/process settings with the fabricator.\n'
        'Check both K1 and K2 contact-to-coil pad pairs (pins 2 and 1). The design target for live-to-isolated copper is 8.00 mm minimum.\n'
        'Confirm the gap on finished copper and review any CAM pad enlargement before production. Report the measured first-article gap.\n'
        'Native and parsed CAM checks do not qualify an assembled mains product.\n'
        'The IPC netlist is a native reference, not connectivity extracted from Gerber copper.\n'
        'Paste files are supplied in a separate stencil archive.\n'
    )
    common = {
        'revision': 'E', 'scope': 'Bare-PCB engineering prototype only',
        'native_and_parsed_cam_checks_passed': True,
        'manufacturer_accepted': False, 'hardware_tested': False,
        'assembled_product_qualified': False, 'gerber_conductive_netlist_extracted': False,
        'source_sha256': frozen,
        'evidence_sha256': {str(p.relative_to(base.resolve())): digest for p, digest in tracked.items()
                            if p.parent == checks.resolve() or p.name == 'fabrication-manifest.json'},
        'fabrication_settings': {key: export[key] for key in
                                 ['outline_mm', 'layer_order', 'thickness_mm', 'solder_mask',
                                  'outer_copper_oz', 'inner_copper_oz', 'finish', 'material',
                                  'origin', 'through_vias_only', 'via_in_pad',
                                  'exact_dielectric_stackup_vendor_confirmation_required',
                                  'controlled_impedance_specified']},
    }
    payloads = [
        ({n: (cam / n).read_bytes() for n in sorted(expected_board)}, notes),
        ({n: (paste / n).read_bytes() for n in sorted(expected_paste)},
         'SEPARATE STENCIL PROTOTYPE — MAIN REV E\n'
         'F.Paste / B.Paste; metric absolute coordinates. Not part of bare-board copper.\n'
         'Assembler must confirm stencil thickness, apertures and assembly process.\n'),
    ]
    packages = {}
    with tempfile.TemporaryDirectory(prefix='pump-e-package-', dir=output) as temp:
        temp = Path(temp)
        for suffix, (payload, text) in zip(SUFFIXES, payloads):
            payload['MANUFACTURING-NOTES.txt'] = text.encode()
            if suffix == SUFFIXES[0]:
                payload['drill-report.txt'] = drill_report.read_bytes()
            manifest = {**common, 'archive_kind': 'bare_board' if suffix == SUFFIXES[0] else 'stencil',
                        'files_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in payload.items()}}
            payload['package-manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
            filename = NAME + suffix
            with zipfile.ZipFile(temp / filename, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, data in sorted(payload.items()):
                    archive.writestr(name, data)
            with zipfile.ZipFile(temp / filename) as archive:
                require(archive.testzip() is None, 'ZIP CRC check failed')
                require(set(archive.namelist()) == set(payload), 'ZIP inventory mismatch')
                require(all(archive.read(n) == b for n, b in payload.items()), 'ZIP content mismatch')
            packages[filename] = {'sha256': sha(temp / filename), 'file_count': len(payload),
                                  'files_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in payload.items()}}
        require(sorted(output.glob('*.kicad_sch')) == sorted(p for p in inputs if p.suffix == '.kicad_sch'),
                'Schematic inventory changed during packaging')
        require(all(sha(path) == digest for path, digest in tracked.items()), 'Sources/evidence changed during packaging')
        for filename in packages:
            (temp / filename).replace(output / filename)
    result = {**common, 'pcb_prototype_order_package': True, 'archives': packages}
    (output / 'package-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    try:
        result = package()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        raise SystemExit('Packaging refused; current validated evidence is required: ' + str(error))
    print(json.dumps({'scope': result['scope'], 'archives': {
        name: {key: details[key] for key in ['sha256', 'file_count']}
        for name, details in result['archives'].items()}}, indent=2))
