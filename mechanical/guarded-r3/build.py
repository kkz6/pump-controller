"""Export nominal service-port cartridge STEP models and 1:1 2D flat patterns.

Use Python with OCP. Case-space coordinates are millimetres. Supplier parts in
the assembly are simplified envelopes. Fit and contact timing need measurement.
"""
from pathlib import Path
from OCP.gp import gp_Pnt,gp_Ax2,gp_Dir
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ColorType
from OCP.TDataStd import TDataStd_Name
from OCP.Quantity import Quantity_Color,Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from check_kinematics import NOMINAL

O=Path(__file__).resolve().parent
grey=(.62,.65,.68); steel=(.42,.49,.53); amber=(.95,.58,.13)
dark=(.12,.14,.15); red=(.64,.13,.11); green=(.16,.49,.32); blue=(.13,.30,.60)

def box(x,y,z,dx,dy,dz):
    return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()
def hole(shape,x,y,z,diameter,length):
    tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,1,0)),diameter/2,length).Shape()
    return BRepAlgoAPI_Cut(shape,tool).Shape()
def cut(a,b):
    return BRepAlgoAPI_Cut(a,b).Shape()
def save(filename,parts):
    doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    labels=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colours=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    for name,shape,rgb in parts:
        label=labels.AddShape(shape,False)
        TDataStd_Name.Set_s(label,TCollection_ExtendedString(name))
        colours.SetColor(label,Quantity_Color(*rgb,Quantity_TOC_RGB),XCAFDoc_ColorType.XCAFDoc_ColorGen)
    writer=STEPCAFControl_Writer();writer.SetColorMode(True);writer.SetNameMode(True)
    writer.Transfer(doc,STEPControl_AsIs)
    assert int(writer.Write(str(O/filename)))==1

def fixed():
    # Wall Y=0. The plug entry is open from the outside to the edge of J40.
    tube=cut(box(82,-2,20.78,20,25.5,13),box(84,-3,22.78,16,28,9))
    # Back guide lands capture the blade above and below. Their rear face stays before J40.
    rails=[]
    for z in [15.5,37.14]:
        rails.append(('Guide rail',box(62,21.0,z,97,3.8,1.36),steel))
    for z in [15.5,35.15]:
        rails.append(('Rear capture strip',box(62,24.5,z,97,.30,3.35),steel))
    front=cut(box(62,21.35,15.5,97,2.15,23),box(84,21.2,22.78,16,3,9))
    # The drive ear passes through the front guide plate as the carriage moves.
    front=cut(front,box(108.6,21.,32.25,44.8,3,4.50))
    exterior=box(5,-4,47,105,4,36)
    for z in [54,76]:
        exterior=hole(exterior,67.5,-5,z,3.3,6) # tap M4 x 0.7
        exterior=hole(exterior,18.,-5,z,3.9,6) # add location studs
    parts=[('Plug-entry tube ID16x9',tube,steel),('Captive front guide',front,steel),
           ('Omron backing plate tap M4',exterior,grey)]+rails
    # Dedicated end stops hit the drive ear, independently of the Omron key and the plug.
    for x in [106.,152.]:
        parts.append(('Fixed slider end stop',box(x,5.,32.4,3,7.,4.25),grey))
    # Guides and tube are secured to a common carrier bolted to the enclosure.
    # Dry-fit the carrier, then shim/dowel to the actual PCB-mounted mouth.
    frame=cut(box(60,-2,13,100,2,29),box(82,-3,20.78,20,4,13))
    frame=cut(frame,box(108.5,-3,32.1,44,4,4.8))
    for x in (64.,156.):
        for z in (16.,39.):frame=hole(frame,x,-3,z,4.5,4)
    parts.append(('Lower cartridge fixing flange',frame,grey))
    for x in (64.,156.):
        parts.append(('Guide support',box(x-1.5,0,13.1,3,23.5,2.4),steel))
    # Tool-removable steel housing houses SG1, its captive tongue and the AL1 striker.
    # The exterior lower face is kept above the open USB tunnel.
    cover=cut(box(-2,-54,46,172,54,44),box(-.5,-52.5,47.5,169,54,41))
    # Lower and upper chambers communicate only inside the closed housing.
    cover=cut(cover,box(106,-17,45.7,49,15,3))
    cover=hole(cover,52,-55,65,10.8,4) # sealed by installed AL1
    parts.append(('SG1 and AL1 steel enclosure',cover,grey))
    keeper=hole(box(42,-43,51.5,20,3,27),52,-44,65,10.6,5)
    parts.append(('AL1 fixed rear keeper',keeper,steel))
    # Fixed keeper ties to the outer wall above/below its sliding 5 mm strike.
    for z in [50,78]:
        parts.append(('AL1 keeper support',box(42,-52.5,z,20,12.5,2),steel))
    lower=cut(box(8,-22,35.1,151,22,12.6),box(9.5,-20.5,36.6,148,22,12))
    lower=cut(lower,box(62,-23,39.2,44,4,4.8))
    lower=cut(lower,box(106,-17,34.5,49,20,3))
    # Below the handle housing, enclose the crosshead where it passes through the wall.
    lower_ear=cut(box(105,-18,30.5,50.5,18,6),box(106.5,-16.5,32,47.5,18,5))
    parts.extend([('Handle shroud with restricted slot',lower,grey),('Lower drive enclosure',lower_ear,grey)])
    return parts

