"""Evaluate the budget cabinet using its KiCad terminal nets and physical contact pairs."""

import csv
import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from check_independent_starter_guard import check_pilot
from check_integrated_cabinet import MAIN, ROOT, terminal_nets

REFERENCE = ROOT / "hardware/starter-guard-r4-probes/checks/guard-netlist.xml"

FIELD = ROOT / "hardware/starter-budget-r4"
CHECKS = FIELD / "checks"
MAIN_XML = MAIN / "checks/source.xml"

# Physical terminal numbers, derived from the functions of the installed devices.
# A switch can connect either way. One network includes every parallel return,
# feedback and holding path regardless of the group used on a drawing.
POLES = {
    "cover_a": "SG1 11 12", "cover_b": "SG1 21 22",
    "stop_aux": "S3 11 12", "stop_pilot": "S3 OEM-IN OEM-OUT",
    "ol_aux": "S4 C NC", "ol_pilot": "S4 OEM-IN OEM-OUT",
    "branch_ok": "KV1 11 14", "pilot_ok": "KC1 11 14",
    "panel_ok": "KPS1 33 34", "host_trip": "XF3 5 6", "local_released": "XF3 7 8",
    "local_trip": "XF3 9 10", "host_released": "XF3 11 12",
    "host_idle": "XF3 13 14", "local_idle": "XF3 15 16",
    "host_fb": "XF3 17 18", "host_logic": "XF3 1 2", "local_logic": "XF3 3 4",
    "ks1_released": "KS1 21 22", "ks2_released": "KS2 21 22",
    "oem_released": "KOF1 21 22", "seal_released": "KHL1 61 62", "start_released": "S5 C NC",
    "ka_released": "KCA1 11 12", "kb_released": "KCB1 11 12",
    "photo": "OC3 3 4", "timer": "KID1 15 18",
    "reset_nc": "S1 21 22", "reset_no": "S1 13 14",
    "ready_memory": "KREADY1 33 34", "ready_press": "KREADY1 43 44",
    "trip_gate": "KH1 13 14", "pilot_gate": "KO1 13 14", "timer_sink": "KT1 12 9",
    "enable_memory": "KEN1 33 34", "enable_output": "KEN1 43 44",
    "ks1_fb": "KS1 13 14", "ks2_fb": "KS2 13 14",
    "ka_board": "J30 1 2", "kb_board": "J35 1 2",
    "ka_pilot": "KCA1 33 34", "kb_pilot": "KCB1 33 34",
    "host_p1": "XPF1 H1 F1", "host_p2": "XPF1 H2 F2",
    "host_p3": "XPF1 H3 F3", "host_p4": "XPF1 H4 F4", "local_p": "XPF1 L3 L4",
    "start_no": "S5 OEM-IN OEM-OUT", "seal_no": "KHL1 53 54",
    "iso_l": "QISO1 L-IN L-OUT", "iso_n": "QISO1 N-IN N-OUT",
    "ks1_main": "KS1 1L1 2T1", "ks2_main": "KS2 1L1 2T1", "oem_main": "KOF1 1L1 2T1",
}

def parts(xml):
    result = ET.parse(xml)
    return {part.get("ref"): part.findtext('fields/field[@name="MPN"]')
            for part in result.findall(".//components/comp")}

def check_export(source, tracked, cli, tmp):
    fresh = tmp / (source.stem + ".xml")
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml",
                    "-o", str(fresh), str(source)], check=True)
    assert terminal_nets(fresh) == terminal_nets(tracked) and parts(fresh) == parts(tracked)

