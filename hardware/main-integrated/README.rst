Integrated main controller R4
=============================

This main PCB contains the controller and its guard signal receiver. The other PCB in the installation is the
`OLED and five-button panel F <../panel-rev-f/README.rst>`_. Motor current still passes through the two
external series contactors and the original starter. The main and panel use a straight twelve-way cable.

Where the independent stop acts
-------------------------------

The original red STOP retains its factory contact in the starter. A second normally closed contact,
operated by that **same actuator**, and a dedicated normally closed high-high float contact feed the
external guard. Opening either drops the guard and removes the motor feeder in both HOST and LOCAL.
A board reset, loss of radio or processor failure cannot bridge those two field contacts. The tank's
conductive level electrodes serve the automatic fill logic. The independent high-high input needs its own
float and cable. A short across the float or a float stuck in the down position masks that input.

KS1 and KS2 break the feeder in series. Both contactors, their monitored feedback contacts,
the 24 V cabinet supply, guard relays, monitored reset and enable, and the USB access interlock are part
of this design. The two-PCB count excludes those cabinet devices. A starter with only an electronic
STOP key requires a verified independent contact/interface before this profile can be commissioned.
See the `cabinet wiring drawing <../starter-guard-r4/starter-wiring.pdf>`_,
`cabinet schematic <../starter-guard-r4/guard-schematic.pdf>`_ and
`fault-model results <../starter-guard-r4/checks/faults.json>`_.

Plug connections
----------------

* **J1** takes the protected, always-on AC branch for main power and line voltage sensing. **J10** takes
  the specified CT secondary. The CT surrounds one total motor-current conductor. On this design the
  CT secondary and metering section are mains-referenced.
* **J20** takes the conductive tank probes. **J21** takes the inlet probe and its return. Route these
  low-voltage sensor wires separately from the live metering wiring on J10.
* **J30** (A) and **J35** (B) each provide two independent normally open relay terminals, COM and NO.
  They command the cabinet's pilot interposers. Starter profiles, terminal numbering and the
  cabinet transfer contacts are documented in the wiring drawing. The reference pilot and proof circuit is for 24 V DC.
  Verify the actual OEM control voltage, spare STOP contact and electronic key behavior for this starter.
* **J32** connects to panel **J1**. The five operator buttons, external button station, OLED and optional
  AUTO/MANUAL key stay on the panel. Panel STOP acts in the host command circuit. The original starter
  STOP has its own independent cabinet path.
* **J52** uses a three-way JST PH housing (PHR-3). Pin 1 is logic common, pin 2 is the HOST position
  return and pin 3 is the LOCAL position return. Use separate isolated selector auxiliary contacts.
* **J54** uses a five-way JST VH housing (VHR-5N). Pin 1 is fused cabinet +24 V, pin 2 cabinet 0 V,
  pin 3 switched-positive heartbeat to WD1, pin 4 switched-positive drive to the panel-permit relay
  KPS1, and pin 5 the switched-positive feedback from the contactors and HOST selector. Pin 5 drives
  the KFB1 coil. The KFB1 normally open contact gates the K1 coil directly on the main PCB.
* **J40** is USB-C programming, with separate target power on **J41** in bench service.
  Follow the trapped-key isolation and shutter procedure on the cabinet drawing.
  USB VBUS inhibits both PCB command coils. The external service isolator also blocks motor power with a dead USB cable.

Build from the `KiCad project <pump-controller-integrated.kicad_pro>`_,
`main schematic <exports/schematic.pdf>`_ and `component list <bom.csv>`_.
The board is double-sided for assembly. Confirm standoff clearance, plug withdrawal, harness bends,
connector access, and shutter fit on the populated unit in the intended cabinet.


Electrical review
-----------------

The `receiver and main pin comparison <checks/net-equivalence.json>`_ checks every retained terminal
against the earlier two designs. The `power and input-margin calculations <power-and-signal-review.rst>`_
reserve 25 mA of isolated 5 V for the added receiver. The simultaneous budget reaches 5.864 W and
1.158 A at different supply corners. This leaves 0.136 W and 42 mA against the converter rating.
The full allocation exceeds the module's 5 W rating at 65 °C. Measure local temperature and supply
margin in the closed cabinet with both command coils energized, radio active and the display lit.

Robu prototype files
--------------------

Upload the `integrated main Gerber ZIP <pump-controller-integrated-r4-gerber-prototype.zip>`_ and the
`OLED panel Gerber ZIP <../panel-rev-f/pump-panel-rev-f-gerber-prototype.zip>`_ as two separate bare-board jobs.
Main R4 is 100 × 115.5 mm with six copper layers, 1.6 mm FR-4 Tg155 or confirmed equivalent, 1 oz outer,
0.5 oz inner, green solder mask and ENIG. Panel F is 60 × 45 mm with two copper layers, 1.6 mm FR-4 and
1 oz copper. Request electrical testing against the IPC-D-356 netlist in each archive. Paste files for a
stencil are separate. The old receiver ZIP belongs to the three-board R3 design.

**Main board DFM request.** Confirm in writing that both J40 USB-C plastic locator holes can be delivered
at 0.65 ±0.05 mm finished with the connector drawing's position tolerance. Review the relieved corners on
the four outer USB lands, and preserve the isolation and mains copper gaps identified in the manufacturing
notes. Robu publishes ±0.20 mm for standard non-plated holes. Obtain agreement before approving the main
job. See `Robu manufacturing capabilities <https://robu.in/pcb-manufacturing-capabilities/>`_ and
the `GCT USB4110 drawing <https://gct.co/files/drawings/usb4110.pdf>`_.

Panel fit and proof testing
---------------------------

The main PCB replaces the previous 100 × 97 mm controller and 68 × 48 mm receiver. Its length increases
by 18.5 mm while their combined bare-board area drops by 1,414 mm² (10.9%). Use the
`full-size mounting template <exports/mounting-template.pdf>`_ and `fit notes <mounting.rst>`_
to check connector access and the underside in the intended cabinet. The `two-board front view
<exports/pcb-layout.png>`_ identifies the starter, display and guard connections.

Before connecting a motor, verify the fitted STOP auxiliary and dedicated float, each separately in
HOST and LOCAL, with controller power removed and a simulated stuck command. Confirm loss of feeder
voltage on the load side of KS2, and verify that closing the float or releasing STOP cannot itself restart
the machine. Then measure actual pump stopping time, tank run-on and the available volume above the float.
Perform these tests with a qualified panel builder and the actual starter.


PCB verification
----------------

KiCad 10.0.8 ERC, DRC and schematic parity passed. The independent geometry audit checks 787 connected
source pins against both the PCB and the exported schematic. Across all six layers, the minimum projected
cabinet-to-live copper separation is 8.175 mm. Cabinet-to-logic separation is 3.064 mm (rounded).
Onboard mains/meter copper to controller logic is 8.400 mm. The starter contacts are 9.425 mm from
onboard mains/meter copper. The design permits 2.80 mm only at the fixed U1 input lands within the
mains circuit. Component bodies, field wiring, fasteners and finished insulation need separate checks.
See the `geometry report <checks/independent-geometry.json>`_,
`injected clearance tests <checks/isolation-negative-tests.json>`_ and
`receiver clamp and return measurements <checks/receiver-routing.json>`_.

The `archive connectivity report <checks/gerber-copper-connectivity.json>`_ compares actual
Gerber copper and plated drills from both ZIPs with their IPC netlists. It includes injected opens
and shorts to verify that the comparison detects faults.
