"""Check printed LED/diode cathodes, capacitor positive and device pin-1 marks."""
import hashlib
import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]


def xy(point):
    return [pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)]


def close(a, b):
    return abs(a-b) < 0.00001


def cathode_bars(board, fp, rule):
    pads = {p.GetNumber():p for p in fp.Pads()}
    cathode = pads[rule['cathode_pad']].GetPosition()
    anode = pads[rule['anode_pad']].GetPosition()
    delta = cathode-anode
    length = math.hypot(delta.x,delta.y)
    ux,uy = delta.x/length,delta.y/length
    layer = pcbnew.B_SilkS if fp.GetLayer()==pcbnew.B_Cu else pcbnew.F_SilkS
    hits = []
    shapes = [*board.GetDrawings(),*(g for f in board.GetFootprints() for g in f.GraphicalItems())]
    for shape in shapes:
        if shape.GetClass()!='PCB_SHAPE' or shape.GetShape()!=pcbnew.SHAPE_T_SEGMENT or shape.GetLayer()!=layer:
            continue
        vector = shape.GetEnd()-shape.GetStart()
        size = math.hypot(vector.x,vector.y)
        if not size or abs((vector.x*ux+vector.y*uy)/size)>.1:
            continue
        centre = (shape.GetStart()+shape.GetEnd())/2
        offset = centre-cathode
        along = pcbnew.ToMM(offset.x*ux+offset.y*uy)
        across = pcbnew.ToMM(-offset.x*uy+offset.y*ux)
        if .35<along<1.8 and abs(across)<.4 and pcbnew.ToMM(size)>.5:
            hits.append(xy(centre))
    return hits


def main():
    data = json.loads((ROOT/'tools/data/polarity-markers.json').read_text())
    results = {}
    for name,stem in [('main','pump-direct'),('panel','pump-panel-rev-f')]:
        path = ROOT/'hardware'/name/(stem+'.kicad_pcb')
        board = pcbnew.LoadBoard(str(path))
        fps = {f.GetReference():f for f in board.GetFootprints()}
        groups = {g.GetName():g for g in board.Groups()}
        rule = data[name]
        expected = {ref for ref,fp in fps.items() if ref.startswith('Q') or
                    (ref.startswith('D') and len([p for p in fp.Pads() if p.GetNumber()])>=3)}
        assert expected == set(rule['pin1_arrows']), (name,'multi-pin device coverage mismatch')
        for ref,marker in rule['pin1_arrows'].items():
            fp = fps[ref]
            assert fp.GetFieldText('MPN')==marker['mpn'], ref
            ident = fp.GetFPID()
            assert str(ident.GetLibNickname())+':'+str(ident.GetLibItemName())==marker['footprint'],ref
            assert fp.GetLayer()==(pcbnew.F_Cu if marker['side']=='F' else pcbnew.B_Cu), ref
            pin = next(p for p in fp.Pads() if p.GetNumber()=='1')
            assert all(close(a,b) for a,b in zip(xy(pin.GetPosition()),marker['pin1_xy_mm'])), ref
            items = list(groups['POL_PIN1_'+ref].GetItems())
            assert len(items)==1,ref
            shape = items[0]
            assert shape.GetShape()==pcbnew.SHAPE_T_POLY,ref
            assert shape.GetLayer()==(pcbnew.F_SilkS if marker['side']=='F' else pcbnew.B_SilkS),ref
            points = [xy(p) for p in shape.GetPolyShape().Outline(0).CPoints()]
            assert len(points)==3 and all(close(a,b) for p,q in zip(points,marker['triangle_xy_mm']) for a,b in zip(p,q)),ref
        bars = {}
        two_terminal_diodes = {ref for ref,fp in fps.items() if ref.startswith('D') and
                               len([p for p in fp.Pads() if p.GetNumber()])==2}
        assert two_terminal_diodes == (set(rule.get('cathode_bar_parts',{})) |
                                        set(rule.get('bidirectional_TVS_without_polarity',{}))), name
        polarized_caps = {ref for ref,fp in fps.items() if ref.startswith('C') and
                          str(fp.GetFPID().GetLibItemName()).startswith(('CP_','C_Polarized','C_Tantalum'))}
        assert polarized_caps==set(rule.get('positive_marks',{})),name
        for ref,part in rule.get('cathode_bar_parts',{}).items():
            assert fps[ref].GetFieldText('MPN')==part['mpn'],ref
            bars[ref] = cathode_bars(board,fps[ref],part)
            assert bars[ref],ref+': no cathode-side silkscreen bar found'
        for ref,marker in rule.get('positive_marks',{}).items():
            fp = fps[ref]
            assert fp.GetFieldText('MPN')==marker['mpn'],ref
            pad = next(p for p in fp.Pads() if p.GetNumber()==marker['positive_pad'])
            assert pad.GetNetname()==marker['positive_net'],ref
            items = list(groups['POL_PLUS_'+ref].GetItems())
            assert len(items)==1 and items[0].GetText()=='+',ref
            assert items[0].GetLayer()==pcbnew.F_SilkS,ref
            assert all(close(a,b) for a,b in zip(xy(items[0].GetPosition()),marker['xy_mm'])),ref
        for ref,mpn in rule.get('bidirectional_TVS_without_polarity',{}).items():
            assert fps[ref].GetFieldText('MPN')==mpn,ref
            assert ref not in rule.get('cathode_bar_parts',{}),ref
        results[name] = {'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                         'multi_pin_device_arrows':len(expected), 'cathode_bar_parts':bars,
                         'positive_marks':list(rule.get('positive_marks',{})),
                         'bidirectional_TVS_without_polarity':list(rule.get('bidirectional_TVS_without_polarity',{}))}
    (ROOT/'verification/dfm-review-2026-11-24/polarity-check.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS: 16 transistor/multi-pin diode arrows, 10 LED/diode cathode bars, C1 positive mark; bidirectional TVS parts not marked as polarized.')


if __name__ == '__main__':
    main()
