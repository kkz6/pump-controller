"""Assign Rev E routing layers and uninterrupted domain-specific reference planes."""
import pcbnew as p

def apply(board):
    # Also run during a clean build, when the board has six layers already
    # but its inherited keepouts and fixed routes still use the donor layer map.
    if any(z.GetLayer()==p.In4_Cu and not z.GetIsRuleArea() for z in board.Zones()):
        return
    if board.GetCopperLayerCount() not in (4,6):
        raise ValueError('Expected the four-layer source geometry before layer assignment')
    board.SetCopperLayerCount(6)
    for t in board.GetTracks():
        if isinstance(t,p.PCB_VIA):
            continue
        layer=t.GetLayer()
        if layer==p.In1_Cu:t.SetLayer(p.In2_Cu)
        elif layer==p.In2_Cu:t.SetLayer(p.In3_Cu)
    for z in board.Zones():
        if z.GetIsRuleArea():
            layers=z.GetLayerSet()
            for layer in [p.In3_Cu,p.In4_Cu]: layers.AddLayer(layer)
            z.SetLayerSet(layers)
        elif z.GetLayer()==p.In2_Cu:
            z.SetLayer(p.In4_Cu)
    # Mounting footprints can also carry internal rule areas.
    for f in board.GetFootprints():
        for z in f.Zones():
            if z.GetIsRuleArea() and z.GetLayerSet().Contains(p.In1_Cu):
                ls=z.GetLayerSet()
                for l in [p.In3_Cu,p.In4_Cu]:ls.AddLayer(l)
                z.SetLayerSet(ls)
