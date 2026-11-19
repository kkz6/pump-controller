from pathlib import Path
import argparse,hashlib,json,itertools,subprocess,xml.etree.ElementTree as ET
import pcbnew as p
B=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description='Read-only native main/panel interface topology and fresh panel CAD checks.')
ap.add_argument('--panel-board',type=Path,default=B/'hardware/panel-rev-e/pump-panel-rev-e.kicad_pcb')
ap.add_argument('--main-board',type=Path,default=B/'hardware/main-rev-e/pump-controller-main-rev-e.kicad_pcb')
ap.add_argument('--panel-source',type=Path,default=B/'design/panel-rev-e.json')
ap.add_argument('--main-source',type=Path,default=B/'design/main-rev-e.json')
ap.add_argument('--output',type=Path,default=B/'hardware/panel-rev-e/checks')
ap.add_argument('--main-summary',type=Path,default=B/'hardware/main-rev-e/checks/independent-summary.json')
ap.add_argument('--require-frozen-main',action='store_true')
ap.add_argument('--control-variant',choices=['rev-e','compact','compact-dual'],default='rev-e')
args=ap.parse_args()
boardpath=args.panel_board.resolve();mainpath=args.main_board.resolve();O=boardpath.parent
CHECKS=args.output.resolve();CHECKS.mkdir(parents=True,exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
inputs=[boardpath,mainpath,args.panel_source.resolve(),args.main_source.resolve()]
for native in (boardpath,mainpath):
 inputs += [native.with_suffix('.kicad_pro'),native.with_suffix('.kicad_dru')]
 inputs += sorted(native.parent.glob('*.kicad_sch'))
frozen={str(path):sha(path) for path in inputs}
def run_cli(*items):
 result=subprocess.run([str(B/'.tools/kicad-cli'),*map(str,items)],cwd=B,capture_output=True,text=True)
 if result.returncode not in (0,5):raise RuntimeError(result.stdout+result.stderr)
run_cli('sch','erc','--format','json','--severity-all','--exit-code-violations','-o',CHECKS/'integration-erc.json',boardpath.with_suffix('.kicad_sch'))
run_cli('pcb','drc','--format','json','--severity-all','--schematic-parity','--all-track-errors','--exit-code-violations','-o',CHECKS/'integration-drc.json',boardpath)
run_cli('sch','export','netlist','--format','kicadxml','-o',CHECKS/'integration-netlist.xml',boardpath.with_suffix('.kicad_sch'))
run_cli('sch','export','netlist','--format','kicadxml','-o',CHECKS/'integration-main-netlist.xml',mainpath.with_suffix('.kicad_sch'))
b=p.LoadBoard(str(boardpath));m=p.LoadBoard(str(mainpath));before=sha(boardpath)
src=json.loads(args.panel_source.read_text());cs={c['ref']:c for s in src['sheets']for c in s['components']};fps={f.GetReference():f for f in b.GetFootprints()};mainfps={f.GetReference():f for f in m.GetFootprints()}
net=lambda ref,num: next(x.GetNetname() for x in fps[ref].Pads()if x.GetNumber()==str(num))
mainnet=lambda ref,num:next(x.GetNetname() for x in mainfps[ref].Pads()if x.GetNumber()==str(num))
x=ET.parse(CHECKS/'integration-netlist.xml').getroot();sch={(n.attrib['ref'],n.attrib['pin']):a.attrib['name'] for a in x.findall('./nets/net')for n in a.findall('node')}
issues=[];checked=0
for ref,c in cs.items():
 if ref not in fps:issues.append('missing footprint '+ref);continue
 f=fps[ref];fid=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
 if fid!=c['footprint']:issues.append('footprint mismatch '+ref)
 if f.GetValue()!=c['value']:issues.append('value mismatch '+ref)
 for pin in c['pins']:
  n=pin.get('net')or'';ps=[a for a in f.Pads()if a.GetNumber()==str(pin['num'])]
  if not ps or any(a.GetNetname()!=n and not (not n and a.GetNetname().startswith('unconnected-(')) for a in ps):issues.append(f'pad mismatch {ref}.{pin["num"]}')
  sn=sch.get((ref,str(pin['num'])))
  if n:
   checked+=1
   if sn!=n:issues.append(f'schematic mismatch {ref}.{pin["num"]}')
  elif sn and not sn.startswith('unconnected-('):issues.append(f'unexpected schematic connection {ref}.{pin["num"]}')
if set(fps)!=set(cs):issues.append('footprint inventory mismatch')
main_source=json.loads(args.main_source.read_text())
main_components={c['ref']:c for sheet in main_source['sheets'] for c in sheet['components'] if c.get('on_board',True)}
main_xml=ET.parse(CHECKS/'integration-main-netlist.xml').getroot()
main_sch={(node.attrib['ref'],node.attrib['pin']):n.attrib['name'] for n in main_xml.findall('./nets/net') for node in n.findall('node')}
main_checked=0
for ref,c in main_components.items():
 if ref not in mainfps:issues.append('main missing footprint '+ref);continue
 for pin in c['pins']:
  num=str(pin['num']);expected=pin.get('net')or''
  pads=[pad for pad in mainfps[ref].Pads() if pad.GetNumber()==num]
  actual={pad.GetNetname() for pad in pads}
  if not pads or (expected and actual!={expected}) or (not expected and any(n and not n.startswith('unconnected-(') for n in actual)):issues.append(f'main source/pad mismatch {ref}.{num}')
  sn=main_sch.get((ref,num),'')
  if (expected and sn!=expected) or (not expected and sn and not sn.startswith('unconnected-(')):issues.append(f'main source/schematic mismatch {ref}.{num}')
  main_checked+=bool(expected)
expected_host=['+5V','STOP_RETURN','MAN_RETURN','AUTO_RETURN','START_N','RESET_N','GND','+3V3','I2C_SDA','I2C_SCL','KEY_MAN_N','KEY_AUTO_N']
for i,n in enumerate(expected_host,1):
 if net('J1',i)!=n:issues.append('host pin mismatch '+str(i))
host_map=[]
for pin,(ref,num)in enumerate([('J32',i)for i in range(1,13)],1):
 mn=mainnet(ref,num);pn=net('J1',pin);expect= {'KEY_MAN_N':'SPARE_B6','KEY_AUTO_N':'SPARE_B7'}.get(pn,pn)
 if mn!=expect:issues.append('host harness mismatch pin '+str(pin))
 host_map.append({'panel_pin':pin,'panel_net':pn,'main_connector':ref,'main_pin':num,'main_net':mn})
if mainnet('J32',7)!='GND':issues.append('main common-ground mismatch')
if net('SW1',1)!='+5V' or net('SW1',3)!='STOP_LOCAL_NC' or not (net('SW1',2)=='' or net('SW1',2).startswith('unconnected-(')):issues.append('local STOP contact map mismatch')
if [net('J3',i)for i in (1,2)]!=['STOP_LOCAL_NC','STOP_RETURN']:issues.append('external STOP is not in series')
if [net('JP1',i)for i in (1,2)]!=['STOP_LOCAL_NC','STOP_RETURN']:issues.append('STOP bypass bridges wrong contacts')
pairs=[('SW2','J2'),('SW3','J4'),('SW4','J5'),('SW5','J6')]
parallel=[]
for sw,j in pairs:
 a={net(sw,1),net(sw,2)};z={net(j,1),net(j,2)}
 parallel.append({'local':sw,'external':j,'nets':sorted(a),'parallel':a==z})
 if a!=z:issues.append('parallel external button mismatch '+j)
stop_cases=[]
for local_closed,external_present,external_closed in itertools.product([False,True],repeat=3):
 shunt=not external_present
 for keys in itertools.product([False,True],repeat=4):
  edges=[]
  if local_closed:edges.append((net('SW1',1),net('SW1',3)))
  if shunt:edges.append((net('JP1',1),net('JP1',2)))
  if external_present and external_closed:edges.append((net('J3',1),net('J3',2)))
  for (sw,j),pressed in zip(pairs,keys):
   if pressed:edges.append((net(sw,1),net(sw,2)))
  reached={'+5V'}
  while True:
   previous=len(reached)
   for a,z in edges:
    if a in reached or z in reached:reached.update([a,z])
   if len(reached)==previous:break
  actual='STOP_RETURN'in reached;expected=local_closed and (shunt or external_closed)
  if actual!=expected:issues.append('STOP contact path truth-table mismatch')
  stop_cases.append({'local_closed':local_closed,'external_present':external_present,'external_closed':external_closed,'other_key_states':keys,'stop_return_connected':actual})
if [net('J7',i)for i in range(1,5)]!=['I2C_SCL','I2C_SDA','GND','+3V3']:issues.append('OLED connector order mismatch')
keychecks=[]
for q,jpin,raw,bn,out,refs in [('Q1',2,'KEY_MAN_RAW','KEY_MAN_B','KEY_MAN_N',['R2','R3','R4','R5','C3']),('Q2',3,'KEY_AUTO_RAW','KEY_AUTO_B','KEY_AUTO_N',['R6','R7','R8','R9','C4'])]:
 if [net(q,i)for i in (1,2,3)]!=[bn,'GND',out]:issues.append('NPN pinout mismatch '+q)
 if net('J8',1)!='+5V'or net('J8',jpin)!=raw:issues.append('key raw pin map mismatch')
 for ref,val,pair in zip(refs,['2.2k','10k','100k','10k','10nF'],[(raw,'GND'),(raw,bn),(bn,'GND'),('+3V3',out),(out,'GND')]):
  if cs[ref]['value']!=val or {net(ref,1),net(ref,2)}!=set(pair):issues.append('key conditioning mismatch '+ref)
 keychecks.append({'transistor':q,'raw_net':raw,'conditioned_net':out,'active_level':'LOW','pins_B_E_C':[1,2,3]})
compact = args.control_variant in ('compact', 'compact-dual')
if compact:
 if mainfps['U33'].GetValue()!='MCP23017-E/SS':issues.append('Compact expander must match the checked MCP23017 pin map')
 if mainnet('U33',7)!='SPARE_B6' or mainnet('U33',21)!='SPARE_B7':issues.append('Compact key inputs must use GPB6/GPA0')
 sp={str(q['num']):q for q in main_components['U33']['pins']}
 if args.control_variant == 'compact-dual':
  legends = {item.GetText() for item in m.GetDrawings() if isinstance(item,p.PCB_TEXT)
             and item.GetLayer() in (p.F_SilkS,p.B_SilkS)}
  if 'PERMIT NO' not in legends or 'HH NC' in legends:
   issues.append('J31 must be marked for the external NO guard feedback contact.')
  connector_keys = [('J21',mainfps,'JST_XH_S2B-XH-A_1x02'),('J31',mainfps,'MC_1,5_2-G-3.81'),
                    ('J36',mainfps,'JST_ZE_SM05B-ZESS-TB_1x05'),('J8',fps,'JST_GH_SM03B-GHS-TB_1x03')]
  for ref, board_fps, key in connector_keys:
   if key not in str(board_fps[ref].GetFPID().GetLibItemName()):
    issues.append('Mechanically keyed connector footprint mismatch: ' + ref)
  if [mainnet('J36',i) for i in range(1,6)] != ['GND','HOST_AUX_N','LOCAL_AUX_N','HB_MON','PANEL_OK_MON']:
   issues.append('Guard receiver and transfer cavity assignments differ.')
  if any(ref.startswith('SW') for ref in mainfps):issues.append('Physical switch footprint on button-free main PCB')
  for pin, name in [('8', 'START_CMD_LED'), ('28', 'STOP_CMD_LED')]:
   if mainnet('U33', pin) != name or sp[pin].get('type') != 'output':
    issues.append('Incorrect compact-dual command LED direction or signal at U33.' + pin)
  for ref in ('SW1','SW2','SW3','SW4','SW5'):
   if cs[ref].get('dnp') or fps[ref].IsDNP():
    issues.append('Operator button omitted on panel: ' + ref)
  if [mainnet('J31', i) for i in (1,2)] != ['STOP_RETURN','K1_COIL_PLUS'] or mainnet('K1',1) != 'K1_COIL_PLUS':
   issues.append('Panel STOP does not directly remove K1 coil power.')
 if args.control_variant == 'compact':
  for pin in ['8','28']:
   if mainnet('U33',pin) and not mainnet('U33',pin).startswith('unconnected-('):issues.append('Compact port7 pin must be unconnected '+pin)
   if sp[pin].get('net') or sp[pin].get('type')!='output':issues.append('Compact port7 must be NC/output in source '+pin)
for ref,signal in [('R92','SPARE_B6'),('R93','SPARE_B7')]:
 if mainfps[ref].GetValue()!='100k'or{mainnet(ref,1),mainnet(ref,2)}!={signal,'GND'}:issues.append('main key pull-down mismatch '+ref)
key_firmware = 'Configure MCP23017 GPB6/GPB7 as inputs with internal pull-ups disabled.'
if compact:
 key_firmware = 'Configure MCP23017 GPB6/GPA0 as key inputs with pull-ups disabled.'
 key_firmware += (' Drive GPB7/GPA7 as the START and STOP command LED outputs.'
                  if args.control_variant == 'compact-dual' else ' Keep NC GPB7/GPA7 configured as outputs.')
drc=json.load(open(CHECKS/'integration-drc.json'));erc=json.load(open(CHECKS/'integration-erc.json'))
report={'control_variant':args.control_variant,'expander_key_inputs':{'manual':'GPB6 / U33.7','auto':'GPA0 / U33.21' if compact else 'GPB7 / U33.8'},'review_scope':'Independent native pin/net and interface topology check; no electrical hardware or firmware test.',
 'source_sha256':{'panel_board':before,'main_board':sha(mainpath),'panel_source':sha(args.panel_source),'main_source':sha(args.main_source),'independently_exported_main_netlist':sha(CHECKS/'integration-main-netlist.xml'),'independently_exported_panel_netlist':sha((CHECKS/'integration-netlist.xml'))},
 'main_connected_source_pins_checked':main_checked,'panel_components_including_mounting_holes':len(cs),'panel_connected_source_pins_checked':checked,
 'native_source_comparison_issues':issues,'host_harness':host_map,'common_ground':'Panel J1.7 returns directly through main J32.7. All twelve host cable cavities connect one-to-one; the former fanout cable is incompatible.',
 'stop_contact_path_cases_checked':len(stop_cases),'stop_contact_path_passed':not any('STOP'in i for i in issues),'stop_path':'+5V -> SW1 COM/NC -> STOP_LOCAL_NC -> external J3 NC contact -> STOP_RETURN -> main J31 ' + ('external guard auxiliary' if args.control_variant=='compact-dual' else 'high-high loop') + ' -> K1 coil',
 'stop_shunt_rule':'Fit JP1 only when no external NC STOP is fitted. It bypasses the external contact only, never local STOP.',
 'external_no_buttons':parallel,'oled_pin_order':{'1':'SCL','2':'SDA','3':'GND','4':'+3V3'},'key_channels':keychecks,
 'key_truth_table':{'MAN_contact_only':'KEY_MAN_N=0, KEY_AUTO_N=1','AUTO_contact_only':'KEY_MAN_N=1, KEY_AUTO_N=0','neither_contact':'1,1 invalid when key mode enabled','both_contacts':'0,0 invalid','panel_unplugged':'0,0 from main R92/R93 pull-downs, invalid'},
 'key_calculations':{'nominal_high_V_at_3V3':3.0,'MCP23017_min_VIH_at_3V3':2.64,'nominal_R_C_rise_time_constant_us':round((10000*100000/(10000+100000))*10e-9*1e6,3),'selected_key_raw_input_mA_5V_VBE0p7':round(5/2200*1000+(5-.7)/10000*1000,4),'STOP_added_wetting_mA_at5V':round(5/2200*1000,4),'note':'Nominal calculations; component tolerances, leakage, contact behavior, cable drops and temperature still need validation.'},
 'required_firmware':[key_firmware,'Enable key input only when intentionally fitted; do not silently auto-detect or fall back on invalid states.','Debounce mechanical contacts; 10nF filters are not sufficient debounce alone.','Mode/key changes stop and disarm; never start solely from selecting AUTO or MANUAL.','Reject both-high/both-low key states when key mode is enabled, and require a fresh START after fault/mode changes.'],
 'main_assembly_variant':'Main board physically removes SW3/SW4 and superseded J33/J34. Panel SW4/SW5 connect through GH12 J32.6/J32.4; all12 host cavities are one-to-one.',
 'native_layout_snapshot':{'drc_violations':len(drc['violations']),'unconnected':len(drc['unconnected_items']),'parity_issues':len(drc.get('schematic_parity',[])),'erc_violations':sum(len(s.get('violations',[]))for s in erc.get('sheets',[]))},
 'primary_references':['https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf','https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf','https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf','design/oled-selection.txt'],
 'main_board_routing_frozen_at_review':False,'hardware_tested':False,'firmware_implemented':False,'release_ready':False,
 'remaining_checks':['Purchased switch/connector contact orientation and harness continuity.','STOP actuator travel/height and OLED/enclosure spacing.','Gold/low-level dry-contact key suitability for approximately 2.7 mA at 5 V.','Mains starter START/STOP isolated auxiliary contacts and capacitor-start path.','Robu fabrication acceptance and assembled-board functional/thermal/EMC tests.']}
if args.control_variant == 'compact-dual':
 report['main_assembly_variant'] = 'All five physical operator switches on the panel. No switch footprints on the main PCB. Twelve cavities one-to-one from panel J1 to main J32.'
 report.pop('firmware_implemented')
 report['firmware_scope'] = 'Native hardware integration check only. Target application and live switching were not exercised.'
unchanged=frozen=={str(path):sha(path) for path in inputs}
if not unchanged:raise SystemExit('Native inputs changed during review; rerun.')
main_frozen=False
if args.main_summary.exists():
 summary=json.loads(args.main_summary.read_text())
 expected_hashes=summary.get('source_sha256',{})
 relevant=[path for path in inputs if path==mainpath or path.parent==mainpath.parent or path==args.main_source.resolve()]
 main_frozen=bool(summary.get('independent_native_checks_passed')) and all(expected_hashes.get(str(path.relative_to(B)))==sha(path) for path in relevant)
 report['main_native_summary_sha256']=sha(args.main_summary)
report['main_native_evidence_current']=main_frozen
report['main_board_routing_frozen_at_review']=main_frozen and args.require_frozen_main
report['native_inputs_unchanged']=unchanged
report['integration_passed']=not issues and not any(report['native_layout_snapshot'].values())
report['main_source_and_schematic_compared']=True
(CHECKS/'integration-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'issues':issues,'panel_connected_pins':checked,'main_connected_pins':main_checked,'stop_cases':len(stop_cases),'layout':report['native_layout_snapshot'],'main_native_evidence_current':main_frozen,'main_frozen':report['main_board_routing_frozen_at_review']},indent=2))
raise SystemExit(0 if report['integration_passed'] and (main_frozen or not args.require_frozen_main) else 1)
