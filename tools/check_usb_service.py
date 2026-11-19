"""Check USB programming and motor permission using KiCad-exported nets and actual PCB pads."""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

from measure_usb_service_routes import measure as measure_routes

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "hardware/main-compact-dual/pump-controller-compact.kicad_sch"
PANEL = ROOT / "hardware/panel-rev-f/pump-panel-rev-f.kicad_sch"
REPORT = MAIN.parent / "checks/usb-service.json"

# Physical pin numbers from manufacturer terminal drawings. All wires below are
# nominal DC connections; external cables connect only their listed cavities.
MAIN_PINS = {
    "J40": {"A1":"GND","A12":"GND","SH":"GND","A4":"USB_VBUS","A9":"USB_VBUS",
            "A5":"USB_CC1","B5":"USB_CC2","A6":"USB_CONN_DP","B6":"USB_CONN_DP",
            "A7":"USB_CONN_DM","B7":"USB_CONN_DM","A8":None,"B8":None},
    "R240": {1:"USB_CC1",2:"GND"}, "R241": {1:"USB_CC2",2:"GND"},
    "D42": {1:"USB_PROT_DP",2:"GND",3:"USB_PROT_DM",4:"USB_CONN_DM",5:"USB_ESD_REF",6:"USB_CONN_DP"},
    "D43": {1:"USB_ESD_REF",2:"USB_VBUS"}, "D44":{1:"USB_VBUS",2:"GND"},
    "U41": {1:"GND",2:"USB_DP",3:None,4:"USB_PROT_DP",5:"GND",6:"USB_PROT_DM",7:None,8:"USB_DM",9:"CMD_ALLOWED",10:"+3V3"},
    "R27": {1:"USB_DM_MCU",2:"USB_DM"}, "R28": {1:"USB_DP_MCU",2:"USB_DP"},
    "U3": {3:"+3V3",8:"MCU_EN",17:"USB_DM_MCU",18:"USB_DP_MCU",22:"STRAP_GPIO8",23:"BOOT"},
    "J2": {1:"GND",2:"+3V3",3:"UART_TX",4:"ARM_CMD",5:"MCU_EN",6:"BOOT"},
    "R20": {1:"+3V3",2:"MCU_EN"}, "R21": {1:"+3V3",2:"BOOT"}, "R22": {1:"+3V3",2:"STRAP_GPIO8"},
    "U1": {1:"L_PROTECTED",2:"MAINS_N",4:"GND",5:"PSU_5V_RAW"},
    "J41": {1:"PSU_5V_RAW",2:"+5V",3:"GND"},
    "U2": {2:"+5V",3:"+5V",6:"+3V3",7:"BUCK_SW"}, "L1": {1:"BUCK_SW",2:"+3V3"},
    "R242":{1:"USB_VBUS",2:"USB_PRESENT"}, "R243":{1:"USB_PRESENT",2:"GND"},
    "Q40":{1:"USB_PRESENT",2:"GND",3:"CMD_ALLOWED"}, "R244":{1:"+3V3",2:"CMD_ALLOWED"},
    "U40":{1:"+5V",2:"GND",3:"CMD_ALLOWED",4:None,5:"+5V_CMD",6:"+5V_CMD"},
    "J32":{1:"+5V_CMD",2:"STOP_RETURN",7:"GND",8:"+3V3"},
    "J31":{1:"STOP_RETURN",2:"K1_COIL_PLUS"}, "R197":{1:"STOP_RETURN",2:"PANEL_OK_MON"},
    "J36":{5:"PANEL_OK_MON"},
    "K1":{1:"K1_COIL_PLUS",2:"CTRL_A_COM",3:"CTRL_A_NO",5:"K1_LOW"},
    "K2":{1:"+5V_CMD",2:"CTRL_B_COM",3:"CTRL_B_NO",5:"K2_LOW"},
    "D31":{1:"K1_COIL_PLUS",2:"K1_LOW"}, "D32":{1:"+5V_CMD",2:"K2_LOW"},
    "Q30":{2:"GND",3:"K1_LOW"}, "Q31":{2:"GND",3:"K2_LOW"},
}
PANEL_PINS = {"J1":{1:"+5V",2:"STOP_RETURN",7:"GND",8:"+3V3"},
              "SW1":{1:"+5V",2:None,3:"STOP_LOCAL_NC"},
              "J2":{3:"STOP_LOCAL_NC",4:"STOP_RETURN"},"J7":{4:"+3V3"}}
