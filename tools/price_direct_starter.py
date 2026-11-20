"""Price a single direct starter with one main board and one OLED panel on the two-set build basis."""
import csv
from decimal import Decimal as D
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/direct-starter'
OLD = ROOT/'output/jlc-r4'
SOCKETED = ROOT/'output/socketed-r4'


def rows(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    board = rows(OUT/'main-BOM.csv')
    panel = rows(OUT/'panel-BOM.csv')
    def mpns(parts):
        return {r['Manufacturer Part Number'] for r in parts}
    omitted = mpns(rows(SOCKETED/'main-BOM.csv')) - mpns(board) - mpns(panel)
    # Retain the entire old purchase lot for every part that is still fitted.
    # Subtract only lots that disappear completely across the two designs.
    credited = {r['Specified MPN']:D(r['Selected components USD, before assembly and freight'])
                for r in rows(OLD/'factory-parts-pricing.csv')
                if r['Design']=='main' and r['Specified MPN'] in omitted and r['Selected for assembly']=='true'}
    offers = rows(OLD/'board-sourcing-comparison.csv')
    for mpn in omitted - credited.keys():
        prices = [D(r['Total component price for lot']) for r in offers if r['Exact MPN']==mpn and
                  r['Route'].startswith('JLCPCB') and r['Currency']=='USD' and r['Total component price for lot']]
        if prices:
            credited[mpn] = min(prices)
    fx = D('93.3461')
    main_cost = (D('118.1238')-D('1.9546')-sum(credited.values())/2+D('33.77'))*fx+D('2071.52')+D('188.22')
    panel_cost = (D('6.5362')+D('33.77'))*fx
    field = rows(OLD/'field-one-starter.csv')
    field_cost = sum(D(r['Listed line subtotal INR'] or 0) for r in field)
    plugs = next(r for r in rows(OLD/'budget-cabinet-one-starter.csv') if r['Schematic refs or field assembly']=='J30 J35')
    installed = main_cost + panel_cost + field_cost + D(plugs['Extended price'])
    def money(x):
        return str(x.quantize(D('0.01')))
    report = dict(main_INR=money(main_cost),panel_INR=money(panel_cost),field_INR=money(field_cost),
                  two_starter_plugs_INR=plugs['Extended price'],installed_priced_INR=money(installed),
                  single_pair_production_priced_INR=money(installed+D('67.54')*fx),rate_INR_per_USD=str(fx),
                  eliminated_two_main_purchase_lots_USD={k:str(v) for k,v in sorted(credited.items())},
                  unquoted='Radio U3, input connector J1, factory fabrication/placement/through-hole costs, antenna, completed CT and cables, site-specific fitting, optional key or factory-only insert, landed charges.')
    (OUT/'costs.json').write_text(json.dumps(report,indent=2)+'\n')
    # No cabinet purchase lines. J30/J35 are the mated output connectors omitted from the old field kit.
    with (OUT/'parts-one-starter.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n')
        w.writerow(['Where','Reference','Part or assembly','Quantity for one installed set','Treatment'])
        for name,parts in [('Main',board),('Panel',panel)]:
            for r in parts:
                w.writerow([name,r['Designator'],r['Manufacturer Part Number'],r['Quantity'],'Factory mount'])
        for r in rows(SOCKETED/'post-assembly-parts.csv'):
            w.writerow(['Main',r['Locations'],r['MPN'],r['Quantity per main board'],r['Operation']])
        for r in field:
            w.writerow(['Field',r['Reference / interface'],r['Part or completed assembly'],r['Requirement for one installed starter'],r['Procurement status / price scope']])
        w.writerow(['Starter','J30 / J35','Phoenix Contact 1836079 mating plug','2','Both counted for the universal set'])
        w.writerow(['Starter','Interface loom','Terminated starter-specific loom','1','Quote for actual input, pilot rating and routing'])
        w.writerow(['Starter','Factory-only service insert','Keyed passive manual restoration plug','Only for a three-wire starter needing board-independent factory operation without an existing factory transfer','Quote as part of the selected starter loom'])
    print('One installed, priced INR',money(installed))


if __name__=='__main__':
    main()