def native_checks(xml):
    cli = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or str(ROOT / ".tools/kicad-cli")
    drawing = FIELD / (FIELD.name + ".kicad_sch")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        check_export(drawing, xml, cli, tmp)
        check_export(MAIN / "pump-controller-integrated.kicad_sch", MAIN_XML, cli, tmp)
        report = tmp / "erc.json"
        subprocess.run([cli,"sch","erc","--format","json","--severity-all","--exit-code-violations",
                        "-o",str(report),str(drawing)], check=True)
        assert not any(s["violations"] for s in json.loads(report.read_text())["sheets"])
    main, pins = terminal_nets(MAIN_XML), terminal_nets(xml)
    cabinet_parts = parts(xml)
    assert not {"SR1", "SR2", "WD1", "LS1"}.intersection(cabinet_parts)
    assert not any("750104" in str(value) or "DD2503" in str(value) for value in cabinet_parts.values())
    assert (pins["KOF1","A1"],pins["KOF1","A2"]) == ("OEM_COIL_PLUS","PILOT_COIL_RETURN")
    for n, label in enumerate(("FUSED_24","CAB_0","HB_24","PANEL_24","KFB_A1"), 1):
        assert main["J54",str(n)] == label
        if n != 3:
            assert pins["J54",str(n)] == label
        else:
            assert ("J54","3") not in pins
    for n, label in enumerate(("GND","HOST_AUX_N","LOCAL_AUX_N"), 1):
        assert main["J52",str(n)] == pins["J52",str(n)] == label
    for plug, relay, coil in (("J30","K1","KCA1"),("J35","K2","KCB1")):
        assert main[plug,"1"] == main[relay,"2"] and main[plug,"2"] == main[relay,"3"]
        assert pins[plug,"1"] == "FUSED_24" and pins[plug,"2"] == pins[coil,"0"]
    assert main["J54","5"] == main["KFB1","1"] and main["KFB1","16"] == "CAB_0"
    assert main["KFB1","4"] == "STOP_RETURN" and main["KFB1","8"] == main["K1","1"]
    # Differential open-command proof and continuously connected pull-downs
    # in the same conventional 24 V DC pilot network as the verified reference.
    for ref, nets in {"R40":("PILOT_P","OPT_SENSE_A"),"R41":("OPT_SENSE_K","PILOT_D"),
                      "R42":("PILOT_D","OEM_CTRL_N"),"R43":("ID_TIMER_24","CAB_0"),
                      "D8":("OPT_SENSE_A","OPT_SENSE_K"),"OC3":("OPT_SENSE_A","OPT_SENSE_K")}.items():
        assert tuple(pins[ref,str(i)] for i in (1,2)) == nets
    # Check every physical terminal feeding a boundary observation used by the model:
    # the monitored supplies, the panel relay, motor interface and pilot bleed/proof parts.
    monitors = {"KV1":("PROTECTED_LINE","MOTOR_RETURN"),"KC1":("OEM_CTRL_L","OEM_CTRL_N"),
                "KID1":("ID_TIMER_24","CAB_0")}
    for ref, nets in monitors.items():
        assert (pins[ref,"A1"],pins[ref,"A2"]) == nets
    assert (pins["KPS1","0"],pins["KPS1","1"]) == (pins["J54","4"],"CAB_0")
    assert (pins["XO1","1"],pins["XO1","2"]) == ("OEM_SWITCHED_LINE","MOTOR_RETURN")
    for diode, coil in (("D4","KCA1"),("D5","KCB1"),("D9","KPS1"),("D10","KREADY1"),("D11","KEN1")):
        assert (pins[diode,"1"],pins[diode,"2"]) == (pins[coil,"0"],pins[coil,"1"])
    assert (pins["D14","1"],pins["D14","2"]) == (pins["KOF1","A1"],pins["KOF1","A2"])
    assert (pins["D15","1"],pins["D15","2"]) == (pins["KS1","A1"],pins["KS1","A2"])
    assert (pins["KS1","A1"],pins["KS1","A2"]) == (pins["KS2","A1"],pins["KS2","A2"])
    assert all(cabinet_parts[r] == cabinet_parts["KH1"] for r in ("KH1","KO1"))
    assert "G3RV-ST500-D-H" in cabinet_parts["KH1"] and "DC24" in cabinet_parts["KH1"]
    assert cabinet_parts["KT1"] == "Autonics CT6S-1P2"
    installed_kt={n:v for (r,n),v in pins.items() if r=="KT1"}
    assert installed_kt=={"4":"CAB_0","5":"FUSED_24","6":"TRIP_RAW","9":"CAB_0","12":"GATE_SINK"}
    assert (pins["KH1","A1"],pins["KH1","A2"]) == ("TRIP_RAW","GATE_SINK")
    assert (pins["KO1","A1"],pins["KO1","A2"]) == (pins["KS1","A1"],"CAB_0")
    for ref,pair in {"R44":("TRIP_RAW","CAB_0"),"R45":("TRIP_OK","CAB_0"),
                     "R46":("TRIP_RAW","GATE_SINK")}.items():
        assert (pins[ref,"1"],pins[ref,"2"]) == pair
    assert pins["KT1","6"]==pins["KH1","13"] and pins["KO1","14"]==pins["KOF1","A1"]
    assert pins["F2","2"] == pins["J54","1"] and pins["PS2","+V"] == pins["F2","1"]
    assert pins["PS2","-V"] == pins["J54","2"]
    baseline=parts(REFERENCE)
    for ref in ("OC3","D8","R40","R41","R42","R43","KV1","KC1","KID1"):
        assert cabinet_parts[ref] == baseline[ref] and cabinet_parts[ref]
    return pins

