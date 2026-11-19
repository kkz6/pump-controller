"""Rev E regulator backbone, plane feed and module-local bypass geometry (mm)."""
import pcbnew as p

CAPACITOR_SELECTION = {
    'C1': {
        'value': '47uF 25V 105C',
        'mpn': 'EEUFR1E470',
        'datasheet': 'https://industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ABA0000C1259.pdf',
        'description': 'Panasonic FR, 47 uF, 25 V, 105 C low-impedance radial. '
                       '2.0 mm lead pitch. Allow 5.5 mm diameter and 12.5 mm can length '
                       'plus installed stand-off. Fit below the PCB and check against the guard and case.',
    },
}
for ref, purpose in {
    'C3': 'Buck VIN bypass. Verify at least 10 uF effective at operating bias and temperature.',
    'C5': 'Buck output bypass at the VOS sense point. Verify filter stability and rail load steps.',
}.items():
    CAPACITOR_SELECTION[ref] = {
        'value': '22uF 16V X7R', 'mpn': 'C3225X7R1C226M250AC',
        'datasheet': 'https://product.tdk.com/info/en/documents/chara_sheet/c3225x7r1c226m250ac.pdf',
        'description': 'TDK 1210, 22 uF, 16 V X7R, 20%. ' + purpose,
    }


def select_capacitors(components):
    for ref, selection in CAPACITOR_SELECTION.items():
        components[ref].update(selection)


def set_placements(components):
    for ref,x,y in [('C21',65.05,37.1),('C20',65.575,40.05)]:
        components[ref]['placement'].update(x=x,y=y,rotation=0,side='F')

def attach(board):
    def pt(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
    for zone in board.Zones():
        if not zone.GetIsRuleArea() and zone.GetLayer()==p.In2_Cu and zone.GetNetname()=='GND':
            zone.SetNet(board.FindNet('+3V3'))
    def trace(net,layer,width,*points):
        for a,b in zip(points,points[1:]):
            t=p.PCB_TRACK(board);t.SetNet(board.FindNet(net));t.SetLayer(layer)
            t.SetStart(pt(*a));t.SetEnd(pt(*b));t.SetWidth(p.FromMM(width));board.Add(t)
    def via(net,x,y):
        v=p.PCB_VIA(board);v.SetNet(board.FindNet(net));v.SetPosition(pt(x,y))
        v.SetWidth(p.FromMM(.65));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH)
        v.SetLayerPair(p.F_Cu,p.B_Cu);board.Add(v)
    trace('+5V',p.F_Cu,.8,(50.32,10),(54.55,14.23),(54.55,16))
    trace('+5V',p.F_Cu,.8,(54.55,14.23),(57.40,14.23),(59.55,16.38),(59.55,16.50),(57.975,18.075),(57.975,19.5))
    trace('+5V',p.In2_Cu,.8,(50.32,10),(52.5,12.18),(52.5,20),(57.5,25))
    for x in [67.9,68.95]:
        trace('+3V3',p.F_Cu,.45,(68.525,19.5),(x,18.5),(x,17.6))
        via('+3V3',x,17.6)
    trace('+3V3',p.F_Cu,.38,(64.1,34.9),(64.1,37.1))
    trace('+3V3',p.F_Cu,.65,(64.1,37.1),(64.1,40.05))
    for x,y in [(65.15,38.25),(65.5,39.25)]:
        trace('+3V3',p.F_Cu,.45,(64.1,37.1),(x,y));via('+3V3',x,y)
    trace('GND',p.F_Cu,.45,(66,37.1),(66.95,37.1));via('GND',66.95,37.1)
    trace('GND',p.F_Cu,.65,(67.05,40.05),(68.30,40.05));via('GND',68.30,40.05)
    trace('GND',p.F_Cu,.32,(63.3,34.9),(62.5,34.9),(61.9,35.5));via('GND',61.9,35.5)
