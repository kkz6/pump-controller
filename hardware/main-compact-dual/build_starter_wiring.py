"""Generate the two-output revision's field-wiring drawings, in PDF points."""
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas


WIDTH, HEIGHT = A4
MARGIN = 39
RIGHT = WIDTH - MARGIN
INK = "#183433"
MUTED = "#415b5a"
RULE = "#a4b8b6"
PALE = "#eff5f3"
A_COLOR = "#18545e"
B_COLOR = "#734e21"
FONT = "Helvetica"
BOLD = "Helvetica-Bold"


def color(value):
    return HexColor(value)


def text(g, x, y, value, size=10, bold=False, tone=INK):
    g.setFillColor(color(tone))
    g.setFont(BOLD if bold else FONT, size)
    g.drawString(x, HEIGHT - y, value)


def line(g, points, tone=INK, width=1.45):
    g.setLineWidth(width)
    g.setStrokeColor(color(tone))
    p = g.beginPath()
    p.moveTo(points[0][0], HEIGHT - points[0][1])
    for x, y in points[1:]:
        p.lineTo(x, HEIGHT - y)
    g.drawPath(p)


def box(g, x, y, w, h, fill=PALE, stroke=RULE):
    g.setStrokeColor(color(stroke))
    g.setFillColor(color(fill))
    g.setLineWidth(0.75)
    g.roundRect(x, HEIGHT - y - h, w, h, 4, stroke=1, fill=1)


def terminal(g, x, y, tone=INK, filled=False):
    g.setStrokeColor(color(tone))
    g.setFillColor(color(tone) if filled else white)
    g.setLineWidth(1.25)
    g.circle(x, HEIGHT-y, 2.8, fill=1, stroke=1)


def paragraph(g, x, y, lines, size=10, step=15, tone=INK):
    for i, value in enumerate(lines):
        text(g, x, y+i*step, value, size=size, tone=tone)


def title(g, heading, sub, page):
    text(g, MARGIN, 42, "Compact dual-output pump controller", size=10, bold=True, tone=MUTED)
    text(g, MARGIN, 78, heading, size=23, bold=True)
    text(g, MARGIN, 100, sub, size=10, tone=MUTED)
    line(g, [(MARGIN,116),(RIGHT,116)], RULE, .8)
    line(g, [(MARGIN,789),(RIGHT,789)], RULE, .8)
    text(g,MARGIN,806,"COMPACT-DUAL  /  R3 cabinet prototype",8,tone=MUTED)
    text(g,RIGHT-48,806,f"{page} of 8",8,tone=MUTED)


def heading(g, y, name, detail):
    text(g,MARGIN,y,name,15,bold=True)
    text(g,MARGIN,y+17,detail,9.5,tone=MUTED)


def port_group(g, y, title_left="Isolated interposer contacts"):
    start_y=y+26
    box(g,MARGIN,y+11,142,109)
    text(g,MARGIN,y+1,title_left,9,bold=True,tone=MUTED)
    labels=("XC1.3    KCA  A COM", "XC1.4    KCA  A NO", "XC1.1    KCB  B COM", "XC1.2    KCB  B NO")
    yrows=[start_y+i*26 for i in range(4)]
    for i,(yy,label) in enumerate(zip(yrows,labels)):
        text(g,MARGIN+12,yy+3,label,10,bold=True,tone=A_COLOR if i<2 else B_COLOR)
    return MARGIN+142, yrows


def target(g, y, labels, title_text):
    x=366
    box(g,x,y+11,RIGHT-x,109)
    text(g,x,y+1,title_text,9,bold=True,tone=MUTED)
    ys=[y+26+i*26 for i in range(4)]
    for yy,label in zip(ys,labels):
        if label:
            text(g,x+10,yy+3,label,10)
    return x,ys


