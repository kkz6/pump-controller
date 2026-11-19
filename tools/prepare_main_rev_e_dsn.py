#!/usr/bin/env python3
"""Apply explicit Rev E routing constraints to a KiCad micrometre DSN copy.

Usage: python3 tools/prepare_main_rev_e_dsn.py input.dsn output.dsn

Does not modify native CAD. Preserves placements, pin definitions, existing
wiring and keepouts; replaces routing net classes/rules with the documented
prototype domains and Robu-oriented geometry. Native KiCad DRC, source parity,
via-drill/SMT overlap and manufacturer review remain release requirements.

Primary parser references:
https://github.com/freerouting/freerouting/blob/master/src/main/java/app/freerouting/io/specctra/parser/Structure.java
https://github.com/freerouting/freerouting/blob/master/src/main/java/app/freerouting/io/specctra/parser/NetClass.java
https://github.com/freerouting/freerouting/blob/v2.5.0/src/main/java/app/freerouting/io/specctra/parser/Network.java
"""
from pathlib import Path
import argparse, hashlib, json, re

QUOTE_MARKER='__REV_E_DSN_LITERAL_QUOTE__'
HV={'MAINS_L','L_FUSED','CTRL_IN','CTRL_MID','CTRL_OUT'}
DIV={'M_VDIV_0':'REVE_DIV198','M_VDIV_1':'REVE_DIV132','M_VDIV_2':'REVE_DIV66'}
MATRIX={'wire_wire':200,'wire_smd':200,'wire_via':254,'wire_pin':330,
        'smd_smd':200,'smd_via':200,'smd_pin':200,'via_via':254,
        'via_pin':500,'pin_pin':500,'area_wire':200,'area_smd':200,
        'area_via':254,'area_pin':330,'area_area':200,'default_boundary':300}

def parse(text):
    # Specctra's string_quote statement contains a literal, unmatched quote.
    text=text.replace('(string_quote ")',f'(string_quote {QUOTE_MARKER})')
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text)
    stack=[]; root=None
    for token in tokens:
        if token=='(':
            current=[]
            if stack:stack[-1].append(current)
            elif root is not None:raise ValueError('Multiple DSN roots')
            else:root=current
            stack.append(current)
        elif token==')':
            if not stack:raise ValueError('Unbalanced closing parenthesis')
            stack.pop()
        else:
            if not stack:raise ValueError('Atom outside DSN root')
            stack[-1].append(token)
    if stack or root is None:raise ValueError('Unbalanced or empty DSN')
    return root

def scalar(token):
    return json.loads(token) if token.startswith('"') else token

def quote(value):return json.dumps(str(value),ensure_ascii=False)

def tag(node):return scalar(node[0]) if isinstance(node,list) and node else None

def child(node,name):
    matches=[item for item in node if tag(item)==name]
    if len(matches)!=1:raise ValueError(f'Expected one {name}, found {len(matches)}')
    return matches[0]

def render(node,depth=0):
    if not isinstance(node,list):return node
    if all(not isinstance(x,list)for x in node):return '('+' '.join(node)+')'
    chunks=[]; inline=[]
    for item in node:
        if isinstance(item,list):
            if inline:chunks.append(' '.join(inline));inline=[]
            chunks.append('\n'+'  '*(depth+1)+render(item,depth+1))
        else:inline.append(item)
    if inline:chunks.append(' '.join(inline))
    return '('+''.join(chunks)+'\n'+'  '*depth+')'

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def domain(name):
    if name in DIV:return DIV[name]
    if name=='L_PROTECTED':return 'REVE_LINE'
    if name in HV:return 'REVE_HV'
    if name=='MAINS_N' or name.startswith('M_') or name.startswith('unconnected-(U10-') or name=='unconnected-(U11-NIC-Pad16)':return 'REVE_LIVE'
    if name=='unconnected-(U11-NIC-Pad13)':return 'REVE_SELV'
    if name.startswith(('MAINS_','CTRL_','L_')):
        raise ValueError('Unclassified hazardous-net name: '+name)
    return 'REVE_SELV'

def clearance_rule(base,width):
    # Explicit item entries avoid the reduced smd_smd override in some exports.
    return ['rule',['width',str(width)],['clearance',str(base)]]+[
        ['clearance',str(max(base,value)),['type',item]]for item,value in MATRIX.items()]

