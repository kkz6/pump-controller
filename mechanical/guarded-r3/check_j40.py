"""Check the physical port interface directly from an R3 KiCad main PCB."""
import argparse,json
from pathlib import Path
import pcbnew as p

folder=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--board',type=Path,default=folder.parents[1]/'hardware/main-compact-dual/pump-controller-compact.kicad_pcb')
args=parser.parse_args()
board=p.LoadBoard(str(args.board.resolve()))
part=next(f for f in board.GetFootprints() if f.GetReference()=='J40')
assert part.GetFPID().GetLibItemName()=='USB_C_GCT_USB4110_12Lands' and not part.IsFlipped()
assert part.GetOrientationDegrees()==90
rect=next(g for g in part.GraphicalItems() if isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.F_Fab and g.GetShape()==p.SHAPE_T_RECT)
xyz=lambda point:[round(p.ToMM(point.x),4),round(p.ToMM(point.y),4)]
ends=[xyz(rect.GetStart()),xyz(rect.GetEnd())]
x=max(x for x,y in ends);y=sum(y for x,y in ends)/2
assert [x,y]==[100.,20.]
assert any(isinstance(g,p.PCB_SHAPE) and g.GetLayer()==p.Edge_Cuts and
           abs(p.ToMM(g.GetStart().x)-x)<.001 and abs(p.ToMM(g.GetEnd().x)-x)<.001 and
           min(p.ToMM(g.GetStart().y),p.ToMM(g.GetEnd().y))<=y<=max(p.ToMM(g.GetStart().y),p.ToMM(g.GetEnd().y)) for g in board.GetDrawings())
report={'footprint':str(part.GetFPID().GetLibItemName()),'footprint_side':'F',
        'fab_rectangle_ends_mm':ends,'native_mouth_mm':[x,y],'native_mouth_direction':'+X',
        'case_transform':'X=112-native Y; Y=125-native X; PCB underside Z=24',
        'case_mouth_mm':[112-y,125-x,27.28],'pcb_thickness_mm':p.ToMM(board.GetDesignSettings().GetBoardThickness())}
assert report['pcb_thickness_mm']==1.6
(folder/'j40-interface.json').write_text(json.dumps(report,indent=2)+'\n')
print(report)
