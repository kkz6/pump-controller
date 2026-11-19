"""Source netlists for Rev B metering, controls and indicator panel."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
S=[]
def sheet(id,title,notes=''):
    s={'id':id,'title':title,'notes':notes,'components':[]}; S.append(s); return s
def add(s,ref,value,fp,pins,kind='ic',mpn='',desc='',url='',**kw):
    pp=[]
    for row in pins:
        n,name,net,*t=row
        pp.append(dict(num=str(n),name=name,net=net,type=t[0] if t else 'passive'))
    c=dict(ref=ref,value=value,footprint=fp,pins=pp,kind=kind,mpn=mpn,description=desc,datasheet=url,**kw)
    s['components'].append(c);return c
RFP='Resistor_SMD:R_0603_1608Metric'
CFP='Capacitor_SMD:C_0603_1608Metric'
def r(s,ref,v,a,b,fp=RFP,mpn='',desc='1%, 0.1W, 0603'):
    return add(s,ref,v,fp,[(1,'1',a),(2,'2',b)],'resistor',mpn or 'SPEC: '+v+' '+desc,desc)
def c(s,ref,v,a,b,fp=CFP,mpn='',desc='X7R, 10%, 16V'):
    return add(s,ref,v,fp,[(1,'1',a),(2,'2',b)],'capacitor',mpn or 'SPEC: '+v+' '+desc,desc)
def conn(s,ref,nets,value,pitch='3.81'):
    n=len(nets)
    fp=f'Connector_Phoenix_MC:PhoenixContact_MC_1,5_{n}-G-3.81_1x{n:02d}_P3.81mm_Horizontal'
    return add(s,ref,value,fp,[(i+1,net,net) for i,net in enumerate(nets)],'connector',f'Phoenix MC 1,5/{n}-G-3,81',value)

# All M_* nets, including M_GND, are LIVE. Only U11 crosses the isolation barrier.
s=sheet('meter_ic','Single-phase metering - LIVE DOMAIN','M_GND is bonded to neutral; it is NEVER sensor ground. 230 V nominal, 264 V maximum design input.')
url='https://www.analog.com/media/en/technical-documentation/data-sheets/ade7953.pdf'
pinmap=[(1,'ZX',None,'output'),(2,'RESET_N','M_RESET_N','input'),(3,'VINTD','M_VINTD','power_out'),(4,'DGND','M_GND','power_in'),
(5,'IAP','M_IAP','input'),(6,'IAN','M_IAN','input'),(7,'PULL_HIGH','M_3V3','input'),(8,'PULL_HIGH','M_3V3','input'),
(9,'IBP','M_GND','input'),(10,'IBN','M_GND','input'),(11,'VN','M_VN','input'),(12,'VP','M_VP','input'),(13,'REF','M_REF','power_out'),
(14,'PULL_LOW','M_GND','input'),(15,'VINTA','M_VINTA','power_out'),(16,'AGND','M_GND','power_in'),(17,'VDD','M_3V3','power_in'),
(18,'CLKIN','M_XIN','input'),(19,'CLKOUT','M_XOUT','output'),(20,'REVP',None,'output'),(21,'ZX_I',None,'output'),(22,'IRQ',None,'open_collector'),
(23,'CF1',None,'output'),(24,'CF2',None,'output'),(25,'SCLK','M_SCLK','input'),(26,'MISO','M_MISO','tri_state'),(27,'MOSI','M_MOSI','input'),(28,'CS_N','M_CS','input'),(29,'EP','M_GND','power_in')]
add(s,'U10','ADE7953ACPZ','Package_CSP:LFCSP-28-1EP_5x5mm_P0.5mm_EP3.14x3.14mm',pinmap,mpn='ADE7953ACPZ',desc='Single phase metering IC; poll registers through SPI at 1MHz',url=url)
for ref,net in [('C40','M_VINTD'),('C42','M_VINTA'),('C44','M_REF')]:
    c(s,ref,'4.7uF',net,'M_GND','Capacitor_SMD:C_0805_2012Metric')
    c(s,'C'+str(int(ref[1:])+1),'100nF',net,'M_GND')
c(s,'C46','10uF','M_3V3','M_GND','Capacitor_SMD:C_0805_2012Metric')
c(s,'C47','100nF','M_3V3','M_GND')
r(s,'R40','10k','M_3V3','M_RESET_N'); c(s,'C48','1uF','M_RESET_N','M_GND')
r(s,'R41','10k','M_3V3','M_CS')
add(s,'Y1','3.579545MHz / CL18pF','Crystal:Crystal_SMD_HC49-SD',[(1,'1','M_XIN'),(2,'2','M_XOUT')],'crystal','ABLS-3.579545MHZ-B2-T','18pF load; 27pF caps assume 4.5pF total stray; confirm oscillator start/accuracy','https://abracon.com/Resonators/ABLS.pdf')
c(s,'C49','27pF','M_XIN','M_GND',desc='C0G, 5%, 50V');c(s,'C50','27pF','M_XOUT','M_GND',desc='C0G, 5%, 50V')

s=sheet('meter_inputs','Meter voltage and current inputs - LIVE DOMAIN','External CT has a permanent burden at the CT. Do not route these nets beside probe or panel wiring.')
r(s,'R42','0R','MAINS_N','M_GND',desc='Neutral bond inside live domain only')
prev='L_PROTECTED'
for i in range(4):
    nxt=f'M_VDIV_{i}' if i<3 else 'M_VP'
    r(s,f'R{43+i}','249k',prev,nxt,'Resistor_SMD:R_1206_3216Metric','TNPW1206249KBEEA','0.1%, 25ppm/K, 200V working, 1206; 4 in series')
    prev=nxt
r(s,'R47','1k','M_VP','M_GND',mpn='RT0603BRD071KL',desc='0.1%, 25ppm/K, 0603 voltage-divider low leg')
c(s,'C51','33nF','M_VP','M_GND',desc='C0G, 5%, 50V')
r(s,'R48','1k','M_GND','M_VN');c(s,'C52','33nF','M_VN','M_GND',desc='C0G, 5%, 50V')
conn(s,'J10',['M_CT_HI','M_GND'],'CT secondary - mains-referenced')
r(s,'R49','1k','M_CT_HI','M_IAP');c(s,'C53','33nF','M_IAP','M_GND',desc='C0G, 5%, 50V')
r(s,'R50','1k','M_GND','M_IAN');c(s,'C54','33nF','M_IAN','M_GND',desc='C0G, 5%, 50V')
add(s,'D10','BAV99W','Package_TO_SOT_SMD:SOT-323_SC-70',[(1,'A1','M_CT_HI'),(2,'K2','M_CT_HI'),(3,'K1_A2','M_GND')],'ic','BAV99W,115','Antiparallel input limiting across CT secondary; not a substitute for the external burden','https://assets.nexperia.com/documents/data-sheet/BAV99W.pdf')
add(s,'CT1','AC1020 20A / 1000:1','',[(1,'S1','M_CT_HI'),(2,'S2','M_GND')],'transformer','AC1020','External to main PCB, insulated enclosure around one motor conductor; 20A nominal,60A maximum','https://talema.com/wp-content/uploads/datasheets/AC-1020.pdf',on_board=False)
add(s,'RB1','6.8R 0.1% 0.5W','',[(1,'1','M_CT_HI'),(2,'2','M_GND')],'resistor','SPEC: 6.8 ohm 0.1% metal film 0.5W','Permanently solder across CT secondary in insulated sensor assembly; stays attached when main-board connector is unplugged',on_board=False)

s=sheet('meter_isolation','Meter isolation - power and SPI','U11 is the only data/power bridge to the live meter. Select ABRNZ5, with 5 V converter input.')
g1={2,3,8,10,12,14}; gi={15,17,19};g2={21,26,27}
special={1:('VDD1','+3V3','power_in'),4:('VIA','METER_SCLK','input'),5:('VIB','METER_MOSI','input'),6:('VIC','METER_CS','input'),7:('VOD','METER_MISO','output'),9:('PDIS','GND','input'),11:('VDDP','+5V','power_in'),13:('NIC',None,'no_connect'),16:('NIC',None,'no_connect'),18:('VISO','M_ISO_RAW','power_out'),20:('VSEL','M_ISO_RETURN','input'),22:('VID','M_MISO','input'),23:('VOC','M_CS','output'),24:('VOB','M_MOSI','output'),25:('VOA','M_SCLK','output'),28:('VDD2','M_3V3','power_in')}
p=[]
for i in range(1,29):
    if i in g1: row=('GND1','GND','power_in')
    elif i in gi: row=('GNDISO','M_ISO_RETURN','power_in')
    elif i in g2: row=('GND2','M_GND','power_in')
    else: row=special[i]
    p.append((i,*row))
add(s,'U11','ADuM6421ABRNZ5','Pump:ADuM6421A_RN28',p,mpn='ADUM6421ABRNZ5',desc='Reinforced signal and isolated-power barrier; 3 forward,1 reverse channel; 8.3mm package creepage',url='https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf')
for ref,a,b in [('FB1','M_ISO_RAW','M_3V3'),('FB2','M_ISO_RETURN','M_GND')]:
    add(s,ref,'1.5k @100MHz','Inductor_SMD:L_0603_1608Metric',[(1,'1',a),(2,'2',b)],'inductor','BLM18HE152SN1D','Ferrite explicitly listed by ADI; keep converter loop isolated from meter ground plane')
c(s,'C55','10uF','+5V','GND','Capacitor_SMD:C_0805_2012Metric');c(s,'C56','100nF','+5V','GND')
c(s,'C57','100nF','+3V3','GND');c(s,'C58','10uF','M_ISO_RAW','M_ISO_RETURN','Capacitor_SMD:C_0805_2012Metric')
c(s,'C59','100nF','M_ISO_RAW','M_ISO_RETURN');c(s,'C60','100nF','M_3V3','M_GND')

s=sheet('relay_protection','Relay drivers and independent watchdog','Both contacts are in series in the existing coil circuit. Never connect motor current through this board.')
add(s,'U30','STWD100NYWY3F / 1.6s','Package_TO_SOT_SMD:SOT-23-5',[(1,'WDO_N','SAFE_CLEAR_N','open_collector'),(2,'GND','GND','power_in'),(3,'EN_N','GND','input'),(4,'WDI','HEARTBEAT','input'),(5,'VCC','+3V3','power_in')],mpn='STWD100NYWY3F',desc='1.6s nominal / 2.24s maximum watchdog; heartbeat generated only after successful control-loop checks',url='https://www.st.com/resource/en/datasheet/stwd100.pdf')
add(s,'U31','SN74LVC1G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',[(1,'CLK','ARM_CMD','input'),(2,'D','+3V3','input'),(3,'Q_N',None,'output'),(4,'GND','GND','power_in'),(5,'Q','ARM_Q','output'),(6,'CLR_N','SAFE_CLEAR_N','input'),(7,'PRE_N','+3V3','input'),(8,'VCC','+3V3','power_in')],mpn='SN74LVC1G74DCUR',desc='Fault/STOP clears arm latch. Only a fresh user re-arm clocks it high; heartbeat never clocks this latch',url='https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf')
add(s,'U32','STM1001TWX6F','Package_TO_SOT_SMD:SOT-23',[(1,'RESET_N','SAFE_CLEAR_N','open_collector'),(2,'VCC','+3V3','power_in'),(3,'GND','GND','power_in')],mpn='STM1001TWX6F',desc='3.08V nominal reset threshold,3.00-3.15V over -40..85C;140-280ms release delay. ST pin1=RESET,2=VCC,3=GND',url='https://www.st.com/resource/en/datasheet/stm1001.pdf')
for i in range(3):c(s,f'C{70+i}','100nF','+3V3','GND')
r(s,'R70','10k','+3V3','SAFE_CLEAR_N');r(s,'R71','100k','HEARTBEAT','GND');r(s,'R72','100k','PERMIT_D','GND');r(s,'R78','100k','ARM_CMD','GND')
add(s,'U34','SN74LVC1G08DBVR','Package_TO_SOT_SMD:SOT-23-5',[(1,'A','ARM_Q','input'),(2,'B','PERMIT_D','input'),(3,'GND','GND','power_in'),(4,'Y','PERMIT_Q','output'),(5,'VCC','+3V3','power_in')],mpn='SN74LVC1G08DBVR',desc='Hardware-armed AND software-healthy gating of K1',url='https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf')
add(s,'U35','SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5',[(1,'NC',None,'no_connect'),(2,'A','HH_SENSE','input'),(3,'GND','GND','power_in'),(4,'Y','INTERLOCK_OK','output'),(5,'VCC','+3V3','power_in')],mpn='SN74LVC1G17DBVR',desc='Schmitt detector of K1 coil positive rail; opens after STOP/OFF/high-high loop break',url='https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf')
c(s,'C75','100nF','+3V3','GND');c(s,'C76','100nF','+3V3','GND')
add(s,'D35','BAT54WS','Diode_SMD:D_SOD-323',[(1,'K','INTERLOCK_OK'),(2,'A','SAFE_CLEAR_N')],'diode','BAT54WS-7-F','Physical interlock low asynchronously clears arm latch; prevents restart on STOP release')
# Manual MCU reset also clears permission, but watchdog does not repeatedly reboot the MCU.
add(s,'D30','BAT54WS','Diode_SMD:D_SOD-323',[(1,'K','MCU_EN'),(2,'A','SAFE_CLEAR_N')],'diode','BAT54WS-7-F','MCU EN low pulls permission clear low; supervisor/WD do not feed a hard MCU reset loop')
for k,g,drain,plus,ca,cb in [(1,'PERMIT_Q','K1_LOW','K1_COIL_PLUS','CTRL_IN','CTRL_MID'),(2,'RUN_CMD','K2_LOW','+5V','CTRL_MID','CTRL_OUT')]:
    qref='Q'+str(29+k);rg='R'+str(72+k*2);rp='R'+str(73+k*2);gn='K'+str(k)+'_GATE'
    r(s,rg,'100R',g,gn);r(s,rp,'100k',gn,'GND')
    add(s,qref,'AO3400A','Package_TO_SOT_SMD:SOT-23',[(1,'G',gn,'input'),(2,'S','GND'),(3,'D',drain)],'mosfet','AO3400A','30V N-MOSFET; specified at 2.5V gate drive','https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf')
    add(s,'K'+str(k),'G5Q-1A4 DC5','Relay_THT:Relay_SPST_Omron-G5Q-1A',[(1,'COIL+',plus),(5,'COIL-',drain),(2,'COM',ca),(3,'NO',cb)],'relay','G5Q-1A4 DC5','5V 40mA coil; contactor coil only; verify actual inductive/inrush rating before installation','https://components.omron.com/sg-en/products/relays/G5Q')
    add(s,'D'+str(30+k),'1N4148W','Diode_SMD:D_SOD-123',[(1,'K',plus),(2,'A',drain)],'diode','1N4148W-7-F','Flyback directly across relay coil')
j30=conn(s,'J30',['CTRL_IN','CTRL_OUT'],'Coil control series contacts - mains')
j30['footprint']='Connector_Phoenix_MC_HighVoltage:PhoenixContact_MC_1,5_2-G-5.08_1x02_P5.08mm_Horizontal'
j30['mpn']='1836189';j30['description']='Phoenix MC1,5/2-G-5,08; 320V OVCIII/PD2; mating plug required'
conn(s,'J31',['MODE_COIL_5V','K1_COIL_PLUS'],'High-high NC float loop / fitted shorting link')

s=sheet('local_controls','Low-voltage physical controls and indicator interface','All J32 controls are isolated low voltage. Existing mains button wiring must be removed before reusing buttons here.')
conn(s,'J32',['+5V','STOP_RETURN','MAN_RETURN','AUTO_RETURN','START_N','RESET_N','GND'],'STOP + selector + START + RESET')
for idx,net in [(33,'MAN_RETURN'),(34,'AUTO_RETURN')]:
    add(s,f'D{idx}','SS14','Diode_SMD:D_SMA',[(1,'K','MODE_COIL_5V'),(2,'A',net)],'diode','SS14-13-F','OR of selector outputs; OFF or STOP removes K1 coil supply physically')
# MCP23017 port A drives lights, B reads contacts. 0x20 at 400 kHz.
p=[]
bnet=['START_FILTER','RESET_FILTER','STOP_SENSE','MAN_SENSE','AUTO_SENSE','INTERLOCK_OK','SPARE_B6','SPARE_B7']
for i,net in enumerate(bnet):p.append((i+1,'GPB'+str(i),net,'bidirectional'))
p += [(9,'VDD','+3V3','power_in'),(10,'VSS','GND','power_in'),(11,'NC',None,'no_connect'),(12,'SCL','I2C_SCL','input'),(13,'SDA','I2C_SDA','bidirectional'),(14,'NC',None,'no_connect'),(15,'A0','GND','input'),(16,'A1','GND','input'),(17,'A2','GND','input'),(18,'RESET_N','MCU_EN','input'),(19,'INTB',None,'open_collector'),(20,'INTA',None,'open_collector')]
for i in range(8):p.append((21+i,'GPA'+str(i),'LED_'+str(i+1),'bidirectional'))
add(s,'U33','MCP23017-E/SS','Package_SO:SSOP-28_5.3x10.2mm_P0.65mm',p,mpn='MCP23017-E/SS',desc='I2C0x20,400kHz. GPA outputs initially HIGH before direction change; GPB inputs only',url='https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf')
c(s,'C73','100nF','+3V3','GND');c(s,'C74','1uF','+3V3','GND')
r(s,'R92','100k','SPARE_B6','GND');r(s,'R93','100k','SPARE_B7','GND')
for n,raw,sense in [(80,'STOP_RETURN','STOP_SENSE'),(82,'MAN_RETURN','MAN_SENSE'),(84,'AUTO_RETURN','AUTO_SENSE'),(86,'K1_COIL_PLUS','HH_SENSE')]:
    r(s,'R'+str(n),'22k',raw,sense);r(s,'R'+str(n+1),'100k' if n==86 else '33k',sense,'GND');c(s,'C'+str(n),'10nF',sense,'GND')
for n,raw,filt in [(88,'START_N','START_FILTER'),(90,'RESET_N','RESET_FILTER')]:
    r(s,'R'+str(n),'1k',raw,filt);r(s,'R'+str(n+1),'10k','+3V3',filt);c(s,'C'+str(n),'100nF',filt,'GND')
add(s,'J33','LED panel harness','Connector_JST:JST_GH_BM10B-GHS-TBT_1x10-1MP_P1.25mm_Vertical',[(1,'3V3','+3V3'),(2,'GND','GND'),('MP','Mount','GND')]+[(i+3,'LED'+str(i+1),'LED_'+str(i+1)) for i in range(8)],'connector','BM10B-GHS-TBT(LF)(SN)','Keyed 10-wire 1:1 harness to indicator PCB')

add(s,'J34','EXPANSION 3V3 I2C + 2 GPIO','Connector_PinHeader_1.27mm:PinHeader_2x03_P1.27mm_Vertical_SMD',[(1,'3V3_25mA','+3V3'),(2,'GND','GND'),(3,'SDA','I2C_SDA'),(4,'SCL','I2C_SCL'),(5,'EXT_IO1','SPARE_B6'),(6,'EXT_IO2','SPARE_B7')],'connector','SPEC: 2x3 1.27mm vertical SMD header; match KiCad land pattern','Internal short-cable expansion only;3.3V logic,25mA maximum allocated;not hot-pluggable;MCP GPIO defaults input with100k pulldown;reserve I2C0x20 and0x48')

# Indicator is a separate PCB and has its own project, so connector duplicates stay off main board.
panel={'title':'Pump starter cover indicator panel','board':{'width':60,'height':20,'layers':2},'sheets':[]}
pS=sheet('panel','Separate 60 x 20 mm LED board','This sheet is generated as a separate PCB; do not merge its copper into the mains board.')
S.pop();panel['sheets']=[pS]
add(pS,'J1','To main J33','Connector_JST:JST_GH_BM10B-GHS-TBT_1x10-1MP_P1.25mm_Vertical',[(1,'3V3','+3V3'),(2,'GND','GND'),('MP','Mount','GND')]+[(i+3,'LED'+str(i+1),'LED_'+str(i+1)) for i in range(8)],'connector','BM10B-GHS-TBT(LF)(SN)')
names=['LOW','L1','L2','L3','FULL','RUN','AUTO','FAULT']
for i,name in enumerate(names,1):
    r(pS,f'R{i}','680R','+3V3',f'ANODE_{i}')
    add(pS,f'D{i}',name,'LED_SMD:LED_0603_1608Metric',[(1,'K',f'LED_{i}'),(2,'A',f'ANODE_{i}')],'led','LTST-C190KGKT' if i<8 else 'LTST-C190KRKT','0603 green (fault red), approx 1-2mA; choose lens/light-pipe with adequate visibility')

for s in S:
    for comp in s['components']:
        for pin in comp['pins']:
            if pin.get('net')=='M_ISO_RETURN':pin['net']='M_ISO_GND'
BASE.joinpath('core.json').write_text(json.dumps({'sheets':S},indent=2))
BASE.joinpath('panel.json').write_text(json.dumps(panel,indent=2))
print('Core',sum(len(s['components']) for s in S),'components; panel',len(pS['components']))
