#!/usr/bin/env python3
"""Parametric OpenCascade mechanical prototype. No PCB/source mutations.
Run: .tools/3d-modern/bin/python mechanical/rev-e/build_enclosure.py
STEP uses millimetres; STL numbers are millimetres. Individual printable parts
are translated to min XYZ=0; assembly placements are retained in the manifest.
"""
from pathlib import Path
import json, math, hashlib, itertools
import numpy as np
import trimesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder,BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut,BRepAlgoAPI_Fuse,BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform,BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.gp import gp_Pnt,gp_Ax2,gp_Dir,gp_Vec,gp_Trsf
from OCP.StlAPI import StlAPI_Writer
from OCP.STEPControl import STEPControl_AsIs,STEPControl_Writer,STEPControl_Reader
from OCP.Interface import Interface_Static
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool,XCAFDoc_ColorType
from OCP.Quantity import Quantity_Color,Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.TDataStd import TDataStd_Name
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'output/enclosure-rev-e'; OUT.mkdir(parents=True,exist_ok=True)
P=json.loads((HERE/'parameters.json').read_text())
model_provenance_path=ROOT/'hardware/3d/rev-e-export-manifest.json'
model_provenance=json.loads(model_provenance_path.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert model_provenance['source_board_sha256']==sha(ROOT/model_provenance['source_board']),'Main PCB changed after model export'
for path,digest in model_provenance['output_sha256'].items():assert sha(ROOT/path)==digest,'Main model artifact changed: '+path
assert model_provenance['coverage_sha256']==sha(ROOT/'hardware/3d/model-coverage-rev-e.json'),'Main model coverage changed'
assert model_provenance['native_independent_checks_sha256']==sha(ROOT/'hardware/main-rev-e/checks/independent-summary.json'),'Native check evidence changed after model export'
B=P['box']; W,D,H=B['width'],B['depth'],B['height']; T=B['wall']; F=B['floor']; L=B['lid']; ZL=H-L
PARTS={}; DISPLAY={}; RECORD={}
COL={'base':(.69,.73,.76),'lid':(.84,.87,.88),'guard':(.91,.64,.24),'carrier':(.27,.42,.53),'retainer':(.22,.30,.36),'button':(.24,.29,.32),'pcb':(.06,.39,.25),'black':(.09,.11,.13),'white':(.90,.91,.88)}
def box(x,y,z,dx,dy,dz):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),dx,dy,dz).Shape()
def cyl(x,y,z,r,h,axis=(0,0,1)):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()
def fuse(*shapes):
 s=shapes[0]
 for q in shapes[1:]:s=BRepAlgoAPI_Fuse(s,q).Shape()
 return s

def cut(s,*tools):
 for q in tools:s=BRepAlgoAPI_Cut(s,q).Shape()
 return s

def move(s,v):
 t=gp_Trsf();t.SetTranslation(gp_Vec(*v));return BRepBuilderAPI_Transform(s,t,True).Shape()
def bounds(s):
 b=Bnd_Box();BRepBndLib.Add_s(s,b);lo,hi=b.CornerMin(),b.CornerMax();return np.array([[lo.X(),lo.Y(),lo.Z()],[hi.X(),hi.Y(),hi.Z()]])
def volume(s):
 g=GProp_GProps();BRepGProp.VolumeProperties_s(s,g);return float(g.Mass())
def polyprism(points,z,h):
 p=BRepBuilderAPI_MakePolygon()
 for x,y in points:p.Add(gp_Pnt(x,y,z))
 p.Close();return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(p.Wire()).Face(),gp_Vec(0,0,h)).Shape()
def hexhole(x,y,z,af,h):
 r=af/math.sqrt(3)
 return polyprism([(x+r*math.cos(math.pi/6+i*math.pi/3),y+r*math.sin(math.pi/6+i*math.pi/3)) for i in range(6)],z,h)
def link(a,b,z,w,h):
 a=np.array(a);b=np.array(b);d=b-a; n=np.array([-d[1],d[0]])/np.linalg.norm(d)*w/2
 return fuse(polyprism([a+n,b+n,b-n,a-n],z,h),cyl(*a,z,w/2,h),cyl(*b,z,w/2,h))
