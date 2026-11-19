"""Package individual mechanical prototype parts; no service upload/order."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/enclosure-rev-e';HERE=Path(__file__).resolve().parent
m=json.loads((OUT/'manifest.json').read_text());c=json.loads((OUT/'fit-checks.json').read_text())
assert c['all_print_parts_valid_watertight_single_solid']
assert not c['printed_part_collisions'] and not c['reference_component_interferences'] and not c['provisional_panel_plug_reservation_interferences']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert c['main_pcb_sha256']==sha(ROOT/'hardware/main-rev-e/pump-controller-main-rev-e.kicad_pcb'),'Main PCB changed after fit checks'
assert c['main_model_export_provenance_sha256']==sha(ROOT/'hardware/3d/rev-e-export-manifest.json'),'Main model provenance changed after fit checks'
assert m['parameters_sha256']==sha(HERE/'parameters.json'),'Parameters changed after geometry build'
for role,filename in [('main','hardware/main-rev-e/exports/pump-controller-main-rev-e.step'),('panel','hardware/panel-rev-e/exports/pump-panel-rev-e.step')]:
 assert c[role+'_step_sha256']==sha(ROOT/filename),role+' STEP changed after fit checks'
assert c['panel_connector_manifest_pcb_sha256']==sha(ROOT/'hardware/panel-rev-e/pump-panel-rev-e.kicad_pcb'),'Panel PCB changed after fit checks'
paths=[]
for p in m['parts'].values():
 assert p['sha256']==sha(OUT/p['stl']),'STL changed after geometry checks: '+p['stl']
 assert p['step_sha256']==sha(OUT/p['step']),'STEP changed after geometry checks: '+p['step']
 paths.extend([OUT/p['step'],OUT/p['stl']])
paths.extend([OUT/n for n in ['manifest.json','fit-checks.json','front-label-template.svg','window-cut-template.svg','assembled-preview.png','exploded-preview.png']])
paths.extend([HERE/'README.rst',HERE/'parameters.json'])
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
checks={'purpose':'Mechanical fit prototype; supplier process/material acceptance and physical fit remain outstanding','individual_parts':len(m['parts']),'default_assembly_parts':len(m['parts'])-1,'optional_part':'key_22p5_adapter_OPTIONAL replaces key_blank_plate','sha256':files}
(OUT/'package-manifest.json').write_text(json.dumps(checks,indent=2)+'\n')
paths.append(OUT/'package-manifest.json')
with zipfile.ZipFile(OUT/'enclosure-rev-e-mechanical-prototype.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in paths:z.write(p,p.name)
with zipfile.ZipFile(OUT/'enclosure-rev-e-mechanical-prototype.zip') as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(paths)
 assert all(z.read(p.name)==p.read_bytes() for p in paths),'Packaged file differs from checked output'
print('Verified package:',len(paths),'files;',len(m['parts']),'individual printable variants')
