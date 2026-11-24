"""Screen both boards for via holes beneath paste and DNP paste openings.

Run with KiCad's Python. This supplements ERC/DRC and CAM connectivity; it is
not a substitute for the assembler's stencil, lead-fit and placement review.
"""
import hashlib
import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]


def paste_hole_overlaps(board):
    """Conservative rectangle/circle screen in each pad's local coordinates."""
    findings = []
    vias = [v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA']
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            for paste in (pcbnew.F_Paste, pcbnew.B_Paste):
                if not pad.GetLayerSet().Contains(paste):
                    continue
                margin = pad.GetSolderPasteMargin(paste)
                width = pad.GetSize().x + 2 * margin.x
                height = pad.GetSize().y + 2 * margin.y
                if min(width, height) <= 0:
                    continue
                angle = math.radians(pad.GetOrientationDegrees())
                for via in vias:
                    copper = pcbnew.F_Cu if paste == pcbnew.F_Paste else pcbnew.B_Cu
                    if not via.GetLayerSet().Contains(copper):
                        continue
                    delta = via.GetPosition() - pad.GetPosition()
                    x = delta.x * math.cos(angle) - delta.y * math.sin(angle)
                    y = delta.x * math.sin(angle) + delta.y * math.cos(angle)
                    distance = math.hypot(max(abs(x)-width/2, 0), max(abs(y)-height/2, 0))
                    if distance < via.GetDrillValue()/2:
                        findings.append({'ref':fp.GetReference(), 'pad':pad.GetNumber(),
                                         'side':board.GetLayerName(paste),
                                         'via_xy_mm':[pcbnew.ToMM(via.GetPosition().x),
                                                      pcbnew.ToMM(via.GetPosition().y)]})
    return findings


def review(board):
    dnp_paste = []
    holes = []
    aperture_ratios = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            for side in (pcbnew.F_Paste, pcbnew.B_Paste):
                if not pad.GetLayerSet().Contains(side):
                    continue
                if fp.IsDNP():
                    dnp_paste.append(fp.GetReference()+'.'+pad.GetNumber())
                margin = pad.GetSolderPasteMargin(side)
                w = pcbnew.ToMM(pad.GetSize().x + 2*margin.x)
                h = pcbnew.ToMM(pad.GetSize().y + 2*margin.y)
                if min(w,h) > 0:
                    aperture_ratios.append(w*h/(2*(w+h)*0.12))
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                holes.append(min(pcbnew.ToMM(pad.GetSize().x-pad.GetDrillSize().x),
                                 pcbnew.ToMM(pad.GetSize().y-pad.GetDrillSize().y))/2)
    return {'via_drills_beneath_paste':paste_hole_overlaps(board),
            'DNP_paste_pads':dnp_paste,
            'minimum_PTH_annular_ring_mm':round(min(holes),4),
            'minimum_rectangular_paste_area_ratio_at_0_12mm':round(min(aperture_ratios),4),
            'limits':'Nominal geometry screen; actual lead tolerances, paste process and solder joints need assembler/first-article review.'}


def main():
    output = ROOT/'verification/dfm-review-2026-11-24/R4'
    output.mkdir(exist_ok=True)
    results = {}
    for name, stem in [('main','pump-direct'), ('panel','pump-panel-rev-f')]:
        path = ROOT/'hardware'/name/(stem+'.kicad_pcb')
        board = pcbnew.LoadBoard(str(path))
        results[name] = {'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         **review(board)}
        assert not results[name]['via_drills_beneath_paste'], (name, results[name])
        assert not results[name]['DNP_paste_pads'], (name, results[name])
        if name == 'main':
            # Mutate only the in-memory copy: prove the two original defects are detected.
            via = next(v for v in board.GetTracks() if v.GetClass() == 'PCB_VIA'
                       and v.GetPosition() == pcbnew.VECTOR2I(pcbnew.FromMM(55.175),pcbnew.FromMM(-6.6)))
            via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(55.175),pcbnew.FromMM(-5.5)))
            assert any(f['ref']=='R246' for f in paste_hole_overlaps(board))
            fp = next(f for f in board.GetFootprints() if f.GetReference()=='R2')
            for pad in fp.Pads():
                layers = pad.GetLayerSet(); layers.AddLayer(pcbnew.B_Paste); pad.SetLayerSet(layers)
            assert len(review(board)['DNP_paste_pads']) == 2
            results[name]['in_memory_negative_controls'] = ['R246 via-in-paste detected','R2 DNP paste detected']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == results[name]['board_sha256']
    (output/'manufacturing-check.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: neither board has screened via holes beneath paste or paste on DNP parts; both injected controls detected.')


if __name__ == '__main__':
    main()
