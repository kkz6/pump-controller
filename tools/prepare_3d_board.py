"""Attach missing visualization bodies on a separate copy using KiCad pcbnew.

Never saves or changes the electrically authoritative board.
"""
from pathlib import Path
import argparse,hashlib,json,os
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--board',default='hardware/pump-controller-rev-b.kicad_pcb')
parser.add_argument('--tag',default='rev-c')
args=parser.parse_args()
SOURCE=ROOT/args.board
DEST=ROOT/'tmp/3d'/('pump-controller-'+args.tag+'-visualization.kicad_pcb')
DEST.parent.mkdir(parents=True,exist_ok=True)
before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
board=pcbnew.LoadBoard(str(SOURCE))
definitions=json.loads((ROOT/'hardware/3d/approximate-bodies.json').read_text())
lookup={ref:name for name,d in definitions.items() for ref in d['references']}
coverage=[]
for footprint in board.GetFootprints():
    ref=footprint.GetReference()
    if ref == 'C1' and args.tag == 'rev-e':
        assert any('C1_EEUFR1E470_max_envelope.step' in model.m_Filename for model in footprint.Models()), 'Apply the C1 installed-envelope patch first'
        footprint.Models().clear()
        model=pcbnew.FP_3DMODEL()
        model.m_Filename=str(ROOT/'hardware/3d/models/C1_EEUFR1E470_max_envelope.step')
        footprint.Add3DModel(model)
        status='approximate_project_body'
    elif ref in lookup:
        footprint.Models().clear()
        model=pcbnew.FP_3DMODEL()
        model.m_Filename=str(ROOT/'hardware/3d/models'/(lookup[ref]+'.step'))
        footprint.Add3DModel(model)
        status='approximate_project_body'
    elif ref.startswith('H'):
        status='mounting_hole_no_body'
    else:
        assert len(footprint.Models()),ref
        for model in footprint.Models():assert Path(os.path.expandvars(model.m_Filename)).exists(),model.m_Filename
        status='installed_KiCad_standard_body'
    coverage.append({'reference':ref,'status':status})
pcbnew.SaveBoard(str(DEST),board)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before
standard=sum(x['status']=='installed_KiCad_standard_body' for x in coverage)
approximate=sum(x['status']=='approximate_project_body' for x in coverage)
holes=sum(x['status']=='mounting_hole_no_body' for x in coverage)
record={'source_board':str(SOURCE.relative_to(ROOT)),'source_board_sha256':before,
        'electrical_board_modified':False,'electrical_components':standard+approximate,
        'standard_library_bodies':standard,'approximate_component_bodies':approximate,
        'mounting_holes_without_fasteners':holes,
        'coordinate_basis':'Native KiCad footprint position, rotation and side; board units millimetres.',
        'not_validated':['Enclosure fit','Mating terminal plugs and wire bends','Part tolerance and lead forming','Fastener clearance','Insulation covers','Thermal or electrical safety'],
        'coverage':sorted(coverage,key=lambda x:x['reference'])}
(ROOT/'hardware/3d'/('model-coverage-'+args.tag+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(DEST)
