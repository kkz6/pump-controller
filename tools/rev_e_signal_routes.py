"""Fixed Rev E USB and ADE7953 clock geometry; millimetres, six-layer board.

USB uses F.Cu with one symmetric through-via pair per signal and a short
In2.Cu crossover. In1.Cu remains the continuous ground reference. Dimensions
are a routing proposal, not a 90-ohm claim without the fabricator's stackup.
"""
import pcbnew as p


def set_placements(components):
    moves = {
        'R27': (74.2, 30.6, 0, 'F'), 'R28': (74.2, 28.2, 0, 'F'),
        'Y1': (17.8, 36.5, 90, 'B'),
        'C49': (22.0, 41.0, 90, 'B'), 'C50': (21.5, 33.5, 90, 'B'),
        'C42': (32.8, 44.2, 0, 'B'), 'C43': (29.4, 44.0, 0, 'B'),
        'C47': (24.3, 45.8, 90, 'F'),
    }
    for ref, (x, y, rotation, side) in moves.items():
        components[ref]['placement'].update(x=x, y=y, rotation=rotation, side=side)


def attach(board):
    def pt(x, y):
        return p.VECTOR2I(p.FromMM(x), p.FromMM(y))
    def trace(net, layer, width, *points):
        for a, b in zip(points, points[1:]):
            item = p.PCB_TRACK(board)
            item.SetNet(board.FindNet(net)); item.SetLayer(layer)
            item.SetStart(pt(*a)); item.SetEnd(pt(*b)); item.SetWidth(p.FromMM(width))
            board.Add(item)
    def via(net, x, y):
        item = p.PCB_VIA(board); item.SetNet(board.FindNet(net)); item.SetPosition(pt(x, y))
        item.SetWidth(p.FromMM(.65)); item.SetDrill(p.FromMM(.30))
        item.SetViaType(p.VIATYPE_THROUGH); item.SetLayerPair(p.F_Cu, p.B_Cu)
        board.Add(item)

    trace('USB_DM_MCU', p.F_Cu, .20, (71.4,29.8),(72.2,29.8),(73.0,30.6),(73.2875,30.6))
    trace('USB_DP_MCU', p.F_Cu, .20, (71.4,29.0),(72.2,29.0),(73.0,28.2),(73.2875,28.2))
    trace('USB_DM', p.F_Cu, .20, (75.1125,30.6),(75.3,30.6),(76.3,29.6),(77.5,29.6),
          (80.2,26.9),(80.5,26.9),(81.8,25.5),(82.5,25.5))
    via('USB_DM',82.5,25.5); via('USB_DM',82.5,24.2)
    trace('USB_DM', p.In2_Cu, .20, (82.5,25.5),(82.5,24.2))
    trace('USB_DM', p.F_Cu, .20, (82.5,24.2),(83.15,24.2),(84.95,26),(86.75,26),
          (87,26.25),(87.5,26.25),(90.07,23.68),(90.07,23.2),(89,22.13),(89,21.62))
    trace('USB_DP', p.F_Cu, .20, (75.1125,28.2),(75.3,28.2),(76.3,29.2),
          (77.3343146,29.2),(80.5343146,26),(80.5,25.5))
    via('USB_DP',80.5,25.5); via('USB_DP',82,27.2)
    trace('USB_DP', p.In2_Cu, .20, (80.5,25.5),(82,27.2))
    trace('USB_DP', p.F_Cu, .20, (82,27.2),(83.5,27.2),(83.8,26.9),(86.75,26.9),
          (87,26.65),(87.6656854,26.65),(90.47,23.8456854),(90.47,23.2),(91.54,22.13),(91.54,21.62))
    for x,y in [(80.5,24.5),(82,28.2),(81.5,23.7),(82.5,22.8)]:
        via('GND',x,y)

    trace('GND', p.B_Cu, .20, (82,28.2),(79.7,28.2),(79.7,25),(80.5,24.5),(81.5,23.7),(82.5,22.8))

    # Crystal and load capacitors stay on the ADE7953 face. No signal vias.
    trace('M_XIN', p.B_Cu, .15, (25.3875,46.5),(27.3,46.5),(27.3,44.4),
          (25.3,42.4),(22.625,42.4),(22,41.775),(20.975,40.75),(17.8,40.75))
    trace('M_XOUT', p.B_Cu, .15, (25.3875,47),(27.8,47),(27.8,44.3),
          (25.4,41.9),(23.1,41.9),(23.1,38.875),(21.5,37.275),(21.5,34.275),(19.475,32.25),(17.8,32.25))
    trace('M_GND', p.B_Cu, .20, (22,40.225),(21.7,39.925),(21.7,39.3)); via('M_GND',21.7,39.3)
    trace('M_GND', p.B_Cu, .20, (21.5,32.725),(21.5,31.5),(20.6,31.5)); via('M_GND',20.6,31.5)
    # Direct local returns to EP, avoiding a detour through the board ground bus.
    trace('M_GND', p.B_Cu, .25, (20.6125,46.5),(23,46.5))
    trace('M_GND', p.B_Cu, .25, (25.3875,45.5),(24.25,45.5),(23.25,46.5),(23,46.5))
    trace('M_GND', p.B_Cu, .20, (24.5,44.1125),(24.5,45.0),(23,46.5))
    trace('M_GND', p.B_Cu, .25, (20.6125,46.5),(18.1,46.5)); via('M_GND',18.1,46.5)

    # Local ADE VDD bypass; power and return each use one off-pad via.
    trace('M_3V3', p.B_Cu, .20, (25.3875,46),(26,46),(26.5,45.5)); via('M_3V3',26.5,45.5)
    trace('M_3V3', p.F_Cu, .20, (26.5,45.5),(26.5,46.575),(24.3,46.575))
    trace('M_GND', p.F_Cu, .20, (24.3,45.025),(25.075,45.025),(25.075,44.2)); via('M_GND',25.075,44.2)
    trace('M_GND', p.B_Cu, .20, (25.075,44.2),(24.5,44.1125))
