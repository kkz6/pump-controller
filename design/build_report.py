"""Build the review pack from the circuit, BOM and native KiCad exports."""
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
from pypdf import PdfReader, PdfWriter

P = Path(__file__).resolve().parents[1]
OUT = P / 'output/pdf'
TMP = P / 'tmp/pdfs'
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
INK = colors.HexColor('#142C3B')
TEAL = colors.HexColor('#137C84')
PALE = colors.HexColor('#EDF5F5')
GRAY = colors.HexColor('#52616B')
ORANGE = colors.HexColor('#B35B15')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Title2', fontName='Helvetica-Bold', fontSize=26, leading=29, textColor=INK, spaceAfter=14))
styles.add(ParagraphStyle(name='H2x', fontName='Helvetica-Bold', fontSize=14, leading=17, textColor=TEAL, spaceBefore=13, spaceAfter=7))
styles.add(ParagraphStyle(name='Bodyx', fontName='Helvetica', fontSize=9.2, leading=13.2, textColor=INK, spaceAfter=7))
styles.add(ParagraphStyle(name='Smallx', fontName='Helvetica', fontSize=7.5, leading=10.1, textColor=INK, spaceAfter=4))
styles.add(ParagraphStyle(name='Tinyx', fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=INK, spaceAfter=2, splitLongWords=True))
styles.add(ParagraphStyle(name='White', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=colors.white))

def clean(s):
    return str(s).translate(str.maketrans({'\u2014':' - ','\u2013':'-','\u00b5':'u','\u03bc':'u','\u03a9':'ohm','\u2265':'>=','\u2264':'<=','\u00b0':' deg','\u00d7':'x','\u00b1':'+/-'}))

def para(s, st='Bodyx'):
    return Paragraph(escape(clean(s)).replace('\n','<br/>'), styles[st])

def heading(s): return para(s,'H2x')

def table(rows, widths, small=False):
    st='Tinyx' if small else 'Smallx'
    data=[[para(c,'White' if i==0 else st) for c in row] for i,row in enumerate(rows)]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('LINEBELOW',(0,0),(-1,0),.5,TEAL)]))
    return t

def footer(c,d):
    w,h=d.pagesize;c.saveState();c.setStrokeColor(TEAL);c.setLineWidth(.5);c.line(17*mm,16*mm,w-17*mm,16*mm)
    c.setFont('Helvetica',7);c.setFillColor(GRAY);c.drawString(17*mm,12*mm,'PUMP CONTROLLER / REV B / ENGINEERING PROTOTYPE / 19 NOV 2026')
    c.drawRightString(w-17*mm,12*mm,str(d.page));c.restoreState()

