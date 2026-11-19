"""Generate the external-only receiver/cabinet schematic and compare the KiCad netlist."""
import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import generate_cad as cad

OUT = cad.BASE / "hardware/starter-guard"
PROJECT = "starter-guard"
OMRON = "https://assets.omron.eu/downloads/latest/datasheet/en/j120_g7sa_relays_with_forcibly_guided_contacts_datasheet_en.pdf"
FEEDER = "https://www.phoenixcontact.com/en-us/products/feed-through-terminal-block-ut-4-3044102"
TRAPPED_KEY = "https://fortress-safety.com/wp-content/uploads/2022/03/EN-mGard-Overview-Brochure-October-2021-v1.6-Digital-Version.pdf"
DOOR = "https://assets.omron.eu/downloads/latest/datasheet/en/d4ns_d4ns-sk_safety-door_switch_datasheet_en.pdf"
PILZ = "https://www.pilz.com/download/open/PNOZ_s4_Operat_Man_21396-EN-20.pdf"
TELEM = "https://www.se.com/id/en/product/RM17UBE15/"
MEANWELL = "https://www.meanwell.com/Upload/PDF/DDR-15/DDR-15-spec.pdf"
KFB_SHEET = "https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5v_2.pdf"
IFM = "https://media.ifm.com/dam/01a0a55a-bd11-7558-86be-c6ddfbef891d/Original/7390953_01_GB.pdf"
TE = "https://iportal.se.com/Contents/docs/SQD-LC1D09BD.PDF"

def part(ref, value, mpn, pins, description="", datasheet="", kind="ic", footprint=""):
    return dict(ref=ref, value=value, mpn=mpn, description=description, datasheet=datasheet,
                kind=kind, footprint=footprint, pins=[
                    dict(num=str(n), name=name, net=net, type=t[0] if t else "passive")
                    for n, name, net, *t in pins])

def passive(ref, value, a, b, kind="resistor"):
    if kind == "resistor":
        val = {"10k":"10K","115k":"115K","33k":"33K","4.7k":"4K7","100k":"100K","560R":"560R"}[value]
        mpn = "RC0805FR-07" + val + "L"
        footprint, desc = "Resistor_SMD:R_0805_2012Metric", "Yageo 1% 0805"
    else:
        mpn = {"10nF":"GRM21BR71H103KA01L","100nF":"GRM21BR71H104KA01L","1uF":"GRM21BR71C105KA01L"}[value]
        footprint, desc = "Capacitor_SMD:C_0805_2012Metric", "Murata X7R ceramic, nonpolar"
    return part(ref,value,mpn,[(1,"1",a),(2,"2",b)],desc,kind=kind,footprint=footprint)

def diode(ref, coil):
    if ref in ("D3","D6"):
        return part(ref,"S1M","S1M-E3/61T",[(1,"K",coil),(2,"A","CAB_0")],
                    "SMA suppression diode. Band to coil positive.", "https://www.vishay.com/docs/88711/s1a.pdf","diode")
    return part(ref,"1N4007","1N4007-E3/54",[(1,"K",coil),(2,"A","CAB_0")],
                "Band to coil positive","https://www.vishay.com/docs/88503/1n4001.pdf","diode")

