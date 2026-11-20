"""Check the R4 probe-only cabinet against its native KiCad netlist and the released R4 guard."""

import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import build_probe_cabinet as build
import check_integrated_cabinet as integrated
import check_independent_starter_guard as guard

OUT = build.OUT
ROOT = integrated.ROOT
XML = OUT / "checks/guard-netlist.xml"
MAIN_XML = integrated.MAIN / "checks/source.xml"


def components(path):
    return {part.get("ref"): (part.findtext("value"), part.findtext("footprint"),
                              part.findtext('fields/field[@name="MPN"]'))
            for part in ET.parse(path).findall(".//components/comp")}


def verify_native():
    integrated.verify_current_exports(MAIN_XML)
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(ROOT / ".tools/kicad-cli")
    with tempfile.TemporaryDirectory() as temporary:
        fresh = Path(temporary) / "guard.xml"
        subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml", "-o",
                        str(fresh), str(OUT / (build.PROJECT + ".kicad_sch"))], check=True)
        assert integrated.terminal_nets(fresh) == integrated.terminal_nets(XML)
        assert components(fresh) == components(XML)
    expected = integrated.terminal_nets(integrated.CABINET_XML)
    for pin, net in {("LS1", "COM"): "ALL_SUPPLIES_OK", ("LS1", "NC"): "AFTER_HH",
                     ("XF2", "5"): "ALL_SUPPLIES_OK", ("XF2", "6"): "AFTER_HH"}.items():
        assert expected.pop(pin) == net
    for pin in ("5", "9"):
        assert expected["XF3", pin] == "AFTER_HH"
        expected["XF3", pin] = "ALL_SUPPLIES_OK"
    assert integrated.terminal_nets(XML) == expected
    old_parts, new_parts = components(integrated.CABINET_XML), components(XML)
    old_parts.pop("LS1")
    old_value, footprint, mpn = old_parts["XF2"]
    assert old_value == "OEM and float contacts"
    old_parts["XF2"] = ("OEM auxiliary contacts", footprint, mpn)
    assert new_parts == old_parts
    # ERC and the explicit no-connect markers distinguish spare cavities from a jumper.
    raw = ET.parse(XML)
    for pin in ("5", "6"):
        assert any(net.get("name").startswith("unconnected-") and
                   net.find(f'node[@ref="XF2"][@pin="{pin}"]') is not None
                   for net in raw.findall(".//nets/net"))
    assert not any(sheet["violations"] for sheet in json.loads((OUT / "checks/erc.json").read_text())["sheets"])


def verify_contacts(c, old):
    assert set(c) == set(old)
    for name in c.keys() - {"SR1_INPUT"}:
        assert c[name] == old[name], name
    after_merge = [(a if a != "AFTER_HH" else "ALL_SUPPLIES_OK", b, cond)
                   for a, b, cond in old["SR1_INPUT"] if cond != "FLOAT_NC"]
    assert c["SR1_INPUT"] == after_merge
    # Independently actuate every pole, including incompatible or failed transfer indications.
    keys = [cond for _, _, cond in c["SR1_INPUT"]]
    required = {"USB_COVER_A", "OEM_STOP_RELEASED", "OVERLOAD_HEALTHY", "KV_IN_RANGE_NO",
                "KC_IN_RANGE_NO", "H_SEATED", "L_RELEASED", "HB_WINDOW_1_NO", "HB_WINDOW_2_NO",
                "PANEL_RELAY_NO", "L_SEATED", "H_RELEASED"}
    assert set(keys) == required and len(keys) == len(required)
    for bits in itertools.product((False, True), repeat=len(keys)):
        state = dict(zip(keys, bits))
        common = all(state[k] for k in ("USB_COVER_A", "OEM_STOP_RELEASED", "OVERLOAD_HEALTHY",
                                         "KV_IN_RANGE_NO", "KC_IN_RANGE_NO"))
        host = all(state[k] for k in ("H_SEATED", "L_RELEASED", "HB_WINDOW_1_NO",
                                      "HB_WINDOW_2_NO", "PANEL_RELAY_NO"))
        local = state["L_SEATED"] and state["H_RELEASED"]
        ok = guard.conducts(c["SR1_INPUT"], "SR1.S11", "SR1.S12", state)
        assert ok == (common and (host or local))
        assert ok == guard.conducts(old["SR1_INPUT"], "SR1.S11", "SR1.S12", dict(state, FLOAT_NC=True))
    return 2 ** len(keys)


