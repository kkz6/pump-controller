"""Export per-board JLCPCB quote BOMs, placement files and assembly review items.

Run from any directory with KiCad 10. Zero translation and no bottom-X mirroring
match the absolute origin of the released Gerber/drill files. Standard placement
columns follow https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
"""
import csv
import os
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'manufacturing'
CLI = os.getenv('KICAD_CLI') or shutil.which('kicad-cli') or 'kicad-cli'
# Same-footprint procurement choices for spec-only capacitors. C20 has a separate bias check.
# JLC Basic parts where one exists (no loading-fee difference on Standard assembly, but lower
# price and deep stock). 33 pF and 1 nF stay C0G/NP0 (Extended); 22 uF 1210 stays X7R (Extended).
CAPACITORS = {
    ('100nF', '0805'): 'CC0805KRX7R9BB104', ('22uF', '1210'): 'CL32B226KOJNNNE',
    ('1uF', '0805'): 'CL21B105KBFNNNE', ('100nF', '0603'): 'CC0603KRX7R9BB104',
    ('1uF', '0603'): 'CL10A105KB8NNNC', ('10nF', '0603'): '0603B103K500NT',
    ('4.7uF', '0805'): 'CL21A475KAQNNNE', ('10uF', '0805'): 'CL21A106KAYNNNE',
    ('4.7uF', '0603'): 'CL10A475KO8NNNC', ('27pF', '0603'): 'CC0603JRNPO9BN270',
    ('1nF', '0603'): 'CC0603JRNPO9BN102', ('22uF', '0805'): 'CL21A226MAQNNNE',
    ('33pF', '0603'): '0603CG330J500NT',
}
# UNI-ROYAL 1% thick film, all JLC Basic.
RESISTORS = {
    '0603': {'10k': '0603WAF1002T5E', '1k': '0603WAF1001T5E', '2.2k': '0603WAF2201T5E',
             '47k': '0603WAF4702T5E', '100k': '0603WAF1003T5E', '22k': '0603WAF2202T5E',
             '33k': '0603WAF3302T5E', '100R': '0603WAF1000T5E', '100': '0603WAF1000T5E',
             '22R': '0603WAF220JT5E', '1M': '0603WAF1004T5E', '47': '0603WAF470JT5E',
             '47R': '0603WAF470JT5E', '5.1k': '0603WAF5101T5E'},
    '0805': {'10k': '0805W8F1002T5E', '3.3k': '0805W8F3301T5E', '22R': '0805W8F220JT5E'},
}
NORMALIZE = {'31171102 (RT13702HBWC)': '31171102', 'Samtec TSW-103-07-G-D': 'TSW-103-07-G-D',
             'Phoenix Contact 1727010 / MKDS 1/2-3,81': '1727010'}
# Parts left out of the JLC files and fitted by hand after assembly.
# Panel: the front buttons are the only front-side parts, so leaving them out lets JLC assemble the rear
# side alone on single-sided Economic PCBA instead of double-sided Standard PCBA.
# Main: the through-hole parts. Each would cost a $1.53 loading line plus hand-soldering labour and joint
# charges at JLC; U1 is bought from DigiKey anyway, and F1/J1 have no JLC catalogue entry.
HAND_FIT = {'panel': {'SW1', 'SW2', 'SW3', 'SW4', 'SW5'},
            'main': {'C1', 'F1', 'J1', 'J2', 'J10', 'J20', 'J21', 'J30', 'J35', 'J41', 'K1', 'K2', 'R1', 'RV1', 'U1'}}
SINGLE_SIDED = {'panel'}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, titles, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(titles)
        writer.writerows(rows)


def ref_order(name):
    match = re.fullmatch(r'([A-Z]+)(\d+)', name)
    if not match:
        raise ValueError(f'Unexpected designator {name}')
    return match[1], int(match[2])


