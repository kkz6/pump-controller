#!/usr/bin/env python3
"""Package verified main-board review data; no upload or ordering action."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'hardware/fabrication/rev-c'
OUT = BASE / 'output/gerber'
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((SOURCE / 'manifest.json').read_text())
for path, expected in manifest['source_sha256'].items():
    assert hashlib.sha256((BASE / path).read_bytes()).hexdigest() == expected, path
for path, expected in manifest['output_sha256'].items():
    assert hashlib.sha256((SOURCE / path).read_bytes()).hexdigest() == expected, path
validation = SOURCE / 'checks/gerber-validation.json'
assert validation.exists(), 'Run validate_gerbers.py before packaging'
checks = json.loads(validation.read_text())
assert checks['serialization_and_registration_passed'] and not checks['errors']
assert checks['pcb_sha256'] == manifest['source_sha256']['hardware/pump-controller-rev-b.kicad_pcb']
for path, record in checks['file_checks'].items():
    assert hashlib.sha256((SOURCE / path).read_bytes()).hexdigest() == record['sha256'], path

archive = OUT / 'pump-controller-rev-c-robu-REVIEW-ONLY.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
    for path in sorted((SOURCE / 'board').iterdir()):
        z.write(path, path.name)
    for directory in ['drill-maps', 'checks']:
        for path in sorted((SOURCE / directory).iterdir()):
            if path.is_file():
                z.write(path, str(path.relative_to(SOURCE)))
    z.write(SOURCE / 'manifest.json', 'manifest.json')
    z.write(BASE / 'hardware/fabrication/README.rst', 'READ-ME-REVIEW-ONLY.rst')
    for name in ['robu-dfm-audit.rst', 'robu-dfm-audit.json']:
        z.write(BASE / 'hardware/fabrication' / name, name)

stencil = OUT / 'pump-controller-rev-c-stencil-REVIEW-ONLY.zip'
with ZipFile(stencil, 'w', ZIP_DEFLATED) as z:
    for path in sorted((SOURCE / 'stencil').iterdir()):
        z.write(path, path.name)
    z.writestr('READ-ME.txt', 'Paste layers only; not a bare PCB order.\n'
               'Review exposed-pad paste, thermal holes and two-sided assembly before ordering.\n')
for path in [archive, stencil]:
    with ZipFile(path) as z:
        assert z.testzip() is None
    print(path.relative_to(BASE), path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest())