def check_stop_and_overload(c):
    faults = ("normal", "missing heartbeat", "main unpowered", "both commands welded",
              "false healthy signals and shorted feedback")
    trips = ("factory STOP", "factory overload", "open STOP auxiliary lead", "open overload auxiliary lead")
    counts = {"HOST": 0, "LOCAL": 0}
    def path(name, left, right, s):
        return guard.conducts(c[name], left, right, s)

    for mode, fault, trip, weld in itertools.product(counts, faults, trips, ("neither", "KS1", "KS2")):
        host = mode == "HOST"
        s = {cond: True for edges in c.values() for _, _, cond in edges}
        s.update(H_SEATED=host, L_RELEASED=host, L_SEATED=not host, H_RELEASED=not host,
                 H_P1=host, H_P2=host, H_P3=host, H_P4=host, L_P34=not host)
        def feeder():
            sr1 = path("SR1_INPUT", "SR1.S11", "SR1.S12", s)
            s.update(SR1_13_14=sr1, SR1_23_24=sr1)
            sr2 = all(guard.stage2_continuity(c, s))
            s.update(SR2_13_14=sr2, SR2_23_24=sr2)
            ks1 = path("KS1_COIL", "FUSED_24", "KS1.A1", s)
            ks2 = path("KS2_COIL", "FUSED_24", "KS2.A1", s)
            s.update(KS1_MAIN_NO=ks1 or weld == "KS1", KS2_MAIN_NO=ks2 or weld == "KS2")
            return path("OEM_FEED", "BRANCH_LINE", "OEM_LINE", s), ks1, ks2
        assert feeder() == (True, True, True)
        hb = fault not in ("missing heartbeat", "main unpowered")
        s.update(HB_WINDOW_1_NO=hb, HB_WINDOW_2_NO=hb, PANEL_RELAY_NO=fault != "main unpowered",
                 KCA_NO=fault != "main unpowered", KCB_NO=fault in ("both commands welded", "false healthy signals and shorted feedback"),
                 KFB_NO=fault == "false healthy signals and shorted feedback")
        assert feeder()[0] == (not host or hb)
        condition = "OEM_STOP_RELEASED" if "STOP" in trip else "OVERLOAD_HEALTHY"
        # An auxiliary lead breaks only the guard circuit. The factory pilot can still be live.
        pilot = dict(s)
        if trip.startswith("factory"):
            pilot[condition] = False
        assert path("PILOT_SUPPLY", "OEM_CTRL_L", "PILOT_P", pilot) == trip.startswith("open")
        assert path("PILOT_PICKUP", "PILOT_P", "PILOT_D", s)  # OEM holding contact retained
        s[condition] = False
        assert feeder() == (False, False, False), (mode, fault, trip, weld)
        assert path(*integrated.FEEDBACK, s) == (fault == "false healthy signals and shorted feedback")
        counts[mode] += 1
    return counts


