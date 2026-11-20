"""Build the external 24 V DC pilot cabinet for the budget OPEN_STOP profile."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import build_probe_cabinet as probes
import build_starter_guard as field
import generate_cad as cad

PROJECT = "starter-budget-r4"
OUT = cad.BASE / "hardware" / PROJECT

# Each entry identifies the physically distinct pole on the referenced component.
# The contact table gets wire names from the same numbered pins exported to KiCad.
POLES = {
    "TRIP": """
SG1 11 12 USB_COVER_A
SG1 21 22 USB_COVER_B
S3 11 12 OEM_STOP_RELEASED
S4 C NC OVERLOAD_HEALTHY
KV1 11 14 KV_IN_RANGE_NO
KC1 11 14 KC_IN_RANGE_NO
XF3 5 6 H_SEATED
XF3 7 8 L_RELEASED
KPS1 33 34 PANEL_RELAY_NO
XF3 9 10 L_SEATED
XF3 11 12 H_RELEASED
""",
    "IDLE": """
KS1 21 22 KS1_MIRROR_NC
KS2 21 22 KS2_MIRROR_NC
KOF1 21 22 OEM_OFF_PROOF
KHL1 61 62 OEM_HOLD_RELEASED
S5 C NC OEM_START_RELEASED
XF3 13 14 H_SEATED
KCA1 11 12 KCA_GUIDED_NC
KCB1 11 12 KCB_GUIDED_NC
XF3 15 16 L_SEATED
OC3 3 4 OPEN_PICKUP_SENSOR
KID1 15 18 OEM_COMMAND_PATH_OPEN
""",
    "ARM": """
S1 21 22 RESET_RELEASED
KREADY1 33 34 READY_SEAL
KREADY1 43 44 READY_PERMIT
S1 13 14 RESET_PRESSED
D12 2 1 FORWARD_RESET_DIODE
KEN1 33 34 ENABLE_SEAL
KEN1 43 44 ENABLE_OUTPUT
""",
    "COMMAND": """
J30 1 2 BOARD_A_NO
J35 1 2 BOARD_B_NO
""",
    "HOST_FEEDBACK": """
KS1 13 14 KS1_AUX_NO
KS2 13 14 KS2_AUX_NO
XF3 17 18 H_SEATED
""",
    "PILOT_SUPPLY": """
S3 OEM-IN OEM-OUT OEM_STOP_RELEASED
S4 OEM-IN OEM-OUT OVERLOAD_HEALTHY
""",
    "PILOT_PICKUP": """
S5 OEM-IN OEM-OUT OEM_START_NO
KHL1 53 54 OEM_SEAL_NO
XPF1 F1 H1 H_P1
KCB1 33 34 KCB_NO
XPF1 H2 F2 H_P2
""",
    "PILOT_RETURN": """
XPF1 F3 H3 H_P3
KCA1 33 34 KCA_NO
XPF1 H4 F4 H_P4
XPF1 L3 L4 L_P34
""",
    "TRIP_QUALIFY": "KT1 12 9 TIMER_SINK_ON\nKH1 13 14 CABINET_FAST_GATE",
    "OEM_COIL_FEED": "KO1 13 14 FAST_PILOT_OUTPUT",
    "OEM_FEED": """
