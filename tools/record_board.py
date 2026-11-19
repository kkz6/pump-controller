#!/usr/bin/env python3
"""Record final native placement and export the current routed DSN."""
from pathlib import Path
import json
import pcbnew as p
B=Path(__file__).resolve().parents[1];f=B/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(f));placement=json.load(open(B/'design/pcb-placement.json'));items=[]
for fp in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
 ref=fp.GetReference();xy=fp.GetPosition();x,y=p.ToMM(xy.x),p.ToMM(xy.y);rotation=fp.GetOrientationDegrees();side='B' if fp.GetLayer()==p.B_Cu else 'F'
 if ref in placement['components']:placement['components'][ref].update(x=x,y=y,rotation=rotation,side=side)
 pads={}
 for pad in fp.Pads():
  if not pad.GetNumber():continue
  pos=pad.GetPosition();pads[pad.GetNumber()]={'x':p.ToMM(pos.x),'y':p.ToMM(pos.y),'net':pad.GetNetname()}
 items.append({'ref':ref,'value':fp.GetValue(),'footprint':str(fp.GetFPID().GetLibNickname())+':'+str(fp.GetFPID().GetLibItemName()),'x':x,'y':y,'rotation':rotation,'side':side,'pads':pads})
summary=json.load(open(B/'hardware/checks/layout-summary.json'))
(B/'design/pcb-placement.json').write_text(json.dumps(placement,indent=2)+'\n')
(B/'hardware/placement.json').write_text(json.dumps({'width':90.0,'height':70.0,'layers':4,'routed':summary['remaining_unrouted']==0,'remaining_unrouted':summary['remaining_unrouted'],'verification':'checks/layout-summary.json','components':items},indent=2)+'\n')
if not p.ExportSpecctraDSN(b,str(f.with_suffix('.dsn'))):raise RuntimeError('DSN export failed')
print('Recorded',len(items),'footprints and final native DSN')