def page_maintained_four(g):
    title(g,"Two- and four-wire starter connections",
          "HOST command contacts. Install the independent guard and command interposers on pages 4 and 5.",1)
    heading(g,148,"Two wires  /  maintained RUN",
            "For a starter that runs on contact closure and stops on opening.")
    x,ys=port_group(g,193)
    z,_=target(g,193,["RUN input, terminal 1","","","RUN input, terminal 2"],"OEM maintained input")
    for i,tone in [(0,A_COLOR),(3,B_COLOR)]:
        line(g,[(x,ys[i]),(z,ys[i])],tone)
        terminal(g,x,ys[i],tone);terminal(g,z,ys[i],tone)
    mid=x+48
    line(g,[(x,ys[1]),(mid,ys[1]),(mid,ys[2]),(x,ys[2])])
    terminal(g,x,ys[1],A_COLOR);terminal(g,x,ys[2],B_COLOR)
    text(g,mid+10,ys[1]+10,"Series link",10,bold=True)
    text(g,mid+10,ys[1]+23,"inside RUN harness",9,tone=MUTED)
    paragraph(g,MARGIN,341,["The factory loom links A NO to B COM. The two outer wires are A COM and B NO.",
                        "Both relays must close for RUN. Opening either contact removes the request."],10)
    line(g,[(MARGIN,380),(RIGHT,380)],RULE,.8)
    heading(g,416,"Four wires  /  independent inputs",
            "Keep four separate conductors when the manufacturer's START and STOP pairs have separate returns.")
    x,ys=port_group(g,460)
    z,_=target(g,460,["Pair A, terminal 1","Pair A, terminal 2","Pair B, terminal 1","Pair B, terminal 2"],"OEM control interface")
    for i,yy in enumerate(ys):
        tone=A_COLOR if i<2 else B_COLOR
        line(g,[(x,yy),(z,yy)],tone);terminal(g,x,yy,tone);terminal(g,z,yy,tone)
    text(g,MARGIN,612,"Choose the four-wire connection by the OEM input behavior",11,bold=True)
    paragraph(g,MARGIN,636,["Close-to-stop keypad. Connect pair A across the approved START input and pair B",
                           "across the approved STOP input. Each command is a bounded closure."],10)
    paragraph(g,MARGIN,684,["Open-to-stop DOL. Insert pair A only into the added permission section of the",
                           "coil circuit. Keep the original STOP and overload in series with every coil path.",
                           "Connect pair B across the approved momentary START input. Only a fresh pulse starts."],10)
    text(g,MARGIN,738,"J30 and J35 drive the 24 V interposer coils. The A/B pairs above are their dry contacts.",9,bold=True)
    text(g,MARGIN,751,"Key A at pole 1 and B at pole 2. Verify each plug fits only its assigned header.",9,bold=True)
    text(g,MARGIN,773,"Keep the starter's capacitor circuit intact. Motor and capacitor current stay off this harness.",9,bold=True)
    g.showPage()


