#!/usr/bin/env python3
"""Audit Rev E control nets and author an unpowered harness acceptance plan.

The generated matrix is a specification, never a fabricated measurement result.
No native schematic or PCB is changed. Meter stimulus is not literally zero energy.
"""
from pathlib import Path
import hashlib
import itertools
import json
import subprocess
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'hardware/main-rev-e/checks'
CLI = BASE / '.tools/kicad-cli'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native(project, output):
    subprocess.run([str(CLI), 'sch', 'export', 'netlist', '--format', 'kicadxml',
                    '-o', str(output), str(project)], check=True, capture_output=True)
    tree = ET.parse(output)
    mapping = {}
    for net in tree.findall('.//nets/net'):
        for node in net.findall('node'):
            mapping[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name']
    return mapping


def connected(edges, start, end):
    seen, pending = {start}, [start]
    while pending:
        a = pending.pop()
        for x, y in edges:
            b = y if x == a else x if y == a else None
            if b is not None and b not in seen:
                seen.add(b)
                pending.append(b)
    return end in seen


def audit():
    OUT.mkdir(parents=True, exist_ok=True)
    main_sch = BASE / 'hardware/main-rev-e/pump-controller-main-rev-e.kicad_sch'
    panel_sch = BASE / 'hardware/panel-rev-e/pump-panel-rev-e.kicad_sch'
    main_xml, panel_xml = OUT / 'control-main-netlist.xml', OUT / 'control-panel-netlist.xml'
    main, panel = native(main_sch, main_xml), native(panel_sch, panel_xml)
    issues, checked = [], []
    def pins(domain, ref, expected):
        mapping = main if domain == 'main' else panel
        for number, net in expected.items():
            got = mapping.get((ref, str(number)))
            ok = got == net if net is not None else got is None or got.startswith('unconnected-')
            checked.append({'domain': domain, 'ref': ref, 'pin': str(number),
                            'expected_net': net, 'actual_net': got, 'passed': ok})
            if not ok:
                issues.append(checked[-1])
    host = ['+5V', 'STOP_RETURN', 'MAN_RETURN', 'AUTO_RETURN', 'START_N',
            'RESET_N', 'GND', '+3V3', 'I2C_SDA', 'I2C_SCL', 'SPARE_B6', 'SPARE_B7']
    pins('main', 'J32', {str(i + 1): v for i, v in enumerate(host)})
    panel_host = host[:10] + ['KEY_MAN_N', 'KEY_AUTO_N']
    pins('panel', 'J1', {str(i + 1): v for i, v in enumerate(panel_host)})
    main_expected = {
        'U3': {25:'RUN_CMD',26:'PERMIT_D',27:'HEARTBEAT',30:'ARM_CMD'},
        'J31': {1:'STOP_RETURN',2:'K1_COIL_PLUS'},
        'J30': {1:'CTRL_IN',2:'CTRL_OUT'},
        'K1': {1:'K1_COIL_PLUS',5:'K1_LOW',2:'CTRL_IN',3:'CTRL_MID'},
        'K2': {1:'+5V',5:'K2_LOW',2:'CTRL_MID',3:'CTRL_OUT'},
        'D31': {1:'K1_COIL_PLUS',2:'K1_LOW'},
        'D32': {1:'+5V',2:'K2_LOW'},
        'Q30': {1:'K1_GATE',2:'GND',3:'K1_LOW'},
        'Q31': {1:'K2_GATE',2:'GND',3:'K2_LOW'},
        'R74': {1:'PERMIT_Q',2:'K1_GATE'},
        'R75': {1:'K1_GATE',2:'GND'},
        'R76': {1:'RUN_CMD',2:'K2_GATE'},
        'R77': {1:'K2_GATE',2:'GND'},
        'R70': {1:'+3V3',2:'SAFE_CLEAR_N'},
        'R71': {1:'HEARTBEAT',2:'GND'},
        'R72': {1:'PERMIT_D',2:'GND'},
        'R78': {1:'ARM_CMD',2:'GND'},
        'U30': {1:'SAFE_CLEAR_N',2:'GND',3:'GND',4:'HEARTBEAT',5:'+3V3'},
        'U32': {1:'SAFE_CLEAR_N',2:'+3V3',3:'GND'},
        'D30': {1:'MCU_EN',2:'SAFE_CLEAR_N'},
        'D35': {1:'INTERLOCK_OK',2:'SAFE_CLEAR_N'},
        'U35': {1:None,2:'HH_SENSE',3:'GND',4:'INTERLOCK_OK',5:'+3V3'},
        'U36': {1:None,2:'SAFE_CLEAR_N',3:'GND',4:'ARM_CLEAR_N',5:'+3V3'},
        'C77': {1:'+3V3',2:'GND'},
        'U37': {1:'STOP_SENSE_RAW',2:'AUTO_SENSE',3:'MAN_SENSE_RAW',4:'GND',5:'MAN_SENSE',6:'AUTO_SENSE_RAW',7:'STOP_SENSE',8:'+3V3'},
        'C78': {1:'+3V3',2:'GND'},
        'C80': {1:'STOP_SENSE_RAW',2:'GND'},'C82': {1:'MAN_SENSE_RAW',2:'GND'},'C84': {1:'AUTO_SENSE_RAW',2:'GND'},
        'U31': {1:'ARM_CMD',2:'+3V3',3:None,4:'GND',5:'ARM_Q',
                6:'ARM_CLEAR_N',7:'+3V3',8:'+3V3'},
        'U34': {1:'ARM_Q',2:'PERMIT_D',3:'GND',4:'PERMIT_Q',5:'+3V3'},
        'U33': {1:'START_FILTER',2:'RESET_FILTER',3:'STOP_SENSE',4:'MAN_SENSE',
                5:'AUTO_SENSE',6:'INTERLOCK_OK',7:'SPARE_B6',8:'SPARE_B7',18:'MCU_EN'},
        'R92': {1:'SPARE_B6',2:'GND'}, 'R93': {1:'SPARE_B7',2:'GND'},
        'R80': {1:'STOP_RETURN',2:'STOP_SENSE_RAW'},'R81': {1:'STOP_SENSE_RAW',2:'GND'},
        'R82': {1:'MAN_RETURN',2:'MAN_SENSE_RAW'},'R83': {1:'MAN_SENSE_RAW',2:'GND'},
        'R84': {1:'AUTO_RETURN',2:'AUTO_SENSE_RAW'},'R85': {1:'AUTO_SENSE_RAW',2:'GND'},
        'R86': {1:'K1_COIL_PLUS',2:'HH_SENSE'},'R87': {1:'HH_SENSE',2:'GND'},
        'C86': {1:'HH_SENSE',2:'GND'},
        'R88': {1:'START_N',2:'START_FILTER'},'R89': {1:'+3V3',2:'START_FILTER'},
        'R90': {1:'RESET_N',2:'RESET_FILTER'},'R91': {1:'+3V3',2:'RESET_FILTER'},
    }
    for ref, values in main_expected.items():
        pins('main', ref, values)
    panel_expected = {
        'SW1': {1:'+5V',2:None,3:'STOP_LOCAL_NC'},
        'JP1': {1:'STOP_LOCAL_NC',2:'STOP_RETURN'},
        'J3': {1:'STOP_LOCAL_NC',2:'STOP_RETURN'},
        'J7': {1:'I2C_SCL',2:'I2C_SDA',3:'GND',4:'+3V3'},
        'J8': {1:'+5V',2:'KEY_MAN_RAW',3:'KEY_AUTO_RAW'},
        'R1': {1:'STOP_RETURN',2:'GND'},
    }
    buttons = [('SW2','J2','START_N','GND'),('SW3','J4','MAN_RETURN','STOP_RETURN'),
               ('SW4','J5','RESET_N','GND'),('SW5','J6','AUTO_RETURN','STOP_RETURN')]
    for sw, jack, a, b in buttons:
        panel_expected[sw] = panel_expected[jack] = {1:a,2:b}
    for q, raw, base, sense, wet, rb, rbe, pull, cap in [
            ('Q1','KEY_MAN_RAW','KEY_MAN_B','KEY_MAN_N','R2','R3','R4','R5','C3'),
            ('Q2','KEY_AUTO_RAW','KEY_AUTO_B','KEY_AUTO_N','R6','R7','R8','R9','C4')]:
        panel_expected[q] = {1:base,2:'GND',3:sense}
        panel_expected[wet] = {1:raw,2:'GND'}
        panel_expected[rb] = {1:raw,2:base}
        panel_expected[rbe] = {1:base,2:'GND'}
        panel_expected[pull] = {1:'+3V3',2:sense}
        panel_expected[cap] = {1:sense,2:'GND'}
    for ref, values in panel_expected.items():
        pins('panel', ref, values)
    # Exact membership catches extra branches that individual expected-pin checks miss.
    membership_checks=[]
    expected_members={
        'main':{
            'STOP_RETURN':['J31.1','J32.2','R80.1'],
            'STOP_SENSE_RAW':['R80.2','R81.1','C80.1','U37.1'],
            'MAN_SENSE_RAW':['R82.2','R83.1','C82.1','U37.3'],
            'AUTO_SENSE_RAW':['R84.2','R85.1','C84.1','U37.6'],
            'STOP_SENSE':['U33.3','U37.7'],'MAN_SENSE':['U33.4','U37.5'],'AUTO_SENSE':['U33.5','U37.2'],
            'K1_COIL_PLUS':['D31.1','J31.2','K1.1','R86.1'],
            'CTRL_IN':['J30.1','K1.2'],'CTRL_MID':['K1.3','K2.2'],'CTRL_OUT':['J30.2','K2.3'],
            'ARM_CLEAR_N':['U31.6','U36.4'],
            'SAFE_CLEAR_N':['D30.2','D35.2','R70.2','U30.1','U32.1','U36.2'],
            'ARM_CMD':['J2.4','R78.1','U3.30','U31.1'],'ARM_Q':['U31.5','U34.1'],
            'PERMIT_Q':['R74.1','U34.4'],'K1_GATE':['Q30.1','R74.2','R75.1'],
            'K2_GATE':['Q31.1','R76.2','R77.1'],'RUN_CMD':['R76.1','U3.25']},
        'panel':{
            '+5V':['J1.1','J8.1','SW1.1'],
            'STOP_LOCAL_NC':['J3.1','JP1.1','SW1.3'],
            'STOP_RETURN':['J1.2','J3.2','J4.2','J6.2','JP1.2','R1.1','SW3.2','SW5.2']}}
    for domain,nets in expected_members.items():
        mapping=main if domain=='main' else panel
        for net,wanted in nets.items():
            actual=sorted(ref+'.'+pin for (ref,pin),name in mapping.items() if name==net)
            record={'domain':domain,'net':net,'expected_members':sorted(wanted),
                    'actual_members':actual,'passed':actual==sorted(wanted)}
            membership_checks.append(record)
            if not record['passed']:issues.append(record)
    value_checks=[]
    main_values={'U37':'SN74LVC3G17DCUR','C78':'100nF','R74':'100R','R70':'47k','R71':'2.2k','R72':'2.2k','R78':'2.2k','R76':'22R',
                 'R77':'2.2k','R75':'100k','C77':'100nF','U36':'SN74LVC1G17DBVR',
                 'R80':'10k','R81':'33k','R82':'10k','R83':'33k','R84':'10k',
                 'R85':'33k','R86':'22k','R87':'100k','C86':'10nF',
                 'R92':'100k','R93':'100k'}
    panel_values={'R1':'2.2k','R2':'2.2k','R6':'2.2k','R3':'10k','R7':'10k',
                  'R4':'100k','R8':'100k','R5':'10k','R9':'10k','C3':'10nF',
                  'C4':'10nF','Q1':'MMBT3904','Q2':'MMBT3904'}
    for domain,xml,expected in [('main',main_xml,main_values),('panel',panel_xml,panel_values)]:
        actual={c.attrib['ref']:c.findtext('value') for c in ET.parse(xml).findall('.//components/comp')}
        for ref,value in expected.items():
            record={'domain':domain,'ref':ref,'expected':value,'actual':actual.get(ref),'passed':actual.get(ref)==value}
            value_checks.append(record)
            if not record['passed']:issues.append(record)
    # Contact-only reachability excludes intentional resistors, transistors,
    # capacitors and relay coils. It checks unintended copper/contact bypasses,
    # not pickup voltage, analogue transient response or component failures.
    cases, failed = 0, []
    for local, external, shunt, hh, start, mode, setting, nxt, km, ka in itertools.product([False,True], repeat=10):
        edges = []
        for closed, a, b in [(local,panel['SW1','1'],panel['SW1','3']),
                (external,panel['J3','1'],panel['J3','2']),
                (shunt,panel['JP1','1'],panel['JP1','2']),
                (hh,main['J31','1'],main['J31','2']),
                (km,panel['J8','1'],panel['J8','2']),
                (ka,panel['J8','1'],panel['J8','3'])]:
            if closed: edges.append((a,b))
        for closed, (sw, jack, _, _) in zip([start,mode,setting,nxt],buttons):
            if closed: edges.append((panel[sw,'1'],panel[sw,'2']))
        got = connected(edges, panel['J1','1'], main['K1','1'])
        expected = local and (external or shunt) and hh
        cases += 1
        if got != expected:
            failed.append({'states':[local,external,shunt,hh,start,mode,setting,nxt,km,ka],
                           'got':got,'expected':expected})
    relay_cases=[]
    for k1,k2 in itertools.product([False,True], repeat=2):
        edges=[]
        for closed,ref in [(k1,'K1'),(k2,'K2')]:
            if closed:edges.append((main[ref,'2'],main[ref,'3']))
        got=connected(edges, main['J30','1'],main['J30','2'])
        relay_cases.append({'K1_NO_closed':k1,'K2_NO_closed':k2,'conductive':got,
                            'passed':got==(k1 and k2)})
    tracked = [BASE/'design/main-rev-e.json', BASE/'design/panel-rev-e.json',main_xml,panel_xml]
    tracked += sorted(main_sch.parent.glob('*.kicad_sch')) + sorted(panel_sch.parent.glob('*.kicad_sch'))
    report = {
        'schema_version':1,'scope':'Independent freshly exported schematic pin map and contact-only graph audit; no board mutation, hardware measurements or firmware simulation.',
        'input_sha256':{str(p.relative_to(BASE)):sha(p) for p in tracked},
        'pin_checks':checked,'value_checks':value_checks,'exact_critical_net_membership':membership_checks,'issues':issues,'stop_reachability_cases':cases,
        'stop_reachability_failures':failed,'relay_series_cases':relay_cases,
        'contact_graph_model':'Ideal copper/closed contacts only; resistors, semiconductor paths, stored charge, pickup/dropout, EMI and contact welding are not modeled.',
        'prohibited_configuration':'JP1 fitted while an external STOP is intended to operate; this bypasses that external contact.',
        'panel_materialization':{'native_schematic_present':panel_sch.is_file(),
             'native_pcb_present':(panel_sch.with_suffix('.kicad_pcb')).is_file(),
             'source_has_key_conditioning_transistors':True,'physically_assembled_or_tested':False,
             'panel_is_passive_only':False,'controller_or_firmware_on_panel':False},
        'hardware_tested':False,'firmware_implemented':False,
        'passed':not issues and not failed and all(c['passed'] for c in relay_cases),
    }
    (OUT/'hardwired-control-review.json').write_text(json.dumps(report,indent=2)+'\n')
    return report, host


def acceptance(host):
    closed={'kind':'resistance','minimum_ohm':0,'maximum_ohm':2,
            'limit_basis':'Engineering assembly-screen limit, including zeroed fixture/contact resistance; not a connector rated-life specification.'}
    opened={'kind':'resistance','minimum_ohm':1000000,'maximum_ohm':None,
            'limit_basis':'Low-voltage open-circuit screen on disconnected cable/mechanical contacts only; not dielectric withstand or mains insulation qualification.'}
    no_hard_short={'kind':'resistance','minimum_ohm':100,'maximum_ohm':None,
                   'limit_basis':'Populated-panel copper-bridge screen; intentional resistors and semiconductor paths prevent a universal megohm criterion.'}
    stages=[]
    def step(identifier,a,b,expected,state=None):
        return {'id':identifier,'a':a,'b':b,'state':state or {},'acceptance':expected,
                'measured_ohm':None,'result':'not_run'}
    # Check every pair of exposed endpoints, including shorts at either end.
    for label,n,ends in [('GH12',12,['MAIN_J32','PANEL_J1']),('PH4',4,['PANEL_J7','OLED_PH4'])]:
        endpoints=[(end,pin) for end in ends for pin in range(1,n+1)]
        rows=[]
        for i,(a,b) in enumerate(itertools.combinations(endpoints,2),1):
            match=a[0]!=b[0] and a[1]==b[1]
            rows.append(step(f'{label}-{i:03}',f'{a[0]}.{a[1]}',f'{b[0]}.{b[1]}',closed if match else opened))
        stages.append({'id':label,'setup':'Cable detached at both ends from every PCB, OLED and other equipment. Cavity numbers follow the connector drawing mating view; colours do not define function.',
                       'expected_closed_pair_count':n,'expected_open_pair_count':len(rows)-n,'cases':rows})
    rows=[]
    for i,(gh,ph) in enumerate(itertools.product([f'{end}.{pin}' for end in ['MAIN_J32','PANEL_J1'] for pin in range(1,13)],
             [f'{end}.{pin}' for end in ['PANEL_J7','OLED_PH4'] for pin in range(1,5)]),1):
        rows.append(step(f'LOOM-CROSS-{i:03}',gh,ph,opened))
    stages.append({'id':'LOOM_CROSS','setup':'Both completed cables in the fixture, with all four ends disconnected from electronics. No wire joins the two cable assemblies.','cases':rows})
    rows=[]
    for name,kind in [('EXT_START','NO'),('EXT_STOP','NC'),('EXT_MODE','NO'),('EXT_SET','NO'),('EXT_NEXT','NO'),('HH_FLOAT','NC')]:
        for active in [False,True]:
            contact_closed=active if kind=='NO' else not active
            rows.append(step(name+('-ACTIVE' if active else '-REST'),name+'.1',name+'.2',closed if contact_closed else opened,
                             {'actuated_or_high_high_trip':active}))
    stages.append({'id':'OPTIONAL_CONTACT_LEADS','setup':'Test each fitted lead and its isolated mechanical contact disconnected from the PCB. Skip absent options with reason. HH active means the float is in its trip position. Test only electrically isolated auxiliary contacts; original mains/capacitor contacts remain disconnected from this fixture.',
                   'cases':rows})
    rows=[]
    for state,contacts in [('MANUAL',{(1,2)}),('AUTO',{(1,3)}),('UNPLUGGED',set())]:
        for a,b in itertools.combinations([1,2,3],2):
            rows.append(step(f'KEY-{state}-{a}{b}',f'KEY_J8.{a}',f'KEY_J8.{b}',closed if (a,b) in contacts else opened,{'key_position':state}))
    stages.append({'id':'OPTIONAL_KEY_CONTACTS','setup':'Completed key lead detached from panel; J8.1 common, .2 MANUAL, .3 AUTO. UNPLUGGED tests the empty fixture, not a claimed center-off key position. Both throws must not be closed in either stable selected position.','cases':rows})
    # Panel at rest; only the NC stop shunt joins distinct net names.
    terminals={f'PANEL_J1.{i+1}':n for i,n in enumerate(host[:10]+['KEY_MAN_N','KEY_AUTO_N'])}
    terminals.update({'PANEL_J7.1':'I2C_SCL','PANEL_J7.2':'I2C_SDA','PANEL_J7.3':'GND','PANEL_J7.4':'+3V3'})
    rows=[]
    for i,(a,b) in enumerate(itertools.combinations(terminals,2),1):
        na,nb=terminals[a],terminals[b]
        match=na==nb or {na,nb}=={'+5V','STOP_RETURN'}
        rows.append(step(f'PANEL-REST-{i:03}',a,b,closed if match else no_hard_short))
    stages.append({'id':'POPULATED_PANEL_REST','setup':'Panel only, no host/OLED/key/external-contact cables. JP1 fitted; SW1 released, all NO keys released. Measure both meter polarities after capacitive readings settle for at least3s. This screen finds copper bridges and direct miswiring, not component-value or powered-logic errors.',
                   'cases':rows})
    rows=[]
    for configuration,shunt,external_present in [('LOCAL_ONLY',True,False),('LOCAL_PLUS_EXTERNAL',False,True),('MISSING_EXTERNAL_OPEN',False,False)]:
        for local_open in [False,True]:
            external_states=[False,True] if external_present else [True]
            for external_open in external_states:
                continuity=not local_open and (shunt or not external_open)
                rows.append(step(f'STOP-{configuration}-L{int(local_open)}E{int(external_open)}','HOST_BREAKOUT.1','HOST_BREAKOUT.2',closed if continuity else opened,
                    {'configuration':configuration,'JP1_fitted':shunt,'local_STOP_pressed':local_open,'external_STOP_present':external_present,'external_STOP_open':external_open}))
    stages.append({'id':'HOST_AND_STOP','setup':'Verified GH12 lead attached only to the panel. Main PCB and OLED detached. Key lead and external NO leads removed. Probe the main-end breakout cavities1/2. Exercise all four NO panel keys in each state: none may alter the expected STOP continuity. Never fit JP1 with an operational external STOP.','cases':rows})
    rows=[]
    for name,signal,common in [('START',5,7),('MODE',3,2),('SET',6,7),('NEXT',4,2)]:
        for local,external in itertools.product([False,True],repeat=2):
            rows.append(step(f'NO-{name}-L{int(local)}E{int(external)}',f'HOST_BREAKOUT.{signal}',f'HOST_BREAKOUT.{common}',closed if local or external else opened,
                             {'local_NO_pressed':local,'external_NO_pressed':external,'external_option':name}))
    stages.append({'id':'PARALLEL_NO_KEYS','setup':'Verified GH12 attached only to panel, main/OLED/key detached, all other NO buttons released. Test one matching optional external NO lead at a time. Its connector mapping must match START J2, MODE J4, SET J5 or NEXT J6.','cases':rows})
    rows=[]
    for local_open,external_open,hh_trip in itertools.product([False,True],repeat=3):
        rows.append(step(f'CHAIN-L{int(local_open)}E{int(external_open)}H{int(hh_trip)}','HOST_BREAKOUT.1','FIXTURE_HH_RETURN',
            closed if not (local_open or external_open or hh_trip) else opened,
            {'local_STOP_pressed':local_open,'external_STOP_open':external_open,'HH_float_tripped':hh_trip,'JP1_fitted':False}))
    stages.append({'id':'STOP_HH_CONTACT_FIXTURE','setup':'No main PCB: a labelled fixture jumper connects HOST_BREAKOUT.2 to the detached HH lead cavity1; HH cavity2 goes only to FIXTURE_HH_RETURN. Panel/key/OLED state as HOST_AND_STOP; external NC STOP fitted and JP1 removed. This mimics the series contact path without energizing relays and does not measure main-board J31 copper or latch timing.','cases':rows})
    return {
        'schema_version':1,'title':'Rev E unpowered loom, panel and STOP contact acceptance matrix',
        'status':'specification_only','hardware_tested':False,'all_measurements_initially_unrun':True,
        'meaning_of_unpowered':'No mains, motor, coil, USB, programmer, battery or other operating supply is connected. Stored energy is verified absent before removing/test connecting parts. A bounded resistance-meter stimulus is permitted; this is not literally zero electrical energy.',
        'instrument_limits':{'maximum_open_circuit_test_voltage_V':0.2,'maximum_short_circuit_test_current_A':0.001,
             'zero_fixture_lead_resistance':True,'use_limited_resistance_range_not_diode_or_megger':True,
             'rationale':'Avoid turning on semiconductor junctions in populated-panel screens. Contact wetting, rated voltage and mechanical endurance require separate powered qualification.'},
        'exclusions':['Mains dielectric/insulation resistance or protective-earth testing','Any measurements with installed mains capacitors or live CT assembly connected','Relay pickup/dropout, contactor interruption, watchdog/reset/latch operation','Powered key-transistor logic, I2C operation, OLED polarity under power','Firmware, EMC, sensor accuracy, motor dry-run protection or release approval'],
        'measurement_record_fields':['DUT serial','board revision','cable part/lot','instrument identification','meter limits and calibration','fixture zero resistance','operator','date','case id','measured resistance/polarity','pass/fail/not applicable and reason'],
        'acceptance_policy':'Every applicable case must pass; a failed case stops acceptance. Retest the complete affected cable/panel stage after rework. Never convert not_run to pass without an actual recorded measurement. All limits are assembly-screen criteria, not manufacturer or safety certification.',
        'pinmaps':{'GH12':{str(i+1):v for i,v in enumerate(host)},
                   'PH4':{'1':'I2C_SCL','2':'I2C_SDA','3':'GND','4':'+3V3'},
                   'KEY_GH3':{'1':'+5V common','2':'MANUAL raw','3':'AUTO raw'}},
        'powered_key_test_deferred':{'MANUAL':[0,1],'AUTO':[1,0],'key_detached':[1,1],'panel_detached':[0,0],
             'order':['KEY_MAN_N','KEY_AUTO_N'],'note':'Expected powered logic only, not measurable as logic while unpowered. With key enabled,11/00 invalid; internal MCP pullups disabled. No universal individual-wire-fault coverage is claimed.'},
        'stages':stages,'case_count':sum(len(s['cases']) for s in stages),
    }


def main():
    report,host=audit()
    matrix=acceptance(host)
    matrix['audit_evidence']={'path':'../hardware/main-rev-e/checks/hardwired-control-review.json','sha256':sha(OUT/'hardwired-control-review.json'),'pin_and_contact_graph_passed':report['passed']}
    path=BASE/'design/rev-e-unpowered-harness-acceptance.json'
    path.write_text(json.dumps(matrix,indent=2)+'\n')
    print(json.dumps({'audit_passed':report['passed'],'checked_pins':len(report['pin_checks']),
                      'stop_cases':report['stop_reachability_cases'],'acceptance_cases':matrix['case_count'],
                      'physical_tests_run':0},indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