@dataclass(frozen=True)
class Controls:
    mode: str = "HOST"
    cabinet: bool = True
    pilot: bool = True
    branch: bool = True
    board: bool = True
    isolator: bool = True
    cover: bool = True
    stop: bool = False
    overload: bool = False
    start: bool = False
    reset: str = "released"  # released, travel (both poles open), pressed
    request_a: bool = False
    request_b: bool = False
    weld_a: bool = False
    weld_b: bool = False
    weld_power: str = ""
    weld_seal: bool = False
    timer_out: bool = True  # independent KT1 output after continuous trip clearance
    defect: str = ""  # Bridge or break only in designated sensitivity tests

@dataclass(frozen=True)
class Relays:
    ka: bool = False
    kb: bool = False
    ready: bool = False
    enable: bool = False  # mechanical KEN1 auxiliary relay
    ks1: bool = False
    ks2: bool = False
    oem: bool = False

class Circuit:
    def __init__(self, pins, field=FIELD, shared_supply=False):
        self.shared_supply = shared_supply
        self.pins = pins
        self.edges = {}
        for name, data in POLES.items():
            if shared_supply and name in ("branch_ok", "pilot_ok"):
                continue
            ref, a, b = data.split()
            self.edges[name] = (pins[ref,a],pins[ref,b])
            assert self.edges[name][0] != self.edges[name][1], name
        # Each declared drawing contact must refer to a checked physical pole.
        with (field / "contacts.csv").open(newline="") as source:
            rows = list(csv.DictReader(source))
        checked = {tuple(s.split()) for s in POLES.values()}
        for row in rows:
            physical = (row["ref"],row["pin_a"],row["pin_b"])
            if physical == ("D12","2","1"):
                assert (pins["D12","2"],pins["D12","1"]) == (row["from"],row["to"]) == ("RESET_PICKUP","ENABLE_COIL")
                continue
            reverse = (physical[0],physical[2],physical[1])
            if physical not in checked and reverse not in checked:
                raise AssertionError(("missing physical pole in checker",physical))
            actual = (pins[physical[0],physical[1]], pins[physical[0],physical[2]])
            assert set(actual) == {row["from"],row["to"]}, (physical,actual,row)
        self.contact_rows = len(rows)

    @lru_cache(maxsize=8192)
    def connected(self, active):
        parent = {}
        def root(n):
            while n in parent:
                n = parent[n]
            return n
        directed = [("RESET_PICKUP","ENABLE_COIL")]
        for label in active:
            if label in ("trip_gate","pilot_gate","timer_sink"):
                directed.append(self.edges[label])
                continue
            a,b = (root(n) for n in self.edges[label])
            if a != b:
                parent[b] = a
        groups={n:root(n) for n in self.pins.values()}
        forward={(groups[a],groups[b]) for a,b in directed}
        while True:
            reach=forward|{(a,d) for a,b in forward for c,d in forward if b==c}
            if reach==forward: break
            forward=reach
        return groups,forward

    def evaluate(self, c, r, timer):
        if self.shared_supply:
            # Settled supplies only. Pilot lead failure can interrupt just the OEM coil.
            dc = c.cabinet and c.branch and c.isolator
            c = replace(c, cabinet=dc, pilot=dc and c.pilot)
        pilot_plus = self.pins["S3","OEM-IN"]
        pilot_return = self.pins["XP1","2"]
        host, local = c.mode == "HOST", c.mode == "LOCAL"
        ks1_contact = r.ks1 or c.weld_power == "KS1"
        ks2_contact = r.ks2 or c.weld_power == "KS2"
        seal = r.oem or c.weld_seal
        state = dict(cover_a=c.cover or c.defect=="shutterA", cover_b=c.cover or c.defect=="shutterB",
            stop_aux=not c.stop and c.defect!="stop_lead", stop_pilot=not c.stop,
            ol_aux=not c.overload and c.defect!="overload_lead", ol_pilot=not c.overload,
            branch_ok=c.branch and c.isolator, pilot_ok=c.pilot, panel_ok=c.board and c.cabinet,
            host_trip=host,local_released=not local,local_trip=local,host_released=not host,
            host_idle=host,local_idle=local,host_fb=host,host_logic=host,local_logic=local,
            ks1_released=not ks1_contact,ks2_released=not ks2_contact,
            oem_released=not r.oem,seal_released=not seal,start_released=not c.start,
            ka_released=not r.ka,kb_released=not r.kb,
            reset_nc=c.reset=="released",reset_no=c.reset=="pressed",
            ready_memory=r.ready,ready_press=r.ready,
            trip_gate=c.defect=="trip_gate_short", pilot_gate=c.defect=="pilot_gate_short",
            timer_sink=c.cabinet and (c.timer_out or c.defect=="holdoff_bypass"),
            enable_memory=r.enable or c.defect=="enable_seal",enable_output=r.enable or c.defect=="enable_output",
            ks1_fb=r.ks1,ks2_fb=r.ks2,ka_pilot=r.ka,kb_pilot=r.kb,
            host_p1=host,host_p2=host,host_p3=host,host_p4=host,local_p=local,
            start_no=c.start,seal_no=seal,iso_l=c.isolator,iso_n=c.isolator,
            ks1_main=ks1_contact,ks2_main=ks2_contact,oem_main=r.oem,
            photo=False,timer=timer,ka_board=c.weld_a,kb_board=c.weld_b or (c.board and c.request_b))
        def network():
            return self.connected(tuple(k for k in self.edges if state[k]))
        nets = network()
        def linked(a,b):
            roots,arcs=nets
            return roots[a] == roots[b] or (roots[a],roots[b]) in arcs
        # KH1 is powered by raw trip clearance with a separately supplied
        # timer sink. KO1 follows the actual KS coil feed behind KH1 and KEN.
        # Resolve one stage at a time from actual returned current paths.
        def coil(ref, plus, minus):
            return c.cabinet and linked("FUSED_24",self.pins[ref,plus]) and linked(self.pins[ref,minus],"CAB_0")
        state["trip_gate"] |= coil("KH1","A1","A2")
        nets=network()
        state["pilot_gate"] |= coil("KO1","A1","A2")
        nets=network()
        feedback = c.cabinet and linked("FUSED_24", self.pins["J54","5"])
        # Main K1's coil is gated by KFB1. K1/K2 dry contacts can weld
        # independently of either coil command and independently of the main supply.
        state["ka_board"] |= c.board and c.request_a and feedback
        state["photo"] = c.pilot and linked(pilot_plus,"PILOT_P") and not linked("PILOT_P","PILOT_D")
        nets = network()
        wanted = Relays(ka=coil("KCA1","0","1"), kb=coil("KCB1","0","1"),
            ready=coil("KREADY1","0","1"), enable=coil("KEN1","0","1"),
            ks1=coil("KS1","A1","A2"), ks2=coil("KS2","A1","A2"),
            oem=c.pilot and linked(pilot_plus,self.pins["KOF1","A1"])
                and linked(self.pins["KOF1","A2"],pilot_return))
        feeder = c.branch and linked("BRANCH_LINE","OEM_LINE") and linked("BRANCH_NEUTRAL","MOTOR_RETURN")
        assert (feeder and r.oem) == (c.branch and linked("BRANCH_LINE","OEM_SWITCHED_LINE")
                                       and linked("MOTOR_RETURN","BRANCH_NEUTRAL"))
        return wanted, coil("KID1","A1","A2"), feeder, feedback

    def settle(self, c, r=Relays(), timer=False):
        # Solve every feedback path with contacts settling in relay ticks. A
        # disagreement that does not settle is a failure, not a forced state.
        seen = set()
        while (r,timer) not in seen:
            seen.add((r,timer))
            wanted, proof, feeder, feedback = self.evaluate(c,r,timer)
            if timer and not proof:
                timer=False
            elif wanted == r:
                return r,timer,proof,feeder,feedback
            else:
                r=wanted
        raise AssertionError(("relay chatter",c,r,timer))