PARTS = {"J40":"USB4110-GF-A", "U41":"TS3USB30EDGSR", "U40":"TPS22919DCKR",
         "J41":"B3B-XH-A(LF)(SN)", "D43":"BAS116H,115", "D44":"SMF6.0A", "Q40":"PMV16XNR", "D42":"USBLC6-2SC6",
         "U3":"ESP32-C6-MINI-1U-H8", "R240":"RC0603FR-075K1L", "R241":"RC0603FR-075K1L",
         "R27":"Generic 22R 1% 0.125 W 0805", "R28":"Generic 22R 1% 0.125 W 0805",
         "K1":"G5Q-1A4 DC5", "K2":"G5Q-1A4 DC5", "Q30":"AO3400A", "Q31":"AO3400A",
         "R242":"RC0603FR-071KL", "R243":"RC0603FR-0747KL", "R244":"RC0603FR-0710KL"}
# New connections to these safety-relevant nets require reviewing every source.
EXCLUSIVE = {
    "USB_VBUS":"J40.A4 J40.A9 D43.2 D44.1 R242.1","USB_ESD_REF":"D43.1 D42.5", "PSU_5V_RAW":"U1.5 J41.1",
    "CMD_ALLOWED":"Q40.3 R244.2 U40.3 U41.9", "USB_PRESENT":"Q40.1 R242.2 R243.1",
    "+5V_CMD":"U40.6 U40.5 C242.1 D32.1 K2.1 J32.1",
    "STOP_RETURN":"J32.2 J31.1 R80.1 R197.1","K1_COIL_PLUS":"J31.2 K1.1 D31.1 R86.1",
    "USB_DP_MCU":"U3.18 R28.1","USB_DM_MCU":"U3.17 R27.1",
    "USB_CONN_DP":"J40.A6 J40.B6 D42.6","USB_CONN_DM":"J40.A7 J40.B7 D42.4",
    "USB_PROT_DP":"D42.1 U41.4","USB_PROT_DM":"D42.3 U41.6",
    "USB_DP":"U41.2 R28.2","USB_DM":"U41.8 R27.2",
}
SOURCES = ["https://gct.co/files/drawings/usb4110.pdf",
           "https://www.ti.com/lit/ds/symlink/ts3usb30e.pdf",
           "https://www.ti.com/lit/ds/symlink/tps22919.pdf",
           "https://assets.nexperia.com/documents/data-sheet/PMV16XN.pdf",
           "https://www.st.com/resource/en/datasheet/usblc6-2.pdf",
           "https://assets.nexperia.com/documents/data-sheet/BAS116H.pdf",
           "https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smf/smf6-0a",
           "https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html#usb",
           "https://www.espressif.com/sites/default/files/documentation/esp32-c6-mini-1_mini-1u_datasheet_en.pdf",
           "https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/get-started/establish-serial-connection.html"]


def require(test, message):
    if not test:
        raise ValueError(message)


def normalize(net):
    if not net or net.startswith("unconnected-"):
        return None
    return net


def schematic(project, tmp):
    path = tmp / (project.stem + ".xml")
    subprocess.run([str(ROOT/".tools/kicad-cli"),"sch","export","netlist","--format","kicadxml",
                    "-o",str(path),str(project)], check=True)
    doc = ET.parse(path)
    pin_map = {f"{pad.get('ref')}.{pad.get('pin')}":normalize(net.get("name"))
               for net in doc.findall(".//nets/net") for pad in net.findall("node")}
    parts = {c.get("ref"):c.findtext("fields/field[@name='MPN']") for c in doc.findall(".//components/comp")}
    return pin_map, parts


