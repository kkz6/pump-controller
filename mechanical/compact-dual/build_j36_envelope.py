"""Create the compact-main JST ZE five-way header clearance envelope, in mm."""
from pathlib import Path

from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer
from OCP.gp import gp_Pnt

ROOT = Path(__file__).resolve().parents[2]
dest = ROOT / 'hardware/main-compact-dual/libraries/Connector_JST.3dshapes/JST_ZE_SM05B-ZESS-TB_envelope.step'
dest.parent.mkdir(parents=True, exist_ok=True)
# JST ZE, SM05B-ZESS-TB, body width 12.0, height 5.8 mm. STEP +Y
# is KiCad footprint -Y. Include the complete solder pad depth and extra
# body margin at the front, sides and roof. The plug is checked separately.
body = BRepPrimAPI_MakeBox(gp_Pnt(-6.2, -5.675, 0), 12.4, 9.9, 6.).Shape()
writer = STEPControl_Writer()
writer.Transfer(body, STEPControl_AsIs)
assert int(writer.Write(str(dest))) == 1