def page_three(g):
    title(g,"Three-wire electronic starter",
          "Controller position. This harness is for a documented common and two momentary closure inputs.",2)
    heading(g,150,"One shared common in the factory loom",
            "Use the OEM's COM, START and STOP functions. Wire colours and terminal numbers vary by starter.")
    x,ys=port_group(g,203)
    z,_=target(g,203,["OEM common","OEM START","","OEM STOP"],"OEM shared-common inputs")
    mid=265
    line(g,[(x,ys[0]),(z,ys[0])],A_COLOR)
    # B COM is routed down then around the START wire. The jump is unconnected.
    wire_crossing=ys[1]
    line(g,[(x,ys[2]),(mid,ys[2]),(mid,wire_crossing+4)])
    g.setStrokeColor(color(INK));g.setLineWidth(1.45)
    p=g.beginPath();p.moveTo(mid,HEIGHT-(wire_crossing+4))
    p.curveTo(mid+6,HEIGHT-(wire_crossing+4),mid+6,HEIGHT-(wire_crossing-4),mid,HEIGHT-(wire_crossing-4))
    g.drawPath(p)
    line(g,[(mid,wire_crossing-4),(mid,ys[0])])
    # Split the other line around the crossing to avoid an apparent junction.
    line(g,[(x,ys[1]),(mid-5,ys[1])],A_COLOR);line(g,[(mid+9,ys[1]),(z,ys[1])],A_COLOR)
    line(g,[(x,ys[3]),(z,ys[3])],B_COLOR)
    terminal(g,mid,ys[0],filled=True)
    for i,yy in enumerate(ys):
        terminal(g,x,yy,A_COLOR if i<2 else B_COLOR)
        if i!=2: terminal(g,z,yy,A_COLOR if i<2 else B_COLOR)
    text(g,mid+6,ys[0]-6,"Captured COM splice",8.5,bold=True)
    paragraph(g,MARGIN,357,["The only common is the captive splice between the KCA and KCB contact commons.",
                           "KCA NO operates START. KCB NO operates STOP. The two contact pairs are kept separate.",
                           "Keep both outputs within the same starter control system. Never join either contact",
                           "to controller ground, J36, a probe common, protective earth or AC neutral."],10)
    line(g,[(MARGIN,428),(RIGHT,428)],RULE,.8)
    heading(g,462,"Check the actual remote inputs",
            "A front-panel button label alone does not establish that an electronic keypad accepts dry contacts.")
    text(g,MARGIN,511,"Contact load",11,bold=True)
    paragraph(g,MARGIN,529,["Check voltage, current and inrush against the exact input and relay data. Omron's",
                            "G7SA low-level reliability reference is 1 mA at 5 V DC. A scanned keypad may run",
                            "well below this. Use a verified low-level interface when the contact load is unsuitable."],10)
    text(g,MARGIN,600,"START timing",11,bold=True)
    paragraph(g,MARGIN,618,["Use the OEM's documented pulse range. A contact can weld or a processor can stall.",
                           "An input that controls a starting capacitor directly needs a verified independent cutoff.",
                           "Do not connect an unverified button circuit to exercise the profile."],10)
    text(g,MARGIN,690,"Controller power loss",11,bold=True)
    paragraph(g,MARGIN,708,["A powerless controller cannot send a closure to STOP. A starter may remain latched.",
                           "Wire the independent guard on pages 4 and 5. Confirm the actual OEM off and release proofs.",
                           "Confirm local STOP priority and no unintended restart after supply restoration."],10)
    g.showPage()


def page_manual(g):
    title(g,"Manual transfer and position feedback",
          "Stop the pump, isolate every supply and verify absence of voltage before changing the service plug.",3)
    heading(g,148,"LOCAL MANUAL insert",
            "A mechanically exclusive plug removes both controller output branches from the starter.")
    text(g,MARGIN,197,"Open-to-stop DOL service socket",11,bold=True)
    text(g,MARGIN,214,"XC1 is the four-cavity dry command transfer.",9,tone=MUTED)
    for x,cavity,host in [(81,"1","B COM"),(133,"2","B NO"),(187,"3","A COM"),(240,"4","A NO")]:
        text(g,x-4,239,cavity,10,bold=True)
        terminal(g,x,249)
        text(g,x-15,284,host,8.5,tone=MUTED)
    line(g,[(187,252),(187,263),(240,263),(240,252)])
    text(g,280,238,"LOCAL insert",10,bold=True)
    paragraph(g,280,253,["1 and 2 open. START branch disconnected.",
                         "Insulated link only between cavities 3 and 4."],9.5,14)
    text(g,280,284,"Labels at left are corresponding HOST conductors.",8.5,tone=MUTED)
    paragraph(g,MARGIN,308,["The link restores the added permission section only. Original hardwired STOP, overload,",
                            "independent trips and START/holding branch remain in the starter's circuit."],10)
    text(g,MARGIN,355,"Maintained RUN and electronic close-to-stop layouts",11,bold=True)
    paragraph(g,MARGIN,375,["Use physically distinct LOCAL inserts with every added field conductor open. Keep the",
                            "RUN link or keypad common splice captive in its disconnected HOST harness. Confirm the",
                            "original buttons work locally. Mechanically exclude the DOL link from either layout."],10)
    line(g,[(MARGIN,432),(RIGHT,432)],RULE,.8)
    heading(g,463,"J36 keyed five-way plug  /  position and guard",
            "Fully seated plug position is reported by two electrically isolated, low-current auxiliary contacts.")
    x=197
    box(g,MARGIN,507,x-MARGIN,88)
    for yy,label in [(528,"J36.2    HOST"),(551,"J36.1    Logic GND"),(575,"J36.3    LOCAL")]:
        text(g,MARGIN+11,yy+3,label,10,bold=True);terminal(g,x,yy)
    for yy,name in [(528,"HOST position contact"),(575,"LOCAL position contact")]:
        line(g,[(x,yy),(248,yy)])
        terminal(g,248,yy);terminal(g,274,yy)
        line(g,[(248,yy),(271,yy-9)])
        line(g,[(274,yy),(315,yy),(315,551)])
        text(g,328,yy+3,name,9.5)
    line(g,[(x,551),(315,551)])
    terminal(g,315,551,filled=True)
    paragraph(g,MARGIN,626,["Each position contact closes to J36.1. HOST alone allows a fresh arm sequence.",
                           "LOCAL alone selects original starter control. Both or neither inhibits controller outputs.",
                           "J36.4 and J36.5 go to the isolated receiver on page 5. Use JST ZER-05V-S."],10)
    text(g,MARGIN,687,"Before returning to service",11,bold=True)
    paragraph(g,MARGIN,706,["Disable OEM automatic start/retry in LOCAL and verify it stays disabled after a power cycle.",
                           "Confirm a released STOP, an overload reset, a transfer or restoration of power cannot",
                           "start the pump unexpectedly. Verify every required independent high-level and dry-run",
                           "trip in the selected position. A disconnected controller cannot enforce a software trip."],10)
    g.showPage()


