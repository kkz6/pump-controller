#!/usr/bin/env python3
"""Build the edge-connected, four-mount Rev E main PCB from the preserved Rev C.
Build creates placed CAD and constrained routing input. Finish imports a session;
no manufacturing ZIP is issued here. Independent audits are required.
"""
from pathlib import Path
import argparse,copy,json,os,subprocess,sys,math,shutil,xml.etree.ElementTree as ET
import wx
app=wx.GetApp() or wx.App(False)
import pcbnew as p
import generate_cad as cad
import rev_e_power_distribution as supply_layout
import rev_e_stackup as stackup
import rev_e_signal_routes as signal_layout
import rev_e_latch_escape as latch_layout
from patch_main_rev_e_c1 import change as set_c1_envelope
from patch_main_rev_e_e11 import apply_source as apply_input_conditioning
from patch_main_rev_e_bias import apply_source as apply_reset_bias
from patch_main_rev_e_safe_clear import apply_source as apply_safe_clear
from prepare_main_rev_e_dsn import prepare,parse,render,child,tag,QUOTE_MARKER
from patch_main_rev_e_j10 import FID as J10_FID, VALUE as J10_VALUE, MPN as J10_MPN, DATASHEET as J10_DATASHEET, DESCRIPTION as J10_DESCRIPTION
B=Path(__file__).resolve().parents[1]; O=B/'hardware/main-rev-e'; P='pump-controller-main-rev-e'; M=p.FromMM
IO=p.PCB_IO_KICAD_SEXPR()
CLI=str(B/'.tools/kicad-cli'); LIB=Path(os.environ['KICAD10_FOOTPRINT_DIR'])
def pt(x,y):return p.VECTOR2I(M(x),M(y))
def run(args):
 r=subprocess.run([CLI]+args,text=True,capture_output=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 print(r.stdout.strip())
def loadfp(fid):
 lib,name=fid.split(':'); d={'Pump':B/'hardware/Pump.pretty','PumpRevE':O/'PumpRevE.pretty'}.get(lib,LIB/(lib+'.pretty'))
 f=p.FootprintLoad(str(d),name)
 if f is None:raise ValueError(fid)
 f.SetFPID(p.LIB_ID(lib,name));return f

def custom_cap():
 f=loadfp('Capacitor_THT:CP_Radial_D5.0mm_P2.00mm')
 for pad in f.Pads():pad.SetSize(pt(1.5,1.5))
 set_c1_envelope(f,p)
 f.SetFPID(p.LIB_ID('PumpRevE','CP_Radial_D5_P2_Pads1p5'))
 IO.FootprintSave(str((O/'PumpRevE.pretty').resolve()),f)

def apply_interface_text(data):
 """Keep current panel/OLED descriptions without altering electrical pin data."""
 texts={'local_controls_1': ('Rev E GH12 panel interface / 1', 'Rev E: main J32 connects 1:1 to panel J1. START/STOP/MODE/SET/NEXT are on the panel. STOP/HH clear ARM; mode/settings require STOP press, release and fresh START.'), 'local_controls_2': ('Rev E external PH4 OLED / 2', 'Rev E: OLED plugs into panel J7: 1 SCL, 2 SDA, 3 GND, 4 +3V3. Main J32 carries power/I2C to panel J1. Main J33/J34 and settings keys are removed.')}
 for sheet in data['sheets']:
  if sheet['id'] in texts:
   sheet['title'],sheet['notes']=texts[sheet['id']]
  for component in sheet['components']:
   if component['ref']=='OLED1':component['description']='External 36 x 12.5 mm module; isolated 3.3 V; panel J7 PH4 pins 1 SCL, 2 SDA, 3 GND, 4 VCC connect 1:1; main J32 to panel J1 GH12; 0x3C default; 100 mA reserved, not a datasheet maximum'

def build():
 O.mkdir(parents=True,exist_ok=True); custom_cap()
 old=p.LoadBoard(str(B/'hardware/pump-controller-rev-b.kicad_pcb'))
 fps={f.GetReference():f for f in old.GetFootprints()}
 data=json.loads((B/'design/circuit.json').read_text());data.update(project=P,revision='E',title='Edge-connected single-phase pump controller')
 data['board']={'width':100,'height':80,'layers':6}
 data['footprint_libraries']={'Pump':'hardware/Pump.pretty','PumpRevE':'hardware/main-rev-e/PumpRevE.pretty'}
 apply_interface_text(data)
 for s in data['sheets']:
  s['components']=[c for c in s['components'] if c['ref']not in['SW3','SW4','J33','J34']]
  for c in s['components']:
   if not c.get('on_board',True):continue
   f=fps[c['ref']];c['placement']={'x':p.ToMM(f.GetPosition().x)+5,'y':p.ToMM(f.GetPosition().y)+5,'rotation':f.GetOrientationDegrees(),'side':'B'if f.IsFlipped()else'F'}
 comps={c['ref']:c for s in data['sheets'] for c in s['components']}
 comps['F1']['description']=comps['F1']['description'].replace('600 VAC per TUV','600 VAC')
 comps['U2']['footprint']='Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm'
 comps['U2']['description']='Fixed3.3V buck; FB to AGND, VOS Kelvin to output capacitor. Solder EP to GND; two external0.65/0.30mm GND vias, no holes in SMT land.'
 comps['U31']['footprint']='PumpRevE:SN74LVC1G74_DCU_TI'
 comps['C1']['footprint']='PumpRevE:CP_Radial_D5_P2_Pads1p5'
 comps['J10'].update(footprint=J10_FID,value=J10_VALUE,mpn=J10_MPN,datasheet=J10_DATASHEET,description=J10_DESCRIPTION)
 comps['J2'].update(footprint='Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical',value='SERVICE 2x4 2.54mm',mpn='SPEC:2x4 2.54mm vertical header,0.64mm square posts')
 comps['J2']['description']=comps['J2']['description'].replace('Internal service header','Internal2.54mm service header')
 ns=['+5V','STOP_RETURN','MAN_RETURN','AUTO_RETURN','START_N','RESET_N','GND','+3V3','I2C_SDA','I2C_SCL','SPARE_B6','SPARE_B7']
 comps['J32'].update(footprint='Connector_JST:JST_GH_SM12B-GHS-TB_1x12-1MP_P1.25mm_Horizontal',value='PANEL / GH12',mpn='SM12B-GHS-TB(LF)(SN)',description='Keyed1:1 twelve-way harness to panelJ1. Isolated low voltage only. STOP opens hardware permit; no mains contacts on this harness. Not hot-pluggable.',datasheet='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf',pins=[{'num':str(i+1),'name':n,'net':n,'type':'passive'}for i,n in enumerate(ns)]+[{'num':'MP','name':'MOUNT','net':'GND','type':'passive'}])
 placement={'J1':(5.4,12,-90),'J30':(8.6,25,-90),'F1':(5,38,-90),'J10':(30,71,0),'J31':(48,71,0),'J20':(60,71,0),'J21':(84,71,0),'J32':(96.5,44,90),'J2':(89,14,0)}
 # Meter decouplers follow their associated IC pins without blocking QFN escape.
 placement.update({'R1':(13.5,35,-90),'RV1':(20,63.2,-90),'C40':(20,44,0),'C41':(20,46.5,0),'C42':(28.5,44,0),'R48':(30.5,47,90),'C43':(32,43.3,0),'C44':(23.5,41.5,0),'C45':(20,38.5,0),'C48':(20,49,0),'C49':(20,41,0),'C51':(24,39,0),'R40':(17.5,50.5,0),'R130':(63,61.5,0),'R131':(57,59,0),'R140':(56,63.5,0),'R141':(63,65,0),'D112':(70.5,64.5,0),'D116':(72,61,0),'R170':(86,63,0),'R171':(86,66,0),'R153':(93,30,90)})
 for ref,(x,y,a)in placement.items():comps[ref]['placement'].update(x=x,y=y,rotation=a)
 # Local front-side decoupling avoids obstructing the bottom-mounted meter fanout.
 for ref in ['C40','C41','C44','C45','C48']:comps[ref]['placement']['side']='F'
 for ref in ['C42','C43']:comps[ref]['placement']['side']='B'
 data['sheets'].append({'id':'mechanical','title':'Four-corner mounting','notes':'Four M3 nylon screws,18mm minimum insulating standoffs.4.2mm radius copper and component keepout.','components':[{'ref':'H'+str(i),'value':'M3 nylon mount','kind':'mechanical','description':'3.2mm NPTH; no conductive mounting hardware inside live region','footprint':'MountingHole:MountingHole_3.2mm_M3','pins':[],'placement':{'x':x,'y':y,'side':'F','rotation':0}}for i,(x,y)in enumerate([(4,4),(96,4),(96,76),(4,76)],1)]})
 supply_layout.select_capacitors(comps)
 supply_layout.set_placements(comps);signal_layout.set_placements(comps)
 apply_reset_bias(data);apply_safe_clear(data);apply_input_conditioning(data)
 (B/'design/main-rev-e.json').write_text(json.dumps(data,indent=2)+'\n');cad.write_schematics(data,O,P);cad.write_bom(data,O);subprocess.run([str(B/'.tools/kicad-python'),str(B/'tools/generate_cad.py'),'--input',str(B/'design/main-rev-e.json'),'--output',str(O)],check=True)
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')))
 # Copy deliberate slots and isolation keepout from the preserved board.
 for g in old.GetDrawings():
  if g.GetLayer()==p.Edge_Cuts:
   box=g.GetBoundingBox();
   if p.ToMM(box.GetX())>1 and p.ToMM(box.GetRight())<89 and p.ToMM(box.GetY())>1 and p.ToMM(box.GetBottom())<69:
    v=g.Duplicate();v.Move(pt(5,5));b.Add(v)
 for z in old.Zones():
  z2=p.Cast_to_ZONE(z.Duplicate(False));z2.Move(pt(5,5))
  if not z.GetIsRuleArea():z2.SetNet(b.FindNet(z.GetNetname()))
  b.Add(z2)
 for i,(x,y)in enumerate([(4,4),(96,4),(96,76),(4,76)],1):
  z=p.ZONE(b);z.SetIsRuleArea(True);ls=p.LSET()
  for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:ls.AddLayer(layer)
  z.SetLayerSet(ls);z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowPads(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowFootprints(False);z.SetZoneName('M3 nylon mount H'+str(i))
  z.Outline().NewOutline()
  for a in range(0,360,5):z.Outline().Append(M(x+4.21*math.cos(math.radians(a))),M(y+4.21*math.sin(math.radians(a))))
  z.Outline().NewHole(0)
  for a in range(355,-1,-5):z.Outline().Append(M(x+1.7*math.cos(math.radians(a))),M(y+1.7*math.sin(math.radians(a))),0,0)
  b.Add(z)
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b);b=p.LoadBoard(str(O/(P+'.kicad_pcb')))
 settings=b.GetDesignSettings();settings.m_MinClearance=M(.2);settings.m_TrackMinWidth=M(.15);settings.m_SolderMaskExpansion=M(.05);settings.m_SolderMaskMinWidth=M(.1);settings.m_SilkClearance=M(.15);settings.m_HoleClearance=M(.33);settings.m_HoleToHoleMin=M(.5);settings.SetBoardThickness(M(1.6))
 cmap={c['ref']:c for s in data['sheets']for c in s['components']}
 for f in b.GetFootprints():
  c=cmap[f.GetReference()];f.SetField('Description',c.get('description',''));f.GetField('Description').SetVisible(False)
  f.Reference().SetVisible(False);f.Value().SetVisible(False)
  if f.GetReference().startswith('H'):f.SetAttributes(f.GetAttributes()&~p.FP_EXCLUDE_FROM_BOM)
  # Dense parts retain fabrication outlines; readable edge connector markings are added separately.
  for g in list(f.GraphicalItems()):
   if isinstance(g,p.PCB_SHAPE) and g.GetLayer()in[p.F_SilkS,p.B_SilkS]:g.SetLayer(p.F_Fab if g.GetLayer()==p.F_SilkS else p.B_Fab)
 for label,x,y in [('MAINS L/N',16,9),('COIL IN/OUT',16,23),('LIVE CT',28,67),('HH NC',49,67),('TANK COM 1 2 3 4',68,67),('INLET / COM',85,68.5),('PANEL',96,32),('SERVICE',89,11),('PUMP E / 100x80',70,77.5)]:
  t=p.PCB_TEXT(b);t.SetText(label);t.SetPosition(pt(x,y));t.SetTextSize(pt(1,1));t.SetTextThickness(M(.16));t.SetLayer(p.F_SilkS);b.Add(t)
 title=p.TITLE_BLOCK();title.SetTitle('Single-phase pump controller / edge harness');title.SetRevision('E-PROTOTYPE');b.SetTitleBlock(title)
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b)
 cache(data)
 project(data)
 # Align native no-connect net names with schematic instead of weakening parity checks.
 (O/'exports').mkdir(exist_ok=True)
 run(['sch','export','netlist','--format','kicadxml','-o',str(O/'exports/netlist.xml'),str(O/(P+'.kicad_sch'))])
 tree=ET.parse(O/'exports/netlist.xml');native={}
 for net in tree.findall('.//nets/net'):
  for n in net.findall('node'):native[(n.attrib['ref'],n.attrib['pin'])]=net.attrib['name']
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')))
 for f in b.GetFootprints():
  for pad in f.Pads():
   name=native.get((f.GetReference(),pad.GetNumber()))
   if name:
    net=b.FindNet(name)
    if net is None or net.GetNetCode()<0:net=p.NETINFO_ITEM(b,name);b.Add(net)
    pad.SetNet(net)
 power_routes(b);supply_layout.attach(b);latch_layout.attach(b);stackup.apply(b);signal_layout.attach(b)
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b);export_dsn(b);project(data)
 print('Rev E placed board generated')
