"""Compare native populated STEP solids with the enclosure in assembly coordinates."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

from OCP.Bnd import Bnd_Box
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec

from build import BOARD_Z, CASE_X_ZERO, CASE_Y_ZERO, FLOOR, GUARD, GUARD_FEET, LID_TOWERS, ROOT, WALL, W, D


def read(path):
    reader = STEPControl_Reader()
    assert int(reader.ReadFile(str(path))) == 1, path
    reader.TransferRoots()
    return reader.OneShape()


def bounds(shape):
    box = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, box, False, False)
    low, high = box.CornerMin(), box.CornerMax()
    return (low.X(),low.Y(),low.Z(),high.X(),high.Y(),high.Z())


def interference(solid, enclosure):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(BRepAlgoAPI_Common(solid, enclosure).Shape(), props)
    return props.Mass()


def overlaps(a, b):
    return all(a[i] < b[i+3] - 1e-4 and b[i] < a[i+3] - 1e-4 for i in range(3))


def in_bounds(small, large):
    return all(small[i] >= large[i] - 1e-4 and small[i+3] <= large[i+3] + 1e-4 for i in range(3))


def check(model, out, missing):
    data = json.loads((out/'fit-checks.json').read_text())
    # KiCad STEP coordinates are X, -Y, Z. Rotate -90 about Z then translate.
    transform = gp_Trsf()
    transform.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), -math.pi/2)
    transform.SetTranslationPart(gp_Vec(CASE_X_ZERO, CASE_Y_ZERO, BOARD_Z))
    assembly = BRepBuilderAPI_Transform(read(model), transform, False).Shape()
    extent = bounds(assembly)
    base, guard = read(out/'base.step'), read(out/'main_board_guard.step')
    # Full STEP booleans are necessary only where bounding boxes overlap matter.
    # The central void, fixed internal divider and screw posts follow build.py.
    base_posts = [(x-4,y-4,FLOOR,x+4,y+4,BOARD_Z) for x,y in data['mount_centres_case_mm'].values()]
    base_posts.extend((x-4.5,y-4.5,FLOOR,x+4.5,y+4.5,8.) for x,y in GUARD_FEET)
    base_posts.extend((x-5.,y-5.,FLOOR,x+5.,y+5.,86.8) for x,y in LID_TOWERS)
    base_posts.append((WALL,84.,FLOOR,29.,86.5,FLOOR+30.))
    base_void = (WALL,WALL,FLOOR,W-WALL,D-WALL,86.8)
    gx,gy,gz,gw,gd,gh=GUARD
    guard_void = (gx+3,gy+3,gz, gx+gw-3,gy+gd-3,gz+gh-3)
    guard_posts = [(x-4.5,y-4.5,8.,x+4.5,y+4.5,11.) for x,y in GUARD_FEET]
    ex=TopExp_Explorer(assembly,TopAbs_SOLID)
    count=0
    intersections=[]
    while ex.More():
        solid=ex.Current(); ex.Next(); count+=1
        b=bounds(solid)
        for name, shell, void, posts in [('base',base,base_void,base_posts),('guard',guard,guard_void,guard_posts)]:
            if in_bounds(b,void) and not any(overlaps(b,p) for p in posts):
                continue
            v = interference(solid,shell)
            if v > .005:
                intersections.append({'solid':count, 'part':name, 'volume_mm3':round(v,5), 'bounds_mm':list(b)})
    assert count >=100, 'Expected populated board with component solids'
    result={'source_pcb_sha256':data['pcb_hash'],'populated_STEP_solids_checked':count,
            'native_export_missing_model_refs':missing,'populated_bounds_case_xyzxyz_mm':[round(v,3) for v in extent],
            'min_clearance_to_floor_plane_mm':round(extent[2]-FLOOR,3),
            'min_clearance_to_guard_roof_plane_mm':round(guard_void[5]-extent[5],3),
            'nominal_step_intersections':intersections, 'volume_tolerance_mm3':.005,
            'measurement_scope':'Modeled solids only. Mating plugs and gland reserves are checked separately in fit-checks.json. Measure real electronics and dressed cables.'}
    (out/'populated-fit.json').write_text(json.dumps(result,indent=2)+'\n')
    assert not intersections, intersections
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--kicad-cli',default=ROOT/'.tools/kicad-cli')
    parser.add_argument('--kicad-python',default=ROOT/'.tools/kicad-python')
    args=parser.parse_args()
    recorded=json.loads((args.output/'fit-checks.json').read_text())
    assert recorded['pcb_hash'] == hashlib.sha256(args.board.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as work:
        work=Path(work); model=work/'main.step'; visual=work/'populated.kicad_pcb'; coverage=work/'coverage.json'
        subprocess.run([str(args.kicad_python),str(ROOT/'tools/prepare_compact_3d.py'),'--board',str(args.board.resolve()),'--visual',str(visual),'--coverage',str(coverage),'--expected-sha256',recorded['pcb_hash'],'--private-inputs',str(work/'models.json')],check=True)
        run=subprocess.run([str(args.kicad_cli),'pcb','export','step','--user-origin','0x0mm','--output',str(model),str(visual)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        missing=re.findall(r'Could not add 3D model for (\S+)\.',run.stdout)
        assert not missing, missing
        result=check(model,args.output,missing)
        records=json.loads(coverage.read_text())['component_records']
        result['approximate_project_body_refs']=sorted(r['reference'] for r in records if r['status']=='approximate_project_body')
        result['component_footprints_represented']=sum(r['status']!='mounting_hole_without_fastener' for r in records)
        result['installed_envelope_refs']=sorted(r['reference'] for r in records if r['status']=='conservative_installed_envelope')
        (args.output/'populated-fit.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