class Rig:
    """An event changes physical inputs; one separate event matures the on-delay."""
    def __init__(self, circuit, controls):
        self.circuit = circuit
        self.c = controls
        self.r = Relays()
        self.timer = False
        self.step()

    def step(self, dwell=False, **inputs):
        self.c = replace(self.c, **inputs)
        self.r,self.timer,self.proof,self.feeder,self.fb = self.circuit.settle(self.c,self.r,self.timer)
        if dwell and self.proof:
            self.r,self.timer,self.proof,self.feeder,self.fb = self.circuit.settle(self.c,self.r,True)
        self.motor = self.feeder and self.r.oem

    def arm(self):
        self.step(reset="released", dwell=True)
        assert self.r.ready and not self.r.enable
        self.step(reset="travel")
        assert self.r.ready and not self.r.enable
        self.step(reset="pressed")
        assert self.r.enable and self.feeder and not self.motor
        self.step(reset="travel")
        self.step(reset="released")
        assert self.r.enable and self.fb == (self.c.mode == "HOST")

    def run(self):
        self.arm()
        if self.c.mode == "HOST":
            self.step(request_a=True)
            assert not self.motor
            self.step(request_b=True)
            assert self.motor
            self.step(request_b=False)
        else:
            self.step(start=True)
            self.step(start=False)
        assert self.motor

    def cannot_arm(self):
        self.step(reset="released",dwell=True)
        self.step(reset="travel")
        self.step(reset="pressed")
        assert not self.r.enable and not self.feeder and not self.motor

