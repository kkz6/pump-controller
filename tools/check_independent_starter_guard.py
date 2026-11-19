"""Solve the external dry-contact netlist and check its receiver divider corners."""
import csv
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/starter-guard/contacts.csv"
REPORT = ROOT / "hardware/main-compact-dual/checks/independent-starter-guard.json"


def edges():
    circuits = defaultdict(list)
    with SOURCE.open(newline="") as stream:
        for row in csv.DictReader(stream):
            circuits[row["circuit"]].append((row["from"], row["to"], row["conducts_when"]))
    return circuits


def conducts(circuit, start, end, states):
    adjacent = defaultdict(set)
    for left, right, condition in circuit:
        if states[condition]:
            adjacent[left].add(right)
            adjacent[right].add(left)
    queue, seen = [start], {start}
    while queue:
        node = queue.pop()
        if node == end:
            return True
        for other in adjacent[node] - seen:
            seen.add(other)
            queue.append(other)
    return False


def check_native(circuits):
    """Independently resolve every functional contact to its KiCad terminal pair."""
    xml = ET.parse(ROOT / "hardware/starter-guard/checks/guard-netlist.xml")
    pins = {(n.get("ref"), n.get("pin")): net.get("name") for net in xml.findall(".//nets/net")
            for n in net.findall("node") if not net.get("name").startswith("unconnected-")}
    terminals = {
        "SR1_INPUT": {"OEM_STOP_RELEASED":"S3 11 12", "OVERLOAD_HEALTHY":"S4 C NC",
                      "KV_IN_RANGE_NO":"KV1 11 14", "KC_IN_RANGE_NO":"KC1 11 14", "FLOAT_NC":"LS1 COM NC",
                      "H_SEATED":"J3 5 6", "L_RELEASED":"J3 7 8", "HB_WINDOW_1_NO":"WD1 13 14","HB_WINDOW_2_NO":"WD1 19 20",
                      "PANEL_RELAY_NO":"KPS1 33 34", "L_SEATED":"J3 9 10", "H_RELEASED":"J3 11 12"},
        "SR1_RESET":{"RESET_PRESSED":"S1 13 14"},
        "SR2_INPUT":{"SR1_13_14":"SR1 13 14", "SR2_33_34":"SR2 33 34",
                     "KS1_MIRROR_NC":"KS1 21 22", "KS2_MIRROR_NC":"KS2 21 22",
                     "OEM_OFF_PROOF":"KOF1 21 22","OEM_HOLD_RELEASED":"KHL1 61 62",
                     "OEM_COMMAND_PATH_OPEN":"KID1 15 18","OEM_START_RELEASED":"S5 C NC",
                     "H_SEATED":"J3 13 14", "KCA_GUIDED_NC":"KCA1 11 12",
                     "KCB_GUIDED_NC":"KCB1 11 12","L_SEATED":"J3 15 16"},
        "SR2_ENABLE":{"ENABLE_PRESSED":"S2 13 14"},
        "KS1_COIL":{"SR2_13_14":"SR2 13 14"}, "KS2_COIL":{"SR2_23_24":"SR2 23 24"},
        "HOST_FEEDBACK":{"KS1_AUX_NO":"KS1 13 14", "KS2_AUX_NO":"KS2 13 14","H_SEATED":"J3 17 18"},
        "J31":{"KFB_NO":"KFB1 4 8"}, "OEM_FEED":{"KS1_MAIN_NO":"KS1 1L1 2T1","KS2_MAIN_NO":"KS2 1L1 2T1"},
    }
    assert xml.find('.//components/comp[@ref="WD1"]/fields/field[@name="MPN"]').text == "DD2503"
    assert {pin: net for (ref,pin),net in pins.items() if ref == "WD1"} == {
        "1":"CAB_0","2":"HB_24_FUSED","4":"HB_24","13":"HOST_EXCLUSIVE",
        "14":"HB_WINDOW_LINK","19":"HB_WINDOW_LINK","20":"AFTER_HB"}
    assert pins["F1","1"] == "FUSED_24" and pins["F1","2"] == "HB_24_FUSED"
    pilot_pins = {"R40":["PILOT_P","OPT_SENSE_A"],"R41":["OPT_SENSE_K","PILOT_D"],
                  "R42":["PILOT_D","OEM_CTRL_N"],"R43":["ID_TIMER_24","CAB_0"],
                  "J10":["PILOT_P","PILOT_D","OEM_CTRL_N"],
                  "OC3":["OPT_SENSE_A","OPT_SENSE_K","FUSED_24","ID_TIMER_24"],
                  "D8":["OPT_SENSE_A","OPT_SENSE_K"]}
    for ref,nets in pilot_pins.items():
        assert [pins[ref,str(i+1)] for i in range(len(nets))]==nets
    assert pins["KID1","A1"]=="ID_TIMER_24" and pins["KID1","A2"]=="CAB_0"
    assert pins["KHL1","53"]=="PILOT_P" and pins["KHL1","54"]=="PILOT_D"
    count=0
    for circuit, wire_list in circuits.items():
        for left, right, condition in wire_list:
            ref, a, b = terminals[circuit][condition].split()
            expected = (left.replace(".", "_"), right.replace(".", "_"))
            actual = pins[(ref, a)], pins[(ref, b)]
            assert actual == expected, (ref, actual, expected)
            count += 1
    return {"contact_pairs":count, "populated_net_pins":len(pins),
            "components":len(xml.findall(".//components/comp"))}


