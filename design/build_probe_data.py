from pathlib import Path
import json
out=Path(__file__).parent
cs=[]
def add(ref,value,mpn,description,datasheet,footprint,kind,pins):
    cs.append(dict(ref=ref,value=value,mpn=mpn,description=description,datasheet=datasheet,footprint=footprint,kind=kind,pins=[dict(num=str(p[0]),name=p[1],net=p[2],type=p[3] if len(p)>3 else 'passive') for p in pins]))
def r(ref,value,a,b,mpn=None,size='0603',desc='1%, >=0.1 W'):
    add(ref,value,mpn or 'SPEC: '+value+' '+desc+' '+size,desc,'https://www.vishay.com/docs/20035/dcrcwe3.pdf','Resistor_SMD:R_'+size+'_1608Metric' if size=='0603' else 'Resistor_SMD:R_1206_3216Metric','resistor',[(1,'1',a),(2,'2',b)])
def c(ref,value,a,b,block=False,desc=None):
    add(ref,value,'C2012X7R1H105K125AB' if block else 'SPEC: '+value+' '+(desc or 'X7R 16V 10%'),desc or ('1uF 50V X7R 10%; DC block, retain >=0.7uF at operating bias/temp' if block else 'X7R 16V 10%'), 'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012X7R1H105K125AB' if block else '', 'Capacitor_SMD:C_0805_2012Metric' if block else 'Capacitor_SMD:C_0603_1608Metric','capacitor',[(1,'1',a),(2,'2',b)])
def tvs(ref,net):
    add(ref,'PESD5V0S1BA','PESD5V0S1BA,115','Bidirectional low-leakage 5V ESD diode; primary field clamp','https://assets.nexperia.com/documents/data-sheet/PESD5V0S1BA.pdf','Diode_SMD:D_SOD-323','diode',[(1,'K1',net),(2,'K2','GND')])
def clamp(ref,net,part='BAS70-04'):
    add(ref,part,part+',215','Dual series Schottky rail clamp: pin1 ground, pin2 rail, pin3 signal','https://assets.nexperia.com/documents/data-sheet/'+part+'.pdf','Package_TO_SOT_SMD:SOT-23','diode',[(1,'A1','GND'),(2,'K2','+3V3'),(3,'K1_A2',net)])
add('U20','TLV9004','TLV9004IPWR','Quad RRIO op-amp; reference, two excitation drivers, mux buffer','https://www.ti.com/lit/ds/symlink/tlv9004.pdf','Package_SO:TSSOP-14_4.4x5mm_P0.65mm','ic',[(1,'OUT1','PROBE_BIAS_RAW','output'),(2,'IN1-','PROBE_BIAS_RAW','input'),(3,'IN1+','PROBE_BIAS_DIV','input'),(4,'V+','+3V3','power_in'),(5,'IN2+','PROBE_TX_SET','input'),(6,'IN2-','PROBE_TX_TANK','input'),(7,'OUT2','PROBE_TX_TANK','output'),(8,'OUT3','PROBE_MUX_BUF','output'),(9,'IN3-','PROBE_MUX_BUF','input'),(10,'IN3+','PROBE_MUX_OUT','input'),(11,'V-','GND','power_in'),(12,'IN4+','PROBE_TX_SET','input'),(13,'IN4-','PROBE_TX_INLET','input'),(14,'OUT4','PROBE_TX_INLET','output')])
add('U21','TMUX1208','TMUX1208PWR','8:1 analog multiplexer; EN tied high, firmware reads only valid fresh samples','https://www.ti.com/lit/ds/symlink/tmux1208.pdf','Package_SO:TSSOP-16_4.4x5mm_P0.65mm','ic',[(1,'A0','MUX_A0','input'),(2,'EN','+3V3','input'),(3,'NC',None,'no_connect'),(4,'S1','PROBE_L1_ADC','bidirectional'),(5,'S2','PROBE_L2_ADC','bidirectional'),(6,'S3','PROBE_L3_ADC','bidirectional'),(7,'S4','PROBE_L4_ADC','bidirectional'),(8,'D','PROBE_MUX_OUT','bidirectional'),(9,'S8','PROBE_TX_INLET','bidirectional'),(10,'S7','PROBE_TX_TANK','bidirectional'),(11,'S6','PROBE_BIAS','bidirectional'),(12,'S5','PROBE_INLET_ADC','bidirectional'),(13,'VDD','+3V3','power_in'),(14,'GND','GND','power_in'),(15,'A2','MUX_A2','input'),(16,'A1','MUX_A1','input')])
add('U22','ADS1115','ADS1115IDGSR','16-bit ADC at 860 SPS, differential AIN0-AIN1, +/-2.048V range; I2C address 0x48','https://www.ti.com/lit/ds/symlink/ads1115.pdf','Package_SO:TSSOP-10_3x3mm_P0.5mm','ic',[(1,'ADDR','GND','input'),(2,'ALERT_RDY','PROBE_ADC_RDY','open_collector'),(3,'GND','GND','power_in'),(4,'AIN0','PROBE_ADC_SIGNAL','input'),(5,'AIN1','PROBE_ADC_BIAS','input'),(6,'AIN2','PROBE_ADC_TX','input'),(7,'AIN3','PROBE_ADC_BIAS2','input'),(8,'VDD','+3V3','power_in'),(9,'SDA','I2C_SDA','bidirectional'),(10,'SCL','I2C_SCL','input')])
r('R100','10k','+3V3','PROBE_BIAS_DIV',desc='0.1%, >=0.1 W');r('R101','10k','PROBE_BIAS_DIV','GND',desc='0.1%, >=0.1 W')
r('R102','47','PROBE_BIAS_RAW','PROBE_BIAS')
r('R103','27k','PROBE_EXC','PROBE_TX_SET');r('R104','43k','PROBE_BIAS','PROBE_TX_SET');r('R105','100k','PROBE_EXC','GND')
for i in range(3):r('R'+str(106+i),'100k','MUX_A'+str(i),'GND')
r('R109','10k','PROBE_ADC_RDY','+3V3')
for i,(src,dst) in enumerate([('PROBE_MUX_BUF','PROBE_ADC_SIGNAL'),('PROBE_BIAS','PROBE_ADC_BIAS'),('PROBE_TX_TANK','PROBE_ADC_TX'),('PROBE_BIAS','PROBE_ADC_BIAS2')]):
    r('R'+str(110+i),'100',src,dst);c('C'+str(110+i),'10nF',dst,'GND')
