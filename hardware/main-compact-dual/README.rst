Guarded single-phase pump controller, revision R2
=================================================

**Engineering prototype for the bench.** The 100 × 97 mm six-layer main PCB,
60 × 45 mm OLED panel, isolated signal receiver and external cabinet guard
work together. The starter
and its capacitor circuit still carry the motor current. The independent guard
adds two series motor contactors ahead of the starter. Allow cabinet space for
them, the control supply, monitoring and terminals before ordering hardware.
For assembly, U11 and its four specified 0402 capacitors require the placement
and inspection tolerances in the `R2 electrical review <../../design/compact-dual-guard-r2.rst>`_.

Start with the `field assembly and wiring <../starter-guard/README.rst>`_ and
`connection drawing <exports/starter-wiring.pdf>`_. The original starter STOP,
overload and a separate normally closed high-high float act on the hardwired
guard in HOST and LOCAL. Opening a float wire also trips it. One stuck float or
a short across its wires needs a separate level-protection design if that fault
must be tolerated. Keep the original capacitor-start cutout and overload in service.

Connections
-----------

* J1 powers the controller from a protected AC branch. The voltage circuit
  monitors the controller supply. Pass one motor-current conductor through the
  specified CT and connect its secondary to J10. Keep that mains-referenced
  secondary segregated from the isolated probe and panel wiring.
* J20 accepts tank common and four level probes. J21 is a shrouded two-way
  JST XH header for the inlet electrode and its qualified return. Confirm the
  existing inlet probe return before connecting it. Do not tie the two
  excitation outputs together. The **independent float goes to the cabinet
  guard**, on its own cable, so loss of the tank common cannot defeat it.
* J30 and J35 are dry contacts. Each pin 1 is COM, pin 2 NO. In R2 they switch
  the guard's separately fused 24 V **command interposer coils** A and B. The
  interposers provide the contacts for the OEM commands and physically prove
  that each command has released before re-enable. Route the original OEM
  controls through the chosen profile harness as shown in the drawing.
* J31, the two-way 3.81 mm Phoenix plug, accepts **only the external guard's
  isolated NO feedback contact**. It closes in permitted HOST operation. Leave
  the PCB unpowered for wiring. A shunt, cabinet voltage or a direct connection
  to the tank float is incompatible with this design.
* J36 is five-way JST ZE. Pin 1 is logic GND, pin 2 HOST auxiliary, pin 3
  LOCAL auxiliary, pin 4 the 3.3 V heartbeat and pin 5 the raw OLED STOP-loop
  health signal (nominal 5 V). Pins 2 and 3 take separate dry contacts to pin 1.
  Pins 4 and 5 feed only the specified high-impedance receiver. Connect main J36 to receiver J36 with five straight-through cores. The separate
  J31-to-J31 two-core cable carries only the permit contact. Number both ends
  by cavity, then test continuity before installation. The isolated receiver
  connects the logic domain to the cabinet controls. See the
  `receiver PCB and connectors <../guard-receiver/README.rst>`_. Never apply 24 V
  to J36. The `harness parts list <starter-harness-parts.csv>`_ specifies the
  mating housings and terminals.
* J32 connects to OLED panel J1 through a pin-for-pin 12-way cable. The panel
  carries START, STOP, MODE, SET/RESET and NEXT/+. Optional external operator
  buttons terminate on the panel. When fitting remote NC STOP at panel J3,
  remove JP1 and verify opening either STOP breaks the loop. The optional
  maintained AUTO/MANUAL selector uses panel J8 (JST GH3), pin 1 common +5 V,
  pin 2 MANUAL, pin 3 AUTO. J8 selects the operating mode. The separate
  mechanical service transfer at the starter determines whether the PCB can
  issue commands. See the `panel drawings <../panel-rev-e/README.rst>`_.
* J2 supports service programming. Pins 7 and 8 are native USB D− and D+,
  pin 1 logic GND, pins 5 and 6 EN and BOOT. Pin 2 is 3.3 V. Leave pin 4
  (ARM_CMD) open for native USB. Use an isolated bench with mains and starter
  wiring disconnected. USB VBUS must stay off the 3.3 V rail.

