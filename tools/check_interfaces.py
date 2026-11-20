"""Verify board interfaces, critical circuit paths and mains isolation rule coverage."""
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
MAIN = {
    "U33": {9: "+3V3", 10: "GND", 12: "I2C_SCL", 13: "I2C_SDA", 15: "GND", 16: "GND",
            17: "GND", 23: "USB_TX_IND", 24: "USB_RX_IND", 8: "START_CMD_LED", 28: "STOP_CMD_LED"},
    "R260": {1: "USB_TX_IND", 2: "USB_TX_LED_A"}, "D60": {1: "GND", 2: "USB_TX_LED_A"},
    "R261": {1: "USB_RX_IND", 2: "USB_RX_LED_A"}, "D61": {1: "GND", 2: "USB_RX_LED_A"},
    "SW60": {1: "BOOT", 2: "GND"}, "SW61": {1: "MCU_EN", 2: "GND"},
    "U3": {3: "+3V3", 8: "MCU_EN", 17: "USB_DM_MCU", 18: "USB_DP_MCU", 22: "STRAP_GPIO8", 23: "BOOT"},
    "R20": {1: "+3V3", 2: "MCU_EN"}, "C22": {1: "MCU_EN", 2: "GND"},
    "R21": {1: "+3V3", 2: "BOOT"}, "R22": {1: "+3V3", 2: "STRAP_GPIO8"},
    "J2": {1: "GND", 2: "+3V3", 5: "MCU_EN", 6: "BOOT"},
    "J40": {"A1": "GND", "A12": "GND", "A4": "USB_VBUS", "A9": "USB_VBUS", "A5": "USB_CC1", "B5": "USB_CC2",
            "A6": "USB_CONN_DP", "B6": "USB_CONN_DP", "A7": "USB_CONN_DM", "B7": "USB_CONN_DM"},
    "R240": {1: "USB_CC1", 2: "GND"}, "R241": {1: "USB_CC2", 2: "GND"},
    "D42": {1: "USB_PROT_DP", 2: "GND", 3: "USB_PROT_DM", 4: "USB_CONN_DM", 5: "USB_ESD_REF", 6: "USB_CONN_DP"},
    "U41": {1: "GND", 2: "USB_DP", 4: "USB_PROT_DP", 5: "GND", 6: "USB_PROT_DM", 8: "USB_DM", 9: "CMD_ALLOWED", 10: "+3V3"},
    "R27": {1: "USB_DM_MCU", 2: "USB_DM"}, "R28": {1: "USB_DP_MCU", 2: "USB_DP"},
    "R242": {1: "USB_VBUS", 2: "USB_PRESENT"}, "R243": {1: "USB_PRESENT", 2: "GND"},
    "Q40": {1: "USB_PRESENT", 2: "GND", 3: "CMD_ALLOWED"}, "R244": {1: "+3V3", 2: "CMD_ALLOWED"},
    "U40": {1: "+5V", 2: "GND", 3: "CMD_ALLOWED", 5: "+5V_CMD", 6: "+5V_CMD"},
    "J41": {1: "PSU_5V_RAW", 2: "+5V", 3: "GND"},
    "K1": {1: "K1_LOW", 3: "CTRL_A_COM", 4: "CTRL_A_NO", 6: "STOP_RETURN"},
    "K2": {1: "K2_LOW", 3: "CTRL_B_COM", 4: "CTRL_B_NO", 6: "+5V_CMD"},
    "J30": {1: "CTRL_A_COM", 2: "CTRL_A_NO"}, "J35": {1: "CTRL_B_COM", 2: "CTRL_B_NO"}
}
# Listed in cavity order for a straight main-to-door-panel loom.
MAIN_LOOM = ("+5V_CMD", "STOP_RETURN", "MAN_RETURN", "AUTO_RETURN", "START_N", "RESET_N",
             "GND", "+3V3", "I2C_SDA", "I2C_SCL", "SPARE_B6", "SPARE_B7")
PANEL_LOOM = ("+5V", "STOP_RETURN", "MAN_RETURN", "AUTO_RETURN", "START_N", "RESET_N",
              "GND", "+3V3", "I2C_SDA", "I2C_SCL", "KEY_MAN_N", "KEY_AUTO_N")


def terminals(*nets):
    return dict(enumerate(nets, start=1))


