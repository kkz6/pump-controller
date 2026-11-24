"""Screen closed nominal fabrication bodies; run with KiCad Python and Shapely.

This is a placement screen, not a maximum-tolerance or solder-process approval.
Open decoration lines, text and screw circles are not treated as body outlines.
"""
import hashlib
import itertools
import json
from pathlib import Path
import pcbnew
from shapely.geometry import Polygon, LineString, box
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'verification/dfm-review-2026-11-24/R4/body-spacing.json'


def xy(p):
    return [pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)]


def body(fp):
    layer = pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab
    polys, lines = [], []
    for item in fp.GraphicalItems():
        if item.GetClass() != 'PCB_SHAPE' or item.GetLayer() != layer:
            continue
        if item.GetShape() == pcbnew.SHAPE_T_RECT:
            (x,y),(u,v) = xy(item.GetStart()),xy(item.GetEnd())
            polys.append(box(min(x,u),min(y,v),max(x,u),max(y,v)))
        elif item.GetShape() == pcbnew.SHAPE_T_POLY:
            shape = item.GetPolyShape()
            polys.extend(Polygon([xy(p) for p in shape.Outline(i).CPoints()])
                         for i in range(shape.OutlineCount()))
        elif item.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            lines.append(LineString([xy(item.GetStart()),xy(item.GetEnd())]))
    polys.extend(polygonize(unary_union(lines)))
    polys = [p for p in polys if p.is_valid and p.area > 0]
    if not polys:
        return None
    merged = unary_union(polys)
    return max(merged.geoms, key=lambda p:p.area) if merged.geom_type == 'MultiPolygon' else merged


def main():
    result = {}
    for name,stem in [('main','pump-direct'),('panel','pump-panel-rev-f')]:
        path = ROOT/'hardware'/name/(stem+'.kicad_pcb')
        board = pcbnew.LoadBoard(str(path))
        fps = list(board.GetFootprints())
        bodies = [(fp,body(fp)) for fp in fps if not fp.IsDNP()]
        bodies = [(fp,p) for fp,p in bodies if p is not None]
        overlaps, close = [], []
        for (a,p),(b,q) in itertools.combinations(bodies,2):
            if a.GetLayer() != b.GetLayer():
                continue
            gap = p.distance(q)
            pair = {'refs':[a.GetReference(),b.GetReference()],
                    'nominal_body_gap_mm':round(gap,4),
                    'body_bbox':[list(p.bounds),list(q.bounds)]}
            if p.intersection(q).area > 0.00001:
                overlaps.append(pair)
            elif gap < .65:
                close.append(pair)
        result[name] = {
            'board_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'native_footprints_including_DNP_and_mounts':len(fps),
            'method':'Union of closed nominal F.Fab/B.Fab polygons; largest connected region per part; excludes text, circles and open decorations. Adjacent closed body compartments are merged. Maximum tolerances and physical solderability remain unqualified.',
            'nominal_body_overlaps':overlaps, 'body_pairs_below_0_65mm':close,
        }
        assert not overlaps, (name,overlaps)
    OUT.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: no same-side intersections of screened nominal fabrication bodies.')


if __name__ == '__main__':
    main()
