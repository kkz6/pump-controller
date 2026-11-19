#!/usr/bin/env python3
"""Add the two Rev C onboard settings switches to an existing routed board.

This preserves existing copper. Route the newly added pads separately and
run native ERC/DRC/netlist checks before accepting the result.
"""
from pathlib import Path
import json,os,re,uuid,shutil
import pcbnew as p
B=Path(__file__).resolve().parents[1];file=B/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(file));source=json.load(open(B/'design/circuit.json'));parts={c['ref']:(s,c) for s in source['sheets'] for c in s['components'] if c.get('on_board',True)};nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
lib='Button_Switch_SMD';name='SW_SPST_B3U-1000P';libdir=B/'hardware/libraries'/(lib+'.pretty');libdir.mkdir(exist_ok=True)
if not (libdir/(name+'.kicad_mod')).exists():
 src=Path(os.environ['KICAD10_FOOTPRINT_DIR'])/(lib+'.pretty')/(name+'.kicad_mod');shutil.copyfile(src,libdir/src.name)
ns=uuid.UUID('65033db8-a70f-4e73-a9d7-049c9a7c8f95');uid=lambda s:str(uuid.uuid5(ns,s));project=source['project'];rootid=uid(project+':root')
for ref,x,y,label in [('SW3',85,12,'SET'),('SW4',85,18,'NEXT')]:
 if b.FindFootprintByReference(ref):raise ValueError(ref+' already exists; do not replay')
 sh,c=parts[ref];f=p.FootprintLoad(str(libdir),name);f.SetReference(ref);f.SetValue(c['value']);f.SetFPID(p.LIB_ID(lib,name));b.Add(f);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
 for pad in f.Pads():pad.SetNet(nets[next(pin['net'] for pin in c['pins'] if pin['num']==pad.GetNumber())])
 f.Value().SetVisible(False)
 for key,value in [('MPN',c['mpn']),('Datasheet',c['datasheet'])]:f.SetField(key,value);f.GetField(key).SetVisible(False)
 f.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));f.Reference().SetTextThickness(p.FromMM(.12))
 text=p.PCB_TEXT(b);text.SetText(label);text.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y+2.25)));text.SetLayer(p.F_SilkS);text.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));text.SetTextThickness(p.FromMM(.12));b.Add(text)
# Synchronize all native hierarchy links after source pagination changes.
for ref,(sh,c) in parts.items():
 f=b.FindFootprintByReference(ref);assert f,ref;sid=re.sub(r'[^A-Za-z0-9_-]','_',sh['id']);f.SetPath(p.KIID_PATH('/'+rootid+'/'+uid(project+':sheet:'+sid)+'/'+uid('component:'+ref)));f.SetValue(c['value'])
fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(file),b)
print('Added SW3 SET at85,12 and SW4 NEXT at85,18 on F.Cu')
