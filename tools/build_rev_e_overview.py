#!/usr/bin/env python3
"""Create the Rev E connection overview from the current connector definitions."""
from pathlib import Path
from html import escape
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/rev-e';OUT.mkdir(parents=True,exist_ok=True)
def components(path):return {c['ref']:c for s in json.loads(path.read_text())['sheets']for c in s['components']}
panel=components(ROOT/'design/panel-rev-e.json');main=components(ROOT/'design/main-rev-e.json')
def pins(c):return {int(p['num']):p['net']for p in c['pins']if p['num'].isdigit()}
expected={1:'+5V',2:'STOP_RETURN',3:'MAN_RETURN',4:'AUTO_RETURN',5:'START_N',6:'RESET_N',7:'GND',8:'+3V3',9:'I2C_SDA',10:'I2C_SCL',11:'KEY_MAN_N',12:'KEY_AUTO_N'}
assert pins(panel['J1'])==expected
assert pins(main['J32'])=={**expected,11:'SPARE_B6',12:'SPARE_B7'}
assert pins(panel['J7'])=={1:'I2C_SCL',2:'I2C_SDA',3:'GND',4:'+3V3'}
assert pins(main['J1'])=={1:'MAINS_L',2:'MAINS_N'}
assert pins(main['J30'])=={1:'CTRL_IN',2:'CTRL_OUT'}
assert '1727010' in main['J10']['mpn']
N='#153548';M='#506975';T='#007f7a';R='#ac4438';G='#c38a2d'
a=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1530" viewBox="0 0 1800 1530"><title>Rev E pump controller and DOL starter connections</title><desc>Connection overview: existing DOL starter with unchanged motor and capacitor wiring, four-mount100x80mm main board, separate60x45mm low-voltage panel, direct one-to-one GH12 cable and PH4 OLED. Functional coil chain preserves existing STOP and overload. Drawing is not a terminal identification from a photograph.</desc><defs><pattern id="barrier" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="10" height="10" fill="#fff3d7"/><rect width="3" height="10" fill="#e4c383"/></pattern></defs><style>text{{font-family:Arial,Helvetica,sans-serif;fill:{N};font-size:21px}}.title{{font-size:32px;font-weight:700}}.head{{font-size:26px;font-weight:700}}.label{{font-size:20px;font-weight:700}}.small{{font-size:18px;fill:{M}}}.tiny{{font-size:16px;fill:{M}}}.mono{{font-family:Menlo,Consolas,monospace;font-size:18px}}</style><rect width="1800" height="1530" fill="#f3f6f7"/>''']
def rect(x,y,w,h,fill,stroke='none',r=0,sw=1):a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def text(x,y,s,cls='',anchor='start',color=None):a.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"'+(f' style="fill:{color}"'if color else'')+f'>{escape(s)}</text>')
def line(x,y,X,Y,color=T,w=3,dash=None):a.append(f'<line x1="{x}" y1="{y}" x2="{X}" y2="{Y}" stroke="{color}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"'if dash else'')+'/>')
def path(d,color=T,w=3,dash=None):a.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'+(f' stroke-dasharray="{dash}"'if dash else'')+'/>')
def circle(x,y,r,fill,stroke='none',sw=1):a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def box(x,y,w,h,s,fill='#e6eff1',cls='label',color=None):rect(x,y,w,h,fill,'#a9bcc4',6);text(x+w/2,y+h/2+7,s,cls,'middle',color)
def card(x,y,w,h):rect(x,y,w,h,'white','#ced9df',14)
text(40,57,'One controller, one plug-in control panel','title')
text(40,91,'REV E • 1 HP single-phase pump • Connection overview • Engineering prototype','small')
text(1755,59,'No motor current through either PCB','label','end',R)
text(1755,91,'Diagram, not photo-derived terminal identification','small','end')
# Existing starter illustration.
card(40,130,350,700);text(64,172,'Existing DOL starter','head');text(64,203,'Simplified view of retained parts','small')
rect(64,225,300,410,'#e6ebee','#98aab4',10,2)
box(85,246,90,66,'MCB','#f7f7f4');text(225,270,'Motor supply','small','middle');text(225,295,'stays here','small','middle')
for x,w in[(95,75),(200,95)]:rect(x,340,w,110,'#d5d9d4','#87958e',15,2)
text(209,477,'Start / run capacitors','small','middle')
box(112,500,205,89,'CONTACTOR','#d1d9df');text(214,615,'Existing overload retained','tiny','middle')
for x,label,col in[(134,'START','#177653'),(268,'STOP',R)]:
 circle(x,686,25,col,'#c6d1d6',5);text(x,731,label,'label','middle')
