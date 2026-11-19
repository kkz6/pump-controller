import importlib.util,json
from pathlib import Path
import wx
app=wx.App(False)
b=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('cad',b/'tools/generate_cad.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
d=json.load(open(b/'design/circuit.json'));layout=json.load(open(b/'design/pcb-placement.json'));d['board'].update(width=90,height=70,layers=4)
for sh in d['sheets']:
 for c in sh['components']:
  if c.get('on_board',True):c['placement']=layout['components'][c['ref']]
m.make_board(d,b/'hardware',d['project'])
import pcbnew as p
file=b/'hardware'/(d['project']+'.kicad_pcb');board=p.LoadBoard(str(file))
for f in board.GetFootprints():f.Value().SetVisible(False);f.Reference().SetVisible(False)
p.SaveBoard(str(file),board);s=file.read_text();zone='''(zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (uuid "80aec00f-5084-46dd-bb9e-73d0875f4826") (hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) (fill (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy 32 0) (xy 40 0) (xy 40 70) (xy 32 70))))\n''';file.write_text(s[:s.rfind(')')]+zone+')\n')
print('Rebuilt from final JSON using verified placements')