def register(name,s,color,qty=1,notes=''):
 assert BRepCheck_Analyzer(s).IsValid(),name+' invalid BREP'
 PARTS[name]=s; RECORD[name]={'quantity':qty,'color':color,'notes':notes}
 return s

def visual(name,s,color):DISPLAY[name]=(s,color)
# Base shell, four lid-screw towers and four independent wall-mount holes.
base=cut(box(0,0,0,W,D,ZL),box(T,T,F,W-2*T,D-2*T,ZL-F+1))
corner=[(8,8),(W-8,8),(W-8,D-8),(8,D-8)]
for x,y in corner:
 base=fuse(base,cyl(x,y,F,5,ZL-F))
 base=cut(base,cyl(x,y,ZL-14,1.7,15),hexhole(x,y,ZL-7,5.7,2.8))
 # Side-loading captive M3 nut slot, facing the inside of the box.
 sx=x if x<W/2 else x-8
 base=cut(base,box(sx,y-3,ZL-7,8,6,2.8))
for x,y in [(16,16),(W-16,16),(W-16,D-16),(16,D-16)]:
 base=cut(base,cyl(x,y,-1,2.25,F+2),cyl(x,y,F-2.1,4.5,3))
# Main board mounts: four integral insulating standoffs, nylon screws.
M=P['main']; mx,my=M['origin']; board_bottom=F+M['standoff']; board_top=board_bottom+M['size'][2]
main_mounts=[(mx+x,my+M['size'][1]-y) for x,y in M['holes']]
for x,y in main_mounts:
 base=fuse(base,cyl(x,y,F,4,M['standoff']))
 base=cut(base,cyl(x,y,-1,1.7,board_bottom+2),cyl(x,y,-.1,3.2,2.3))
# Guard secured on separate bosses; captive nuts approached from underside.
for x,y in P['guard']['mounts']:
 base=fuse(base,cyl(x,y,F,4.5,4))
 base=cut(base,cyl(x,y,-1,1.7,10),hexhole(x,y,-.1,5.7,2.7))
# Four segregated cable entries; actual glands are purchased components.
for g in P['glands']:
 x,y,z=g['centre']
 if g['wall']=='left':base=cut(base,cyl(-1,y,z,g['hole']/2,T+2,(1,0,0)))
 else:base=cut(base,cyl(x,-1,z,g['hole']/2,T+2,(0,1,0)))
base=cut(base,cyl(W-T-1,120,55,3.25,T+2,(1,0,0)))
# Cable clamp bosses and lower saddles, inside segregated wiring vestibules.
base=fuse(base,box(76,T,F,3,21.8-T,38))
clamps=[('mains',25,55,'x',9),('coil',25,95,'x',9),('live_CT',60,31,'y',7),('probes',105,31,'y',9),('sensors',137,30,'y',7)]
clamp_mounts=[]
for name,x,y,axis,cable_d in clamps:
 if axis=='x': anchors=[(x,y-9),(x,y+9)]; pad=box(x-5,y-cable_d/2,F,10,cable_d,5)
 else: anchors=[(x-9,y),(x+9,y)]; pad=box(x-cable_d/2,y-5,F,cable_d,10,5)
 base=fuse(base,pad)
 for ax,ay in anchors:
  base=fuse(base,cyl(ax,ay,F,4,9.5));base=cut(base,cyl(ax,ay,6,1.7,10),hexhole(ax,ay,8.5,5.7,2.8),box(ax,ay-3,8.5,8,6,2.8))
 clamp_mounts.append((name,x,y,axis,cable_d,anchors))
