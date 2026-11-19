from pathlib import Path
import json,uuid,sys,os
import wx
app=wx.App(False)
import pcbnew as p
BASE=Path(__file__).resolve().parents[1];hw=BASE/'hardware';file=hw/'pump-controller-rev-b.kicad_pcb'
def live(n):return n in {'MAINS_L','MAINS_N','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT'} or n.startswith('M_')
data=json.load(open(BASE/'design/circuit.json'));nets=sorted({pin['net'] for sh in data['sheets'] for c in sh['components'] for pin in c['pins'] if pin.get('net')})
pro=json.load(open(file.with_suffix('.kicad_pro')))
pro['net_settings']={'meta':{'version':3},'classes':[{'name':name,'clearance':.15,'track_width':.2,'via_diameter':.55,'via_drill':.25,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.2} for name in ['Default','LIVE','SELV']], 'netclass_patterns':[{'netclass':'LIVE' if live(n) else 'SELV','pattern':n} for n in nets]}
pro['board']={'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.4,'min_through_hole_diameter':.2,'min_copper_edge_clearance':.3,'min_hole_clearance':.25}}}
file.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
file.with_suffix('.kicad_dru').write_text('''(version 1)
(rule "Reinforced live to isolated control separation"
  (condition "(A.NetClass == 'LIVE' && B.NetClass == 'SELV') || (A.NetClass == 'SELV' && B.NetClass == 'LIVE')")
  (constraint clearance (min 8mm)))
''')
b=p.LoadBoard(str(file)); b.GetDesignSettings().m_MinClearance=p.FromMM(.15);b.GetDesignSettings().m_TrackMinWidth=p.FromMM(.15)
lib=Path(os.environ.get('KICAD10_FOOTPRINT_DIR',str(BASE/'hardware/libraries')))
for ref,x,y in [('H1',87,3),('H2',87,67)]:
 if ref in [f.GetReference() for f in b.GetFootprints()]:continue
 f=p.FootprintLoad(str(lib/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5');f.SetReference(ref);f.Value().SetVisible(False);f.Reference().SetVisible(False);f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));b.Add(f)
p.SaveBoard(str(file),b)
s=file.read_text()
for net,x1,x2 in [('GND',46,56.75),('+5V',57.25,68)]:
 n=next(n for n in b.GetNetsByNetcode().values() if n.GetNetname()==net)
 z='''(zone (net %d) (net_name "%s") (layer "B.Cu") (uuid "%s") (hatch edge 0.5) (priority 5) (connect_pads yes (clearance 0.25)) (min_thickness 0.15) (filled_areas_thickness no) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy %s 2) (xy %s 2) (xy %s 18) (xy %s 18))))\n'''%(n.GetNetCode(),net,uuid.uuid4(),x1,x2,x2,x1)
 s=s[:s.rfind(')')]+z+')\n'
file.write_text(s);b=p.LoadBoard(str(file));filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard(str(file),b)
print('Zone count',len(b.Zones()))
print('DSN exported',p.ExportSpecctraDSN(b,str(file.with_suffix('.dsn'))))
