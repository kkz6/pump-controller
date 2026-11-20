"""Verify programming, relay contacts and the panel stop loop from the native KiCad schematics."""
import json
import os
from pathlib import Path
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
    "J41": {1: "PSU_5V_RAW", 2: "+5V", 3: "GND"}, "J32": {1: "+5V_CMD", 2: "STOP_RETURN"},
    "K1": {1: "K1_LOW", 3: "CTRL_A_COM", 4: "CTRL_A_NO", 6: "STOP_RETURN"},
    "K2": {1: "K2_LOW", 3: "CTRL_B_COM", 4: "CTRL_B_NO", 6: "+5V_CMD"},
    "J30": {1: "CTRL_A_COM", 2: "CTRL_A_NO"}, "J35": {1: "CTRL_B_COM", 2: "CTRL_B_NO"}
}
PANEL = {"J1": {1: "+5V", 2: "STOP_RETURN"}, "SW1": {1: "+5V", 3: "STOP_LOCAL_NC"},
         "J2": {3: "STOP_LOCAL_NC", 4: "STOP_RETURN"}}

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
    counts = {"main_named_terminals": check("main", "pump-direct", MAIN),
              "panel_named_terminals": check("panel", "pump-panel-rev-f", PANEL),
              "physical_usb_and_starter_tested": False}
    print(json.dumps(counts, indent=2))
