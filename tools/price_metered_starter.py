"""Build one installed set from the per-board placement BOMs and purchasing schedules."""
import csv
import json
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/starter-metered-r4'
OLD = ROOT / 'output/jlc-r4'
BOARDS = ROOT / 'output/socketed-r4'


def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def write(path, rows):
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def cabinet():
    rows = [r for r in read(OLD/'budget-cabinet-one-starter.csv')
            if r['Schematic refs or field assembly'] not in {'KV1','KC1'}]
    by_ref = {r['Schematic refs or field assembly']:r for r in rows}
    for ref, label, mpn, terms in [
        ('XP1','Shared pilot distribution','Fixed protected 24 V pilot terminals',
         'Take the OEM pilot and cabinet from the same F2 rail and return. Verify OEM approval, terminal rating and total load on PS2.'),
        ('XT1','Protected auxiliary AC distribution','Covered distribution terminals',
         'Quote protected distribution to PS2 and the main PCB J1 downstream of QISO1 and F3.'),
        ('PS2','Common 24 V DC supply for cabinet and OEM pilot','HDR-60-24',
         'One isolated supply for the complete DC rail. Verify motor contactor cold pickup and sustained loading.'),
        ('XP10','OEM pickup detector terminals','Shrouded low-voltage terminals',
         'One three-position protected tap. The pilot uses the same fused DC source as the guard.')
    ]:
        by_ref[ref].update({'Item':label,'Specified part or selection':mpn,'Fitting or quote condition':terms})
    fuse={k:'' for k in rows[0]}
    fuse.update({'Schematic refs or field assembly':'F3','Item':'Protected auxiliary AC spur',
                 'Specified part or selection':'AC branch protection matched to fault current, conductors and supply inrush',
                 'Installed quantity':'1','Cost treatment':'Required quote',
                 'Fitting or quote condition':'Include rated protection and enclosure hardware. Check coordination with the original motor branch and board F1.'})
    rows.append(fuse)
    return rows


def main():
    parts = []
    def add(scope, ref, item, mpn, qty, status, source):
        parts.append(dict(scope=scope,reference=ref,item=item,part_or_specification=mpn,
                          quantity_for_one=qty,treatment=status,source=source))
    for board in ('main','panel'):
        for r in read(BOARDS/(board+'-BOM.csv')):
            add(board,r['Designator'],r['Comment'],r['Manufacturer Part Number'],r['Quantity'],
                'Fit during board assembly','../../output/socketed-r4/'+board+'-BOM.csv')
    for r in read(BOARDS/'post-assembly-parts.csv'):
        add('main after soldering',r['Locations'],r['Operation'],r['MPN'],r['Quantity per main board'],
            'Fit once per indicated socket','../../output/socketed-r4/post-assembly-parts.csv')
    field = read(OLD/'field-one-starter.csv')
    for r in field:
        add('field',r['Reference / interface'],r['Part or completed assembly'],r['Exact order breakdown and quantity tier'],
            r['Requirement for one installed starter'],r['Procurement status / price scope'],'../../output/jlc-r4/field-one-starter.csv')
    cab = cabinet()
    for r in cab:
        add('cabinet',r['Schematic refs or field assembly'],r['Item'],r['Specified part or selection'],
            r['Installed quantity'],r['Cost treatment'],'cabinet-purchases.csv')
    # J1 is a schematic boundary to the board connector already counted as main.J1.
    native_refs = {r['Reference'] for r in read(OUT/'bom.csv')}
    listed = {ref for row in cab for ref in row['Schematic refs or field assembly'].split()}
    assert native_refs - listed == {'J1'}
    write(OUT/'parts-one-starter.csv',parts)
    write(OUT/'cabinet-purchases.csv',cab)
    totals = {currency:sum(D(r['Extended price']) for r in cab if r['Cost treatment'].startswith('Counted')
                           and r['Currency']==currency) for currency in ('INR','USD')}
    fx=D('93.3461')
    main=(D('118.1238')-D('1.9546')+D('33.77'))*fx+D('2071.52')+D('188.22')
    panel=(D('6.5362')+D('33.77'))*fx
    field_inr=sum(D(r['Listed line subtotal INR'] or '0') for r in field)
    installed=main+panel+field_inr+totals['INR']+totals['USD']*fx
    sources = read(OLD/'budget-cabinet-one-starter.csv')
    cut = sum(D(r['Extended price']) for r in sources if r['Schematic refs or field assembly'] in ('KV1','KC1'))
    results={'pricing_basis':'Historical reference prices and two-board-per-design assembly setup allocation',
             'reference_INR_per_USD':str(fx)}
    for key,amount in [('main_including_plug_in_relays_INR',main),('five_button_panel_INR',panel),
                       ('field_parts_INR',field_inr),('cabinet_INR',totals['INR']),('cabinet_USD',totals['USD']),
                       ('cabinet_converted_INR',totals['INR']+totals['USD']*fx),
                       ('one_installed_priced_INR',installed),('removed_monitor_pair_INR',cut),
                       ('one_pair_production_only_priced_INR',installed+D('67.54')*fx)]:
        results[key]=str(amount.quantize(D('0.01')))
    (OUT/'costs.json').write_text(json.dumps(results,indent=2)+'\n')
    print(results)


if __name__=='__main__':
    main()