def receiver():
    inputs = [
        part("PS1","ISOLATED 24V / 5V","DDR-15G-5",
             [("+Vi","Vin+","FUSED_24"),("-Vi","Vin-","CAB_0"),("+Vo","Vout+","ISO_5","power_out"),
              ("-Vo","Vout-","ISO_0","power_out")],"Separate floating 5 V supply, set to 5.0 V.",MEANWELL),
        part("J36","MAIN GUARD LOOM","ZER-05V-S",[(1,"ISO common","ISO_0"),
             (2,"HOST aux","HOST_LOGIC"),(3,"LOCAL aux","LOCAL_LOGIC"),
             (4,"HB via main R196","HB_MON"),(5,"PANEL via main R197","PANEL_MON")],
             "Cable end facing the existing main header.","https://www.jst.com/wp-content/uploads/2025/06/eZE.pdf"),
        part("U1","HB and PANEL comparators","LM393BDR",[(1,"OUT1","HB_GATE","open_collector"),
             (2,"IN1-","HB_REF","input"),(3,"IN1+","HB_IN","input"),(4,"GND","ISO_0","power_in"),
             (5,"IN2+","PANEL_IN","input"),(6,"IN2-","PANEL_REF","input"),
             (7,"OUT2","PANEL_GATE","open_collector"),(8,"VCC","ISO_5","power_in")],
             "TI dual comparator, SOIC-8.","https://www.ti.com/lit/ds/symlink/lm393b.pdf"),
        passive("C1","100nF","ISO_5","ISO_0","capacitor"),passive("C2","1uF","ISO_5","ISO_0","capacitor"),
    ]
    transfer = []
    for n, side in enumerate(("HB","PANEL"), 1):
        def net(s):
            return side + "_" + s
        def r(index,value,a,b):
            return passive(f"R{n}{index}",value,a,b)
        (inputs if n==1 else transfer).extend([
            part(f"D{n}","BAV199W blocking diode","BAV199W,115",
                 [(1,"A1",net("MON")),(3,"K1/A2",net("DIODE")),(2,"K2",None)],
                 "Use diode 1 only. SC-70 pin 2 open.","https://assets.nexperia.com/documents/data-sheet/BAV199W.pdf"),
            r(1,"10k",net("DIODE"),net("IN")),r(2,"10k",net("IN"),"ISO_0"),
            passive(f"C{n+2}","10nF",net("IN"),"ISO_0","capacitor"),
            r(3,"115k" if n==1 else "33k","ISO_5",net("REF")),r(4,"10k",net("REF"),"ISO_0"),
            r(5,"4.7k","ISO_5",net("GATE")),r(6,"100k",net("GATE"),"ISO_0"),
            part(f"Q{n}","2N7002 / optical LED driver","2N7002,215",[(1,"G",net("GATE")),
                 (2,"S","ISO_0"),(3,"D",net("LED_K"))],"Nexperia SOT-23","https://assets.nexperia.com/documents/data-sheet/2N7002.pdf"),
            r(7,"560R","ISO_5",net("LED_A")),
            part(f"U{n+1}","VO617A-3 / isolation","VO617A-3",[(1,"A",net("LED_A")),
                 (2,"K",net("LED_K")),(3,"E","CAB_0"),(4,"C",net("OPTO_C"))],
                 "Phototransistor DIP-4. Keep galvanic domains separate.","https://www.vishay.com/docs/83430/vo617a.pdf"),
            r(8,"10k",net("OPTO_C"),net("BASE")),r(9,"10k",net("BASE"),"FUSED_24"),
            part(f"Q{n+2}","BC807-40 / 24V driver","BC807-40,215",[(1,"B",net("BASE")),
                 (2,"E","FUSED_24"),(3,"C",net("24"))],"Nexperia SOT-23","https://assets.nexperia.com/documents/data-sheet/BC807_SER.pdf"),
        ])
    transfer.extend([
        passive("C5","100nF","FUSED_24","CAB_0","capacitor"),
        part("C6","4.7uF / 50V","GRM32ER71H475KA88L",[(1,"1","FUSED_24"),(2,"2","CAB_0")],
             "Murata X7R ceramic 1210; nonpolar.",kind="capacitor",footprint="Capacitor_SMD:C_1210_3225Metric"),
        part("D7","24V SELV transient clamp","SMBJ26A-E3/52",[(1,"K","FUSED_24"),(2,"A","CAB_0")],
             "Unidirectional 26 V TVS, use a regulated 24 V rail.", "https://www.vishay.com/docs/88392/smbj.pdf","diode"),
    ])
    inputs.append(passive("R30","10k","HB_24","CAB_0"))
    return inputs, transfer

