"""Create the R4 1:1 mounting PDF from both native PCBs. Requires KiCad 10 pcbnew and ReportLab."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "hardware/main-integrated/pump-controller-integrated.kicad_pcb"
PANEL = ROOT / "hardware/panel-rev-f/pump-panel-rev-f.kicad_pcb"
PANEL_MECHANICS = PANEL.parent / "connector-mechanical-interface.json"


def extract(path):
    import pcbnew as k
    board = k.LoadBoard(str(path))
    poly = k.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(poly, False) and poly.OutlineCount() == 1
    def verts(chain):
        return [(k.ToMM(chain.CPoint(i).x), k.ToMM(chain.CPoint(i).y)) for i in range(chain.PointCount())]
    edge=verts(poly.Outline(0))
    x0, y0 = min(x for x,y in edge), min(y for x,y in edge)
    def local(x,y):
        return [round(x-x0,4),round(y-y0,4)]
    def xy(v):
        return local(k.ToMM(v.x),k.ToMM(v.y))
    def ring(chain):
        return [local(x,y) for x,y in verts(chain)]
    holes, ports, underside, tails = {}, {}, [], []
    main_height_parts = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        back = fp.GetLayer() == k.B_Cu
        if ref in {"U1","Y1"}:
            main_height_parts[ref] = "back" if back else "front"
        courtyard = fp.GetCourtyard(k.B_CrtYd if back else k.F_CrtYd)
        outlines = [ring(courtyard.Outline(i)) for i in range(courtyard.OutlineCount())]
        if not outlines:
            box = fp.GetBoundingBox(False,False)
            a,b = xy(box.GetOrigin()),xy(box.GetEnd())
            outlines = [[a,[b[0],a[1]],b,[a[0],b[1]]]]
        pads = list(fp.Pads())
        if ref.startswith("H") and "MountingHole" in fp.GetFPIDAsString():
            bore, = pads
            assert bore.GetAttribute() == k.PAD_ATTRIB_NPTH and bore.GetDrillSize().x == bore.GetDrillSize().y
            holes[ref] = [*xy(bore.GetPosition()), k.ToMM(bore.GetDrillSize().x)]
            continue
        if ref.startswith("J"):
            ports[ref] = dict(xy=xy(fp.GetPosition()), back=back, outlines=outlines)
        if back:
            underside.extend(outlines)
        for pad in pads:
            if pad.GetAttribute()==k.PAD_ATTRIB_PTH:
                size = pad.GetDrillSize()
                tails.append([*xy(pad.GetPosition()), k.ToMM(max(size.x,size.y))])
    return dict(sha=hashlib.sha256(path.read_bytes()).hexdigest(), origin=[x0,y0],
                outline=ring(poly.Outline(0)), cutouts=[ring(poly.Hole(0,i)) for i in range(poly.HoleCount(0))],
                size=[round(max(x for x,y in edge)-x0,4), round(max(y for x,y in edge)-y0,4)],
                thickness=k.ToMM(board.GetDesignSettings().GetBoardThickness()),holes=holes,
                ports=ports, underside=underside,tails=tails, main_height_parts=main_height_parts)


def draw(main,panel,mechanics,output):
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen.canvas import Canvas
    c=Canvas(str(output), pagesize=A4, invariant=1)
    c.setTitle("R4 board mounting templates and connector locations")
    c.setAuthor("Pump controller hardware")
    W,H=A4
    ink="#193742"; muted="#486168"; light="#b1c3c0"; teal="#006855"; orange="#a7531b"
    def txt(x,y,msg,size=8,bold=False,color=ink):
        c.setFont("Helvetica-Bold" if bold else "Helvetica",size)
        c.setFillColor(HexColor(color)); c.drawString(x*mm,H-y*mm,msg)
    def para(x,y,msg,span=177,size=9,step=5):
        line=""
        for word in msg.split():
            new=(line+" "+word).strip()
            if line and stringWidth(new,"Helvetica",size) > span*mm:
                txt(x,y,line,size,color=muted);y+=step;line=word
            else: line=new
        txt(x,y,line,size,color=muted)
        return y+step
    def line(x0,y0,x1,y1,color=light,width=.5):
        c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x0*mm,H-y0*mm,x1*mm,H-y1*mm)
    def ring(points,offset,col=ink,fill=None,weight=.5):
        c.setStrokeColor(HexColor(col)); c.setLineWidth(weight)
        if fill: c.setFillColor(HexColor(fill))
        path=c.beginPath()
        px,py=offset
        for i,(x,y) in enumerate(points):
            (path.moveTo if i==0 else path.lineTo)((px+x)*mm,H-(py+y)*mm)
        path.close();c.drawPath(path,stroke=1,fill=bool(fill))
    def circle(x,y,r,color,fill=False):
        c.setStrokeColor(HexColor(color));c.setFillColor(HexColor(color) if fill else white);c.setLineWidth(.5)
        c.circle(x*mm,H-y*mm,r*mm,stroke=1,fill=int(fill))
    def base(number,title,msg,board):
        txt(15,14,"PUMP CONTROLLER    /    MECHANICAL REFERENCE",8,True,teal)
        txt(15,26,title,21,True)
        para(15,34,msg,181,9,4.6)
        line(15,46,195,46)
        txt(15,281,"Print A4 at actual size (100%). The scale bar must measure 50.0 mm.",8,True)
        line(143,280,193,280,ink,1);line(143,278,143,282,ink,1);line(193,278,193,282,ink,1)
        txt(15,289,"PCB SHA-256  "+board["sha"],6.3,color=muted);txt(184,289,f"{number} / 3",7,True)
    def dimensions(board,ox,oy):
        w,h=board["size"]; d=7
        for x in (ox,ox+w): line(x,oy-d-1.5,x,oy-2)
        line(ox,oy-d,ox+w,oy-d)
        txt(ox+w/2-7,oy-d-2,f'{w:g} mm',8,True)
        for y in (oy,oy+h): line(ox-d-1.5,y,ox-2,y)
        line(ox-d,oy,ox-d,oy+h)
        c.saveState(); c.translate((ox-d-1.6)*mm,H-(oy+h/2+6)*mm);c.rotate(90)
        c.setFillColor(HexColor(ink));c.setFont("Helvetica-Bold",8);c.drawString(0,0,f"{h:g} mm");c.restoreState()
    def plan(board,ox,oy,rear=False):
        ring(board["outline"],(ox,oy),ink,"#fafcfb",.9)
        for points in board["cutouts"]: ring(points,(ox,oy),ink,"#ffffff")
        if rear:
            for pts in board["underside"]: ring(pts,(ox,oy),"#7b9294","#d7e1e0",.3)
            for x,y,drill in board["tails"]: circle(ox+x,oy+y,max(.22,drill/2),orange,True)
        else:
            for ref,port in sorted(board["ports"].items()):
                for pts in port["outlines"]: ring(pts,(ox,oy),teal,"#e0efeb",.5)
                x,y=port["xy"]; circle(ox+x,oy+y,.44,teal,True)
                pts=port["outlines"][0]; x=min(x for x,y in pts); y=max(y for x,y in pts)
                txt(ox+x,oy+y+2.6,ref,6,True,teal)
        for ref,(x,y,d) in board["holes"].items():
            x+=ox;y+=oy
            circle(x,y,d/2,ink);line(x-2.7,y,x+2.7,y,ink,.35);line(x,y-2.7,x,y+2.7,ink,.35)
            txt(x+2.2 if x-ox < board["size"][0]/2 else x-5.5,
                y+3 if y-oy < board["size"][1]/2 else y-2,ref,5.5,True)
        dimensions(board,ox,oy)
    def holes(board,x,y):
        txt(x,y,"Hole centres",11,True);y+=7
        txt(x,y,"REF       X          Y        BORE (mm)",6.8,True,muted);y+=5
        for ref,(ax,ay,d) in sorted(board["holes"].items()):
            txt(x,y,ref);txt(x+10,y,f"{ax:.2f}");txt(x+22,y,f"{ay:.2f}");txt(x+36,y,f"{d:.2f}");y+=5
        return y
    def ports(board,x,y,names):
        txt(x,y,"Connector origins",11,True);y+=7
        txt(x,y,"REF / FUNCTION",6.8,True,muted);txt(x+40,y,"X / Y (mm)",6.8,True,muted);y+=5
        for ref in sorted(board["ports"],key=lambda r:int(r[1:])):
            port=board["ports"][ref];ax,ay=port["xy"]
            txt(x,y,f"{ref}  {names.get(ref,'service')}",7.2,True);txt(x+40,y,f"{ax:g} / {ay:g}",7.2)
            y+=5.1
        return y
    orig=(23,67)
    w,h=main["size"]
    assert main["main_height_parts"] == {"U1":"front","Y1":"back"}, "Check vertical allowance references"
    if w>105 or h>134:
        raise ValueError("Board exceeds this actual-size sheet layout; adjust the drawing before issuing it.")
    base(1,"Main board mounting plan","Top view. X increases right and Y down from the upper-left corner of the board outline. Crosshairs locate the non-plated mounting holes. Green outlines show connector courtyards.",main)
    plan(main,*orig); holes(main,134,61); ports(main,134,111,{"J1":"AC supply","J2":"service","J10":"live CT","J20":"tank levels","J21":"inlet","J30":"command A","J32":"panel","J35":"command B","J40":"USB-C","J41":"target power","J52":"selector","J54":"cabinet I/O"})
    low=max(206,orig[1]+h+13)
    txt(15,low,"Using the template",13,True)
    y=para(15,low+8,"Coordinates use each header's KiCad footprint origin (green dot). The origin may differ from the plug mouth or pin 1. Use this sheet for supports and relative placement; size wall openings on the actual mated connectors.")
    y=para(15,y+4,"Use the specified insulating supports at every mounting hole. Provide strain relief and service room for the AC, mains-referenced CT and cabinet cables. Segregate them from the selector, panel and water-level wiring.")
    para(15,y+3,"J40 needs the matched positively isolated, trapped-key USB shutter. Keep access to its retaining fasteners, the key exchange and the cable obstruction independent of all other openings.")
    c.showPage()
    base(2,"Main board underside","X-ray view from the component side. Registration and hole positions match page 1. Grey shows rear component courtyards. Orange points mark plated through-hole lead locations on either face.",main)
    plan(main,*orig,rear=True)
    y=holes(main,134,61)+7
    txt(134,y,"Vertical clearances",11,True)
    y=para(134,y+7,f'Bare PCB thickness is {main["thickness"]:g} mm. Courtyards describe footprint space in the X-Y plane. Actual bodies, lead lengths, connector housings and cable bends determine the finished depth.',59,8.5,4.7)
    para(134,y+4,"Keep the populated underside and all leads clear of the mounting plate and guard. Reserve a service path for every removable plug and its latch.",59,8.5,4.7)
    txt(15,low,"Installed depth",13,True)
    y=para(15,low+8,"At each position add the measured underside projection and required clearance to the PCB thickness, top projection, cover clearance, mated connector and cable envelope. Include component, mounting and fabrication tolerances.")
    y=para(15,y+3,"J52 mates vertically. Provide overhead space for the harness and straight withdrawal. Reserve side access at J54 for the five-way cabinet harness. Keep the module antenna pigtail clear of metalwork and maintain its specified bend radius.")
    para(15,y+3,"The starter's available width, height and depth are unmeasured. Validate the complete R4 assembly, shutter travel, mains barriers and external DIN devices before drilling the cabinet or printing an enclosure.")
    c.showPage()
    assert panel["sha"]==mechanics["pcb_sha256"],"Stale panel-interface coordinates"
    base(3,"Five-button and OLED panel","Front view of the low-voltage panel. Rear connector locations are projected into this view. Orange marks the switch actuator centres; the shaded rectangle shows the nominal display module body.",panel)
    ox,oy=28,77; plan(panel,ox,oy)
    a,b,e,f=mechanics["oled_envelope_mm"]
    ring([(a,b),(e,b),(e,f),(a,f)],(ox,oy),"#507888","#e7f0f3")
    txt(ox+a+5,oy+b+7.5,"OLED MODULE",7,True)
    for name,(x,y) in mechanics["buttons_mm"].items():
        circle(ox+x,oy+y,.65,orange,True)
        txt(ox+x-3.2,oy+y-2.3,{"SET_RESET":"SET"}.get(name,name),5.3,True,orange)
    holes(panel,119,62)
    ports(panel,119,111,{"J1":"main J32","J2":"station","J7":"OLED","J8":"key"})
    txt(15,166,"Lid and harness fit",13,True)
    y=para(15,175,"Align the five actuators with their measured centres. The STOP microswitch uses a different plunger height and travel from START, MODE, SET/RESET and NEXT. Match the visible window to the purchased display's active area; the module rectangle includes its board.")
    y=para(15,y+4,"J1 connects to main J32. J7 is the plug-in OLED connection; J2 accepts the external button station and J8 accepts the optional maintained AUTO/MANUAL key. Route these low-voltage looms clear of the starter's mains, CT and capacitor circuits.")
    y=para(15,y+4,f'The current panel interface reserves {mechanics["rear_clearance_reservation_mm"]:g} mm behind the panel and limits support boss radius to {mechanics["max_support_boss_radius_mm"]:g} mm. Verify these design allowances with plugs fitted and the lid closed. Check free return, operating force and overtravel of every button.')
    para(15,y+4,"This sheet locates the panel separately from the main board. Side exits, the receiver relay, shutter and external cabinet hardware determine installation space for the whole controller.")
    c.showPage();c.save()


def write_note(main, panel, path):
    w,h=main["size"]
    pw,ph=panel["size"]
    table="\n".join(f"* **{name}** ({x:g}, {y:g}) mm, diameter {d:g} mm."
                    for name,(x,y,d) in sorted(main["holes"].items()))
    path.write_text(f"""Mounting the integrated main board and OLED panel
