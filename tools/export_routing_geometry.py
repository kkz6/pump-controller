from pathlib import Path
import json
import pcbnew as p
B=Path(__file__).resolve().parents[1];file=B/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(file));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
def xy(z):return [p.ToMM(z.x),p.ToMM(z.y)]
shapes=[];items={}
for f in b.GetFootprints():
 for d in f.Pads():
  ls=[i for i,l in enumerate(layers) if d.IsOnLayer(l)]
  if not ls:continue
  bb=d.GetBoundingBox();q={'kind':'pad','net':d.GetNetname(),'layers':ls,'bbox':[p.ToMM(n) for n in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]],'point':xy(d.GetPosition()),'circle':d.GetShape()==p.PAD_SHAPE_CIRCLE,'ref':f.GetReference(),'pin':d.GetNumber(),'uuid':str(d.m_Uuid.AsString())}
  shapes.append(q);items[q['uuid']]=q
for t in b.GetTracks():
 q={'net':t.GetNetname(),'uuid':str(t.m_Uuid.AsString())}
 if isinstance(t,p.PCB_VIA):q.update(kind='via',point=xy(t.GetPosition()),width=p.ToMM(t.GetWidth(p.F_Cu)),layers=[0,1,2,3])
 else:q.update(kind='track',point=xy(t.GetStart()),end=xy(t.GetEnd()),width=p.ToMM(t.GetWidth()),layers=[layers.index(t.GetLayer())])
 shapes.append(q);items[q['uuid']]=q
r=json.load(open(B/'hardware/checks/main-drc.json'));targets=[]
for c in r['unconnected_items']:
 a,z=c['items'];a=items[a['uuid']];z=items[z['uuid']];targets.append({'net':a['net'],'a':a,'b':z})
(B/'hardware/checks/routing-geometry.json').write_text(json.dumps({'shapes':shapes,'targets':targets}));print('Shapes',len(shapes),'targets',len(targets))
