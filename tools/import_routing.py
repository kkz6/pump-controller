#!/usr/bin/env python3
"""Import the router session, refill planes, and record board/netlist checks."""
from pathlib import Path
import json,argparse,subprocess,shutil,os,hashlib
import wx
app=wx.App(False)
import pcbnew as p
BASE=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,default=BASE/'hardware/pump-controller-rev-b.ses');ap.add_argument('--check-only',action='store_true');args=ap.parse_args()
file=BASE/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(file))
if not args.check_only and not p.ImportSpecctraSES(b,str(args.session)):raise RuntimeError('Router session import failed')
latest=json.load(open(BASE/'design/circuit.json')); values={c['ref']:c['value'] for sh in latest['sheets'] for c in sh['components'] if c.get('on_board',True)}
metadata={c['ref']:c for sh in latest['sheets'] for c in sh['components'] if c.get('on_board',True)}
for fp in b.GetFootprints():
 if fp.GetReference() in values:
  fp.SetValue(values[fp.GetReference()]);c=metadata[fp.GetReference()]
  for key,value in [('MPN',c.get('mpn','')),('Datasheet',c.get('datasheet',''))]:
   fp.SetField(key,value);fp.GetField(key).SetVisible(False)
f=p.ZONE_FILLER(b);f.Fill(b.Zones());p.SaveBoard(str(file),b)
cli=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or str(BASE/'.tools/kicad-cli')
report=BASE/'hardware/checks/main-drc.json';subprocess.run([cli,'pcb','drc','--format','json','-o',str(report),str(file)],check=True)
d=json.load(open(BASE/'design/circuit.json'));expected={c['ref']:c for s in d['sheets'] for c in s['components'] if c.get('on_board',True)};actual={f.GetReference():f for f in b.GetFootprints()};mismatches=[];pin_count=0
for ref,c in expected.items():
 if ref not in actual:mismatches.append({'ref':ref,'reason':'missing footprint'});continue
 f=actual[ref]
 fid=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
 if fid!=c['footprint']:mismatches.append({'ref':ref,'reason':'footprint mismatch','expected':c['footprint'],'actual':fid})
 if f.GetValue()!=c['value']:mismatches.append({'ref':ref,'reason':'value mismatch','expected':c['value'],'actual':f.GetValue()})
 pm={str(pin['num']):pin.get('net') or '' for pin in c['pins']}
 missing=set(pm)-{pad.GetNumber() for pad in f.Pads()}
 if missing:mismatches.append({'ref':ref,'reason':'missing physical pads','pins':sorted(missing)})
 for pad in f.Pads():
  num=pad.GetNumber()
  if not num and not any(pad.IsOnLayer(layer) for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]):continue
  if num not in pm:mismatches.append({'ref':ref,'pin':num,'reason':'unmapped pad'});continue
  pin_count+=1
  if pad.GetNetname()!=pm[num]:mismatches.append({'ref':ref,'pin':num,'expected':pm[num],'actual':pad.GetNetname()})
for ref in sorted(set(actual)-set(expected)-{'H1','H2'}):mismatches.append({'ref':ref,'reason':'unexpected footprint'})
checks={'pcb_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'circuit_sha256':hashlib.sha256((BASE/'design/circuit.json').read_bytes()).hexdigest(),'electrical_component_count':len(expected),'physical_pad_count':pin_count,'mismatches':mismatches,'passed':not mismatches}
(BASE/'hardware/checks/board-netlist-check.json').write_text(json.dumps(checks,indent=2)+'\n')
drc=json.load(open(report));v=drc['violations'];thermal=sum(z.GetFilledArea()/1e12 for z in b.Zones() if z.GetLayer()==p.B_Cu and z.GetNetname() in ['+5V','GND'])
summary={'pcb_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'board':'pump-controller-rev-b','revision':d.get('revision','B'),'dimensions_mm':[90,70],'layers':b.GetCopperLayerCount(),'component_count':len(expected),'mounting_hole_count':2,'bottom_side_components':sum(f.GetLayer()==p.B_Cu for r,f in actual.items() if r in expected),'remaining_unrouted':len(drc['unconnected_items']),'native_drc_errors':sum(x['severity']=='error' for x in v),'native_drc_warnings':sum(x['severity']=='warning' for x in v),'board_netlist_matches_source':not mismatches,'R2_filled_copper_mm2':round(thermal,2),'R2_required_copper_mm2':300,'isolation_corridor_mm':8,'release_ready':False,'release_status':'Engineering prototype; independent circuit/land-pattern review, electrical and thermal validation remain required.'}
(BASE/'hardware/checks/layout-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if mismatches:raise RuntimeError('Board does not match final circuit source')