def page_guard(g):
    title(g, "Independent motor shutdown",
          "External cabinet hardware. All profiles and both service positions share these trips.", 4)
    heading(g, 146, "Guard inputs", "SR1 single-channel In2+. SR2 dual-channel In2- with cross-short detection. Both use rising-edge start.")
    box(g, MARGIN, 182, RIGHT-MARGIN, 98)
    paragraph(g, MARGIN+12, 204, [
        "SR1.S11  >  SG1.11-12  >  original STOP spare NC  >  overload spare NC  >  KV and KC NO",
        ">  independent high-high float NC  >  position branches below  >  SR1.S12 / S22.",
        "HOST: HOST seated + LOCAL released + both DD2503 window NOs + panel-stop relay NO.",
        "LOCAL: LOCAL seated + HOST released, with both OEM command pairs disconnected.",
    ], 9.5, 18)
    paragraph(g, MARGIN, 300, [
        "KV senses the protected motor supply before KS1/KS2. KC senses an independent OEM",
        "control supply if present. A qualified common-source arrangement uses one monitor.",
        "Main J1 and cabinet XT1 are fed upstream. Confirm worst-case brownout detection at the starter.",
    ], 9.7, 15)
    heading(g, 379, "Reset and deliberate enable", "SR1.S12 > RESET > S34. Reset alone leaves the motor feeder open.")
    box(g, MARGIN, 413, RIGHT-MARGIN, 117)
    paragraph(g, MARGIN+12, 436, [
        "Channel A: SR2.S11 > SR1.13-14 > [off proofs or SR2.33-34 RUN seal] > SR2.S12.",
        "Off proofs: both KS mirrors, three XF2.7/8 proofs (page 6), START release and",
        "in HOST both guided KCA/KCB NCs. LOCAL isolates both controller command pairs.",
        "Channel B: SR2.S21 > SR1.23-24 > SG1.21-22 > SR2.S22. No S12-S22 link on SR2.",
        "SR2.S12 > dedicated ENABLE momentary NO > SR2.S34. Keep all proofs off S34.",
    ], 9.5, 18)
    heading(g, 552, "Two series motor contactors", "Feed each coil from a different dry safety contact. Use contactors rated for the actual load.")
    paragraph(g, MARGIN, 598, [
        "Fused cabinet +24 V > SR2.13-14 > KS1.A1. Fused +24 V > SR2.23-24 > KS2.A1.",
        "Both A2 terminals return to cabinet 0 V. Route the protected motor feed as shown.",
    ], 9.7, 15)
    nodes = [(MARGIN, 114, "XM1 L after QISO1"), (184, 78, "KS1 NO"), (296, 78, "KS2 NO"),
             (410, RIGHT-410, "Whole OEM starter")]
    for i, (x, w, name) in enumerate(nodes):
        box(g, x, 646, w, 33)
        text(g, x+10, 667, name, 9.7, True)
        if i:
            prev_x, prev_w, _ = nodes[i-1]
            line(g, [(prev_x+prev_w,662), (x,662)])
    paragraph(g, MARGIN, 712, [
        "STOP and high-high drop both channels of SR2. One welded main contactor leaves",
        "the other available and its NC mirror blocks re-enable. Qualify release, anti-restart",
        "and the actual OEM start/stop behavior before connecting a motor.",
    ], 10, 15)
    g.showPage()


