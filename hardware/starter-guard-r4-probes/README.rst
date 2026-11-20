R4 cabinet reference with probe-only level control
==================================================

This profile uses the existing conductive tank electrodes at main J20 for
controller-based level sensing. The inlet sensor at J21 serves a separate
purpose. The cabinet has **no independent high-water shutdown**. A faulty
controller, an open electrode wire that looks dry, a stuck command or a pump
operated locally can overfill the tank. The guard has no direct contact that
reports a full tank. Automatic full-level stopping requires working sensing,
firmware and an accepted starter interface.

This is a **24 V DC pilot engineering reference** for the integrated main board
and Panel F. The native drawing also shows the protected motor feeder and
separate power supplies. The fitted starter, coil characteristics, short-circuit
protection, stopping time and physical hardware have not been qualified.

- `Native KiCad project <starter-guard-r4-probes.kicad_pro>`_
- `Five-sheet cabinet schematic PDF <guard-schematic.pdf>`_
- `Cabinet parts <bom.csv>`_ and `contact paths <contacts.csv>`_
- `KiCad electrical rules report <checks/erc.json>`_ and
  `fault and restart verification <checks/faults.json>`_

Operating controls
------------------

The removable tank plug on the main board is **J20**. Its numbered positions are
**1 COM, 2 L1 (lowest), 3 L2, 4 L3, 5 L4 (FULL)**. COM is the immersed tank
electrode. The four sensing heights give five level bands. The inlet probe uses
its own plug and return at J21.

For controller-commanded filling, the starter control component requests STOP
at a qualified FULL reading or when the configured maximum time for that run
expires, whichever comes first. A normal full stop lets AUTO wait for the next
qualified low level. A time-limit stop requires confirmation that the motor has
stopped, a fresh local SET acknowledgement and a new START. Commission the
time limit against the actual pump and tank. A tank starting nearly full can
overflow well before that time if L4 fails. The production probe reader,
settings interface and integrated application still require implementation.

The application must timestamp each successful tank scan and qualify the wet
pattern before passing it to the controls. A scan older than one second or an
impossible pattern blocks starting and requests a stop during a fill. AUTO
starts at a qualified level below L1. Hold the fill request through the middle
bands until the tank is full or filling is deliberately cancelled.

In **HOST**, the board may request operation through the factory starter
interface. Original STOP and overload each open their OEM pilot contact. Their
isolated auxiliary contacts also remove the common guard permission. The USB
shutter, monitored supplies, selected transfer position, heartbeat and panel
permission retain their R4 functions.

In **physical LOCAL**, the transfer disconnects board commands and restores the
factory pilot return. The original START, STOP and overload still act on the
starter. The separate guard supply, cabinet transfer and power contactors are
still required. A stopped controller can leave a locally started pump running.
The OLED Auto/Manual control is a software selection in HOST. It cannot grant
the board control of a physically LOCAL pump.

The two separate reset and enable actions, OEM idle/release proofs, contactor
mirror feedback and series motor contactors are inherited from the
`R4 cabinet <../starter-guard-r4/README.rst>`_. The published R4 profile
includes a separate working high-high float.

Cabinet differences
-------------------

The probe-only drawing omits LS1. XF2 cavities 5 and 6 are unused and require
no wire or plug link. All other XF2 cavities retain their numbering. The two
physical transfer branches share the supply-proven guard node after KC1. The
native comparison verifies every other connected cabinet terminal and the
selected parts against the original R4 netlist. Both controller PCBs retain
the original R4/Panel F electrical interfaces.

Validation
----------

From the repository root, run::

    python3 tools/build_probe_cabinet.py
    python3 tools/check_probe_cabinet.py

The generator emits the cabinet source, BOM, KiCad ERC report, PDF and native
netlist. The verifier compares a fresh native export and the original published
terminal map, checks all 4,096 possible combinations of the twelve guard input
contacts, and exercises the STOP and overload demands with a broken auxiliary
lead, retained command, false feedback and either single power contactor welded.
It tests ordered reset and enable, held buttons and individual missing release
proofs directly on this profile. It also checks the independent OEM idle proofs,
the USB service lock and supply restoration with an unpowered USB cable.

For the other R4 restart sequences, the verifier proves that every permitted
and failed input combination has the same first-stage result as the published
R4 circuit with a healthy float. It verifies exact equality of every other
contact path, reruns the original transition model and excludes the float demand
from the reported results. The report distinguishes the direct tests from these
equivalent cases.

These are electrical-rule, connectivity and ideal settled-contact checks.
Actual coil release, protective-device DC interruption, tank readings, pump
run-on, service lock geometry and full-level behavior require physical testing.

The `host firmware tests <checks/firmware-host.json>`_ exercise the three
starter command profiles, stale tank readings, FULL, the elapsed run limit and
restart. The `ESP32-C6 build <checks/firmware-target.json>`_ links the control
component into a disabled test application. Neither test operated a pump.
