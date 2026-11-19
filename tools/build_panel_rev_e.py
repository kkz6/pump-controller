#!/usr/bin/env python3
"""Build the low-voltage OLED/button panels E and F, including their native fabrication checks.
Run with KiCad's Python. --build creates the placed PCB/DSN. --finish imports the
adjacent .ses and runs native checks/exports. Manual review still required.
"""
from pathlib import Path
import argparse,sys,os,json,shutil,subprocess,hashlib,csv,zipfile,collections
import wx
app=wx.GetApp() or wx.App(False)
import pcbnew as p
sys.path.insert(0,str(Path(__file__).resolve().parent))
import generate_cad as cad
KEYED_PANEL = '--rev-f' in sys.argv
REV = 'F' if KEYED_PANEL else 'E'
B=Path(__file__).resolve().parents[1]; O=B/'hardware'/f'panel-rev-{REV.lower()}'; P=f'pump-panel-rev-{REV.lower()}'; CLI=str(B/'.tools/kicad-cli'); MM=p.FromMM
O.mkdir(parents=True,exist_ok=True)
def pt(x,y):return p.VECTOR2I(MM(x),MM(y))
def component(ref,value,fp,pins,x,y,side='B',rotation=0,mpn='',kind='ic',description='',datasheet=''):
 ref={'JMAIN':'J1','JSTART':'J2','JSTOP':'J3','JMODE':'J4','JSET':'J5','JNEXT':'J6','JOLED':'J7','JKEY':'J8','SWSTOP':'SW1','SWSTART':'SW2','SWMODE':'SW3','SWSET':'SW4','SWNEXT':'SW5','JPSTOP':'JP1','RWET':'R1','RK1W':'R2','RK1B':'R3','RK1E':'R4','RK1C':'R5','RK2W':'R6','RK2B':'R7','RK2E':'R8','RK2C':'R9','QK1':'Q1','QK2':'Q2','CK1':'C3','CK2':'C4'}.get(ref,ref)
 return dict(ref=ref,value=value,footprint=fp,pins=[dict(num=str(n),name=name,net=net,type='passive')for n,name,net in pins],placement=dict(x=x,y=y,side=side,rotation=rotation),mpn=mpn,kind=kind,description=description,datasheet=datasheet)
def conn(ref,count,nets,x,y,rotation=0):
 fp=f'Connector_JST:JST_GH_SM{count:02}B-GHS-TB_1x{count:02}-1MP_P1.25mm_Horizontal'
 return component(ref,ref.replace('J','')+' / JST GH '+str(count),fp,[(i+1,n,n)for i,n in enumerate(nets)]+[('MP','MOUNT','GND')],x,y,rotation=rotation,mpn=f'SM{count:02}B-GHS-TB(LF)(SN)',description='Rear horizontal cable connector; mating GHR-'+str(count).zfill(2)+'V-S housing, SSHL-002T-P0.2 contacts; verify purchased keying.',datasheet='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf')