def circuit_signature(nets, pins):
    for ref, pinout in pins.items():
        for number, expected in pinout.items():
            key = f"{ref}.{number}"
            require(key in nets and nets[key]==expected, f"{key} expected {expected}, found {nets.get(key)}")


def validate(nets, panel, parts):
    circuit_signature(nets, MAIN_PINS)
    circuit_signature(panel, PANEL_PINS)
    for ref, expected in PARTS.items():
        require(parts.get(ref)==expected, f"{ref} expected {expected}, found {parts.get(ref)}")
    for rail, terminals in EXCLUSIVE.items():
        actual = {pin for pin,net in nets.items() if net==rail}
        require(actual==set(terminals.split()), f"{rail} has unexpected sources/endpoints: {actual}")


def check_pads(project, pins, parts=None):
    board = pcbnew.LoadBoard(str(project.with_suffix(".kicad_pcb")))
    found = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in pins:
            continue
        if parts and ref in parts:
            fields = {field.GetName():field.GetText() for field in fp.GetFields()}
            require(fields.get("MPN")==parts[ref], f"{ref} routed footprint and BOM MPN disagree")
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            key = ref+"."+num
            net = normalize(pad.GetNetname())
            require(key not in found or found[key]==net, f"Duplicate physical pad disagrees on {key}")
            found[key] = net
    circuit_signature(found,pins)
    return sum(len(pinout) for pinout in pins.values())


