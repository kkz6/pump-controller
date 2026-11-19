"""Nominal KiCad connector bodies from GCT USB4110 B4 and METZ 311711 sheet 4."""
from pathlib import Path
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDocStd import TDocStd_Document
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool

OUT = Path(__file__).parent / 'CompactGuard.3dshapes'
BLACK = (.10, .11, .13)
METAL = (.72, .74, .75)


def box(x, y, z, dx, dy, dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), dx, dy, dz).Shape()


def cylinder(x, y, z, radius, length, axis=(0, 0, 1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z), gp_Dir(*axis)), radius, length).Shape()


def capsule(width, height, axis_z, start_y, depth):
    radius = height / 2
    offset = (width - height) / 2
    body = box(-offset, start_y, axis_z-radius, 2*offset, depth, height)
    for x in (-offset, offset):
        body = BRepAlgoAPI_Fuse(body, cylinder(x, start_y, axis_z, radius, depth, (0,1,0))).Shape()
    return body


def write(name, parts):
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    shapes = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for shape, color in parts:
        label = shapes.AddShape(shape, False)
        colors.SetColor(label, Quantity_Color(*color, Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorGen)
    writer = STEPCAFControl_Writer()
    writer.Transfer(doc, STEPControl_AsIs)
    file = OUT / (name+'.step')
    writer.Write(str(file))
    file.write_text('\n'.join(line.rstrip() for line in file.read_text().splitlines())+'\n')


def usb():
    # The mating face is on the PCB edge, +3.675 in footprint Y, negative model Y.
    shell = capsule(8.94, 3.16, 1.68, -3.675, 7.35)
    opening = capsule(8.34, 2.56, 1.68, -3.775, 6.35)
    parts = [(BRepAlgoAPI_Cut(shell, opening).Shape(), METAL),
             (box(-3.25, -2.55, 1.45, 6.5, 5.35, .46), BLACK)]
    for x in (-5.65, 4.40):
        for y in (-1.7, 2.23):
            parts.append((box(x, y, 0, 1.25, 1.15, .16), METAL))
    for x in (-2.89, 2.89):
        parts.append((cylinder(x, 2.605, -.63, .25, .68), BLACK))
    write('USB4110-GF-A', parts)


def terminal():
    body = box(-3.75, -4.5, 0, 15, 9, 12.7)
    parts = []
    for x in (0, 7.5):
        body = BRepAlgoAPI_Cut(body, box(x-1.85, -4.55, 2.80, 3.7, 6.0, 4.4)).Shape()
        body = BRepAlgoAPI_Cut(body, cylinder(x, 0, 10.4, 1.75, 2.4)).Shape()
        screw = cylinder(x, 0, 10.4, 1.48, 1.4)
        screw = BRepAlgoAPI_Cut(screw, box(x-1.5, -.19, 11.4, 3, .38, .5)).Shape()
        parts.extend([(screw, METAL), (cylinder(x, 0, -3.4, .5, 3.4), METAL)])
    write('RT13702HBWC', [(body, BLACK)] + parts)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    usb()
    terminal()