def input_sweep(circuits):
    count = 0
    for flags in itertools.product((False, True), repeat=10):
        stop, ol, kv, kc, hh, host, local, hb1, hb2, panel = flags
        states = dict(OEM_STOP_RELEASED=stop, OVERLOAD_HEALTHY=ol,
                      KV_IN_RANGE_NO=kv, KC_IN_RANGE_NO=kc, FLOAT_NC=hh,
                      H_SEATED=host, L_SEATED=local, L_RELEASED=not local,
                      H_RELEASED=not host, HB_WINDOW_1_NO=hb1, HB_WINDOW_2_NO=hb2, PANEL_RELAY_NO=panel)
        expected = (all((stop, ol, kv, kc, hh)) and host != local
                    and (local or hb1 and hb2 and panel))
        assert conducts(circuits["SR1_INPUT"], "SR1.S11", "SR1.S12", states) == expected
        count += 1
    return count


def check_sequences(c):
    """Ideal Pilz monitored rising-edge behavior after each input has settled."""
    counts = defaultdict(int)
    for host, fault, weld_a, weld_b, weld_ks1, weld_ks2 in itertools.product(
        (False, True),
        ("OEM_STOP_RELEASED", "OVERLOAD_HEALTHY", "KV_IN_RANGE_NO", "KC_IN_RANGE_NO",
         "FLOAT_NC", "HB_WINDOW_1_NO", "HB_WINDOW_2_NO", "PANEL_RELAY_NO", "CABINET_24", "UNSEAT"),
        (False, True), (False, True), (False, True), (False, True)
    ):
        if weld_ks1 and weld_ks2:
            continue  # a double main-pole weld exceeds the independent interruption design
        if not host and fault in ("HB_WINDOW_1_NO", "HB_WINDOW_2_NO", "PANEL_RELAY_NO"):
            continue  # service LOCAL physically isolates the board
        sr1 = sr2 = prev_sr1 = prev_sr2 = False
        state = {condition: True for wires in c.values() for _, _, condition in wires}
        state.update(H_SEATED=host, H_RELEASED=not host, L_SEATED=not host, L_RELEASED=host,
                     RESET_PRESSED=False, ENABLE_PRESSED=False, CABINET_24=True,
                     SR2_33_34=False)

        def step(reset=False, enable=False):
            nonlocal sr1, sr2, prev_sr1, prev_sr2
            state.update(RESET_PRESSED=reset, ENABLE_PRESSED=enable)
            ok1 = state["CABINET_24"] and conducts(c["SR1_INPUT"], "SR1.S11", "SR1.S12", state)
            request1 = conducts(c["SR1_RESET"], "SR1.S12", "SR1.S34", state)
            sr1 = ok1 and (sr1 or request1 and not prev_sr1)
            prev_sr1 = request1
            state["SR1_13_14"] = sr1
            ok2 = ok1 and conducts(c["SR2_INPUT"], "SR2.S11", "SR2.S12", state)
            request2 = conducts(c["SR2_ENABLE"], "SR2.S12", "SR2.S34", state)
            sr2 = ok2 and (sr2 or request2 and not prev_sr2)
            prev_sr2 = request2
            state.update(SR2_13_14=sr2, SR2_23_24=sr2, SR2_33_34=sr2)
            coil1 = state["CABINET_24"] and conducts(c["KS1_COIL"], "FUSED_24", "KS1.A1", state)
            coil2 = state["CABINET_24"] and conducts(c["KS2_COIL"], "FUSED_24", "KS2.A1", state)
            state["KS1_MAIN_NO"] = coil1 or weld_ks1
            state["KS2_MAIN_NO"] = coil2 or weld_ks2
            state.update(KS1_AUX_NO=coil1, KS2_AUX_NO=coil2)
            state["KFB_NO"] = state["CABINET_24"] and conducts(c["HOST_FEEDBACK"], "FUSED_24", "KFB.A1", state)
            live = conducts(c["OEM_FEED"], "PROTECTED_LINE", "OEM_LINE", state)
            fb = conducts(c["J31"], "J31.1", "J31.2", state)
            return live, fb

        assert step() == (False, False)
        assert step(reset=True) == (False, False)
        assert step() == (False, False)
        assert step(enable=True) == (True, host)
        # Inject a main-pole weld only after energization. Mirrors now report it.
        state.update(KCA_GUIDED_NC=not weld_a, KCB_GUIDED_NC=not weld_b,
                     KS1_MIRROR_NC=not weld_ks1, KS2_MIRROR_NC=not weld_ks2)
        if fault == "UNSEAT":
            state.update(H_SEATED=False, L_SEATED=False, H_RELEASED=True, L_RELEASED=True)
        else:
            state[fault] = False
        assert step() == (False, False)
        # A held reset across recovery cannot cause the SR1 latch to energize.
        assert step(reset=True) == (False, False)
        if fault == "UNSEAT":
            state.update(H_SEATED=host, L_SEATED=not host, H_RELEASED=not host, L_RELEASED=host)
        else:
            state[fault] = True
        assert step(reset=True) == (False, False)
        assert not sr1
        assert step() == (False, False)
        assert step(reset=True) == (False, False)
        assert step() == (False, False)
        # OEM-off proof and fresh local START release are prerequisites for re-energization.
        state["OEM_OFF_PROOF"] = False
        assert step(enable=True) == (False, False)
        assert step() == (False, False)
        state.update(OEM_OFF_PROOF=True, OEM_START_RELEASED=False)
        assert step(enable=True) == (False, False)
        assert step() == (False, False)
        assert step(enable=True) == (False, False)
        state["OEM_START_RELEASED"] = True
        assert step(enable=True) == (False, False)  # proof regained with ENABLE tied down
        assert step() == (False, False)
        expected = not (weld_ks1 or weld_ks2 or host and (weld_a or weld_b))
        assert step(enable=True) == (expected, expected and host)
        counts[fault] += 1
    return dict(sorted(counts.items()))


