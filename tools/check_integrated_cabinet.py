"""Check R4 native main/cabinet interfaces and hardwired trip paths in HOST and LOCAL."""
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import check_independent_starter_guard as guard

ROOT = Path(__file__).resolve().parents[1]
FIELD = ROOT / "hardware/starter-guard-r4"
MAIN = ROOT / "hardware/main-integrated"
CABINET_XML = FIELD / "checks/guard-netlist.xml"
CONTACTS = FIELD / "contacts.csv"
FEEDBACK = ("MAIN_KFB", "STOP_RETURN", "K1_COIL_PLUS")


def terminal_nets(xml):
    return {(n.get("ref"), n.get("pin")): net.get("name")
            for net in ET.parse(xml).findall(".//nets/net") if not net.get("name").startswith("unconnected-")
            for n in net.findall("node")}


def verify_current_exports(main_xml):
    """Reject stale pin-derived evidence even if the tracked sources have just changed."""
    def signature(path):
        xml = ET.parse(path)
        parts = {part.get("ref"): (part.findtext("value"), part.findtext("footprint"),
                                   part.findtext('fields/field[@name="MPN"]'))
                 for part in xml.findall(".//components/comp")}
        return terminal_nets(path), parts
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(ROOT / ".tools/kicad-cli")
    drawings = [
        (FIELD / "starter-guard-r4.kicad_sch", CABINET_XML),
        (MAIN / "pump-controller-integrated.kicad_sch", main_xml),
    ]
    with tempfile.TemporaryDirectory() as temp:
        for source, tracked in drawings:
            fresh = Path(temp) / (source.stem + ".xml")
            subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml", "-o",
                            str(fresh), str(source)], check=True)
            assert signature(fresh) == signature(tracked), f"Stale native netlist for {source.name}"


def interfaces(main_xml):
    cabinet, main = terminal_nets(CABINET_XML), terminal_nets(main_xml)
    def pinmap(pins, ref):
        return {number: net for (part,number),net in pins.items() if part == ref}
    plugs = {"J52": ["GND", "HOST_AUX_N", "LOCAL_AUX_N"],
             "J54": ["FUSED_24", "CAB_0", "HB_24", "PANEL_24", "KFB_A1"]}
    for ref, values in plugs.items():
        want = dict(zip(map(str,range(1,len(values)+1)), values))
        assert pinmap(main, ref) == pinmap(cabinet, ref) == want, ref
    assert [cabinet["XF3",str(p)] for p in range(1,5)] == ["HOST_AUX_N","GND","LOCAL_AUX_N","GND"]
    for plug, relay, command in (("J30","K1","A"),("J35","K2","B")):
        assert pinmap(main, plug) == {"1": f"CTRL_{command}_COM","2": f"CTRL_{command}_NO"}
        assert main[plug,"1"] == main[relay,"2"] and main[plug,"2"] == main[relay,"3"]
        assert pinmap(cabinet, plug) == {"1":"FUSED_24", "2":f"KC{command}_COIL"}
    assert not any(r in {"J31","J36"} for r,p in main)
    assert not any(r in {"KFB1","J31","J36","PS1","D3","D6"} for r,p in cabinet)
    for ref,pin,net in (("KFB1","1","KFB_A1"),("KFB1","16","CAB_0"),("KFB1","4","STOP_RETURN"),
                        ("KFB1","8","K1_COIL_PLUS"),("K1","1","K1_COIL_PLUS"),
                        ("D306","1","KFB_A1"),("D306","2","CAB_0"),
                        ("D303","1","PANEL_24"),("D303","2","CAB_0")):
        assert main[ref,pin] == net, (ref, pin, main[ref,pin], net)
    # These full node sets catch an extra connector pin, pullup, bypass or rail crossing.
    exclusive = {
        "AFTER_USB_A":{"S3.11","SG1.12","XF2.1","XSG1.2"},
        "AFTER_STOP":{"S3.12","S4.C","XF2.2","XF2.3"},
        "ALL_SUPPLIES_OK":{"KC1.14","LS1.COM","XF2.5"},
        "AFTER_HH":{"LS1.NC","XF2.6","XF3.5","XF3.9"},
        "PROTECTED_LINE":{"KS1.1L1","KV1.A1","QISO1.L-OUT","XM1.1"},
        "BETWEEN_KS":{"KS1.2T1","KS2.1L1"}, "OEM_LINE":{"KS2.2T1","XM2.1"},
        "GND":{"J52.1","XF3.2","XF3.4"}, "KFB_A1":{"XF3.18","J54.5"},
        "PILOT_AFTER_STOP":{"S3.OEM-OUT","S4.OEM-IN"},
        "KS1_A1":{"KS1.A1","SR2.14"}, "KS2_A1":{"KS2.A1","SR2.24"},
        "HB_24":{"J54.3","WD1.4"}, "PANEL_24":{"D9.1","J54.4","KPS1.0"},
        "PILOT_P":{"S4.OEM-OUT","S5.OEM-IN","KHL1.53","XP10.1","R40.1","XPF1.F1"},
        "PILOT_D":{"S5.OEM-OUT","KHL1.54","XP10.2","R41.2","R42.1","KOF1.A1","XPF1.F2"},
    }
    for net, expected in exclusive.items():
        actual = {r+"."+p for (r,p),n in cabinet.items() if n == net}
        assert actual == expected, (net, actual ^ expected)
    safety_nets = {"AFTER_HH","ALL_SUPPLIES_OK","AFTER_USB_A","AFTER_STOP","SR1_S11","SR1_S12",
                   "SR2_S11","SR2_S12","BETWEEN_KS","OEM_LINE","PROTECTED_LINE"}
    assert not safety_nets.intersection(main.values())
    return {"matched_cabinet_header_pins": 12, "exclusive_cabinet_nodes": len(exclusive),
            "onboard_privately_wired_feedback": "KFB1.4 STOP_RETURN to KFB1.8 K1_COIL_PLUS",
            "safety_nets_on_main_board": []}