register('base',base,COL['base'],notes=f'{W:g} x{D:g} x{ZL:g} mm; four main mounts, four case mounts, separate cable entries')
# Lid plate and locating lip, avoiding the four base nut towers.
lid=box(0,0,ZL,W,D,L)
lip=cut(box(T+.4,T+.4,ZL-3,W-2*(T+.4),D-2*(T+.4),3),box(T+2.4,T+2.4,ZL-4,W-2*(T+2.4),D-2*(T+2.4),5))
for x,y in corner:lip=cut(lip,cyl(x,y,ZL-4,5.5,6))
lid=fuse(lid,lip)
for x,y in corner:lid=cut(lid,cyl(x,y,ZL-5,1.7,10),cyl(x,y,H-2.1,3.2,3))
# Panel carrier mounted from lid, separate PCB fasteners at all four corners.
PA=P['panel']; px,py=PA['origin']; panel_front=PA['front_z']; panel_back=panel_front-PA['size'][2]
carrier_z=panel_back-13.4
panel_mounts=sorted([(px+x,py+PA['size'][1]-y) for x,y in PA['holes']],key=lambda q:(q[1],q[0]))
outer=PA['carrier_mounts']
carrier_parts=[]
for a,b in zip(outer,[outer[1],outer[3],outer[0],outer[2]]):carrier_parts.append(link(a,b,carrier_z,3.5,3.2))
for a,b in zip(outer,[panel_mounts[0],panel_mounts[1],panel_mounts[2],panel_mounts[3]]):
 carrier_parts.extend([link(a,b,carrier_z,4,3.2),cyl(*b,carrier_z,3.3,panel_back-carrier_z)])
carrier=fuse(*carrier_parts)
for x,y in panel_mounts:carrier=cut(carrier,cyl(x,y,carrier_z-1,1.4,panel_back-carrier_z+2),hexhole(x,y,carrier_z-.1,4.9,2.1))
for x,y in outer:
 carrier=cut(carrier,cyl(x,y,carrier_z-1,1.7,5))
 lid=fuse(lid,cyl(x,y,carrier_z+3.2,3.7,ZL-(carrier_z+3.2)))
 lid=cut(lid,cyl(x,y,carrier_z+2.2,1.7,10),hexhole(x,y,carrier_z+4.5,5.7,2.8),box(x,y-3,carrier_z+4.5,8,6,2.8))
register('panel_carrier',carrier,COL['carrier'],notes='Four M2.5 PCB mounts; four separate M3 lid attachments')
# Captive plungers: two lengths; a shoulder physically limits downward travel.
for b in PA['buttons']:
 x,y=px+b['xy'][0],py+PA['size'][1]-b['xy'][1]
 radius=3.0;stroke=b['stroke_stop']; gap=PA['actuator_rest_gap'];tip=panel_front+b['free_height']+gap
 lid=cut(lid,cyl(x,y,ZL-1,3.25,L+3))
 # Stem plus a flange captured below lid. Outside cap stop is above lid by stroke.
 stem=fuse(cyl(x,y,tip,1.4,ZL-tip),cyl(x,y,ZL-1.05,3.0,L+1.05+stroke+.9),cyl(x,y,ZL-1.05,4.0,1.05),cyl(x,y,H+stroke,4.0,1.4))
 color=(.77,.13,.12) if b['name']=='STOP' else ((.12,.51,.30) if b['name']=='START' else COL['button'])
 register('plunger_'+b['name'].lower(),stem,color,notes='Adjust stem after measured switch fit; never preload; shoulder stroke '+str(stroke)+'mm')
# OLED frame and retainer; the purchased window is mechanically captured.
O=P['oled']; ox,oy=O['centre']; ow,od,ot=O['module']; ob=O['board_bottom_z']; glass_top=ob+ot+O['glass'][2]
# Seat to PCB front at its extreme edges; roomy glass opening avoids active glass pressure.
seat=cut(box(ox-20.3,oy-8.55,ob+ot,40.6,17.1,ZL-(ob+ot)),box(ox-16,oy-5.9,ob+ot-.1,32,11.8,ZL-(ob+ot)+.2))
# PCB end clearance is relieved; board is inserted before rear clamp.
lid=fuse(lid,seat)
lid=cut(lid,box(ox-O['aperture'][0]/2,oy-O['aperture'][1]/2,ZL-.1,O['aperture'][0],O['aperture'][1],L+.2))
# Window recess on underside, closed externally by retaining ledge.
lid=cut(lid,box(ox-19.15,oy-8.15,ZL-1.05,38.3,16.3,1.06))
ret_z=ob-2
ret=cut(box(ox-23,oy-9.5,ret_z,46,19,2),box(ox-16.5,oy-5.5,ret_z-1,33,11,4))
# PH plug/back electronics relief: no central crossbar under the module.
for x in [ox-22,ox+22]:
 ret=fuse(ret,cyl(x,oy,ret_z,3.0,2))
 lid=fuse(lid,cyl(x,oy,ob,3.3,ZL-ob))
 lid=cut(lid,cyl(x,oy,ob-1,1.4,7.1),hexhole(x,oy,ob+.9,4.9,2.2),box(x,oy-2.6,ob+.9,7,5.2,2.2))
 ret=cut(ret,cyl(x,oy,ret_z-1,1.4,4))
