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
    text(g,MARGIN,806,"COMPACT-DUAL  /  Field wiring review",8,tone=MUTED)
    text(g,RIGHT-48,806,f"{page} of 3",8,tone=MUTED)


def heading(g, y, name, detail):
    text(g,MARGIN,y,name,15,bold=True)
    text(g,MARGIN,y+17,detail,9.5,tone=MUTED)


def port_group(g, y, title_left="Controller harness"):
    start_y=y+26
    box(g,MARGIN,y+11,142,109)
    text(g,MARGIN,y+1,title_left,9,bold=True,tone=MUTED)
    labels=("J30.1    A COM", "J30.2    A NO", "J35.1    B COM", "J35.2    B NO")
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
          "Controller position. Use the harness and matching profile documented for the exact starter.",1)
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
    text(g,MARGIN,738,"Fit two Phoenix 1836079 plugs and two CP-MSTB 1734634 coding elements.",9,bold=True)
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
    paragraph(g,MARGIN,357,["The only common is the captive splice between J30.1 and J35.1 in this harness.",
                           "J30.2 operates START. J35.2 operates STOP. The main PCB keeps both pairs separate.",
                           "Keep both outputs within the same starter control system. Never join either contact",
                           "to controller ground, J36, a probe common, protective earth or AC neutral."],10)
    line(g,[(MARGIN,428),(RIGHT,428)],RULE,.8)
    heading(g,462,"Check the actual remote inputs",
            "A front-panel button label alone does not establish that an electronic keypad accepts dry contacts.")
    text(g,MARGIN,511,"Contact load",11,bold=True)
    paragraph(g,MARGIN,529,["Check voltage, current and inrush against the exact input and relay data. Omron's",
                            "G5Q low-level reliability reference is 10 mA at 5 V DC. A scanned keypad may run",
                            "well below this. Use a verified low-level interface when the contact load is unsuitable."],10)
    text(g,MARGIN,600,"START timing",11,bold=True)
    paragraph(g,MARGIN,618,["Use the OEM's documented pulse range. A contact can weld or a processor can stall.",
                           "An input that controls a starting capacitor directly needs a verified independent cutoff.",
                           "Do not connect an unverified button circuit to exercise the profile."],10)
    text(g,MARGIN,690,"Controller power loss",11,bold=True)
    paragraph(g,MARGIN,708,["A powerless controller cannot send a closure to STOP. A starter may remain latched.",
                           "Unattended use requires an independent verified inhibit or trip in this installation.",
                           "Confirm local STOP priority and no unintended restart after supply restoration."],10)
    g.showPage()


def page_manual(g):
    title(g,"Manual transfer and position feedback",
          "Stop the pump, isolate every supply and verify absence of voltage before changing the service plug.",3)
    heading(g,148,"LOCAL MANUAL insert",
            "A mechanically exclusive plug removes both controller output branches from the starter.")
    text(g,MARGIN,197,"Open-to-stop DOL service socket",11,bold=True)
    text(g,MARGIN,214,"Cavity numbers apply to this fixed adapter only.",9,tone=MUTED)
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
    heading(g,463,"J36 logic-side plug  /  separate three-wire cable",
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
                           "J36 mates with a separate JST GHR-03V-S housing. Keep all starter voltage off these pins."],10)
    text(g,MARGIN,687,"Before returning to service",11,bold=True)
    paragraph(g,MARGIN,706,["Disable OEM automatic start/retry in LOCAL and verify it stays disabled after a power cycle.",
                           "Confirm a released STOP, an overload reset, a transfer or restoration of power cannot",
                           "start the pump unexpectedly. Verify every required independent high-level and dry-run",
                           "trip in the selected position. A disconnected controller cannot enforce a software trip."],10)
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
    g.save()


if __name__=="__main__":
    main()