class Circuit(Flowable):
    def __init__(self,kind,height): Flowable.__init__(self);self.kind=kind;self.width=498;self.height=height
    def draw(self):
        c=self.canv;c.setLineWidth(1);c.setStrokeColor(INK);c.setFillColor(INK)
        def txt(x,y,t,size=8,bold=False):
            c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,clean(t))
        def box(x,y,w,h,title,sub=''):
            c.setFillColor(PALE);c.roundRect(x,y,w,h,4,stroke=1,fill=1);c.setFillColor(INK)
            txt(x+7,y+h-15,title,9,True)
            for i,line in enumerate(sub.split('\n')):txt(x+7,y+h-29-i*11,line,7.7)
        def wire(*points):
            for (x,y),(xx,yy) in zip(points,points[1:]):c.line(x,y,xx,yy)
        def node(x,y):c.circle(x,y,2,stroke=0,fill=1)
        def res(x,y,w,label):
            wire((x,y),(x+8,y));c.rect(x+8,y-4,w-16,8);wire((x+w-8,y),(x+w,y));txt(x,y+10,label,7)
        def cap(x,y,label):
            wire((x,y),(x,y-8));c.line(x-7,y-8,x+7,y-8);c.line(x-7,y-12,x+7,y-12);wire((x,y-12),(x,y-27));txt(x+10,y-15,label,7)
        if self.kind=='architecture':
            box(0,145,143,57,'Incoming 230 V AC','F1 + R1 + protected MOV\nSupply taken before contactor')
            box(184,145,143,57,'Isolated 5 V / 6 W','U1: RACM06E-05SK/277\nU2: 3.3 V buck regulator')
            wire((143,174),(184,174));box(365,145,132,57,'Local controls','STOP / MAN-OFF-AUTO\nSTART / fault RESET')
            box(0,50,143,65,'Voltage + motor CT','ADE7953, live domain\nReal W, RMS A / V, PF\nADuM6421A isolation')
            box(184,50,143,65,'ESP32-C6-MINI-1U','Matter over Wi-Fi\nLocal protection logic\nExternal 2.4 GHz antenna')
            box(365,50,132,65,'Tank + inlet probes','AC excitation, 4 levels\nTMUX1208 + ADS1115\n0.91 inch OLED display')
            wire((255,145),(255,115));wire((143,82),(184,82));wire((327,82),(365,82));wire((431,145),(431,130),(338,130),(338,100),(327,100))
            txt(194,29,'K1 health permit + K2 run',8,True);wire((255,50),(255,40))
            txt(178,13,'Series contacts control existing KM coil',8)
        elif self.kind=='power':
            txt(0,176,'J1.1  L',9,True);wire((42,179),(60,179));res(60,179,60,'F1 T1A');res(120,179,83,'R1 22R / 3W')
            wire((203,179),(273,179));node(232,179)
            box(273,112,125,88,'U1  isolated AC/DC','RACM06E-05SK/277\n5 V / 1.2 A\n25.4 x 25.4 x 16.7 mm')
            txt(0,124,'J1.2  N',9,True);wire((42,127),(273,127));node(232,127)
            wire((232,179),(232,162));c.rect(226,144,12,18);wire((232,144),(232,127));txt(166,151,'RV1',7);txt(151,141,'TMOV 320VAC',7)
            wire((398,179),(473,179));txt(422,188,'+5V',9,True);wire((398,127),(473,127));txt(422,114,'GND (isolated)',8)
            res(412,153,62,'R2 33R / 2W');wire((412,153),(412,179));wire((474,153),(484,153),(484,127),(473,127));node(412,179)
            box(0,15,144,71,'U2 TPS62162DSGR','VIN/EN = 5 V; FB = GND\nL1 = 2.2 uH, >=3 A sat\n3.3 V / 1 A output')
            box(176,15,145,71,'Bypass and bulk','5 V: 47 uF + 100 nF\nBuck input: 22 uF + 100 nF\n3V3: 22 uF + 100 nF')
            box(353,15,144,71,'Thermal requirement','5.7 W reserved worst case\nPSU local ambient <=50 C\nR2 copper area >=300 mm2')
        elif self.kind=='control':
            txt(0,188,'MAINS COIL CIRCUIT - keep overload; confirm actual coil rating',9,True)
            box(0,130,97,40,'Control supply','Existing coil supply')
            box(126,130,98,40,'Overload NC','Existing protection')
            box(254,130,111,40,'J30: K1 + K2','Two NO contacts')
            box(398,130,99,40,'KM coil A1/A2','Existing contactor')
            wire((97,150),(126,150));wire((224,150),(254,150));wire((365,150),(398,150))
            txt(0,108,'All parallel holding/start paths around K1/K2 must be removed or reworked.',8)
            txt(0,80,'ISOLATED 5 V CONTROL PATH',9,True)
            box(0,19,105,43,'J32.1 +5 V','NC STOP -> J32.2')
            box(126,19,113,43,'MAN / OFF / AUTO','J32.3 / J32.4 returns')
            box(259,19,106,43,'D33/D34 + J31','SS14 OR + HH NC')
            box(386,19,111,43,'K1 coil + Q30','ARM AND PERMIT')
            wire((105,40),(126,40));wire((239,40),(259,40));wire((365,40),(386,40))
        elif self.kind=='meter':
            txt(0,168,'VOLTAGE CHANNEL: all nodes below are mains-referenced',9,True)
            txt(0,139,'L protected',8);wire((65,142),(80,142));res(80,142,174,'R43-R46: 4 x 249k, 0.1%, 1206')
            wire((254,142),(389,142));node(282,142);txt(398,139,'ADE VP',8,True)
            wire((282,142),(282,128));c.rect(278,103,8,25);wire((282,103),(282,84));txt(294,114,'R47 1k 0.1%',7)
            cap(366,142,'C51 33nF');wire((366,115),(366,84),(282,84),(230,84));txt(187,72,'M_GND = N through R42 0R',8)
            txt(0,47,'CURRENT CHANNEL: CT = AC1020 (1000:1)',9,True)
            txt(0,30,'RB1 = 6.8R 0.1%, 0.5W permanently across CT secondary.',8)
            txt(0,15,'J10.1 -> R49 1k -> IAP; C53 33nF to M_GND; J10.2 = M_GND.',8)
            txt(0,0,'Ideal meter range ~26 Arms; startup inrush may clip. CT is not on main PCB.',8)

