"""Generate the common-supply, socketed 24 V DC reference with onboard AC metering."""
import build_budget_cabinet as budget
from build_starter_guard import part

PROJECT = "starter-metered-r4"
OUT = budget.cad.BASE / "hardware" / PROJECT


def design():
    data = budget.design()
    data.update(project=PROJECT, revision="R4-M", title="Socketed R4 / shared 24 V DC pilot / onboard AC meter")
    sheets = {s["id"]: s for s in data["sheets"]}
    field = sheets["field"]
    field["components"] = [p for p in field["components"] if p["ref"] not in {"KV1", "KC1"}]
    names = {"CAB_SUPPLY_L": "AUX_AC_L", "CAB_SUPPLY_N": "MOTOR_RETURN",
             "OEM_CTRL_L": "FUSED_24", "OEM_CTRL_N": "CAB_0", "ALL_SUPPLIES_OK": "AFTER_OL"}
    for s in data["sheets"]:
        for p in s["components"]:
            for pin in p["pins"]:
                pin["net"] = names.get(pin["net"], pin["net"])
    parts = {p["ref"]: p for s in data["sheets"] for p in s["components"]}
    parts["PS2"]["description"] = "Sole control source. Supplies OEM 24 V DC pilot and cabinet through F2. Check inrush and all fuse and lead ratings."
    parts["XP1"].update(value="OEM pilot distribution", mpn="Fixed protected 24 V pilot terminals",
                        description="Both poles from the cabinet DC rail. No independent OEM supply here.")
    parts["XT1"].update(value="Auxiliary AC distribution", description="Fed from the isolated motor branch via F3. Supplies PS2 and main J1 before the motor contactors.")
    field["components"].extend([
        part("F3", "Auxiliary AC feed protection", "Site-coordinated AC branch protection",
             [(1, "Line from QISO1", "PROTECTED_LINE"), (2, "Auxiliary line", "AUX_AC_L")],
             "Select for available fault current, wire sizes and the combined PS2 and PCB input inrush.", kind="fuse"),
        part("J1", "Socketed main J1 / AC and meter", "Board interface, already fitted",
             [(1, "Main J1 line", "AUX_AC_L"), (2, "Main J1 neutral", "MOTOR_RETURN")],
             "Reference to J1 on the main PCB. The board fuse and voltage divider feed the ADE7953.")
    ])
    field["notes"] = "J1 measures protected incoming AC ahead of the motor contactors. The same branch powers PS2. F2 supplies both the OEM 24 V DC pilot and the guard."
    poles = dict(budget.POLES)
    poles["TRIP"] = "\n".join(line for line in poles["TRIP"].splitlines() if line.split()[:1] not in (["KV1"], ["KC1"]))
    return data, poles


if __name__ == "__main__":
    data, poles = design()
    budget.export(data, OUT, PROJECT, poles)