def nominated(row):
    source = row['MPN']
    if not source.startswith(('Generic ', 'SPEC: ')):
        if not source:
            raise ValueError(f"Missing part number or specification for {row['Reference']}")
        return NORMALIZE.get(source, source)
    package = re.search(r'_[RC]?([0-9]{4})_', row['Footprint'])[1]
    value = row['Value'].split()[0]
    if row['Reference'].startswith('C'):
        return CAPACITORS[value, package]
    if row['Reference'].startswith('R'):
        if '0.1%' in source:
            if package != '0603' or value != '10k':
                raise ValueError(f'Unknown precision resistor {source}')
            return 'RT0603BRD0710KL'
        if '1%' not in source or value not in RESISTORS.get(package, {}):
            raise ValueError(f'Unknown resistor class {source}')
        return RESISTORS[package][value]
    raise ValueError(f'Unknown specification {source}')


def catalog():
    result = {}
    published = read_csv(ROOT / 'tools/data/jlc-parts-verified.csv')
    for row in published:
        code = row['JLCPCB Part #']
        if not re.fullmatch(r'C\d+', code):
            raise ValueError(f'Invalid catalog identifier {code}')
        mpn = NORMALIZE.get(row['MPN'], row['MPN'])
        if mpn in result and result[mpn] != code:
            raise ValueError(f'Conflicting supplier identifiers for {mpn}')
        result[mpn] = code
    return result


def prepare(board, location, stem, parts, destination=OUT):
    base = ROOT / 'hardware' / location
    rows = read_csv(base/'bom.csv')
    with tempfile.TemporaryDirectory() as work:
        pos = Path(work) / 'placements.csv'
        subprocess.run([CLI, 'pcb', 'export', 'pos', '--units', 'mm', '--format', 'csv',
                        '--side', 'both', '--exclude-dnp', '-o', str(pos), str(base/(stem+'.kicad_pcb'))],
                       check=True, stdout=subprocess.DEVNULL)
        imported = read_csv(pos)
    placements = {r['Ref']:r for r in imported}
    fitted = {r['Reference']:r for r in rows if r['DNP']=='False' and
              not r['Footprint'].startswith('MountingHole:')}
    if len({r['Reference'] for r in rows}) != len(rows):
        raise ValueError(f'{board}: repeated BOM reference')
    if len(placements) != len(imported) or placements.keys() != fitted.keys():
        raise ValueError(f'{board}: duplicate placements or BOM/CPL reference mismatch {placements.keys() ^ fitted.keys()}')
    groups = defaultdict(list)
    cpl = []
    hand = HAND_FIT.get(board, set())
    if not hand <= fitted.keys():
        raise ValueError(f'{board}: hand-fit references missing from BOM {hand - fitted.keys()}')
    sides = {placements[r]['Side'] for r in fitted if r not in hand}
    if board in SINGLE_SIDED and len(sides) != 1:
        raise ValueError(f'{board}: JLC-placed parts must be on one side for Economic assembly, found {sides}')
    for ref in sorted(fitted, key=ref_order):
        if ref in hand:
            continue
        row = fitted[ref]
        part = nominated(row)
        pos = placements[ref]
        footprint = row['Footprint'].split(':',1)[1]
        if pos['Package'] != footprint or pos['Val'] != row['Value'] or pos['Side'] not in ('top','bottom'):
            raise ValueError(f'{board} {ref}: native and BOM package/value/side mismatch')
        x, y, angle = [Decimal(pos[k]) for k in ('PosX','PosY','Rot')]
        if not all(n.is_finite() for n in (x,y,angle)):
            raise ValueError(f'{ref}: invalid coordinates')
        angle = (angle + Decimal(360)) % Decimal(360)
        cpl.append((ref, str(x), str(y), pos['Side'].title(), format(angle, 'f')))
        groups[part,footprint].append(ref)
    bom = []
    for (part,footprint), refs in groups.items():
        desc = fitted[refs[0]]['Value']
        bom.append((part+' '+desc,','.join(refs),footprint,parts.get(part,''),part,len(refs)))
    write_csv(destination/(board+'-BOM.csv'),('Comment','Designator','Footprint','JLCPCB Part #','Manufacturer Part Number','Quantity'),bom)
    write_csv(destination/(board+'-CPL.csv'),('Designator','Mid X','Mid Y','Layer','Rotation'),cpl)
    print(f'{board}: {len(cpl)} JLC placements ({len(hand)} hand-fitted); {len(bom)} lines; '
          f'{sum(bool(b[3]) for b in bom)} matched catalog lines')
