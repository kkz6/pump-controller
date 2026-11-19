"""Export and independently check the two-layer receiver's bare-board and stencil CAM."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from gerbonara import ExcellonFile, GerberFile
from gerbonara.graphic_objects import Flash, Line
from gerbonara.ipc356 import Netlist
from gerbonara.utils import MM

from package_main_rev_e import require

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'hardware/guard-receiver'
CLI = ROOT / '.tools/kicad-cli'
STEM = 'guard-receiver-rev-a'
REVISION = 'GUARD-RX-A'
BOARD = PROJECT / 'guard-receiver.kicad_pcb'
LAYERS = {
    'F.Cu': ('GTL', 'Copper,L1,Top'), 'B.Cu': ('GBL', 'Copper,L2,Bot'),
    'F.Mask': ('GTS', 'Soldermask,Top'), 'B.Mask': ('GBS', 'Soldermask,Bot'),
    'F.Silkscreen': ('GTO', 'Legend,Top'), 'B.Silkscreen': ('GBO', 'Legend,Bot'),
    'Edge.Cuts': ('GKO', 'Profile,NP'),
}
PASTE = {'F.Paste': ('GTP', 'Paste,Top'), 'B.Paste': ('GBP', 'Paste,Bot')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cli(*args):
    subprocess.run([str(k) for k in (CLI, *args)], check=True, cwd=ROOT, capture_output=True, text=True)


def layer_export(temp, dest, layers):
    plot = temp / dest.name
    plot.mkdir()
    cli('pcb', 'export', 'gerbers', '--layers', ','.join(layers), '--disable-aperture-macros',
        '--subtract-soldermask', '--check-zones', '--precision', '6', '-o', str(plot) + '/', BOARD)
    result = {}
    renamed = {}
    for ext, role in layers.values():
        files = [f for f in plot.iterdir() if f.suffix != '.gbrjob'
                 and '%TF.FileFunction,' + role + '*%' in f.read_text()]
        require(len(files) == 1, 'Missing or duplicate layer ' + role)
        f, = files
        text = f.read_text()
        require('%MOMM*%' in text and text.rstrip().endswith('M02*') and
                re.search(r'%TF.ProjectId,[^\r\n]+,' + REVISION + r'\*%', text),
                'Plot units, termination or revision failed on ' + f.name)
        layer = GerberFile.open(f)
        if ext in ('GTL', 'GBL', 'GTS', 'GKO', 'GTP'):
            require(layer.objects, 'Unexpected empty layer ' + ext)
        target = dest / (STEM + '.' + ext)
        renamed[f.name] = target.name
        shutil.copyfile(f, target)
        result[ext] = layer
    if 'Edge.Cuts' in layers:
        job, = plot.glob('*.gbrjob')
        data = json.loads(job.read_text())
        for entry in data['FilesAttributes']:
            entry['Path'] = renamed[entry['Path']]
        require({e['Path'] for e in data['FilesAttributes']} == set(renamed.values()), 'Incomplete job file')
        (dest / (STEM + '.gbrjob')).write_text(json.dumps(data, indent=2) + '\n')
    return result


def check_reference(ipc_path, xml, drills):
    ipc = Netlist.open(ipc_path)
    aliases = dict(re.findall(r'^P\s+NNAME(\S+)\s+(\S+)\s*$', ipc_path.read_text(), re.M))
    actual = {}
    expected_holes = {True: [], False: []}
    for pin in ipc.test_records:
        pair = pin.ref_des, pin.pin
        if pin.ref_des and pin.pin and not pin.is_via:
            actual.setdefault(pair, set()).add(aliases.get(pin.net_name, pin.net_name))
        if pin.hole_dia:
            expected_holes[bool(pin.is_plated)].append((MM(pin.x,pin.unit), MM(pin.y,pin.unit),
                                                       MM(pin.hole_dia,pin.unit)))
    expected = {(p.get('ref'), p.get('pin')): n.get('name') for n in ET.parse(xml).findall('.//nets/net')
                for p in n.findall('node') if not p.get('ref').startswith('#')}
    for key, net in expected.items():
        require(actual.get(key) == {net}, f'IPC pin {key} differs from schematic {net}: {actual.get(key)}')
    require(not (actual.keys() - expected.keys()), 'PCB contains a pad missing from the schematic')
    counts = {}
    for plated, path in drills.items():
        remaining = expected_holes[plated].copy()
        for hole in ExcellonFile.open(path).objects:
            require(isinstance(hole, Flash), 'Circular through drills expected')
            centre = (MM(hole.x,hole.unit), MM(hole.y,hole.unit), MM(hole.tool.diameter,hole.tool.unit))
            # IPC resolution is 0.0001 inch; the Excellon writer uses 0.001 mm.
            # Two rounded coordinates can differ by the sum of their half units.
            matches = [i for i, pin in enumerate(remaining) if all(abs(a-b) <= .001771 for a,b in zip(centre,pin))]
            require(len(matches) == 1, 'Unmatched/ambiguous Excellon drill ' + str(centre))
            remaining.pop(matches[0])
            if plated:
                require(centre[2] >= .3, 'Plated hole below the 2-layer 0.30 mm via drill limit')
        require(not remaining, 'Excellon file omits a native hole')
        counts['PTH' if plated else 'NPTH'] = len(expected_holes[plated])
    return len(expected), counts


def package():
    # A failed re-export must not leave an upload labeled as the current board.
    for name in (STEM+'-gerber-prototype.zip', STEM+'-stencil-prototype.zip', 'checks/cam-package.json'):
        (PROJECT/name).unlink(missing_ok=True)
    sources = sorted(f for f in PROJECT.rglob('*') if f.is_file() and (f.suffix in
                     ('.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_mod','.kicad_sym')
                     or f.name in ('fp-lib-table','sym-lib-table')))
    hashes = {str(f.relative_to(ROOT)): sha(f) for f in sources}
    geometry_path = PROJECT/'checks/geometry.json'
    geometry_digest = sha(geometry_path)
    geometry = json.loads(geometry_path.read_text())
    require(geometry['board_sha256'] == sha(BOARD) and geometry['board_revision'] == REVISION
            and geometry['minimum_projected_copper_gap_mm'] >= 3
            and not geometry['all_drill_to_smt_mask_overlaps']
            and all(geometry[key] == 0 for key in
                    ('erc_violations','drc_violations','unconnected_items','schematic_parity_findings')),
            'Receiver geometry does not qualify this board revision')
    with tempfile.TemporaryDirectory() as work:
        temp = Path(work)
        built = temp / 'deliverables'
        copper, stencil = built / 'board', built / 'stencil'
        copper.mkdir(parents=True)
        stencil.mkdir()
        erc, drc, xml = (built / n for n in ['erc.json','drc.json','netlist.xml'])
        cli('sch','erc','--severity-all','--exit-code-violations','--format','json','-o',erc,BOARD.with_suffix('.kicad_sch'))
        cli('pcb','drc','--severity-all','--schematic-parity','--all-track-errors','--exit-code-violations',
            '--format','json','-o',drc,BOARD)
        cli('sch','export','netlist','--format','kicadxml','-o',xml, BOARD.with_suffix('.kicad_sch'))
        parsed = layer_export(temp, copper, LAYERS)
        layer_export(temp, stencil, PASTE)
        outline = parsed['GKO'].objects
        require(len(outline) == 4 and all(isinstance(x,Line) for x in outline), 'Rectangular outline expected')
        ends = [(round(MM(getattr(s,x),s.unit),5),round(MM(getattr(s,y),s.unit),5))
                for s in outline for x,y in [('x1','y1'),('x2','y2')]]
        corners = set(ends)
        dim = [round(max(v[k] for v in ends)-min(v[k] for v in ends),4) for k in (0,1)]
        require(len(corners)==4 and all(ends.count(v)==2 for v in corners) and dim==[68,48],
                'Outline or finished size differs from design')
        drill_dir = temp / 'drill'
        cli('pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm',
            '--excellon-zeros-format','decimal','--excellon-separate-th','-o',str(drill_dir)+'/',BOARD)
        drills = {}
        for f in drill_dir.glob('*.drl'):
            plated = 'NPTH' not in f.stem
            require(plated not in drills, 'Duplicate drill file')
            dest = copper / (STEM + ('-PTH.XLN' if plated else '-NPTH.XLN'))
            shutil.copyfile(f,dest)
            drills[plated] = dest
        require(set(drills) == {False,True}, 'Both plated and non-plated drill files required')
        ipc = copper / (STEM+'.d356')
        cli('pcb','export','ipcd356','-o',ipc,BOARD)
        pins, counts = check_reference(ipc,xml,drills)
        report = dict(revision=REVISION, source_sha256=hashes, geometry_sha256=geometry_digest, native_erc=0, native_drc=0,
                      unconnected=0, schematic_parity=0, outline_mm=dim, copper_layers=2,
                      schematic_pins_compared_with_ipc=pins, drills_compared_with_ipc=counts,
                      gerber_conductive_netlist_extracted=False, prototype_hardware_tested=False,
                      archives={})
        for folder, kind in [(copper,'gerber'), (stencil,'stencil')]:
            files = {f.name:sha(f) for f in sorted(folder.iterdir())}
            archive = built/(STEM+'-'+kind+'-prototype.zip')
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
                for name in files:
                    z.write(folder/name,name)
            with zipfile.ZipFile(archive) as z:
                require(z.testzip() is None and set(z.namelist()) == set(files) and
                        all(hashlib.sha256(z.read(n)).hexdigest()==v for n,v in files.items()),
                        'Archive inventory, checksum or CRC mismatch')
            report['archives'][archive.name] = dict(sha256=sha(archive), files_sha256=files)
        require(hashes == {str(f.relative_to(ROOT)):sha(f) for f in sources} and sha(geometry_path)==geometry_digest,
                'CAD source or geometry evidence changed during export')
        for filename in report['archives']:
            shutil.copyfile(built/filename,PROJECT/filename)
        (PROJECT/'checks/cam-package.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','archives')},indent=2))


if __name__ == '__main__':
    package()
