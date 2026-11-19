"""Export the R4 cabinet wiring guide. Requires ReportLab."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

DIR = Path(__file__).resolve().parents[1] / "hardware/starter-guard-r4"
W, H = A4
INK, SUB, TEAL, OCHRE = "#172f3c", "#455e68", "#006858", "#8b4406"


def tone(color):
    return colors.HexColor(color)


def label(g, x, y, value, size=10, bold=False, color=INK):
    g.setFillColor(tone(color))
    g.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    g.drawString(x, H-y, value)


def rule(g, x1, y1, x2, y2, color="#a1b2b5", weight=.7):
    g.setStrokeColor(tone(color))
    g.setLineWidth(weight)
    g.line(x1,H-y1,x2,H-y2)


def rect(g,x,y,w,h,stroke="#bdcecb",fill="#f4f8f7"):
    g.setStrokeColor(tone(stroke))
    g.setFillColor(tone(fill))
    g.roundRect(x,H-y-h,w,h,5,fill=1,stroke=1)


def words(g,x,y,value,w=510,size=10,height=15):
    line = ""
    for word in value.split():
        extended = (line+" "+word).strip()
        if line and stringWidth(extended,"Helvetica",size)>w:
            label(g,x,y,line,size,color=SUB)
            line = word
            y += height
        else:
            line=extended
    if line:
        label(g,x,y,line,size,color=SUB)
    return y+height


def header(g, number, title, description):
    label(g,42,43,"PUMP CONTROLLER    /    R4 FIELD WIRING",9,True,TEAL)
    label(g,42,80,title,23,True)
    words(g,42,102,description,512,10,14)
    rule(g,42,139,W-42,139)
    rule(g,42,795,W-42,795)
    label(g,42,812,"Engineering prototype    |    Field installation and measured trip tests pending",8,color=SUB)
    label(g,W-65,812,f"{number} / 3",8,True)


def row(g,y,left,right,height):
    label(g,49,y,left,10,True,TEAL)
    words(g,168,y,right,W-211,10,14)
    rule(g,44,y+height-13,W-44,y+height-13)


def chain(g,y,items):
    widths=[width for _,_,width in items]
    gap=13
    x=43
    for i,(title,desc,w) in enumerate(items):
        rect(g,x,y,w,48)
        label(g,x+7,y+18,title,9.5,True)
        label(g,x+7,y+34,desc,8.5,color=SUB)
        if i < len(widths)-1:
            xend=x+w+gap
            rule(g,x+w,y+24,xend-1,y+24,TEAL,1.2)
            rule(g,xend-5,y+21,xend-1,y+24,TEAL,1.1)
            rule(g,xend-5,y+27,xend-1,y+24,TEAL,1.1)
        x+=w+gap


def trip(g):
    header(g,1,"Independent pump shutdown",
           "The original STOP and the tank high-high float act directly on the cabinet. The main PCB and OLED/button PCB carry the operating controls.")
    label(g,43,168,"Protection loop in both transfer positions",14,True)
    chain(g,184,[("SG1","USB guard A",91),("S3 / S4","STOP / overload NC",116),("KV1 / KC1","Supply proofs",109),("LS1","High-high NC",148)])
    words(g,43,256,"These contacts are in series with SR1.S11. From the float, HOST continues through its transfer contacts, both WD1 outputs and KPS1. LOCAL continues through its separate seated/released contacts. Each branch returns to SR1.S12.",510)
    label(g,43,328,"Two separate trip outputs open the motor feeder",14,True)
    chain(g,344,[("SR1","Trip and RESET",110),("SR2","Two input channels",116),("KS1 / KS2","Separate coil drives",117),("Feeder","Series contacts",121)])
    words(g,43,418,"SR1 13-14 and 23-24 control SR2's two inputs. SR2 13-14 feeds KS1.A1 and 23-24 feeds KS2.A1. Both coil returns go to cabinet 0 V. S1 is the attended RESET; S2 is a separate ENABLE. Releasing a trip alone cannot re-arm the guard.")
    words(g,43,486,"Motor branch: QF1 to QISO1 to XM1. Protected line passes through KS1 then KS2 to XM2 and the existing starter. QISO1 also interrupts neutral. Terminate protective earth on its continuous bar. All sources that can power the pump must pass through the guards.")
    label(g,43,560,"Field contacts",14,True)
    row(g,586,"XF2.1 / .2","Mechanically linked NC auxiliary of original STOP S3. Keep the factory STOP in its original pilot circuit.",45)
    row(g,631,"XF2.3 / .4","Additional isolated NC auxiliary of the original overload S4.",40)
    row(g,671,"XF2.5 / .6","Independent float LS1 COM and NC. Measure continuity at normal level and confirm that it opens on rising water.",47)
    words(g,43,733,"One broken float core opens the loop. A short across its cores or a stuck float hides high water. Two welded power contacts can retain feeder power. Verify physical stopping time and overflow margin.",510,9.8,14)
    g.showPage()


def looms(g):
    header(g,2,"Main-board field connectors",
           "Cavity numbers refer to markings on the housings. Confirm pin 1 and continuity on each completed harness. J52 and J54 belong to separate electrical domains.")
    label(g,43,169,"J52    Transfer indication  /  JST PHR-3",14,True)
    row(g,198,"1   Logic GND","XF3.2 and XF3.4, common of the two isolated position contacts.",36)
    row(g,234,"2   HOST","XF3.1. The HOST-seated dry contact closes to J52.1.",36)
    row(g,270,"3   LOCAL","XF3.3. The LOCAL-seated dry contact closes to J52.1.",36)
    label(g,43,337,"J54    Cabinet supply and signals  /  JST VHR-5N",14,True)
    row(g,365,"1   Fused +24 V","F2 output. Supply to the cabinet-side receiver drivers.",34)
    row(g,399,"2   Cabinet 0 V","PS2 -V. Return for the 24 V signal circuits and KFB1 coil.",34)
    row(g,433,"3   HB output","Sourcing pulse output to WD1 terminal 4. WD1 terminals 1 and 2 take cabinet 0 V and F1-fused +24 V respectively.",48)
    row(g,481,"4   PANEL output","Sourcing drive to KPS1 terminal 0 (+). Terminal 1 returns to 0 V. D9 cathode goes to coil terminal 0.",48)
    row(g,529,"5   KFB input","From fused +24 V through KS1.13-14, KS2.13-14 and XF3.17-18. This energizes the onboard KFB1 coil in permitted HOST.",48)
    label(g,43,614,"J30 and J35    Dry commands",14,True)
    words(g,43,640,"For both plugs, cavity 1 is COM and takes F2 protected cabinet +24 V. Cavity 2 is NO. J30.2 drives interposer A (KCA1.0), J35.2 drives interposer B (KCB1.0). Each coil terminal 1 returns to cabinet 0 V. Wire D4/D5 at the coils, band toward terminal 0.")
    words(g,43,704,"J1 is the protected AC feed for the controller. J10 serves the specified CT on one motor conductor; its secondary belongs to the mains-referenced meter domain. The tank and inlet probe plugs are J20 and J21. Keep these looms separate from mains and feeder wiring.")
    g.showPage()


def profile(g):
    header(g,3,"Starter wiring and re-arm",
           "Use the manufacturer's approved remote connections for the installed starter. Qualify the actual coil voltage, dry input behavior, return paths and proof contacts before connecting motor power.")
    label(g,43,172,"Conventional DOL with independently powered 24 V DC pilot",14,True)
    chain(g,187,[("OEM pilot +","21.6-26.4 V DC",109),("Original STOP","Factory NC pole",111),("Overload","Factory NC pole",99),("P","Pickup common",145)])
    words(g,43,261,"Factory START NO, actual factory seal NO and the HOST interposer B NO each span P to D. D goes to the OEM coil A1. Coil A2 returns to pilot 0 V through interposer A in HOST or the dedicated return link in LOCAL. Leave B open in LOCAL. Keep the capacitor-start sequence intact.")
    words(g,43,335,"XF2.7/8 includes power stage off, actual holding contact released and independent open-command proof. XF2.9/10 verifies the original START is released. See the native pilot sheet for the specific optical proof and 70-150 ohm coil restriction.")
    label(g,43,412,"Electronic starter or maintained RUN input",14,True)
    words(g,43,436,"Electronic START/STOP uses A (XC1.3/4) and B (XC1.1/2) across their respective documented momentary inputs. Only a documented shared common permits a captive three-wire splice. A documented maintained RUN input uses A only. LOCAL opens all added commands in these profiles.")
    words(g,43,510,"Each profile needs an observable stopped power stage, cleared held demand and open command paths. A keypad button label alone does not establish dry-contact compatibility or an independent STOP auxiliary.")
    label(g,43,580,"Commissioning with the motor isolated",14,True)
    words(g,43,604,"Test both stops in HOST and LOCAL with command contacts held closed, controller supply lost and each guard contactor retained individually on a suitable test fixture. Verify opening a float wire trips. Confirm that releasing STOP, lowering the float and restoring any supply cannot restart the motor.")
    words(g,43,680,"For USB service, the unique key releases from two-pole QISO1 only when the motor branch is positively isolated; AL1 traps it while the USB shutter is open or a cable prevents closure. SG1 also interrupts two separate guard inputs. Isolate every supply separately for cabinet work.")
    g.showPage()


if __name__=="__main__":
    g=Canvas(str(DIR/"starter-wiring.pdf"),pagesize=A4,invariant=1)
    g.setTitle("R4 starter field wiring")
    g.setAuthor("Pump controller hardware")
    for page in (trip,looms,profile):
        page(g)
    g.save()
