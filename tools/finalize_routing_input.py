from pathlib import Path
import json,uuid
import wx
app=wx.App(False)
import pcbnew as p
BASE=Path(__file__).resolve().parents[1];file=BASE/'hardware/pump-controller-rev-b.kicad_pcb';b=p.LoadBoard(str(file));fps={f.GetReference():f for f in b.GetFootprints()};nets={n.GetNetname():n for n in b.GetNetsByNetcode().values()}
data=json.load(open(BASE/'design/circuit.json'))
for sh in data['sheets']:
 for c in sh['components']:
  if not c.get('on_board',True):continue
  f=fps[c['ref']];f.SetValue(c['value']);pm={str(x['num']):x.get('net') for x in c['pins']}
  for d in f.Pads():
   if d.GetNumber() in pm:d.SetNet(nets[pm[d.GetNumber()]]) if pm[d.GetNumber()] else d.SetNetCode(0)
def pos(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pad(ref,num):return next(d for d in fps[ref].Pads() if d.GetNumber()==str(num) and d.IsOnLayer(p.F_Cu))
def point(ref,num):d=pad(ref,num);return p.ToMM(d.GetPosition().x),p.ToMM(d.GetPosition().y)
def trace(net,points,width=.2,layer=p.F_Cu):
 for a,z in zip(points,points[1:]):
  if a==z:continue
  t=p.PCB_TRACK(b);t.SetStart(pos(*a));t.SetEnd(pos(*z));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
def via(net,x,y):
 q=p.PCB_VIA(b);q.SetPosition(pos(x,y));q.SetWidth(p.FromMM(.55));q.SetDrill(p.FromMM(.25));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNet(nets[net]);b.Add(q)
# Short buck input/switch/output routes and ground returns; remaining signals route around these.
trace('+5V',[point('C3',1),(54.2,14.5)],.5)
trace('+5V',[(54.2,14.5),point('U2',2)],.2)
trace('+5V',[(54.2,14.5),point('U2',3)],.2)
trace('BUCK_SW',[point('U2',7),(57.3,14.25)],.2)
trace('BUCK_SW',[(57.3,14.25),point('L1',1)],.5)
trace('+3V3',[point('L1',2),point('C5',1)],.6)
for pin,target in [(1,(55.75,13.95)),(4,(55.75,15.05)),(5,(55.75,15.05))]:trace('GND',[point('U2',pin),target],.2)
for ref,num,x,y in [('C3',2,49.75,16.5),('C5',2,67,16),('C4',2,56.45,12.25)]:
 trace('GND',[point(ref,num),(x,y)],.3);via('GND',x,y)
p.SaveBoard(str(file),b);s=file.read_text()
for net,x1,x2 in [('GND',40.2,89.5),('M_GND',.5,31.8)]:
 z='''(zone (net %d) (net_name "%s") (layer "In1.Cu") (uuid "%s") (hatch edge 0.5) (priority 1) (connect_pads yes (clearance 0.2)) (min_thickness 0.15) (filled_areas_thickness no) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy %s 0.5) (xy %s 0.5) (xy %s 69.5) (xy %s 69.5))))\n'''%(nets[net].GetNetCode(),net,uuid.uuid4(),x1,x2,x2,x1)
 s=s[:s.rfind(')')]+z+')\n'
file.write_text(s);b=p.LoadBoard(str(file));f=p.ZONE_FILLER(b);f.Fill(b.Zones());p.SaveBoard(str(file),b);print('DSN',p.ExportSpecctraDSN(b,str(file.with_suffix('.dsn'))))
