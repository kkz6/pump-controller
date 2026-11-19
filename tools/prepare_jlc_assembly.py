"""Export per-board JLCPCB quote BOMs, placement files and assembly review items.

Run from any directory with KiCad 10. Zero translation and no bottom-X mirroring
match the absolute origin of the released Gerber/drill files. Standard placement
columns follow https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
"""
import argparse
import csv
import os
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/jlc-r4'
CLI = os.getenv('KICAD_CLI') or shutil.which('kicad-cli') or str(ROOT / '.tools/kicad-cli')
BOARDS = {'main': ('main-integrated', 'pump-controller-integrated'),
          'panel': ('panel-rev-f', 'pump-panel-rev-f')}
# Same-footprint procurement choices for spec-only capacitors. C20 has a separate bias check.
CAPACITORS = {
    ('100nF', '0805'): 'GRM21BR71H104KA01L', ('22uF', '1210'): 'C3225X7R1C226M250AC',
    ('1uF', '0805'): 'GRM21BR71C105KA01L', ('100nF', '0603'): 'GRM188R71C104KA01D',
    ('1uF', '0603'): 'GRM188R71C105KA12D', ('10nF', '0603'): 'GRM188R71C103KA01D',
    ('4.7uF', '0805'): 'EMK212AB7475KGHT', ('10uF', '0805'): 'TCC0805X7R106K160FT',
    ('4.7uF', '0603'): 'TCC0603X7R475K160CT', ('27pF', '0603'): 'GRM1885C1H270JA01D',
    ('1nF', '0603'): 'GRM1885C1H102JA01D',
}
NORMALIZE = {'31171102 (RT13702HBWC)': '31171102', 'Samtec TSW-103-07-G-D': 'TSW-103-07-G-D',
             'Phoenix Contact 1727010 / MKDS 1/2-3,81': '1727010'}
REVIEW_MAIN = {
    'C20':'Confirm the selected 22 uF MLCC retains at least 10 uF at 3.3 V under the design conditions.',
    'J40':'Inspect all USB-C lands, mechanical tabs, fit and both 0.65 ±0.05 mm finished locator holes.',
    'U11':'Confirm pin 1, exact isolation package and close bypass layout with four 0402 capacitors.',
    'U1':'Confirm exact AC/DC converter mechanical pins, isolation rating, footprint and through-hole assembly.',
    'U301':'Resolve the exact TI orderable SOIC-8 comparator against its data sheet. Review any MPN correction before assembly.',
    'RV1':'Thermally protected MOV must have the specified inline lead-form suffix.',
    'R1':'Use the specified fusible, flameproof resistor and lead form.',
    'F1':'Use the specified time-delay 600 VAC axial pigtail fuse.',
    'R2':'Verify resistor dissipation, land size and solder spreading on the production assembly.',
    'K1':'Verify coil voltage and contact configuration; preserve the isolation corridor.',
    'K2':'Verify coil voltage and contact configuration; preserve the isolation corridor.',
    'KFB1':'Require the exact 24 V H1 coil, low-level contact and pin assignment.',
    'U302':'Use the exact VO617A-3 CTR rank and DIP package.',
    'U303':'Use the exact VO617A-3 CTR rank and DIP package.',
    'U3':'Use the external-antenna 1U module with H8 flash; confirm module orientation.',
    'J10':'Confirm fixed CT terminal and side-entry orientation; this connector is mains-referenced.',
}
REVIEW_PANEL = {'SW1':'Through-hole normally closed STOP. Inspect COM/NC and actual body/actuator position.',
                'J7':'The OLED module and mating cable are purchased separately.',
                'J2':'The mandatory remote STOP station or cavity 3–4 loop plug is purchased separately.'}


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
        if '1%' not in source or package not in ('0603', '0805'):
            raise ValueError(f'Unknown resistor class {source}')
        token = value.upper()
        if token == '2.2K':
            token = '2K2'
        elif token == '3.3K':
            token = '3K3'
        elif token.isdigit():
            token += 'R'
        return 'RC' + package + 'FR-07' + token + 'L'
    raise ValueError(f'Unknown specification {source}')


