import json,csv,copy
from pathlib import Path
P=Path(__file__).resolve().parent
sheets=[]
for name in ['power-mcu.json','core.json','probe-front-end.json']:
    d=json.loads((P/name).read_text())
    for s in d['sheets']:
        parts=s['components']
        # Keep no more than 24 components per A3 sheet; connectivity uses global labels.
        for off in range(0,len(parts),24):
            out=copy.deepcopy(s);out['components']=parts[off:off+24]
            if len(parts)>24:
                n=off//24+1;out['id']=s['id']+'_'+str(n);out['title']=s['title']+' / '+str(n)
            sheets.append(out)
for s in sheets:
    for c in s['components']:
        if c['ref'] in ['K1','K2']:c['footprint']='Pump:Relay_G5Q_8mm'
        if c['ref']=='R42':c['mpn']='RC0603JR-070RL'
# Power flags document externally supplied AC and passive-filter outputs.
flags=[]
for i,net in enumerate(['L_PROTECTED','MAINS_N','M_GND','M_3V3','M_ISO_GND','+3V3']):
    flags.append({'ref':'#FLG'+str(i+1),'value':'PWR_FLAG '+net,'kind':'power_flag','footprint':'','on_board':False,'in_bom':False,'pins':[{'num':'1','name':'pwr','net':net,'type':'power_out'}]})
sheets.append({'id':'power_flags','title':'Power-source declarations for electrical-rule checking','components':flags})
d={'project':'pump-controller-rev-b','revision':'C','title':'Rev C - 1 HP pump controller','board':{'width':90,'height':70,'layers':4},'sheets':sheets}
refs=[c['ref'] for s in sheets for c in s['components']]
assert len(refs)==len(set(refs))
(P/'circuit.json').write_text(json.dumps(d,indent=2))
with (P/'parts-complete.csv').open('w',newline='') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['Reference','Value','MPN or procurement specification','Description','Footprint','Board','Datasheet'])
    for s in sheets:
        for c in s['components']:
            if c['ref'].startswith('#'):continue
            w.writerow([c['ref'],c.get('value',''),c.get('mpn',''),c.get('description',''),c.get('footprint',''),'main' if c.get('on_board',True) else 'external',c.get('datasheet','')])
    for ref,value,spec in [('S_STOP','SPST-NC STOP','Reuse existing STOP actuator with verified isolated NC auxiliary contact;5V /0.1A capability; preserve original starter safety contacts'),('S_MODE','SPST-NO MODE','One external momentary button; low-level contacts suitable for5V /0.1mA; toggles MAN/AUTO only unarmed'),('S_START','SPST-NO START','Reuse existing START actuator with verified isolated NO auxiliary contact;3.3V /0.3mA; preserve any capacitor-start contacts'),('S_HH','Optional independent high-high float','NC healthy; opens on high-high or wire break; suitable5V /40mA; fitted local shorting link if absent'),('ANT1','External 2.4GHz antenna','50ohm antenna with mating connector for MINI-1U; verify module antenna connector type'),('HARNESS1','4-wire OLED cable','Board JST GH1.25mm 4ways to module PH2.0mm 4ways; J33->OLED numeric map1->4,2->3,3->2,4->1; short internal harness,3.3V only')]:
        w.writerow([ref,value,spec,'External installation item','','external',''])
print(len(sheets),'sheets;',sum(c.get('on_board',True) for s in sheets for c in s['components']),'main PCB parts')