r('R114','1M','PROBE_MUX_OUT','PROBE_BIAS')
c('C100','100nF','PROBE_BIAS_DIV','GND');c('C101','1uF','PROBE_BIAS','GND')
for i in range(102,105):c('C'+str(i),'100nF','+3V3','GND')
c('C105','4.7uF','+3V3','GND')
for j,(bank,label) in enumerate([('TANK','TCOM'),('INLET','ICOM')]):
    rr=115+3*j
    r('R'+str(rr),'2.2k','PROBE_TX_'+bank,'PROBE_'+label+'_DRIVE')
    clamp('D'+str(102+j),'PROBE_'+label+'_DRIVE','BAT54S')
    c('C'+str(106+j),'1uF','PROBE_'+label+'_DRIVE','PROBE_'+label+'_CLAMP',True)
    c('C'+str(108+j),'1uF','PROBE_'+label+'_DRIVE','PROBE_'+label+'_CLAMP',True)
    tvs('D'+str(100+j),'PROBE_'+label+'_CLAMP')
    r('R'+str(rr+1),'4.99k','PROBE_'+label+'_CLAMP','PROBE_'+label+'_MID','CRCW12064K99FKEA','1206','1%, 0.25W; surge qualification required')
    r('R'+str(rr+2),'4.99k','PROBE_'+label+'_MID','PROBE_'+label,'CRCW12064K99FKEA','1206','1%, 0.25W; surge qualification required')
for i,name in enumerate(['L1','L2','L3','L4','INLET']):
    stem='PROBE_'+name;rr=130+10*i
    r('R'+str(rr),'10k',stem,stem+'_MID','CRCW120610K0FKEA','1206','1%, 0.25W; surge qualification required')
    r('R'+str(rr+1),'10k',stem+'_MID',stem+'_CLAMP','CRCW120610K0FKEA','1206','1%, 0.25W; surge qualification required')
    tvs('D'+str(110+2*i),stem+'_CLAMP')
    c('C'+str(120+2*i),'1uF',stem+'_CLAMP',stem+'_SENSE',True)
    r('R'+str(rr+2),'47k',stem+'_SENSE','PROBE_BIAS')
    r('R'+str(rr+3),'22k',stem+'_SENSE',stem+'_ADC')
    clamp('D'+str(111+2*i),stem+'_ADC')
    c('C'+str(121+2*i),'1nF',stem+'_ADC','PROBE_BIAS',desc='C0G 50V 5%')
add('J20','TANK PROBES','1803303','Phoenix MC 1,5/5-G-3,81 header; mating screw plug 1803604, verify fit','https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-5-g-381-1803303','Connector_Phoenix_MC:PhoenixContact_MC_1,5_5-G-3.81_1x05_P3.81mm_Horizontal','connector',[(1,'COM','PROBE_TCOM'),(2,'L1','PROBE_L1'),(3,'L2','PROBE_L2'),(4,'L3','PROBE_L3'),(5,'L4','PROBE_L4')])
add('J21','INLET PROBES','1803277','Phoenix MC 1,5/2-G-3,81 header; mating screw plug 1803578, verify fit','https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-2-g-381-1803277','Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal','connector',[(1,'INLET','PROBE_INLET'),(2,'INLET_COM','PROBE_ICOM')])
data=dict(sheets=[dict(id='probes',title='AC conductive probe interface - prototype Rev B',components=cs)],notes=['All GND/+3V3 are isolated controller domain, never mains neutral.','Common electrodes use separate AC-coupled drivers. No direct field electrode ground connection.','I2C bus needs shared pullups, not included on this sheet.','Pin NC on U21 intentionally unconnected; net=null.','Passives marked SPEC are value/package specifications, not procurement-approved MPNs.','See probe-front-end.txt and probe-calculation.txt for timing, limits and required verification.'])
out.joinpath('probe-front-end.json').write_text(json.dumps(data,indent=2)+'\n')
print(len(cs),'components written')