def field(contacts_file=OUT/"contacts.csv"):
    # Every contact carries the exact two wire labels from the continuity solver.
    with contacts_file.open(newline="") as f:
        contacts = {(r["circuit"], r["conducts_when"]):(r["from"].replace(".","_"),r["to"].replace(".","_"))
                    for r in csv.DictReader(f)}
    def switch(group,name,a,b):
        left,right=contacts[group,name]
        # Terminal IDs carry the manufacturer numbering. Keep contact labels short.
        label = {"OEM_STOP_RELEASED":"STOP NC", "OVERLOAD_HEALTHY":"OL NC", "FLOAT_NC":"Float NC",
                 "KV_IN_RANGE_NO":"KV NO", "KC_IN_RANGE_NO":"KC NO", "PANEL_RELAY_NO":"Panel NO",
                 "OEM_START_RELEASED":"Start NC", "KCA_GUIDED_NC":"Cmd A NC", "KCB_GUIDED_NC":"Cmd B NC",
                 "OEM_OFF_PROOF":"Stopped NC","OEM_HOLD_RELEASED":"Seal NC","OEM_COMMAND_PATH_OPEN":"Idle proof NO","HB_WINDOW_1_NO":"Window1 NO","HB_WINDOW_2_NO":"Window2 NO","ENABLE_PRESSED":"Enable NO",
                 "RESET_PRESSED":"Reset NO"}.get(name,name)
        return [(a,label,left),(b,label,right)]
    def chain(name,a,b):
        return switch("SR1_INPUT",name,a,b)
    def proofs(name,a,b):
        return switch("SR2_INPUT",name,a,b)
    def coils(ref):
        return [("A1","24V coil",ref+"_A1"),("A2","0V coil","CAB_0")]
    def source_monitor(ref,name,circuit,inputs):
        return part(ref,name,circuit,[(a,a,n) for a,n in inputs]+chain(name,11,14)+[(12,"NC",None)],
                    "Dry NO closed only in range; select exact source and timing for installation.",
                    TELEM if circuit=="RM17UBE15" else "https://www.se.com/ww/en/product/RM17UBE16/")
    def guided(ref,value,coil,contacts):
        return part(ref,value,"G7SA-2A2B DC24 / P7SA-10F",
                    [(0,"Coil +",coil),(1,"Coil -","CAB_0")]+contacts,
                    "Non-LED terminal base. 33-34 NO, 11-12 NC. Other contacts unused.",OMRON)
    instruments=[
        part("PS2","Cabinet isolated 24V / 2.5A","HDR-60-24",
             [("L","Protected supply L","CAB_SUPPLY_L"),("N","Supply return","CAB_SUPPLY_N"),
              ("+V","24V DC","CAB_24_RAW","power_out"),("-V","Return","CAB_0","power_out")],
             "Separate always-on supply. Qualify DC inrush, protection and cabinet temperature.",
             "https://www.meanwell.com/Upload/PDF/HDR-60/HDR-60-SPEC.PDF"),
        part("F2","Cabinet DC distribution protection","Site-selected DC branch protection",
             [(1,"Input","CAB_24_RAW"),(2,"Output","FUSED_24")],
             "Select for available fault energy, wire capacity and actual coil loads.",kind="fuse"),
        part("XT1","Cabinet supply input","Fixed protected supply terminals",
             [(1,"Cabinet L","CAB_SUPPLY_L"),(2,"Cabinet N","CAB_SUPPLY_N")]),
        part("XM1","Protected motor feed IN","Phoenix UT 4 3044102 + UT 4 BU 3044115",
             [(1,"Upstream L","PROTECTED_LINE"),(2,"Upstream N","MOTOR_RETURN")],
             "Protected motor branch upstream of both contactors. Keep separate from all pilot and control connectors. D-UT 3047028 end covers and rail end stops.",FEEDER),
        part("XP1","OEM pilot supply","Separate fixed pilot terminals",
             [(1,"Pilot source","OEM_CTRL_L"),(2,"Pilot return","OEM_CTRL_N")],
             "Monitored OEM pilot source, separately protected and upstream of the pilot STOP."),
        part("XF2","OEM and float contacts","Profile-specific field loom",
             [(1,"OEM STOP aux NC in","AFTER_USB_A"),(2,"OEM STOP aux NC out","AFTER_STOP"),
              (3,"Overload aux NC in","AFTER_STOP"),(4,"Overload aux NC out","AFTER_OL"),
              (5,"Independent float NC in","ALL_SUPPLIES_OK"),(6,"Independent float NC out","AFTER_HH"),
              (7,"OEM proofs in","EDM2"),(8,"OEM proofs out","OEM_IDLE"),
              (9,"OEM START released in","OEM_IDLE"),(10,"OEM START released out","START_IDLE")],
             "Use OEM-approved isolated auxiliaries. All pairs open on fault."),
        part("LS1","Independent NC high-high float","SJE 1062686 MilliAmpMaster WPS",
             chain("FLOAT_NC","COM","NC")+[("NO","Unused",None)],
             "Use COM/NC that opens on rising water at XF2.5/6. Verify with the assembled float.",
             "https://www.sjerhombus.com/wp-content/uploads/2020/05/9500460A-MilliAmpMaster-WPS.pdf"),
        part("S3","Original STOP / spare NC","Match installed OEM actuator",
             chain("OEM_STOP_RELEASED",11,12),"Linked isolated NC accessory, proof independently at original STOP."),
        part("S4","OEM overload / spare NC","Match installed OEM overload",
             chain("OVERLOAD_HEALTHY","C","NC"),"Additional isolated NC, keep original overload circuit intact."),
        part("S5","OEM START release proof","Match installed OEM actuator",
             proofs("OEM_START_RELEASED","C","NC"),"Additional isolated NC, open while original START is held."),
        part("KOF1","OEM power stage off","LC1D09BD / verified OEM equivalent",
             proofs("OEM_OFF_PROOF",21,22),"External stopped-state contact, one of three proofs on XF2.7/8."),
        part("KHL1","Actual hold contact released","LADN11 on compatible TeSys D or verified OEM equivalent",
             proofs("OEM_HOLD_RELEASED",61,62) + [(53,"Linked seal NO","PILOT_P"),(54,"Linked seal NO","PILOT_D")],"For a DOL use the linked NC of the actual NO holding pair. "
             "For an electronic starter use independently verified latched-demand-clear feedback.",
             "https://www.se.com/ca/en/faqs/FA115177/"),
        source_monitor("KV1","KV_IN_RANGE_NO","RM17UBE15",[("A1","PROTECTED_LINE"),("A2","MOTOR_RETURN")]),
        source_monitor("KC1","KC_IN_RANGE_NO","RM17UBE16",[("A1","OEM_CTRL_L"),("A2","OEM_CTRL_N")]),
        part("F1","315 mA time-lag","Littelfuse 0218.315MXP",[(1,"1","FUSED_24"),(2,"2","HB_24_FUSED")],
             "5 x 20 mm DD2503 L+ branch, 315 mA time-lag",kind="fuse"),
        part("WD1","DD2503 / 3 to 7 Hz","DD2503",[
             (1,"DC L-","CAB_0"),(2,"DC L+","HB_24_FUSED"),(4,"PNP input","HB_24"),
             (17,"Reset 1",None),(18,"Reset 2",None)]
             +chain("HB_WINDOW_1_NO",13,14)+chain("HB_WINDOW_2_NO",19,20)
             +[(15,"NC 1",None),(21,"NC 2",None)],
             "Two series NOs, FO1/2=5, SP1/2=5 Hz, HY1/2=40%. ST, DT, FT, SO=0. Reset pins open. See heartbeat-window.json.",IFM),
        guided("KPS1","PANEL healthy","PANEL_24",chain("PANEL_RELAY_NO",33,34)),diode("D3","PANEL_24"),
        diode("D9","PANEL_24"),  # At remote KPS1. D3 stays at the receiver driver.
        part("XF3","Transfer pole pairs","Profile-matched service socket auxiliaries",
             [(1,"Host position","HOST_LOGIC"),(2,"Host common","ISO_0"),(3,"Local position","LOCAL_LOGIC"),(4,"Local common","ISO_0")]
             +chain("H_SEATED",5,6)+chain("L_RELEASED",7,8)+chain("L_SEATED",9,10)+chain("H_RELEASED",11,12)
             +proofs("H_SEATED",13,14)+proofs("L_SEATED",15,16)+switch("HOST_FEEDBACK","H_SEATED",17,18),
             "Separate isolated dry poles; all seat-dependent contacts mechanically linked to the exclusive transfer."),
        part("S1","Momentary service RESET","Harmony XB5AA31",switch("SR1_RESET","RESET_PRESSED",13,14)),
        part("S2","Momentary guard ENABLE","Harmony XB5AA61",switch("SR2_ENABLE","ENABLE_PRESSED",13,14)),
    ]
    interlock = [
        part("QF1","Protected motor branch source","Installed upstream motor branch protection",
             [("L-OUT","Branch L","BRANCH_LINE"),("N","Branch neutral","BRANCH_NEUTRAL")],
             "Load-side connection schedule only. N is a supply neutral from the same protected branch. Verify protective device and short-circuit coordination on site."),
        part("QISO1","Key-trapped motor disconnector","Motor-rated 2-pole disconnector + Fortress mGard bolt interlock",
             switch("OEM_FEED","ISOLATOR_L","L-IN","L-OUT")+switch("OEM_RETURN","ISOLATOR_N","N-IN","N-OUT"),
             "Functional terminal IDs; match the approved disconnector drawing. Key captured ON, releasable only with both poles positively isolated OFF. Upstream of XM1. PE never switched.",TRAPPED_KEY),
        part("AL1","USB shutter access lock","Factory-matched Fortress mGard single-door interlock",
             [],"Mechanical, no electrical terminals. Same unique key as QISO1. Captures the key until the shutter is closed, bolted and verified to exclude an inserted cable.",TRAPPED_KEY),
        part("SG1","USB access interlock","D4NS-4BF with captive D4DS-K1",
             chain("USB_COVER_A",11,12)+switch("SR2_INPUT_B","USB_COVER_B",21,22),
             "Two direct-opening contacts. The fixed switch and captive tongue must open before the USB socket can be reached.",DOOR),
        part("XSG1","USB shutter contacts","Dedicated four-terminal field loom",
             [(1,"SG1.11 / A out","SR1_S11"),(2,"SG1.12 / A back","AFTER_USB_A"),
              (3,"SG1.21 / B out","SECOND_STAGE"),(4,"SG1.22 / B back","SR2_S22")],
             "Four distinct insulated cores. Keep both positive-opening contacts independent. Do not use cable shield as a return."),
    ]
    outputs=[
        part("SR1","Trip and monitored RESET","750104",[("A1","24V","FUSED_24"),("A2","0V","CAB_0"),
             ("S11","Input feed","SR1_S11"),("S12","Input return","SR1_S12"),("S22","Single-channel jumper","SR1_S12"),
             ("S34","Reset","SR1_S34")]+proofs("SR1_13_14",13,14)
             +switch("SR2_INPUT_B","SR1_23_24",23,24),"PNOZ s4, single-channel input, monitored rising edge",PILZ),
        part("SR2","Run gate and monitored ENABLE","750104",[("A1","24V","FUSED_24"),("A2","0V","CAB_0"),
             ("S11","Channel A feed","SR2_S11"),("S12","Channel A return","SR2_S12"),
             ("S21","Channel B feed","SR2_S21"),("S22","Channel B return","SR2_S22"),
             ("S34","Enable","SR2_S34")]+switch("KS1_COIL","SR2_13_14",13,14)+switch("KS2_COIL","SR2_23_24",23,24)
             +proofs("SR2_33_34",33,34),"PNOZ s4, dual channel with cross-short detection, monitored rising edge. No S12-S22 bridge.",PILZ),
        part("J30","Main command A","1836079",[(1,"COM","FUSED_24"),(2,"NO","KCA_COIL")]),
        part("J35","Main command B","1836079",[(1,"COM","FUSED_24"),(2,"NO","KCB_COIL")]),
        guided("KCA1","Command interposer A","KCA_COIL",proofs("KCA_GUIDED_NC",11,12)+[(33,"NO common","A_COM"),(34,"NO output","A_NO")]),
        guided("KCB1","Command interposer B","KCB_COIL",proofs("KCB_GUIDED_NC",11,12)+[(33,"NO common","B_COM"),(34,"NO output","B_NO")]),
        diode("D4","KCA_COIL"),diode("D5","KCB_COIL"),
        part("XC1","Four dry OEM commands","Four-pole keyed control transfer",
             [(1,"B COM","B_COM"),(2,"B NO","B_NO"),(3,"A COM","A_COM"),(4,"A NO","A_NO")],
             "DOL LOCAL restores only the added A permission via 3-4. See profile-specific field drawing."),
        part("XM2","Switched motor feed OUT","Phoenix UT 4 3044102 + UT 4 BU 3044115",
             [(1,"Switched L","OEM_LINE"),(2,"Motor N","MOTOR_RETURN")],
             "Physically separate from XC1 and RX.J4. Motor power terminals only. Maintain a separate continuous protective-earth bar. D-UT 3047028 end covers and rail end stops.",FEEDER),
    ]
    for n in (1,2):
        ref=f"KS{n}"
        outputs.append(part(ref,"Motor isolation contactor","LC1D09BD",coils(ref)
            +proofs(ref+"_MIRROR_NC",21,22)+switch("HOST_FEEDBACK",ref+"_AUX_NO",13,14)
            +switch("OEM_FEED",ref+"_MAIN_NO","1L1","2T1"),
            "Representative protected line shown; qualify pole usage and whole starter for the installation.",TE))
    outputs.extend([
        part("KFB1","HOST guard feedback","G5V-2-H1 DC24",[(1,"Coil +","KFB_A1"),(16,"Coil -","CAB_0"),
             (4,"COM","J31_1"),(8,"NO","J31_2"),(6,"NC",None),(9,"NO2",None),(13,"COM2",None),(11,"NC2",None)],
             "Omron single-side stable, isolated bifurcated gold-alloy NO.",KFB_SHEET),
        diode("D6","KFB_A1"),
        part("J31","Main guard feedback plug","1803578",[(1,"STOP_RETURN","J31_1"),(2,"K1 coil +","J31_2")]),
    ])
    return instruments,outputs,interlock