for wx in [ox-19.5,ox+19.5]:
 ret=fuse(ret,box(wx-1.3,oy-3,ret_z,2.6,6,ZL-1-ret_z))
 lid=cut(lid,box(wx-1.5,oy-3.2,ob-.1,3,6.4,ZL-1-ob+.2))
register('display_retainer',ret,COL['retainer'],notes='Two M2.5 screws; verify edge bearing pads and actual module thickness')
# Optional key plate is interchangeable with a solid blank; reserved body is25mm deep.
K=P['key']; kx,ky=K['centre']; ks=K['plate']; ko=K['opening']
lid=cut(lid,box(kx-ko/2,ky-ko/2,ZL-1,ko,ko,L+2))
key_mounts=[(kx+dx,ky+dy) for dx in [-18,18] for dy in [-18,18]]
plate=fuse(box(kx-ks/2,ky-ks/2,H,ks,ks,3.2),box(kx-ko/2+.3,ky-ko/2+.3,H-2,ko-.6,ko-.6,2))
for x,y in key_mounts:
 lid=cut(lid,cyl(x,y,ZL-1,1.7,L+2));plate=cut(plate,cyl(x,y,H-3,1.7,8))
register('key_blank_plate',plate,COL['lid'],notes='Default fitted blank. Four M3 through-fasteners; optional key plate replaces it')
register('key_22p5_adapter_OPTIONAL',cut(plate,cyl(kx,ky,H-3,K['optional_hole_diameter']/2,8)),COL['lid'],notes='Alternative to blank only;22.5mm hole does not establish compatibility with an unspecified key')
lid=cut(lid,box(ox-19.15,oy-8.15,ZL-1.05,38.3,16.3,1.06))
register('lid',lid,COL['lid'],notes='Captured plungers, OLED window and four-column panel mounting')
# Whole-main-board cover; roof with four fixing flanges and segregated cable tunnels.
G=P['guard']; gx,gy,gz=G['origin']; gw,gd,gh=G['size']; gt=G['wall']; roof=G['roof']
guard=cut(box(gx,gy,gz,gw,gd,gh),box(gx+gt,gy+gt,gz-.1,gw-2*gt,gd-2*gt,gh-roof+.1))
for x,y in G['mounts']:
 guard=fuse(guard,cyl(x,y,8,4.5,3))
 guard=cut(guard,cyl(x,y,7,1.7,5),cyl(x,y,3.9,4.7,4.1))
# Side wire windows are engineering openings, not an IP/finger-protection rating.
for y in [55,95]:guard=cut(guard,box(gx-1,y-8,board_bottom+2,gt+2,16,12))
for x,width in [(60,12),(105,18),(140,12)]:guard=cut(guard,box(x-width/2,gy-1,board_bottom+2,width,gt+2,12))
guard=cut(guard,box(gx+gw-gt-1,78,board_bottom+7,gt+2,22,12),cyl(gx+gw-gt-1,112,board_bottom+19,4,gt+2,(1,0,0)))
register('main_board_guard',guard,COL['guard'],notes='Full-board removable guard; screw retained; segregated wire apertures; not a qualified electrical enclosure')
# Retained cable saddles, each screws to integral base supports.
for name,x,y,axis,cd,anchors in clamp_mounts:
 if axis=='x':s=box(x-5,y-13,13.5,10,26,5);tool=cyl(x-6,y,13.5,cd/2,12,(1,0,0))
 else:s=box(x-13,y-5,13.5,26,10,5);tool=cyl(x,y-6,13.5,cd/2,12,(0,1,0))
 s=cut(s,tool)
 for ax,ay in anchors:s=cut(s,cyl(ax,ay,12.5,1.7,7))
 register('cable_clamp_'+name,s,COL['retainer'],notes=f'Nominal {cd}mm cable saddle; liner/actual cable outside diameter must be checked')
