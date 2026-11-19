"""Check field harness continuity against the exported dual-output KiCad schematic."""
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from check_manual_service_plug import connected


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware/main-compact-dual"
CLI = os.environ.get("KICAD_CLI") or shutil.which("kicad-cli") or ROOT / ".tools/kicad-cli"


def export_pins(folder, out):
    subprocess.run([CLI, "sch", "export", "netlist", "--format", "kicadxml", "-o", out,
                    folder / "pump-controller-compact.kicad_sch"], check=True)
    return {f"{node.get('ref')}.{node.get('pin')}": net.get("name")
            for net in ET.parse(out).findall(".//nets/net") for node in net.findall("node")}


def equal(actual, expected, context):
    if actual != expected:
        raise ValueError(f"{context}: expected {expected!r}, got {actual!r}")


def check():
    with tempfile.TemporaryDirectory() as directory:
        dest = Path(directory)
        pins = export_pins(BOARD, dest / "dual.xml")
        old = export_pins(ROOT / "hardware/main-compact-led", dest / "original.xml")
    expected_changes = {"K1.2", "K1.3", "K2.2", "K2.3", "J30.1", "J30.2", "U33.24", "U33.23"}
    removed_service_switch_pins = {"SW1.1", "SW1.2", "SW2.1", "SW2.2"}
    equal(old.keys() - pins.keys(), removed_service_switch_pins, "removed service switch pins")
    equal({pin for pin in old.keys() & pins.keys() if pins[pin] != old[pin]}, expected_changes, "baseline changed pins")
    membership = {
        "CTRL_A_COM": {"J30.1", "K1.2"}, "CTRL_A_NO": {"J30.2", "K1.3"},
        "CTRL_B_COM": {"J35.1", "K2.2"}, "CTRL_B_NO": {"J35.2", "K2.3"},
        "HOST_AUX_N": {"J36.2", "R192.1"}, "LOCAL_AUX_N": {"J36.3", "R193.1"},
        "HOST_SENSE_N": {"U33.24", "R192.2", "R194.2"},
        "LOCAL_SENSE_N": {"U33.23", "R193.2", "R195.2"},
    }
    for net, terminals in membership.items():
        equal({pin for pin, name in pins.items() if name == net}, terminals, net)
    for pin, net in {"J36.1": "GND", "R194.1": "+3V3", "R195.1": "+3V3",
                     "J2.1": "GND", "J2.2": "+3V3", "J2.5": "MCU_EN", "J2.6": "BOOT",
                     "J2.7": "USB_DM", "J2.8": "USB_DP",
                     "U33.8": "START_CMD_LED", "U33.28": "STOP_CMD_LED"}.items():
        equal(pins[pin], net, pin)
    a1, a2, b1, b2 = (pins[p] for p in ("J30.1", "J30.2", "J35.1", "J35.2"))

    cases = 0
    for a, b in itertools.product((False, True), repeat=2):
        contacts = []
        if a:
            contacts.append((pins["K1.2"], pins["K1.3"]))
        if b:
            contacts.append((pins["K2.2"], pins["K2.3"]))
        # No conductive link between the two bare PCB channels in any relay state.
        for left, right in itertools.product((a1, a2), (b1, b2)):
            equal(connected(contacts, left, right), False, "independent field pairs")

        for host in (False, True):
            # Exclusive transfer disconnects all remote field conductors in LOCAL.
            run = contacts + ([(a1, "run1"), (a2, b1), (b2, "run2")] if host else [])
            equal(connected(run, "run1", "run2"), host and a and b, "two-wire RUN")
            cases += 1
            for common in (False, True):
                # One approved shared OEM common, or two electrically separate contact pairs.
                ca = "common-a"
                cb = ca if common else "common-b"
                remote = [(a1, ca), (a2, "function-a"), (b1, cb), (b2, "function-b")]
                keypad = contacts + (remote if host else [])
                equal(connected(keypad, ca, "function-a"), host and a, "electronic START")
                equal(connected(keypad, cb, "function-b"), host and b, "electronic STOP")
                equal(connected(keypad, ca, cb), common, "OEM common arrangement")
                cases += 1
            # An NC-stop DOL uses A for permission and B for START. Only here
            # does the LOCAL insert restore the added series permission section.
            for physical_stop_ok, overload_ok, required_trip_ok, local_start, holding in itertools.product(
                    (False, True), repeat=5):
                path = contacts + ([("permission-in", a1), (a2, "permission-out"),
                                    ("permission-out", b1), (b2, "coil")] if host
                                   else [("permission-in", "permission-out")])
                for first, second, closed in [
                    ("feed", "overload", physical_stop_ok), ("overload", "safety", overload_ok),
                    ("safety", "permission-in", required_trip_ok), ("permission-out", "coil", local_start or holding)
                ]:
                    if closed:
                        path.append((first, second))
                expect = physical_stop_ok and overload_ok and required_trip_ok and (a or not host)
                expect = expect and (local_start or holding or (host and b))
                equal(connected(path, "feed", "coil"), expect, "DOL hardwired coil path")
                cases += 1
    return {"ideal_harness_cases": cases, "unchanged_baseline_pin_assignments": len(old) - len(expected_changes) - len(removed_service_switch_pins),
            "removed_service_switch_pins": sorted(removed_service_switch_pins),
            "changed_baseline_pins": sorted(expected_changes), "passed": True,
            "physical_harness_tested": False}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
