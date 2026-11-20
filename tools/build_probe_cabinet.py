"""Generate the probe-only R4 cabinet reference from the released cabinet design."""

import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import build_integrated_cabinet as original
import generate_cad as cad

PROJECT = "starter-guard-r4-probes"
OUT = cad.BASE / "hardware" / PROJECT
COMMON = "ALL_SUPPLIES_OK"


def design():
    data = original.design()
    data.update(project=PROJECT, revision="R4-PROBES", title="Probe-only level control / independent starter guard")
    field = next(sheet for sheet in data["sheets"] if sheet["id"] == "field")
    field["notes"] = "XF2.5 and XF2.6 are unused. Factory STOP and overload trip the guard. There is no independent high-water trip."
    by_ref = {part["ref"]: part for part in field["components"]}
    field["components"].remove(by_ref["LS1"])
    xf2 = by_ref["XF2"]
    xf2["value"] = "OEM auxiliary contacts"
    xf2["description"] = "Dedicated auxiliary contacts. Positions 5 and 6 are unused in this profile."
    for pin in xf2["pins"]:
        if pin["num"] in ("5", "6"):
            pin.update(name="Unused", net=None)
    for pin in by_ref["XF3"]["pins"]:
        if pin["num"] in ("5", "9"):
            assert pin["net"] == "AFTER_HH"
            pin["net"] = COMMON
    return data


def write_contacts():
    with (original.OUT / "contacts.csv").open(newline="") as infile, (OUT / "contacts.csv").open("w", newline="") as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            if row["conducts_when"] == "FLOAT_NC":
                assert (row["circuit"], row["from"], row["to"]) == ("SR1_INPUT", COMMON, "AFTER_HH")
                continue
            if row["from"] == "AFTER_HH":
                assert row["conducts_when"] in ("H_SEATED", "L_SEATED")
                row["from"] = COMMON
            writer.writerow(row)


def main():
    data = design()
    checks = OUT / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    write_contacts()
    cad.write_schematics(data, OUT, PROJECT)
    cad.write_bom(data, OUT)
    (OUT / (PROJECT + ".kicad_pro")).write_text(json.dumps({"meta": {"filename": PROJECT + ".kicad_pro", "version": 3}}, indent=2) + "\n")
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(cad.BASE / ".tools/kicad-cli")
    exports = [
        ["erc", "--format", "json", "--severity-all", "--exit-code-violations", "-o", "checks/erc.json"],
        ["export", "netlist", "--format", "kicadxml", "-o", "checks/guard-netlist.xml"],
        ["export", "pdf", "-o", "guard-schematic.pdf"],
    ]
    for args in exports:
        subprocess.run([cli, "sch", *args, PROJECT + ".kicad_sch"], cwd=OUT, check=True)
    path = checks / "guard-netlist.xml"
    cad.validate_netlist(data, path)
    xml = ET.parse(path)
    for element in xml.findall(".//source") + xml.findall(".//uri"):
        if element.text:
            element.text = element.text.replace(str(OUT) + "/", "")
    xml.write(path, encoding="utf-8", xml_declaration=True)
    erc = checks / "erc.json"
    report = json.loads(erc.read_text())
    for sheet in report["sheets"]:
        if "source" in sheet:
            sheet["source"] = Path(sheet["source"]).name
    erc.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