def check_oem_pickup_proofs(circuits):
    """Field contact consequences at the first enable following a feeder trip."""
    proof = circuits["SR2_INPUT"]
    report = {}
    for mode, fault in itertools.product(("HOST", "LOCAL"),
            ("healthy", "welded_seal_no", "bridged_start_terminals", "lost_monitor_power",
             "open_monitor_output_lead", "open_positive_sense_lead", "open_negative_sense_lead", "retained_electronic_demand")):
        state = {condition: True for wire in circuits.values() for _, _, condition in wire}
        state.update(SR2_33_34=False, SR1_13_14=False, H_SEATED=mode=="HOST",
                     L_SEATED=mode=="LOCAL", OEM_OFF_PROOF=True, OEM_START_RELEASED=True)
        # Both actual pushbuttons are released, the OEM stage is deenergized,
        # and the two guard contactors and both command relays are unwelded.
        # The active monitor is an external field acceptance requirement. Here
        # we model what its specified dry output does, not a tested instrument.
        hold_open = fault not in ("welded_seal_no", "retained_electronic_demand")
        command_open = hold_open and fault != "bridged_start_terminals"
        monitor_ok = fault not in ("lost_monitor_power", "open_monitor_output_lead", "open_positive_sense_lead", "open_negative_sense_lead")
        state.update(OEM_HOLD_RELEASED=hold_open, OEM_COMMAND_PATH_OPEN=command_open and monitor_ok)
        assert not conducts(proof, "SR2.S11", "SR2.S12", state)
        state["SR1_13_14"] = True  # Feeder restored and SR1 reset with guard still open.
        available = conducts(proof, "SR2.S11", "SR2.S12", state)
        state["ENABLE_PRESSED"] = True
        fresh_enable = conducts(circuits["SR2_ENABLE"], "SR2.S12", "SR2.S34", state)
        assert fresh_enable and available == (fault=="healthy")
        if fault == "bridged_start_terminals":
            assert state["OEM_OFF_PROOF"] and state["OEM_START_RELEASED"] and state["OEM_HOLD_RELEASED"]
            # Sensitivity control. A permanently bypassed KID1 would falsely arm here.
            assert conducts(proof, "SR2.S11", "SR2.S12", dict(state, OEM_COMMAND_PATH_OPEN=True))
        if fault == "welded_seal_no":
            assert not conducts(proof, "SR2.S11", "SR2.S12", dict(state, OEM_COMMAND_PATH_OPEN=True))
        report[f"{mode}/{fault}"] = "may accept fresh ENABLE" if available else "blocked"
    return report


