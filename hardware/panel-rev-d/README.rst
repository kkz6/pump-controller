Rev D low-voltage control panel
==============================

This separate 60 x 45 mm, two-layer PCB carries START, STOP, MODE, SET/RESET
and NEXT/+ buttons, a connector for the small Waveshare 14657 OLED, and
optional connections for all five external buttons. An additional three-wire
connector accepts a maintained AUTO/MANUAL key switch. The main controller
retains its existing control circuit; its onboard SET/NEXT keys are omitted
in the panel assembly variant.

This is a reviewed engineering prototype, not an approved installation or
manufacturing release. Firmware, physical switch operation, contact endurance,
ESD and enclosure fit have not been tested. Isolated low voltage only: no
starter coil, mains, motor or capacitor wiring belongs on this panel.

Files and checks
----------------

* ``pump-panel-rev-d.kicad_pro``: open this project in KiCad 10.
* ``pump-panel-rev-d.kicad_sch`` and four functional sheets: detailed circuit.
* ``pump-panel-rev-d.kicad_pcb``: routed 60 x 45 mm board.
* ``bom.csv`` and ``parts-and-interface.rst``: values, part numbers and harness.
* ``pump-panel-rev-d-gerber-review.zip``: bare-board manufacturer review package,
  including seven Gerber layers, separate PTH/NPTH drills and IPC-D-356 netlist.
* ``exports/panel-front.svg`` / ``panel-rear.svg``: native board views. The rear
  view is mirrored to show the board as seen from its component side.
* ``exports/pump-panel-rev-d.step`` / ``pump-panel-rev-d.glb``: partial native
  3D exports; see the model limitations below.
* ``checks/summary.json``: native ERC 0, DRC 0, unconnected 0, schematic parity
  issues 0, source-pad mismatches 0, via-drill/SMT-pad overlaps 0.

Final board SHA-256:
``6b85b968fdaa5b8524018d4f0972232ee2e1979a254ebbc7d08e5de322ee4418``.

There are 29 electrical components, four mounting holes, 23 through vias,
28 plated holes total, and four nonplated holes. General tracks are 0.30 mm
with a few 0.25 mm sections. Vias are 1.0 mm diameter with 0.4 mm holes.
Default copper clearance is 0.30 mm, with a 0.254 mm via-to-track rule and
0.50 mm drilled-pad spacing. The mask expansion is 0.05 mm. No filled/plated-over
via-in-pad process is required by the nominal SMT drill-overlap audit.

Robu review
-----------

Proposed bare-board order settings: one design, two copper layers, FR-4,
60 x 45 mm, 1.6 mm overall thickness, 1 oz copper, green mask and white legend.
Finish and final material/stackup remain subject to Robu's engineering review;
ENIG is a proposed finish for the SMT assembly. This package does not establish
acceptance of the separate four-layer main PCB.

The Gerber profile centreline is exactly 60 x 45 mm. KiCad's job-file Size field
is 60.05 x 45.05 mm because it includes the 0.05 mm outline stroke; use the
profile centreline as the finished outline. Do not convert it into a larger
board. Gerbers and drills share the absolute origin and are not mirrored.
The rear preview is mirrored only for readability. The ZIP contains no stencil
layer; optional assembly paste files are provided separately under
``exports/stencil``.

Physical controls and STOP loop
------------------------------

SW1 is an Omron D2F-01F, normally closed through its COM and NC terminals.
The custom footprint numbers are 1=COM, 2=NO, 3=NC. The NO terminal is unused.
This numbering is a project convention; the switch manufacturer identifies
its terminals by function. Verify COM/NC continuity on the purchased part.

The hardwired loop is::

    Host +5V -> SW1 COM/NC -> J3 external NC STOP -> STOP_RETURN -> host

JP1 bypasses only the optional external J3 contact. Fit its removable shunt
when no external STOP button is connected. Remove the shunt when an external
NC STOP is installed. Leaving J3 open with no shunt prevents operation.
Never bridge the onboard STOP contact. R1 provides a 2.2 kohm wetting load from
the final STOP_RETURN to GND; the STOP current path contains no series resistor.

SW2 START, SW3 MODE, SW4 SET/RESET and SW5 NEXT/+ are normally open. Their
matching external contacts are connected in parallel. External controls must
be voltage-free contacts in this same low-voltage circuit. Original starter
buttons can be reused only through suitable isolated auxiliary contacts.

MODE requests AUTO/MANUAL selection; it does not directly bypass STOP,
dry-run protection or other interlocks. Firmware must require STOP/release
and a fresh START after a mode change. Settings must not start the motor.

Optional maintained key switch
------------------------------

J8 accepts a break-before-make SPDT key switch. Common goes to J8.1 (+5V),
MANUAL to J8.2 and AUTO to J8.3. Use gold contacts suitable for the approximately
2.7 mA low-voltage load. The NPN stages produce 3.3 V-domain active-low outputs:

========== ============ ===========================
KEY_MAN_N  KEY_AUTO_N   Meaning when key enabled
========== ============ ===========================
0          1            MANUAL selected
1          0            AUTO selected
1          1            Neither contact selected
0          0            Invalid / both active
========== ============ ===========================

The two invalid combinations inhibit starting. Key operation is optional and
must be explicitly configured; unused key inputs are otherwise ignored.
With the key enabled, panel MODE must not override the maintained selection.
Mode changes stop/disarm the controller and require a fresh START.

Main GPIO B6/B7 retain their existing 100 kohm pulldowns and remain inputs with
internal pullups disabled. Panel 10 kohm pullups yield about 0.91 times the
3.3 V rail for a high state. An unplugged key normally gives 1/1; an unplugged
whole panel leaves the host pulldowns at 0/0. This does not detect every possible
individual wire or contact fault.

Mechanical and 3D limitations
-----------------------------

The OLED module envelope is drawn on the front fabrication layer, from
(12,4) to (48,16.5) mm. It is not an OLED mounting footprint or a verified lid
cutout. Provide insulating stand-offs/retention and clearance from front copper
and vias. Mounting holes are at (3,3), (57,3), (3,42), (57,42) mm, diameter2.7mm.

The four B3U tactile buttons and D2F STOP have different actuator heights.
The D2F pin plunger is at approximately (20,30) mm in the proposed orientation;
tactile centres are (7.5,30), (34.5,30), (45,30), (54,30) mm. Panel caps/plungers,
travel, preload and finger access require mechanical design and first-article
verification. Do not treat the board as a finished sealed operator panel.

The STEP and GLB contain the PCB and available standard component bodies.
SW1's custom D2F body and J7's SMT PH connector body are absent; their footprints
remain present. The external OLED module, mating plugs, cables, removable JP1
shunt, key barrel, standoffs and lid are also absent. These partial models must
not be used to approve assembly fit or clearances.

Rebuilding
----------

``tools/build_panel_rev_d.py --check`` reruns native checks and manufacturing
exports without changing the source PCB. It uses KiCad's Python/pcbnew runtime.
``--build`` replaces the board with its initial placement and routing input;
do not run it on a reviewed board unless intentionally starting a new layout.
``--finish`` imports the stored route session, applies the documented minimum
track-width and clearance corrections, and reruns checks. A newly generated
route still requires manual review. Standard footprints are cached locally;
the D2F footprint was derived from its manufacturer's drawing.
