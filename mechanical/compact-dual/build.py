"""Build the compact dual-output replacement case body and removable PCB guard.

Use .tools/3d-modern/bin/python; the geometry is in millimetres. This fits the
existing Rev E lid interface. The KiCad board is read-only.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
# KiCad XY (x right, y down) to case XY (viewed from the open lid).
CASE_X_ZERO, CASE_Y_ZERO = 112.0, 125.0
W, D, WALL, FLOOR, BASE_TOP = 170.0, 150.0, 3.2, 4.0, 86.8
BOARD_Z = 24.0
GUARD = (16., 10., 4., 137., 125., 50.)
GUARD_FEET = [(26., 13.), (144., 13.), (26., 132.), (144., 132.)]
LID_TOWERS = [(8,8), (162,8), (162,142), (8,142)]
# Entries each carry one continuous cable jacket. The clamp nut stays inside.
PORTS = [
    ('STARTER CONTROL', 'right', 91., 29.5, 20.1),
    ('AC SUPPLY', 'far', 103., 31., 20.1),
    ('LIVE CT', 'left', 105., 32., 16.1),
    ('TANK', 'left', 54., 32., 20.1),
    ('INLET', 'left', 26., 32., 16.1),
    ('FLOAT', 'near', 24., 30., 12.1),
    ('TRANSFER SENSE', 'near', 52., 30., 12.1),
    ('MODE KEY', 'near', 93., 68., 12.1),
    ('ANTENNA', 'near', 135., 57., 6.5),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case_xy(native):
    x, y = native
    return [CASE_X_ZERO-y, CASE_Y_ZERO-x]


def read_board(path):
    import pcbnew as k
    board = k.LoadBoard(str(path))
    def xy(v):
        return [round(k.ToMM(v.x), 5), round(k.ToMM(v.y), 5)]
    corners = {tuple(xy(p)) for g in board.GetDrawings() if g.GetLayer() == k.Edge_Cuts
               and isinstance(g, k.PCB_SHAPE) and g.GetShape() == k.SHAPE_T_SEGMENT
               for p in (g.GetStart(), g.GetEnd())}
    assert corners == {(0., -17.), (100., -17.), (100., 80.), (0., 80.)}, corners
    holes, ports = {}, {}
    for f in board.GetFootprints():
        ref = f.GetReference()
        if ref.startswith('H') and ref[1:].isdigit():
            p, = f.Pads()
            assert p.GetAttribute() == k.PAD_ATTRIB_NPTH and xy(p.GetDrillSize()) == [3.2, 3.2]
            holes[ref] = xy(p.GetPosition())
        if ref in ('J1', 'J10', 'J20', 'J21', 'J30', 'J31', 'J32', 'J35', 'J36'):
            pads = {p.GetNumber(): xy(p.GetPosition()) for p in f.Pads()
                    if p.GetNumber() in ('1','2')}
            ports[ref] = dict(position=xy(f.GetPosition()), side='B' if f.IsFlipped() else 'F',
                              rotation=round(f.GetOrientationDegrees(), 4), pads=pads)
    assert set(holes) == {'H1','H2','H3','H4','H5'}, holes
    assert holes['H5'] == [50., -12.8], holes
    assert set(ports) == {'J1','J10','J20','J21','J30','J31','J32','J35','J36'}, ports
    for ref, expected_x in [('J30',30.), ('J35',43.)]:
        port = ports[ref]
        assert port['position'] == [expected_x, -8.4], port
        assert port['side'] == 'F' and abs(port['rotation']) == 180, port
        assert abs(port['pads']['2'][0] - port['pads']['1'][0] + 5.08) < .001, port
    return dict(pcb_hash=digest(path), outline=sorted(corners), holes=holes, ports=ports)


def build(geometry, out):
    import numpy as np
    import trimesh
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.GProp import GProp_GProps
    from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Vec
    from OCP.Interface import Interface_Static
    from OCP.StlAPI import StlAPI_Writer
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer

    def box(x,y,z,w,d,h):
        return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,d,h).Shape()
    def cyl(x,y,z,r,h,axis=(0,0,1)):
        return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()
    def cut(s,*tools):
        for t in tools: s=BRepAlgoAPI_Cut(s,t).Shape()
        return s
    def fuse(s,*parts):
        for t in parts: s=BRepAlgoAPI_Fuse(s,t).Shape()
        return s
    def volume(s):
        props=GProp_GProps(); BRepGProp.VolumeProperties_s(s,props); return props.Mass()
    def overlap(a,b):
        return volume(BRepAlgoAPI_Common(a,b).Shape())
    def hextrap(x,y,z,af,height):
        r=af/math.sqrt(3)
        wire=BRepBuilderAPI_MakePolygon()
        for n in range(6):
            angle=math.pi/6+n*math.pi/3
            wire.Add(gp_Pnt(x+r*math.cos(angle),y+r*math.sin(angle),z))
        wire.Close()
        return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(),gp_Vec(0,0,height)).Shape()

    def wall_hole(side,pos,z,r,start,length):
        if side=='right': return cyl(W-start,pos,z,r,length,(-1,0,0))
        if side=='left': return cyl(start,pos,z,r,length,(1,0,0))
        if side=='far': return cyl(pos,D-start,z,r,length,(0,-1,0))
        return cyl(pos,start,z,r,length,(0,1,0))

    out.mkdir(parents=True,exist_ok=True)
    base=cut(box(0,0,0,W,D,BASE_TOP), box(WALL,WALL,FLOOR,W-2*WALL,D-2*WALL,BASE_TOP))
    for x,y in LID_TOWERS:
        base=fuse(base,cyl(x,y,FLOOR,5,BASE_TOP-FLOOR))
        base=cut(base,cyl(x,y,BASE_TOP-14,1.7,15),hextrap(x,y,BASE_TOP-7,5.7,2.8),
                 box(x if x<W/2 else x-8,y-3,BASE_TOP-7,8,6,2.8))
    for x,y in ((16,16),(154,16),(16,134),(154,134)):
        base=cut(base,cyl(x,y,-1,2.25,FLOOR+2),cyl(x,y,FLOOR-2.1,4.5,3))
    for name,point in sorted(geometry['holes'].items()):
        x,y=case_xy(point)
        base=fuse(base,cyl(x,y,FLOOR,4,BOARD_Z-FLOOR))
        base=cut(base,cyl(x,y,-1,1.7,BOARD_Z+2),cyl(x,y,-.1,3.2,3.1))
    for x,y in GUARD_FEET:
        base=fuse(base,cyl(x,y,FLOOR,4.5,4))
        base=cut(base,cyl(x,y,-1,1.7,10),hextrap(x,y,-.1,5.7,2.7))

    for _,side,pos,z,bore in PORTS:
        base=cut(base,wall_hole(side,pos,z,bore/2,-1,WALL+2))
    # Isolate the captive current-transformer route from the isolated probe routes.
    base=fuse(base,box(WALL,84,FLOOR,29-WALL,2.5,30))

    gx,gy,gz,gw,gd,gh=GUARD
    guard=cut(box(*GUARD),box(gx+3,gy+3,gz-.1,gw-6,gd-6,gh-3+.1))
    for x,y in GUARD_FEET:
        guard=fuse(guard,cyl(x,y,8,4.5,3))
        guard=cut(guard,cyl(x,y,7,1.7,5),cyl(x,y,3.9,4.7,4.1))

    # Slots open to the lower edge so the screw-fastened guard lifts clear of connected leads.
    # The closed outer case and cable glands enclose these internal passages.
    ports=geometry['ports']
    def pad_mid(ref):
        a,b = ports[ref]['pads']['1'],ports[ref]['pads']['2']
        return case_xy([(a[0]+b[0])/2,(a[1]+b[1])/2])
    plug_centres={}
    for ref in ('J30','J35'):
        x,y=pad_mid(ref)
        # Header mating end is 8 mm from its terminal pin centres per F.Fab outline.
        plug_centres[ref]={'face_x':x+8.,'centre_y':y}
        guard=cut(guard,box(gx+gw-3.5,y-4.5,gz-.1,4,9,36-gz+.1))
    supply_x,_=pad_mid('J1')
    guard=cut(guard,box(supply_x-7,gy+gd-3.5,gz-.1,14,4,38-gz+.1))
    for ref,width in [('J10',12),('J31',9),('J20',20),('J21',10)]:
        # Centre the longer J20 window between first and last contacts.
        x,y=pad_mid(ref)
        if ref=='J20':
            y -= 1.5*(ports[ref]['pads']['2'][0]-ports[ref]['pads']['1'][0])
        guard=cut(guard,box(gx-.5,y-width/2,gz-.1,4,width,38-gz+.1))
    for ref,width in [('J32',19),('J36',11)]:
        x,_=case_xy(ports[ref]['position'])
        guard=cut(guard,box(x-width/2,gy-.5,gz-.1,width,4,40-gz+.1))
    # Tongue relief lets the guard straddle the fixed CT/probe divider.
    guard=cut(guard,box(gx-.5,83.6,gz-.1,4,3.3,FLOOR+30.4-gz+.1))
    # Under the guard roof, the coax crosses on the isolated side.
    guard=cut(guard,box(127,gy-.5,gz-.1,8,4,47-gz+.1))
    board=box(32,25,BOARD_Z,97,100,1.6)
    for point in geometry['holes'].values():
        x,y=case_xy(point);board=cut(board,cyl(x,y,BOARD_Z-1,1.6,5))
    check={}
    for name,side,pos,z,bore in PORTS:
        assert overlap(base,wall_hole(side,pos,z,bore/2-.02,-.1,WALL+.2))<1e-4,name
    # Test a pessimistic 15.5-mm unmated plug length entirely outside its header.
    # Reserve additional axial withdrawal and space above the screws with the guard removed.
    plugs={}
    for ref,p in plug_centres.items():
        x,y=p['face_x'],p['centre_y']; z=BOARD_Z+1.6
        installed=box(x,y-5.08,z,15.5,10.16,12.)
        pulled=box(x,y-5.08,z,23.5,10.16,14.)
        screwdriver=box(x+1,y-5.5,z+8,13,11,BASE_TOP-(z+8)+1)
        for part_name,part,keepout in [('base/installed',base,installed),('guard/installed',guard,installed),
                                       ('base/withdrawal',base,pulled),('base/tool',base,screwdriver)]:
            assert overlap(part,keepout)<1e-4,(ref,part_name)
        plugs[ref]=dict(mating_face_case_x_mm=round(x,3),centre_case_y_mm=round(y,3),
                        plug_width_mm=10.16,plug_outward_allowance_mm=15.5,
                        installed_clearance_to_guard_mm=round(gx+gw-3-(x+15.5),3),
                        clearance_to_outer_wall_after_8mm_withdrawal_mm=round(W-WALL-(x+23.5),3))
    for name in ('base','guard'):
        assert overlap(board,base if name=='base' else guard)<1e-4,name
    assert overlap(base,guard)<1e-4,'guard interferes with base'
    # Reserve full nut corner diameters and independent thread barrels inside each wall.
    # M12 allowance is for a selected 9.5 mm thread or shorter. Check the fitted stack.
    gland_dimensions = {20.1: (29.7, 6., 13.), 16.1: (24.2, 5., 12.), 12.1: (18.7, 5., 9.5)}
    glands = {}
    for name, side, pos, z, bore in PORTS:
        if bore not in gland_dimensions:
            continue
        corners, thickness, length = gland_dimensions[bore]
        nut = wall_hole(side, pos, z, corners / 2, WALL + .02, thickness)
        thread = wall_hole(side, pos, z, (bore - .1) / 2, WALL + .02, length - WALL)
        for reserve in (nut, thread):
            assert overlap(reserve,base) < 1e-4 and overlap(reserve,guard) < 1e-4, name
            assert overlap(reserve,board) < 1e-4, name
            for other in glands.values():
                assert all(overlap(reserve,prior)<1e-4 for prior in other), name
        glands[name] = (nut,thread)
    starter_port=PORTS[0]
    nut=wall_hole('right',starter_port[2],starter_port[3],29.7/2,WALL+.02,6.)
    thread=wall_hole('right',starter_port[2],starter_port[3],10.,WALL+.02,13.-WALL)
    for solid in (nut,thread):
        assert overlap(solid,base)<1e-4 and overlap(solid,guard)<1e-4
        for ref,p in plug_centres.items():
            assert overlap(solid,box(p['face_x'],p['centre_y']-5.08,BOARD_Z+1.6,23.5,10.16,14.))<1e-4,ref

    for name,shape,flip in [('base',base,False),('main_board_guard',guard,True)]:
        assert BRepCheck_Analyzer(shape).IsValid(),name
        step=out/(name+'.step');stl=out/(name+'.stl')
        Interface_Static.SetCVal_s('write.step.unit','MM')
        writer=STEPControl_Writer();writer.Transfer(shape,STEPControl_AsIs); writer.Write(str(step))
        BRepMesh_IncrementalMesh(shape,.05,False,.12,True)
        StlAPI_Writer().Write(shape,str(stl))
        mesh=trimesh.load_mesh(stl)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume and len(mesh.split())==1,name
        if flip: mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
        mesh.apply_translation(-mesh.bounds[0]);mesh.export(stl)
        check[name]={'watertight_single_solid':True,'STEP_sha256':digest(step),'STL_sha256':digest(stl),
                     'STL_size_mm':np.round(mesh.extents,3).tolist()}
    return dict(**geometry,case_mm=[W,D,90.],transform='X=112-y; Y=125-x; board underside Z=24',
                mount_centres_case_mm={n:case_xy(x) for n,x in sorted(geometry['holes'].items())},
                ports_case_coordinates=dict((n,dict(wall=s,centre_along_wall_mm=p,height_mm=z,hole_diameter_mm=h)) for n,s,p,z,h in PORTS),
                starter_plug_checks=plugs,starter_gland_nut_and_thread_clear=True, gland_envelopes_clear=list(glands),
                base_guard_and_board_nominal_intersections=0,printed_parts=check,
                nominal_guard_roof_to_retained_panel_carrier_mm=59.5-(gz+gh),
                nominal_distance_J35_pin1_to_H5_mm=round(math.dist(geometry['holes']['H5'],ports['J35']['pads']['1']),3),
                physical_fit_verified=False,mains_material_qualified=False,ingress_or_touch_rating_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',type=Path,required=True)
    p.add_argument('--out',type=Path,default=ROOT/'output/enclosure-compact-dual')
    p.add_argument('--extract',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.extract:
        print(json.dumps(read_board(a.board)));return
    kpython=os.environ.get('KICAD_PYTHON',str(ROOT/'.tools/kicad-python'))
    data=json.loads(subprocess.check_output([kpython,__file__,'--board',str(a.board),'--extract'],text=True))
    result=build(data,a.out)
    result['pcb_file']=os.path.relpath(a.board.resolve(),ROOT)
    (a.out/'fit-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['starter_plug_checks'],indent=2))

if __name__=='__main__':
    main()
