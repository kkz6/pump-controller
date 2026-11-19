#!/usr/bin/env python3
"""Inventory actual via-drill overlap with SMT copper; no DFM waiver implied."""
from pathlib import Path
import json,hashlib
import pcbnew as p
B=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(B/'hardware/pump-controller-rev-b.kicad_pcb'));out=[]
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA):continue
 pos=t.GetPosition();di=t.GetDrillValue();od=t.GetWidth(p.F_Cu)
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
   for layer in [p.F_Cu,p.B_Cu]:
    if not pad.IsOnLayer(layer):continue
    shape=pad.GetEffectiveShape(layer)
    if shape.Collide(pos,int(di/2)):
     out.append({'ref':f.GetReference(),'pad':pad.GetNumber(),'net':pad.GetNetname(),'side':b.GetLayerName(layer),'via_xy_mm':[p.ToMM(pos.x),p.ToMM(pos.y)],'via_diameter_mm':p.ToMM(od),'drill_mm':p.ToMM(di),'via_uuid':str(t.m_Uuid.AsString()),'center_inside_pad':shape.Collide(pos,0)})
     break
result={'pcb_sha256':hashlib.sha256((B/'hardware/pump-controller-rev-b.kicad_pcb').read_bytes()).hexdigest(),'method':'Native effective copper pad geometry intersects finished-drill nominal disk; includes edge intersections. Does not substitute for CAM/assembly review.','mandatory_process':'Filled and plated-over vias for every listed SMT-pad drill overlap, or reroute before fabrication. Tenting alone is not accepted.','overlap_count':len(out),'unique_via_count':len({x['via_uuid'] for x in out}),'overlaps':sorted(out,key=lambda x:(x['ref'],x['pad'],x['via_xy_mm']))}
(B/'hardware/checks/via-in-pad-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

summary_path=B/'hardware/checks/layout-summary.json'
if summary_path.exists():
 summary=json.load(open(summary_path))
 if summary.get('pcb_sha256')==result['pcb_sha256']:
  summary.update(via_in_pad_unique_vias=result['unique_via_count'],via_in_pad_pad_overlaps=result['overlap_count'],via_in_pad_process=result['mandatory_process']);summary_path.write_text(json.dumps(summary,indent=2)+'\n')
