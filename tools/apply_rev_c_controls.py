#!/usr/bin/env python3
"""One-time incremental Rev B→C control ECO; preserves the routed board.

D33/D34 are removed, the former diode-OR rail becomes STOP_RETURN, and
schematic association paths/metadata follow the current source. This helper
does not complete the new STOP_RETURN connection; a checked route patch does.
"""
from pathlib import Path
import json,re,uuid
import pcbnew as p
B=Path(__file__).resolve().parents[1];file=B/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(file));remove=[]
for ref in ['D33','D34']:
 fp=b.FindFootprintByReference(ref)
 if not fp:raise ValueError('Expected Rev B footprint '+ref+' is absent; do not replay this ECO')
 remove.append(str(fp.m_Uuid.AsString()))
# Remove only the obsolete manual-input spur back to its live resistor/via junction.
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname()!='MAN_RETURN':continue
 pts={(round(p.ToMM(v.x),4),round(p.ToMM(v.y),4)) for v in [t.GetStart(),t.GetEnd()]}
 if pts in [{(64.5,34.0),(63.125,32.625)},{(63.125,32.625),(63.125,28.3761)}]:remove.append(str(t.m_Uuid.AsString()))
assert len(remove)==4,remove
s=file.read_text();level=0;quoted=False;escape=False;spans=[];start=0
for i,ch in enumerate(s):
 if quoted:
  if escape:escape=False
  elif ch=='\\':escape=True
  elif ch=='"':quoted=False
 elif ch=='"':quoted=True
 elif ch=='(':
  level+=1
  if level==2:start=i
 elif ch==')':
  if level==2 and any(u in s[start:i+1] for u in remove):spans.append((start,i+1))
  level-=1
assert len(spans)==len(remove)
for a,z in reversed(spans):s=s[:a]+s[z:]
file.write_text(s);b=p.LoadBoard(str(file));nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()};stop=nets['STOP_RETURN'];count=0
for item in list(b.GetTracks())+[pad for fp in b.GetFootprints() for pad in fp.Pads()]+list(b.Zones()):
 if item.GetNetname()=='MODE_COIL_5V':item.SetNet(stop);count+=1
source=json.load(open(B/'design/circuit.json'));ns=uuid.UUID('65033db8-a70f-4e73-a9d7-049c9a7c8f95');uid=lambda s:str(uuid.uuid5(ns,s));project=source['project'];rootid=uid(project+':root')
for sh in source['sheets']:
 for c in sh['components']:
  if not c.get('on_board',True):continue
  fp=b.FindFootprintByReference(c['ref'])
  if fp is None and c['ref'] in ['SW3','SW4']:continue
  assert fp is not None,c['ref']
  sid=re.sub(r'[^A-Za-z0-9_.-]+','_',sh['id'])
  fp.SetPath(p.KIID_PATH('/'+rootid+'/'+uid(project+':sheet:'+sid)+'/'+uid('component:'+c['ref'])))
  fp.SetValue(c['value'])
title=b.GetTitleBlock();title.SetTitle(source['title']);title.SetRevision('C-DRAFT');b.SetTitleBlock(title)
fill=p.ZONE_FILLER(b);fill.Fill(b.Zones());p.SaveBoard(str(file),b)
# The old net is now unused; remove any retained native declaration only.
s=file.read_text();s=re.sub(r'\n\s*\(net \d+ "MODE_COIL_5V"\)','',s);file.write_text(s)
print('Removed two diodes and obsolete manual spur; merged',count,'items into STOP_RETURN')