=================================================

The main PCB outline is **{w:g} × {h:g} mm**, with a nominal board thickness of
{main["thickness"]:g} mm. Panel F is **{pw:g} × {ph:g} × {panel["thickness"]:g} mm**. The
`1:1 mounting and connector drawing <exports/mounting-template.pdf>`_ contains
a main plan, its underside projected into the same view, and the OLED/button
panel plan. Print A4 at actual size and measure the 50 mm scale bar in each
print. Coordinates start at the upper-left corner of the board outline as
viewed from the component side. X increases right and Y increases down.

Main mounting centres
---------------------

{table}

Use the five M3 insulating supports on the main board and all four M2.5
mounts on panel F. Measure the installed dimensions
of both the screw heads and the support shoulders against adjacent copper
and component bodies. The drawing uses actual native hole bores, connector
origins, side-specific courtyards and plated through-hole lead locations.
Rear lead positions indicate possible protrusion. Circular symbols use the
larger of the two drill dimensions for a slotted hole. The copper insulation requirement also applies in
three dimensions to case walls, support hardware, nearby conductive parts
and tools. Derive required installation spacing from the cabinet environment.

Access in the starter
---------------------

Give the J54 side-entry five-way cabinet plug room to unlatch and withdraw.
The vertical J52 selector plug and J41 service connector need space above
the board. Route J10 and its strain relief in the mains-referenced wiring
area. J32 needs its own clear path to the twelve-position panel harness.
Keep the shielded USB-C entrance aligned with J40 after mounting the
populated board. Verify the actual mating cable, the captive-key isolator,
the two-channel shutter switch, full shutter travel and cable obstruction
in the finished enclosure. The radio module uses an external antenna;
include its cable, connector and the metal cabinet in the fit and RF check.

