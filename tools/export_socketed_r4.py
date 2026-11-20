"""Export and independently check the socketed R4 main PCB and its five-button panel."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

from gerbonara import GerberFile
from gerbonara.utils import MM
from shapely.geometry import LinearRing
from shapely.ops import linemerge
from cam.check_archives import UPSTREAM, check
from export_main_rev_e import LAYERS
from prepare_jlc_assembly import catalog, prepare

ROOT = Path(__file__).resolve().parents[1]
CLI = os.environ.get('KICAD_CLI', str(ROOT / '.tools/kicad-cli'))
OUTPUT = ROOT / 'output/socketed-r4'
BOARDS = {
    'main': ('main-socketed', 'pump-controller-integrated', (100, 117), 6, 'integrated'),
    'panel': ('panel-rev-f', 'pump-panel-rev-f', (60, 45), 2, 'panel'),
}


def run(*args):
    subprocess.run([CLI, *map(str, args)], check=True, stdout=subprocess.DEVNULL)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(path, members):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(members.items()):
            z.writestr(name, data)


def board_outputs(name, temp, driver):
    directory, stem, dimensions, layers, profile = BOARDS[name]
    source = ROOT / 'hardware' / directory
    pcb = source / (stem + '.kicad_pcb')
    schematic = pcb.with_suffix('.kicad_sch')
    inputs = [pcb, pcb.with_suffix('.kicad_pro'), pcb.with_suffix('.kicad_dru'),
              source / 'bom.csv', source / 'Pump.kicad_sym', source / 'fp-lib-table',
              *source.glob('*.kicad_sch'), *source.glob('Socket.pretty/*.kicad_mod')]
    snapshot = {p: digest(p) for p in inputs}
    erc, drc = [temp / (name + '-' + kind + '.json') for kind in ('erc','drc')]
    run('sch','erc','--severity-all','--exit-code-violations','--format','json','-o',erc,schematic)
    run('pcb','drc','--severity-all','--all-track-errors','--schematic-parity',
        '--exit-code-violations','--format','json','-o',drc,pcb)
    roles = dict(LAYERS)
    if layers == 2:
        roles = {key: value for key,value in roles.items() if not key.startswith('In')}
        roles['B_Cu'] = ('GBL','Copper,L2,Bot')
    plots = temp / (name + '-plots')
    run('pcb','export','gerbers','--layers',','.join(k.replace('_','.') for k in roles),
        '--disable-aperture-macros','--subtract-soldermask','--check-zones',
        '--precision','6','-o',str(plots)+'/',pcb)
    members, renamed = {}, {}
    for layer,(ext,role) in roles.items():
        [plot] = plots.glob('*-' + layer + '.g*')
        data = plot.read_bytes()
        if ('%TF.FileFunction,'+role+'*%').encode() not in data:
            raise ValueError(f'{name}: unexpected layer attributes for {layer}')
        filename = name + '.' + ext
        members[filename] = data
        renamed[plot.name] = filename
        if layer == 'Edge_Cuts':
            geometry = GerberFile.open(plot)
            edges = [[(o.unit.convert_to(MM, o.x1), o.unit.convert_to(MM, o.y1)),
                      (o.unit.convert_to(MM, o.x2), o.unit.convert_to(MM, o.y2))]
                     for o in geometry.objects]
            outline = linemerge(edges)
            if not outline.is_ring:
                raise ValueError(f'{name}: profile is open or intersects itself')
            x1,y1,x2,y2 = LinearRing(outline.coords).bounds
            if (round(x2-x1,3),round(y2-y1,3)) != dimensions:
                raise ValueError(f'{name}: unexpected cut dimensions')
    [job_path] = plots.glob('*.gbrjob')
    job = json.loads(job_path.read_text())
    for entry in job['FilesAttributes']:
        entry['Path'] = renamed[entry['Path']]
    if {f['Path'] for f in job['FilesAttributes']} != set(members):
        raise ValueError(f'{name}: job is missing a Gerber')
    job['GeneralSpecs']['Size'] = dict(zip(('X','Y'), dimensions))
    members[name+'.gbrjob'] = json.dumps(job, indent=2)+'\n'
    drills = temp / (name + '-drills')
    run('pcb','export','drill','--format','excellon','--drill-origin','absolute',
        '--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th',
        '-o',str(drills)+'/',pcb)
    for kind in ('PTH','NPTH'):
        [path] = drills.glob('*-' + kind + '.drl')
        members[name+'-'+kind+'.XLN'] = path.read_bytes()
    ipc = temp / (name+'.d356')
    run('pcb','export','ipcd356','-o',ipc,pcb)
    members[ipc.name] = ipc.read_bytes()
    fab = temp / (name+'-gerbers.zip')
    archive(fab, members)
    paste = temp / (name+'-paste')
    run('pcb','export','gerbers','--layers','F.Paste,B.Paste','--disable-aperture-macros',
        '--precision','6','-o',str(paste)+'/',pcb)
    stencil = temp / (name+'-stencil.zip')
    archive(stencil, {name+'.'+ext: next(paste.glob('*-'+side+'_Paste.g*')).read_bytes()
                      for side,ext in [('F','GTP'),('B','GBP')]})
    prepare(name, directory, stem, catalog(), destination=temp)
    record, controls = check(profile, driver, str(fab.relative_to(ROOT)))
    record['path'] = 'output/socketed-r4/'+fab.name
    if any(digest(p) != old for p,old in snapshot.items()):
        raise ValueError(f'{name}: source changed during validation')
    return {'source_sha256':{str(p.relative_to(ROOT)):h for p,h in snapshot.items()},
            'cut_dimensions_mm':dimensions,'copper_layers':layers,'connectivity':record,
            'injected_faults_detected':controls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compare', type=Path, required=True, help='Built tools/cam/compare.cpp')
    driver = parser.parse_args().compare.resolve()
    OUTPUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT) as work:
        temp = Path(work)
        checks = {n:board_outputs(n,temp,driver) for n in BOARDS}
        results = [p for p in temp.iterdir() if p.is_file() and p.suffix in ('.csv','.zip','.json')]
        report = {'kicad_version':subprocess.check_output([CLI,'version'],text=True).strip(),
                  'gerbertools_commit':UPSTREAM,'boards':checks,
                  'output_sha256':{p.name:digest(p) for p in sorted(results)}}
        (temp/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
        for p in [*results,temp/'verification.json']:
            p.replace(OUTPUT / p.name)


if __name__ == '__main__':
    main()
