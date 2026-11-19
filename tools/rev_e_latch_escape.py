"""Keep the latch supply local and reserve separate exits for its asynchronous signals."""
import pcbnew as p

def attach(board):
    layer=p.B_Cu
    def xy(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
    def line(name, width, *points):
        for a,b in zip(points,points[1:]):
            t=p.PCB_TRACK(board);t.SetLayer(layer);t.SetWidth(p.FromMM(width))
            t.SetStart(xy(*a));t.SetEnd(xy(*b));t.SetNet(board.FindNet(name));board.Add(t)
    def via(name,x,y):
        v=p.PCB_VIA(board);v.SetPosition(xy(x,y));v.SetWidth(p.FromMM(.65))
        v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH)
        v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(board.FindNet(name));board.Add(v)
    line('+3V3',.18,(78.75,27.95),(78.25,27.95),(78.25,29.5),(78.25,31.05))
    line('+3V3',.18,(78.25,31.05),(78.25,31.67),(78.01,32.025))
    via('+3V3',78.01,32.025)
    line('GND',.18,(77.25,31.05),(77.25,31.70),(77.02,31.93))
    via('GND',77.02,31.93)
    line('ARM_Q',.18,(77.25,27.95),(77.25,27.5),(76.65,26.90))
    via('ARM_Q',76.65,26.90)
    line('ARM_CLEAR_N',.18,(77.75,27.95),(77.75,26.6))
    via('ARM_CLEAR_N',77.75,26.6)
    line('ARM_CMD',.18,(78.75,31.05),(78.75,32.925),(78.675,33.0))
    # Local bypass loop for the reset Schmitt buffer.
    line('+3V3',.30,(83.1375,38.45),(85.325,38.45),(85.5,38.275))
    line('GND',.24,(80.8625,36.55),(81.7625,35.65),(84.425,35.65),(85.5,36.725))
