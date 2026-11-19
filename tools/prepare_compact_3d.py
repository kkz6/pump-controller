"""Prepare a component-body visualization copy; never save the native PCB."""
from pathlib import Path
import argparse,hashlib,json,os
import pcbnew as p
R=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--board',required=True,type=Path);a.add_argument('--visual',required=True,type=Path);a.add_argument('--coverage',required=True,type=Path);a.add_argument('--expected-sha256',required=True);a.add_argument('--private-inputs',required=True,type=Path);args=a.parse_args()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(args.board)==args.expected_sha256,'Selected PCB changed'
b=p.LoadBoard(str(args.board));defs=json.loads((R/'hardware/3d/approximate-bodies.json').read_text());lookup={ref:name for name,d in defs.items() for ref in d['references']};coverage=[];models={};public_models={}
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref=='C1':
  assert any('C1_EEUFR1E470_max_envelope.step' in x.m_Filename for x in f.Models()),'C1 maximum installed envelope is absent'
  filename=R/'hardware/3d/models/C1_EEUFR1E470_max_envelope.step';f.Models().clear();m=p.FP_3DMODEL();m.m_Filename=str(filename);f.Add3DModel(m);status='conservative_installed_envelope'
 elif ref=='J36' and any(x.m_Filename.endswith('JST_ZE_SM05B-ZESS-TB_envelope.step') for x in f.Models()):
  filename=R/'hardware/main-compact-dual/libraries/Connector_JST.3dshapes/JST_ZE_SM05B-ZESS-TB_envelope.step'
  f.Models().clear();m=p.FP_3DMODEL();m.m_Filename=str(filename);f.Add3DModel(m);status='conservative_installed_envelope'
 elif any(x.m_Filename.startswith('${KIPRJMOD}/libraries/CompactGuard.3dshapes/') for x in f.Models()):
  assert len(f.Models())==1, 'Expected one project connector body: '+ref
  filename=args.board.resolve().parent / f.Models()[0].m_Filename.removeprefix('${KIPRJMOD}/')
  f.Models().clear();m=p.FP_3DMODEL();m.m_Filename=str(filename);f.Add3DModel(m);status='nominal_project_body'
 elif ref in lookup:
  filename=R/'hardware/3d/models'/(lookup[ref]+'.step');f.Models().clear();m=p.FP_3DMODEL();m.m_Filename=str(filename);f.Add3DModel(m);status='approximate_project_body'
 elif ref.startswith('H'):status='mounting_hole_without_fastener'
 else:
  assert len(f.Models()),'Missing component model '+ref
  status='standard_library_body'
 for m in f.Models():
  filename=Path(os.path.expandvars(m.m_Filename));assert filename.exists(),str(filename)
  for source in [filename,*([filename.with_suffix('.step')] if filename.suffix.lower()=='.wrl' and filename.with_suffix('.step').exists() else [])]:
   models[str(source)]=sha(source)
   if source.is_relative_to(R):key='project/'+str(source.relative_to(R))
   else:
    library=Path(os.environ['KICAD10_3DMODEL_DIR'])
    key='KiCad10/'+str(source.relative_to(library)) if source.is_relative_to(library) else 'external/'+source.name
   assert key not in public_models or public_models[key]==models[str(source)]
   public_models[key]=models[str(source)]
 coverage.append({'reference':ref,'status':status,'side':'B' if f.IsFlipped() else 'F','xy_mm':[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)]})
args.visual.parent.mkdir(parents=True,exist_ok=True);p.SaveBoard(str(args.visual),b);assert sha(args.board)==args.expected_sha256
args.coverage.parent.mkdir(parents=True,exist_ok=True)
args.coverage.write_text(json.dumps({'source_board_sha256':args.expected_sha256,'native_modified':False,'component_records':coverage,'model_sha256':public_models,'C1':'6x6mm XY and13.5mm installed depth envelope; trimmed leads3mm beyond opposite face','Y1':'Generic HC49-SD model is nominal4mm high. Abracon ABLS drawing specifies4.2mm maximum; model bounds are not tolerance-qualified.','Y1_primary_source':'https://abracon.com/Resonators/ABLS.pdf','physical_fit_tested':False},indent=2)+'\n')
args.private_inputs.parent.mkdir(parents=True,exist_ok=True);args.private_inputs.write_text(json.dumps(models,indent=2)+'\n')
print('Prepared',len(coverage),'native footprint bodies/holes')