def page_signals(g):
    title(g, "Guard loom and command interfaces",
          "Cabinet 24 V, controller logic and the OEM button circuit are three separate wiring domains.", 5)
    heading(g, 151, "Main board to cabinet", "Use preterminated, keyed harnesses. Each arrow below identifies an electrical connection.")
    for y, label, details in [
        (195, "J30.1 / J30.2", "Fused +24 V to COM. NO to KCA1 coil 0 (+). Coil 1 to cabinet 0 V."),
        (231, "J35.1 / J35.2", "Fused +24 V to COM. NO to KCB1 coil 0 (+). Coil 1 to cabinet 0 V."),
        (267, "J36.1", "Floating receiver return and isolated position contacts common."),
        (303, "J36.2 / J36.3", "HOST / LOCAL full-seat dry contacts to J36.1 respectively."),
        (339, "J36.4", "3.3 V heartbeat to isolated HB receiver. Nominal 5 Hz."),
        (375, "J36.5", "5 V raw panel STOP return to separate isolated PANEL receiver."),
        (411, "J31.1 / J31.2", "KFB isolated gold NO, closed only with both KS picked up in HOST."),
    ]:
        box(g, MARGIN, y-18, RIGHT-MARGIN, 28)
        text(g, MARGIN+9, y, label, 10, True)
        text(g, 155, y, details, 9.5)
    heading(g, 475, "Cabinet receiver", "J36 connects only to floating low-voltage, high-impedance inputs.")
    paragraph(g, MARGIN, 518, [
        "Isolated 5 V > LM393B input comparators > individual optocouplers > cabinet PNP outputs.",
        "Heartbeat: isolated pulses to ifm DD2503.4. Both windows: FO=5, SP=5 Hz, HY=40%.",
        "HOST path through 13-14, link 14 to 19, then 19-20. Leave reset inputs 17/18 open.",
        "Panel: RX.J4.4 > KPS1 coil 0 (+). Coil 1 to cabinet 0 V. KPS1 NO permits HOST.",
        "Feedback: fused +24 V > KS1 NO > KS2 NO > separate HOST-seated NO > KFB coil.",
    ], 9.7, 18)
    heading(g, 652, "Commissioning hold", "The cabinet also needs the isolated receiver PCB and the external guard hardware.")
    paragraph(g, MARGIN, 695, [
        "Identify the exact OEM contacts and no-voltage-release behavior. Use the contact schedule,",
        "receiver components and power-return tests in hardware/starter-guard/README.rst.",
        "Confirm a held RESET or ENABLE cannot start after supply, mirror or command recovery.",
        "Verify the original STOP and high-high at the load while both controller contacts are held.",
    ], 9.7, 17)
    g.showPage()


def page_pickup_proof(g):
    title(g, "Starter neutral proof before enable",
          "Both HOST and LOCAL require proven open pickup wiring before the starter supply is restored.", 6)
    heading(g,150,"XF2.7 to XF2.8  /  three isolated contacts in series",
            "External cabinet 24 V proof circuit. Keep the OEM pickup wiring electrically separate.")
    line(g,[(MARGIN+5,233),(RIGHT-5,233)])
    for x, tag, status in [(78,"KOF1","Power stage off"),(234,"KHL1","Actual hold released"),(388,"KID1","Whole pickup open")]:
        box(g,x,205,129,55)
        text(g,x+8,227,tag,12,bold=True)
        text(g,x+8,247,status,9.1)
    terminal(g,MARGIN+5,233)
    terminal(g,RIGHT-5,233)
    text(g,MARGIN,280,"XF2.7",9,bold=True)
    text(g,RIGHT-25,280,"XF2.8",9,bold=True)
    heading(g,326,"Conventional holding circuit",
            "Trace every parallel START, holding and remote contact in the actual installed transfer position.")
    paragraph(g,MARGIN,369,[
        "KOF1 is the verified OEM stopped-state contact. KHL1 is the mechanically linked NC",
        "of the NO actually carrying the seal-in current. A compatible TeSys D / LADN11 is",
        "one example. Retire any former independent seal-in contact left across this pair.",
        "KID1 is the healthy NO from an independent, powered, isolated pickup-path monitor.",
        "It must detect a bridge across START while the OEM feeder is off and both buttons",
        "are released. XF2.9/10 separately checks the OEM START actuator release.",
    ],10,18)
    heading(g,514,"Electrical restart acceptance",
            "Use an isolated dummy load; keep the motor disconnected for fault injection.")
    paragraph(g,MARGIN,558,[
        "Trip the feeder. With both buttons released, test a welded holding NO and a bridge",
        "across the real START terminals separately, in both modes. Restore all supplies,",
        "RESET and press ENABLE. The two motor contactors and J31 must remain open.",
        "Verify the holding weld bars KHL1. A wire bridge tests KID1, even if KHL1 is healthy.",
        "Repeat with the monitor unpowered and its return open. Remove the fault, release",
        "ENABLE, then verify that a fresh ENABLE and subsequent new START are required.",
    ],10,18)
    paragraph(g,MARGIN,709,[
        "Page 7 shows one specific 24 V DC pilot interface. A keypad",
        "display, released button or mirror alone cannot establish command neutrality.",
        "Keep the profile disabled if the actual pickup circuit or retained demand is unobservable.",
    ],9.5,17)
    g.showPage()