# Reference volumes are explicitly not printable components.
mainpcb=box(mx,my,board_bottom,*M['size'])
for x,y in main_mounts:mainpcb=cut(mainpcb,cyl(x,y,board_bottom-1,1.6,4))
main_step=ROOT/'hardware/main-rev-e/exports/pump-controller-main-rev-e.step'
reader=STEPControl_Reader();assert int(reader.ReadFile(str(main_step)))==1;reader.TransferRoots()
main_native=move(reader.OneShape(),[mx,my+M['size'][1],board_bottom]);visual('main_native_REV_E',main_native,COL['pcb'])
main_bounds=bounds(main_native)
main_rear_depth=board_bottom-main_bounds[0,2]
main_top_height=main_bounds[1,2]-board_top
assert main_rear_depth<=M['bottom_envelope']+.001,'Native main underside exceeds the declared envelope'
assert main_top_height<=M['top_envelope']+.001,'Native main height exceeds the declared envelope'
panelpcb=box(px,py,panel_back,*PA['size'])
for x,y in panel_mounts:panelpcb=cut(panelpcb,cyl(x,y,panel_back-1,1.35,4))
panel_step=ROOT/'hardware/panel-rev-e/exports/pump-panel-rev-e.step'
reader=STEPControl_Reader();assert int(reader.ReadFile(str(panel_step)))==1;reader.TransferRoots()
panel_native=move(reader.OneShape(),[px,py+PA['size'][1],panel_back])
visual('panel_native_REV_E',panel_native,COL['pcb'])
connector_manifest=json.loads((ROOT/'hardware/panel-rev-e/connector-mechanical-interface.json').read_text())
j7=next(c for c in connector_manifest['connectors'] if c['reference']=='J7');jx0,jy0,jx1,jy1=j7['body_fab_bounds_mm']
visual('panel_J7_PH4_allowance',box(px+jx0,py+PA['size'][1]-jy1,panel_back-8,jx1-jx0,jy1-jy0,8),(.84,.82,.71))
for b in PA['buttons']:
 if b['name']!='STOP':continue
 x,y=px+b['xy'][0],py+PA['size'][1]-b['xy'][1]
 if b['name']=='STOP':s=box(px+16.85,py+PA['size'][1]-32.9,panel_front,12.8,5.8,6.5)
 else:s=box(x-1.5,y-1.25,panel_front,3,2.5,1.2)
 visual('switch_'+b['name'],s,COL['black'])
 visual('actuator_'+b['name'],cyl(x,y,panel_front+(6.5 if b['name']=='STOP' else 1.2),(.9 if b['name']=='STOP' else .75),b['free_height']-(6.5 if b['name']=='STOP' else 1.2)),COL['white'])
visual('OLED_module_PCB',box(ox-ow/2,oy-od/2,ob,ow,od,ot),COL['pcb'])
visual('OLED_glass_allowance',box(ox-15,oy-5.5,ob+ot,30,11,1.6),COL['black'])
visual('OLED_active',box(ox-11.19,oy-2.79,glass_top,22.38,5.58,.05),(.12,.73,.85))
window=box(ox-19,oy-8,ZL-1,38,16,1)
visual('clear_window_PURCHASED',window,(.42,.73,.80))
# Fastener representation at actual holes: not detailed purchased screw CAD.
for x,y in main_mounts:
 visual(f'main_nylon_screw_{x}_{y}',fuse(cyl(x,y,2.2,1.5,25),cyl(x,y,.2,2.8,2)),COL['white'])