def resistor(ref,value,a,z,x,y,rotation=0):return component(ref,value,'Resistor_SMD:R_0603_1608Metric',[(1,'1',a),(2,'2',z)],x,y,rotation=rotation,kind='resistor',mpn={'2.2k':'RC0603FR-072K2L','10k':'RC0603FR-0710KL','100k':'RC0603FR-07100KL'}[value],description='1%, 0.1W, 0603')
def capacitor(ref,value,a,z,x,y,rotation=0):return component(ref,value,'Capacitor_SMD:C_0603_1608Metric',[(1,'1',a),(2,'2',z)],x,y,rotation=rotation,kind='capacitor',mpn={'100nF':'GRM188R71C104KA01D','4.7uF':'GRM188R60J475KE19D','10nF':'GRM188R71H103KA01D'}[value],description='X7R/X5R ceramic, voltage rating per selected MPN')
mainnets=['+5V','STOP_RETURN','MAN_RETURN','AUTO_RETURN','START_N','RESET_N','GND','+3V3','I2C_SDA','I2C_SCL','KEY_MAN_N','KEY_AUTO_N']
control=[conn('JMAIN',12,mainnets,30,3.3,rotation=0),
 conn('JSTART',2,['START_N','GND'],10,41.7,rotation=180),conn('JSTOP',2,['STOP_LOCAL_NC','STOP_RETURN'],20,41.7,rotation=180),conn('JMODE',2,['MAN_RETURN','STOP_RETURN'],30,41.7,rotation=180),conn('JSET',2,['RESET_N','GND'],40,41.7,rotation=180),conn('JNEXT',2,['AUTO_RETURN','STOP_RETURN'],50,41.7,rotation=180),
 component('SWSTOP','STOP / NC','Panel:Omron_D2F-01F',[(1,'COM','+5V'),(2,'NO',None),(3,'NC','STOP_LOCAL_NC')],18.17,30,'F',mpn='D2F-01F',description='Normally closed STOP. COM to NC opens while pressed. Pin numbering1=COM2=NO3=NC is this project convention; manufacturer uses names.',datasheet='https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf'),
 component('JPSTOP','EXT STOP BYPASS','Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',[(1,'1','STOP_LOCAL_NC'),(2,'2','STOP_RETURN')],10,23,mpn='Samtec TSW-102-07-G-S',description='Removable 2.54mm shunt. Fit only when no external NC STOP contact is installed. Never bypasses onboard STOP.'),
 resistor('RWET','2.2k','STOP_RETURN','GND',14,25.5)]
if KEYED_PANEL:
 # Each remote contact has its own pair and each contact is permanently terminated
 # at the switch end. The optional station always uses the same one-piece keyed plug.
 remote=conn('J2',10,['START_N','GND','STOP_LOCAL_NC','STOP_RETURN','MAN_RETURN',
                      'STOP_RETURN','RESET_N','GND','AUTO_RETURN','STOP_RETURN'],
             30,41.7,rotation=180)
 remote['value']='REMOTE BUTTON STATION / GH10'
 remote['description']='One GHR-10V-S station plug. Fixed remote-button pairs 1/2 START, 3/4 NC STOP, 5/6 MODE, 7/8 SET, 9/10 NEXT. An unplugged station opens STOP.'
 control=[control[0],remote]+[c for c in control if c['ref'] in ('SW1','R1')]
 # Omron D2F p. 3-4. The plunger is 5.2 mm left of the right mounting hole.
 # Maintain the intended actuator position (20,30) with its COM pad at x=16.87 mm.
 next(c for c in control if c['ref']=='SW1')['placement']['x']=16.87
for ref,label,a,z,x in [('SWSTART','START','START_N','GND',7.5),('SWMODE','AUTO / MANUAL','MAN_RETURN','STOP_RETURN',34.5),('SWSET','SET / RESET','RESET_N','GND',45),('SWNEXT','NEXT / +','AUTO_RETURN','STOP_RETURN',54)]:
 control.append(component(ref,label,'Button_Switch_SMD:SW_SPST_B3U-1000P',[(1,'1',a),(2,'2',z)],x,30,'F',mpn='B3U-1000P',kind='switch',description='Momentary normally open tactile switch; external contact wired in parallel.',datasheet='https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf'))
