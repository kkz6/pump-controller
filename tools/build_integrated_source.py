"""Materialize the integrated guard schematic and BOM from design/main-integrated.json."""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

import build_guard_receiver
import generate_cad as cad

ROOT = cad.BASE
OUT = ROOT / "hardware/main-integrated"
R3 = ROOT / "hardware/main-compact-dual"
SOURCE = ROOT / "design/main-integrated.json"
OLD_PROJECT = "pump-controller-compact"
PROJECT = "pump-controller-integrated"
REVISION = "INTEGRATED-R4"
DROP_MAIN = {"J31", "J36"}
DROP_RECEIVER = {"J3", "J31", "J36", "H1", "H2", "H3", "H4"}
NET_MAP = {"ISO_5": "+5V", "ISO_0": "GND", "HOST_LOGIC": "HOST_AUX_N",
           "LOCAL_LOGIC": "LOCAL_AUX_N", "PANEL_MON": "PANEL_OK_MON",
           "J31_1": "STOP_RETURN", "J31_2": "K1_COIL_PLUS"}
SHEET_MAP = {"receiver": "guard_inputs", "cabinet": "guard_field", "plugs": "guard_ports"}


def receiver_reference(ref):
    if ref in {"J2", "J4", "KFB1"}:
        return {"J2": "J52", "J4": "J54", "KFB1": "KFB1"}[ref]
    match = re.fullmatch(r"([DCRQU])(\d+)", ref)
    if not match:
        raise ValueError(f"Unexpected integrated receiver part {ref}")
    return match[1] + str(300 + int(match[2]))


def derive():
    """Initial migration. Preserve routed placement if refreshing an existing R4 source."""
    design = json.loads((ROOT / "design/main-compact-dual.json").read_text())
    design.update(project=PROJECT, revision=REVISION, title="Single-phase pump controller with integrated guard receiver")
    design["board"]["variant"] = "integrated"
    sheet_notes = {
        "relay_protection_2": "KFB1 closes the K1 permit. Cabinet STOP and the independent high-high float interrupt the field contactors in HOST and LOCAL.",
        "local_controls_2": "J32 connects to the OLED/button board. J52 returns HOST/LOCAL position. Heartbeat and panel STOP monitor links run on this PCB.",
    }
    part_notes = {
        "U35": "K1 coil-positive Schmitt detector. Opening panel STOP or the KFB1 normally open permit contact clears ARM in hardware.",
        "R196": "1 kΩ series resistor from HEARTBEAT to the integrated guard comparator input channel.",
        "R197": "1 kΩ series resistor from the raw panel STOP return to the integrated guard comparator input channel.",
        "J52": "Position auxiliary contacts only. Pin 1 logic GND, 2 HOST return, 3 LOCAL return. JST PHR-3 housing.",
        "J54": "Independent cabinet guard interface. Pin 1 fused regulated 24 V, 2 cabinet 0 V, 3 sourced watchdog pulse to WD1, 4 sourced panel permission to KPS1, 5 permission relay coil feed from the cabinet auxiliaries. JST VHR-5N housing.",
        "KFB1": "Guard permission relay. The cabinet drives coil 1/16. Normally open contact 4/8 gates the main K1 coil supply. The other contacts remain open-circuit.",
    }
    for sheet in design["sheets"]:
        if sheet["id"] in sheet_notes:
            sheet["notes"] = sheet_notes[sheet["id"]]
        sheet["components"] = [c for c in sheet["components"] if c["ref"] not in DROP_MAIN]
    for sheet in build_guard_receiver.pcb_design()["sheets"]:
        parts = []
        for part in sheet["components"]:
            if part["ref"] in DROP_RECEIVER:
                continue
            part["ref"] = receiver_reference(part["ref"])
            # Integrated placements come from the routed main board. Legacy XYs are relative to the receiver.
            part.pop("placement", None)
            for pin in part["pins"]:
                pin["net"] = NET_MAP.get(pin.get("net"), pin.get("net"))
                pin["name"] = NET_MAP.get(pin["name"], pin["name"])
            if part["ref"] in {"J52", "J54"}:
                series = "PH" if part["ref"] == "J52" else "VH"
                part["datasheet"] = f"https://www.jst-mfg.com/product/pdf/eng/e{series}.pdf"
            parts.append(part)
        meta = {
            "receiver": ("Guard heartbeat and panel STOP receivers", "U301 and both input channels draw from isolated logic +5V. U302 and U303 couple signals to the independent 24 V guard."),
            "cabinet": ("Independent 24 V guard drivers and permission contact", "CAB_0 is the cabinet return. KFB1 coil and transistor outputs belong to this domain. KFB1 COM/NO are in the controller logic domain."),
            "plugs": ("Guard and selector field connectors", "J52 goes to dry position contacts. J54 connects to the cabinet guard. The OEM STOP and NC high-high float stay wired into the cabinet guard."),
        }
        title, notes = meta[sheet["id"]]
        design["sheets"].append(dict(id=SHEET_MAP[sheet["id"]], title=title, notes=notes, components=parts))
    for sheet in design["sheets"]:
        for part in sheet["components"]:
            if part["ref"] in part_notes:
                part["description"] = part_notes[part["ref"]]
    if SOURCE.exists():
        existing = json.loads(SOURCE.read_text())
        design["board"] = existing["board"]
        placed = {p["ref"]: p["placement"] for s in existing["sheets"] for p in s["components"] if "placement" in p}
        for sheet in design["sheets"]:
            for part in sheet["components"]:
                if part["ref"] in placed:
                    part["placement"] = placed[part["ref"]]
    return design


