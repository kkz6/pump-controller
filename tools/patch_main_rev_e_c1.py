#!/usr/bin/env python3
"""Update C1 courtyard/model only; preserve all pad and routing geometry.

Run with .tools/kicad-python. --board is explicit; library copies are updated
only with --update-libraries. No source/BOM/component fields are changed.
"""
from pathlib import Path
import argparse,hashlib,json,re,tempfile
BASE=Path(__file__).resolve().parents[1]
NAME='CP_Radial_D5_P2_Pads1p5'
MODEL='${KIPRJMOD}/../3d/models/C1_EEUFR1E470_max_envelope.step'

def span(text):
 for m in re.finditer(r'^\t\(footprint ',text,re.M):
  start=m.start()+1;depth=0;quoted=False;escaped=False
  for i in range(start,len(text)):
   c=text[i]
   if quoted:
    if escaped:escaped=False
    elif c=='\\':escaped=True
    elif c=='"':quoted=False
   elif c=='"':quoted=True
   elif c=='(':depth+=1
   elif c==')':
    depth-=1
    if depth==0:
     if re.search(r'\(property "Reference" "C1"\s',text[start:i+1]):return start,i+1
     break
 raise ValueError('C1 native footprint block is missing')

def pad_record(fp):
 return sorted((x.GetNumber(),x.m_Uuid.AsString(),x.GetPosition().x,x.GetPosition().y,
                x.GetSize().x,x.GetSize().y,x.GetDrillSize().x,x.GetDrillSize().y,
                x.GetNetname()) for x in fp.Pads())

def change(fp,p):
 pads=list(fp.Pads());assert len(pads)==2
 assert abs((pads[0].GetPosition()-pads[1].GetPosition()).EuclideanNorm()-p.FromMM(2))<2
 assert abs(fp.GetOrientationDegrees()/90-round(fp.GetOrientationDegrees()/90))<1e-6
 cx=sum(x.GetPosition().x for x in pads)//2;cy=sum(x.GetPosition().y for x in pads)//2
 for g in list(fp.GraphicalItems()):
  if g.GetLayer() in [p.F_CrtYd,p.B_CrtYd]:fp.Remove(g)
 shape=p.PCB_SHAPE(fp);shape.SetShape(p.SHAPE_T_RECT)
 shape.SetStart(p.VECTOR2I(cx-p.FromMM(3.25),cy-p.FromMM(3.25)))
 shape.SetEnd(p.VECTOR2I(cx+p.FromMM(3.25),cy+p.FromMM(3.25)))
 shape.SetWidth(p.FromMM(.05));shape.SetLayer(p.B_CrtYd if fp.IsFlipped() else p.F_CrtYd);fp.Add(shape)
 fp.Models().clear();model=p.FP_3DMODEL();model.m_Filename=MODEL;fp.Add3DModel(model)
 fp.SetLibDescription('C1 radial P2.0; original pads retained; 6.5mm courtyard and conservative EEUFR1E470 installed envelope, maximum rear depth13.5mm')

def patch(board_path,update_libraries=False):
 import wx
 app=wx.GetApp() or wx.App(False)
 import pcbnew as p
 board_path=board_path.resolve();oldtext=board_path.read_text()
 pro=board_path.with_suffix('.kicad_pro');probytes=pro.read_bytes() if pro.exists() else None
 b=p.LoadBoard(str(board_path));fp=b.FindFootprintByReference('C1');assert fp is not None
 assert str(fp.GetFPID().GetLibItemName())==NAME
 before=pad_record(fp);uid=fp.m_Uuid.AsString();position=fp.GetPosition();rotation=fp.GetOrientationDegrees()
 change(fp,p);assert pad_record(fp)==before
 fp.BuildCourtyardCaches();layer=p.B_CrtYd if fp.IsFlipped() else p.F_CrtYd;court=fp.GetCourtyard(layer)
 overlaps=[]
 for other in b.GetFootprints():
  if other.GetReference()=='C1':continue
  other.BuildCourtyardCaches();oc=other.GetCourtyard(layer)
  if oc.OutlineCount() and court.Collide(oc):overlaps.append(other.GetReference())
 assert not overlaps,'C1 expanded courtyard overlaps: '+str(overlaps)
 with tempfile.TemporaryDirectory(prefix='pump-c1-envelope-') as folder:
  q=Path(folder)/board_path.name;p.SaveBoard(str(q),b);serialized=q.read_text();a,z=span(serialized);s,e=span(oldtext)
  board_path.write_text(oldtext[:s]+serialized[a:z]+oldtext[e:])
 verified_board=p.LoadBoard(str(board_path));check=verified_board.FindFootprintByReference('C1')
 assert pad_record(check)==before and check.m_Uuid.AsString()==uid
 assert check.GetPosition()==position and check.GetOrientationDegrees()==rotation
 if probytes is not None:assert pro.read_bytes()==probytes
 if update_libraries:
  for directory in [BASE/'hardware/main-rev-e/PumpRevE.pretty',BASE/'hardware/main-rev-e/libraries/PumpRevE.pretty']:
   item=p.FootprintLoad(str(directory),NAME);bp=pad_record(item);change(item,p);assert pad_record(item)==bp
   p.PCB_IO_KICAD_SEXPR().FootprintSave(str(directory),item)
 return {'pcb_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),
         'original_pcb_sha256':hashlib.sha256(oldtext.encode()).hexdigest(),
         'footprint':'PumpRevE:'+NAME,'pad_uuids_geometry_and_nets_preserved':True,
         'footprint_uuid_position_and_rotation_preserved':True,'outside_C1_text_unchanged':True,
         'library_description_updated_to_installed_envelope':True,
         'project_unchanged':True,'courtyard_square_mm':6.5,'courtyard_overlaps':overlaps,
         'installed_body_depth_mm':13.5,'model_reference':MODEL,'requires_native_DRC_and_fresh_3D_fit_check':True}

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--board',required=True,type=Path)
 ap.add_argument('--update-libraries',action='store_true');ap.add_argument('--report',type=Path);a=ap.parse_args()
 r=patch(a.board,a.update_libraries)
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