def transient_no_pickup(circuit, c, r):
    """All orders of relay changes, including simultaneous movements, from a settled trip.

    A one-second delay cannot mature during these relay transients; its verified
    reset and a delay longer than the worst measured response are preconditions.
    """
    seen = set()
    todo = [r]
    fields = tuple(Relays.__dataclass_fields__)
    while todo:
        state = todo.pop()
        if state in seen:
            continue
        seen.add(state)
        desired,_,feeder,_ = circuit.evaluate(c,state,False)
        assert not state.enable and not feeder
        changes = [f for f in fields if getattr(state,f) != getattr(desired,f)]
        for k in range(1,len(changes)+1):
            for group in itertools.combinations(changes,k):
                todo.append(replace(state,**{f:getattr(desired,f) for f in group}))
    return len(seen)

def trip_and_restart_tests(circuit):
    counts = {"HOST":0,"LOCAL":0}
    transient_states = 0
    # Arbitrary energized command states include failed-closed board output A
    # (maintained permit), failed-closed B (pickup), and both together.
    for mode, trip, a, b, reset, weld in itertools.product(
            counts, ("stop","overload"), (False,True),(False,True),
            ("pressed","released","travel"), ("","KS1","KS2")):
        rig = Rig(circuit,Controls(mode=mode))
        rig.run()
        rig.step(weld_a=a,weld_b=b,weld_power=weld,reset=reset)
        assert rig.motor
        rig.step(**{trip:True})
        assert not rig.r.enable and not rig.r.oem and not rig.feeder and not rig.fb
        physical = replace(rig.c,**{trip:False})
        transient_states += transient_no_pickup(circuit,physical,rig.r)
        rig.step(**{trip:False},dwell=True)
        assert not rig.r.enable and not rig.motor and not rig.feeder
        # If RESET was held through trip, simply releasing it can only prepare
        # the next deliberate press. All command contacts are still as failed.
        rig.step(reset="released",dwell=True)
        assert not rig.motor and not rig.r.enable
        if weld or (mode == "HOST" and (a or b)):
            rig.cannot_arm()
        else:
            rig.arm()
            assert not rig.motor
        counts[mode] += 1
    return counts,transient_states

def reset_qualification(circuit):
    for mode in ("HOST","LOCAL"):
        rig=Rig(circuit,Controls(mode=mode))
        assert rig.proof and not rig.timer and not rig.r.ready
        rig.step(reset="pressed",dwell=True)
        assert rig.timer and not rig.r.ready and not rig.r.enable
        rig.step(reset="released",dwell=True)
        assert rig.r.ready and not rig.r.enable
        # A second supply interruption or STOP invalidates that earlier release.
        rig.step(stop=True)
        rig.step(stop=False,reset="pressed",dwell=True)
        assert rig.timer and not rig.r.ready and not rig.r.enable
        rig.arm()
        # Both poles must open during a physical transfer. The budget profile
        # makes no claim against a defective reset button with both poles bridged.
        rig.step(mode="NONE")
        assert not rig.feeder
    return "pre-held RESET, early press during idle qualification, break-before-make travel and proper re-arm passed"


def release_cases(circuit):
    tests = {}
    for mode in ("HOST","LOCAL"):
        for defect in ("stop_lead","overload_lead"):
            rig = Rig(circuit,Controls(mode=mode))
            rig.run()
            rig.step(defect=defect, weld_a=True,weld_b=True)
            assert not rig.feeder and not rig.motor
            rig.step(defect="",dwell=True)
            assert not rig.feeder
            tests[f"{mode}/{defect}"] = "dropped and retained off"
        for fault in ("stuck factory START","stuck factory seal","start bridged in HOST"):
            if fault.endswith("HOST") and mode != "HOST":
                continue
            rig=Rig(circuit,Controls(mode=mode))
            rig.run()
            rig.step(start=fault=="stuck factory START",weld_seal=fault=="stuck factory seal",
                     weld_b=fault=="start bridged in HOST")
            rig.step(stop=True)
            rig.step(stop=False,dwell=True)
            rig.cannot_arm()
            tests[f"{mode}/{fault}"] = "blocked deliberate re-enable"
        rig=Rig(circuit,Controls(mode=mode))
        rig.run()
        rig.step(mode="NONE",weld_a=True,weld_b=True)
        assert not rig.motor and not rig.feeder
        rig.step(mode="LOCAL" if mode=="HOST" else "HOST",dwell=True)
        assert not rig.r.enable and not rig.feeder
        tests[f"{mode}/transfer via open position"] = "fresh reset required"
    return tests