display=[component('JOLED','OLED / PH4','Connector_JST:JST_PH_S4B-PH-SM4-TB_1x04-1MP_P2.00mm_Horizontal',[(1,'SCL','I2C_SCL'),(2,'SDA','I2C_SDA'),(3,'GND','GND'),(4,'VCC','+3V3'),('MP','MOUNT','GND')],54.8,21,rotation=270,mpn='S4B-PH-SM4-TB(LF)(SN)',description='Waveshare14657 numeric order1SCL2SDA3GND4VCC; match pin numbers at both harness ends, not wire colors.',datasheet='https://www.jst-mfg.com/product/pdf/eng/ePH.pdf'),capacitor('C1','100nF','+3V3','GND',44,16),capacitor('C2','4.7uF','+3V3','GND',48,16)]
key=[conn('JKEY',3,['+5V','KEY_MAN_RAW','KEY_AUTO_RAW'],3.3,20,rotation=90)]
for suffix,base,x in [('MAN',1,22),('AUTO',2,33)]:
 raw='KEY_'+suffix+'_RAW';be='KEY_'+suffix+'_B';sense='KEY_'+suffix+'_N'
 key+=[resistor('RK'+str(base)+'W','2.2k',raw,'GND',x,13),resistor('RK'+str(base)+'B','10k',raw,be,x,16.5),resistor('RK'+str(base)+'E','100k',be,'GND',x,20.5),resistor('RK'+str(base)+'C','10k','+3V3',sense,x+5,16.5),capacitor('CK'+str(base),'10nF',sense,'GND',x+3.5,20.5),component('QK'+str(base),'MMBT3904','Package_TO_SOT_SMD:SOT-23',[(1,'B',be),(2,'E','GND'),(3,'C',sense)],x+5,13,mpn='MMBT3904LT1G',description='NPN active-low5V-to3.3V key input; pin1B2E3C. Existing main100k sense pulldown retained.',datasheet='https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf')]
mechanical=[component('H'+str(i),'M2.5 mount','MountingHole:MountingHole_2.7mm_M2.5',[],x,y,'F',description='Non-plated mounting hole; insulating standoffs and metal-panel clearance required.')for i,(x,y)in enumerate([(3,3),(57,3),(3,42),(57,42)],1)]
data={'project':P,'revision':REV,'title':'Low-voltage OLED and five-button panel','board':{'width':60,'height':45,'layers':2},'footprint_libraries':{'Panel':f'hardware/panel-rev-{REV.lower()}/Panel.pretty'},'sheets':[{'id':'panel-controls','title':'Five local buttons and optional external contacts','notes':'STOP is NC and hardwired in series. Other contacts are NO. This panel accepts isolated low voltage only.','components':control},{'id':'panel-display','title':'OLED power and I2C','notes':'Waveshare14657 external display module36x12.5mm. Host provides I2C pullups.','components':display},{'id':'panel-key','title':'Optional maintained AUTO/MANUAL key input','notes':'SPDT break-before-make dry key: common+5V. MAN/AUTO sense activeLOW. Open/open and closed/closed invalid.','components':key},{'id':'panel-mechanical','title':'Mechanical mounting','notes':'Front: five buttons and OLED envelope. Rear: connectors and conditioning. Enclosure plungers and fit need verification.','components':mechanical}]}

def custom_stop():
 d=O/'Panel.pretty';d.mkdir(exist_ok=True)
 s='''(footprint "Omron_D2F-01F" (version 20241229) (generator "pcbnew") (layer "F.Cu")
 (descr "Omron D2F-01F straight PCB terminals. COM1 NO2 NC3 project numbering. Datasheet eD2F pages3-4; derived footprint needs firstarticle check.")
 (attr through_hole)
 (property "Reference" "REF**" (at 5.08 -4 0) (layer "F.SilkS") (effects(font(size 1 1)(thickness 0.16))))
 (property "Value" "D2F-01F" (at 5.08 4 0) (layer "F.Fab") (effects(font(size 1 1)(thickness 0.15))))
 (fp_rect(start -1.32 -2.9)(end 11.48 2.9)(stroke(width 0.15)(type default))(fill none)(layer "F.Fab"))
 (fp_rect(start -1.5 -3.1)(end 11.65 3.1)(stroke(width 0.16)(type default))(fill none)(layer "F.SilkS"))
 (fp_rect(start -1.9 -3.5)(end 12.05 3.5)(stroke(width 0.05)(type default))(fill none)(layer "F.CrtYd"))
 (fp_circle(center 1.83 0)(end 2.93 0)(stroke(width 0.15)(type default))(fill none)(layer "F.Fab"))
 (pad "1" thru_hole rect(at 0 0)(size 2 2)(drill 1.2)(layers "*.Cu" "*.Mask"))
 (pad "2" thru_hole circle(at 5.08 0)(size 2 2)(drill 1.2)(layers "*.Cu" "*.Mask"))
 (pad "3" thru_hole circle(at 10.16 0)(size 2 2)(drill 1.2)(layers "*.Cu" "*.Mask"))
)'''
 if KEYED_PANEL:
  s=s.replace('center 1.83 0)(end 2.93 0','center 3.13 0)(end 4.23 0')
  s=s[:-1]+' (model "${KIPRJMOD}/models/D2F-01F-nominal.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))\n)'
 (d/'Omron_D2F-01F.kicad_mod').write_text(s+'\n')
