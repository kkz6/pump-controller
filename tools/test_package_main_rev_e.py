#!/usr/bin/env python3
"""Exercise the package gate with synthetic evidence in temporary directories.

These tests verify packaging behavior, not the electrical or CAM validity of
any real PCB. Actual design checks are mandatory before real packages exist.
"""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import zipfile

import package_main_rev_e as gate


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PackageGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-pcb-package-test-')
        self.base = Path(self.temp.name)
        self.out = self.base / 'hardware/main-rev-e'
        self.checks = self.out / 'checks'
        self.checks.mkdir(parents=True)
        name = gate.NAME
        inputs = [self.out / (name + ext) for ext in
                  ['.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_sch']]
        inputs.append(self.base / 'design/main-rev-e.json')
        for path in inputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic fixture: ' + path.name)
        sources = {str(p.relative_to(self.base)): digest(p) for p in inputs}
        board_hash = digest(inputs[0])
        source_hash = digest(inputs[-1])
        for filename in gate.REPORTS:
            dump(self.checks / filename, {'synthetic': True})
        dump(self.checks / 'independent-geometry.json',
             {'pcb_sha256': board_hash, 'source_sha256': source_hash,
              'copper_layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'],
              'geometry_and_source_passed': True})
        dump(self.checks / 'independent-summary.json', {
            'source_sha256': sources, 'independent_native_checks_passed': True,
            'native_sources_unchanged': True, 'geometry_and_source_passed': True,
            'isolation_negative_tests_passed': True, 'critical_checks_ignored': [],
            'native_violation_counts': dict(erc=0, drc=0, unconnected=0, schematic_parity=0),
            'report_sha256': {n: digest(self.checks / n) for n in gate.REPORTS}})
        cam = self.out / 'gerber'
        stencil = self.out / 'exports/stencil'
        cam.mkdir()
        stencil.mkdir(parents=True)
        paths = [cam / (name + '.' + ext) for ext in gate.BOARD_EXTENSIONS]
        paths += [cam / (name + ext) for ext in ['.gbrjob', '-PTH.XLN', '-NPTH.XLN', '.d356']]
        paths += [stencil / (name + '.' + ext) for ext in ['GTP', 'GBP']]
        for path in paths:
            path.write_text('synthetic artifact: ' + path.name)
        drill = self.out / 'exports/drill-maps/drill-report.txt'
        drill.parent.mkdir()
        drill.write_text('synthetic drill report')
        dump(self.out / 'fabrication-manifest.json', {
            **gate.SETTINGS, 'origin': 'absolute, metric, unmirrored across all CAM and drill files',
            'source_sha256': sources,
            'output_sha256': {str(p.relative_to(self.out)): digest(p) for p in paths + [drill]}})
        dump(self.checks / 'independent-gerbers.json', {
            'pcb_sha256': board_hash, 'source_sha256': source_hash,
            'native_inventory_sha256': digest(self.checks / 'independent-geometry.json'),
            'serialization_registration_and_mask_passed': True, 'errors': [],
            'gerber_files_parsed': 13, 'outline_centerline_size_mm': [100, 80],
            'mask_geometry': {'F.Mask': {'passed': True}, 'B.Mask': {'passed': True}},
            'file_checks': {str(p.relative_to(self.base)): {'sha256': digest(p)} for p in paths},
            'gerber_conductive_netlist_extracted': False})

    def tearDown(self):
        self.temp.cleanup()

    def update(self, path, key, value):
        data = json.loads(path.read_text())
        data[key] = value
        dump(path, data)

    def refused(self):
        # A failed retry must remove earlier archives, not leave stale uploads.
        for suffix in gate.SUFFIXES:
            (self.out / (gate.NAME + suffix)).write_text('obsolete upload')
        with self.assertRaises((ValueError, KeyError, OSError)):
            gate.package(self.base)
        for suffix in gate.SUFFIXES:
            self.assertFalse((self.out / (gate.NAME + suffix)).exists())
        self.assertFalse((self.out / 'package-manifest.json').exists())

    def test_packages_only_matching_artifacts_and_separates_stencil(self):
        result = gate.package(self.base)
        self.assertTrue(result['pcb_prototype_order_package'])
        self.assertFalse(result['assembled_product_qualified'])
        self.assertFalse(result['manufacturer_accepted'])
        counts = []
        for filename, details in result['archives'].items():
            with zipfile.ZipFile(self.out / filename) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), set(details['files_sha256']))
                counts.append(len(archive.namelist()))
                for name, value in details['files_sha256'].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), value)
                if 'gerber' in filename:
                    self.assertFalse(any(n.endswith(('.GTP', '.GBP')) for n in archive.namelist()))
        self.assertEqual(counts, [18, 4])

    def test_stale_pcb(self):
        (self.out / (gate.NAME + '.kicad_pcb')).write_text('changed PCB')
        self.refused()

    def test_altered_native_report(self):
        (self.checks / 'independent-drc.json').write_text('changed report')
        self.refused()

    def test_failed_native_summary(self):
        self.update(self.checks / 'independent-summary.json', 'independent_native_checks_passed', False)
        self.refused()

    def test_failed_cam(self):
        self.update(self.checks / 'independent-gerbers.json', 'serialization_registration_and_mask_passed', False)
        self.refused()

    def test_modified_copper(self):
        (self.out / 'gerber' / (gate.NAME + '.GTL')).write_text('changed copper')
        self.refused()

    def test_modified_stencil(self):
        (self.out / 'exports/stencil' / (gate.NAME + '.GBP')).write_text('changed paste')
        self.refused()

    def test_extra_unchecked_copper(self):
        (self.out / 'gerber/unknown.GTL').write_text('unreviewed copper')
        self.refused()

    def test_settings_changed(self):
        self.update(self.out / 'fabrication-manifest.json', 'outer_copper_oz', 2)
        self.refused()

    def test_missing_cam_evidence(self):
        (self.checks / 'independent-gerbers.json').unlink()
        self.refused()

    def test_old_four_layer_manifest(self):
        self.update(self.out / 'fabrication-manifest.json', 'layer_order', ['GTL', 'G2L', 'G3L', 'GBL'])
        self.refused()

    def test_old_four_layer_cam_count(self):
        self.update(self.checks / 'independent-gerbers.json', 'gerber_files_parsed', 11)
        self.refused()


if __name__ == '__main__':
    unittest.main()
