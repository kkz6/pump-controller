"""Create nominal panel F component envelopes and a display overlay (requires cadquery-ocp).

Coordinates are millimetres, with model Y opposite KiCad footprint Y. The display
is a separately supported part. Only its two published XY dimensions qualify fit.
"""
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.gp import gp_Pnt
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs

DEST = Path(__file__).resolve().parents[1] / 'hardware/panel-rev-f/models'
DEST.mkdir(exist_ok=True)
black, cream, silver = (.13,.14,.15), (.82,.82,.76), (.70,.70,.72)

def box(color, x, y, z, dx, dy, dz):
    return color, BRepPrimAPI_MakeBox(gp_Pnt(x,y,z), dx,dy,dz).Shape()

def save(name, parts):
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for color, solid in parts:
        label = shapes.AddShape(solid, False)
        colors.SetColor(label, Quantity_Color(*color, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorGen)
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.Transfer(doc, STEPControl_AsIs)
    if int(writer.Write(str(DEST / (name+'.step')))) != 1:
        raise RuntimeError(f'Failed to export {name}')

# Omron D2F pp. 3–4. Footprint pads line up with COM/NO/NC in the drawing.
stop = [box(black,-1.32,-2.9,0,12.8,5.8,6.5),
        box((.8,.22,.15),3.13-.6,-1.45,6.5,1.2,2.9,.95)]
for x in (0,5.08,10.16):
    stop.append(box(silver,x-.35,-.2,-3.5,.7,.4,3.5))
save('D2F-01F-nominal', stop)

# Body bounds from F.Fab, SMT side-entry assembly drawing in JST ePH.
# Mouth opens toward negative model Y, i.e. positive footprint Y.
ph = [box(cream,-5.95,-4.4,0,11.9,6.0,.65),
      box(cream,-5.95,-4.4,4.1,11.9,7.6,.75),
      box(cream,-5.95,-4.4,.65,.8,7.6,3.45),
      box(cream,5.15,-4.4,.65,.8,7.6,3.45),
      box(cream,-5.15,.4,.65,10.3,1.2,3.45)]
for x in (-3,-1,1,3):
    ph.append(box(silver,x-.22,-3.5,1.35,.44,4.1,.44))
save('S4B-PH-SM4-TB-envelope', ph)

# Published 36 x 12.5 module and 22.38 x 5.58 active area. Window centre
# and nominal Z are illustrative only, pending actual Waveshare 14657.
oled = [box((.10,.20,.45),0,-12.5,0,36,12.5,1.2),
        box(black,3.5,-10.75,1.2,29,9,1),
        box((.22,.38,.46),6.81,-9.04,2.2,22.38,5.58,.1)]
save('Waveshare-14657-display-envelope', oled)
