"""Export current compact PCB bodies and previews without changing native CAD."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--expected-pcb-sha256',required=True);args=a.parse_args()
board=R/'hardware/main-compact/pump-controller-compact.kicad_pcb';out=board.parent/'exports';out.mkdir(exist_ok=True);visual=R/'tmp/3d/pump-controller-compact-visualization.kicad_pcb';coverage=out/'model-coverage.json';private_inputs=R/'tmp/3d/compact-model-inputs.json';logs=R/'tmp/compact-model-logs';logs.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixed={board:args.expected_pcb_sha256,R/'design/main-compact.json':sha(R/'design/main-compact.json')}
def check():
 for p,h in fixed.items():assert sha(p)==h,'Source changed: '+str(p)
def run(name,cmd):
 check();r=subprocess.run([str(v) for v in cmd],cwd=R,capture_output=True,text=True);(logs/(name+'.log')).write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(name+' failed')
 check();print(name+' complete',flush=True)
run('prepare-model',[R/'.tools/kicad-python',R/'tools/prepare_compact_3d.py','--board',board,'--visual',visual,'--coverage',coverage,'--expected-sha256',args.expected_pcb_sha256,'--private-inputs',private_inputs])
c=json.loads(coverage.read_text());fixed.update({Path(p):h for p,h in json.loads(private_inputs.read_text()).items()})
for kind in ['step','glb']:
 run('export-'+kind,[R/'.tools/kicad-cli','pcb','export',kind,'--force','--subst-models','--user-origin','0x0mm','-o',out/('pump-controller-compact.'+kind),visual])
r=STEPControl_Reader();assert int(r.ReadFile(str(out/'pump-controller-compact.step')))==1;r.TransferRoots();b=Bnd_Box();BRepBndLib.Add_s(r.OneShape(),b);lo,hi=b.CornerMin(),b.CornerMax();bounds=[[lo.X(),lo.Y(),lo.Z()],[hi.X(),hi.Y(),hi.Z()]]
record={'native_board_sha256':args.expected_pcb_sha256,'source_sha256':sha(R/'design/main-compact.json'),'coverage_sha256':sha(coverage),'native_modified':False,'scope':'Populated component-body preview; not a tolerance-qualified fit or safety approval','model_bounds_mm':bounds,'modeled_populated_thickness_mm':hi.Z()-lo.Z(),'modeled_rear_depth_mm':-lo.Z(),'modeled_front_height_above_1p6_board_mm':hi.Z()-1.6,'Y1_maximum_body_height_from_manufacturer_mm':4.2,'Y1_model_is_nominal_not_installed_maximum':True,'physical_fit_tested':False,'model_input_sha256':c['model_sha256'],'generator_sha256':{str(p.relative_to(R)):sha(p) for p in [R/'tools/prepare_compact_3d.py',R/'tools/export_compact_3d.py',R/'tools/render_compact_3d.py']}}
(out/'model-verification.json').write_text(json.dumps(record,indent=2)+'\n')
run('render-model',[sys.executable,R/'tools/render_compact_3d.py'])
record['output_sha256']={str(p.relative_to(R)):sha(p) for p in [out/'pump-controller-compact.step',out/'pump-controller-compact.glb',coverage,R/'output/compact/pcb-front.png',R/'output/compact/pcb-back.png',R/'output/compact/pcb-preview.png']}
check();(out/'model-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['native_board_sha256','modeled_populated_thickness_mm','modeled_rear_depth_mm','modeled_front_height_above_1p6_board_mm']},indent=2))