MAIN.update({
    "J32": terminals(*MAIN_LOOM),
    "J1": terminals("MAINS_L", "MAINS_N"), "F1": terminals("MAINS_L", "L_FUSED"),
    "U1": {1: "L_PROTECTED", 2: "MAINS_N", 4: "GND", 5: "PSU_5V_RAW"},
    "U2": {1: "GND", 2: "+5V", 3: "+5V", 4: "GND", 5: "GND", 6: "+3V3", 7: "BUCK_SW", 9: "GND"},
    "L1": terminals("BUCK_SW", "+3V3"),
    "J10": terminals("M_CT_HI", "M_GND"), "R42": terminals("MAINS_N", "M_GND"),
    "R43": terminals("L_PROTECTED", "M_VDIV_0"), "R44": terminals("M_VDIV_0", "M_VDIV_1"),
    "R45": terminals("M_VDIV_1", "M_VDIV_2"), "R46": terminals("M_VDIV_2", "M_VP"),
    "R47": terminals("M_VP", "M_GND"), "R48": terminals("M_GND", "M_VN"),
    "R49": terminals("M_CT_HI", "M_IAP"), "R50": terminals("M_GND", "M_IAN"),
    "U10": {5: "M_IAP", 6: "M_IAN", 11: "M_VN", 12: "M_VP", 18: "M_XIN", 19: "M_XOUT",
            25: "M_SCLK", 26: "M_MISO", 27: "M_MOSI", 28: "M_CS"},
    "U11": {1: "+3V3", 4: "METER_SCLK", 5: "METER_MOSI", 6: "METER_CS", 7: "METER_MISO",
            9: "GND", 11: "+5V", 18: "M_ISO_RAW", 20: "M_ISO_GND",
            22: "M_MISO", 23: "M_CS", 24: "M_MOSI", 25: "M_SCLK", 28: "M_3V3"},
    "FB1": terminals("M_ISO_RAW", "M_3V3"), "FB2": terminals("M_ISO_GND", "M_GND"),
    "D31": terminals("STOP_RETURN", "K1_LOW"), "D32": terminals("+5V_CMD", "K2_LOW"),
    "Q30": terminals("K1_GATE", "GND", "K1_LOW"), "Q31": terminals("K2_GATE", "GND", "K2_LOW"),
    "J20": terminals("PROBE_TCOM", "PROBE_L1", "PROBE_L2", "PROBE_L3", "PROBE_L4"),
    "J21": terminals("PROBE_INLET", "PROBE_ICOM"),
    "U20": {5: "PROBE_TX_SET", 6: "PROBE_TX_TANK", 7: "PROBE_TX_TANK", 8: "PROBE_MUX_BUF",
            9: "PROBE_MUX_BUF", 10: "PROBE_MUX_OUT", 12: "PROBE_TX_SET", 13: "PROBE_TX_INLET", 14: "PROBE_TX_INLET"},
    "R115": terminals("PROBE_TX_TANK", "PROBE_TCOM_DRIVE"), "C106": terminals("PROBE_TCOM_DRIVE", "PROBE_TCOM_CLAMP"),
    "R116": terminals("PROBE_TCOM_CLAMP", "PROBE_TCOM_MID"), "R117": terminals("PROBE_TCOM_MID", "PROBE_TCOM"),
    "R170": terminals("PROBE_INLET", "PROBE_INLET_MID"), "R171": terminals("PROBE_INLET_MID", "PROBE_INLET_CLAMP"),
    "C128": terminals("PROBE_INLET_CLAMP", "PROBE_INLET_SENSE"), "R173": terminals("PROBE_INLET_SENSE", "PROBE_INLET_ADC"),
    "U21": {1: "MUX_A0", 2: "+3V3", 4: "PROBE_L1_ADC", 5: "PROBE_L2_ADC", 6: "PROBE_L3_ADC",
            7: "PROBE_L4_ADC", 8: "PROBE_MUX_OUT", 12: "PROBE_INLET_ADC", 15: "MUX_A2", 16: "MUX_A1"},
    "U22": {1: "GND", 3: "GND", 4: "PROBE_ADC_SIGNAL", 5: "PROBE_ADC_BIAS", 8: "+3V3", 9: "I2C_SDA", 10: "I2C_SCL"},
    "U31": {1: "ARM_CMD", 2: "+3V3", 5: "ARM_Q", 6: "ARM_CLEAR_N", 7: "+3V3"},
    "U30": terminals("SAFE_CLEAR_N", "GND", "GND", "HEARTBEAT", "+3V3"),
    "U32": terminals("SAFE_CLEAR_N", "+3V3", "GND"),
})
MAIN["U33"].update({1: "START_FILTER", 2: "RESET_FILTER", 3: "STOP_SENSE", 4: "MAN_SENSE",
                    5: "AUTO_SENSE", 7: "SPARE_B6", 21: "SPARE_B7"})
