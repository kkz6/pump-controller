"""Build the R4 field schematic, BOM and native ERC/PDF/netlist for the two-PCB system."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import build_starter_guard as field
import generate_cad as cad

PROJECT = "starter-guard-r4"
OUT = cad.BASE / "hardware" / PROJECT


def design():
    instruments, outputs, service = field.field(OUT / "contacts.csv")
    # The internal feedback switch and its suppressor now live entirely on the main PCB.
    instruments = [part for part in instruments if part["ref"] != "D3"]
    outputs = [part for part in outputs if part["ref"] not in {"J31", "KFB1", "D6"}]
    for part in instruments:
        if part["ref"] == "XF3":
            for pin in part["pins"]:
                pin["net"] = {"HOST_LOGIC": "HOST_AUX_N", "LOCAL_LOGIC": "LOCAL_AUX_N",
                              "ISO_0": "GND"}.get(pin["net"], pin["net"])
    instruments.extend([
        field.part("J52", "Main selector auxiliary mating plug", "JST PHR-3 / SPH-002T-P0.5S",
                   [(1, "Logic common", "GND"), (2, "HOST dry pole", "HOST_AUX_N"),
                    (3, "LOCAL dry pole", "LOCAL_AUX_N")],
                   "Low-level isolated transfer auxiliary. Only these three cores share the main logic domain."),
        field.part("J54", "Main cabinet I/O mating plug", "JST VHR-5N / SVH-21T-P1.1",
                   [(1, "Fused +24 V", "FUSED_24"), (2, "Cabinet 0 V", "CAB_0"),
                    (3, "PNP heartbeat", "HB_24"), (4, "Panel relay +", "PANEL_24"),
                    (5, "Host feedback +", "KFB_A1")],
                   "Field-side 24 V only. At the main PCB, pin 5 feeds the onboard feedback relay coil."),
    ])
    # Illustrate the factory pilot explicitly, using functional OEM terminal names.
    # The common trip chain uses spare electrically isolated contact poles.
    factory_poles = {
        "S3": [("OEM-IN", "Original STOP NC", "OEM_CTRL_L"), ("OEM-OUT", "Original STOP NC", "PILOT_AFTER_STOP")],
        "S4": [("OEM-IN", "Original overload NC", "PILOT_AFTER_STOP"), ("OEM-OUT", "Original overload NC", "PILOT_P")],
        "S5": [("OEM-IN", "Original START NO", "PILOT_P"), ("OEM-OUT", "Original START NO", "PILOT_D")],
        "KOF1": [("A1", "OEM coil +", "PILOT_D"), ("A2", "OEM coil return", "PILOT_COIL_RETURN")],
    }
    for part in instruments:
        for number, name, net in factory_poles.get(part["ref"], []):
            part["pins"].append(dict(num=number, name=name, net=net, type="passive"))
    pilot = field.pilot_profile()
    pilot.append(field.part(
        "XPF1", "DOL service plug mating positions", "Same XC1 profile-matched break-before-make transfer",
        [("H1", "XC1.1 HOST", "B_COM"), ("F1", "Field P", "PILOT_P"),
         ("H2", "XC1.2 HOST", "B_NO"), ("F2", "Field D", "PILOT_D"),
         ("H3", "XC1.3 HOST", "A_COM"), ("F3", "Coil return", "PILOT_COIL_RETURN"),
         ("H4", "XC1.4 HOST", "A_NO"), ("F4", "Pilot 0 V", "OEM_CTRL_N"),
         ("L3", "LOCAL link in", "PILOT_COIL_RETURN"), ("L4", "LOCAL link out", "OEM_CTRL_N")],
        "Functional view of the XC1 inserts, not an additional device. HOST connects H1-F1 through H4-F4. LOCAL connects only L3-L4. All are open during transfer."))
    for part in outputs + pilot:
        if part["ref"] == "XM2":
            part["description"] = "Motor L and N only. Segregate from J52, J54 and XC1. Keep PE continuous on the separate earth bar. Fit rail end stops and 3047028 end covers."
        elif part["ref"] == "XP10":
            part["description"] = "KS1/KS2 interrupt the motor feeder. The SELV pilot stays powered. Only for the verified 24 V DC pilot profile."
    sheets = [
        ("field", "Independent trips and main board interfaces", instruments),
        ("outputs", "Guard relays and series motor contactors", outputs),
        ("pilot", "Conventional 24 V DC pilot proof", pilot),
        ("service", "Motor isolator and USB access interlock", service),
    ]
    return {"project": PROJECT, "revision": "R4", "title": "Independent external starter guard",
            "sheets": [dict(id=s, title=t, components=c) for s,t,c in sheets]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Run KiCad ERC and export the field drawing and netlist")
    args = parser.parse_args()
    data = design()
    cad.write_schematics(data, OUT, PROJECT)
    cad.write_bom(data, OUT)
    (OUT / (PROJECT + ".kicad_pro")).write_text(json.dumps(
        {"meta": {"filename": PROJECT + ".kicad_pro", "version": 3}}, indent=2) + "\n")
    if not args.check:
        return
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(cad.BASE / ".tools/kicad-cli")
    checks = OUT / "checks"
    checks.mkdir(exist_ok=True)
    jobs = [
        ("erc", "--format", "json", "--severity-all", "--exit-code-violations", "-o", "checks/erc.json"),
        ("export", "netlist", "--format", "kicadxml", "-o", "checks/guard-netlist.xml"),
        ("export", "pdf", "-o", "guard-schematic.pdf"),
    ]
    for job in jobs:
        subprocess.run([cli, "sch", *job, PROJECT + ".kicad_sch"], cwd=OUT, check=True)
    netlist = checks / "guard-netlist.xml"
    cad.validate_netlist(data, netlist)
    xml = ET.parse(netlist)
    for element in xml.findall(".//source") + xml.findall(".//uri"):
        if element.text:
            element.text = element.text.replace(str(OUT) + "/", "")
    xml.write(netlist, encoding="utf-8", xml_declaration=True)
    ercfile = checks / "erc.json"
    erc = json.loads(ercfile.read_text())
    for sheet in erc["sheets"]:
        if "source" in sheet:
            sheet["source"] = Path(sheet["source"]).name
    ercfile.write_text(json.dumps(erc, indent=2) + "\n")


if __name__ == "__main__":
    main()
