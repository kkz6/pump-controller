"""Measure direct four-layer conversions of the compact layout in temporary projects.

Run with KiCad's Python interpreter. Retains the routed geometry and component
placement. The two variants are engineering comparisons, not production layouts.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'hardware/main-compact'
BOARD = PROJECT / 'pump-controller-compact.kicad_pcb'


def trial(folder, swap_and_fill):
    file = folder / BOARD.name
    for source in [*PROJECT.glob('*.kicad_sch'), BOARD.with_suffix('.kicad_pro'),
                   BOARD.with_suffix('.kicad_dru'), PROJECT / 'Pump.kicad_sym',
                   PROJECT / 'fp-lib-table', PROJECT / 'sym-lib-table']:
        shutil.copy2(source, folder / source.name)
    (folder / 'libraries').symlink_to((ROOT / 'hardware/main-rev-e/libraries').resolve())
    board = pcb.LoadBoard(str(BOARD))
    layers = {pcb.In2_Cu: pcb.In1_Cu, pcb.In3_Cu: pcb.In2_Cu}
    if swap_and_fill:
        layers = {pcb.In2_Cu: pcb.In2_Cu, pcb.In3_Cu: pcb.In1_Cu}
    for track in board.GetTracks():
        if not isinstance(track, pcb.PCB_VIA) and track.GetLayer() in layers:
            track.SetLayer(layers[track.GetLayer()])
    zones = list(board.Zones()) + [zone for part in board.GetFootprints() for zone in part.Zones()]
    for zone in zones:
        if zone.GetIsRuleArea():
            active = zone.GetLayerSet()
            active.RemoveLayer(pcb.In3_Cu)
            active.RemoveLayer(pcb.In4_Cu)
            zone.SetLayerSet(active)
        elif zone.GetLayer() == pcb.In4_Cu:
            zone.SetLayer(pcb.In2_Cu)
    if swap_and_fill:
        outer = {'GND': pcb.F_Cu, '+3V3': pcb.B_Cu}
        for zone in list(board.Zones()):
            if zone.GetIsRuleArea() or zone.GetLayer() not in (pcb.In1_Cu, pcb.In2_Cu):
                continue
            if zone.GetNetname() in outer:
                extra = pcb.Cast_to_ZONE(zone.Duplicate(False))
                extra.SetLayer(outer[zone.GetNetname()])
                board.Add(extra)
    board.SetCopperLayerCount(4)
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(file), board)
    report = folder / 'drc.json'
    subprocess.run([str(ROOT / '.tools/kicad-cli'), 'pcb', 'drc', '--all-track-errors',
                    '--severity-all', '--schematic-parity', '--format', 'json',
                    '-o', str(report), str(file)], check=True, capture_output=True)
    drc = json.loads(report.read_text())
    return {k: len(drc[k]) for k in ['violations', 'unconnected_items', 'schematic_parity']}


if __name__ == '__main__':
    result = {'six_layer_source_sha256': hashlib.sha256(BOARD.read_bytes()).hexdigest()}
    for name, swap in [('direct', False), ('swapped_with_outer_fills', True)]:
        with tempfile.TemporaryDirectory(prefix='pump-4layer-') as path:
            result[name] = trial(Path(path), swap)
    print(json.dumps(result, indent=2))
