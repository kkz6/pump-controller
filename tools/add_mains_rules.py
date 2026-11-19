from pathlib import Path
import json
b=Path(__file__).resolve().parents[1];pro=b/'hardware/pump-controller-rev-b.kicad_pro';d=json.load(open(pro))
high=['MAINS_L','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT']
classes=[('HV',2.0,high),('DIV198',1.8,['M_VDIV_0']),('DIV132',1.2,['M_VDIV_1']),('DIV66',.6,['M_VDIV_2'])]
for name,clr,nets in classes:
 d['net_settings']['classes'].append({'name':name,'clearance':clr,'track_width':.25,'via_diameter':.65,'via_drill':.3})
 for n in nets:d['net_settings']['netclass_patterns'].append({'netclass':name,'pattern':n})
pro.write_text(json.dumps(d,indent=2)+'\n')
rules='''(version 1)
(rule "Hazardous line and coil circuits basic spacing prototype"
  (condition "(A.hasNetclass('HV') && B.hasNetclass('LIVE')) || (B.hasNetclass('HV') && A.hasNetclass('LIVE'))")
  (constraint clearance (min 2mm)))
(rule "Upper divider node spacing prototype"
  (condition "(A.hasNetclass('DIV198') && B.hasNetclass('LIVE')) || (B.hasNetclass('DIV198') && A.hasNetclass('LIVE'))")
  (constraint clearance (min 1.8mm)))
(rule "Middle divider node spacing prototype"
  (condition "(A.hasNetclass('DIV132') && B.hasNetclass('LIVE')) || (B.hasNetclass('DIV132') && A.hasNetclass('LIVE'))")
  (constraint clearance (min 1.2mm)))
(rule "Lower divider node spacing prototype"
  (condition "(A.hasNetclass('DIV66') && B.hasNetclass('LIVE')) || (B.hasNetclass('DIV66') && A.hasNetclass('LIVE'))")
  (constraint clearance (min 0.6mm)))
(rule "Reinforced live to isolated control separation"
  (condition "(A.hasNetclass('LIVE') && B.hasNetclass('SELV')) || (A.hasNetclass('SELV') && B.hasNetclass('LIVE'))")
  (constraint clearance (min 8mm)))
'''
# Order high-voltage rules last among live-only rules so highest potential wins.
parts=rules.split('(rule ');rules=parts[0]+''.join('(rule '+parts[i] for i in [4,3,2,1,5])
exceptions="""(rule "First divider resistor differential voltage spacing"
  (condition "(A.NetName == 'L_PROTECTED' && B.NetName == 'M_VDIV_0') || (B.NetName == 'L_PROTECTED' && A.NetName == 'M_VDIV_0')")
  (constraint clearance (min 0.6mm)))
(rule "Adjacent divider resistor differential voltage spacing"
  (condition "(A.NetName == 'M_VDIV_0' && B.NetName == 'M_VDIV_1') || (B.NetName == 'M_VDIV_0' && A.NetName == 'M_VDIV_1') || (A.NetName == 'M_VDIV_1' && B.NetName == 'M_VDIV_2') || (B.NetName == 'M_VDIV_1' && A.NetName == 'M_VDIV_2')")
  (constraint clearance (min 0.6mm)))
(rule "Two divider segment differential voltage spacing"
  (condition "(A.NetName == 'M_VDIV_0' && B.NetName == 'M_VDIV_2') || (B.NetName == 'M_VDIV_0' && A.NetName == 'M_VDIV_2')")
  (constraint clearance (min 1.2mm)))
"""
pro.with_suffix('.kicad_dru').write_text(rules+exceptions)
