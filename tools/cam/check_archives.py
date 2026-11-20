"""Compare the archived copper islands and plated holes with named IPC-D-356 nets.

Use Gerbonara and a built compare.cpp driver. Build the driver against the pinned
GerberTools source by compiling it with src/*.cpp, -std=c++17, -Iinclude and -Isrc.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from gerbonara.ipc356 import Netlist
from gerbonara.utils import MM

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "integrated": "hardware/main-integrated/pump-controller-integrated-r4-gerber-prototype.zip",
    "main": "hardware/main-compact-dual/pump-controller-compact-dual-guard-r3-gerber-prototype.zip",
    "panel": "hardware/panel-rev-f/pump-panel-rev-f-gerber-prototype.zip",
    "receiver": "hardware/guard-receiver/guard-receiver-rev-a-gerber-prototype.zip",
}
UPSTREAM = "7d797b51b13da8060e27d5b16444052a73c5fc32"


def extract(archive_path, directory, layers):
    suffixes = [".gbl"] + ([".g5l", ".g4l", ".g3l", ".g2l"] if layers == 6 else []) + [".gtl"]
    members = {f"L{idx}.gbr": (suffix,) for idx, suffix in enumerate(suffixes)}
    members.update({"outline.gbr": (".gko", ".gm1"), "pth.drl": ("-pth.xln", "-pth.drl"),
                    "npth.drl": ("-npth.xln", "-npth.drl"), "ref.d356": (".d356",)})
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Bad CRC in {archive_path}")
        for target, endings in members.items():
            matches = [name for name in archive.namelist() if name.lower().endswith(endings)]
            if len(matches) != 1:
                raise ValueError(f"{archive_path}: ambiguous or missing {target}: {matches}")
            data = archive.read(matches[0])
            if target.endswith(".gbr"):
                data = re.sub(rb"(?m)^%(?:TD|TO)[^%\r\n]*\*%\r?\n", b"", data)
            (directory / target).write_bytes(data)


def witnesses(directory, layers):
    rows, names, pads = [], set(), {}
    records = 0
    for record in Netlist.open(directory / "ref.d356").test_records:
        pin = getattr(record, "pin", None) or record.pin_num
        if not record.net_name and not (record.ref_des and pin and record.is_connected is False):
            continue
        if record.access_layer not in (0, 1, layers):
            raise ValueError(f"Unexpected IPC access face {record}")
        net = record.net_name
        if not net or net == "N/C":
            net = f"NC_{record.ref_des}_{pin}"
        x, y = [record.unit.convert_to(MM, value) for value in (record.x, record.y)]
        faces = [0, layers - 1] if record.access_layer == 0 else [layers - record.access_layer]
        for face in faces:
            rows.append(f"{x:.6f}\t{y:.6f}\t{face}\t{net}\n")
        pads[record.ref_des, str(pin)] = (x, y, faces, net)
        names.add(net)
        records += 1
    (directory / "logical.tsv").write_text("".join(rows))
    return pads, dict(ipc_records=records, ipc_named_nets=len(names), layer_witnesses=len(rows))


def compare(driver, directory, layers, count, expect_fault=False):
    result = subprocess.run([driver, directory, str(layers)], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    if not lines or lines[0] != f"witnesses {count} findings {len(lines)-1}":
        raise ValueError(f"Failed to read all CAM witnesses: {result.stderr} {result.stdout}")
    if expect_fault:
        if result.returncode != 2 or len(lines) < 2:
            raise ValueError(f"Injected fault escaped detection: {result.stdout}")
    elif result.returncode or len(lines) != 1:
        raise ValueError(f"Archive connectivity failed: {result.stdout} {result.stderr}")
    return lines[1:]


def check(name, driver, relative=None):
    relative = relative or FILES[name]
    archive = ROOT / relative
    layers = 6 if name in ("main", "integrated") else 2
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        extract(archive, directory, layers)
        pads, counts = witnesses(directory, layers)
        compare(driver, directory, layers, counts["layer_witnesses"])
        # Bridge two unlike nets using the independently exported connector pad centres.
        ref = {"integrated": "J1", "main": "J1", "panel": "J2", "receiver": "J4"}[name]
        a, b = [pads[ref, pin] for pin in ("1", "2")]
        face = next(iter(sorted(set(a[2]) & set(b[2]), reverse=True)))
        plot = directory / f"L{face}.gbr"
        original = plot.read_text()
        if not re.search(r"%FSLAX\d6Y\d6\*%", original) or original.count("M02*") != 1:
            raise ValueError("Fault fixture requires six metric decimal places and a single end command")
        stroke = "%ADD900C,0.40*%\n%LPD*%\nD900*\n"
        for point, command in ((a, "02"), (b, "01")):
            stroke += f"X{round(point[0]*1e6)}Y{round(point[1]*1e6)}D{command}*\n"
        plot.write_text(original.replace("M02*", stroke + "M02*"))
        findings = compare(driver, directory, layers, counts["layer_witnesses"], True)
        if not any(a[3] in msg and b[3] in msg and "short-circuited" in msg for msg in findings):
            raise ValueError(f"Incorrect fault diagnostic: {findings}")
        controls = [dict(board=name, injected=f"Bridge {ref}.1 and {ref}.2 on layer {face} (bottom = 0)",
                         findings=findings)]
        if name in ("main", "integrated"):
            # Retain the R2 inner-layer open control as well as the inlet short.
            plot.write_text(original)
            inner = directory / "L2.gbr"  # G4L / In3.Cu in a six-layer board
            dark = inner.read_text()
            open_trace = "%ADD900C,0.35*%\n%LPC*%\nD900*\nX35400000Y-31875000D03*\n%LPD*%\n"
            inner.write_text(dark.replace("M02*", open_trace + "M02*"))
            findings = compare(driver, directory, layers, counts["layer_witnesses"], True)
            if findings != ["logical net M_MISO is divided up into 2 islands"]:
                raise ValueError(f"Incorrect inner-layer open diagnostic: {findings}")
            controls.append(dict(board=name, injected="Open M_MISO on In3.Cu at (35.400, -31.875) mm",
                                 findings=findings))
        if name == "panel":
            # Retain the J2.3 landing but disconnect it from the hardwired STOP trace.
            x, y, _, net = pads["J2", "3"]
            point = f"X{round(x*1e6)}Y{round(y*1e6)}D03*"
            clear = (f"%ADD900C,2.50*%\n%ADD901C,0.20*%\n%LPC*%\nD900*\n{point}\n"
                     f"%LPD*%\nD901*\n{point}\n")
            plot.write_text(original.replace("M02*", clear + "M02*"))
            findings = compare(driver, directory, layers, counts["layer_witnesses"], True)
            if not any(net in finding and "divided" in finding for finding in findings):
                raise ValueError(f"Incorrect remote STOP open diagnostic: {findings}")
            controls.append(dict(board=name, injected="Isolate J2.3 from the panel STOP trace", findings=findings))
        if name == "receiver":
            top = directory / "L1.gbr"
            # Disconnect R17 from its routed trace while retaining its IPC landing.
            clear = ("%ADD900C,1.90*%\n%ADD901C,0.40*%\n%LPC*%\nD900*\nX30000000Y-8288000D03*\n"
                     "%LPD*%\nD901*\nX30000000Y-8288000D03*\n")
            top.write_text(original.replace("M02*", clear + "M02*"))
            findings = compare(driver, directory, layers, counts["layer_witnesses"], True)
            if findings != ["logical net HB_LED_A is divided up into 2 islands"]:
                raise ValueError(f"Incorrect open-circuit diagnostic: {findings}")
            controls.append(dict(board=name, injected="Isolate R17 on front copper at (30.000, -8.288) mm",
                                 findings=findings))
    return dict(path=relative, sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                copper_layers=layers, **counts, opens_shorts=0), controls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path)
    parser.add_argument("--boards", nargs="+", choices=FILES, default=["main","panel","receiver"])
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    result = dict(tool="jvanstraten/gerbertools", upstream_commit=UPSTREAM,
                  method="Nominal Gerber copper and plated drill connectivity against every named IPC-D-356 record. Physical bare-board and insulation tests are separate.",
                  archives=[], negative_controls=[])
    for board in options.boards:
        entry, controls = check(board, options.driver.resolve())
        result["archives"].append(entry)
        result["negative_controls"].extend(controls)
    report = json.dumps(result, indent=2) + "\n"
    if options.output:
        options.output.write_text(report)
    print(report, end="")
