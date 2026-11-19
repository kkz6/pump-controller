"""Conservative C1 installed envelope, not a manufacturer's visual model."""
from pathlib import Path
import hashlib,json
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.gp import gp_Pnt,gp_Ax2,gp_Dir
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'hardware/3d/models/C1_EEUFR1E470_max_envelope.step'
# Local footprint origin is positive lead1; negative lead2 is at(2,0).
# 5.5mm maximum can plus0.25mm lateral installation allowance on each side.
# Maximum body12.5mm plus1mm mounting gap. Trimmed leads extend no more than
# 3mm beyond the opposite PCB face; board thickness is1.6mm.
s=BRepPrimAPI_MakeBox(gp_Pnt(-2,-3,1),6,6,12.5).Shape()
for x in [0,2]:
 lead=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,0,-4.6),gp_Dir(0,0,1)),.275,6.1).Shape()
 s=BRepAlgoAPI_Fuse(s,lead).Shape()
assert BRepCheck_Analyzer(s).IsValid()
w=STEPControl_Writer();w.Transfer(s,STEPControl_AsIs);assert int(w.Write(str(out)))==1
record={'mpn':'Panasonic EEUFR1E470','scope':'Conservative installed bounding solid; not a realistic manufacturer model',
 'maximum_can_diameter_mm':5.5,'maximum_can_length_mm':12.5,'mounting_gap_max_mm':1,
 'xy_installation_allowance_each_side_mm':.25,'body_envelope_xy_mm':[6,6],
 'body_depth_from_mounting_face_mm':13.5,'board_thickness_mm':1.6,
 'trimmed_lead_extension_opposite_board_face_max_mm':3,'lead_diameter_max_mm':.55,
 'footprint_local_body_bounds_mm':[[-2,-3,1],[4,3,13.5]],
 'step_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'manufacturer_source':'https://industry.panasonic.eu/storage/imported/industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ast-ind-152839.pdf',
 'manufacturer_drawing':'FR-A dimensions, catalogue2025.9 p15; part rowp19'}
(ROOT/'hardware/3d/C1-envelope-provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print(out)