def power_and_shutter(circuit):
    counts = {}
    for mode, fault in itertools.product(("HOST","LOCAL"),("none","both welded")):
        key=f"{mode}/{fault}"
        n=0
        for source in ("cabinet","pilot","branch","board"):
            rig=Rig(circuit,Controls(mode=mode))
            rig.run()
            rig.step(weld_a=fault!="none",weld_b=fault!="none",reset="pressed")
            rig.step(**{source:False})
            if source=="board" and mode=="LOCAL":
                assert rig.motor  # physical LOCAL is independent of the main logic supply
            else:
                assert not rig.feeder and not rig.motor
            rig.step(**{source:True},dwell=True)
            assert rig.motor == (source=="board" and mode=="LOCAL")
            n+=1
        for order in itertools.permutations(("cabinet","pilot","branch","board")):
            c=Controls(mode=mode,cabinet=False,pilot=False,branch=False,board=False,reset="pressed",
                       weld_a=fault!="none",weld_b=fault!="none")
            rig=Rig(circuit,c)
            for source in order:
                rig.step(**{source:True},dwell=True)
                assert not rig.r.ready and not rig.r.enable and not rig.motor
            rig.step(reset="released",dwell=True)
            assert not rig.r.enable and not rig.motor
            n+=1
        for welded_shutter in ("","shutterA","shutterB"):
            rig=Rig(circuit,Controls(mode=mode))
            rig.run()
            rig.step(cover=False,isolator=False,weld_a=True,weld_b=True,defect=welded_shutter)
            assert not rig.motor and not rig.feeder and not rig.r.enable
            rig.cannot_arm()
            rig.step(cover=True,isolator=True,dwell=True)
            assert not rig.motor and not rig.feeder
            n+=1
        counts[key]=n
    return counts

class RecloseTimer:
    """KT1 OND/HOLD contract for one established run and one raw-bus loss.

    The input width is a manufacturer setting. Worst OFF latency and minimum
    blank duration below are required cabinet acceptance measurements.
    """
    def __init__(self, aux_open_ms, recovered_ms, output_drop_ms):
        self.trip_at=aux_open_ms
        self.clear_at=recovered_ms
        self.drop_at=aux_open_ms+output_drop_ms

    def output(self, t):
        if self.clear_at-self.trip_at < 1:
            return True  # conservative: no pulse captured
        return t < self.drop_at or t >= self.clear_at+900


def short_trip_capture(circuit):
    # Operating-envelope requirements, not measured performance of the actual
    # starter: max 2 ms mechanical auxiliary skew, max 8 ms to a confirmed
    # nonconducting timer output and SSRs, and min 16 ms effective factory
    # pilot opening. A nominal 1-ms minimum signal width alone cannot prove
    # output latency. 900 ms of reclose inhibit must outlast *all* relay drops.
    tested=0
    transient_states=0
    for mode,trip,pulse,skew,delay,reset,phase in itertools.product(
            ("HOST","LOCAL"),("stop","overload"),(16,20),(0,2),(1,8),
            ("pressed","released"),("running","just enabled","idle with held RUN")):
        c=Controls(mode=mode)
        rig=Rig(circuit,c)
        if phase=="running":
            rig.run()
            rig.step(weld_a=True,weld_b=True,reset=reset)
        elif phase=="just enabled":
            rig.step(dwell=True)
            rig.step(reset="travel")
            # Event interrupted between KEN pickup and KS/mirror travel.
            rig.c=replace(rig.c,reset=reset,weld_b=True)
            rig.r=replace(rig.r,enable=True,ready=True)
        else:
            rig.step(weld_b=True,reset=reset,dwell=True)
            assert not rig.motor
        # Any qualifying pulse is long enough to be captured and open all
        # fast gates before *any possible* original pilot contact reclosure.
        assert pulse-skew>=1 and skew+delay<pulse
        held=replace(rig.c,**{trip:True})
        demanded,_,_,_=circuit.evaluate(held,rig.r,rig.timer)
        assert not demanded.oem and not demanded.enable
        # The timer's positive output stays withdrawn after the physical button
        # re-closes. Freeze the old KEN/KS/KREADY contacts in the most adverse
        # positions, forcing the OEM armature to be the first mechanical dropout.
        timer = RecloseTimer(skew,pulse,delay)
        assert timer.output(-1) and not timer.output(pulse) and not timer.output(pulse+899)
        during_reclose=replace(rig.c,timer_out=timer.output(pulse))
        slow_state=replace(rig.r,oem=False)
        queued=[(slow_state,rig.timer)]; seen=set()
        while queued:
            r,qual=queued.pop()
            if (r,qual) in seen: continue
            seen.add((r,qual))
            desired,proof,feeder,_=circuit.evaluate(during_reclose,r,qual)
            assert not desired.oem and not desired.ks1 and not desired.ks2 and not desired.enable
            assert not (feeder and r.oem)
            pending=[f for f in Relays.__dataclass_fields__ if getattr(r,f)!=getattr(desired,f)]
            for changed in pending:
                queued.append((replace(r,**{changed:getattr(desired,changed)}),qual))
            if qual and not proof: queued.append((r,False))
        transient_states+=len(seen)
        # Dwell through the measured 900-ms blanking interval: all mechanical
        # values have time to follow their forced unpowered states, including
        # a still-held KREADY/RESET. Hardware does not sample a new RESET edge.
        rig.r,rig.timer,_,_,_=circuit.settle(during_reclose,slow_state,rig.timer)
        rig.c=during_reclose
        rig.step(timer_out=timer.output(pulse+900),dwell=True)
        assert not rig.r.enable and not rig.motor
        tested+=1
    assert RecloseTimer(0,0.5,8).output(0.5)  # outside the credited capture range
    # Negative control: bypass the restart timer (instantaneous reclose)
    # while the ordinary KEN seal, KS poles and original held A still persist.
    rig=Rig(circuit,Controls())
    rig.run(); rig.step(weld_b=True)
    released_contact=replace(rig.r,oem=False)
    wanted,_,feeder,_=circuit.evaluate(replace(rig.c,defect="holdoff_bypass",timer_out=False),
                                       released_contact,False)
    assert wanted.oem and wanted.enable and feeder
    return {"boundary_cases":tested,"mechanical_microstates_under_fast_inhibit":transient_states,
            "tested_effective_open_ms":[16,20],"max_aux_skew_ms":2,"min_INA_capture_ms":1,
            "required_max_to_both_outputs_off_ms":8,"required_min_reclose_blank_ms":900,
            "margin_before_earliest_pilot_reclose_ms":6,
            "timer_bypassed_counterexample":"With KEN and KS held in position, OEM releases first; B welded and normal maintained A can restart upon STOP release.",
            "out_of_envelope":"For a pulse shorter than capture or too much auxiliary skew the bypass counterexample can recur. No timing values were measured on the installation."}


