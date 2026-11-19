#!/usr/bin/env python3
"""Build the two-set component quantity plan from the assembly BOMs and JLC data."""
import csv
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "output" / "jlc-r4"
BOARDS = ("main", "panel")
SETS = 2
HEADERS = (
    "MPN", "Main designators per board", "Panel designators per board",
    "Main pieces per board", "Panel pieces per board", "Net build / planned pieces for 2 sets",
    "Of net pieces, demand from repeated placements beyond first per set",
    "JLCPCB Part #", "JLC catalog URL", "Catalog checked UTC",
    "JLC catalog unit USD at net quantity", "Net component subtotal USD",
    "JLC public stock (pcs)", "Public stock shortfall vs net (pcs)",
    "Observed supplier preorder MOQ for replenishment (pcs)", "Previous supplier preview lot (pcs)",
    "Indicative preorder unit USD at previous lot", "Sourcing status for net build quantity",
)


def read(filename):
    with (PACKAGE / filename).open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def index(rows, key):
    keyed = {row[key]: row for row in rows}
    if len(keyed) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return keyed


def placements():
    components = defaultdict(lambda: {board: [] for board in BOARDS})
    for board in BOARDS:
        seen = set()
        for entry in read(f"{board}-BOM.csv"):
            refs = [ref.strip() for ref in entry["Designator"].split(",")]
            mpn = entry["Manufacturer Part Number"]
            if not mpn or not all(refs) or len(set(refs)) != int(entry["Quantity"]) or len(set(refs)) != len(refs):
                raise ValueError(f"Invalid BOM line on {board}: {entry}")
            if seen.intersection(refs):
                raise ValueError(f"Duplicate designator on {board}: {refs}")
            seen.update(refs)
            components[mpn][board].extend(refs)
    return components


def price_for_net(tiers, need):
    breaks = sorted((int(min_qty), Decimal(price)) for min_qty, price in
                    (item.strip().split(":") for item in tiers.split("|")))
    if not breaks or breaks[0][0] != 1:
        raise ValueError("No small-quantity catalog price")
    return [price for minimum, price in breaks if minimum <= need][-1]


def board_plan():
    catalog = index(read("jlc-parts-verified.csv"), "Exact catalog MPN")
    preorders = index(read("sourcing-minimums.csv"), "Requested MPN")
    results = []
    totals = Counter()
    for mpn, by_board in sorted(placements().items()):
        positions = sum(len(refs) for refs in by_board.values())
        need = SETS * positions
        repeat = need - SETS
        part = catalog.get(mpn, {})
        preorder = preorders.get(mpn, {})
        if preorder.get("Proposed MPN") != mpn:
            preorder = {}
        minimum = preorder.get("Supplier MOQ (pcs)", "")
        lot = preorder.get("JLC preview lot (pcs)", "")
        preorder_unit = preorder.get("Implied unit USD at shown lot", "")
        code = part.get("JLCPCB Part #", "")
        if part:
            if preorder and preorder["JLCPCB code"] != code:
                raise ValueError(f"Conflicting exact supplier code for {mpn}")
            price = price_for_net(part["Price tiers USD each (min qty:price)"], need)
            cost = price * need
            stock = int(part["Availability"])
            shortage = max(0, need - stock)
            if not shortage:
                status = "Catalog stock covers net build; refresh before purchase"
            elif minimum and int(minimum) > shortage:
                status = "Public stock short; observed replenishment MOQ exceeds deficit"
            elif minimum:
                status = "Public stock short; exact preorder needs supplier confirmation"
            else:
                status = "Public stock short; obtain exact sourcing quote"
            totals["catalog net component subtotal USD"] += cost
            totals["priced distinct MPNs"] += 1
            totals["priced pieces"] += need
            totals["understocked priced MPNs"] += bool(shortage)
            totals["catalog shortfall among priced MPNs"] += shortage
        else:
            price, cost, stock, shortage = "", "", "", ""
            status = "Exact JLC match, price, stock and MOQ pending"
            totals["unpriced distinct MPNs"] += 1
            totals["unpriced pieces"] += need
        totals.update({"distinct populated MPNs": 1, "net pieces for two sets": need,
                       "net pieces from repeated placements": repeat})
        results.append((mpn, ", ".join(by_board["main"]), ", ".join(by_board["panel"]),
                        len(by_board["main"]), len(by_board["panel"]), need, repeat, code,
                        part.get("Catalog URL", ""), part.get("Checked UTC", ""), price, cost,
                        stock, shortage, minimum, lot, preorder_unit, status))
    assert totals["priced pieces"] + totals["unpriced pieces"] == totals["net pieces for two sets"]
    assert SETS * totals["distinct populated MPNs"] + totals["net pieces from repeated placements"] == totals["net pieces for two sets"]
    with (PACKAGE / "component-quantity-plan.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(results)
    return totals


def installation_plan():
    source = read("offboard-parts.csv")
    new_column = "Net requirement across 2 installations; retain scope and conditions"
    scope_column = "Applicability for purchase"
    with (PACKAGE / "offboard-two-installations.csv").open("w", newline="", encoding="utf-8") as output:
        fields = list(source[0])
        fields[4:4] = [new_column, scope_column]
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in source:
            quantity = row["Quantity per complete installation unless stated"]
            selection = row["Selection status"]
            if quantity.startswith("0 or 1"):
                two = "0–2 sets" if quantity.endswith("set") else "0–2"
            elif re.fullmatch(r"[0-9]+", quantity):
                two = str(SETS * int(quantity))
            elif quantity == "5 main + 4 panel":
                two = "10 main + 8 panel"
            elif quantity in {"1 matched assembly", "1 matched set", "1 set", "1 fitted set", "1 existing set", "2 elements"}:
                number, unit = quantity.split(" ", 1)
                two = f"{SETS * int(number)} {unit}"
                if unit == "matched assembly":
                    two = "2 matched assemblies"
                elif unit.endswith("set"):
                    two += "s"
            elif quantity in {"per cabinet", "per layout", "per terminal layout", "per enclosure"}:
                two = "Size for two cabinets from final layout"
            elif quantity == "per bench":
                two = "As required per service bench; shared equipment"
            elif quantity == "per commissioned profile":
                two = "As required for the commissioned electronic host profile"
            else:
                raise ValueError(f"Unclassified off-board quantity: {quantity}")
            if selection.startswith(("Verify installed", "Verify existing", "Reuse after")):
                scope = "Installed requirement; inspect and reuse where suitable"
            elif selection.startswith(("Optional", "Conditional", "Conventional", "Electronic")):
                scope = "Conditional or optional; apply only to selected profile or option"
            elif selection == "Bench equipment":
                scope = "Service bench only"
            else:
                scope = "Installation requirement; follow selection and purchasing notes"
            writer.writerow({**row, new_column: two, scope_column: scope})
    return len(source)


if __name__ == "__main__":
    for name, value in board_plan().items():
        print(f"{name}: {value}")
    print(f"Off-board inventory lines: {installation_plan()}")