for x,y in panel_mounts:visual(f'panel_M2p5_{x}_{y}',cyl(x,y,carrier_z-2,1.25,panel_front-carrier_z+3.5),(.65,.68,.7))
for x,y in outer:visual(f'carrier_M3_{x}_{y}',fuse(cyl(x,y,carrier_z,1.5,10),cyl(x,y,carrier_z-2,2.8,2)),(.65,.68,.7))
for x,y in G['mounts']:visual(f'guard_nylon_M3_{x}_{y}',cyl(x,y,2,1.5,11),COL['white'])
# Geometry validation and exports.
Interface_Static.SetCVal_s('write.step.unit','MM')
manifest={'revision':P['revision'],'units':'mm','outer_body_mm':[W,D,H], 'external_features':'key plate +3.2mm, buttons above lid, purchased glands outside body','parameters_sha256':hashlib.sha256((HERE/'parameters.json').read_bytes()).hexdigest(),'parts':{},'status':'Mechanical prototype; physical fit and material qualification outstanding'}
meshes={}; assembly=[]
for name,s in PARTS.items():
 b=bounds(s);minimum=b[0]; local=move(s,-minimum)
 step=OUT/(name+'.step');writer=STEPControl_Writer();writer.Transfer(local,STEPControl_AsIs);assert int(writer.Write(str(step)))==1
 stl=OUT/(name+'.stl');BRepMesh_IncrementalMesh(local,.08,False,.25,True).Perform();sw=StlAPI_Writer();sw.ASCIIMode=False;assert sw.Write(local,str(stl))
 mesh=trimesh.load(stl,force='mesh',process=True);mesh.merge_vertices();mesh.remove_unreferenced_vertices()
 assert mesh.is_watertight,name+' not watertight';assert mesh.is_winding_consistent,name+' inconsistent winding';assert mesh.volume>0,name+' zero volume'
 solids=mesh.split(only_watertight=False);assert len(solids)==1,(name,'disconnected solids',len(solids))
 # Normalize to binary STL after validation.
 printmesh=mesh.copy();print_transform=np.eye(4)
 if name in ['lid','main_board_guard','key_blank_plate','key_22p5_adapter_OPTIONAL'] or name.startswith('plunger_'):
  turn=trimesh.transformations.rotation_matrix(math.pi,[1,0,0]);printmesh.apply_transform(turn);shift=trimesh.transformations.translation_matrix(-printmesh.bounds[0]);printmesh.apply_transform(shift);print_transform=shift@turn
 stl.write_bytes(printmesh.export(file_type='stl'));mesh.apply_translation(minimum);meshes[name]=mesh
 rec=dict(RECORD[name]);rec.update({'bounds_mm':b.tolist(),'size_mm':(b[1]-b[0]).tolist(),'step_to_assembly_translation_mm':minimum.tolist(),'stl_to_assembly_transform':(trimesh.transformations.translation_matrix(minimum)@np.linalg.inv(print_transform)).tolist(),'stl_print_orientation':'front/roof/head down' if not np.allclose(print_transform,np.eye(4)) else 'as designed, lowest surface on build plate','brep_valid':True,'watertight':True,'winding_consistent':True,'connected_solids':len(solids),'volume_mm3':volume(s),'triangles':len(mesh.faces),'step':step.name,'stl':stl.name,'step_sha256':sha(step),'sha256':sha(stl)});manifest['parts'][name]=rec
 if not name.endswith('OPTIONAL'):assembly.append((name,s,RECORD[name]['color']))
# CAD assembly includes labeled reference components and exact print solids.
doc=TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'));shapes=XCAFDoc_DocumentTool.ShapeTool_s(doc.Main());colors=XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
for name,s,col in assembly+[(n,s,c) for n,(s,c) in DISPLAY.items()]:
 label=shapes.AddShape(s,False);TDataStd_Name.Set_s(label,TCollection_ExtendedString(name));colors.SetColor(label,Quantity_Color(*col,Quantity_TOC_RGB),XCAFDoc_ColorType.XCAFDoc_ColorGen)
w=STEPCAFControl_Writer();w.SetColorMode(True);w.SetNameMode(True);w.Transfer(doc,STEPControl_AsIs);w.Write(str(OUT/'assembled.step'))
# Interference checks between retained printed parts. Fasteners and the intentionally
# contacting faces do not count as intersections; only positive volume is reported.
collisions=[]
active=[n for n in PARTS if not n.endswith('OPTIONAL')]
for a,b in itertools.combinations(active,2):
 ba,bb=bounds(PARTS[a]),bounds(PARTS[b])
 if np.any(ba[1]<bb[0]) or np.any(bb[1]<ba[0]):continue
 v=volume(BRepAlgoAPI_Common(PARTS[a],PARTS[b]).Shape())
 if v>1e-5:collisions.append({'a':a,'b':b,'volume_mm3':v})
