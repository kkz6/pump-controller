"""Compare the direct main schematic with the socketed revision and exercise its pilot contacts."""
import csv
import itertools
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'hardware/main-direct'
OUT = ROOT / 'output/direct-starter'


def export(cli, schematic, dest):
    subprocess.run([cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', dest, schematic], check=True)
    tree = ET.parse(dest)
    return {(p.get('ref'), p.get('pin')):net.get('name') for net in tree.findall('.//nets/net')
            for p in net.findall('node')}


def main():
    cli = os.getenv('KICAD_CLI') or shutil.which('kicad-cli') or str(ROOT/'.tools/kicad-cli')
    previous = ROOT/'hardware/main-socketed'
    with tempfile.TemporaryDirectory() as work:
        tmp = Path(work)
        old = export(cli, previous/'pump-controller-integrated.kicad_sch', tmp/'old.xml')
        pins = export(cli, BOARD/'pump-direct.kicad_sch', tmp/'main.xml')
        panel = export(cli, ROOT/'hardware/panel-rev-f/pump-panel-rev-f.kicad_sch', tmp/'panel.xml')
    with (previous/'bom.csv').open(newline='') as f:
        excluded = {r['Reference'] for r in csv.DictReader(f) if r['Sheet'].startswith('guard_')}
    excluded.update(f'R{i}' for i in range(192,198))
    expected = {k:('STOP_RETURN' if v=='K1_COIL_PLUS' else v) for k,v in old.items() if k[0] not in excluded}
    for number,port in [('23','2'),('24','3')]:
        expected['U33',number] = f'unconnected-(U33-GPA{port}-Pad{number})'
    assert pins == expected, (pins.items()-expected.items(), expected.items()-pins.items())
    assert pins['K1','6']==pins['J32','2']==pins['R86','1']==pins['D31','1']
    assert pins['K2','6']==pins['J32','1']==pins['U40','5']==pins['D32','1']
    for k,plug in [('K1','J30'),('K2','J35')]:
        assert pins[k,'3']==pins[plug,'1'] and pins[k,'4']==pins[plug,'2']
    pairs = {(pins[r,n]) for r in ('J30','J35') for n in ('1','2')}
    assert len(pairs)==4 and pairs.isdisjoint({pins['J1','1'],pins['J1','2'],pins['J32','7']})
    # Panel: the actual NC STOP and external NC return precede the A coil.
    assert panel['J1','1']==panel['SW1','1'] and panel['SW1','3']==panel['J2','3']
    assert panel['J2','4']==panel['J1','2'] and panel['J2','3']!=panel['J2','4']
    counts=0
    for stop,ol,physical_start,sealed,enable,pickup in itertools.product((False,True),repeat=6):
        # OEM pilot network, with both the operator pickup and the existing holding branch.
        edges=[('supply','after_stop',not stop),('after_stop','after_overload',not ol),
               ('after_overload','permit_out',enable),('permit_out','coil',physical_start),
               ('permit_out','coil',sealed),('permit_out','coil',pickup)]
        live={'supply'}
        for src,dst,closed in edges:
            if src in live and closed: live.add(dst)
        assert ('coil' in live)==(not stop and not ol and enable and (physical_start or sealed or pickup))
        counts+=1
    # Direct outputs cannot guarantee release-to-restart protection. Held B plus A permission
    # supplies pickup as soon as the NC STOP recloses, even when the factory seal has opened.
    report=dict(removed_positions=len(excluded),native_terminal_assignments_compared=len(expected),
                dol_pilot_contact_combinations=counts,physical_starter_tested=False,
                welded_pickup='If A remains enabled and B is stuck closed, releasing the factory STOP can energize a conventional DOL coil.',
                electronic='Two NO dry contacts require documented remote inputs and a verified independent factory STOP/overload path.')
    OUT.mkdir(exist_ok=True)
    (OUT/'direct-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report)


if __name__=='__main__':
    main()