def catalog():
    result = {}
    published = read_csv(OUT / 'jlc-parts-verified.csv')
    for row in published:
        code = row['JLCPCB Part #']
        if not re.fullmatch(r'C\d+', code):
            raise ValueError(f'Invalid catalog identifier {code}')
        mpn = NORMALIZE.get(row['MPN'], row['MPN'])
        if mpn in result and result[mpn] != code:
            raise ValueError(f'Conflicting supplier identifiers for {mpn}')
        result[mpn] = code
    return result


def prepare(board, location, stem, parts):
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
    cpl, notes, decisions = [], [], []
    specials = REVIEW_MAIN if board=='main' else REVIEW_PANEL
    for ref in sorted(fitted, key=ref_order):
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
        if row['MPN'].startswith(('Generic ', 'SPEC: ')):
            decisions.append((board,ref,row['MPN'],part,footprint,
                              'Verify >=10 uF under bias before assembly' if ref=='C20' else 'Nominal ratings and package selected for quote'))
        if not parts.get(part):
            notes.append((board,ref,part,'Supplier match','Select the exact manufacturer part number and validate package, stock and price.'))
        if ref in specials:
            notes.append((board,ref,part,'Part review',specials[ref]))
        if ref.startswith(('J','K','SW','RV','F','D','Q','U','Y')) or (board=='main' and ref in ('C1','R1')):
            notes.append((board,ref,part,'Placement review',
                          'Compare native anchor, pin 1, polarity/contact numbering and mating face to JLC placement preview. Confirm through-hole work if applicable.'))
    bom = []
    for (part,footprint), refs in groups.items():
        desc = fitted[refs[0]]['Value']
        bom.append((part+' '+desc,','.join(refs),footprint,parts.get(part,''),part,len(refs)))
    write_csv(OUT/(board+'-BOM.csv'),('Comment','Designator','Footprint','JLCPCB Part #','Manufacturer Part Number','Quantity'),bom)
    write_csv(OUT/(board+'-CPL.csv'),('Designator','Mid X','Mid Y','Layer','Rotation'),cpl)
    print(f'{board}: {len(fitted)} placements; {len(bom)} lines; {sum(bool(b[3]) for b in bom)} matched catalog lines')
    return notes, decisions


def stock_exceptions(quantity):
    catalog_rows = read_csv(OUT / 'jlc-parts-verified.csv')
    available = {row['JLCPCB Part #']: int(row['Availability']) for row in catalog_rows}
    needed = Counter()
    orders = []
    for board in BOARDS:
        for item in read_csv(OUT / (board + '-BOM.csv')):
            code = item['JLCPCB Part #']
            if code:
                needed[code] += quantity * int(item['Quantity'])
                orders.append((board, item))
    for board, item in orders:
        code = item['JLCPCB Part #']
        if code not in available:
            action = 'Check live catalog inventory and ask for production allocation.'
        elif available[code] < needed[code]:
            action = (f"Catalog snapshot {available[code]} pieces; need {needed[code]} "
                      f"for {quantity} complete pairs before assembly attrition.")
        else:
            continue
        yield (board, item['Designator'], item['Manufacturer Part Number'], 'Procurement', action)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quantity', type=int, default=2, help='Sets of main and panel for the inventory comparison')
    quantity = parser.parse_args().quantity
    if quantity < 1:
        raise ValueError('Quantity must be positive')
    OUT.mkdir(parents=True, exist_ok=True)
    parts = catalog()
    notes, decisions = [], []
    for name,(directory,stem) in BOARDS.items():
        errors, chosen = prepare(name,directory,stem,parts)
        notes.extend(errors)
        decisions.extend(chosen)
    notes.extend(stock_exceptions(quantity))
    write_csv(OUT/'assembly-exceptions.csv',('Board','Designator','Manufacturer Part Number','Review','Action'),notes)
    write_csv(OUT/'passive-selections.csv',('Board','Designator','Original procurement specification','Quoted manufacturer part number','Footprint','Qualification'),decisions)


if __name__=='__main__':
    main()
