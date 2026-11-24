"""Verify R4 relay lands, field routing, STOP supply and JLC procurement.

Run with KiCad's Python after tools/export_boards.py completes. CAM connectivity,
physical temperature rise and actual starter waveforms are separate checks.
"""
import csv
import hashlib
import json
from fnmatch import fnmatchcase
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
path = ROOT/'hardware/main/pump-direct.kicad_pcb'
board = pcbnew.LoadBoard(str(path))
fps = {f.GetReference(): f for f in board.GetFootprints()}
def mm(point):
    return [pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)]
def near(a, b):
    return abs(a-b) < 0.00001
errors = []
for ref, channel, x, y in [('K1','A',42,81.2), ('K2','B',87,81)]:
    fp = fps[ref]
    if fp.GetFieldText('MPN') != 'G5RL-1-E-HR DC5':
        errors.append(ref+': wrong relay variant (SPST is not acceptable)')
    expected = {'1': ref+'_LOW', '8': 'K1_5V' if ref == 'K1' else '+5V_CMD'}
    for numbers, suffix in [('27','NC'), ('36','COM'), ('45','NO')]:
        expected.update({n:'CTRL_'+channel+'_'+suffix for n in numbers})
    pads = {p.GetNumber(): p for p in fp.Pads()}
    if set(pads) != set(expected):
        errors.append(ref+': all eight physical terminals must be populated')
    positions = {'1': [x,y], '8':[x,y+7.5], '2':[x-15,y], '7':[x-15,y+7.5],
                 '3':[x-20,y], '6':[x-20,y+7.5], '4':[x-25,y], '5':[x-25,y+7.5]}
    for number, net in expected.items():
        p = pads[number]
        if p.GetNetname() != net or not all(near(a,b) for a,b in zip(mm(p.GetPosition()), positions[number])):
            errors.append(ref+'.'+number+': physical pin/net mismatch')
        if not all(near(v,1.3) for v in mm(p.GetDrillSize())):
            errors.append(ref+'.'+number+': wrong manufacturer hole size')
for ref, channel in [('J30','A'), ('J35','B')]:
    fp = fps[ref]
    if fp.GetFieldText('MPN') != '1711738':
        errors.append(ref+': wrong power terminal')
    for p in fp.Pads():
        suffix = {'1':'NO', '2':'COM', '3':'NC'}[p.GetNumber()]
        if p.GetNetname() != 'CTRL_'+channel+'_'+suffix:
            errors.append(ref+': expected pin 1 NO, 2 COM, 3 NC')
# Physical edge access and the compact outline are intentional release requirements.
for ref, expected in {'J30':(17,98.4,0), 'J35':(62,98.4,0),
                       'J20':(83,-5.5,180), 'J21':(25,-3.5,180),
                       'H1':(4,-10.5,0), 'H2':(96,-10.5,0),
                       'H3':(96,100,0), 'H4':(4,100,0)}.items():
    fp=fps[ref]
    if not all(near(a,b) for a,b in zip(mm(fp.GetPosition())+[fp.GetOrientationDegrees()],expected)):
        errors.append(ref+': unexpected compact-layout pose or wire-entry orientation')
edges=[d for d in board.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]
points=[mm(p) for d in edges for p in [d.GetStart(),d.GetEnd()]]
width=max(p[0] for p in points)-min(p[0] for p in points)
height=max(p[1] for p in points)-min(p[1] for p in points)
if not near(width,100) or not near(height,118.5) or board.GetCopperLayerCount()!=6:
    errors.append('Expected 100 x 118.5 mm, six-layer compact main board')