def guard_silk(text):
    """Thicken only silkscreen graphic strokes in the new footprint cache."""
    def graphics(match):
        item = match[0]
        if '(layer "F.SilkS")' in item or '(layer "B.SilkS")' in item:
            item = re.sub(r"\(width ([\d.]+)\)",
                          lambda w: "(width 0.16)" if 0 < float(w[1]) < .16 else w[0], item)
        return item
    return re.sub(r"(?ms)^\t\(fp_(?:line|rect|poly|arc|circle|curve)\b.*?^\t\)", graphics, text)


def set_footprints(design, refresh):
    """Use released compact land patterns where available, and vendor the missing guard footprints."""
    previous = (R3 / "fp-lib-table").read_text()
    previous_libs = {name: Path(uri.replace("${KIPRJMOD}", str(R3))).resolve()
                     for name, uri in re.findall(r'\(name "(.*?)"\).*?\(uri "(.*?)"\)', previous)}
    used = defaultdict(set)
    for sheet in design["sheets"]:
        for part in sheet["components"]:
            if part.get("on_board", True):
                library, footprint = part["footprint"].split(":")
                used[library].add(footprint)
    stock = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", ROOT / ".tools/kicad-volume/KiCad/KiCad.app/Contents/SharedSupport/footprints"))
    table = []
    folders = {}
    for library, names in sorted(used.items()):
        base = previous_libs.get(library)
        if base and all((base / (name + ".kicad_mod")).exists() for name in names):
            folder = base
        else:
            folder = OUT / "libraries" / (library + ".pretty")
            if refresh:
                folder.mkdir(parents=True, exist_ok=True)
                for name in sorted(names):
                    filename = name + ".kicad_mod"
                    source = base / filename if base else None
                    is_new = not source or not source.exists()
                    if is_new:
                        source = stock / (library + ".pretty") / filename
                    text = guard_silk(source.read_text()) if is_new else source.read_text()
                    if name == "JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical":
                        # 0.325 mm radial annulus on the 0.75 mm finished holes.
                        if text.count("(size 1.2 1.75)") != 3:
                            raise ValueError("Unexpected PH3 source land dimensions")
                        text = text.replace("(size 1.2 1.75)", "(size 1.4 1.75)")
                    (folder / filename).write_text(text)
        for name in names:
            if not (folder / (name + ".kicad_mod")).is_file():
                raise FileNotFoundError(f"Missing {library}:{name}. Refresh footprint cache with --refresh-footprints and KiCad 10 libraries.")
        folders[library] = folder.relative_to(ROOT).as_posix()
        uri = "${KIPRJMOD}/" + os.path.relpath(folder, OUT)
        table.append(f'(lib (name "{library}") (type "KiCad") (uri "{uri}") (options "") (descr "Released main board land patterns"))')
    (OUT / "fp-lib-table").write_text("(fp_lib_table (version 7)\n" + "\n".join(table) + "\n)\n")
    if refresh:
        for model in (R3 / "libraries/CompactGuard.3dshapes").glob("*.step"):
            dest = OUT / "libraries/CompactGuard.3dshapes" / model.name
            dest.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(model, dest)
    return folders