def check_restart_inputs(c):
    """Exercise the actual profile paths into each monitored rising-edge stage after a trip."""
    results = {"HOST": 0, "LOCAL": 0}
    for mode, demand, held_reset, held_enable, retained in itertools.product(
            results, ("OEM_STOP_RELEASED", "OVERLOAD_HEALTHY"), (False, True), (False, True),
            ("none", "KS1_MIRROR_NC", "KS2_MIRROR_NC", "OEM_OFF_PROOF", "OEM_HOLD_RELEASED",
             "OEM_COMMAND_PATH_OPEN", "OEM_START_RELEASED", "KCA_GUIDED_NC", "KCB_GUIDED_NC")):
        host = mode == "HOST"
        s = {cond: True for edges in c.values() for _, _, cond in edges}
        s.update(H_SEATED=host, H_RELEASED=not host, L_SEATED=not host, L_RELEASED=host)
        sr1 = sr2 = True
        prev_ok1 = prev_ok2 = True
        prev_reset = prev_enable = False

        def tick(reset, enable):
            nonlocal sr1, sr2, prev_ok1, prev_ok2, prev_reset, prev_enable
            s.update(RESET_PRESSED=reset, ENABLE_PRESSED=enable)
            ok1 = guard.conducts(c["SR1_INPUT"], "SR1.S11", "SR1.S12", s)
            request = guard.conducts(c["SR1_RESET"], "SR1.S12", "SR1.S34", s)
            sr1 = ok1 and (sr1 or (prev_ok1 and request and not prev_reset))
            prev_ok1, prev_reset = ok1, request
            s.update(SR1_13_14=sr1, SR1_23_24=sr1, SR2_33_34=sr2)
            ok2 = all(guard.stage2_continuity(c, s))
            request = guard.conducts(c["SR2_ENABLE"], "SR2.S12", "SR2.S34", s)
            sr2 = ok2 and (sr2 or (prev_ok2 and request and not prev_enable))
            prev_ok2, prev_enable = ok2, request
            return sr1, sr2

        s[demand] = False
        assert tick(held_reset, held_enable) == (False, False)
        s[demand] = True
        if retained != "none":
            s[retained] = False
        assert tick(held_reset, held_enable) == (False, False)
        assert tick(False, False) == (False, False)
        assert tick(True, True) == (True, False)
        assert tick(False, True) == (True, False)
        assert tick(False, False) == (True, False)
        expect_enable = retained == "none" or (not host and retained in ("KCA_GUIDED_NC", "KCB_GUIDED_NC"))
        assert tick(False, True) == (True, expect_enable)
        results[mode] += 1
    return results


def main():
    verify_native()
    c = guard.edges(OUT / "contacts.csv")
    old = guard.edges(integrated.CONTACTS)
    combinations = verify_contacts(c, old)
    # After proving identical SR1 truth tables for every pole vector and identical
    # remaining circuits, R4's sequencer receives identical inputs at every step
    # with LS1 closed. Run its original transition tests and report only applicable trips.
    sequences = guard.check_sequences(old, integrated.FEEDBACK)
    sequences.pop("FLOAT_NC")
    cascade = guard.check_cascade_faults(old)
    cascade["single_bridge_or_gate_contact_cases_by_demand"].pop("FLOAT_NC")
    result = {
        "profile": build.PROJECT,
        "native_contact_pairs": guard.check_native(c, XML, MAIN_XML),
        "R4_reference_interfaces_before_verified_pin_delta": integrated.interfaces(MAIN_XML),
        "all_independent_SR1_contact_vectors": combinations,
        "direct_stop_and_overload_feeder_cases_by_mode": check_stop_and_overload(c),
        "direct_restart_and_retained_proof_cases_by_mode": check_restart_inputs(c),
        "restart_sequence_cases_by_demand_from_equivalent_R4_state_machine": sequences,
        "cascade_results_for_retained_demands_from_equivalent_R4_state_machine": cascade,
        "oem_rearm_proofs": guard.check_oem_pickup_proofs(c),
        "usb_trapped_key": guard.check_trapped_key(c),
        "supply_restorations_with_dead_usb_cable": guard.check_dead_cable_restoration(c),
        "heartbeat_reference_configuration": guard.check_heartbeat_window(),
        "conventional_pilot_corners": guard.check_pilot(),
        "limits": "No independent water-level trip. Ideal settled contacts. Installed starter, firmware, open/short electrode faults, DC protection, EMC and measured motor stopping remain unverified.",
    }
    sources = {*OUT.glob("*.kicad_sch"), OUT/"contacts.csv", XML, OUT/"checks/erc.json",
               build.original.OUT/"contacts.csv", integrated.CABINET_XML, MAIN_XML,
               ROOT/"hardware/starter-guard/heartbeat-window.json"}
    sources.update(Path(module.__file__).resolve() for module in (build, build.cad, build.original,
                                                                  build.original.field, integrated, guard))
    sources.add(Path(__file__).resolve())
    result["sha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}
    (OUT/"checks/faults.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"{combinations} independent contact vectors matched, checks passed for {build.PROJECT}.")


if __name__ == "__main__":
    main()
