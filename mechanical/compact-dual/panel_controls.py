"""Check the native panel and generate serviceable captive button stems and caps."""
import hashlib
import json
import math
import sys
from pathlib import Path

FUNCTIONS={'START':'SW2','STOP':'SW1','MODE':'SW3','SET':'SW4','NEXT':'SW5'}

def native_panel(path):
    import pcbnew as k
    b=k.LoadBoard(str(path)); controls={}; mounting={};J8=None
    for f in b.GetFootprints():
        n=f.GetReference(); pos=f.GetPosition();xy=[k.ToMM(pos.x),k.ToMM(pos.y)]
        if n in FUNCTIONS.values():
            assert not f.IsFlipped() and f.GetOrientationDegrees()==0
            # Omron D2F actuator is displaced from its two-hole pattern origin.
            if n=='SW1': xy[0]+=1.83
            controls[n]=xy
        if n in ('H1','H2','H3','H4'):mounting[n]=xy
        if n=='J8':J8={p.GetNumber():p.GetNetname() for p in f.Pads() if p.GetNumber() in ('1','2','3')}
    assert len(controls)==5 and len(mounting)==4
    assert J8=={'1':'+5V','2':'KEY_MAN_RAW','3':'KEY_AUTO_RAW'}
    return {'panel_pcb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'actuators_native_mm':controls,'mounting_holes_native_mm':mounting,'J8_pins':J8}


def printable(shape,out,name,flip=False):
    import trimesh
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer
    assert BRepCheck_Analyzer(shape).IsValid(),name
    stl=out/(name+'.stl');BRepMesh_IncrementalMesh(shape,.015,False,.08,True)
    StlAPI_Writer().Write(shape,str(stl));mesh=trimesh.load_mesh(stl)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume and len(mesh.split())==1,name
    if flip:mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
    mesh.apply_translation(-mesh.bounds[0]);return mesh.export(file_type='stl')


def hardware(interface,native,temp,shapes):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
    from OCP.gp import gp_Ax2,gp_Dir,gp_Pnt,gp_Trsf,gp_Vec
    from check_assembly import interference,overlaps,bounds
    def cylinder(x,y,z,r,h): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(0,0,1)),r,h).Shape()
    def box(x,y,z,w,h,d):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,h,d).Shape()
    def shifted(s,dx,dy,dz):
        t=gp_Trsf();t.SetTranslation(gp_Vec(dx,dy,dz));return BRepBuilderAPI_Transform(s,t,False).Shape()
    def clear(a,b):return not overlaps(bounds(a),bounds(b)) or interference(a,b)<.005
    def union(a,b):return BRepAlgoAPI_Fuse(a,b).Shape()
    def subtract(a,b):return BRepAlgoAPI_Cut(a,b).Shape()
    panel=interface['panel'];px,py=panel['origin']; w,h,t=panel['size'];face=panel['front_z']
    assert sorted(native['mounting_holes_native_mm'].values())==sorted(panel['holes'])
    # Confirm each lid-panel mounting screw can cross its retained carrier hole.
    for hx,hy in panel['holes']:
        x,y=px+hx,py+h-hy
        assert clear(shapes['panel_carrier'],cylinder(x,y,59.4,1.25,14.))
    controls={}; parts={}; moving=[]; lid=shapes['lid']; base=shapes['base']; guard=shapes['main_board_guard']
    for item in panel['buttons']:
        name=item['name'];ref=FUNCTIONS[name]; x,y=native['actuators_native_mm'][ref]
        assert abs(x-item['xy'][0])<.001 and abs(y-item['xy'][1])<.001
        x,y=px+x,py+h-y;stroke=item['stroke_stop'];top=90+stroke;tip=face+item['free_height']+panel['actuator_rest_gap']
        # Insert stem from underside; the 8 mm return flange seats below the lid.
        shoulder_z=top-5.7
        stem=union(cylinder(x,y,tip,1.4,shoulder_z-tip+.05),cylinder(x,y,shoulder_z,3.10,5.7))
        stem=union(stem,cylinder(x,y,85.75,4.,1.05))
        stem=subtract(stem,cylinder(x,y,top-5.,1.6,5.1))
        # A separately screwed cap provides the upper 8 mm stop and covers the bore.
        cap=cylinder(x,y,top,4.,2.)
        cap=subtract(cap,cylinder(x,y,top-.1,1.1,2.2))
        seat=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(x,y,top+.95),gp_Dir(0,0,1)),1.1,2.2,1.1).Shape()
        cap=subtract(cap,seat)
        assert clear(lid,cylinder(x,y,86.75,3.245,3.35)),name+' bore'
        assert all(clear(lid,shifted(stem,0,0,d)) for d in (-8.,-5.,-2.,0.)),name+' installation'
        for delta in (0.,-stroke/2,-stroke):
            for shape in (stem,cap):
                part=shifted(shape,0,0,delta)
                assert all(clear(part,other) for other in (lid,base,guard,shapes['display_retainer'],shapes['panel_carrier'])),name+' travel'
                assert all(clear(part,other) for other in moving),name+' neighboring cap'
        for part,suffix,flip in ((stem,'stem',True),(cap,'cap',False)):
            n=name.lower()+'_'+suffix
            parts[n+'.stl']=printable(part,temp,n,flip)
        moving.extend((stem,cap));controls[name]={'switch':ref,'case_xy_mm':[x,y],'actuator_rest_gap_mm':panel['actuator_rest_gap'],'nominal_stroke_stop_mm':stroke,'nominal_switch_travel_after_rest_gap_mm':round(stroke-panel['actuator_rest_gap'],3),'stem_tip_z_mm':round(tip,3)}
    key=interface['key'];kx,ky=key['centre'];ww,dd,depth=key['reserved_body'];below=86.8-depth
    reserved=box(kx-ww/2,ky-dd/2,below,ww,dd,depth)
    assert all(clear(reserved,s) for s in [base,guard,shapes['panel_carrier'],shapes['display_retainer'],*moving])
    assert clear(shapes['key_22p5_adapter_OPTIONAL'],cylinder(kx,ky,87.5,11.24,6))
    assert interference(shapes['key_blank_plate'],cylinder(kx,ky,87.5,11.24,6))>100
    for alternative in ('key_blank_plate','key_22p5_adapter_OPTIONAL'):
        assert clear(lid,shapes[alternative]),alternative
    key_data={'adapter_hole_mm':22.5,'plate_thickness_at_bore_mm':5.2,'reserved_below_lid_xyz_mm':[ww,dd,depth],'reserved_body_to_guard_roof_mm':round(below-bounds(guard)[5],3),'external_panel_key_entry':'dedicated M12 MODE KEY'}
    return parts, controls, key_data

if __name__=='__main__':print(json.dumps(native_panel(Path(sys.argv[1]))))
