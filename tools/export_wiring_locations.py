"""Read native PCB connector/key positions for the illustrated wiring guide."""
import hashlib
import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/pump-controller-rev-b.kicad_pcb"
board = pcbnew.LoadBoard(str(SOURCE))
connectors = []
keys = []

for footprint in board.GetFootprints():
    reference = footprint.GetReference()
    if not (reference.startswith("J") or reference in {"SW1", "SW2", "SW3", "SW4"}):
        continue
    item = {
        "ref": reference,
        "value": footprint.GetValue(),
        "position_mm": [pcbnew.ToMM(footprint.GetPosition().x), pcbnew.ToMM(footprint.GetPosition().y)],
        "angle": footprint.GetOrientationDegrees(),
        "side": board.GetLayerName(footprint.GetLayer()),
        "pads": [
            {
                "pin": pad.GetNumber(),
                "net": pad.GetNetname(),
                "xy_mm": [pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)],
            }
            for pad in footprint.Pads()
        ],
    }
    (connectors if reference.startswith("J") else keys).append(item)

result = {
    "revision": board.GetTitleBlock().GetRevision(),
    "view": "Top component side; origin at upper-left; x right, y down; all dimensions mm. Connector pin numbers are PCB pad numbers, not mating-face left/right.",
    "board_mm": [90, 70],
    "source": str(SOURCE.relative_to(ROOT)),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "connectors": connectors,
    "onboard_keys": keys,
}
output = ROOT / "hardware/wiring/connector-locations.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + "\n")
print(f"Recorded {len(connectors)} connectors and {len(keys)} PCB keys in {output.relative_to(ROOT)}")
