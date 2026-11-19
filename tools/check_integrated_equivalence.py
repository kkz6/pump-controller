"""Compare integrated KiCad exports to the released main and receiver pinouts."""
import hashlib
import json
import os
import re
import shutil
import subprocess
from xml.etree import ElementTree as ET

from build_integrated_source import (DROP_MAIN, DROP_RECEIVER, NET_MAP, OUT, PROJECT,
                                     R3, ROOT, SOURCE, receiver_reference)

CHECK = OUT / "checks"
NATIVE = OUT / (PROJECT + ".kicad_sch")


def pins(xml):
    return {(node.get("ref"), node.get("pin")): net.get("name")
            for net in xml.findall("nets/net") for node in net.findall("node")}


def footprints(xml):
    return {c.get("ref"): c.findtext("footprint") for c in xml.findall("components/comp")}


def assert_same(label, expected, actual):
    different = {k: (expected.get(k), actual.get(k))
                 for k in set(expected) | set(actual) if expected.get(k) != actual.get(k)}
    if different or set(expected) != set(actual):
        raise ValueError(f"{label} mismatch: {different}, missing keys {set(expected) ^ set(actual)}")


def main():
    CHECK.mkdir(parents=True, exist_ok=True)
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(ROOT / ".tools/kicad-cli")
    subprocess.run([cli, "sch", "erc", "--format", "json", "--severity-all", "--exit-code-violations",
                    "-o", "checks/erc.json", NATIVE.name], cwd=OUT, check=True)
    export = CHECK / "source.xml"
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml",
                    "-o", "checks/source.xml", NATIVE.name], cwd=OUT, check=True)
    text = export.read_text().replace(str(OUT) + "/", "")
    # KiCad stamps each export with the wall clock. Leave design and net content reproducible.
    text, edits = re.subn(r"(?m)^    <date>[^<]+</date>$", "    <date/>", text, count=1)
    if edits != 1:
        raise ValueError("Missing KiCad design export timestamp")
    export.write_text(text)
    main_netlist = R3 / "checks/independent-netlist.xml"
    receiver_netlist = ROOT / "hardware/guard-receiver/checks/source.xml"
    original = ET.parse(main_netlist)
    receiver = ET.parse(receiver_netlist)
    actual = ET.parse(export)

    retained = {k: net for k, net in pins(original).items() if k[0] not in DROP_MAIN}
    retained_fps = {r: fp for r, fp in footprints(original).items() if r not in DROP_MAIN}
    added = {}
    for (ref, num), net in pins(receiver).items():
        if ref in DROP_RECEIVER:
            continue
        newref = receiver_reference(ref)
        if net.startswith("unconnected-"):
            newnet = net.replace("(" + ref + "-", "(" + newref + "-")
        else:
            newnet = NET_MAP.get(net, net)
        added[newref, num] = newnet
    receiver_fps = {receiver_reference(ref): fp for ref, fp in footprints(receiver).items() if ref not in DROP_RECEIVER}
    assert_same("Component footprints", retained_fps | receiver_fps, footprints(actual))
    assert_same("Native pin assignments and NC aliases", retained | added, pins(actual))

    design = json.loads(SOURCE.read_text())
    guard_footprints = set()
    for s in design["sheets"]:
        for c in s["components"]:
            ref = c["ref"]
            if ref not in receiver_fps:
                continue
            lib, name = c["footprint"].split(":")
            footprint = ROOT / design["footprint_libraries"][lib] / (name + ".kicad_mod")
            guard_footprints.add(footprint)
            lands = set(re.findall(r'^\s*\(pad "([^"]+)" ', footprint.read_text(), re.M))
            pin_ids = {str(p["num"]) for p in c["pins"]}
            if lands != pin_ids:
                raise ValueError(f"{ref}: symbol pins {pin_ids} vs footprint {lands}")
    report = {
        "kicad_version": subprocess.check_output([cli, "version"], text=True).strip(),
        "source": str(NATIVE.relative_to(ROOT)),
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [main_netlist, receiver_netlist, export, *sorted(OUT.glob("*.kicad_sch"))]},
        "guard_footprint_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(guard_footprints)},
        "main_pin_assignments_preserved": len(retained),
        "receiver_pin_assignments_mapped": len(added),
        "integrated_pins_including_native_nc_aliases": len(pins(actual)),
        "nets_including_native_nc_aliases": len(actual.findall("nets/net")),
        "receiver_component_pin_sets_compared_to_land_numbers": len(receiver_fps),
        "field_connectors": {ref: {pin: net for (r, pin), net in pins(actual).items() if r == ref}
                             for ref in ["J52", "J54", "KFB1"]},
        "receiver_reference_mapping": {r: receiver_reference(r) for r in sorted(footprints(receiver)) if r not in DROP_RECEIVER},
        "removed_main": sorted(DROP_MAIN), "removed_receiver": sorted(DROP_RECEIVER),
        "receiver_net_renames": NET_MAP,
        "result": "pass",
    }
    (CHECK / "net-equivalence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Matched {len(retained)} main and {len(added)} receiver pins with {len(receiver_fps)} guard footprints.")


if __name__ == "__main__":
    main()