def receptacle_lands(footprint):
    # GCT USB4110 sheet 1, recommended component-side copper pattern. Four
    # paired GND/VBUS lands share metal tails with the reverse orientation.
    positions = {"A1":-3.2,"A4":-2.4,"B8":-1.75,"A5":-1.25,"B7":-.75,"A6":-.25,
                 "A7":.25,"B6":.75,"A8":1.25,"B5":1.75,"A9":2.4,"A12":3.2}
    wide = {"A1","A4","A9","A12"}
    pads = {p.GetNumber():p for p in footprint.Pads() if p.GetNumber() in positions}
    holes = [p for p in footprint.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
    require(pads.keys()==positions.keys() and len(holes)==2,"J40 missing terminals or locating holes")
    hole_centers = []
    for hole in holes:
        pos = hole.GetFPRelativePosition()
        hole_centers.append((round(pcbnew.ToMM(pos.x),4),round(pcbnew.ToMM(pos.y),4)))
        require(hole.GetDrillSize()==pcbnew.VECTOR2I(650000,650000),"J40 locating hole diameter")
    require(sorted(hole_centers)==[(-2.89,-2.605),(2.89,-2.605)],"J40 locating hole centers")
    gaps = {}
    for name, pad in pads.items():
        pos = pad.GetFPRelativePosition()
        require(abs(pcbnew.ToMM(pos.x)-positions[name])<.00001 and
                abs(pcbnew.ToMM(pos.y)+3.68)<.00001, f"J40 {name} displaced from recommended row")
        width = .6 if name in wide else .3
        require(pad.GetSize()==pcbnew.VECTOR2I(pcbnew.FromMM(width),pcbnew.FromMM(1.15)),
                f"J40 {name} incorrect land width or length")
        copper = pad.GetEffectiveShape(pcbnew.F_Cu)
        gap = min(pcbnew.ToMM(copper.Distance(h.GetPosition()))-pcbnew.ToMM(h.GetDrillSize().x)/2 for h in holes)
        require(gap>=.254-.000005,f"J40 {name} hole-to-copper {gap:.4f} mm")
        gaps[name] = round(gap,4)
    return {"twelve_land_centers_and_sizes_verified":True,"hole_diameter_mm":.65,
            "NPTH_to_copper_mm":gaps,"minimum_mm":min(gaps.values()),
            "assembly":"Four 0.60 × 1.15 mm paired lands have heel-corner relief; inspect wetting of both tails on each wide land."}


def closure(sources, edges):
    energized = set(sources)
    while True:
        extra = {b for a,b in edges if a in energized}
        if extra <= energized:
            return energized
        energized |= extra


def power_case(n, p, harness, ac, usb, want):
    # Scope includes the physical panel STOP and receiver feedback in their
    # most permissive state. Both low-side drivers are modeled continuously on.
    # Using actual net names makes an unintended connection change the result.
    P = lambda pin: "panel/"+p[pin]
    sources = []
    paths = []
    if ac:
        sources.append(n["U1.5"])
    if usb:
        sources.append(n["J40.A4"])
    if harness=="run":
        paths += [(n["J41.1"],n["J41.2"]),(n["J41.2"],n["J41.1"])]
    if harness=="bench":
        sources.append(n["J41.2"])  # cavity 1 empty; isolated 5 V between 2 and 3
    paths += [(n["U2.2"],n["L1.2"]), (n["J32.8"],P("J1.8")),
              (n["R197.1"],n["R197.2"]), (n["J32.1"],P("J1.1")), (P("SW1.1"),P("SW1.3")),
              (P("J2.3"),P("J2.4")), (P("J1.2"),n["J32.2"]), (n["J31.1"],n["J31.2"])]
    live = closure(sources,paths)
    gated = n["R242.1"] in live and n["R242.2"]==n["Q40.1"] and n["Q40.2"]=="GND"
    pullup = n["R244.1"] in live
    allow = pullup and not (gated and n["Q40.3"]==n["U40.3"])
    if allow:
        paths.append((n["U40.1"],n["U40.6"]))
    live = closure(sources,paths)
    logic = n["U3.3"] in live
    data = logic and gated and n["Q40.3"]==n["U41.9"]
    result = dict(logic_3v3=logic, data_connected=data, oled_3v3=P("J7.4") in live,
                  panel_command_5v=P("J1.1") in live, raw_panel_permit=n["J36.5"] in live,
                  coil_A_feed=n["K1.1"] in live, coil_B_feed=n["K2.1"] in live,
                  converter_output_node=n["U1.5"] in live)
    require(result==want, f"{harness=} {ac=} {usb=}: {result} expected {want}")
    return result


def scenarios(nets, panel):
    cases = []
    for harness, ac, usb in itertools.product(("open","run","bench"),(False,True),(False,True)):
        logic = harness=="bench" or harness=="run" and ac
        cmd = logic and not usb
        want = dict(logic_3v3=logic,data_connected=logic and usb,oled_3v3=logic,panel_command_5v=cmd,raw_panel_permit=cmd,
                    coil_A_feed=cmd,coil_B_feed=cmd,converter_output_node=ac)
        cases.append(dict(harness=harness,ac_source=ac,host_vbus=usb,**power_case(nets,panel,harness,ac,usb,want)))
    return cases


def data_orientations(n, esd_pairs=(("6","1"),("4","3"))):
    # Assume U41 is powered, /OE low and SEL=0 (DGS pin layout). Trace the
    # native nets through D1+/D1− and the series resistors for each insertion.
    paths = [(n["D42."+a],n["D42."+b]) for a,b in esd_pairs]
    paths += [(n["U41.4"],n["U41.2"]), (n["U41.6"],n["U41.8"]),
             (n["R27.2"],n["R27.1"]), (n["R28.2"],n["R28.1"])]
    report = {}
    for label,side in (("normal","A"),("flipped","B")):
        legs = {}
        for pad,dest,other,signal in (("6","18","17","D+"),("7","17","18","D-")):
            reachable = closure([n["J40."+side+pad]], paths)
            require(n["U3."+dest] in reachable and n["U3."+other] not in reachable, f"{label} {signal} polarity")
            legs[signal] = f"J40.{side}{pad} → U3.{dest}"
        report[label] = dict(legs, cc=side+"5")
    return report


def sustained_vbus_from_usb_pullup(n):
    # Start from the worst unplug instant: the board is still powered, full-
    # speed D+ is pulled up, the mux is enabled and the host supply floats.
    # D42 has upper steering diodes to pin 5. D43 conducts anode 2 to cathode
    # 1 only. D44 can conduct GND to connector VBUS, never from the data rail.
    paths = [(n["R28.1"],n["R28.2"]), (n["U41.2"],n["U41.4"]),
             (n["D42.1"],n["D42.6"]), (n["D42.1"],n["D42.5"]),
             (n["D43.2"],n["D43.1"]), (n["D44.2"],n["D44.1"])]
    live = closure([n["U3.18"]],paths)
    require(n["D42.5"] in live,"Missing ESD upper steering path in unplug simulation")
    return n["J40.A4"] in live


def source_transitions(n):
    old = dict(n,**{"D42.5":n["J40.A4"]})
    reversed_diode = dict(n,**{"D43.1":n["D43.2"],"D43.2":n["D43.1"]})
    require(sustained_vbus_from_usb_pullup(old),"Failed to reproduce original unplug latch")
    require(sustained_vbus_from_usb_pullup(reversed_diode),"Failed to detect reversed blocking diode")
    coupled = sustained_vbus_from_usb_pullup(n)
    require(not coupled,"MCU pullup can sustain VBUS after upstream source opens")
    sequences = {}
    for name,events in {
        "bench_first_plug_unplug_replug":[(1,0),(1,1),(1,0),(1,1)],
        "USB_first_cycle_bench_supply":[(0,1),(1,1),(0,1),(1,1),(1,0)],
        "floating_host_VBUS_while_target_stays_on":[(1,1),(1,0),(1,0)],
    }.items():
        connected = False
        results = []
        for powered, host_source in events:
            sensed = bool(host_source or (connected and powered and coupled))
            connected = bool(powered and sensed)
            require(connected==bool(powered and host_source),name+" fails release or reconnection")
            results.append(dict(target_5v=bool(powered),host_source=bool(host_source),
                                mux_connected=connected,Vbus_sensed=sensed))
        sequences[name]=results
    # Old connected rail provides an illustrative 25 °C sustained-on solution:
    # 3.3 V pull-up, 1.5 kΩ + 22 Ω + 10 Ω mux, 1.1 V steering drop, then
    # R242+R243 to ground. This exceeds Q40's 1.8 V rated drive point.
    old_gate = (3.3-1.1)*47000/(1500+22+10+1000+47000)
    require(old_gate>1.8,"Original no-source feedback example did not hold Q40")
    leakage = 80e-9  # BAS116H specifies a maximum at 75 V / 150 °C.
    new_vbus = leakage * (47000+1000) * 1.01
    require(new_vbus<.004,"Excess DC feedback through blocking diode")
    return {"sequences":sequences,"source_open_static_VBUS_from_D43_leakage_max_mV":round(new_vbus*1000,3),
            "prior_shared_clamp_example_Q40_gate_V":round(old_gate,3),
            "negative_controls":["direct shared clamp rail","reversed D43 anode/cathode"],
            "scope":"Powered/unpowered stable states with a floating upstream supply. The leakage bound covers D43 alone. Measure total VBUS leakage and discharge, attach/detach timing, brownout transitions and enumeration on the assembly."}


def sensitivity(n, p, parts):
    changed_pins = {
        "reversed_CC2":("J40.B5","USB_CC1"), "flipped_DM":("J40.B7","USB_CONN_DP"),
        "unprotected_D2":("D42.4","USB_CONN_DP"), "unswitched_relay_A":("J32.1","+5V"),
        "unswitched_relay_B":("K2.1","+5V"), "reverse_coil_A_clamp":("D31.1","K1_LOW"),
        "bench_backfeeds_converter":("J41.1","+5V"), "VBUS_powers_logic":("J40.A4","+5V"),
        "USB_output_always_enabled":("U41.9","GND"), "broken_QOD":("U40.5",None),
        "wrong_ROM_DM":("U3.17","USB_DP_MCU"),
    }
    mutations = [(name,dict(n,**{pin:value}),p,parts) for name,(pin,value) in changed_pins.items()]
    mutations += [("ESD_bypassed_copper",dict(n,**{"U41.4":"USB_CONN_DP"}),p,parts),
                  ("unexpected_uninhibited_supply",dict(n,**{"J99.1":"+5V_CMD"}),p,parts),
                  ("mislanded_remote_STOP_return",n,dict(p,**{"J2.4":"NEXT_RETURN"}),parts),
                  ("panel_STOP_feed_from_logic",n,dict(p,**{"SW1.1":"+3V3"}),parts),
                  ("wrong_VBUS_MOSFET",n,p,dict(parts,Q40="2N7002,215"))]
    rejected = []
    for name, main, panel, inventory in mutations:
        try:
            validate(main,panel,inventory)
        except ValueError:
            rejected.append(name)
        else:
            raise RuntimeError(f"Failed to detect {name}")
    # Run two regressions through the power graph without the direct pin checks.
    for name,pin in (("bypass_B_power_model","K2.1"),("bypass_A_power_model","J32.1")):
        try:
            scenarios(dict(n,**{pin:"+5V"}),p)
        except ValueError:
            rejected.append(name)
        else:
            raise RuntimeError(f"Power solver missed {name}")
    for name, pairs in (("unfitted_ESD_breaks_USB",()),("crossed_ESD_channels",(("6","3"),("4","1")))):
        try:
            data_orientations(n,pairs)
        except ValueError:
            rejected.append(name)
        else:
            raise RuntimeError(f"Data path solver missed {name}")
    for name,main in (("unplug_held_by_shared_clamp",dict(n,**{"D42.5":n["J40.A4"]})),
                      ("unplug_held_by_reversed_D43",dict(n,**{"D43.1":n["D43.2"],"D43.2":n["D43.1"]}))):
        require(sustained_vbus_from_usb_pullup(main),f"Unplug solver missed {name}")
        rejected.append(name)
    return rejected


def main():
    input_files = [Path(__file__).resolve(), Path(__file__).with_name("measure_usb_service_routes.py").resolve()]
    for project in (MAIN,PANEL):
        input_files.extend(sorted(project.parent.glob("*.kicad_sch")))
        input_files.append(project.with_suffix(".kicad_pcb"))
    def input_hashes():
        return {str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in input_files}
    original_hashes = input_hashes()
    with tempfile.TemporaryDirectory() as tmp:
        nets, parts = schematic(MAIN,Path(tmp))
        panel, _ = schematic(PANEL,Path(tmp))
    validate(nets,panel,parts)
    pins = {"main":check_pads(MAIN,MAIN_PINS,PARTS),"panel":check_pads(PANEL,PANEL_PINS)}
    # Conservative DC point at 4.0 V VBUS, below the intended nominal 5 V.
    # Includes 1% resistor tolerance and 100 nA gate leakage at room temperature.
    gate_v = (4./(1010.+47000*.99))*47000*.99 - 100e-9*1010
    require(gate_v>2.5,"Insufficient Q40 gate voltage")
    board = pcbnew.LoadBoard(str(MAIN.with_suffix(".kicad_pcb")))
    jack = next(fp for fp in board.GetFootprints() if fp.GetReference()=="J40")
    results = dict(receptacle=receptacle_lands(jack),routed_usb=measure_routes(board),usb_orientations=data_orientations(nets), native_usb="U3.18 GPIO13 D+, U3.17 GPIO12 D−",
                   boot="J2.6 GPIO9 low during J2.5 EN reset; GPIO8 high via R22. J2.2 reference only.",
                   components=PARTS,physical_pad_nets_checked=pins,
                   gate_min_V_at_4V_VBUS_room_temperature=round(gate_v,3),
                   power_combinations=scenarios(nets,panel),hot_unplug=source_transitions(nets),negative_controls_rejected=sensitivity(nets,panel,parts),
                   scope="Nominal DC topology with all permissive contacts closed and both firmware drivers forced on. "
                         "Without VBUS a powered board can enable command supplies. QISO1 motor isolation and the interlocked shutter protect access with a powered or dead cable. "
                         "Data-only host USB needs board power. Relay release timing, leakage, reverse power, ROM boot, USB eye/EMI, "
                         "cabinet trip timing and blocked shutter closure still require measurements.",
                   sources=SOURCES, input_sha256=original_hashes)
    require(original_hashes==input_hashes(),"USB audit input changed during verification")
    REPORT.write_text(json.dumps(results,indent=2,ensure_ascii=False)+"\n")
    print(REPORT.relative_to(ROOT))


if __name__=="__main__":
    main()