def page_24v_pilot(g):
    title(g,"24 V DC DOL pilot example","Separate live SELV pilot. Motor feeder through KS1 and KS2. Do not apply to an AC coil or keypad.",7)
    heading(g,149,"Motor contactor pilot / four-wire DOL HOST profile",
            "P and D remain directly across the START and holding contacts in HOST and LOCAL.")
    box(g,42,224,77,30)
    text(g,47,243,"+24 / STOP / OL",8.2,True)
    line(g,[(119,238),(133,238),(133,322)])
    for yy,label in [(210,"OEM START NO"),(257,"Actual seal NO"),(302,"KCB NO / HOST")]:
        line(g,[(133,yy),(316,yy)])
        box(g,167,yy-12,111,24)
        text(g,175,yy+3,label,9,True)
    line(g,[(133,238),(133,210)])
    line(g,[(316,210),(316,322)])
    for xx,tag in [(133,"P  /  XP10.1"),(316,"D  /  XP10.2")]:
        terminal(g,xx,257,filled=True)
        text(g,xx-17,190,tag,9,True,tone=A_COLOR)
    line(g,[(316,257),(RIGHT,257)])
    box(g,330,243,78,28)
    text(g,337,260,"A1  coil  A2",9,True)
    box(g,418,232,104,50)
    text(g,423,251,"KCA NO in HOST",8.5,True)
    text(g,423,267,"Link in LOCAL",8.5)
    text(g,530,245,"0 V",8.5,True)
    line(g,[(133,322),(133,354),(316,354),(316,322)])
    box(g,153,339,144,31)
    text(g,159,359,"R40 - OC3 LED - R41",9,True)
    line(g,[(316,322),(531,322)])
    box(g,355,306,117,32)
    text(g,363,326,"R42  680R / 5 W",9.5,True)
    text(g,497,345,"Pilot 0 V",8.5)
    text(g,496,310,"XP10.3",8.5,True)
    heading(g,410,"Affirmative open-path sensing",
            "Optical isolation separates cabinet 24 V from the OEM pilot. See the native pilot sheet for each pin.")
    paragraph(g,MARGIN,451,[
        "R40 and R41 are 1.60 k, 1%, 0.6 W each. P to R40 to AQY212EH pin 1,",
        "pin 2 to R41 to D. D8 clamps reverse LED voltage. Shorting P to D removes LED drive;",
        "opening either sense lead does the same. R42 returns D to pilot 0 V even with KCA open.",
        "Cabinet fused +24 V to OC3.3; OC3.4 to KID1.A1; A2 to cabinet 0 V. R43 (2.20 k,",
        "1%, 1 W) shunts A1-A2. RE17RAMU function A, 1 s, Y1 open. Timed dry 15-18 goes",
        "in series with KOF1 and KHL1 as drawn on page 6. Check actual timing and wetting.",
    ],9.8,17)
    heading(g,587,"Preconditions and acceptance",
            "OEM pilot stays energized for supervision. Isolate and verify both supplies before servicing.")
    paragraph(g,MARGIN,631,[
        "Example coil LC1D09BD. Qualify 21.6-26.4 V pilot, coil resistance 70-150 ohms hot/cold.",
        "Fit KC1 RM17UBE16 on the pilot supply; KV1 RM17UBE15 monitors the 230 V motor feed.",
        "Open-to-stop coil permission is on the return. The LOCAL insert restores only that return",
        "and disconnects remote KCB. Test a P-D bridge with KCA open and with LOCAL selected.",
        "Check actual coil release, heating, supply loss, nuisance pickup and false idle. If the OEM",
        "seal stays picked after a trip, use original STOP to clear it before RESET / ENABLE.",
        "Other pilot voltages and electronic memory require separate, qualified proof hardware.",
    ],9.7,17)
    g.showPage()