def sync_layout(design, pcb_path):
    """Record the routed layout dimensions and component transforms in the editable source."""
    import pcbnew

    board = pcbnew.LoadBoard(str(pcb_path.resolve()))
    if board.GetTitleBlock().GetRevision() != REVISION:
        raise ValueError(f"Expected a routed {REVISION} main board")
    polygons = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(polygons, False) or polygons.OutlineCount() != 1:
        raise ValueError("Expected one closed board outline")
    outline = polygons.BBox()
    design["board"].update(width=pcbnew.ToMM(outline.GetWidth()), height=pcbnew.ToMM(outline.GetHeight()),
                           layers=board.GetCopperLayerCount())
    parts = {f.GetReference(): f for f in board.GetFootprints()}
    intended = {c["ref"]: c for s in design["sheets"] for c in s["components"] if c.get("on_board", True)}
    if set(parts) != set(intended):
        raise ValueError(f"Different schematic/board references: {set(parts) ^ set(intended)}")
    for name, c in intended.items():
        part = parts[name]
        pos = part.GetPosition()
        c["placement"] = dict(x=pcbnew.ToMM(pos.x), y=pcbnew.ToMM(pos.y),
                              rotation=part.GetOrientationDegrees(), side="B" if part.IsFlipped() else "F")


def render(design):
    # Retain the native R3 sheet IDs. Its first 16 sheets originated in a different project.
    old_root = (R3 / (OLD_PROJECT + ".kicad_sch")).read_text()
    root_uid = re.search(r'^\(uuid "(.*?)"\)', old_root, re.M)[1]
    replacements = {cad.uid(OLD_PROJECT + ":root"): root_uid}
    for line in old_root.splitlines():
        if line.startswith("(sheet "):
            file = re.search(r'\(property "Sheetfile" "(.*?)\.kicad_sch"', line)[1]
            replacements[cad.uid(OLD_PROJECT + ":sheet:" + file)] = re.search(r'\(uuid "(.*?)"\)', line)[1]
            prior = (R3 / (file + ".kicad_sch")).read_text()
            replacements[cad.uid(OLD_PROJECT + ":file:" + file)] = re.search(r'^\(uuid "(.*?)"\)', prior, re.M)[1]
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        cad.write_schematics(design, work, OLD_PROJECT)
        for path in work.iterdir():
            text = path.read_text()
            for old, new in replacements.items():
                text = text.replace(old, new)
            name = path.name
            if name == OLD_PROJECT + ".kicad_sch":
                name = PROJECT + ".kicad_sch"
                text = text.replace('(paper "A3")', '(paper "A2")')
            text = text.replace(f'(project "{OLD_PROJECT}"', f'(project "{PROJECT}"')
            text = text.replace(f'(rev "{REVISION}-DRAFT")', f'(rev "{REVISION}")')
            (OUT / name).write_text(text)
    cad.write_bom(design, OUT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--derive", action="store_true", help="Migrate the R3 main and receiver sources. By default render the existing R4 source.")
    parser.add_argument("--refresh-footprints", action="store_true", help="Copy newly required land patterns from the installed KiCad 10 footprint library.")
    parser.add_argument("--placement-from", type=Path, metavar="PCB", help="Synchronize all placements and the outline from an R4 PCB using KiCad Python.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    design = derive() if args.derive else json.loads(SOURCE.read_text())
    folders = set_footprints(design, args.refresh_footprints)
    if args.placement_from:
        sync_layout(design, args.placement_from)
    if args.derive or args.placement_from:
        design["footprint_libraries"] = folders
        SOURCE.write_text(json.dumps(design, indent=2) + "\n")
    render(design)