text(64,774,'Reuse actuators with separate','small');text(64,800,'isolated auxiliary contacts.','small')
# Main board envelope, approximate blocks, actual edge allocation.
text(442,172,'Main PCB • 100 × 80 mm','head');text(442,202,'Four insulating mounts • guarded live section','small')
bx,by=450,225;rect(bx,by,600,480,'#e1f1e9','#638d79',8,2);rect(bx+1,by+1,221,478,'#f7e7e2');rect(bx+222,by+1,48,478,'url(#barrier)')
for x,y in[(474,249),(1026,249),(474,681),(1026,681)]:circle(x,y,10,'white','#6e9482',2)
text(558,274,'LIVE DOMAIN','label','middle',R);text(875,274,'ISOLATED CONTROL','label','middle',T)
box(485,300,150,82,'AC INPUT','#eed9d2');box(485,409,150,73,'COIL RELAYS','#e6ddd4');box(485,515,150,96,'METER + CT','#eed9d2')
parts=a;parts.append('<text x="701" y="490" class="tiny" text-anchor="middle" transform="rotate(-90 701 490)">8 mm copper isolation corridor</text>')
box(752,307,240,82,'ISOLATED AC/DC','#d6e8e0');box(752,417,240,86,'ESP32-C6 + I/O','#c9e5d6');text(871,548,'Local pump protection','small','middle');text(871,579,'independent of the network','small','middle')
# Live connections and main edge connector tags.
for y,label in[(325,'J1  L / N'),(445,'J30  COIL')]:
 rect(430,y-18,40,36,'#d8b3a9',R,3);line(364,y,430,y,R,4);text(407,y-29,label,'tiny','middle',R)
box(1013,450,66,44,'J32','#d5eae6','label',T)
# Direct GH12 cable, no obsolete three-header fanout.
path('M1079 472 H1120 V209 H1650 V290 H1450 V307',T,10);path('M1079 472 H1120 V209 H1650 V290 H1450 V307','#63b9ad',4)
text(1260,163,'DIRECT 12-WAY CABLE','label','middle',T);text(1260,189,'Main J32.n → panel J1.n','small','middle')
# Main sensor groups, cables are distinct.
for x,label,sub,col in[(608,'J10 CT','Fixed lead',R),(739,'J31 HH','NC float',T),(858,'J20 TANK','COM + 4',T),(977,'J21 INLET','SENSE + COM',T)]:
 box(x-51,669,102,36,label,'#f7faf9','tiny',col);line(x,705,x,746,col,3);box(x-57,748,114,54,sub,'#f7faf9','tiny',col)
text(450,851,'Fixed LIVE CT lead; CT surrounds ONE motor supply conductor.','small',color=R)
# Panel shape follows real button and mounting positions.
text(1207,240,'Control panel • 60 × 45 mm','head');text(1207,272,'Only isolated 3.3 V / 5 V circuits','small')
px,py=1270,325;rect(px,py,360,270,'#dff2e7','#608e77',8,2)
for x,y in[(1288,343),(1612,343),(1288,577),(1612,577)]:circle(x,y,7,'white','#6e9482',2)
box(1395,307,110,36,'J1 HOST','#d5eae6','tiny',T)
# OLED envelope and display mock contents, not an assembled photo.
rect(1342,349,216,75,'#173f45','#426d6c',4);rect(1353,358,194,46,'#0b242f',r=2);text(1361,378,'AUTO  READY','tiny',color='#80e8d8');text(1361,398,'LEVEL 3/4  230V','tiny',color='#80e8d8');text(1450,419,'0.91-inch OLED','tiny','middle','#d3e9df')
box(1604,433,61,35,'J7','#e7f3ed','tiny',T);path('M1665 450 H1690 V383 H1558',T,3);text(1701,416,'PH4','tiny');text(1701,440,'plug-in','tiny')
box(1234,435,61,35,'J8','#e7f3ed','tiny',T);line(1234,453,1187,453,T,3);circle(1168,453,18,'#e3e9ed','#8299a6',2);line(1168,438,1168,468,M,3);text(1168,497,'Optional key','tiny','middle');text(1168,521,'MAN / AUTO','tiny','middle')
for x,label,col in[(1315,'START','#177653'),(1390,'STOP',R),(1477,'MODE','#247b9d'),(1540,'SET','#627c88'),(1594,'NEXT','#627c88')]:
 circle(x,505,12,col,'white',2);text(x,541,label,'tiny','middle')