Choosing a starter profile
--------------------------

============================  ==========================  =========================
Verified OEM interface        Guard contact A              Guard contact B
============================  ==========================  =========================
Maintained RUN                Series RUN contact           Second series RUN contact
Close START, open STOP        Series holding permission    Momentary START closure
Close START, close STOP       Momentary START closure      Momentary STOP closure
============================  ==========================  =========================

The two-, three- and four-wire alternatives describe the **OEM side of the
interposers**. A shared common needs explicit OEM approval. The guard still
requires its independent STOP, float, overload, voltage and restart-proof
connections in each case. The pictured electronic starters have no verified
terminal mapping or restart proof. An electronic keypad by itself cannot
establish compatibility. Keep that profile disabled until its documented
power-restoration behavior and field tests meet the guard requirements.
For a holding-circuit starter, prove that a welded seal-in contact or short
across START cannot create a false idle indication when its feeder is off.

With the motor isolated, mark and secure the physical harness, exercise both
commands individually into a low-voltage simulator, check neutral proof and
verify the polarity and timing on the actual OEM interface. Record the harness
identity and accepted profile in service configuration separately from the
requested profile. A missing or mismatched profile disables the sequencer.
Seal or lock access to the transfer and harness. Recommission after changing
either. The PCB does not automatically identify a swapped OEM harness.

Power return and loss of control
--------------------------------

The cabinet guard drops the motor contactors on a trip. Restoring supply or
releasing STOP alone must leave them open. The wired sequence requires a
separate monitored reset and a new guarded enable with commands released and
the starter proven off. Only then can a fresh START operate the pump. Verify
loss and restoration of the starter feeder while cabinet 24 V stays live, and
the reverse, on the actual installation. Coordinate the feeder monitor with
the earliest voltage dip that resets this particular starter.

In HOST, the external guard also checks the OLED STOP return directly and
requires heartbeat edges from GPIO21. The firmware component accepts a new
heartbeat edge no faster than every 100 ms, only after fresh panel data and a
new, successful protection evaluation. Service this control task and refresh the
qualified input assessment at least every 25 ms for the nominal 5 Hz signal.
Use the original conversion timestamps to check sample freshness. Boot or a failed sample holds the
heartbeat low for at least 3 s. Healthy readings can qualify the external
monitor while J31 is open. J31 is required to start. A power cycle clears
AUTO run authorization even when the maintained key still selects AUTO. The
operator must release START and press it again after recovery. A live task,
radio connection or running timer alone must never service the guard.

Field use requires the complete application to make a fresh conversion-based
health assessment, apply ``guard_gpio_step`` from its control task, drive
the sequenced relay and arm pins and fail closed on errors. This repository
provides control components. There is no commissioned application or
pump-specific metering and dry-run calibration. The two SMD command LEDs show
accepted commands. Use independent feedback to establish actual motor state.

Design files and verification
-----------------------------

* `KiCad project <pump-controller-compact.kicad_pro>`_, `PCB <pump-controller-compact.kicad_pcb>`_,
  `schematic PDF <exports/schematic.pdf>`_ and `BOM <bom.csv>`_.
* `Board top <exports/board-top.png>`_, `starter connector view <exports/main-starter-contacts.png>`_,
  `panel front and rear <exports/oled-panel-3d.png>`_ and `enclosure <../../mechanical/compact-dual/README.rst>`_.
* `Native rule checks <checks/independent-summary.json>`_, `copper measurements <checks/independent-geometry.json>`_,
  `panel and cable checks <checks/panel-integration.json>`_ and `harness continuity <checks/starter-harness.json>`_.
* `Prototype copper and drill archive <pump-controller-compact-dual-guard-r2-gerber-prototype.zip>`_,
  `stencil archive <pump-controller-compact-dual-guard-r2-stencil-prototype.zip>`_ and
  `fabrication file checks <checks/independent-gerbers.json>`_.
* `R2 release conditions <../../design/compact-dual-guard-r2.rst>`_ and
  `electrical findings on the previous layout <../../design/compact-dual-electrical-audit.rst>`_.