def apply_panel_model(fp):
 if KEYED_PANEL and 'S4B-PH-SM4-TB' in str(fp.GetFPID().GetLibItemName()):
  fp.Models().clear();model=p.FP_3DMODEL();model.m_Filename='${KIPRJMOD}/models/S4B-PH-SM4-TB-envelope.step';fp.Add3DModel(model)
def boardtext(b,t,x,y,layer=p.F_SilkS):
 a=p.PCB_TEXT(b);a.SetText(t);a.SetPosition(pt(x,y));a.SetTextSize(pt(1,1));a.SetTextThickness(MM(.16));a.SetLayer(layer)
 if layer==p.B_SilkS:a.SetMirrored(True)
 b.Add(a)
def archive_suffixes():
 tag='prototype' if KEYED_PANEL else 'review'
 return [f'-gerber-{tag}.zip',f'-stencil-{tag}.zip']
def build():
 for suffix in archive_suffixes():(O/(P+suffix)).unlink(missing_ok=True)
 custom_stop();(B/'design'/f'panel-rev-{REV.lower()}.json').write_text(json.dumps(data,indent=2)+'\n');cad.write_schematics(data,O,P);cad.write_bom(data,O);cad.make_board(data,O,P)
 for f in O.glob('*.kicad_sch'):
  s=f.read_text().replace('Engineering prototype; mains review and bench tests pending','Isolated low voltage only; prototype bench and mechanical validation pending').replace('1 HP single-phase pump controller','Pump controller low-voltage panel')
  f.write_text(s)
 pro={'meta':{'filename':P+'.kicad_pro','version':1},'net_settings':{'meta':{'version':3},'classes':[{'name':'Default','clearance':.30,'track_width':.3,'via_diameter':1.0,'via_drill':.4,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.3,'diff_pair_gap':.3}]},'board':{'design_settings':{'rules':{'min_clearance':.25,'min_track_width':.25,'min_via_diameter':1.0,'min_via_annular_width':.3,'min_through_hole_diameter':.4,'min_hole_clearance':.33,'min_hole_to_hole':.5,'min_copper_edge_clearance':.3,'min_silk_clearance':.15,'min_text_height':1.0,'min_text_thickness':.153},'rule_severities':{},'drc_exclusions':[]}},'erc':{'rule_severities':{'global_label_dangling':'ignore'}}}
 (O/(P+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
 (O/(P+'.kicad_dru')).write_text('''(version 1)
(rule "Panel drilled-pad clearance" (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.Pad_Type == 'Through-hole' && B.Pad_Type == 'Through-hole'") (constraint clearance (min 0.5mm)))
(rule "Panel via to track copper clearance" (condition "(A.Type == 'Via' && B.Type == 'Track') || (B.Type == 'Via' && A.Type == 'Track')") (constraint clearance (min 0.254mm)))
(rule "Panel PTH to track copper clearance" (condition "(A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && B.Type == 'Track') || (B.Type == 'Pad' && B.Pad_Type == 'Through-hole' && A.Type == 'Track')") (constraint clearance (min 0.33mm)))
''')
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')));settings=b.GetDesignSettings();settings.m_MinClearance=MM(.25);settings.m_TrackMinWidth=MM(.25);settings.m_SolderMaskExpansion=MM(.05);settings.m_SolderMaskMinWidth=MM(.1);settings.m_SilkClearance=MM(.15);settings.m_HoleClearance=MM(.33);settings.m_HoleToHoleMin=MM(.5);settings.SetBoardThickness(MM(1.6))
 cmap={c['ref']:c for sh in data['sheets']for c in sh['components']}
 for f in b.GetFootprints():
  apply_panel_model(f)
  f.SetField('Description',cmap[f.GetReference()].get('description',''));f.GetField('Description').SetVisible(False)
  f.Reference().SetVisible(False);f.Value().SetVisible(False)
  for g in f.GraphicalItems():
   if g.GetLayer()in[p.F_SilkS,p.B_SilkS]and isinstance(g,p.PCB_SHAPE):g.SetWidth(MM(.16))
 for label,x in [('START',7.5),('STOP',20),('MODE',34.5),('SET',45),('NEXT',54)]:boardtext(b,label,x,35)
 boardtext(b,'OLED / 5-BUTTON PANEL '+REV,30,43)
 if KEYED_PANEL:
  boardtext(b,'J2 BUTTONS / GH10',30,36,p.B_SilkS)
  boardtext(b,'3-4 NC STOP',11,40,p.B_SilkS)
 else:
  for label,x in [('START',10),('NC STOP',20),('MODE',30),('SET',40),('NEXT',50)]:boardtext(b,label,x,37.4,p.B_SilkS)
 boardtext(b,'KEY',8,15,p.B_SilkS);boardtext(b,'OLED',48,21,p.B_SilkS);boardtext(b,'HOST / GH12',30,9,p.B_SilkS)
 if not KEYED_PANEL:boardtext(b,'STOP BYPASS',11,18,p.B_SilkS)
 rect=p.PCB_SHAPE();rect.SetShape(p.SHAPE_T_RECT);rect.SetStart(pt(12,4));rect.SetEnd(pt(48,16.5));rect.SetLayer(p.F_Fab);rect.SetWidth(MM(.15));b.Add(rect)
 boardtext(b,'Waveshare14657 / 36x12.5',30,10,p.F_Fab)
 title=p.TITLE_BLOCK();title.SetTitle('Low-voltage five-button and OLED panel');title.SetRevision(REV+'-PROTOTYPE');title.SetCompany('Pump controller');b.SetTitleBlock(title)
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b)
 nc=settings.m_NetSettings.GetDefaultNetclass();nc.SetClearance(MM(.30));nc.SetTrackWidth(MM(.30));nc.SetViaDiameter(MM(1.0));nc.SetViaDrill(MM(.4));b.SynchronizeNetsAndNetClasses(False)
 if not p.ExportSpecctraDSN(b,str(O/(P+'.dsn'))):raise RuntimeError('DSN export failed')
 dsn=O/(P+'.dsn');dsn.write_text(dsn.read_text().replace('(clearance 75 (type smd_smd))','(clearance 300 (type smd_smd))').replace('(structure','(structure\n    (control (via_at_smd off))',1))
 if KEYED_PANEL:
  # Allow routing margin around the large rear annuli of the physical NC STOP.
  dsn.write_text(dsn.read_text().replace('(clearance 300)', '(clearance 385)').replace(str(O/(P+'.dsn')),P+'.dsn'))
 cache_libraries()
 print('Built panel and routing input')
def cache_libraries():
 libs=Path(os.environ['KICAD10_FOOTPRINT_DIR']);seen=set();names=set()
 for sh in data['sheets']:
  for c in sh['components']:
   lib,name=c['footprint'].split(':');names.add(lib)
   if (lib,name)in seen or lib=='Panel':continue
   seen.add((lib,name));path=O/'libraries'/(lib+'.pretty');path.mkdir(parents=True,exist_ok=True)
   fp=p.FootprintLoad(str(libs/(lib+'.pretty')),name)
   apply_panel_model(fp)
   for g in fp.GraphicalItems():
    if g.GetLayer()in[p.F_SilkS,p.B_SilkS]and isinstance(g,p.PCB_SHAPE):g.SetWidth(MM(.16))
   if lib=='MountingHole':fp.SetAttributes(fp.GetAttributes()&~p.FP_EXCLUDE_FROM_BOM)
   p.PCB_IO_KICAD_SEXPR().FootprintSave(str(path.resolve()),fp)
 lines=['(fp_lib_table (version 7)']
 for lib in sorted(names):
  path='${KIPRJMOD}/Panel.pretty'if lib=='Panel'else'${KIPRJMOD}/libraries/'+lib+'.pretty'
  lines.append(f'(lib (name "{lib}")(type "KiCad")(uri "{path}")(options "")(descr "Project-local footprints; silk strokes0.16mm"))')
 lines.append(')');(O/'fp-lib-table').write_text('\n'.join(lines)+'\n')
def normalize_board(b):
 # Preserve a genuinely unused SPDT terminal while matching native no-connect net naming.
 n=b.FindNet('unconnected-(SW1-NO-Pad2)')
 if n is None or n.GetNetCode()<0:n=p.NETINFO_ITEM(b,'unconnected-(SW1-NO-Pad2)');b.Add(n)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):continue
  if t.GetWidth()<MM(.25):t.SetWidth(MM(.25))

 # Preserve the reviewed MAN_RETURN escape around SW1.3 after importing the
 # original routing session. Move this diagonal and its two shared junctions
 # 0.10 mm upward; no component, drill or connector position changes.
 moves={tuple(pt(30.625,30.2334)):pt(30.625,30.1334),
        tuple(pt(28.6549,28.2633)):pt(28.6549,28.1633)}
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA) or t.GetNetname()!='MAN_RETURN' or t.GetLayer()!=p.B_Cu:continue
  if tuple(t.GetStart())in moves:t.SetStart(moves[tuple(t.GetStart())])
  if tuple(t.GetEnd())in moves:t.SetEnd(moves[tuple(t.GetEnd())])

 for fp in b.GetFootprints():
  if fp.GetReference().startswith('H'):fp.SetAttributes(fp.GetAttributes()&~p.FP_EXCLUDE_FROM_BOM)
  if fp.GetReference()=='SW1':
   for pad in fp.Pads():
    if pad.GetNumber()=='2':pad.SetNet(n)