def controller_faults(c):
    modes = ["HOST","LOCAL"]
    conditions = ["MCU frozen with static heartbeat", "false healthy receiver and valid heartbeat",
                  "main board unpowered", "both command contacts welded",
                  "J54.1 shorted to J54.5 with false panel and in-band heartbeat"]
    totals = {}
    def path(group, left, right, state):
        return guard.conducts(c[group], left, right, state)
    for mode, fault, trip, welded in itertools.product(
            modes, conditions, ["original STOP","float high","broken float wire"], ["neither","KS1","KS2"]):
        host = mode == "HOST"
        s = {condition: True for edges in c.values() for _,_,condition in edges}
        s.update(H_SEATED=host,L_RELEASED=host,L_SEATED=not host,H_RELEASED=not host,
                 H_P1=host,H_P2=host,H_P3=host,H_P4=host,L_P34=not host)
        # Start with two accepted guard stages, a running motor and an active OEM seal.
        def feeder():
            sr1 = path("SR1_INPUT","SR1.S11","SR1.S12",s)
            s.update(SR1_13_14=sr1, SR1_23_24=sr1)
            sr2 = all(guard.stage2_continuity(c,s))
            s.update(SR2_13_14=sr2,SR2_23_24=sr2)
            k1 = path("KS1_COIL","FUSED_24","KS1.A1",s)
            k2 = path("KS2_COIL","FUSED_24","KS2.A1",s)
            s.update(KS1_MAIN_NO=k1 or welded=="KS1",KS2_MAIN_NO=k2 or welded=="KS2")
            return path("OEM_FEED","BRANCH_LINE","OEM_LINE",s)
        assert feeder()
        feedback_shorted = fault.startswith("J54.1")
        heartbeat_ok = fault not in ("main board unpowered", "MCU frozen with static heartbeat")
        s.update(HB_WINDOW_1_NO=heartbeat_ok, HB_WINDOW_2_NO=heartbeat_ok,
                 PANEL_RELAY_NO=fault != "main board unpowered",
                 KCA_NO=fault != "main board unpowered", KCB_NO=fault=="both command contacts welded" or feedback_shorted)
        assert feeder() == (not host or heartbeat_ok)
        if trip == "original STOP":
            s["OEM_STOP_RELEASED"] = False
            assert not path("PILOT_SUPPLY","OEM_CTRL_L","PILOT_P",s)
            assert path("PILOT_PICKUP","PILOT_P","PILOT_D",s)  # Even if a pickup path remains closed.
            assert path("PILOT_RETURN","PILOT_COIL_RETURN","OEM_CTRL_N",s) == (not host or fault != "main board unpowered")
        else:
            s["FLOAT_NC"] = False
        assert not feeder(), (mode,fault,trip,welded)
        # Direct fused 24 V on J54.5 energizes KFB1 irrespective of the KS auxiliaries
        # or transfer pole. Keep both command NOs closed above and verify the independent
        # motor feeder has dropped even with the real onboard feedback path conducting.
        s["KFB_NO"] = feedback_shorted
        assert path(*FEEDBACK, s) == feedback_shorted
        assert not path("KS1_COIL","FUSED_24","KS1.A1",s) and not path("KS2_COIL","FUSED_24","KS2.A1",s)
        totals[mode] = totals.get(mode,0)+1

    s = {cond: True for group in c.values() for _,_,cond in group}
    s.update(H_SEATED=False,L_RELEASED=False,L_SEATED=True,H_RELEASED=True)
    for failing_contact in ("OEM_STOP_RELEASED","FLOAT_NC"):
        faulted = dict(s,**{failing_contact:False, "SHUNT":True})
        pairs = [(a,b) for a,b,k in c["SR1_INPUT"] if k == failing_contact]
        assert len(pairs)==1
        a,b = pairs[0]
        assert not path("SR1_INPUT","SR1.S11","SR1.S12",faulted)
        assert guard.conducts(c["SR1_INPUT"]+[(a,b,"SHUNT")],"SR1.S11","SR1.S12",faulted)
    assert path("OEM_FEED","BRANCH_LINE","OEM_LINE",dict(s,KS1_MAIN_NO=True,KS2_MAIN_NO=True))
    return {"fault_demand_and_single_power_contactor_weld_cases":totals,
            "injections":conditions, "negative_controls":["shorted single float remains healthy to SR1",
            "shorted auxiliary STOP alone hides that contact from SR1", "two welded series power contacts conduct"],
            "scope":"Settled ideal contacts with cabinet wiring per the native schematic. Timing, float motion and relay mechanics require hardware proof."}