def check_pilot():
    """Resistive DC bounds; coil R is a field acceptance limit over temperature."""
    corners = itertools.product((21.6,26.4), (0.,1.5), (0.99,1.01), (0.99,1.01),
                                (0.99,1.01), (70.,150.), (False,True), (None, 1, 2))
    normal_min, normal_max, coil_max, fault_coil_max = 1.,0.,0.,0.
    total = 0
    for supply, vf, s1, s2, sr, coil, kca, short in corners:
        r1 = 0 if short==1 else 1600*s1
        r2 = 0 if short==2 else 1600*s2
        pull = 680*sr
        equivalent = 1/(1/pull+1/coil) if kca else pull
        current = (supply-vf)/(r1+r2+equivalent)
        coil_v = current*equivalent if kca else 0.
        if short is None:
            normal_min=min(normal_min,current)
            normal_max=max(normal_max,current)
            coil_max=max(coil_max,coil_v)
        else:
            fault_coil_max=max(fault_coil_max,coil_v)
        assert coil_v < 2.4 and current < .030
        total += 1
    assert .005 <= normal_min <= normal_max <= .030
    # Upper bound even if the LED forward voltage were zero. The complete
    # closed pickup branch is a 0.0–0.5 ohm shunt directly between P and D.
    # Removing the detector can only increase the computed shunt voltage.
    bridged_max = 0.
    for supply, pull, coil, kca, bridge in itertools.product((21.6,26.4), (673.2,686.8),
                                                              (70.,150.), (False,True), (0.,.5)):
        load = 1/(1/pull+1/coil) if kca else pull
        branch_drop = supply*bridge/(load+bridge)
        led_upper_mA = 1000*branch_drop/(2*1600*.99)
        bridged_max=max(bridged_max,led_upper_mA)
        assert led_upper_mA < .4  # Minimum Panasonic LED turn-off current.
    # If either series sense wire is open there is no LED current path.
    return dict(corners=total,healthy_idle_LED_mA=[round(1000*n,3) for n in (normal_min,normal_max)],
                idle_coil_max_V=round(coil_max,3),one_limit_resistor_short_coil_max_V=round(fault_coil_max,3),
                minimum_drop_out_V=2.4,bridged_START_LED_max_mA=round(bridged_max,3),
                LED_turnoff_min_mA=.4,closed_START_R42_max_mA=round(1000*26.4/(680*.99),3),
                closed_START_R42_max_W=round(26.4**2/(680*.99),3),
                timer_off_1uA_leakage_max_mV=round(1e-3*2200*1.01,3),
                scope="Conventional continuously supplied 21.6–26.4 V DC pilot, coil 70–150 ohm. Bench qualification pending.")


