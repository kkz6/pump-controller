"""Derive a JLC assembly variant that leaves K1/K2 for local fitting.

The released R4 PCB and all electrical connections remain unchanged. Run after
exporting and validating the full assembly, then upload this variant's BOM/CPL.
"""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from prepare_jlc_assembly import HAND_FIT

ROOT = Path(__file__).resolve().parents[1]
MF = ROOT/'manufacturing'
OUT = MF/'local-relays'
OMIT = {'K1','K2'}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encode(columns, rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode()

def main():
    release=json.loads((MF/'verification.json').read_text())
    for name in ['main-gerbers.zip','main-BOM.csv','main-CPL.csv','main-stencil.zip']:
        assert digest((MF/name).read_bytes())==release['output_sha256'][name],name
    source='hardware/main/pump-direct.kicad_pcb'
    board_hash=digest((ROOT/source).read_bytes())
    assert board_hash==release['boards']['main']['source_sha256'][source]
    with (MF/'main-BOM.csv').open() as stream:
        reader=csv.DictReader(stream);bom_columns=reader.fieldnames;bom=list(reader)
    with (MF/'main-CPL.csv').open() as stream:
        reader=csv.DictReader(stream);cpl_columns=reader.fieldnames;cpl=list(reader)
    dropped=[r for r in bom if set(r['Designator'].split(',')) & OMIT]
    assert len(dropped)==1 and set(dropped[0]['Designator'].split(','))==OMIT
    assert dropped[0]['Manufacturer Part Number']=='G5RL-1-E-HR DC5'
    variant_bom=[r for r in bom if r not in dropped]
    variant_cpl=[r for r in cpl if r['Designator'] not in OMIT]
    assert len(bom)==63 and len(variant_bom)==62 and len(cpl)==226 and len(variant_cpl)==224
    assert {r['Designator'] for r in cpl if r not in variant_cpl}==OMIT
    assert any(set(r['Designator'].split(','))=={'J30','J35'} and r['JLCPCB Part #']=='C91156' for r in variant_bom)
    files={'main-gerbers.zip':(MF/'main-gerbers.zip').read_bytes(),
           'main-BOM.csv':encode(bom_columns,variant_bom),
           'main-CPL.csv':encode(cpl_columns,variant_cpl),
           'main-stencil.zip':(MF/'main-stencil.zip').read_bytes()}
    record={'PCB_revision':'DIRECT-R4-PROTOTYPE','assembly_variant':'locally fitted relays',
            'board_sha256':board_hash,'omitted_from_JLC_assembly':sorted(OMIT),
            'locally_fitted_relay':'G5RL-1-E-HR DC5 (5 V coil, eight-pin SPDT)',
            'JLC_output_terminals':'J30/J35: Phoenix 1711738 / C91156',
            'JLC_BOM_lines':62,'JLC_placements_per_board':224,
            'hand_fitted_parts':sorted(HAND_FIT['main'] | OMIT),
            'source_full_release_output_sha256':{n:release['output_sha256'][n] for n in files},
            'variant_output_sha256':{n:digest(d) for n,d in files.items()},
            'other_BOM_rows_and_placement_coordinates_unchanged':True}
    files['assembly-variant.json']=(json.dumps(record,indent=2)+'\n').encode()
    files['READ-ME-FIRST.txt']=b'''R4 PCB - LOCAL RELAY ASSEMBLY VARIANT

Upload the matching main-gerbers.zip, main-BOM.csv and main-CPL.csv in this
folder. Finished board: 100 x 118.5 mm, six layers. Standard PCBA on both sides.
Assemble two boards from five bare PCBs unless the order explicitly says otherwise.

Leave K1/K2 UNPOPULATED. The customer will fit exact G5RL-1-E-HR DC5 relays
locally: 5 V coil, eight-pin SPDT. DC12/12 V and SPST 1A variants do not match.
J30/J35 Phoenix 1711738 / C91156 remain included for factory THT assembly.
62 JLC BOM lines, 224 placements per board, 13 hand-fitted main-board parts.

PCB, copper, mask, drill, stencil and all remaining placement coordinates are
identical to the validated pcb-r4 release. Only K1/K2 are omitted from this
assembly BOM and CPL. The relay lands remain on the PCB.

Do not combine this variant's BOM with the full R4 CPL or vice versa. Historical
JLC angle corrections are already included. Request actual placement review,
with automatic approval disabled, and JLC-added rails/fiducials/tooling clear
of the edge connectors. No physical commissioning or production approval is
established by the released design checks.
'''
    manifest={n:digest(d) for n,d in files.items()}
    files['SHA256.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    OUT.mkdir(exist_ok=True)
    for name,data in files.items():(OUT/name).write_bytes(data)
    bundle=MF/'pump-controller-R4-local-relays-JLC-upload.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():archive.writestr(name,data)
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        assert all(digest(archive.read(n))==h for n,h in manifest.items())
    print('PASS: same R4 PCB; only K1/K2 omitted; 62 BOM lines / 224 JLC placements; connectors retained.')

if __name__=='__main__':main()
