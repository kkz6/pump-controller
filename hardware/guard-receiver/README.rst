Guard receiver PCB
==================

This 68 × 48 mm, two-layer PCB belongs in the cabinet beside the independent
guard equipment. J36 brings the controller heartbeat and raw panel STOP to two
high-impedance comparator inputs. Separate optocouplers convert them to
24 V signals on J4. A distinct, deenergized-open Omron KFB1 contact returns
the actual HOST guard permission on J31. The hardwired high-high float and
original STOP operate the external guard directly in both HOST and LOCAL.
See the `cabinet schematic <../starter-guard/guard-schematic.pdf>`_ and
`field connection guide <../main-compact-dual/exports/starter-wiring.pdf>`_.

Harnesses
---------

Label both ends by reference and cavity number. Crimp off the board and check
pin 1 at both **mating faces** before power. Both service plugs for J36 and
J31 go straight through between the corresponding board headers.

.. list-table::
   :header-rows: 1
   :widths: 17 35 48

   * - Header
     - Mating part
     - Cavity order and purpose
   * - J36 logic
     - JST ZER-05V-S, SZE-002T-P0.3
     - 1 controller ground, 2 HOST sense, 3 LOCAL sense, 4 heartbeat, 5 raw panel-STOP return. Mate to main J36.
   * - J31 permit
     - Phoenix Contact 1803578, MC 1,5/2-ST-3,81
     - 1 STOP_RETURN and 2 K1-coil permission. Mate to main J31. KFB1 COM4 and NO8 are the only contact between these wires. No shunt.
   * - J2 position
     - JST PHR-3, SPH-002T-P0.5S
     - 1 logic common, 2 isolated HOST full-seat NO, 3 isolated LOCAL full-seat NO. Wire each contact only between its respective pin and pin 1.
   * - J3 receiver supply
     - JST PHR-2, SPH-002T-P0.5S
     - 1 floating +5 V from DDR-15G-5 +Vo, 2 receiver 0 V from -Vo. Set and verify 5.00 V before plugging in.
   * - J4 cabinet
     - JST VHR-5N, SVH-21T-P1.1
     - 1 fused regulated +24 V, 2 cabinet 0 V, 3 PNP heartbeat to WD1, 4 PNP raw panel OK to KPS coil 1, 5 +24 V HOST feedback drive from the KS1/KS2 auxiliaries and independent HOST contact.

Use 26 AWG with 0.76–1.2 mm jacket OD for the ZE logic loom. PH contacts
accept 24–28 AWG at roughly 0.9–1.5 mm insulation OD. Use 22 AWG, with
1.7–3.0 mm OD insulation, for the specified VH contacts. Use 24 AWG flexible
wire and the correct terminal preparation for the J31 screw plugs.
Cable engineering must satisfy the specific connector and field rating.
Install tie-downs at each enclosure boundary to prevent pulling on the headers.

J2, J3 and J4 have distinct mating housings. J36 and J31 retain the intentional
one-to-one connection to their main-board counterparts. Keep the logic loom
short, inside the cabinet, and away from contactor wiring. Use 300 mm as the
prototype maximum J36 run and verify the actual cable with contactor and radio
switching. Route J4 with its own 0 V return, away from the CT, mains and
capacitor circuits. J31 remains electrically isolated from the cabinet rail.

KPS coil terminal 0 returns to cabinet 0 V at the cabinet. Fit a 1N4007
**at that remote coil**, band to terminal 1, in addition to the receiver
clamp D3. KFB1's local clamp D6 is on this PCB. J4.5 energizes KFB1 only
after both motor contactors physically pick up in HOST. Releasing either
contactor, moving to LOCAL, or losing the guard's 24 V opens J31. Never
power drive J4.5 from a lasting 24 V rail. The factory regulator supplies
the logic island through J3. Leave its return isolated from cabinet 0 V
and protective earth. The receiver has no motor or mains terminals.

Supply and driver limits
------------------------

Set the cabinet rail to 24.0 V. Commission it within 22.8–25.2 V at J4.1
with the coils switching and the longest installed cable. The upper bound
leaves margin below D7's 26 V continuous standoff. At 23 °C the selected
four-pole G7SA panel relay has a 1.60 kΩ coil, ±15%. This represents
approximately 12.4–18.5 mA over the stated rail range before cable and
driver drops. Verify voltage directly at the coil and prove pickup and
release at the installed temperature limits.
`Omron G7SA coil data <https://www.ia.omron.com/products/family/386/specification.html>`_
and `Vishay SMBJ data <https://www.vishay.com/docs/88392/smbj.pdf>`_.