field = {}
for channel in ['A','B']:
    for suffix in ['NC','COM','NO']:
        name = 'CTRL_'+channel+'_'+suffix
        tracks = [t for t in board.GetTracks() if t.GetNetname() == name]
        if not tracks or any(t.GetClass() != 'PCB_TRACK' for t in tracks):
            errors.append(name+': power path must not depend on a small via')
        layers = {t.GetLayer() for t in tracks}
        if layers != {pcbnew.F_Cu, pcbnew.B_Cu} or any(pcbnew.ToMM(t.GetWidth()) < 2.79999 for t in tracks):
            errors.append(name+': expected >=2.8 mm routes on BOTH outer layers')
        field[name] = {'layers':['F.Cu','B.Cu'], 'minimum_width_mm':min(pcbnew.ToMM(t.GetWidth()) for t in tracks), 'separate_vias':0}
        relay = 'K1' if channel == 'A' else 'K2'
        connector = 'J30' if channel == 'A' else 'J35'
        relay_pins, terminal_pin = {'NC':({'2','7'},'3'), 'COM':({'3','6'},'2'), 'NO':({'4','5'},'1')}[suffix]
        actual_pads = {(f.GetReference(),p.GetNumber()) for f in fps.values() for p in f.Pads() if p.GetNetname() == name}
        if actual_pads != {(relay,p) for p in relay_pins} | {(connector,terminal_pin)}:
            errors.append(name+': field contact must have no connection to control or sensing circuitry')
        patterns = json.loads(path.with_suffix('.kicad_pro').read_text())['net_settings']['netclass_patterns']
        classes = {p['netclass'] for p in patterns if fnmatchcase(name,p['pattern'])}
        if not {'LIVE','HV','STARTER_FIELD'} <= classes or classes & {'SELV','CABINET'}:
            errors.append(name+': missing hazardous-voltage isolation rule coverage')
        field[name]['isolated_from_control_nets'] = True
        field[name]['net_classes'] = sorted(classes)
stop_pads = {(f.GetReference(),p.GetNumber()) for f in fps.values() for p in f.Pads() if p.GetNetname() == 'STOP_RETURN'}
if stop_pads != {('J32','2'),('R80','1'),('R86','1'),('R247','1')}:
    errors.append('STOP_RETURN must feed sensing/base current, not a relay coil')
for ref, nets in {'Q50':{1:'K1_PGATE',2:'+5V_CMD',3:'K1_5V'}, 'Q51':{1:'K1_PBASE',2:'GND',3:'K1_PGATE'}, 'D31':{1:'K1_5V',2:'K1_LOW'}}.items():
    pads = {p.GetNumber():p for p in fps[ref].Pads()}
    for number, name in nets.items():
        if pads[str(number)].GetNetname() != name:
            errors.append(ref+': high-side / flyback pin mismatch')
with (ROOT/'manufacturing/main-BOM.csv').open() as stream:
    bom = list(csv.DictReader(stream))
with (ROOT/'manufacturing/main-CPL.csv').open() as stream:
    cpl = {r['Designator']:r for r in csv.DictReader(stream)}
# Independently calculated nominal package centres, not coil/first-pin datums.
for ref, centre in {'K1':(29.9,-84.95), 'K2':(74.9,-84.75), 'J30':(22.08,-98.1), 'J35':(67.08,-98.1)}.items():
    row = cpl.get(ref)
    expected_rotation = 0 if ref.startswith('J') else 180
    if row is None or row['Layer'] != 'Top' or not near(float(row['Mid X']),centre[0]) or not near(float(row['Mid Y']),centre[1]) or not near(float(row['Rotation']),expected_rotation):
        errors.append(ref+': JLC CPL must use the package centre and expected native pose')
for mpn, code, refs in [('G5RL-1-E-HR DC5','C1563288',{'K1','K2'}), ('1711738','C91156',{'J30','J35'})]:
    rows = [r for r in bom if r['Manufacturer Part Number'] == mpn]
    if len(rows) != 1 or rows[0]['JLCPCB Part #'] != code or set(rows[0]['Designator'].split(',')) != refs or rows[0]['Quantity'] != '2':
        errors.append(mpn+': missing/wrong JLC BOM selection')
result = {'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'board_dimensions_mm':[100,118.5], 'terminal_wire_entry':'outward bottom edge', 'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'errors':errors,
          'relays':'G5RL-1-E-HR DC5 / C1563288', 'terminal_order':{'1':'NO','2':'COM','3':'NC'},
          'field_routes':field, 'STOP_loop_carries_relay_coil_current':False,
          'nominal_total_coil_current_mA':160, 'physical_load_and_thermal_qualification':'PENDING',
          'supplier_reservation_and_DFM_approval':'PENDING'}
out = ROOT/'verification/relay-upgrade-2026-11-24/R4/relay-check.json'
out.write_text(json.dumps(result,indent=2)+'\n')
if errors:
    raise SystemExit('\n'.join(errors))
print('PASS: eight-pin SPDT relays, both terminals of each contact, NC/COM/NO outputs, dual-layer power paths, STOP supply and JLC BOM.')