def pilot_profile():
    # The field adapter applies only to the illustrated conventional 24 V DC pilot.
    def resistor(ref,value,mpn,front,back):
        return part(ref,value,mpn,[(1,"1",front),(2,"2",back)],"24 V pilot field adapter.",kind="resistor")
    return [
        part("XP10","24 VDC pilot pickup taps","Shrouded low-voltage terminals",
             [(1,"P after STOP / OL","PILOT_P"),(2,"D OEM coil A1","PILOT_D"),(3,"Pilot 0V","OEM_CTRL_N")],
             "KS1/KS2 interrupt all motor energy; SELV pilot stays powered. See field wiring p7."),
        resistor("R40","1.60k 1% 0.6W","1.60 kOhm 1% 0.6 W flameproof","PILOT_P","OPT_SENSE_A"),
        resistor("R41","1.60k 1% 0.6W","1.60 kOhm 1% 0.6 W flameproof","OPT_SENSE_K","PILOT_D"),
        resistor("R42","680R 1% 5W","680 Ohm 1% 5 W flameproof","PILOT_D","OEM_CTRL_N"),
        part("OC3","Open START / hold detector","AQY212EH",[(1,"LED A","OPT_SENSE_A"),(2,"LED K","OPT_SENSE_K"),
             (3,"NO output","FUSED_24"),(4,"NO output","ID_TIMER_24")],
             "Positive differential pickup proof. Isolated cabinet supply and pilot circuits.",
             "https://industry.panasonic.com/ap/en/products/control/relay/photomos/number/aqy212eh"),
        part("D8","1N4148 reverse LED clamp","1N4148",[(1,"Cathode","OPT_SENSE_A"),(2,"Anode","OPT_SENSE_K")],
             "Reverse protection across OC3 LED, band to pin 1.",kind="diode"),
        resistor("R43","2.20k 1% 1W","2.20 kOhm 1% 1 W flameproof","ID_TIMER_24","CAB_0"),
        part("KID1","Timed pickup-open proof","RE17RAMU",[("A1","Timed supply +","ID_TIMER_24"),
             ("A2","Supply return","CAB_0"),("Y1","Unused",None),(15,"Proof common","OEM_HOLD_OPEN"),
             (18,"Timed healthy NO","OEM_IDLE"),(16,"NC",None)],"24 V profile; function A 1 s. Validate actual times. "
             "Other OEM profiles need independently qualified open-command proof at this interface.",
             "https://iportal.se.com/Contents/docs/SQD-RE17RAMU.PDF"),
    ]

