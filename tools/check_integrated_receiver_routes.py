"""Measure the integrated field clamps and comparator bypass on the routed KiCad PCB."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

import pcbnew as k

from check_compact_bypasses import Board
from measure_usb_service_routes import network, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/main-integrated"
LEGS = [
    ("U301.8", "C301.1", "+5V", "Comparator 100 nF supply"),
    ("J54.1", "D307.1", "FUSED_24", "Entry TVS cathode"),
    ("J54.2", "D307.2", "CAB_0", "Entry TVS anode return"),
    ("KFB1.1", "D306.1", "KFB_A1", "Local KFB1 coil to its clamp cathode"),
    ("KFB1.16", "D306.2", "CAB_0", "Local KFB1 return to its clamp anode"),
    ("J54.4", "D303.1", "PANEL_24", "Remote KPS1 driver harness to local clamp"),
    ("J54.2", "D303.2", "CAB_0", "Remote KPS1 harness return to local clamp"),
]


def pair_name(first, last):
    return f"{first} to {last}"


def audit(path):
    reader = Board(path)
    board = reader.board

    def pad(name):
        ref, pin = name.split(".")
        return reader.pad(ref, pin)

    graphs = {}
    missing = []
    result = {}
    for start, end, net, purpose in LEGS:
        src, dst = pad(start), pad(end)
        if src.GetNetname() != net or dst.GetNetname() != net:
            raise ValueError(f"{start} and {end} must both be {net}")
        if net not in graphs:
            graphs[net] = network(board, net)
        entry = {"net": net, "function": purpose,
                 "pad_separation_mm": round(math.dist(tuple(src.GetPosition()), tuple(dst.GetPosition())) / 1e6, 3)}
        try:
            length, vias, steps, _ = walk(graphs[net], start, {end})
            per_layer = defaultdict(float)
            for step in steps:
                if step[0] != "via":
                    _, layer, a, b = step
                    per_layer[board.GetLayerName(layer)] += math.dist(a, b) / 1e6
            entry.update(track_and_land_length_mm=round(length, 3), routed_via_transitions=vias,
                         xy_length_by_copper_layer_mm={layer: round(mm, 3) for layer, mm in sorted(per_layer.items())})
        except ValueError:
            missing.append(pair_name(start, end))
        result[pair_name(start, end)] = entry
    returns = {}
    for name in ["U301.4", "C301.2"]:
        item = pad(name)
        if item.GetNetname() != "GND":
            raise ValueError(f"{name} should return to logic GND")
        try:
            returns[name] = reader.route(item, item.GetParentFootprint().GetLayer())
        except ValueError as err:
            returns[name] = {"finding": str(err)}
            missing.append(name + " to In1 GND plane")
    common = all("plane_island" in v for v in returns.values()) and len({v["plane_island"] for v in returns.values()}) == 1
    if not common:
        missing.append("Comparator and capacitor need common GND island")
    field = {str(i): pad(f"J54.{i}").GetNetname() for i in range(1, 6)}
    if field != {"1":"FUSED_24","2":"CAB_0","3":"HB_24","4":"PANEL_24","5":"KFB_A1"}:
        raise ValueError(f"Incorrect field header pinout: {field}")
    return {"kicad_version": k.GetBuildVersion(), "board_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "revision": board.GetTitleBlock().GetRevision(), "measured_legs": result,
            "comparator_returns_to_inner_ground": returns, "comparator_shares_inner_ground_island":common,
            "field_header": {"1": "Protected 24 V input", "2": "Cabinet return", "3": "PNP sourcing output to WD1",
                             "4": "PNP sourcing output to remote KPS1", "5": "Cabinet proof input energizing local KFB1"},
            "flyback_diodes": {"D306": "Across KFB1 pins 1/16. Cathode on coil positive.",
                               "D303": "Across J54.4/.2 at the board. KPS1 also requires D9 at the physical remote coil."},
            "scope": "Shortest continuous XY centreline/land path on explicit copper. Barrel height and current spreading in planes are excluded. GND return measurements terminate at a via on a verified filled In1 GND island. Geometry does not establish clamp voltage, inductance, contact release time, immunity or EMC.",
            "missing_routes":missing, "electrically_bench_tested":False}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, default=OUT / "pump-controller-integrated.kicad_pcb")
    ap.add_argument("--output", type=Path, default=OUT / "checks/receiver-routing.json")
    args = ap.parse_args()
    data = audit(args.board)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    if data["missing_routes"]:
        raise SystemExit("Incomplete routed witnesses: " + ", ".join(data["missing_routes"]))
