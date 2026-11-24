"""Verify physical pin-1 arrow coverage for every native main-board IC."""
import hashlib
import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]


def near(a, b):
    return abs(a-b) < 0.00001


def main():
    path = ROOT/'hardware/main/pump-direct.kicad_pcb'
    board = pcbnew.LoadBoard(str(path))
    registry = json.loads((ROOT/'tools/data/ic-pin1-markers.json').read_text())
    ics = {f.GetReference():f for f in board.GetFootprints() if f.GetReference().startswith('U')}
    groups = {g.GetName():g for g in board.Groups() if g.GetName().startswith('IC_PIN1_')}
    assert set(registry) == set(ics), 'Every IC, including power modules, needs a reviewed pin-1 marker'
    assert set(groups) == {'IC_PIN1_'+r for r in ics}, 'Marker group coverage mismatch'
    checked = {}
    for ref, fp in ics.items():
        rule = registry[ref]
        assert fp.GetFieldText('MPN') == rule['mpn'], ref+': marker requires exact-part review'
        ident = fp.GetFPID()
        assert str(ident.GetLibNickname())+':'+str(ident.GetLibItemName()) == rule['footprint'], ref
        assert fp.GetLayer() == (pcbnew.F_Cu if rule['side']=='F' else pcbnew.B_Cu), ref
        pad = next(p for p in fp.Pads() if p.GetNumber()=='1')
        pin = [pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)]
        assert all(near(a,b) for a,b in zip(pin,rule['pin1_xy_mm'])), ref+': pad-1 position changed'
        items = list(groups['IC_PIN1_'+ref].GetItems())
        assert len(items) == 1, ref+': expected one arrow polygon'
        shape = items[0]
        assert shape.GetClass() == 'PCB_SHAPE' and shape.GetShape() == pcbnew.SHAPE_T_POLY, ref
        assert shape.GetLayer() == (pcbnew.F_SilkS if rule['side']=='F' else pcbnew.B_SilkS), ref
        points = [[pcbnew.ToMM(p.x),pcbnew.ToMM(p.y)] for p in shape.GetPolyShape().Outline(0).CPoints()]
        assert len(points) == 3, ref
        assert all(near(a,b) for p,q in zip(points,rule['triangle_xy_mm']) for a,b in zip(p,q)), ref
        # Triangle vertex zero points toward the actual numbered pin 1.
        tip = points[0]; base = [(points[1][i]+points[2][i])/2 for i in (0,1)]
        direction = [tip[i]-base[i] for i in (0,1)]
        target = [pin[i]-tip[i] for i in (0,1)]
        assert sum(a*b for a,b in zip(direction,target)) > 0, ref
        assert abs(direction[0]*target[1]-direction[1]*target[0]) < 0.00001, ref
        checked[ref] = {'mpn':rule['mpn'], 'side':rule['side'], 'pin1_xy_mm':pin,
                        'arrow_tip_xy_mm':tip}
    result = {'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'marked_IC_count':len(checked), 'all_ICs_marked':True, 'parts':checked,
              'supplier_model_orientation_approved':False}
    (ROOT/'verification/dfm-review-2026-11-24/ic-pin1-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS:',len(checked),'ICs have side-correct arrows pointing to actual pad 1; exact MPN/footprint/positions checked.')


if __name__ == '__main__':
    main()