def make_design():
    inputs, transfer = receiver()
    instruments, outputs, interlock = field()
    definitions=[
        ("heartbeat", "Heartbeat receiver and common supplies", inputs),
        ("panel", "Panel STOP receiver and 24 V driver", transfer),
        ("field", "Guard inputs and position contacts", instruments),
        ("outputs", "Reset, enable and series contactors", outputs),
        ("pilot", "24 V DC conventional DOL pilot adapter only", pilot_profile()),
        ("service", "USB programming access and hardwired trip channels", interlock),
    ]
    return dict(project=PROJECT, revision="R3", title="Independent cabinet starter guard",
                sheets=[dict(id=n,title=t,components=c) for n,t,c in definitions])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="Run KiCad ERC, export PDF/netlist and compare pins.")
    args=parser.parse_args()
    design=make_design()
    cad.write_schematics(design,OUT,PROJECT)
    cad.write_bom(design,OUT)
    if not args.check:
        return
    cli=os.getenv("KICAD_CLI") or shutil.which("kicad-cli") or str(cad.BASE/".tools/kicad-cli")
    project=PROJECT+".kicad_sch"
    checks=OUT/"checks"
    checks.mkdir(exist_ok=True)
    def run(*args):
        subprocess.run([cli,*args],cwd=OUT,check=True)
    run("sch","erc","--format","json","--severity-all","--exit-code-violations","-o","checks/erc.json",project)
    run("sch","export","netlist","--format","kicadxml","-o","checks/guard-netlist.xml",project)
    run("sch","export","pdf","-o","guard-schematic.pdf",project)
    cad.validate_netlist(design,checks/"guard-netlist.xml")
    xml=ET.parse(checks/"guard-netlist.xml")
    domain_nets = {n.get("name") for n in xml.findall(".//nets/net")}
    assert {"ISO_0","CAB_0","ISO_5","FUSED_24"}<=domain_nets
    # Keep ERC records portable. The KiCad netlist preserves hierarchy, symbols and pin names.
    for xml_element in xml.findall(".//source") + xml.findall(".//uri"):
        if xml_element.text and str(OUT) in xml_element.text:
            xml_element.text=xml_element.text.replace(str(OUT)+"/","")
    xml.write(checks/"guard-netlist.xml",encoding="utf-8",xml_declaration=True)
    erc=json.loads((checks/"erc.json").read_text())
    for sheet in erc.get("sheets",[]):
        if "source" in sheet:
            sheet["source"]=Path(sheet["source"]).name
    (checks/"erc.json").write_text(json.dumps(erc,indent=2)+"\n")

if __name__ == "__main__":
    main()