The existing enclosure, old hole pattern, wire openings and shutter case
coordinates were developed for other boards. The R4 installation needs its
own support positions, cable access, circuit barriers and shutter alignment.
For the front-side U1 converter, the manufacturer specifies 16.7 ±0.5 mm
body height. The underside Y1 package has a 4.2 mm drawing envelope. Allow
for these parts before adding solder height, seating and clearances. See the
`RECOM converter drawing <https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_
and `Abracon crystal drawing <https://abracon.com/Resonators/ABLS.pdf>`_.

The footprint-only XY drawing cannot establish the assembled Z envelope.
Measure the largest projection on each face (including lead ends), PCB
thickness, installed plugs, cable bends, insulation clearances and assembly
tolerances. Verify space to mate and withdraw every plug. The minimum
panel rear-space allowance and switch/OLED envelope come from the
`panel mechanical interface <../panel-rev-f/connector-mechanical-interface.json>`_.
Check each actuator against its actual purchased switch and check the display
window with the retained module. The two motor contactors, guard relays,
power supply, service isolator and terminal blocks also need cabinet space.
The starter dimensions, final installed depth and a complete enclosure
fit have not been measured.

Regenerate from the repository root with
``python3 tools/draw_integrated_mounting.py`` in a Python environment with
ReportLab. Set ``KICAD_PYTHON`` to a KiCad Python interpreter with pcbnew if
using a different KiCad installation.
""")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract",type=Path,help=argparse.SUPPRESS)
    parser.add_argument("--main",type=Path,default=MAIN)
    parser.add_argument("--output",type=Path,default=MAIN.parent/"exports/mounting-template.pdf")
    parser.add_argument("--note",type=Path,help="Output fit note; defaults beside the production project")
    args=parser.parse_args()
    if args.extract:
        print(json.dumps(extract(args.extract)))
        return
    engine=os.environ.get("KICAD_PYTHON") or str(ROOT/".tools/kicad-python")
    def geometry(board):
        return json.loads(subprocess.check_output([engine,str(Path(__file__).resolve()),"--extract",str(board)]))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    main_geometry, panel_geometry = geometry(args.main), geometry(PANEL)
    draw(main_geometry,panel_geometry,json.loads(PANEL_MECHANICS.read_text()),args.output)
    if args.note or args.main == MAIN and args.output == MAIN.parent/"exports/mounting-template.pdf":
        write_note(main_geometry,panel_geometry,args.note or MAIN.parent/"mounting.rst")


if __name__=="__main__":
    main()