def cache(data):
 names=set()
 for s in data['sheets']:
  for c in s['components']:
   if not c.get('on_board',True):continue
   lib,name=c['footprint'].split(':');names.add(lib)
   path=O/'libraries'/(lib+'.pretty');path.mkdir(parents=True,exist_ok=True)
   f=loadfp(c['footprint'])
   for g in list(f.GraphicalItems()):
    if isinstance(g,p.PCB_SHAPE) and g.GetLayer()in[p.F_SilkS,p.B_SilkS]:g.SetLayer(p.F_Fab if g.GetLayer()==p.F_SilkS else p.B_Fab)
   if lib=='MountingHole':f.SetAttributes(f.GetAttributes()&~p.FP_EXCLUDE_FROM_BOM)
   IO.FootprintSave(str(path.resolve()),f)
 (O/'fp-lib-table').write_text('(fp_lib_table (version 7)\n'+'\n'.join('(lib (name "'+lib+'") (type "KiCad") (uri "${KIPRJMOD}/libraries/'+lib+'.pretty") (options "") (descr "Rev E project-local land patterns"))'for lib in sorted(names))+'\n)\n')
def project(data):
 pro=json.loads((B/'hardware/pump-controller-rev-b.kicad_pro').read_text());pro['meta']['filename']=P+'.kicad_pro'
 ns=pro['net_settings']
 for c in ns['classes']:
  c['clearance']=max(.2,c['clearance']);c['via_diameter']=.65;c['via_drill']=.3
 ns['netclass_patterns']+=[{'netclass':'SELV','pattern':'ARM_CLEAR_N'},{'netclass':'LIVE','pattern':'unconnected-(U10-*'},{'netclass':'LIVE','pattern':'unconnected-(U11-NIC-Pad16)'},{'netclass':'SELV','pattern':'unconnected-(U11-NIC-Pad13)'}]
 for net in ('STOP_SENSE_RAW','MAN_SENSE_RAW','AUTO_SENSE_RAW'):
  ns['netclass_patterns'].append({'netclass':'SELV','pattern':net})
 for c in [c for s in data['sheets']for c in s['components']if c['ref']not in['U10','U11']]:
  if any(not pin.get('net')for pin in c['pins']):ns['netclass_patterns'].append({'netclass':'SELV','pattern':'unconnected-('+c['ref']+'-*'})
 ds=pro['board']['design_settings'];ds['drc_exclusions']=[]
 ds['rules'].update(min_clearance=.2,min_track_width=.15,min_via_diameter=.65,min_via_annular_width=.15,min_through_hole_diameter=.3,min_hole_clearance=.33,min_hole_to_hole=.5,min_copper_edge_clearance=.3,min_silk_clearance=.15,min_text_height=1.0,min_text_thickness=.153)
 (O/(P+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
 old=(B/'hardware/pump-controller-rev-b.kicad_dru').read_text().replace('(version 1)','')
 generic='''(version 1)
(rule "Robu SMT to trace" (condition "(A.Type == 'Pad' && B.Type == 'Track') || (B.Type == 'Pad' && A.Type == 'Track')") (constraint clearance (min 0.2mm)))
(rule "Robu via to trace" (condition "(A.Type == 'Via' && B.Type == 'Track') || (B.Type == 'Via' && A.Type == 'Track')") (constraint clearance (min 0.254mm)))
(rule "Robu PTH to trace" (condition "(A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && B.Type == 'Track') || (B.Type == 'Pad' && B.Pad_Type == 'Through-hole' && A.Type == 'Track')") (constraint clearance (min 0.33mm)))
(rule "Robu PTH pad spacing" (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.Pad_Type == 'Through-hole' && B.Pad_Type == 'Through-hole'") (constraint clearance (min 0.5mm)))
'''
 (O/(P+'.kicad_dru')).write_text(generic+old)
def power_routes(b):
 fps={f.GetReference():f for f in b.GetFootprints()}
 def point(ref,num):
  d=next(q for q in fps[ref].Pads() if q.GetNumber()==str(num) and q.IsOnLayer(p.F_Cu))
  return p.ToMM(d.GetPosition().x),p.ToMM(d.GetPosition().y)
 def trace(net,points,width):
  for a,z in zip(points,points[1:]):
   if a==z:continue
   t=p.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*z));t.SetWidth(M(width));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet(net));b.Add(t)
 def via(x,y):
  v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(M(.65));v.SetDrill(M(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
 trace('+5V',[point('C3',1),(59.2,19.5)],.5)
 for pin in[2,3]:trace('+5V',[(59.2,19.5),point('U2',pin)],.2)
 trace('BUCK_SW',[point('U2',7),(62.8,19.25)],.2)
 trace('BUCK_SW',[(62.8,19.25),point('L1',1)],.5)
 trace('+3V3',[point('L1',2),point('C5',1)],.6)
 # Dedicated voltage-sense branch terminates at the output capacitor.
 trace('+3V3',[point('U2',6),(62.5,19.75),(62.5,21.75),(66.9,21.75),point('C5',1)],.2)
 for pin,target in[(1,(60.75,18.95)),(4,(60.75,20.05)),(5,(60.75,20.05))]:trace('GND',[point('U2',pin),target],.2)
 trace('GND',[(60.75,17.9),(60.75,21.1)],.6);via(60.75,17.9);via(60.75,21.1)
 trace('GND',[point('C4',2),(60.75,17.2),(60.75,17.9)],.4)
 trace('GND',[point('C3',2),(55.025,21.5),(60.35,21.5),(60.75,21.1)],.5)
 trace('GND',[point('C5',2),(71.475,21.45)],.5);via(71.475,21.45)

def export_dsn(b):
 settings=b.GetDesignSettings();nc=settings.m_NetSettings.GetDefaultNetclass();nc.SetClearance(M(.2));nc.SetTrackWidth(M(.2));nc.SetViaDiameter(M(.65));nc.SetViaDrill(M(.3));b.SynchronizeNetsAndNetClasses(False)
 if not p.ExportSpecctraDSN(b,str(O/(P+'-native.dsn'))):raise RuntimeError('DSN export failed')
 tree=parse((O/(P+'-native.dsn')).read_text());structure=child(tree,'structure')
 # Route around keepouts on all layers; native zones are refilled after session import.
 structure[:]=[x for x in structure if tag(x)!='plane']
 route_input=O/(P+'-routing-input.dsn');route_input.write_text(render(tree).replace(QUOTE_MARKER,'"')+'\n')
 prepare(route_input,O/(P+'.dsn'))
def finish():
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')))
 if not p.ImportSpecctraSES(b,str(O/(P+'.ses'))):raise RuntimeError('SES import failed')
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b);project(json.loads((B/'design/main-rev-e.json').read_text()))
def check():
 (O/'checks').mkdir(exist_ok=True)
 run(['sch','erc','--format','json','-o',str(O/'checks/erc.json'),str(O/(P+'.kicad_sch'))])
 run(['pcb','drc','--format','json','--all-track-errors','--schematic-parity','--refill-zones','--save-board','-o',str(O/'checks/drc.json'),str(O/(P+'.kicad_pcb'))])
 d=json.loads((O/'checks/drc.json').read_text());e=json.loads((O/'checks/erc.json').read_text())
 counts={k:len(d[k]) for k in ('violations','unconnected_items','schematic_parity')}
 counts['erc']=sum(len(sheet.get('violations',[])) for sheet in e['sheets'])
 print(counts)
 if any(counts.values()):raise SystemExit('Board has unresolved electrical or layout findings')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--finish',action='store_true');ap.add_argument('--check',action='store_true');a=ap.parse_args()
 if a.build:build()
 if a.finish:finish()
 if a.check:check()
