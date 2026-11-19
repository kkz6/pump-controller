#!/usr/bin/env python3
"""Check proposed service-plug topology using ideal unpowered contact continuity.

Names describe nodes, not connector pins. Only one plug can occupy the socket.
GAP is a service state entered with both supplies isolated and the motor stopped.
This does not test hardware, timing, OEM electronic logic or a welded motor contactor.
"""

from itertools import product
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET


# In HOST each remote pair is carried on its own two wires. LOCAL disconnects
# all four and restores only the inserted DOL permission segment.
HOST = (("start_a", "remote_start_a"), ("start_b", "remote_start_b"),
        ("stop_a", "remote_stop_a"), ("stop_b", "remote_stop_b"))
LOCAL_DOL = (("stop_a", "stop_b"),)
LOCAL_KEYPAD = ()
GAP = ()
REMOTE = ("remote_start_a", "remote_start_b", "remote_stop_a", "remote_stop_b")
FIELD = ("start_a", "start_b", "stop_a", "stop_b")


def connected(links, source, target):
    reached = {source}
    pending = [source]
    while pending:
        current = pending.pop()
        for a, b in links:
            if current not in (a, b):
                continue
            other = b if current == a else a
            if other not in reached:
                reached.add(other)
                pending.append(other)
    return target in reached


def command_contacts(remote_start, remote_stop_contact):
    # Each value is the actual contact position. It includes power loss,
    # healthy commands, and a relay stuck open or welded closed.
    links = []
    if remote_start:
        links.append(REMOTE[:2])
    if remote_stop_contact:
        links.append(REMOTE[2:])
    return links


def dol_coil_path(plug, remote, local_start, stop_released, overload_ok, holding, independent_ok=True):
    # The last series contact represents a separately engineered common trip
    # (for example high-high). The controller-board J31 is not such a contact.
    links = list(plug) + remote + [("stop_b", "start_a")]
    for pair, closed in [(("feed", "after_stop"), stop_released),
                         (("after_stop", "after_overload"), overload_ok),
                         (("after_overload", "stop_a"), independent_ok),
                         (("start_a", "start_b"), local_start or holding)]:
        if closed:
            links.append(pair)
    return connected(links, "feed", "start_b")


class ManualPlugChecks(unittest.TestCase):
    def test_kicad_contact_wiring(self):
        root = Path(__file__).resolve().parents[1]
        cli = shutil.which("kicad-cli")
        if not cli and (root / ".tools/kicad-cli").is_file():
            cli = root / ".tools/kicad-cli"
        if not cli:
            self.skipTest("KiCad CLI is required for the schematic wiring check")

        schematic = root / "hardware/manual-transfer/manual-transfer.kicad_sch"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manual-transfer.xml"
            subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadxml",
                            "-o", output, schematic], check=True)
            nets = ET.parse(output).findall(".//nets/net")

        expected = [
            # Fixed starter harness: STOP, overload, socket, independent
            # trips, original START/hold branch and contactor coil.
            "T1.1 S1.1", "S1.2 F1.1", "F1.2 J1.3", "J1.4 F2.1",
            "F2.2 J1.1 S2.1 K4.1", "J1.2 S2.2 K4.2 K5.1", "K5.2 T2.1",
            # Controller cable: separate START pair and series permission contacts.
            "P1.1 K3.1", "P1.2 K3.2", "P1.3 K1.1", "K1.2 K2.1", "K2.2 P1.4",
            # Manual insert: both START cavities open, one permission link.
            "P2.1", "P2.2", "P2.3 P2.4",
        ]
        actual = [frozenset(f"{node.get('ref')}.{node.get('pin')}" for node in net.findall("node"))
                  for net in nets]
        self.assertCountEqual(actual, [frozenset(group.split()) for group in expected])

    def test_field_separation(self):
        for plug in (LOCAL_DOL, GAP):
            for a, b in product(REMOTE, FIELD):
                self.assertFalse(connected(plug, a, b))

    def test_dol_paths(self):
        for start, released, healthy, holding, remote_start, permit, independent_ok in product((False, True), repeat=7):
            remote = command_contacts(remote_start, permit)
            hardwired_ok = released and healthy and independent_ok
            args = (remote, start, released, healthy, holding, independent_ok)
            self.assertEqual(dol_coil_path(LOCAL_DOL, *args), hardwired_ok and (start or holding))
            self.assertEqual(dol_coil_path(HOST, *args), hardwired_ok and permit and (start or remote_start or holding))
            self.assertFalse(dol_coil_path(GAP, *args))

    def test_close_to_command_keypad(self):
        # Local button circuits remain intact on the OEM side. This checks
        # delivery of button closures only, not whether the starter accepts them.
        for start, stop, remote_start, remote_stop in product((False, True), repeat=4):
            physical = command_contacts(remote_start, remote_stop)
            if start:
                physical.append(FIELD[:2])
            if stop:
                physical.append(FIELD[2:])
            for plug, host in [(GAP, False), (LOCAL_KEYPAD, False), (HOST, True)]:
                # For a keypad, both the LOCAL plug and empty socket provide
                # no remote links and no permission bridge. Opening both
                # command paths cannot issue STOP to a running, latched panel.
                links = list(plug) + physical
                self.assertEqual(connected(links, *FIELD[:2]), start or (host and remote_start))
                self.assertEqual(connected(links, *FIELD[2:]), stop or (host and remote_stop))

    def test_dol_rearm_with_controller_contacts_welded(self):
        remote = command_contacts(True, True)
        running = False  # supply isolation released the OEM holding contact
        # START released on restoration, fresh press, seal-in, STOP, release
        for start, stop_released, expected in [(False, True, False), (True, True, True),
                                                (False, True, True), (False, False, False),
                                                (False, True, False)]:
            running = dol_coil_path(LOCAL_DOL, remote, start, stop_released, True, running)
            self.assertEqual(running, expected)
        # A stuck OEM START would defeat fresh-press behavior on a simple DOL.
        self.assertTrue(dol_coil_path(LOCAL_DOL, remote, True, True, True, False))


if __name__ == "__main__":
    unittest.main()
