"""Verify the retained lid in assembly space and bundle the five-button enclosure and key option."""
import argparse
import hashlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import trimesh
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Vec
from build import ROOT
from panel_controls import hardware
from draw_panel import draw
from check_assembly import bounds, interference, overlaps, read


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--panel',type=Path,default=ROOT/'hardware/panel-rev-e/pump-panel-rev-e.kicad_pcb')
    parser.add_argument('--kicad-python',default=ROOT/'.tools/kicad-python')
    args=parser.parse_args();output=args.output
    native=json.loads(subprocess.check_output([str(args.kicad_python),str(Path(__file__).with_name('panel_controls.py')),str(args.panel.resolve())],text=True))
    frozen=Path(__file__).with_name('five-button-lid.zip')
    body, guard = read(output/'base.step'), read(output/'main_board_guard.step')
    printed = {n+'.stl': (output/(n+'.stl')).read_bytes() for n in ('base','main_board_guard')}
    fit=json.loads((output/'fit-checks.json').read_text())
    for name,data in printed.items():
        assert fit['printed_parts'][Path(name).stem]['STL_sha256']==sha(data)
    parts={};shapes={'base':body,'main_board_guard':guard}
    with ZipFile(frozen) as archive, tempfile.TemporaryDirectory() as temp:
        lid=json.loads(archive.read('lid-manifest.json'))
        for n,record in lid.items():
            data=archive.read(n+'.stl');assert sha(data)==record['sha256']
            mesh=trimesh.load(io.BytesIO(data),file_type='stl')
            assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
            printed[n+'.stl']=data
            path=Path(temp)/(n+'.step');path.write_bytes(archive.read(path.name))
            assert sha(path.read_bytes())==record['step_sha256']
            move=gp_Trsf();move.SetTranslation(gp_Vec(*record['step_to_assembly_translation_mm']))
            part=BRepBuilderAPI_Transform(read(path),move,False).Shape()
            shapes[n]=part
            for target in (body,guard):
                assert not overlaps(bounds(target),bounds(part)) or interference(part,target)<.005,n
            parts[n]={'stl':n+'.stl','sha256':sha(data),'step_sha256':record['step_sha256']}
        interface=json.loads(archive.read('interface.json'))
        button_parts,controls,key=hardware(interface,native,Path(temp),shapes)
        printed.update(button_parts)
    outzip=output/'compact-dual-five-button-print-parts.zip'
    with ZipFile(outzip,'w',compression=ZIP_DEFLATED) as zipout:
        for name,data in sorted(printed.items()):
            info = ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipout.writestr(info,data)
    with ZipFile(outzip) as zipin:
        assert zipin.testzip() is None and sorted(zipin.namelist())==sorted(printed)
    result={'source_pcb_sha256':fit['pcb_hash'], 'packed_stl_count':len(printed),'print_file_sha256':sha(outzip.read_bytes()),
            'print_part_sha256':{n:sha(v) for n,v in sorted(printed.items())},'lid_subset_source_sha256':sha(frozen.read_bytes()),
            'panel':native,'five_button_fits':controls,'optional_key_fit':key,'retained_lid_parts_checked':list(parts),
            'parts_per_assembly':len(printed)-1,'interchangeable_key_plates':['key_blank_plate.stl','key_22p5_adapter_OPTIONAL.stl'],'lid_base_guard_nominal_intersections':0,
            'hardware_excluded':['fasteners','window','glands, locknuts and blanks','connector hardware','electronics','wired looms']}
    (output/'print-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    draw(output)
    result['front_label_sha256']=sha((output/'front-label-template.svg').read_bytes())
    (output/'print-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
