"""Build simplified missing package bodies; requires cadquery-ocp.

These are visualization envelopes, not manufacturer mechanical CAD. Local X
follows the footprint; local model Y is the negative of footprint Y.
"""
from pathlib import Path
import json
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'hardware/3d/models'
DEST.mkdir(parents=True,exist_ok=True)
BLACK=(.10,.12,.14);SILVER=(.72,.75,.78);GREEN=(.05,.30,.18)
BLUE=(.10,.30,.62);CREAM=(.74,.69,.56);WHITE=(.88,.89,.87)

def box(x,y,z,dx,dy,dz):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()
def cylinder(x,y,z,r,h,axis=(0,0,1)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()

def write_model(name,parts):
    doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    shapes=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for shape,color in parts:
        label=shapes.AddShape(shape,False)
        colors.SetColor(label,Quantity_Color(*color,Quantity_TOC_RGB),XCAFDoc_ColorType.XCAFDoc_ColorGen)
    writer=STEPCAFControl_Writer();writer.SetColorMode(True)
    writer.Transfer(doc,STEPControl_AsIs)
    path=DEST/(name+'.step')
    writer.Write(str(path))
    path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')

models={}
def record(name,refs,body,description,parts):
    write_model(name,parts)
    models[name]={'references':refs,'body_dimensions_mm':body,'status':'Approximate visualization envelope; not a manufacturer model','basis':description}

record('RACM06E',['U1'],[25.4,25.4,16.7],
       'Manufacturer nominal body dimensions; footprint origin/pin layout from current RACM06E footprint.',
       [(box(-2.54,-22.86,0,25.4,25.4,16.7),BLACK)] +
       [(cylinder(x,y,-3.2,.4,3.2),SILVER) for x,y in [(0,-5.08),(0,0),(20.32,-10.16),(20.32,0)]])
record('ESP32_C6_MINI_1U',['U3'],[13.2,12.5,2.4],
       'Manufacturer module outline; shield and antenna socket are simplified. Not an RF/mechanical clearance model.',
       [(box(-6.6,-5.6,0,13.2,12.5,.65),GREEN),
        (box(-6.15,-5.1,.65,11.4,10.1,1.75),SILVER),
        (cylinder(4.8,5.5,.65,.8,1.1),SILVER)])
record('G5Q_1A',['K1','K2'],[20.3,10.3,15.8],
       'Omron G5Q nominal maximum body; aligned with the current footprint body. Pins simplified.',
       [(box(-1.26,-1.34,0,20.3,10.3,15.8),BLACK)] +
       [(box(x-.3,y-.3,-3.5,.6,.6,3.5),SILVER) for x,y in [(0,0),(0,7.62),(10.16,0),(17.78,0)]])
record('Fuse_5x20',['F1'],[21,5.5,5.5],
       'Current footprint body envelope. 4mm center height is an illustrative lead-forming assumption.',
       [(cylinder(3.47,0,4,2.75,21,(1,0,0)),WHITE),
        (cylinder(3.47,0,4,2.8,3,(1,0,0)),SILVER),
        (cylinder(21.47,0,4,2.8,3,(1,0,0)),SILVER)] +
       [(cylinder(x,0,-3.2,.4,7.2),SILVER) for x in [0,27.94]] +
       [(cylinder(x,0,4,.4,3.47,(1,0,0)),SILVER) for x in [0,24.47]])
record('Fusible_resistor',['R1'],[13.5,6.5,6.5],
       'Current footprint body envelope. 4.5mm center height is an illustrative lead-forming assumption.',
       [(cylinder(3.41,0,4.5,3.25,13.5,(1,0,0)),CREAM)] +
       [(cylinder(x,0,-3.2,.4,7.7),SILVER) for x in [0,20.32]] +
       [(cylinder(x,0,4.5,.4,3.41,(1,0,0)),SILVER) for x in [0,16.91]])
record('TMOV14',['RV1'],[17,11,20],
       'Current 17x11mm footprint envelope. 20mm installed height is a visualization allowance pending purchased-part measurement.',
       [(cylinder(3.75,-5.5,11.5,8.5,11,(0,1,0)),BLUE)] +
       [(cylinder(x,0,-3.2,.4,7),SILVER) for x in [0,7.5]])
record('ADuM6421_RN28',['U11'],[7.5,10.2,2.65],
       'Current footprint body outline; nominal SOIC body height and simplified leads; verify against the RN-28-1 drawing.',
       [(box(-3.75,-5.1,.2,7.5,10.2,2.45),BLACK)] +
       [(box(x,y-.15,0,1.2,.3,.3),SILVER) for x in [-4.95,3.75] for y in [-4.225+i*.65 for i in range(14)]])
record('WSON_2x2',['U2'],[2,2,.8],
       'Generic WSON 2x2 body with approximate 0.8mm height; not a thermal or solder-joint model.',
       [(box(-1,-1,0,2,2,.8),BLACK)])
record('LFCSP_5x5',['U10'],[5,5,.85],
       'Generic 5x5 LFCSP body with approximate 0.85mm height; not a thermal or solder-joint model.',
       [(box(-2.5,-2.5,0,5,5,.85),BLACK)])

(ROOT/'hardware/3d/approximate-bodies.json').write_text(json.dumps(models,indent=2)+'\n')
print('Created',len(models),'body definitions for',sum(len(x['references']) for x in models.values()),'components')