def build_front():
    doc=SimpleDocTemplate(str(TMP/'overview.pdf'),pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=19*mm,bottomMargin=22*mm)
    story=[para('Compact pump controller','Title2'),para('1 HP single-phase DOL starter | Rev B | Detailed prototype design','H2x'),
      para('A local controller for tank filling, motor monitoring and dry-run protection. It uses the existing contactor to switch the motor; motor current does not pass through this PCB.'),
      Circuit('architecture',215),
      table([['Design choice','Implementation'],['Local connectivity','Matter over Wi-Fi using ESP32-C6; Apple Home / compatible Aqara Matter controller. LAN required for app control; WAN not required for local operation after setup.'],['Probe reuse','Assumed five tank wires = common + four level probes. Separate inlet sensing has a dedicated reference terminal. Probe material and insulation must be verified.'],['Board envelope','90 x 70 mm main-board placement target, four copper layers, SMD on both sides. Separate 0.91-inch OLED module, 36 x 12.5 mm PCB, 128 x 32 pixels. Final PCB checks are supplied separately.'],['Power conversion','Isolated 6 W switching module. A small high-frequency transformer remains inside; no mains-referenced capacitive-dropper supply.']], [102,396]),
      heading('Design status'),para('Component values and pin assignments are defined. Native schematic connectivity is checked. This is an engineering prototype, not a fabrication release or a tested controller. Firmware, enclosure fit, contactor-coil suitability, mains protection coordination and physical tests remain required.'),
      PageBreak(),para('Power and starter integration','Title2'),Circuit('power',218),
      para('U1 requires a permanent load for its specified light-load behavior. R2 dissipates 0.677-0.844 W over the design voltage/tolerance range. Its heat-spreading copper and the closed starter temperature are part of the layout constraint.'),
      Circuit('control',205),
      para('The new STOP/selector/START/RESET wiring is isolated low voltage. Disconnect old mains button connections before reusing contacts. J30 carries only the contactor-coil circuit; verify coil inrush and inductive switching ratings. Existing motor overload protection remains in series.'),
      para('F1 interrupting capacity is 200 A at 600 VAC. R1 limits faults after R1 only. Prospective fault current and upstream protective-device coordination must be verified; the upstream breaker rating alone is not proof of coordination.','Smallx'),
      PageBreak(),para('Field connections','Title2'),
      para('Connector numbering is authoritative in the native schematic. Do not assume an old controller uses the same terminal order.'),
      table([['Connector','Pins and use'],['J1 - AC input','1 L; 2 N. Supply before the contactor, through suitable upstream protection.'],['J10 - motor CT','1 CT high; 2 M_GND. Mains-referenced secondary. Permanent 6.8-ohm burden at the CT; pass one motor conductor through its aperture.'],['J20 - tank','1 common; 2 L1; 3 L2; 4 L3; 5 L4/full. Fit L1 lowest, L4 highest. Existing electrode wires must be detached from the old controller.'],['J21 - inlet','1 inlet sense; 2 inlet common/reference. A single electrode needs a verified second electrode in the same water body; never substitute protective earth.'],['J30 - coil contacts','1 CTRL_IN; 2 CTRL_OUT. Series K1 + K2 contacts. No existing holding path may bypass them.'],['J31 - high-high','1 mode-coil 5 V; 2 K1 coil+. Normally closed independent overflow float; opens on high-high. Local link only if this independent protection is intentionally absent.'],['J32 - controls','1 +5 V; 2 STOP return + selector common; 3 MAN return; 4 AUTO return; 5 START_N; 6 RESET_N; 7 GND. START and RESET are momentary NO to pin7.'],['J33 - OLED','1 +3V3; 2 GND; 3 SDA; 4 SCL. GH1.25 cable end on main PCB, PH2.0 at Waveshare display. Numeric pin map J33 -> display: 1->4, 2->3, 3->2, 4->1. 3.3 V only; 100 mA reserved pending measurement.'],['J34 - expansion','1 +3V3 (25 mA maximum reserved); 2 GND; 3 I2C SDA; 4 I2C SCL; 5 spare MCP GPB6; 6 spare GPB7. 3.3 V only, short internal cable, no hot plug.'],['J2 - internal service','1 GND; 2 3V3 sense; 3 UART TX; 4 ARM test; 5 MCU reset; 6 BOOT; 7 USB D-; 8 USB D+. No USB 5 V input. ARM test is not UART RX.']], [110,388]),
      heading('Mounting and wiring'),para('Use the external antenna outside a metal starter enclosure, with a suitable feedthrough. Keep CT and mains wiring in the live area, probe wiring in the isolated area, and maintain the PCB isolation corridor through the enclosure and mounting hardware. The small OLED needs a protective window and insulated mounting; confirm access and total depth after measuring the starter.'),
      PageBreak(),para('Measurement and protection','Title2'),Circuit('meter',182),
      heading('Conductive probe front end'),
      table([['Stage','Values / implementation'],['Reference and excitation','1.65 V bias: 10k / 10k, TLV9004 buffer, 47R + 1uF. GPIO -> 27k with 43k to bias gives nominal 0.636 / 2.664 V drive. Balanced 25 Hz excitation.'],['Common leads','Separate tank and inlet buffers. 2.2k + two parallel 1uF / 50V blocking capacitors + 4.99k + 4.99k field resistance. TVS and clamps per detailed sheets.'],['Each sense lead','10k + 10k field resistance, TVS/clamp, 1uF DC block, 47k to bias, 22k ADC isolation, 1nF C0G filter. Repeat for four levels and inlet.'],['Readout','TMUX1208 -> TLV9004 -> ADS1115 differential against bias. 100R / 10nF input filters. I2C address 0x48; 860 samples/s; 400 kHz bus.'],['Provisional classification','WET >=0.100 V demodulated amplitude; DRY <=0.060 V; intermediate ambiguous. Validate with actual water, cable and temperature; not universal thresholds.']], [110,388]),
      para('Four level probes provide five height bands, not continuous litres. A volume estimate requires the tank shape, capacity and probe heights. Broken common wires can resemble an empty tank; the independent high-high float is the separate overflow stop.'),
      heading('Load-based dry-run detection'),para('Calibrate real power, current and power factor while pumping water across the normal lift/head range. Apply a measured startup/priming allowance, then require sustained underload before stopping. Treat clipped inrush, stale readings and out-of-range sensors as invalid data. No fixed current or watt threshold can be derived from the 1 HP nameplate alone.'),
      PageBreak(),para('Operating behavior and checks','Title2'),
      table([['Mode / event','Required behavior'],['OFF / STOP / high-high','Physically interrupts K1 coil supply and clears hardware ARM latch. Restoring the switch or float does not itself restart the pump.'],['MANUAL','Local START requests run through both relay gates. Level/full, inlet, electrical, dry-run and maximum-run protections remain active. Does not require Wi-Fi.'],['AUTO','After deliberate arming, fill at the configured low band and stop at full with hysteresis. Enforce minimum off time and level-progress / maximum-run limits.'],['Matter request','Validated control request only. It cannot override OFF, physical STOP, a fault latch or high-high. Detail telemetry is intended for a local LAN dashboard; Apple Home display of litres, W, A and V is not guaranteed.'],['Fault / power return','Outputs default off. A fresh user re-arm is required after power return or watchdog/interlock fault. Fault RESET and START have separate meanings.'],['Hardware watchdog','STWD100 timeout: 1.6 s nominal, 2.24 s maximum. Service it only after a successful fresh control/sensor cycle. HEARTBEAT must never clock ARM_CMD.']], [110,388]),
      heading('Required validation before connecting the motor'),
      para('1. Inspect polarity, footprint pads, isolation, soldering and resistance between live and isolated domains. Confirm the finished layout reports and manufacturer land patterns.'),
      para('2. Use isolated, current-limited low-voltage bench power to check rails, startup, probe amplitudes, ADC timing, OLED and control inputs. Keep mains disconnected. Exercise STOP/OFF/high-high with stalled software and stuck requests.'),
      para('3. Verify mains insulation, protective-device coordination, surge/EMC behavior and the coil interface with qualified equipment and supervision. Test supply/current measurement against a reference meter.'),
      para('4. Measure the closed-starter temperature at worst ambient and load. Check R2 temperature and the PSU <=50 C local ambient requirement. Validate RF with the enclosure closed.'),
      para('5. Commission actual wet/dry probes and pump loads. Confirm full-stop, broken-wire cases, power interruption, brownout, stale ADC, watchdog, and controlled dry-run simulation before relying on automatic operation.'),
      para('Firmware is not included in this hardware revision. No motor, water, insulation, RF-interoperability or temperature test has yet been performed. The independent controls are a functional protection design, not a certified safety-rated control system.','Smallx'),
      PageBreak(),para('Built for future programming','Title2'),
      para('The hardware supports software changes and small sensor additions. The following are firmware requirements for implementation, not functions already tested on a working device.'),
      table([['Capability','Provision and design rule'],['Recovery programming','Native USB D-/D+ at J2, BOOT and RESET buttons, and UART TX logs. Keep a recovery path that does not depend on working Wi-Fi or application firmware.'],['Wireless updates','Local authenticated update path; signed firmware, two application slots, boot validation and rollback to the previous working version. Update only with pump disabled; do not resume pumping on reboot.'],['Separate settings','Versioned nonvolatile configuration for probe mapping, tank shape, level thresholds, timings, voltage limits and calibrated dry-run envelopes. Validate ranges and migrate old settings when firmware changes.'],['Calibration and records','Keep meter/probe calibration separate from ordinary settings and firmware images. Provide versioned export/import and bounded fault records; do not wear flash with per-sample writes.'],['Expandable hardware','J34 gives I2C plus two spare MCP23017 GPIO, isolated-domain 3.3 V logic and a 25 mA supply allowance. Reserve addresses 0x20 and 0x48. Longer field wiring or other voltages require an appropriate interface.'],['Modular software','Separate device drivers, sensor processing, protection state machine, configuration storage, Matter endpoint and local dashboard. Network handlers submit requests; they do not write relay GPIO directly.'],['Fixed hardware limits','Physical STOP, OFF, independent high-high and existing overload cannot be disabled by an app setting. Motor ratings, mains isolation and analog measurement ranges remain hardware limits.']], [110,388]),
      heading('Small screen, adaptable pages'),para('Use Waveshare 14657, a 0.91-inch 128 x 32 SSD1306 OLED with a 36 x 12.5 mm PCB. Rotate readable pages: water band/mode, V/A/W, then faults. Show one or two readings clearly instead of crowding every value onto one screen. Dim or blank after inactivity; faults can wake the display. Screen layout is software-defined.'),para('OLED updates share the sensor I2C bus. Use deadline-aware short transfers between probe samples, never a blocking whole-frame write. The display must not delay protection checks or hide a stale sensor result.','Smallx'),heading('Flash capacity and update planning'),
      para('ESP32-C6-MINI-1U-H8 provides 8 MB flash. Reserve two firmware slots from the first build and leave space for NVS, calibration and bounded records. A trial budget of two 3 MB application slots is plausible; the compiled Matter/application size must be measured before freezing the partition table.'),
      para('The C6 hardware can support a future Thread-oriented firmware variant, but Wi-Fi/Thread concurrency, memory use and Matter compatibility require a separate implementation and validation. A firmware update cannot promise arbitrary new hardware functions.'),
      heading('Acceptance tests for programmability'),
      para('Demonstrate USB recovery from invalid firmware, rollback after a failed OTA boot, interrupted update recovery, settings migration, invalid-config rejection, calibration preservation, and default-off output behavior during every update/reset.')]

    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def build_bom():
    rows=list(csv.DictReader((P/'design/parts-complete.csv').open()))
    groups=OrderedDict()
    for r in rows:
        key=(r['Board'],r['Value'],r['MPN or procurement specification'],r['Footprint'],r['Description'])
        groups.setdefault(key,[]).append(r['Reference'])
    out=[para('Parts list','Title2'),para('All fitted main-board parts, the external OLED module and installation items. Exact order codes are provided where selected. Entries marked Generic or SPEC are procurement requirements: qualify the chosen manufacturer part before purchasing or assembling.'),para('Each ungrouped reference, footprint and manufacturer source link is also supplied in design/parts-complete.csv. Do not substitute mains/isolation parts or change the CT burden arrangement without reviewing the affected ratings.','Smallx')]
    data=[['Qty / board','References','Value and part / procurement requirement','Package / notes']]
    for (board,value,mpn,fp,description),refs in groups.items():
        pkg=fp.split(':')[-1].replace('_',' ') if fp else 'External installation item'
        data.append([str(len(refs))+' / '+board,', '.join(refs),value+'\n'+mpn,pkg+'\n'+description])
    out.append(table(data,[58,112,235,339],small=True))
    doc=SimpleDocTemplate(str(TMP/'parts-list.pdf'),pagesize=landscape(A4),leftMargin=17*mm,rightMargin=17*mm,topMargin=19*mm,bottomMargin=22*mm)
    doc.build(out,onFirstPage=footer,onLaterPages=footer)

def combine():
    writer=PdfWriter()
    parts=[(TMP/'overview.pdf','Design overview and integration'),(P/'hardware/exports/schematic.pdf','Main-board detailed circuit'),(TMP/'parts-list.pdf','Complete parts list')]
    for p,title in parts:
        if p.exists():writer.append(str(p),outline_item=title)
    for p in sorted((P/'hardware/exports').glob('layout-*.pdf')):writer.append(str(p),outline_item=p.stem.replace('-',' '))
    writer.add_metadata({'/Title':'1 HP pump controller - Rev B design pack','/Author':'kkz6','/Subject':'Detailed circuit, component values, integration and prototype PCB review'})
    path=OUT/'pump-controller-rev-b-design-pack.pdf'
    with path.open('wb') as f:writer.write(f)
    print(path)
    print('Pages:',len(PdfReader(path).pages))

if __name__=='__main__':build_front();build_bom();combine()