def check_heartbeat_window():
    """Check the specified configuration against the IFM range equations."""
    config=json.loads((SOURCE.parent/"heartbeat-window.json").read_text())
    settings=config["parameters"]
    assert settings["DIM"] == 1 and settings["NC1"] == 1
    results={}
    for outlet in (1,2):
        setting=lambda key: settings[f"{key}{outlet}"]
        assert setting("FO") == 5 and all(setting(k) == 0 for k in ("SO","ST","DT","FT"))
        sp,hys=setting("SP"),setting("HY")/100.
        bounds=[round(sp*(1-hys),3),round(sp*(1+hys),3)]
        assert bounds == config["acceptance_limits_hz"] == [3.,7.]
        results[str(outlet)] = bounds
    decisions={str(f): all(low < f < high for low,high in results.values())
               for f in config["on_bench_test_frequencies_hz"]}
    assert {f for f, valid in decisions.items() if valid} == {"4","5","6"}
    assert config["maximum_monitor_pickup_seconds_after_valid_train_starts"] == 1.0
    assert config["maximum_permitted_trip_seconds_at_load"] == 1.0
    return {"configured_windows_hz":results, "ideal_interior_test_points":decisions,
            "permitted_monitor_pickup_seconds_after_valid_train":config["maximum_monitor_pickup_seconds_after_valid_train_starts"],
            "permitted_end_to_end_trip_seconds":config["maximum_permitted_trip_seconds_at_load"],
            "actual_timing_and_emi_test":"Pending assembled hardware. In-band spurious edges can imitate the heartbeat."}


def check_receiver():
    margins = {}
    for port, high, reference_top in (("HB", 2.4, 115_000), ("PANEL", 4.4, 33_000)):
        high_margin = low_margin = float("inf")
        closed_high = open_low = 0
        for scale in itertools.product((0.99, 1.01), repeat=5):
            main_r, top, bottom, ref_t, ref_b = (
                a*b for a, b in zip(scale, (1_000, 10_000, 10_000, reference_top, 10_000)))
            for rail, diode_v in itertools.product((4.75, 5.25), (0.0, 1.0)):
                vref = rail * ref_b / (ref_t + ref_b)
                gain = bottom / (main_r + top + bottom)
                high_margin = min(high_margin, max(high - diode_v, 0) * gain - vref - .010)
                low_margin = min(low_margin, vref - max(.4 - diode_v, 0) * gain - .010)
                closed_high += 1
                open_low += 1
        assert high_margin > 0 and low_margin > 0
        margins[port] = dict(high_margin_mV=round(high_margin*1000, 1),
                             low_margin_mV=round(low_margin*1000, 1),
                             high_cases=closed_high, low_cases=open_low)
    return margins


if __name__ == "__main__":
    circuit = edges()
    results = {
        "scope": "Ideal external contact connectivity, monitored relay sequences and DC divider calculations",
        "contact_netlist_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "field_schematic":check_native(circuit),
        "input_combinations": input_sweep(circuit),
        "oem_pickup_restoration_cases":check_oem_pickup_proofs(circuit),
        "trip_and_rearm_sequences_by_fault": check_sequences(circuit),
        "receiver_tolerance_corners": check_receiver(),
        "heartbeat_window":check_heartbeat_window(),
        "conventional_24V_pilot":check_pilot(),
        "hardware_evidence": "Pending prototype, original starter accessories, voltage-dip, EMC and measured release tests",
    }
    REPORT.write_text(json.dumps(results, indent=2) + "\n")
    print(REPORT.relative_to(ROOT))
