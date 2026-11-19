"""Generate the two-layer receiver from the same parts and pin definitions as its cabinet."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import build_starter_guard as guard
import generate_cad as cad

OUT = cad.BASE / "hardware/guard-receiver"
P = "guard-receiver"
PCB = OUT/(P + ".kicad_pcb")
TMP = Path(os.getenv("TMPDIR", "/tmp"))/"pump-guard-rx-aligned"
WIDTH, HEIGHT = 68, 48
CLI = os.getenv("KICAD_CLI") or shutil.which("kicad-cli") or str(cad.BASE/".tools/kicad-cli")
ISO = {"ISO_0","ISO_5","HB_MON","PANEL_MON","HOST_LOGIC","LOCAL_LOGIC","J31_1","J31_2"}
ISO.update(prefix+"_"+suffix for prefix in ("HB","PANEL") for suffix in
           ("DIODE","IN","REF","GATE","LED_A","LED_K"))

def pcb_design():
    items = {p["ref"]:copy.deepcopy(p) for s in guard.make_design()["sheets"] for p in s["components"]}
    positions = {'J36': (10, 2, 0),
 'J2': (22.0, 3, 0),
 'J3': (32, 3.2, 0),
 'J4': (53.8, 31.7, 90),
 'J31': (8.65, 33, -90),
 'D1': (9.0, 11.5, 0),
 'D2': (9.0, 24.0, 0),
 'R11': (12.75, 11.25, 0),
 'R12': (16.0, 12.0, 90),
 'C3': (18.5, 12.0, 90),
 'R13': (12.75, 13.75, 0),
 'R14': (21.75, 13.0, 0),
 'R15': (24.8, 12.5, 90),
 'R16': (27.25, 12.5, 90),
 'Q1': (26.5, 8.65, 0),
 'R17': (30.0, 9.2, 90),
 'U2': (33.5, 10, 0),
 'U1': (19, 19, 0),
 'C1': (24.25, 16.8, 90),
 'C2': (26.75, 17.0, 90),
 'R21': (12.75, 24.0, 0),
 'R22': (16.0, 25.0, 90),
 'C4': (13.75, 20.75, 90),
 'R23': (17.0, 28.25, 0),
 'R24': (20.0, 25.75, 0),
 'R25': (24.0, 25.0, 90),
 'R26': (27.0, 25.0, 90),
 'Q2': (28.0, 21.0, 0),
 'R27': (31.45, 18.25, 90),
 'U3': (33.5, 22, 0),
 'R18': (44.5, 9.75, 0),
 'R19': (47.75, 8.0, 90),
 'Q3': (48.0, 13.0, 0),
 'R30': (50.05, 9.0, 90),
 'R28': (44.5, 21.75, 0),
 'R29': (44.75, 18.5, 90),
 'Q4': (48.0, 25.0, 0),
 'KFB1': (41.4, 35.5, -90),
 'D3': (51.1, 38.6, 90),
 'D6': (46.7, 37, 90),
 'D7': (47.5, 30.5, 180),
 'C5': (55.1, 42.25, 90),
 'C6': (55.1, 37, 90),
 'H1': (3, 3, 0),
 'H2': (65, 3, 0),
 'H3': (3, 45, 0),
 'H4': (65, 45, 0)}
    refs = [r for r in positions if r in items and r not in {"J31","J36","J2","J3","J4"}]
    def connector(ref,label,mpn,foot,nets):
        return guard.part(ref,label,mpn,[(i+1,n,n) for i,n in enumerate(nets)],footprint="Connector_"+foot)
    jst = "JST:JST_"
    connectors=[
        connector("J36","Logic loom","S05B-ZESK-2D(T)(LF)(SN)",jst+"ZE_S05B-ZESK-2D_1x05_P1.50mm_Horizontal",
                  ["ISO_0","HOST_LOGIC","LOCAL_LOGIC","HB_MON","PANEL_MON"]),
        connector("J2","Position aux","B3B-PH-K-S(LF)(SN)",jst+"PH_B3B-PH-K_1x03_P2.00mm_Vertical",
                  ["ISO_0","HOST_LOGIC","LOCAL_LOGIC"]),
        connector("J3","Floating 5 V","B2B-PH-K-S(LF)(SN)",jst+"PH_B2B-PH-K_1x02_P2.00mm_Vertical",["ISO_5","ISO_0"]),
        connector("J4","Cabinet 24 V I/O","S5P-VH(LF)(SN)",jst+"VH_S5P-VH_1x05_P3.96mm_Horizontal",
                  ["FUSED_24","CAB_0","HB_24","PANEL_24","KFB_A1"]),
        connector("J31","Guard feedback","1803277","Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal",
                  ["J31_1","J31_2"]),
    ]
    footprints={"U1":"Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "D1":"Package_TO_SOT_SMD:SOT-323_SC-70",
        "D2":"Package_TO_SOT_SMD:SOT-323_SC-70", "U2":"Package_DIP:DIP-4_W7.62mm",
        "U3":"Package_DIP:DIP-4_W7.62mm", "KFB1":"Relay_THT:Relay_DPDT_Omron_G5V-2",
        "D3":"Diode_SMD:D_SMA", "D6":"Diode_SMD:D_SMA", "D7":"Diode_SMD:D_SMB"}
    for r in ("Q1","Q2","Q3","Q4"):
        footprints[r]="Package_TO_SOT_SMD:SOT-23"
    components=[items[r] for r in refs]+connectors
    for i in range(1,5):
        components.append(guard.part(f"H{i}","M2.5 mount","2.7 mm NPTH",[],
                                     footprint="MountingHole:MountingHole_2.7mm_M2.5"))
    for c in components:
        r=c["ref"]
        if r in footprints:
            c["footprint"]=footprints[r]
        x,y,deg=positions[r]
        c["placement"]=dict(x=x,y=y,rotation=deg)
        if r in ("J3","J4"):
            for pin in c["pins"][:2]:
                pin["type"]="power_out"
    groups = [("receiver","Signal receiving and isolation",[c for c in components if c["ref"] in refs and
                  not (c["ref"] in ("D3","D6","D7","KFB1","Q3","Q4","C5","C6","R18","R19","R28","R29","R30"))]),
              ("cabinet","Cabinet 24 V drivers and feedback",[c for c in components if c["ref"] in
                  ("D3","D6","D7","KFB1","Q3","Q4","C5","C6","R18","R19","R28","R29","R30")]),
              ("plugs","Keyed harnesses and mounting",[c for c in components if c["ref"].startswith(("H","J"))])]
    assert sum(len(g[2]) for g in groups)==len(components)
    return dict(project=P,revision="GUARD-RX-A",title="Independent guard isolated receiver",board=dict(width=WIDTH,height=HEIGHT,layers=2),
                sheets=[dict(id=n,title=t,components=c) for n,t,c in groups])

def prepare():
    import pcbnew as k
    design=pcb_design()
    TMP.mkdir(parents=True,exist_ok=True)
    check=OUT/"checks"
    check.mkdir(exist_ok=True)
    cad.write_schematics(design,OUT,P)
    for path in OUT.glob("*.kicad_sch"):
        path.write_text(path.read_text().replace("GUARD-RX-A-DRAFT","GUARD-RX-A"))
    cad.write_bom(design,OUT)
    proj={"meta":{"filename":P+".kicad_pro","version":3},"net_settings":{"meta":{"version":3},"classes":[
        {"name":"Default","clearance":.23,"track_width":.28,"via_diameter":.85,"via_drill":.4}],
        "netclass_patterns":[]},
        "board":{"design_settings":{"rules":{"min_clearance":.22,"min_track_width":.25,
        "min_via_diameter":.8,"min_via_annular_width":.2,"min_through_hole_diameter":.3,"min_hole_clearance":.25,
        "min_hole_to_hole":.35,"min_copper_edge_clearance":.30,"min_text_height":1.0,"min_text_thickness":.153,
        "min_silk_clearance":.10}}}}
    (OUT/(P+".kicad_pro")).write_text(json.dumps(proj,indent=2)+"\n")
    expr=" || ".join("A.NetName == '"+key+"'" for key in sorted(ISO))
    # Name otherwise isolated no-connect pads: all unused KFB contact pads belong to the logic side.
    expr+=" || (A.NetName == 'unconnected-(KFB1-*') || (A.NetName == 'unconnected-(D?-*')"
    (OUT/(P+".kicad_dru")).write_text('(version 1)\n(rule "Separate logic and cabinet ELV domains"\n'
        +' (constraint clearance (min 2.5mm))\n (condition "('+expr+') != ('+expr.replace("A.","B.")+')"))\n')
    cad.make_board(design,OUT,P)
    # Only the footprints/board are released. Placement source lives in this file.
    (OUT/"placement.json").unlink(missing_ok=True)
    run("sch","erc","--format","json","--exit-code-violations","-o","checks/erc.json",P+".kicad_sch")
    run("sch","export","netlist","--format","kicadxml","-o","checks/source.xml",P+".kicad_sch")
    xml=ET.parse(check/"source.xml")
    for element in xml.findall(".//source")+xml.findall(".//uri"):
        if element.text:
            element.text=element.text.replace(str(OUT)+"/","")
    xml.write(check/"source.xml",encoding="utf-8",xml_declaration=True)
    nets={(n.get("ref"),n.get("pin")):net.get("name") for net in xml.findall(".//nets/net") for n in net.findall("node")}
    board=k.LoadBoard(str(PCB))
    title=k.TITLE_BLOCK();title.SetTitle("Isolated guard receiver");title.SetRevision("GUARD-RX-A");board.SetTitleBlock(title)
    catalog={c["ref"]:c for sheet in design["sheets"] for c in sheet["components"]}
    for fp in board.GetFootprints():
        c=catalog[fp.GetReference()]
        fp.SetField("Description",c["description"]);fp.GetField("Description").SetVisible(False)
        fp.SetAttributes(fp.GetAttributes() & ~k.FP_EXCLUDE_FROM_BOM)

        for pad in fp.Pads():
            name=nets.get((fp.GetReference(),pad.GetNumber()))
            if name and not pad.GetNetname():
                item=board.FindNet(name)
                if item is None or item.GetNetCode()<0:
                    item=k.NETINFO_ITEM(board,name);board.Add(item)
                pad.SetNet(item)
        ref=fp.Reference()
        ref.SetVisible(False)
        # Most KiCad library courtyard and silk geometry is already present.
        for a in fp.GraphicalItems():
            if a.GetLayer() in (k.F_SilkS,k.B_SilkS) and hasattr(a,"SetWidth"):
                a.SetWidth(k.FromMM(.16))
    # Uninterrupted isolation corridor under optocouplers and the wide-gap relay.
    zone=k.ZONE(board)
    zone.SetIsRuleArea(True)
    ls=k.LSET();ls.AddLayer(k.F_Cu);ls.AddLayer(k.B_Cu);zone.SetLayerSet(ls)
    zone.SetDoNotAllowTracks(True);zone.SetDoNotAllowVias(True);zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False)
    zone.SetZoneName("Logic to field separation")
    poly=zone.Outline();poly.NewOutline()
    for x,y in [(35.4,0),(38.5,0),(38.5,HEIGHT),(35.4,HEIGHT)]:
        poly.Append(k.FromMM(x),k.FromMM(y))
    board.Add(zone)
    # Position each label where its full bounding box clears every component.
    occupied=[fp.GetBoundingBox(False,False) for fp in board.GetFootprints()]
    def point(x,y):
        return k.VECTOR2I(k.FromMM(x),k.FromMM(y))
    def legend(value,x,y):
        t=k.PCB_TEXT(board);t.SetLayer(k.F_SilkS);t.SetText(value)
        t.SetTextSize(point(1.0,1.0));t.SetTextThickness(k.FromMM(.16))
        offsets=sorted((dx*dx+dy*dy,dx,dy) for dx in range(-40,41) for dy in range(-24,25))
        for _,dx,dy in offsets:
            t.SetPosition(point(x+dx*.5,y+dy*.5))
            dest=t.GetBoundingBox();dest.Inflate(k.FromMM(.4))
            if dest.GetLeft()<k.FromMM(.4) or dest.GetTop()<k.FromMM(.4) or dest.GetRight()>k.FromMM(WIDTH-.4) or dest.GetBottom()>k.FromMM(HEIGHT-.4):continue
            if all(not dest.Intersects(box) for box in occupied):
                occupied.append(dest);board.Add(t);return
        raise RuntimeError("No silk location for "+value)
    for t,x,y in [("J36 LOGIC",9,11),("J2 SEAT",21,8),("J3 +5 / 0",31,8),
                 ("J31 PERMIT",10,43),("J4 FIELD",62,10),("GUARD RX A",54,44)]:
        legend(t,x,y)
    board.GetDesignSettings().m_SolderMaskMargin=k.FromMM(.05)
    k.SaveBoard(str(PCB),board)
    if not k.ExportSpecctraDSN(board,str(TMP/"receiver.dsn")):
        raise RuntimeError("DSN export failed")
    dsn=TMP/"receiver.dsn"
    txt=dsn.read_text()
    txt=re.sub(r'\(clearance \d+ \(type smd_smd\)\)', '(clearance 230 (type smd_smd))',txt)
    txt=txt.replace("600:300_um","850:400_um").replace("(circle F.Cu 600)","(circle F.Cu 850)").replace("(circle B.Cu 600)","(circle B.Cu 850)")
    txt=txt.replace("(width 200)","(width 280)").replace("(clearance 200)","(clearance 250)")
    txt=txt.replace("(clearance 230 (type smd_smd))","(clearance 250 (type smd_smd))\n      (clearance 400 (type smd_via))\n      (clearance 330 (type wire_pin))\n      (clearance 500 (type via_pin))")
    txt=txt.replace('(structure' ,'(structure\n    (control (via_at_smd off))',1)
    dsn.write_text(txt)
    print(TMP/"receiver.dsn")

def run(*args):
    subprocess.run([CLI,*args],cwd=OUT,check=True)

def route(session):
    import pcbnew as k
    board=k.LoadBoard(str(PCB))
    if not k.ImportSpecctraSES(board,str(session)):
        raise RuntimeError("SES import failed")
    for track in board.GetTracks():
        if not isinstance(track,k.PCB_VIA) and track.GetWidth()<k.FromMM(.25):
            track.SetWidth(k.FromMM(.25))
    # Preserve 45-degree bends at the R14 gate escape after the minimum neck-width change.
    lane={(k.FromMM(23.5273),k.FromMM(13.3948)):(23.62,13.3021),
          (k.FromMM(23.5273),k.FromMM(13.8260)):(23.62,13.7333)}
    for t in board.GetTracks():
        if isinstance(t,k.PCB_VIA) or t.GetNetname()!="HB_GATE" or t.GetLayer()!=k.F_Cu:
            continue
        for get,set_endpoint in ((t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)):
            point=get()
            if (point.x,point.y) in lane:
                x,y=lane[point.x,point.y]
                set_endpoint(k.VECTOR2I(k.FromMM(x),k.FromMM(y)))
    # Restricted, independent return planes for the millivolt comparator and cabinet switching.
    for name,left,right in (("ISO_0",.45,35.4),("CAB_0",38.5,WIDTH-.45)):
        if any(existing.GetZoneName()==name+" return" for existing in board.Zones()):
            continue
        z=k.ZONE(board);z.SetLayer(k.B_Cu);z.SetNet(board.FindNet(name))
        z.SetZoneName(name+" return");z.SetLocalClearance(k.FromMM(.30));z.SetMinThickness(k.FromMM(.25))
        z.SetThermalReliefGap(k.FromMM(.30));z.SetThermalReliefSpokeWidth(k.FromMM(.35))
        z.Outline().NewOutline()
        for x,y in [(left,.45),(right,.45),(right,HEIGHT-.45),(left,HEIGHT-.45)]:
            z.Outline().Append(k.FromMM(x),k.FromMM(y))
        board.Add(z)
    for fp in board.GetFootprints():
        fp.SetLocalSolderMaskMargin(k.FromMM(.05))
    k.ZONE_FILLER(board).Fill(board.Zones())
    k.SaveBoard(str(PCB),board)

if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("step",choices=("prepare","import"))
    args.add_argument("--session",type=Path,default=OUT/(P+".ses"),
                      help="Reviewed router session. Defaults to the version stored beside the board.")
    options=args.parse_args()
    if options.step=="prepare":
        prepare()
    else:
        route(options.session)
