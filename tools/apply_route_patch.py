from pathlib import Path
import json,argparse
import pcbnew as p
B=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('patch',type=Path);args=ap.parse_args();patch=json.load(open(args.patch));f=B/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(f));remove=[]
def xy(v):return p.ToMM(v.x),p.ToMM(v.y)
def near(a,z):return sum((x-y)**2 for x,y in zip(a,z))<1e-8
for r in patch.get('remove',[]):
 found=[]
 for t in b.GetTracks():
  vi=isinstance(t,p.PCB_VIA)
  if t.GetNetname()!=r['net'] or vi!=r.get('via',False):continue
  a=xy(t.GetPosition() if vi else t.GetStart());z=a if vi else xy(t.GetEnd())
  if not vi and b.GetLayerName(t.GetLayer())!=r['layer']:continue
  if (near(a,r['a']) and near(z,r['b'])) or (near(a,r['b']) and near(z,r['a'])):found.append(str(t.m_Uuid.AsString()))
 if len(found)!=1:raise ValueError('Removal must uniquely match: '+str(r)+' found '+str(found))
 remove+=found
if remove:
 s=f.read_text();level=0;quoted=False;escaped=False;start=0;spans=[]
 for i,ch in enumerate(s):
  if quoted:
   if escaped:escaped=False
   elif ch=='\\':escaped=True
   elif ch=='"':quoted=False
  elif ch=='"':quoted=True
  elif ch=='(':
   level+=1
   if level==2:start=i
  elif ch==')':
   if level==2 and any(u in s[start:i+1] for u in remove):spans.append((start,i+1))
   level-=1
 if len(spans)!=len(remove):raise ValueError('UUID block mismatch')
 for a,z in reversed(spans):s=s[:a]+s[z:]
 f.write_text(s)
b=p.LoadBoard(str(f));nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()};ls={'F.Cu':p.F_Cu,'B.Cu':p.B_Cu,'In1.Cu':p.In1_Cu,'In2.Cu':p.In2_Cu}
def pos(a):return p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1]))
for r in patch.get('add',[]):
 for a,z in zip(r['points'],r['points'][1:]):
  if a[2]!=z[2]:
   t=p.PCB_VIA(b);t.SetPosition(pos(a));t.SetWidth(p.FromMM(r.get('via_width',.4)));t.SetDrill(p.FromMM(r.get('via_drill',.2)));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu)
  else:
   if a[:2]==z[:2]:continue
   t=p.PCB_TRACK(b);t.SetStart(pos(a));t.SetEnd(pos(z));t.SetWidth(p.FromMM(r.get('width',.15)));t.SetLayer(ls[a[2]])
  t.SetNet(nets[r['net']]);b.Add(t)
fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(f),b);print('Removed',len(remove),'items; added',len(patch.get('add',[])),'routes')