QISO1 L-IN L-OUT ISOLATOR_L
KS1 1L1 2T1 KS1_MAIN_NO
KS2 1L1 2T1 KS2_MAIN_NO
KOF1 1L1 2T1 OEM_MAIN_NO
""",
    "OEM_RETURN": "QISO1 N-IN N-OUT ISOLATOR_N",
}


def latch_relay(ref, role, coil, seal_from, seal_to, output_from, output_to):
    return field.part(ref, role, "G7SA-2A2B DC24 / P7SA-10F", [
        (0, "Coil +", coil), (1, "Coil -", "CAB_0"),
        (33, "Latch NO", seal_from), (34, "Latch NO", seal_to),
        (43, "Output NO", output_from), (44, "Output NO", output_to),
    ], "24 V DC coil and direct-wired socket. Unused NC contacts have no connections.", field.OMRON)


def fast_switch(ref, role, control_plus, control_minus, source, output):
    return field.part(ref, role, "G3RV-ST500-D-H DC24", [
        ("A1", "Input +", control_plus), ("A2", "Input -", control_minus),
        (13, "Output +", source), (14, "Output -", output),
    ], "Exact DC-input, high-speed module. Check DC load and switching peaks at the installed coil.",
       "https://www.ia.omron.com/products/family/3869/specification.html")


def diode(ref, role, anode, cathode):
    return field.part(ref, role, "1N4007-E3/54", [(1, "K", cathode), (2, "A", anode)],
                      "Observe cathode band and keep flyback loop local to the coil.",
                      "https://www.vishay.com/docs/88503/1n4001.pdf", "diode")


def bleed(ref, net, return_net="CAB_0"):
    return field.part(ref, "2.20k 1% 1W", "2.20 kOhm 1% 1 W flameproof",
                      [(1, "1", net), (2, "2", return_net)],
                      "Discharges the node and defines the off voltage with leakage.", kind="resistor")


def design():
    data = probes.design()
    data.update(project=PROJECT, revision="R4-BUDGET", title="Budget DOL / 24 V DC OPEN_STOP only")
    sheets = {s["id"]: s for s in data["sheets"]}
    for sheet in data["sheets"]:
        sheet["components"] = [part for part in sheet["components"]
                               if part["ref"] not in {"SR1", "SR2", "WD1", "F1", "S1", "S2"}]
    parts = {p["ref"]: p for s in data["sheets"] for p in s["components"]}

    rewires = {
        "SG1": {"11": "FUSED_24", "12": "USB_MID", "21": "USB_MID", "22": "AFTER_USB_A"},
        "XSG1": {"1": "FUSED_24", "2": "USB_MID", "3": "USB_MID", "4": "AFTER_USB_A"},
        "KPS1": {"33": "HOST_EXCLUSIVE", "34": "TRIP_RAW"},
        "XF3": {"12": "TRIP_RAW", "16": "RAW_IDLE"},
        "KS1": {"A1": "KS_COILS", "21": "TRIP_OK"},
        "KS2": {"A1": "KS_COILS"},
        "KOF1": {"A1": "OEM_COIL_PLUS"},
        "KHL1": {"62": "OEM_START_IDLE_IN"},
        "S5": {"C": "OEM_START_IDLE_IN"},
        "XF2": {"8": "OEM_START_IDLE_IN", "9": "OEM_START_IDLE_IN"},
        "KCB1": {"12": "RAW_IDLE"},
        "OC3": {"3": "RAW_IDLE"},
        "KID1": {"15": "RAW_IDLE", "18": "IDLE_OK"},
        "J54": {"3": None},
    }
    for ref, changes in rewires.items():
        pins = {pin["num"]: pin for pin in parts[ref]["pins"]}
        for number, net in changes.items():
            pins[number]["net"] = net
    for pin in parts["J54"]["pins"]:
        if pin["num"] == "3":
            pin["name"] = "Unused (HB)"
    parts["SG1"]["description"] = "Both direct-opening NC contacts in series. USB shutter mechanically interlocked with QISO1."
    parts["XSG1"]["description"] = "Four insulated cores; USB_MID joins the two field pairs at the cabinet end."
    parts["J54"]["description"] = "Cabinet +24 V, return, unused position 3, panel-permit feed and actual HOST/KS feedback."
    parts["KID1"]["description"] = ("Power-on delay mode A, no pause. Engineering setting 1 s. "
                                    "Check reset time, timer tolerance and actual command release/pickup.")
    parts["OC3"]["description"] = "Detect open pickup path. The separate RAW_IDLE proof chain supplies the timer only through OC3."
    parts["KOF1"]["pins"].extend(field.part("X", "", "", [
        ("1L1", "OEM line in", "OEM_LINE"), ("2T1", "Switched OEM line", "OEM_SWITCHED_LINE")])["pins"])
    parts["KOF1"]["description"] = "Actual DOL contactor with 24 V DC coil, linked off proof and motor power contact."
    sheets["service"]["components"].append(field.part("XO1", "Retained OEM motor circuit",
        "Existing capacitor starter, motor and overload power elements",
        [(1, "Switched line", "OEM_SWITCHED_LINE"), (2, "Motor neutral", "MOTOR_RETURN")],
        "Functional load boundary. Retain OEM overload elements, capacitor sequencing and continuous PE per the identified starter."))
    sheets["field"]["components"].append(field.part("S1", "Manual guard RESET / spring-return",
        "Harmony XB5AA31 + compatible ZBE102 NC block",
        [(21, "Released NC", "IDLE_OK"), (22, "Released NC", "READY_COIL"),
         (13, "Pressed NO", "RESET_ARMED"), (14, "Pressed NO", "RESET_PICKUP")],
        "Both poles on one mechanically linked spring-return actuator; prove break-before-make on press and release.",
        "https://www.se.com/ww/en/product/ZBE102/"))
    sheets["outputs"]["components"].extend([
        latch_relay("KREADY1", "Reset released memory", "READY_COIL", "IDLE_OK", "READY_COIL", "IDLE_OK", "RESET_ARMED"),
        latch_relay("KEN1", "Manual permission memory", "ENABLE_COIL", "TRIP_OK", "ENABLE_COIL", "TRIP_OK", "KS_COILS"),
        field.diode("D10", "READY_COIL"), field.diode("D11", "ENABLE_COIL"),
        diode("D12", "Reset pickup isolation", "RESET_PICKUP", "ENABLE_COIL"),
    ])
    data["sheets"].append(dict(id="fast_permit", title="Rapid trip input and reclose delay",
        notes="KT1 is always powered. NPN output enables KH1. KO1 follows the actual enabled coil supply. Plain OND, 1 ms input, 1.000 s delay, power-reset memory.",
        components=[
            field.part("KT1", "One-second reclose inhibit", "Autonics CT6S-1P2", [
                (4, "Supply -", "CAB_0"), (5, "Supply +", "FUSED_24"),
                (6, "INA/START", "TRIP_RAW"), (9, "Input/output 0V", "CAB_0"), (12, "Transistor OUT", "GATE_SINK"),
                (1, "Relay NO unused", None), (2, "Relay COM unused", None), (3, "Relay NC unused", None),
                (7, "Inhibit unused", None), (8, "Sensor 12V unused", None),
                (10, "External reset unused", None), (11, "Unused", None)],
                "Non-communications version. TIMER / PNP / OND / 1 ms INA / retained time-output / zero PV on power loss. Set 1.000 s. Verify actual INA-low to semiconductor OFF timing.",
                "https://www.autonics.com/in/model/CT6S-1P2"),
            fast_switch("KH1", "Cabinet reclose gate", "TRIP_RAW", "GATE_SINK", "TRIP_RAW", "TRIP_OK"),
            fast_switch("KO1", "Factory coil reclose gate", "KS_COILS", "CAB_0", "PILOT_D", "OEM_COIL_PLUS"),
            diode("D14", "Factory coil flyback", "PILOT_COIL_RETURN", "OEM_COIL_PLUS"),
            diode("D15", "KS coil flyback", "CAB_0", "KS_COILS"),
            bleed("R44", "TRIP_RAW"), bleed("R45", "TRIP_OK"), bleed("R46", "TRIP_RAW", "GATE_SINK"),
        ]))
    sheets["field"]["notes"] = "Original STOP and overload open the OEM pilot and the raw cabinet trip bus. J54.3 is unused."
    sheets["outputs"]["notes"] = "KREADY1 stores a released reset. KEN1 seals from the delayed trip bus. A raw trip restarts the independent reclose delay."
    return data


def write_contacts(data, output=OUT, poles=POLES):
    pins = {part["ref"]: {pin["num"]: pin["net"] for pin in part["pins"]}
            for sheet in data["sheets"] for part in sheet["components"]}
    with (output / "contacts.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["circuit", "from", "to", "conducts_when", "ref", "pin_a", "pin_b"])
        for circuit, paths in poles.items():
            for line in paths.strip().splitlines():
                ref, pin_a, pin_b, state = line.split()
                a, b = pins[ref][pin_a], pins[ref][pin_b]
                assert a and b and a != b
                writer.writerow([circuit, a, b, state, ref, pin_a, pin_b])


def export(data, output, project, poles):
    checks = output / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    write_contacts(data, output, poles)
    cad.write_schematics(data, output, project)
    cad.write_bom(data, output)
    (output / (project + ".kicad_pro")).write_text(json.dumps(
        {"meta": {"filename": project + ".kicad_pro", "version": 3}}, indent=2) + "\n")
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(cad.BASE / ".tools/kicad-cli")
    for job in [
        ["erc", "--format", "json", "--severity-all", "--exit-code-violations", "-o", "checks/erc.json"],
        ["export", "netlist", "--format", "kicadxml", "-o", "checks/guard-netlist.xml"],
        ["export", "pdf", "-o", "cabinet-schematic.pdf"],
    ]:
        subprocess.run([cli, "sch", *job, project + ".kicad_sch"], cwd=output, check=True)
    netlist = checks / "guard-netlist.xml"
    cad.validate_netlist(data, netlist)
    xml = ET.parse(netlist)
    for element in xml.findall(".//source") + xml.findall(".//uri"):
        if element.text:
            element.text = element.text.replace(str(output) + "/", "")
    xml.write(netlist, encoding="utf-8", xml_declaration=True)
    erc = checks / "erc.json"
    result = json.loads(erc.read_text())
    for sheet in result["sheets"]:
        if "source" in sheet:
            sheet["source"] = Path(sheet["source"]).name
    erc.write_text(json.dumps(result, indent=2) + "\n")


def main():
    export(design(), OUT, PROJECT, POLES)


if __name__ == "__main__":
    main()
