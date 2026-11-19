"""Generate the panel F display assembly and both native views using KiCad Python."""
from pathlib import Path
import os, pcbnew as p,json,hashlib
R=Path.cwd(); board=Path('hardware/panel-rev-f/pump-panel-rev-f.kicad_pcb'); O=board.parent
b=p.LoadBoard(str(board));components=[]
for f in b.GetFootprints():
 if f.GetReference().startswith('H'): continue
 paths=[]
 for m in f.Models():
  path=m.m_Filename.replace('${KIPRJMOD}',str(O.resolve()))
  resolved=Path(os.path.expandvars(path)); assert resolved.exists(), resolved
  paths.append(m.m_Filename)
  # KIPRJMOD will be different on temporary assembly preview.
  m.m_Filename=str(resolved)
 components.append({'reference':f.GetReference(),'models':paths})
part=p.FOOTPRINT(b);part.SetReference('Display');part.SetPosition(p.VECTOR2I(p.FromMM(12),p.FromMM(4)))
mdl=p.FP_3DMODEL();mdl.m_Filename=str((O/'models/Waveshare-14657-display-envelope.step').resolve());mdl.m_Offset.z=1
part.Add3DModel(mdl);b.Add(part)
from tempfile import TemporaryDirectory
import subprocess
# Mechanical previews add a stand-in for the separately supported operator display.
with TemporaryDirectory() as temp:
 preview=Path(temp)/'panel-display.kicad_pcb'
 p.SaveBoard(str(preview),b)
 preview.write_text(preview.read_text().replace('${KIPRJMOD}',str(O.resolve())))
 cli=str(R/'.tools/kicad-cli')
 def run(*args):
  proc=subprocess.run([cli,*map(str,args)],capture_output=True,text=True)
  if proc.returncode or 'Could not add 3D model' in proc.stdout+proc.stderr:
   raise RuntimeError(proc.stdout+proc.stderr)
 exports=(O/'exports').resolve()
 for source,extension,name in ((board,'step','pump-panel-rev-f'),(preview,'step','pump-panel-rev-f-with-display'),(preview,'glb','pump-panel-rev-f-with-display')):
  run('pcb','export',extension,'--force','-o',exports/(name+'.'+extension),source.resolve())
 for source,side,name in ((preview,'top','panel-front'),(board,'bottom','panel-rear')):
  run('pcb','render','--width','1100','--height','760','--side',side,'--rotate','16,0,8','-o',exports/(name+'.png'),source.resolve())
(O/'checks/model-coverage.json').write_text(json.dumps({'pcb_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'electrical_footprints':len(components),'with_models':len(components),'nominal_project_envelopes':['SW1','J7','external display (only in preview)'],'mating_plugs_cables_standoffs_modelled':False,'physical_fit_tested':False,'component_models':sorted(components,key=lambda c:c['reference'])},indent=2)+'\n')