At 25 °C, a 4.75 V logic supply and resistor tolerances give at least
4.53 V on the active MOSFET gate before device leakage. Budgeting 1.65 V
for the optocoupler LED and 5.3 Ω for the 2N7002 gives at least 5.42 mA
through the LED. The VO617A-3 specifies 100% minimum current-transfer
ratio at 5 mA and 5 V across its phototransistor. At the high 25.2 V rail
the 10 kΩ output-drive resistor draws at most 2.55 mA even with its
1% tolerance and zero junction drops. These calculations establish a room-
temperature drive budget. Include hot/cold optocoupler gain, off leakage,
the actual WD1 input current and remote-coil flyback in commissioning.
`Nexperia 2N7002 data <https://assets.nexperia.com/documents/data-sheet/2N7002.pdf>`_
and `Vishay VO617A data <https://www.vishay.com/docs/83430/vo617a.pdf>`_.

Mounting and validation
-----------------------

Use four insulating M2.5 standoffs. The four 2.7 mm nonplated mounting holes
are on a 62 × 42 mm pattern with each centre 3 mm from its adjacent edges.
Allow separate clearance for the side-entry cables and the top-entry J2/J3
plugs. Both layers are reserved for the two extra-low-voltage domains.
Keep the clearance corridor clear of metal mounting hardware and cable clips.

The released layout uses 0.25–0.80 mm tracks with 0.85 mm copper / 0.40 mm
drill vias. The independently measured minimum projected separation between
the isolated and 24 V copper is 3.10 mm including the ground pours. Native
KiCad checked all 115 netlisted pads. Nominal geometry checked all 65 drilled
features against SMT solder-mask openings. These are prototype design
measurements before fabrication/registration tolerances.

U1's positive supply pin reaches the 100 nF capacitor on a 3.05 mm
top-layer path. U1 and the capacitor connect to the isolated return plane
through local vias 0.90 mm and 1.27 mm from their respective pad centres.
J4.1 reaches the 24 V TVS on a 4.32 mm long, 0.80 mm wide top trace.
The TVS ground pad reaches its own cabinet-plane via in 1.70 mm.
Both flyback clamps have 1.50 mm returns. These are measured copper lengths.
Surge clamping voltage, ringing and release times require bench measurements.

The `native KiCad project <guard-receiver.kicad_pro>`_, `BOM <bom.csv>`_,
`ERC <checks/erc.json>`_, `routing/parity report <checks/drc.json>`_ and
`geometry audit <checks/geometry.json>`_ accompany the prototype. The `assembly positions <assembly-positions.csv>`_,
`top assembly drawing <assembly-top.svg>`_ and
`pin-by-pin schematic <receiver-schematic.pdf>`_ identify the populated parts.
The reviewed router session is saved beside the PCB.
Confirm actual supply levels, cable dropout, contact wetting and guard release
times at temperature. Test low, high and in-band interference on the open or
frozen heartbeat wire. A legitimate-looking in-band waveform still requires
physical immunity testing. The two independent physical trip switches continue
to interrupt the motor permission even with a falsely asserted HOST-health input.

`JST ZE <https://www.jst.com/wp-content/uploads/2025/06/eZE.pdf>`_,
`PH <https://www.jst-mfg.com/product/pdf/eng/ePH.pdf>`_,
`VH <https://www.jst-mfg.com/product/pdf/eng/eVH.pdf>`_ and
`Phoenix MC mating connector <https://www.phoenixcontact.com/en-gb/products/pcb-plug-mc-15-2-st-381-1803578>`_.

Prototype fabrication
---------------------

Use the `GUARD-RX-A bare-board Gerbers and drills <guard-receiver-rev-a-gerber-prototype.zip>`_
for the receiver. Select a two-layer, 68 × 48 mm board with green solder mask.
The `paste layers for a stencil <guard-receiver-rev-a-stencil-prototype.zip>`_
are a separate upload. The `CAM package checks <checks/cam-package.json>`_
record the source hash, outline, native pin/net and drill comparison, and archive
checksums. Electrical performance requires the populated cabinet tests.
