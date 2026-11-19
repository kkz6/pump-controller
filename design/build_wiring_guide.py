"""Create terminal-location/wiring SVGs and a six-page illustrated Rev C wiring guide."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, String, PolyLine
from reportlab.graphics import renderSVG, renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, Image
from reportlab.lib.units import mm

P=Path(__file__).resolve().parents[1]
W=P/'hardware/wiring'; O=P/'output/pdf'; W.mkdir(exist_ok=True); O.mkdir(exist_ok=True)
INK='#183442'; TEAL='#007C83'; RED='#A83E2D'; BLUE='#315F98'; GRAY='#5E6B72'; PALE='#EAF4F3'; HOT='#FBEEEA'

def t(d,x,y,s,size=20,color=INK,bold=False):
    d.add(String(x,y,s,fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,fillColor=colors.HexColor(color)))
def rect(d,x,y,w,h,fill='white',stroke=GRAY,r=0):
    d.add(Rect(x,y,w,h,rx=r,ry=r,fillColor=colors.toColor(fill),strokeColor=colors.HexColor(stroke),strokeWidth=2))
def wire(d,pts,color=TEAL,width=4):
    flat=[a for point in pts for a in point]
    d.add(PolyLine(flat,strokeColor=colors.HexColor(color),strokeWidth=width,fillColor=None))
def dot(d,x,y,color=TEAL,r=5):
    d.add(Circle(x,y,r,fillColor=colors.HexColor(color),strokeColor=None))
def box(d,x,y,w,h,title,lines=(),color=TEAL):
    rect(d,x,y,w,h,PALE if color==TEAL else HOT if color==RED else '#F2F4F5',color,8)
    t(d,x+14,y+h-28,title,21,color,True)
    for i,line in enumerate(lines):t(d,x+14,y+h-53-i*23,line,18)
def scaled(d,w):
    n=Drawing(w,d.height*w/d.width); n.add(d); n.scale(w/d.width,w/d.width); n.hAlign='CENTER'; return n

def locator():
    d=Drawing(1400,1000)
    t(d,25,950,'CONNECTOR LOCATIONS / TOP COMPONENT SIDE',31,INK,True)
    t(d,25,915,'Actual PCB pad positions. Numbers do not describe a loose plug viewed from its mating face.',20,GRAY)
    rect(d,300,190,810,630,'#F5F8F7',TEAL)
    t(d,590,165,'90 mm',21,GRAY);t(d,1120,195,'70 mm',19,GRAY)
    rect(d,525,545,229,229,'#E6EAEB','#A6B0B4');t(d,567,650,'AC/DC module',21,GRAY)
    for yy in [318,435]:
        rect(d,510,yy,165,80,'#E6EAEB','#A6B0B4');t(d,550,yy+31,'Relay',20,GRAY)
    for yy in [217,793]:d.add(Circle(1083,yy,12,fillColor=colors.white,strokeColor=colors.HexColor(GRAY),strokeWidth=2))
    locations=json.loads((W/'connector-locations.json').read_text()); data=locations['connectors']; positions={}
    for j in data:
        ref=j['ref']; col=RED if ref in ['J1','J30','J10'] else TEAL if ref not in ['J2','J34'] else GRAY
        pads=[q for q in j['pads'] if q['pin'].isdigit()]
        coords=[(300+q['xy_mm'][0]*9,820-q['xy_mm'][1]*9,q['pin']) for q in pads]
        xs=[q[0] for q in coords];ys=[q[1] for q in coords]
        rect(d,min(xs)-15,min(ys)-15,max(xs)-min(xs)+30,max(ys)-min(ys)+30,'white',col,3)
        for x,y,n in coords:
            if n=='1':rect(d,x-5,y-5,10,10,col,col)
            else:dot(d,x,y,col,5)
            if ref in ['J2','J34','J33']:t(d,x-3,y-15,n,10,col,True)
            elif ref in ['J1','J10','J21']:t(d,x-4,y-29,n,15,col,True)
            else:t(d,x+18,y-5,n,15,col,True)
        positions[ref]=(sum(xs)/len(xs),sum(ys)/len(ys))
    calls=[('J1',20,710,240,100,'J1 / BOARD POWER',['1 = L   2 = N','Incoming supply branch'],RED),
           ('J30',20,520,240,100,'J30 / COIL SWITCH',['1 = IN   2 = OUT','Both are coil-circuit wires'],RED),
           ('J10',20,220,240,100,'J10 / MOTOR CT',['1 = CT high','2 = meter return (live)'],RED),
           ('J32',1140,700,240,110,'J32 / BUTTONS',['1-7 run top to bottom','STOP / MODE / START','4 and 6: no external wire'],TEAL),
           ('J33',1140,460,240,100,'J33 / OLED',['1 3V3 / 2 GND','3 SDA / 4 SCL'],TEAL),
           ('J21',1140,220,240,100,'J21 / INLET',['Left 2 = reference','Right 1 = inlet sensor'],TEAL),
           ('J20',810,45,300,105,'J20 / TANK',['Top 5=L4; then 4=L3, 3=L2,','2=L1; bottom 1=common'],TEAL),
           ('J31',460,45,300,105,'J31 / HIGH-HIGH FLOAT',['Top 2 / bottom 1','Normally closed dry contact'],TEAL),
           ('J2',1050,845,330,65,'J2 / SERVICE',['Programming, not field power'],GRAY),
           ('J34',610,845,370,65,'J34 / EXPANSION',['Internal use; not field power'],GRAY)]
    for ref,x,y,w,h,title,lines,col in calls:
        cx,cy=positions[ref]
        if x<300:wire(d,[(x+w,y+h/2),(280,y+h/2),(cx-19,cy)],col,2)
        elif ref=='J32':wire(d,[(x,y+h/2),(1008,y+h/2),(1008,cy),(cx+19,cy)],col,2)
        elif x>=1140:wire(d,[(x,y+h/2),(1125,y+h/2),(cx+19,cy)],col,2)
        elif y<190:wire(d,[(x+w/2,y+h),(x+w/2,178),(cx,cy-18)],col,2)
        elif ref=='J2':wire(d,[(x,y+h/2),(1030,y+h/2),(1030,cy+24),(cx-18,cy)],col,2)
        else:wire(d,[(x+w/2,y),(x+w/2,833),(cx,cy+18)],col,2)
        box(d,x,y,w,h,title,lines,col)
    settings={k['ref']:k for k in locations.get('onboard_keys',[]) if k['ref'] in ['SW3','SW4']}
    if len(settings)==2:
        for ref,k in settings.items():
            x=300+k['position_mm'][0]*9;y=820-k['position_mm'][1]*9
            rect(d,x-15,y-12,30,24,PALE,TEAL,3);t(d,x-6,y-5,ref[-1],16,TEAL,True)
            wire(d,[(1140,620),(1127,620),(1127,y),(x+17,y)],TEAL,2)
        box(d,1140,570,240,100,'PCB SETTINGS',['3 = SW3 SET / RESET','4 = SW4 NEXT / +'],TEAL)
    t(d,25,12,'RED: mains or mains-referenced. TEAL: isolated low voltage. Square pad marks pin 1. SW1/SW2 service keys are on the reverse side.',17,GRAY)
    return d

def controls():
    d=Drawing(1400,880)
    t(d,30,830,'THREE FRONT CONTROLS + TWO SMALL PCB SETTINGS KEYS',31,INK,True)
    t(d,30,790,'Existing START/STOP actuators: preserve power contacts; add separate isolated contacts where compatible.',21,GRAY)
    box(d,30,650,220,85,'J32.1 / +5 V',['STOP supply'])
    wire(d,[(250,695),(330,695)]);dot(d,330,695);dot(d,450,695)
    wire(d,[(330,695),(450,695)]);wire(d,[(350,715),(430,675)],TEAL,2)
    t(d,310,742,'STOP / NC',24,TEAL,True)
    wire(d,[(450,695),(770,695)]);dot(d,560,695)
    box(d,470,560,245,74,'J32.2 / RETURN',['MODE feed'])
    wire(d,[(560,695),(560,634)])
    dot(d,770,695);dot(d,925,695);wire(d,[(770,695),(900,730)])
    t(d,765,760,'MODE / NO',24,TEAL,True);wire(d,[(925,695),(1110,695)])
    box(d,1110,660,255,70,'J32.3 / MODE',[])
    box(d,30,424,250,74,'J32.5 / START',[])
    wire(d,[(280,460),(450,460)]);dot(d,450,460);dot(d,600,460)
    wire(d,[(450,460),(575,495)]);t(d,450,520,'START / NO',24,TEAL,True)
    wire(d,[(600,460),(1110,460)]);box(d,1110,424,255,74,'J32.7 / GND',['Isolated return'])
    t(d,30,365,'External wires: STOP 1-2 (NC), MODE 2-3 (NO), START 5-7 (NO). Leave J32.4 and J32.6 unwired.',23,INK,True)
    rect(d,30,95,1335,215,'#F2F4F5',GRAY,10)
    t(d,55,270,'ON THE PCB / INTERNAL SERVICE KEYS - NO EXTRA FRONT-PANEL WIRES',25,GRAY,True)
    box(d,65,135,500,95,'SW3 / SET / RESET',['Short: select/save or acknowledge cleared fault','Hold: enter settings / back / exit'],TEAL)
    box(d,770,135,540,95,'SW4 / NEXT / +',['Short: next item / increase value','Hold: previous item / decrease value'],TEAL)
    t(d,30,50,'Press/release STOP before MODE/settings. SW1 MCU RESET and SW2 BOOT are service keys, not settings.',22,GRAY)
    return d

def power():
    d=Drawing(1400,900)
    t(d,30,850,'POWER AND COIL CONTROL / FUNCTIONAL CONNECTIONS',31,INK,True)
    t(d,30,810,'Capacitor-start sequence and actual coil voltage must be identified before using the coil example.',22,GRAY)
    box(d,30,610,230,150,'L / N SUPPLY',['After upstream isolator','and appropriate','circuit protection'],RED)
    rect(d,560,575,390,190,'#F2F4F4',GRAY,10)
    t(d,580,735,'EXISTING CAPACITOR STARTER',21,INK,True)
    rect(d,605,595,55,110,'#DBCB63',GRAY,12);rect(d,690,595,55,110,'#C9D0D2',GRAY,12)
    rect(d,775,595,145,110,'#E1E7E8',GRAY,5);t(d,783,640,'Contactor',20,GRAY)
    for x in [800,895]:
        for y in [610,690]:dot(d,x,y,GRAY,6)
    t(d,570,550,'Keep motor/capacitor wiring; verify overload.',20,GRAY)
    box(d,1170,635,195,125,'1 HP MOTOR',['Existing motor','cable/leads'],RED)
    wire(d,[(260,725),(560,725)],RED);wire(d,[(260,670),(560,670)],BLUE)
    t(d,285,739,'L',22,RED,True);t(d,285,683,'N',22,BLUE,True)
    wire(d,[(950,700),(1170,700)],GRAY,13);t(d,972,735,'Existing cable',20,GRAY)
    dot(d,345,725,RED);dot(d,410,670,BLUE)
    wire(d,[(345,725),(345,495),(560,495)],RED);wire(d,[(410,670),(410,450),(560,450)],BLUE)
    box(d,560,415,390,105,'J1 / CONTROLLER POWER',['1 = L / 2 = N'],RED)
    t(d,990,490,'No motor current',22,RED,True);t(d,990,460,'through J1 or J30.',22,RED,True)
    t(d,30,385,'PE stays bonded to motor/enclosure. Trace the total-current CT location; do not pick an arbitrary winding lead.',20,GRAY)
    rect(d,20,25,1360,330,HOT,RED,12)
    t(d,45,310,'COIL EXAMPLE ONLY: VERIFIED 230 VAC COIL + WORKING CAPACITOR-START CIRCUIT',25,RED,True)
    box(d,45,180,190,80,'Control L',['Protected feed'],RED)
    box(d,285,180,235,80,'Overload NC',['95-96 common; verify'],RED)
    box(d,580,165,340,110,'J30 / BOARD RELAYS',['1 IN -> K1 -> K2 -> 2 OUT','Series NO contacts'],RED)
    box(d,1120,165,220,110,'KM COIL',['A1 switched feed','A2 control return'],RED)
    wire(d,[(235,220),(285,220)],RED);wire(d,[(520,220),(580,220)],RED)
    wire(d,[(920,220),(1120,220)],RED);t(d,955,238,'to A1',20,RED)
    wire(d,[(1230,165),(1230,120),(165,120)],BLUE);t(d,50,112,'Control N',20,BLUE,True)
    t(d,45,67,'J30 cannot replace an unknown start-capacitor switch. No old START/holding path may bypass J30.',22,RED,True)
    return d

def oled():
    d=Drawing(1400,420)
    t(d,30,380,'OLED CABLE / FOUR SIGNALS, REVERSED NUMERIC ORDER',29,INK,True)
    box(d,30,45,345,270,'J33 / MAIN PCB',['JST GH 1.25 mm'],TEAL)
    box(d,1020,45,350,270,'OLED / FRONT PANEL',['PH 2.0 mm connector'],TEAL)
    rows=[('1','+3.3 V','4','VCC',RED),('2','GND','3','GND',GRAY),('3','SDA','2','SDA',TEAL),('4','SCL','1','SCL',BLUE)]
    for i,(a,s,b,ss,col) in enumerate(rows):
        y=225-i*45
        t(d,185,y-6,a+'  '+s,24,col,True);t(d,1040,y-6,b+'  '+ss,24,col,True)
        wire(d,[(375,y),(1020,y)],col,4);t(d,600,y+9,a+' -> '+b,18,col)
    return d

DIAGRAMS={'connector-map':locator(),'panel-controls':controls(),'power-and-coil':power(),'oled-harness':oled()}
for name,drawing in DIAGRAMS.items():
    renderSVG.drawToFile(drawing,str(W/(name+'.svg')))
    tmp=P/'tmp/pdfs';tmp.mkdir(parents=True,exist_ok=True)
    renderPDF.drawToFile(drawing,str(tmp/('wiring-'+name+'.pdf')))


styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='T',fontName='Helvetica-Bold',fontSize=25,leading=29,textColor=colors.HexColor(INK),spaceAfter=11))
styles.add(ParagraphStyle(name='H',fontName='Helvetica-Bold',fontSize=13,leading=16,textColor=colors.HexColor(TEAL),spaceBefore=9,spaceAfter=6))
styles.add(ParagraphStyle(name='B',fontName='Helvetica',fontSize=10,leading=14,textColor=colors.HexColor(INK),spaceAfter=7))
styles.add(ParagraphStyle(name='S',fontName='Helvetica',fontSize=8.5,leading=11.5,textColor=colors.HexColor(INK),spaceAfter=5))
styles.add(ParagraphStyle(name='TH',fontName='Helvetica-Bold',fontSize=9,leading=12,textColor=colors.white))
def para(s,style='B'):return Paragraph(escape(s).replace('\n','<br/>'),styles[style])
def tab(rows,widths):
    data=[[para(v,'TH' if i==0 else 'S') for v in row] for i,row in enumerate(rows)]
    q=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    q.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor(PALE)]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));return q

def foot(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor(TEAL));c.line(17*mm,15*mm,280*mm,15*mm);c.setFont('Helvetica',8);c.setFillColor(colors.HexColor(GRAY));c.drawString(17*mm,10*mm,'PUMP CONTROLLER / REV C / FRONT CONTROLS + PCB SETTINGS / PROTOTYPE');c.drawRightString(280*mm,10*mm,str(doc.page));c.restoreState()
width=744
story=[para('Where every wire connects','T'),para('Rev C / existing START + STOP, one MODE button, settings on PCB','H'),
para('The main PCB mounts inside the starter; the small OLED mounts behind a protected lid window. The existing motor and capacitor-start power circuit stays in place. The board only commands the contactor coil.'),
tab([['Connection','PCB terminals','External connection'],['Existing STOP','J32.1 and J32.2','Separate isolated NC auxiliary contact on the same actuator, where compatible. Preserve required original power function.'],['Existing START','J32.5 and J32.7','Separate isolated NO auxiliary contact on the same actuator, where compatible. Preserve original capacitor-start contacts.'],['New MODE','J32.2 and J32.3','One NO button toggles MANUAL/AUTO while stopped/unarmed. It never arms or starts.'],['Settings on PCB','SW3 SET/RESET; SW4 NEXT/+','Built-in keys. No extra front wires; J32.4 and J32.6 remain externally unwired.'],['Board power / coil command','J1.1=L, J1.2=N / J30.1=IN, J30.2=OUT','J1: protected incoming branch before contactor. J30: series coil-control contacts, not a voltage output.'],['OLED screen','J33: 1 3V3, 2 GND, 3 SDA, 4 SCL','Cable to OLED pins 4, 3, 2, 1 respectively. GH 1.25 at board; PH 2.0 at screen.']],[105,220,419]),
para('Before replacing RMG: identify its start/run/stop outputs','H'),para('Existing RMG AUTO starts without pressing green START, but its capacitor-start switching path is unidentified. This Rev C interface is not yet a verified drop-in RMG replacement. Preserve motor/capacitor wiring and original START/STOP functions. J32 requires separate isolated auxiliary contacts, not shared mains contacts. Actuator/contact compatibility remains unverified.','S'),
para('This is a prototype proposal. Exact starter-terminal mapping, coil voltage, motor overload protection and enclosure fit remain unverified; firmware is not implemented. No wire colour in a photo is an approved connection identity.','S'),
PageBreak(),para('Find the connector on the board','T'),scaled(DIAGRAMS['connector-map'],600),
PageBreak(),para('Three front buttons; settings on the PCB','T'),scaled(DIAGRAMS['panel-controls'],590),
para('Press AND RELEASE STOP, press MODE to choose MANUAL/AUTO, then fresh START to operate. Internal settings: hold SET only stopped/unarmed; NEXT short = next/increase, NEXT held = previous/decrease; SET short = select/save, SET held = back/exit. Saving/exiting never starts.','S'),
para('MODE while armed cancels run and shows PRESS STOP. Reject ambiguous events and prevent short/hold double actions. Internal keys require isolated low-voltage service power with mains/coil disconnected, unless a verified insulated access arrangement is provided.','S'),
PageBreak(),para('Power wires and the contactor coil','T'),scaled(DIAGRAMS['power-and-coil'],600),
para('The lower diagram applies only after a 230 VAC coil and independent capacitor-start operation are verified. Preserve required overload/emergency-stop functions; old holding paths cannot bypass J30. Press/release physical STOP before overload reset. No direct overload feedback is fitted.','S'),
PageBreak(),para('OLED screen and sensor wires','T'),scaled(DIAGRAMS['oled-harness'],495),
para('Screen: Waveshare 14657, 0.91-inch 128 x 32, module 36 x 12.5 mm. Mount behind a lid window; 3.3 V supply only. Keep the correctly mapped GH-to-PH cable short, provisionally <=100 mm, in the isolated area. No separate level LEDs.','S'),
tab([['Terminal','Wire / sensor','Key constraint'],['J10.1 / .2','CT secondary high / meter return','Mains-referenced. Permanent 6.8-ohm burden at CT. Trace one total motor-supply conductor before winding/capacitor splits.'],['J20.1 / .2 / .3 / .4 / .5','Tank common / L1 / L2 / L3 / L4','L1 lowest; L4 full. Disconnect all probes from the old controller first.'],['J21.1 / .2','Inlet electrode / inlet reference','One inlet wire alone is insufficient: identify its return or add a suitable electrode/conductor.'],['J31.1 / .2','Independent high-high NC float','Closed normally, opens at excess level. A link removes this protection.'],['J2 / J34','Service / internal expansion','Neither is field power. No USB 5 V feed. Follow service instructions.']],[103,235,406]),
para('No sensor return may use unverified earth/neutral/pipe connections. J10 stays in the hazardous area; J20/J21/J31/J32/J33 stay isolated. J33 numeric cable order is reversed; confirm actual mating-face pin numbers.','S'),
PageBreak(),para('Reference starter: what can be identified','T')]
photo=Image(str(W/'reference-starter.png'),width=197,height=350)
legend=[para('Visible functions - exact terminals still unverified','H'),
para('Inside box, centre: two large capacitors. Retain the correct start/run capacitor circuit; their ratings and switching sequence must be checked.','S'),
para('Inside box, upper right: two-pole contactor. J30 eventually controls its verified coil circuit. The photograph does not establish which screws are coil A1/A2 or the coil voltage.','S'),
para('Inside box, lower centre: terminal strip. Do not infer supply/motor identities from wire colours or apparent position. Motor leads may include separate winding/start connections.','S'),
para('Open lid: backs of analogue meters and MCB/control hardware. No mounting cutout or wiring change is approved from this image. An MCB alone does not prove suitable motor overload protection.','S'),
para('Below box: existing RMG water controller. AUTO already starts the pump without pressing green START. A related RMG manual uses separate starter relay pairs; the installed variant is not confirmed. Identify which device handles starting-capacitor switching before removal.','S'),
para('Proposed additions: controller on insulated internal mounting; existing START/STOP actuators plus one MODE button and OLED on the lid; two small settings keys on the PCB; external antenna. Fit is not demonstrated by this photograph or a rendered model.','S')]
photo_table=Table([[photo,legend]],colWidths=[215,529]);photo_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),14)]));story.append(photo_table)
story.append(para('Sources: final circuit/PCB + connector-locations.json; full guide in design/wiring-guide.rst. Schneider: se.com/nl/nl/faqs/FA139744/ and se.com/nl/en/faqs/FA141338/. OLED: waveshare.com/wiki/0.91inch_OLED_Module. Related RMG manual: rmgautomation.com/Downloads/Manual/DFAWLC-044-100101.pdf (installed variant unconfirmed). Photo is not a verified wiring diagram.','S'))
path=O/'pump-controller-rev-c-wiring-guide.pdf'
SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=17*mm,rightMargin=17*mm,topMargin=16*mm,bottomMargin=21*mm,title='Pump controller Rev C - front controls and PCB settings wiring guide',author='kkz6').build(story,onFirstPage=foot,onLaterPages=foot)
print(path)
