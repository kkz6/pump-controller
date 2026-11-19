from pathlib import Path
import shutil,json,hashlib,os
import pcbnew as p
base=Path(__file__).resolve().parents[1];hw=base/'hardware';source=Path(os.environ['KICAD10_FOOTPRINT_DIR']);manifest=[]
for board_path in [hw/'pump-controller-rev-b.kicad_pcb']:
 b=p.LoadBoard(str(board_path));libraries=set()
 for f in b.GetFootprints():
  lib=str(f.GetFPID().GetLibNickname());name=str(f.GetFPID().GetLibItemName())
  if not lib:
   # KiCad-loaded mounting-hole footprints retain their item name but no nickname.
   if name.startswith('MountingHole'):lib='MountingHole';f.SetFPID(p.LIB_ID(lib,name))
   else:raise ValueError((f.GetReference(),str(f.GetFPID())))
  libraries.add(lib)
  if lib=='Pump':continue
  src=source/(lib+'.pretty')/(name+'.kicad_mod');dst=hw/'libraries'/(lib+'.pretty')/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  entry={'library':lib,'footprint':name,'source':'KiCad 10.0.8 official macOS distribution','sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
  if entry not in manifest:manifest.append(entry)
 p.SaveBoard(str(board_path),b)
 table=['(fp_lib_table (version 7)']
 for lib in sorted(libraries):
  dest=hw/'Pump.pretty' if lib=='Pump' else hw/'libraries'/(lib+'.pretty');uri='${KIPRJMOD}/'+os.path.relpath(dest,board_path.parent)
  table.append('(lib (name "%s") (type "KiCad") (uri "%s") (options "") (descr "Project-local portable footprint cache"))'%(lib,uri))
 table.append(')');(board_path.parent/'fp-lib-table').write_text('\n'.join(table)+'\n')
(hw/'libraries/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Cached',len(manifest),'standard footprints')