def run(args):
 a=subprocess.run([CLI]+args,capture_output=True,text=True);print(a.stdout.strip());
 if a.returncode:raise RuntimeError(a.stderr or str(args))
def finish():
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')))
 if not p.ImportSpecctraSES(b,str(O/(P+'.ses'))):raise RuntimeError('Session import failed')
 normalize_board(b)
 p.SaveBoard(str(O/(P+'.kicad_pcb')),b)
 validate_export()
def validate_export():
 for suffix in archive_suffixes():(O/(P+suffix)).unlink(missing_ok=True)
 checks=O/'checks';checks.mkdir(exist_ok=True);exports=O/'exports';exports.mkdir(exist_ok=True)
 run(['sch','erc','--format','json','--severity-all','-o',str(checks/'erc.json'),str(O/(P+'.kicad_sch'))])
 run(['sch','export','netlist','--format','kicadxml','-o',str(exports/'netlist.xml'),str(O/(P+'.kicad_sch'))]);cad.validate_netlist(data,exports/'netlist.xml')
 if KEYED_PANEL:
  netlist=exports/'netlist.xml'
  netlist.write_text(netlist.read_text().replace(str(B)+'/', ''))
 run(['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','-o',str(checks/'drc.json'),str(O/(P+'.kicad_pcb'))])
 run(['sch','export','svg','-o',str(exports/'schematic-svg')+'/',str(O/(P+'.kicad_sch'))])
 for side in ['F','B']:
  (exports/('pcb-'+side)).mkdir(exist_ok=True)
  run(['pcb','export','svg','--mode-multi','--layers',side+'.Cu,'+side+'.Silkscreen,Edge.Cuts','-o',str(exports/('pcb-'+side))+'/',str(O/(P+'.kicad_pcb'))])
 b=p.LoadBoard(str(O/(P+'.kicad_pcb')));expected={c['ref']:c for s in data['sheets']for c in s['components']};errors=[]
 for f in b.GetFootprints():
  c=expected[f.GetReference()];pm={pin['num']:pin.get('net')or''for pin in c['pins']}
  for pad in f.Pads():
   if pad.GetNumber()in pm and pad.GetNetname()!=pm[pad.GetNumber()]and not(pm[pad.GetNumber()]==''and pad.GetNetname().startswith('unconnected-')):errors.append([f.GetReference(),pad.GetNumber(),pad.GetNetname(),pm[pad.GetNumber()]])
 overlaps=[]
 for t in b.GetTracks():
  if not isinstance(t,p.PCB_VIA):continue
  for fp in b.GetFootprints():
   for pad in fp.Pads():
    if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
    for layer in [p.F_Cu,p.B_Cu]:
     if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(t.GetPosition(),int(t.GetDrillValue()/2)):
      overlaps.append({'ref':fp.GetReference(),'pad':pad.GetNumber(),'via_uuid':str(t.m_Uuid)});break
 (checks/'via-in-pad-audit.json').write_text(json.dumps({'pcb_sha256':hashlib.sha256((O/(P+'.kicad_pcb')).read_bytes()).hexdigest(),'method':'Native SMT copper shape intersection with nominal drill disk','overlap_count':len(overlaps),'overlaps':overlaps},indent=2)+'\n')
 # Compare all actual drill shapes (round and slotted) with solder-mask openings,
 # including opposite-side pads. This includes NPTH mounts and connector PTHs.
 holes=[]
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):holes.append(('via:'+str(t.m_Uuid),t.GetEffectiveHoleShape()))
 for fp in b.GetFootprints():
  for pad in fp.Pads():
   if max(pad.GetDrillSize().x,pad.GetDrillSize().y)>0:
    holes.append((fp.GetReference()+'.'+pad.GetNumber(),pad.GetEffectiveHoleShape()))
 mask_overlaps=[]
 for hole_name,hole_shape in holes:
  for fp in b.GetFootprints():
   for pad in fp.Pads():
    if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
    for copper,mask in [(p.F_Cu,p.F_Mask),(p.B_Cu,p.B_Mask)]:
     if pad.IsOnLayer(copper) and pad.IsOnLayer(mask):
      expansion=pad.GetSolderMaskExpansion(mask)
      if expansion<0:raise RuntimeError('Negative mask expansion requires polygon erosion audit')
      if pad.GetEffectiveShape(copper).Collide(hole_shape,expansion):
       mask_overlaps.append({'hole':hole_name,'ref':fp.GetReference(),'pad':pad.GetNumber(),'side':p.LayerName(copper),'mask_expansion_mm':p.ToMM(expansion)})
 (checks/'drill-to-smt-mask-audit.json').write_text(json.dumps({'pcb_sha256':hashlib.sha256((O/(P+'.kicad_pcb')).read_bytes()).hexdigest(),'method':'Every native effective drill shape against each SMT copper shape inflated by its effective solder-mask expansion, on both board faces; includes vias, PTH and NPTH; nominal geometry without fabrication registration tolerance','drilled_feature_count':len(holes),'overlap_count':len(mask_overlaps),'overlaps':mask_overlaps},indent=2)+'\n')
 drc=json.load(open(checks/'drc.json'));erc=json.load(open(checks/'erc.json'))
 summary={'pcb_sha256':hashlib.sha256((O/(P+'.kicad_pcb')).read_bytes()).hexdigest(),'dimensions_mm':[60,45],'layers':2,'source_pad_mismatches':errors,'drc_violations':len(drc['violations']),'schematic_parity_issues':len(drc.get('schematic_parity',[])),'electrical_components':sum(1 for f in b.GetFootprints() if not f.GetReference().startswith('H')),'mounting_holes':4,'unconnected':len(drc['unconnected_items']),'erc_violations':sum(len(s.get('violations',[]))for s in erc.get('sheets',[])),'via_in_smt_pad_drill_overlaps':len(overlaps),'drill_to_smt_mask_overlaps':len(mask_overlaps),'hardware_tested':False,'release_ready':False}
 (checks/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
 if errors or overlaps or mask_overlaps or summary['schematic_parity_issues']or summary['drc_violations']or summary['unconnected']or summary['erc_violations']:
  (O/(P+archive_suffixes()[0])).unlink(missing_ok=True)
  (O/(P+archive_suffixes()[1])).unlink(missing_ok=True)
  raise SystemExit('Panel validation failed; no fabrication export generated and previous upload ZIPs removed.')
 fab=O/'gerber-review';fab.mkdir(exist_ok=True)
 run(['pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','-o',str(fab)+'/',str(O/(P+'.kicad_pcb'))])
 run(['pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path',str(fab/'drill-report.txt'),'-o',str(fab)+'/',str(O/(P+'.kicad_pcb'))])
 run(['pcb','export','ipcd356','-o',str(fab/(P+'.d356')),str(O/(P+'.kicad_pcb'))])
 (fab/'REVIEW-ONLY.txt').write_text('Engineering prototype for manufacturer review. Not a fabrication release. 60x45mm,2layers,1.6mm. Isolated low voltage only. Source SHA256 '+summary['pcb_sha256']+'\n')
 if KEYED_PANEL:
  (fab/'REVIEW-ONLY.txt').unlink(missing_ok=True)
  (fab/'MANUFACTURING-NOTES.txt').write_text('Bare PCB engineering prototype. 60 x 45 mm, 2 copper layers, 1.6 mm FR-4, 1 oz copper, separate plated and non-plated drills. Electrical test against the included IPC-D-356 netlist. Supplier DFM pending. Board SHA256 '+summary['pcb_sha256']+'\n')
 with zipfile.ZipFile(O/(P+archive_suffixes()[0]),'w',zipfile.ZIP_DEFLATED)as z:
  for f in sorted(fab.iterdir()):z.write(f,f.name)
 stencil=O/'stencil-review';stencil.mkdir(exist_ok=True)
 run(['pcb','export','gerbers','--layers','F.Paste,B.Paste','-o',str(stencil)+'/',str(O/(P+'.kicad_pcb'))])
 (stencil/'REVIEW-ONLY.txt').write_text('Separate stencil review files for both faces. Apertures, stencil thickness and assembly process need assembler review. Not included in the bare-board ZIP. Source SHA256 '+summary['pcb_sha256']+'\n')
 if KEYED_PANEL:
  (stencil/'REVIEW-ONLY.txt').unlink(missing_ok=True)
  (stencil/'MANUFACTURING-NOTES.txt').write_text('Engineering prototype stencil set. Both paste faces are populated. Confirm frame, foil thickness, paste and aperture treatment with the assembler. Board SHA256 '+summary['pcb_sha256']+'\n')
 with zipfile.ZipFile(O/(P+archive_suffixes()[1]),'w',zipfile.ZIP_DEFLATED)as z:
  for f in sorted(stencil.iterdir()):z.write(f,f.name)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--rev-f',action='store_true',help='Select the single-plug panel revision');ap.add_argument('--build',action='store_true');ap.add_argument('--finish',action='store_true');ap.add_argument('--check',action='store_true');a=ap.parse_args()
 if a.build:build()
 if a.finish:finish()
 if a.check:validate_export()