reference_interferences=[]
for ref in ['main_native_REV_E','panel_native_REV_E','panel_J7_PH4_allowance','switch_STOP','actuator_STOP','OLED_module_PCB','OLED_glass_allowance','clear_window_PURCHASED']:
 for name in active:
  if name=='key_22p5_adapter_OPTIONAL':continue
  ba,bb=bounds(PARTS[name]),bounds(DISPLAY[ref][0])
  if np.any(ba[1]<bb[0]) or np.any(bb[1]<ba[0]):continue
  v=volume(BRepAlgoAPI_Common(PARTS[name],DISPLAY[ref][0]).Shape())
  if v>1e-4:reference_interferences.append({'printed':name,'reference':ref,'volume_mm3':v})
reservation_collisions=[]
for c in connector_manifest['connectors']:
 x0,y0,x1,y1=c['body_fab_bounds_mm'];dx,dy=c['mouth_direction_xy'];r=c['reserve_outward_from_mouth_mm']
 if dx>0:x0=c['mouth_plane_mm'];x1=x0+r
 elif dx<0:x1=c['mouth_plane_mm'];x0=x1-r
 elif dy>0:y0=c['mouth_plane_mm'];y1=y0+r
 else:y1=c['mouth_plane_mm'];y0=y1-r
 space=box(px+x0,py+PA['size'][1]-y1,panel_back-10,x1-x0,y1-y0,10)
 for n in active:
  a,b=bounds(space),bounds(PARTS[n])
  if np.any(a[1]<b[0]) or np.any(b[1]<a[0]):continue
  v=volume(BRepAlgoAPI_Common(space,PARTS[n]).Shape())
  if v>1e-4:reservation_collisions.append({'connector':c['reference'],'printed':n,'volume_mm3':v})