PANEL = {
    "J1": terminals(*PANEL_LOOM),
    "J2": terminals("START_N", "GND", "STOP_LOCAL_NC", "STOP_RETURN", "MAN_RETURN", "STOP_RETURN",
                    "RESET_N", "GND", "AUTO_RETURN", "STOP_RETURN"),
    "J7": terminals("I2C_SCL", "I2C_SDA", "GND", "+3V3"), "J8": terminals("+5V", "KEY_MAN_RAW", "KEY_AUTO_RAW"),
    "SW1": {1: "+5V", 3: "STOP_LOCAL_NC"}, "SW2": terminals("START_N", "GND"),
    "SW3": terminals("MAN_RETURN", "STOP_RETURN"), "SW4": terminals("RESET_N", "GND"),
    "SW5": terminals("AUTO_RETURN", "STOP_RETURN"),
    "Q1": terminals("KEY_MAN_B", "GND", "KEY_MAN_N"), "Q2": terminals("KEY_AUTO_B", "GND", "KEY_AUTO_N"),
}


def check_isolation_classes(board, patterns):
    # KiCad 10 stores pad and routed copper net names directly in the board file.
    nets = set(re.findall(r'^\s*\(net "([^"]+)"\)', board, re.MULTILINE))
    if not nets:
        raise ValueError("No named copper found in KiCad board")
    for net in sorted(nets):
        domains = {p["netclass"] for p in patterns if p["netclass"] in {"LIVE", "SELV", "CABINET"}
                   and fnmatchcase(net, p["pattern"])}
        if len(domains) != 1:
            raise ValueError(f"{net} must have exactly one isolation domain, found {sorted(domains)}")
    return len(nets)


def check(directory, stem, expected):
    with tempfile.TemporaryDirectory() as tmp:
        netlist = Path(tmp) / "board.xml"
        subprocess.run([os.getenv("KICAD_CLI", "kicad-cli"), "sch", "export", "netlist", "--format",
                        "kicadxml", "-o", str(netlist), str(ROOT / "hardware" / directory / (stem + ".kicad_sch"))],
                       check=True, stdout=subprocess.DEVNULL)
        nets = ElementTree.parse(netlist).findall(".//nets/net")
    pins = {(node.get("ref"), node.get("pin")): net.get("name") for net in nets for node in net.findall("node")}
    for ref, terminals in expected.items():
        for pin, name in terminals.items():
            actual = pins.get((ref,str(pin)))
            if actual != name:
                raise ValueError(f"{directory} {ref}.{pin}: wanted {name}, found {actual}")
    if directory == "main":
        for ref, other, channel in (("K1","J30","A"), ("K2","J35","B")):
            for net, coil_pin, plug_pin in (("COM","3","1"), ("NO","4","2")):
                name = f"CTRL_{channel}_{net}"
                if {key for key, value in pins.items() if value == name} != {(ref,coil_pin),(other,plug_pin)}:
                    raise ValueError(f"Unexpected connection to dry contact {name}")
    return sum(len(values) for values in expected.values())

if __name__ == "__main__":
    board = ROOT / "hardware/main/pump-direct.kicad_pcb"
    project = json.loads(board.with_suffix(".kicad_pro").read_text())
    counts = {"main_copper_nets_with_isolation_domain": check_isolation_classes(
                  board.read_text(), project["net_settings"]["netclass_patterns"]),
              "main_named_terminals": check("main", "pump-direct", MAIN),
              "panel_named_terminals": check("panel", "pump-panel-rev-f", PANEL),
              "physical_usb_and_starter_tested": False}
    print(json.dumps(counts, indent=2))