def boundary_cases(circuit):
    results = {}
    for defect in ("enable_seal","enable_output"):
        rig=Rig(circuit,Controls())
        rig.run()
        rig.step(weld_a=True,weld_b=True,defect=defect)
        rig.step(stop=True,timer_out=False)
        assert not rig.motor and not rig.feeder
        rig.step(stop=False)
        assert not rig.motor
        rig.step(timer_out=True)
        assert rig.motor
        results[defect]="additional KEN bridge plus retained A and B can permit restart after the delay"
    for defect in ("trip_gate_short","pilot_gate_short"):
        rig=Rig(circuit,Controls())
        rig.run()
        rig.step(weld_b=True)
        # Additional gate short while B is already stuck: STOP itself still
        # interrupts the OEM pilot. For a short pulse hold KEN/KS mechanically
        # seated and allow OEM as the first mechanical dropout.
        parked=replace(rig.r,oem=False)
        inhibited=replace(rig.c, timer_out=False, defect=defect)
        wanted,_,feeder,_=circuit.evaluate(inhibited,parked,False)
        assert wanted.oem and feeder
        results[defect]="additional short can allow pickup during remaining KS mechanical release time; no single-fault safety rating"
    rig = Rig(circuit,Controls())
    rig.run()
    rig.step(weld_a=True,weld_b=True)
    rig.step(request_a=False,request_b=False)
    assert rig.motor
    results["frozen or welded automatic outputs"]="no guaranteed automatic stop; factory STOP still trips"
    rig.step(stop=True)
    assert not rig.motor
    rig=Rig(circuit,Controls())
    rig.run()
    rig.step(stop=True,request_a=True,request_b=False)
    rig.step(stop=False); rig.arm()
    assert rig.r.ka and not rig.motor
    results["retained upstream A demand masked by KFB1"]="fresh manual enable can restore A; B or factory pickup still needed"
    return results