def main():
    main_xml = MAIN / "checks/source.xml"
    verify_current_exports(main_xml)
    c=guard.edges(CONTACTS)
    inputs = [*MAIN.glob("*.kicad_sch"), *FIELD.glob("*.kicad_sch"), CONTACTS, CABINET_XML,
              main_xml, ROOT/"tools/check_integrated_cabinet.py",
              ROOT/"tools/check_independent_starter_guard.py", ROOT/"tools/build_integrated_cabinet.py",
              ROOT/"tools/build_starter_guard.py", ROOT/"hardware/starter-guard/heartbeat-window.json"]
    results={
        "source_sha256":{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(inputs)},
        "native_contact_pairs":guard.check_native(c,CABINET_XML,main_xml),
        "interfaces":interfaces(main_xml),
        "independent_stop_and_float":controller_faults(c),
        "input_combinations":guard.input_sweep(c),
        "cascade_faults":guard.check_cascade_faults(c),
        "sequences":guard.check_sequences(c,FEEDBACK),
        "oem_pickup_proofs":guard.check_oem_pickup_proofs(c),
        "usb_trapped_key":guard.check_trapped_key(c),
        "dead_usb_cable_supply_restorations":guard.check_dead_cable_restoration(c),
        "cabinet_monitor_configuration":guard.check_heartbeat_window(),
        "pilot_dc_corners":guard.check_pilot(),
        "release_status":"Engineering prototype. Cabinet build, cabinet and starter compatibility, insulation, EMC, end-to-end trip time and pump stopping distance remain unverified.",
    }
    (FIELD/"checks/faults.json").write_text(json.dumps(results,indent=2)+"\n")
    print("R4 cabinet and main interfaces, hardwired trips and restoration tests passed.")


if __name__ == "__main__":
    main()
