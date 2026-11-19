"""Verify both Panel F uploads against the exported files and exercise the remote station nets."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from cam.check_archives import FILES, ROOT, check


def validate(driver):
    archive = ROOT / FILES['panel']
    board = archive.parent / 'pump-panel-rev-f.kicad_pcb'
    entry, controls = check('panel', driver)
    archives = {}
    for kind in ('gerber', 'stencil'):
        path = board.with_name(f'{board.stem}-{kind}-prototype.zip')
        folder = board.parent / f'{kind}-review'
        with zipfile.ZipFile(path) as z:
            members = z.namelist()
            expected = {p.name for p in folder.iterdir() if p.is_file()}
            if z.testzip() or sorted(members) != sorted(expected):
                raise ValueError(f'ZIP CRC or members differ: {path}')
            if any(z.read(name) != (folder / name).read_bytes() for name in members):
                raise ValueError(f'Archived bytes differ from panel exports: {path}')
            archives[path.name] = dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                       members=sorted(members))
    report = dict(pcb_sha256=hashlib.sha256(board.read_bytes()).hexdigest(), archives=archives,
                  ipc_records=entry['ipc_records'], logical_nets_including_separate_unused_pins=entry['ipc_named_nets'],
                  layer_witnesses=entry['layer_witnesses'], opens_shorts=entry['opens_shorts'],
                  negative_controls_detected=controls, physical_harness_tested=False)
    (board.parent / 'checks/artwork.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f"Panel F: {entry['layer_witnesses']} copper witnesses, {len(controls)} injected faults detected")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', required=True, type=Path, help='Executable built from tools/cam/compare.cpp')
    validate(parser.parse_args().compare.resolve())