def electrical_corners():
    """Check the specified installation envelope. Measuring it is a separate field test."""
    lo,hi=23.5,24.5
    wiring=0.30               # budget for ALL wiring, sockets and ordinary contacts in a path
    timer_sink=1.5            # acceptance ceiling at <=25 mA including the R46 parallel load
    kh_peak,ko_peak=1.0,0.5   # peak acceptance at actual cold/hot operating conditions
    ron=0.30                  # G3RV-ST500-D-H published maximum at 24 V
    diode=1.10                # D12/D14/D15 maximum forward drop at <=1 A
    raw=lo-wiring
    kh_input=raw-timer_sink
    permitted=raw-kh_peak*ron
    ko_input=permitted
    enable_pick=permitted-diode
    # The 75% G7SA pickup threshold applies at its specified conditions.
    assert kh_input>=21.6 and ko_input>=21.6
    assert enable_pick>=18 and permitted>=18
    assert hi<=26.4 and ko_peak*ron<=0.15
    coil_current_room=2*5.4/24  # two LC1D09BD windings at 24 V and 20 C
    assert coil_current_room<kh_peak and hi/70<ko_peak
    bleed_min,bleed_max=2200*.99,2200*1.01
    sink_nominal_mA=9+1000*hi/bleed_min  # rated KH1 input plus nominal worst voltage/tolerance on R46
    assert sink_nominal_mA<25<100
    assert hi**2/bleed_min<1
    # At 24 V each SSR leakage is <=10 uA. At all installed temperatures/
    # voltages, including any timer/output leakage, require <=100 uA combined
    # into each bleeder. No undocumented timer OFF-current spec is assumed.
    off_v=.0001*bleed_max
    assert off_v<1<2
    # 100 nF/node is a design/measurement ceiling including the field cables.
    raw_to_low=bleed_max*100e-9*math.log((hi-off_v)/(2-off_v))
    assert raw_to_low<.001
    # Worst source maximum, clamped inductive excursion and measured harness ringing.
    max_output=hi+diode+.5
    assert max_output<26.4
    return {"required_at_installed_cabinet_and_pilot_sources_V":[lo,hi],
            "required_total_wiring_and_contact_drop_max_V":wiring,
            "required_KT1_sink_max_V_at_25mA":timer_sink,
            "min_KH1_input_V":round(kh_input,2),"min_KO1_input_V":round(ko_input,2),
            "both_SSR_required_pickup_V":21.6,"min_KEN_set_V":round(enable_pick,2),
            "min_KREADY_and_KEN_hold_V":round(permitted,2),"G7SA_room_pickup_max_V":18,
            "nominal_KS_pair_inrush_and_hold_A_at_24V_20C":round(coil_current_room,3),
            "max_OEM_steady_coil_A_at_70ohm":round(hi/70,3),
            "qualification_peak_A_including_cold_inrush":{"KH1":kh_peak,"KO1":ko_peak},
            "KT1_sink_nominal_mA":round(sink_nominal_mA,2),"required_measured_peak_sink_mA":25,
            "combined_off_leakage_acceptance_uA":100,"max_bleeder_off_V":round(off_v,3),
            "bleeder_worst_power_W":round(hi**2/bleed_min,3),"max_node_capacitance_nF":100,
            "raw_to_2V_RC_ceiling_ms":round(1000*raw_to_low,3),
            "required_measured_ringing_max_V":0.5,"source_plus_clamp_and_ringing_V":max_output,
            "SSR_output_voltage_ceiling_V":26.4,
            "limits":"Engineering corners, not measurements. Check current, leakage, pulse shapes and gate margins across installed temperature/load, including SSR thermal derating, exact specified DC-only -D-H switching performance, cabling and the actual flyback load."}


def main():
    xml=CHECKS/"guard-netlist.xml"
    circ=Circuit(native_checks(xml))
    trips,transients=trip_and_restart_tests(circ)
    result = {
        "kicad_erc_violations":0,
        "cabinet_electrical_envelope":electrical_corners(),
        "checked_declared_native_contact_rows":circ.contact_rows,
        "normal_run_then_stop_or_overload_cases":trips,
        "reset_and_idle_qualification":reset_qualification(circ),
        "post_trip_recovery_microstates_checked":transients,
        "open_leads_and_retained_commands":release_cases(circ),
        "power_return_and_service_cases":power_and_shutter(circ),
        "short_trip_reclose_inhibit":short_trip_capture(circ),
        "sensitivity_and_limits":boundary_cases(circ),
        "conventional_24V_pilot_proof_calculations":check_pilot(),
        "assumptions":[
            "Conventional 24 V DC OEM pilot, compatible auxiliaries and OPEN_STOP firmware. One electrical installation, settled contact states.",
            "Settled cases allow the relays and timer to release. Short STOP/overload cases separately freeze KEN/KS and credit an independently powered KT1 reclose blank only inside its specified acceptance envelope. Actual switch travel, bounce, timing and coast remain unmeasured.",
            "Relay travel normally settles before the 1 s idle proof matures; loss of timer supply resets this delay per the timer's physical specification.",
            "Open-position transfer and captured-key service interlock require physical verification. No unattended overflow protection or safety integrity rating is inferred."
        ],
        "physical_starter_tested":False,
    }
    files=[Path(__file__).resolve(), ROOT/"tools/build_budget_cabinet.py", ROOT/"tools/check_integrated_cabinet.py",
           ROOT/"tools/check_independent_starter_guard.py", xml,MAIN_XML,REFERENCE,CHECKS/"erc.json",FIELD/"contacts.csv",
           FIELD/"bom.csv",*(FIELD.glob("*.kicad_sch"))]
    result["sha256"]={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    (CHECKS/"faults.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"{circ.contact_rows} schematic poles, {trips} trip cases and {transients} recovery microstates passed.")

if __name__=="__main__":
    main()