def prepare(src,dst,signal_width_mm=.2,power_width_mm=.25,report=None):
    original=src.read_text();root=parse(original)
    if tag(root).lower()!='pcb':raise ValueError('Input is not a Specctra PCB DSN')
    if scalar(child(root,'unit')[1])!='um':raise ValueError('Only KiCad DSN unit um is supported')
    structure=child(root,'structure');library=child(root,'library');network=child(root,'network')
    if any(tag(x)=='layer_rule'for x in structure):
        raise ValueError('Input has per-layer routing overrides; review those explicitly before applying this helper')
    before={k:digest(child(root,k))for k in ['placement','wiring']}
    pins_before=digest([x for x in network if tag(x)=='net'])
    keepouts_before=digest([x for x in structure if tag(x)in['keepout','via_keepout','boundary','plane']])
    layers=[x[1]for x in structure if tag(x)=='layer']
    if list(map(scalar,layers))!=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']:
        raise ValueError('Expected the Rev E six-layer copper order')
    for entry in structure:
        if tag(entry)=='layer' and scalar(entry[1]) in ('In1.Cu','In4.Cu'):
            child(entry,'type')[1]='power'
    nets=[scalar(x[1])for x in network if tag(x)=='net']
    for required in ['MAINS_L','MAINS_N','M_GND','GND','L_PROTECTED']:
        if required not in nets:raise ValueError('Missing expected main-board net '+required)
    classes={}
    for net in nets:classes.setdefault(domain(net),[]).append(net)
    signal_width=round(signal_width_mm*1000);power_width=round(power_width_mm*1000)
    if signal_width<150 or power_width<200:raise ValueError('Requested track width is below Rev E routing assumptions')
    via_name='Via[0-5]_650:300_um';via_token=quote(via_name)
    # Preserve other control options while explicitly disabling via attachment to SMT pads.
    controls=[x for x in structure if tag(x)=='control']
    if len(controls)>1:raise ValueError('Multiple structure control scopes require manual review')
    control=controls[0]if controls else['control']
    control[:]=[x for x in control if tag(x)!='via_at_smd']+[['via_at_smd','off']]
    structure[:]=[x for x in structure if tag(x)not in['control','rule']]
    structure.extend([control,clearance_rule(200,signal_width)])
    via_scopes=[x for x in structure if tag(x)=='via']
    if len(via_scopes)>1:raise ValueError('Multiple via definitions require manual review')
    if via_scopes:
        if via_token not in via_scopes[0]:via_scopes[0].append(via_token)
    else:structure.append(['via',via_token])
    # Keep legacy padstacks so retained wiring remains representable, but use
    # only this through-via padstack for all newly routed nets.
    library[:]=[x for x in library if not(tag(x)=='padstack'and scalar(x[1])==via_name)]
    library.append(['padstack',via_token]+[['shape',['circle',layer,'650']]for layer in layers]+[['attach','off']])
    network[:]=[x for x in network if tag(x)not in['class','class_class']]
    for name,items in sorted(classes.items()):
        base=2000 if name in['REVE_HV','REVE_LINE'] else 200
        width=power_width if base==2000 else signal_width
        network.append(['class',quote(name)]+[quote(n)for n in sorted(items)]+[
            ['circuit',['use_via',via_token]],clearance_rule(base,width)])
    pairs=[]
    def pair(a,b,minimum):
        if a in classes and b in classes:
            # Freerouting v2.5.0 leaves item-specific classes unchanged for an
            # untyped class_class rule. Spell out every copper-item pair so
            # pads and vias receive the same domain separation as traces.
            pair_rule=['rule',['clearance',str(minimum)]]+[
                ['clearance',str(max(minimum,base)),['type',kind]]
                for kind,base in MATRIX.items() if kind!='default_boundary']
            network.append(['class_class',['classes',quote(a),quote(b)],pair_rule])
            pairs.append({'classes':[a,b],'clearance_mm':minimum/1000})
    live=['REVE_HV','REVE_LINE','REVE_LIVE','REVE_DIV198','REVE_DIV132','REVE_DIV66']
    for name in live:pair(name,'REVE_SELV',8000)
    for name in live:
        if name!='REVE_HV':pair('REVE_HV',name,2000)
    pair('REVE_LINE','REVE_LIVE',2000)
    pair('REVE_LINE','REVE_DIV198',600)
    pair('REVE_LINE','REVE_DIV132',2000)
    pair('REVE_LINE','REVE_DIV66',2000)
    for name,gap in [('REVE_DIV198',1800),('REVE_DIV132',1200),('REVE_DIV66',600)]:pair(name,'REVE_LIVE',gap)
    pair('REVE_DIV198','REVE_DIV132',600);pair('REVE_DIV132','REVE_DIV66',600);pair('REVE_DIV198','REVE_DIV66',1200)
    assert before=={k:digest(child(root,k))for k in before},'Placement or existing wiring changed'
    assert pins_before==digest([x for x in network if tag(x)=='net']),'Net/pin assignments changed'
    assert keepouts_before==digest([x for x in structure if tag(x)in['keepout','via_keepout','boundary','plane']]),'Keepout/boundary/plane changed'
    output=render(root).replace(QUOTE_MARKER,'"')+'\n'
    assert parse(output)==root,'DSN round trip failed'
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(output)
    record={'input':str(src),'output':str(dst),'input_sha256':hashlib.sha256(original.encode()).hexdigest(),'output_sha256':hashlib.sha256(output.encode()).hexdigest(),'units':'um','new_route_via_diameter_mm':.65,'new_route_drill_mm':.3,'via_at_smd':False,'signal_width_mm':signal_width_mm,'power_width_mm':power_width_mm,'default_clearance_mm':.2,'item_clearance_mm':{k:v/1000 for k,v in MATRIX.items()},'class_pairs':pairs,'net_domains':classes,'placements_preserved':True,'existing_wiring_preserved':True,'net_pin_assignments_preserved':True,'existing_keepouts_preserved':True,'class_pair_item_rules_explicit':True,'native_drc_required':True,'manufacturer_accepted':False}
    target=report or dst.with_suffix('.rules-report.json');target.write_text(json.dumps(record,indent=2)+'\n')
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--signal-width-mm',type=float,default=.2);parser.add_argument('--power-width-mm',type=float,default=.25);parser.add_argument('--report',type=Path);a=parser.parse_args()
    if a.input.resolve()==a.output.resolve():raise SystemExit('Input and output must differ; preserve the original routing input.')
    r=prepare(a.input,a.output,a.signal_width_mm,a.power_width_mm,a.report)
    print(json.dumps({k:r[k]for k in ['output','output_sha256','via_at_smd','new_route_via_diameter_mm','new_route_drill_mm','placements_preserved','existing_wiring_preserved']},indent=2))
if __name__=='__main__':main()