def page_service(g):
    title(g,"USB service and field terminals",
          "Guarded service access and separate motor feeder. Qualify the finished cabinet on an isolated dummy load.",8)
    heading(g,148,"USB shutter  /  both transfer positions",
            "SG1 Omron D4NS-4BF, two direct-opening NC contacts, captive D4DS-K1 actuator.")
    for y,name,route in [
        (201,"XSG1.1 / .2","SR1.S11  >  SG1.11-12  >  original STOP spare NC"),
        (242,"XSG1.3 / .4","SR1.24  >  SG1.21-22  >  SR2.S22"),
    ]:
        box(g,MARGIN,y-20,RIGHT-MARGIN,31)
        text(g,MARGIN+10,y,name,10,True)
        text(g,164,y,route,10)
    paragraph(g,MARGIN,289,[
        "Open QISO1 upstream of XM1. It must isolate both motor conductors before it releases its",
        "unique transfer key. This key unlocks AL1 on the sole USB shutter. AL1 captures the key",
        "until the shutter is locked after cable removal. Keep PE continuous and logic powered separately.",
        "SG1 also drops KS1/KS2 in HOST and LOCAL. A plugged cable physically prevents closure.",
        "Test both QISO1 poles with both KS contacts held closed. Isolate all supplies for cabinet work.",
    ],10,17)
    heading(g,419,"Fixed terminals  /  power and pilot",
            "XM1 and XM2 use separate 32 A Phoenix UT 4 grey and blue DIN terminal pairs, covers and end stops.")
    for y,tag,links in [
        (462,"XM1.1 / .2","Motor L / N from QISO1 outputs. Both poles open with service key out."),
        (494,"XM2.1 / .2","Switched L from KS2 / N from QISO1. PE via separate continuous bar."),
        (526,"XT1.1 / .2","Protected always-on L / N for cabinet PSU PS2."),
        (558,"XP1.1 / .2","Independently protected OEM pilot source / return."),
        (590,"XC1.1 / .2 / .3 / .4","Dry B COM / B NO / A COM / A NO. Profile mapping on pages 1-3."),
        (622,"RX.J4.1 to .5","Receiver +24 V / 0 V / heartbeat / KPS1 drive / KFB1 drive."),
    ]:
        text(g,MARGIN,y,tag,9.5,True)
        text(g,166,y,links,9.4)
    heading(g,683,"Check at each relay socket",
            "G7SA-2A2B on P7SA-10F: KPS1, KCA1 and KCB1 require terminal 0 positive, 1 negative.")
    paragraph(g,MARGIN,730,[
        "D9, D4 and D5 are remote 1N4007 clamps at KPS1, KCA1 and KCB1 respectively.",
        "Band to socket terminal 0. Record measured pickup, release and feeder interruption times.",
    ],10,17)
    g.showPage()


def main():
    output=Path(__file__).parent/"exports"/"starter-wiring.pdf"
    output.parent.mkdir(exist_ok=True)
    g=Canvas(str(output),pagesize=A4,pageCompression=1,invariant=1)
    g.setTitle("Starter field wiring and manual transfer | Compact dual-output controller")
    g.setAuthor("Pump controller")
    page_maintained_four(g)
    page_three(g)
    page_manual(g)
    page_guard(g)
    page_signals(g)
    page_pickup_proof(g)
    page_24v_pilot(g)
    page_service(g)
    g.save()


if __name__=="__main__":
    main()
