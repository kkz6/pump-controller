#!/usr/bin/env python3
"""Export Rev E prototype CAM after native and independent geometry checks pass.
Packaging additionally requires the independently parsed final CAM report.
Never submits an order or claims assembled-product qualification.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,tempfile,shutil,zipfile
from package_main_rev_e import add_board_options, board_variant, invalidate_packages
B=Path(__file__).resolve().parents[1];CLI=B/'.tools/kicad-cli'
LAYERS={'F_Cu':('GTL','Copper,L1,Top'),'In1_Cu':('G2L','Copper,L2,Inr'),'In2_Cu':('G3L','Copper,L3,Inr'),'In3_Cu':('G4L','Copper,L4,Inr'),'In4_Cu':('G5L','Copper,L5,Inr'),'B_Cu':('GBL','Copper,L6,Bot'),'F_Mask':('GTS','Soldermask,Top'),'B_Mask':('GBS','Soldermask,Bot'),'F_Silkscreen':('GTO','Legend,Top'),'B_Silkscreen':('GBO','Legend,Bot'),'Edge_Cuts':('GKO','Profile,NP')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
 r=subprocess.run([str(CLI)]+list(map(str,args)),capture_output=True,text=True,cwd=B)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 print(r.stdout.strip())
def source_hashes(BOARD, source):
 O=BOARD.parent
 paths=[BOARD,BOARD.with_suffix('.kicad_pro'),BOARD.with_suffix('.kicad_dru'),source]+sorted(O.glob('*.kicad_sch'))
 return{str(p.relative_to(B)):sha(p)for p in paths}
def export(compact=False, compact_dual=False, integrated=False):
 variant=board_variant(compact, compact_dual, integrated)
 O=B/'hardware'/variant.directory
 P=variant.cam_name
 BOARD=O/(variant.native_name+'.kicad_pcb')
 source=B/variant.design
 size=list(variant.size)
 invalidate_packages(O,variant)
 frozen=source_hashes(BOARD, source);checks=O/'checks';checks.mkdir(exist_ok=True)
 run(['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',checks/'export-erc.json',BOARD.with_suffix('.kicad_sch')])
 run(['pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--exit-code-violations','-o',checks/'export-drc.json',BOARD])
 d=json.loads((checks/'export-drc.json').read_text())
 if any(d[k]for k in['violations','unconnected_items','schematic_parity']):raise SystemExit('Native checks failed; export refused')
 independent=json.loads((checks/'independent-summary.json').read_text())
 if not independent['independent_native_checks_passed']or independent['source_sha256']!=frozen:raise SystemExit('Independent evidence missing, failed or stale; export refused')
 fab=O/'gerber';paste=O/'exports/stencil';maps=O/'exports/drill-maps'
 for d in[fab,paste,maps]:d.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='pump-e-cam-')as t:
  temp=Path(t)
  run(['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--disable-aperture-macros','--subtract-soldermask','--check-zones','--precision','6','-o',str(temp/'board')+'/',BOARD])
  rename={}
  for layer,(ext,function)in LAYERS.items():
   src=next(p for p in(temp/'board').iterdir()if p.stem.endswith('-'+layer))
   if '%TF.FileFunction,'+function+'*%'not in src.read_text():raise RuntimeError('Wrong layer '+layer)
   dst=fab/(P+'.'+ext);shutil.copyfile(src,dst);rename[src.name]=dst.name
  job=json.loads(next((temp/'board').glob('*.gbrjob')).read_text())
  for f in job['FilesAttributes']:f['Path']=rename[f['Path']]
  # Requested finished dimensions are outline centreline, not the stroked plot bounding box.
  job.setdefault('GeneralSpecs',{})['Size']={'X':size[0],'Y':size[1]}
  (fab/(P+'.gbrjob')).write_text(json.dumps(job,indent=2)+'\n')
  run(['pcb','export','gerbers','--layers','F.Paste,B.Paste','--disable-aperture-macros','--precision','6','-o',str(temp/'stencil')+'/',BOARD])
  for layer,ext in[('F_Paste','GTP'),('B_Paste','GBP')]:
   src=next(p for p in(temp/'stencil').iterdir()if p.stem.endswith('-'+layer));shutil.copyfile(src,paste/(P+'.'+ext))
  run(['pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-map','--map-format','svg','--generate-report','--report-path',maps/'drill-report.txt','-o',str(temp/'drills')+'/',BOARD])
  for src in(temp/'drills').iterdir():
   if src.suffix=='.drl':shutil.copyfile(src,fab/(P+('-NPTH.XLN'if'NPTH'in src.name else'-PTH.XLN')))
   elif src.suffix=='.svg':shutil.copyfile(src,maps/src.name)
  run(['pcb','export','ipcd356','-o',fab/(P+'.d356'),BOARD])
 run(['pcb','export','pos','--format','csv','--units','mm','--side','both','--exclude-dnp','-o',O/'exports/component-positions.csv',BOARD])
 if compact_dual or integrated:
  run(['sch','export','pdf','-o',O/'exports/schematic.pdf',BOARD.with_suffix('.kicad_sch')])
 svg_output=O/'exports/schematic-svg'
 svg_output.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='pump-schematic-svg-') as temp:
  svg_temp=Path(temp)
  run(['sch','export','svg','-o',str(svg_temp)+'/',BOARD.with_suffix('.kicad_sch')])
  pages=list(svg_temp.glob('*.svg'))
  if not pages: raise RuntimeError('No schematic SVG pages were exported')
  for page in pages: shutil.copyfile(page,svg_output/page.name)
  current={page.name for page in pages}
  for previous in svg_output.glob(BOARD.stem+'*.svg'):
   if previous.name not in current: previous.unlink()
 if source_hashes(BOARD, source)!=frozen:raise RuntimeError('CAD changed during export')
 manifest={'revision':variant.revision,'purpose':'Bare PCB engineering prototype','pcb_prototype_order_package':False,'assembled_product_qualified':False,'source_sha256':frozen,'outline_mm':size,'layer_order':['GTL','G2L','G3L','G4L','G5L','GBL'],'thickness_mm':1.6,'solder_mask':'green','outer_copper_oz':1,'inner_copper_oz':.5,'finish':'ENIG','material':'FR4 Tg155 or vendor-confirmed equivalent','exact_dielectric_stackup_vendor_confirmation_required':True,'controlled_impedance_specified':False,'origin':'absolute, metric, unmirrored across all CAM and drill files','through_vias_only':True,'via_in_pad':False,'manufacturer_confirmed':False,'hardware_tested':False,'output_sha256':{str(p.relative_to(O)):sha(p)for folder in[fab,paste,maps]for p in sorted(folder.iterdir())if p.is_file()}}
 (O/'fabrication-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Raw CAM exported. Independent CAM validation required before packaging.')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 add_board_options(parser)
 export(**vars(parser.parse_args()))