for x,n in[(1330,2),(1390,3),(1450,4),(1510,5),(1570,6)]:box(x-21,571,42,28,'J'+str(n),'#f2f8f5','tiny')
text(1450,630,'Connectors face outward on the rear.','tiny','middle')
card(1197,655,560,201);text(1220,691,'Optional external controls','label');text(1220,724,'J2 START   J3 NC STOP   J4 MODE','small');text(1220,754,'J5 SET       J6 NEXT','small');text(1220,789,'NO contacts parallel the matching local keys.','small');text(1220,819,'NC STOP is in series; see loop below.','small')
# Functional coil chain, deliberately not generic start-capacitor wiring.
card(40,890,1717,234);text(65,930,'DOL coil circuit: retain STOP and overload in series','head')
chain=[(65,180,'Verified coil supply'),(295,190,'Existing STOP NC'),(535,180,'Overload NC'),(765,405,'J30.1 → K1 NO → K2 NO → J30.2'),(1220,200,'Contactor coil A1'),(1470,260,'A2 / verified return')]
for i,(x,w,label)in enumerate(chain):
 box(x,963,w,48,label,'#fff1eb','small',R)
 if i<len(chain)-1:line(x+w,987,chain[i+1][0],987,R,4)
text(65,1052,'Functional series path only: integrate within the verified starter start/hold circuit. The PCB switches coil current only.','small')
text(65,1085,'Retain motor/capacitor wiring. Confirm coil voltage and the existing automatic start-capacitor sequence before replacing the old controller.','small',color=R)
# Independent low-voltage STOP chain.
card(40,1154,840,326);text(65,1194,'Panel STOP loop: either STOP removes permission','label')
text(67,1250,'+5V','mono');line(120,1243,160,1243,R,3);box(160,1219,210,48,'SW1 local NC STOP','#fff1eb','small',R);line(370,1243,412,1243,R,3);box(412,1219,210,48,'J3 external NC STOP','#fff1eb','small',R);line(622,1243,660,1243,R,3);text(675,1238,'STOP_RETURN','mono');text(675,1263,'to main J32.2','tiny')
path('M400 1243 V1306 H636 V1243',G,3,'6 4');text(518,1335,'JP1 only when external STOP is absent','small','middle',G)
text(65,1380,'Existing START auxiliary NO → panel J2.','small');text(65,1410,'Existing STOP auxiliary NC → panel J3; remove JP1.','small');text(65,1442,'Use separate isolated contacts; never feed mains into the panel.','small',color=R)
# Compact numeric cable map and OLED pin order.
card(910,1154,847,326);text(935,1194,'J32 → J1: all 12 cavities wired one-to-one','label');text(935,1226,'Factory-crimped GH1.25 cable • short internal harness','small')
labels=['1 +5V','2 STOP_RETURN','3 MODE','4 NEXT','5 START_N','6 SET / RESET_N','7 GND','8 +3V3','9 SDA','10 SCL','11 KEY_MAN_N','12 KEY_AUTO_N']
for i,s in enumerate(labels):text(945+(i//6)*400,1261+(i%6)*27,s,'mono')
text(935,1444,'OLED J7 → module: 1 SCL · 2 SDA · 3 GND · 4 +3V3','small')
text(40,1511,'Illustrated blocks are not to scale. Numeric pin maps come from the Rev E CAD sources; final starter terminals, insulation and mechanical fit still require verification.','small')
a.append('</svg>');target=OUT/'connection-overview.svg';target.write_text('\n'.join(a));print(target)
