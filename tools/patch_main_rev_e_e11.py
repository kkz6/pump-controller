#!/usr/bin/env python3
"""Add Rev E three-channel Schmitt input conditioning to sources, never PCB.

--root selects an explicit repository/staging root. --source patches current
schematic labels/fields without replacing existing UUIDs or sheet positions.
The native PCB must receive a separately reviewed matching physical ECO.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re
import tempfile
import generate_cad as cad
from patch_main_rev_e_bias import expression_ranges

PROJECT='pump-controller-main-rev-e'
SHEET='controls_conditioning'
TITLE='STOP, MODE and NEXT input conditioning'
RAW_RENAMES={
    'R80':('2','STOP_SENSE','STOP_SENSE_RAW'),
    'R81':('1','STOP_SENSE','STOP_SENSE_RAW'),
    'C80':('1','STOP_SENSE','STOP_SENSE_RAW'),
    'R82':('2','MAN_SENSE','MAN_SENSE_RAW'),
    'R83':('1','MAN_SENSE','MAN_SENSE_RAW'),
    'C82':('1','MAN_SENSE','MAN_SENSE_RAW'),
    'R84':('2','AUTO_SENSE','AUTO_SENSE_RAW'),
    'R85':('1','AUTO_SENSE','AUTO_SENSE_RAW'),
    'C84':('1','AUTO_SENSE','AUTO_SENSE_RAW'),
}
PLACEMENTS={'U37':{'x':54.0,'y':43.0,'rotation':90,'side':'B'},
            'C78':{'x':54.75,'y':38.9,'rotation':90,'side':'B'}}

def new_components():
    return [
        {'ref':'U37','value':'SN74LVC3G17DCUR','mpn':'SN74LVC3G17DCUR','kind':'ic',
         'footprint':'PumpRevE:SN74LVC3G17_DCU_TI','symbol_width':25.4,
         'description':'Three non-inverting Schmitt inputs; 5.5V-tolerant raw inputs and Ioff support. Outputs use U33 supply; STOP/MODE/NEXT polarity unchanged.',
         'datasheet':'https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf',
         'placement':copy.deepcopy(PLACEMENTS['U37']),
         'pins':[{'num':str(n),'name':name,'net':net,'type':kind} for n,name,net,kind in [
             (1,'1A','STOP_SENSE_RAW','input'),(2,'3Y','AUTO_SENSE','output'),
             (3,'2A','MAN_SENSE_RAW','input'),(4,'GND','GND','power_in'),
             (5,'2Y','MAN_SENSE','output'),(6,'3A','AUTO_SENSE_RAW','input'),
             (7,'1Y','STOP_SENSE','output'),(8,'VCC','+3V3','power_in')]]},
        {'ref':'C78','value':'100nF','mpn':'SPEC: 100nF X7R, 10%, 16V','kind':'capacitor',
         'footprint':'Capacitor_SMD:C_0603_1608Metric',
         'description':'Local U37 bypass; short direct connection between pins8 and4.',
         'datasheet':'','placement':copy.deepcopy(PLACEMENTS['C78']),
         'pins':[{'num':'1','name':'1','net':'+3V3','type':'passive'},
                 {'num':'2','name':'2','net':'GND','type':'passive'}]},
    ]

def apply_source(data):
    parts={c['ref']:c for s in data['sheets'] for c in s['components']}
    for ref,(number,old,new) in RAW_RENAMES.items():
        pin=next(p for p in parts[ref]['pins'] if str(p['num'])==number)
        if pin['net'] not in (old,new):
            raise ValueError('Unexpected original E11 pin/net: '+ref+'.'+number)
        pin['net']=new
    for ref in ['R80','R82','R84']:
        if parts[ref]['value'] not in ['22k','10k']:
            raise ValueError('Unexpected E11 input resistor '+ref)
        parts[ref].update(value='10k',mpn='SPEC: 10k 1%, 0.1W, 0603',
            description='Series input resistor for 10k/33k raw divider into U37 Schmitt buffer; not a direct U33 input.')
    sheets={s['id']:s for s in data['sheets']}
    if SHEET not in sheets:
        sheet={'id':SHEET,'title':TITLE,
               'notes':'U37 inputs accept the filtered 5V-derived levels; outputs share U33 3V3. GPIO polarity unchanged. Hardwired STOP/HH path is separate. Validate supply ramps and disturbance behavior.',
               'components':new_components()}
        data['sheets'].append(sheet)
    else:
        actual={c['ref']:c for c in sheets[SHEET]['components']}
        for c in new_components():
            prior=actual.get(c['ref'])
            if not prior or prior['pins']!=c['pins'] or prior['footprint']!=c['footprint']:
                raise ValueError('Conflicting existing E11 component: '+c['ref'])
            prior.update(c)
    return data

def update_properties(text,parts):
    changes=[]
    for start,end in expression_ranges(text):
        block=text[start:end]
        if not re.match(r'\(symbol\s',block):
            continue
        found=re.search(r'\(property "Reference" "([^"]+)"',block)
        if not found or found.group(1) not in ['R80','R82','R84']:
            continue
        c=parts[found.group(1)];updated=block
        for field,key in [('Value','value'),('MPN','mpn'),('Description','description')]:
            pattern=r'(\(property "'+field+r'" )"(?:\\.|[^"\\])*"'
            updated=re.sub(pattern,lambda m:m.group(1)+json.dumps(c[key]),updated)
        if updated!=block:changes.append((start,end,updated))
    changes.sort()
    if any(a[1]>b[0] for a,b in zip(changes,changes[1:])):
        raise ValueError('Overlapping property patches')
    for start,end,new in reversed(changes):text=text[:start]+new+text[end:]
    return text

def patch_sources(base):
    source=base/'design/main-rev-e.json';out=base/'hardware/main-rev-e'
    data=json.loads(source.read_text());apply_source(data)
    parts={c['ref']:c for s in data['sheets'] for c in s['components']}
    before={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in out.glob('*.kicad_sch')}
    source.write_text(json.dumps(data,indent=2)+'\n')
    # Rename only the specified RC pin labels, preserving all object identities.
    for file in out.glob('*.kicad_sch'):
        text=file.read_text();original=text
        for ref,(number,old,new) in RAW_RENAMES.items():
            index=next(i for i,p in enumerate(parts[ref]['pins']) if str(p['num'])==number)
            label_uid=cad.uid('label:'+ref+':'+str(index))
            matches=[(a,b) for a,b in expression_ranges(text)
                     if text[a:b].startswith('(global_label ') and f'(uuid "{label_uid}")' in text[a:b]]
            if not matches:continue
            if len(matches)!=1:raise ValueError('Duplicate pin label '+ref)
            a,b=matches[0];block=text[a:b]
            if not any(block.startswith('(global_label '+json.dumps(n)) for n in (old,new)):
                raise ValueError('Unexpected E11 native label '+ref)
            updated=block.replace('(global_label '+json.dumps(old),'(global_label '+json.dumps(new),1)
            text=text[:a]+updated+text[b:]
        text=update_properties(text,parts)
        if re.findall(r'\(uuid "([^"]+)"\)',text)!=re.findall(r'\(uuid "([^"]+)"\)',original):
            raise ValueError('Existing UUID changed '+file.name)
        if text!=original:file.write_text(text)
    # Generate a new page and its root-sheet entry without touching old sheets.
    with tempfile.TemporaryDirectory(prefix='e11-sheet-') as temporary:
        temp=Path(temporary);cad.write_schematics(data,temp,PROJECT)
        new_sheet=(temp/(SHEET+'.kicad_sch')).read_text()
        (out/(SHEET+'.kicad_sch')).write_text(new_sheet)
        root=out/(PROJECT+'.kicad_sch');text=root.read_text()
        sid=cad.uid(PROJECT+':sheet:'+SHEET)
        if f'(uuid "{sid}")' not in text:
            generated=(temp/(PROJECT+'.kicad_sch')).read_text()
            block=next(generated[a:b] for a,b in expression_ranges(generated)
                       if generated[a:b].startswith('(sheet ') and f'(uuid "{sid}")' in generated[a:b])
            index=text.index('(sheet_instances ')
            text=text[:index]+block+'\n'+text[index:];root.write_text(text)
    lib=out/'Pump.kicad_sym';text=update_properties(lib.read_text(),parts)
    for component in new_components():
        marker='(symbol '+json.dumps(component['ref'])+'\n'
        matches=[(a,b) for a,b in expression_ranges(text) if text[a:b].startswith(marker)]
        definition=cad.symbol_definition(component,False)
        if matches:
            if len(matches)!=1:raise ValueError('Duplicate new library definition')
            a,b=matches[0];text=text[:a]+definition+text[b:]
        else:
            i=text.rfind(')');text=text[:i]+definition+'\n'+text[i:]
    lib.write_text(text)
    cad.write_bom(data,out)
    pro=out/(PROJECT+'.kicad_pro');settings=json.loads(pro.read_text())
    patterns=settings['net_settings']['netclass_patterns']
    for net in ['STOP_SENSE_RAW','MAN_SENSE_RAW','AUTO_SENSE_RAW']:
        entry={'netclass':'SELV','pattern':net}
        if entry not in patterns:patterns.append(entry)
    pro.write_text(json.dumps(settings,indent=2)+'\n')
    after={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in out.glob('*.kicad_sch')}
    return {'scope':'Source/schematic/library/BOM/project only; no PCB write',
            'changed_or_added_sheets':[path for path,value in after.items() if before.get(path)!=value],
            'added_components':['U37','C78'],'raw_pin_changes':RAW_RENAMES,
            'input_resistors_10k':['R80','R82','R84'],
            'placements':PLACEMENTS,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source',action='store_true',required=True)
    args=parser.parse_args()
    print(json.dumps(patch_sources(args.root.resolve()),indent=2))