def carriage(s):
    blade_x=NOMINAL['closed_left_x']+s
    parts=[('Gate blade 301 half-hard 0.60',box(blade_x,23.75,17,46,.60,20),amber),
           ('Welded transverse drive',box(109+s,-8,32.5,3,31.75,4),amber),
           ('Welded riser',box(109+s,-11,32.5,3,3,53),amber)]
    back=box(109+s,-11,52.5,18,3,25)
    for z in (57.5,72.5):back=hole(back,120.75+s,-12,z,3.3,5)
    parts.append(('K1 fixed two-M4 mounting tab',back,amber))
    strike=hole(box(0+s,-49,54,114,5,22),52+s,-50,65,10.6,7)
    parts.extend([('AL1 single-window moving striker',strike,amber),
                  ('AL1 upper return',box(109+s,-49,75,3,5,10.5),amber),
                  ('Rigid link above SG1',box(109+s,-49,82.5,3,41,3),amber),
                  ('Handle crossbar',box(64+s,-17,39.8,48,9,3.4),amber),
                  ('Handle-overlap slide mask',box(18+s,-20.25,36.9,93,.7,9.0),amber),
                  ('Handle shaft',box(63+s,-26,39.8,2,10,3.4),amber),
                  ('Finger grip',box(57+s,-32,37.8,14,6,7.4),dark)])
    return parts

def envelope(s):
    # Body is rotated horizontally with the top entry pointing +X.
    switch=cut(box(10,-35.5,49.5,96,31.5,31),box(78,-13.5,57.8,30,3,14.4))
    head=cut(box(76,-34.6,49.9,30,30.6,30.2),box(78,-13.5,57.8,30,3,14.4))
    main=cut(switch,box(75.99,-36,49,30.02,33,33))
    key=box(79.75+s,-13,58.5,28,2,13)
    key=cut(key,box(79.6+s,-14,61.5,18,4,7))
    base=box(107.75+s,-13,50,17.5,2,30)
    for z in (57.5,72.5):base=hole(base,120.75+s,-14,z,4.3,5)
    mouth=cut(box(87.53,25,25.60,8.94,7.35,3.26),box(87.83,24.8,26,8.34,7.0,2.56))
    # AL1 bolt engagement interface only; its proprietary housing is supplier-selected.
    start,end=(-54.,-40.35) if not s else (-54.,-51.)
    bolt=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(52,start,65),gp_Dir(0,1,0)),5,end-start).Shape()
    return [('AL1 commercial bolt interface only',bolt,blue),('D4NS-4BF BODY ENVELOPE',main,dark),('D4NS head envelope',head,red),
            ('D4DS-K1 nominal captive key',key,grey),('D4DS-K1 base',base,grey),
            ('J40 GCT envelope',mouth,grey),('Local board edge section',box(77,25,24,30,14,1.6),green)]

def dxf():
    # Closed CUT profiles are 1:1, separated into independent files. Frame and mount plates
    # also have drill/clearance/tap layers. All DXF coordinates are case X/Z.
    def polygon(x,z,w,h):return [(x,z),(x+w,z),(x+w,z+h),(x,z+h)]
    def write(name,profiles,circles):
        s='0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n'
        for layer,points in profiles:
            for a,b in zip(points,points[1:]+points[:1]):
                s+=f'0\nLINE\n8\n{layer}\n10\n{a[0]}\n20\n{a[1]}\n11\n{b[0]}\n21\n{b[1]}\n'
        for layer,x,z,r in circles:
            s+=f'0\nCIRCLE\n8\n{layer}\n10\n{x}\n20\n{z}\n40\n{r}\n'
        (O/name).write_text(s+'0\nENDSEC\n0\nEOF\n')
    write('access-lock-striker-5mm.dxf',[('CUT',polygon(0,54,114,22))],[('BORE_VERIFIED_BOLT',52,65,5.3)])
    write('blade-0p60mm.dxf',[('CUT',polygon(66,17,46,20))],[])
    write('cartridge-flange-2mm.dxf',[('CUT',polygon(60,13,100,29)),('CUT',polygon(82,20.78,20,13)),('CUT',polygon(108.5,32.1,44,4.8))],[('CLEARANCE',x,z,2.25) for x in (64.,156.) for z in (16.,39.)])
    write('sg1-backing-4mm.dxf',[('CUT',polygon(5,47,105,36))],
          [('TAP_M4',67.5,z,1.65) for z in (54,76)]+[('LOCATOR',18,z,1.95) for z in (54,76)])
    write('captive-key-plate-3mm.dxf',[('CUT',polygon(109,52.5,18,25))],[('TAP_M4',120.75,z,1.65) for z in (57.5,72.5)])

if __name__=='__main__':
    dxf()
    fixed_parts=fixed()
    save('custom-fixed-parts.step',fixed_parts)
    save('custom-moving-carriage.step',carriage(0))
    for s,label in [(0,'closed'),(40,'open')]:
        save('usb-service-'+label+'.step',fixed_parts+carriage(s)+envelope(s))