checks={'provisional_panel_plug_reservation_interferences':reservation_collisions,'panel_connector_manifest_pcb_sha256':connector_manifest['pcb_sha256'],'reference_component_interferences':reference_interferences,'panel_step_sha256':hashlib.sha256(panel_step.read_bytes()).hexdigest(),'main_step_sha256':hashlib.sha256(main_step.read_bytes()).hexdigest(),'all_print_parts_valid_watertight_single_solid':True,'printed_part_collisions':collisions,'main_hole_centres_global_mm':main_mounts,'panel_hole_centres_global_mm':panel_mounts,'main_standoff_mm':M['standoff'],'main_bottom_component_clearance_mm':M['standoff']-M['bottom_envelope'],'main_top_envelope_to_guard_roof_mm':gz+gh-roof-(board_top+M['top_envelope']),'guard_to_panel_back_mm':panel_back-(gz+gh),'key_reserved_body_to_guard_roof_mm':ZL-K['reserved_body'][2]-(gz+gh),'printed_material_qualified_for_mains':False,'actual_connector_plug_and_wire_bend_fit_verified':False,'button_travel_physically_verified':False,'OLED_received_module_fit_verified':False}
checks.update({'main_pcb_sha256':model_provenance['source_board_sha256'],'main_model_export_provenance_sha256':sha(model_provenance_path),'main_step_status':'Current independently checked native PCB; approximate body and physical fit limitations remain','main_model_bounds_global_mm':main_bounds.tolist(),'main_model_underside_depth_mm':float(main_rear_depth),'main_model_top_height_above_pcb_mm':float(main_top_height),'panel_model_bounds_global_mm':bounds(panel_native).tolist()})
(OUT/'fit-checks.json').write_text(json.dumps(checks,indent=2)+'\n');(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Scene exports in millimetres/Z-up, with scene metadata declaring units.
scene=trimesh.Scene();exploded=trimesh.Scene()
for name in active:
 m=meshes[name].copy();m.visual.vertex_colors=(np.array([*RECORD[name]['color'],1])*255).astype(np.uint8);scene.add_geometry(m,node_name=name)
 off=[0,0,0]
 if name=='main_board_guard':off=[125,0,30]
 elif name=='panel_carrier':off=[0,0,100]
 elif name=='lid' or name.startswith('plunger_'):off=[100,0,145]
 elif name=='display_retainer':off=[-35,0,135]
 elif name=='key_blank_plate':off=[100,0,165]
 m=m.copy();m.apply_translation(off)
 if name=='base':
  section=cut(PARTS['base'],box(-1,-1,28,W+2,25,100),box(-1,-1,28,27,D+2,100))
  BRepMesh_IncrementalMesh(section,.08,False,.25,True).Perform();sw=StlAPI_Writer();sw.ASCIIMode=False;sw.Write(section,str(OUT/'_section.stl'));m=trimesh.load(OUT/'_section.stl',force='mesh');(OUT/'_section.stl').unlink();m.visual.vertex_colors=(np.array([*RECORD[name]['color'],1])*255).astype(np.uint8)
 exploded.add_geometry(m,node_name=name)
for name,(s,col) in DISPLAY.items():
 if name in ['panel_native_REV_E','main_native_REV_E']:continue
 f=OUT/('_reference_'+name+'.stl');BRepMesh_IncrementalMesh(s,.2,False,.3,True).Perform();sw=StlAPI_Writer();sw.ASCIIMode=False;sw.Write(s,str(f));m=trimesh.load(f,force='mesh');f.unlink();m.visual.vertex_colors=(np.array([*col,1])*255).astype(np.uint8)
 scene.add_geometry(m,node_name=name)
 off=[0,0,0]
 if name.startswith(('panel_','switch_','actuator_','carrier_')):off=[0,0,100]
 elif name.startswith('OLED_'):off=[-35,0,155]
 elif name=='clear_window_PURCHASED':off=[-35,0,170]
 elif name.startswith('guard_'):off=[125,0,30]
 elif name.startswith('main_'):off=[0,0,18]
 m=m.copy();m.apply_translation(off);exploded.add_geometry(m,node_name=name)
def merge_native_glb(path,offset):
 native=trimesh.load(path,force='scene')
 total=trimesh.transformations.translation_matrix(offset)@trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0])@np.diag([1000,1000,1000,1])
 vertices=[];faces=[];cols=[];count=0
 for node in native.graph.nodes_geometry:
  tr,g=native.graph[node];m=native.geometry[g];v=trimesh.transform_points(m.vertices,total@tr)
  vertices.append(v);faces.append(m.faces+count);count+=len(v)
  if getattr(m.visual,'kind',None)=='vertex':c=np.asarray(m.visual.vertex_colors,dtype=np.uint8)
  else:
   mat=getattr(m.visual,'material',None);cc=getattr(mat,'baseColorFactor',getattr(mat,'main_color',[150,155,160,255]));cc=np.asarray(cc,dtype=float)
   if cc.max()<=1:cc*=255
   c=np.tile(cc.astype(np.uint8),(len(v),1))
  cols.append(c)
 return trimesh.Trimesh(vertices=np.concatenate(vertices),faces=np.concatenate(faces),vertex_colors=np.concatenate(cols),process=False)
for name,path,offset,explode in [('native_panel',ROOT/'hardware/panel-rev-e/exports/pump-panel-rev-e.glb',[px,py+PA['size'][1],panel_back],[0,0,100]),('native_main',ROOT/'hardware/main-rev-e/exports/pump-controller-main-rev-e.glb',[mx,my+M['size'][1],board_bottom],[0,0,18])]:
 mesh=merge_native_glb(path,offset);scene.add_geometry(mesh,node_name=name);mesh=mesh.copy();mesh.apply_translation(explode);exploded.add_geometry(mesh,node_name=name)
for name,s in [('assembled',scene),('exploded',exploded)]:
 s.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]));s.apply_scale(.001)
 s.metadata={'units':'m','up_axis':'Y','purpose':'Mechanical fit prototype; not rated enclosure'};(OUT/(name+'.glb')).write_bytes(s.export(file_type='glb'))
print(json.dumps({'parts':len(PARTS),'collisions':collisions,'checks':checks},indent=2))
if collisions or reference_interferences or reservation_collisions:raise SystemExit('Resolve geometric interferences before using these exports')
