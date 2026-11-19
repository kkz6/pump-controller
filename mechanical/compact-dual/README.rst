Standalone case for the dual-output main board
=============================================

The starter button cable enters the **right wall** through its own M20 gland.
Two removable plugs face it directly, J30 for output A and J35 for output B.
A separate entry on the near wall carries the isolated manual-transfer position
signal to J36. The top-view drawing shows which wall is near. The steel starter
and the capacitors, contactor, overload, and original operator buttons stay in
their original cabinet.

* `Cable-entry drawing and full-size right-wall template <../../output/enclosure-compact-dual/wire-entries.pdf>`_
* `Top-view preview <../../output/enclosure-compact-dual/wire-entries.png>`_
* `Five-button lid preview <../../output/enclosure-compact-dual/five-button-panel.png>`_,
  `complete five-button print set <../../output/enclosure-compact-dual/compact-dual-five-button-print-parts.zip>`_
  and `full-size front labels <../../output/enclosure-compact-dual/front-label-template.svg>`_.
* `Starter contact wiring drawing <../../hardware/main-compact-dual/exports/starter-wiring.pdf>`_
  and `terminal assignments and supported profiles <../../hardware/main-compact-dual/README.rst>`_

Starter cable
------------

The M20 opening is 20.1 mm in diameter, centred 91.0 mm from the near wall
and 29.5 mm above the underside. The wall fits LAPP SKINTOP ST-M 53017030
(long M20 × 1.5 thread, 13 mm, 24 mm spanner) and locknut 53119020
(27 mm spanner, 29.7 mm across corners, 6 mm thick). Its 5–12 mm clamping
range applies to the **outside of one round, continuous jacket**. Verify the
finished bore measures 20.0–20.2 mm. Dimension the jacket, insulation,
conductors, ferrules and gland for the actual starter control circuit. This
is a pilot cable. The one-horsepower motor current stays in the starter.
`LAPP gland data <https://products.lappgroup.com/online-catalogue/cable-glands/skintop-cable-glands-plastic-metric/standard/skintop-st-m.html>`_,
`locknut data <https://www.lapp.com/en_US/us/skintop-gmp-gl-m/p/53119020>`_,
`mounting-hole tolerance, LAPP T21 <https://products.lappgroup.com/fileadmin/catalog/en_T_pdf/T21_Thread_dimensions_for_cable_glands_int.pdf>`_.

=============  ===============================================================
Cable cores    Starter cable assembly
=============  ===============================================================
Two            One maintained RUN pair. Locally link J30.2 to J35.1 in the
               removable harness and carry J30.1 and J35.2 to the starter.
Four           Carry J30.1, J30.2, J35.1 and J35.2 separately, as two pairs.
Three          Use only a manufacturer-documented shared common for the two
               inputs of the same starter. Fit a covered splice in the harness
               for the common and carry two separate signal cores.
=============  ===============================================================

Both board headers have pin 1 COM and pin 2 NO. Use a professionally terminated
loom marked A and B at both ends. Where a branch needs a splice, keep the
splice enclosed and allow one correctly prepared conductor per plug cavity.
Route the jacket into the case before fitting the removable screw plugs.
Leave enough free length for unplugging without pulling on screws, moving
the gland or exceeding the cable maker's bend radius. Bring the independent
HOST/LOCAL position-sense jacket through TRANSFER SENSE. The keyed manual
transfer insert remains accessible at the starter with both energy sources
isolated. Confirmed HOST feedback is required for controller operation.

**Physically code the two plugs.** Use two Phoenix Contact 1836189 headers,
two 1836079 removable mating plugs and two individual CP-MSTB coding elements
from 1734634. Prepare A at pole 1 and B at pole 2 using the manufacturer's
paired coding tab/profile method. Preserve the unselected coding feature on
each pair. Identify poles by pin number when the halves face each other.
With all supplies isolated, check each intended pair seats, each crossed pair
stops before contact, and the harness has the required end-to-end continuity.
This two-way rejection test is pending on real parts.
`Phoenix header/accessory datasheet <https://www.farnell.com/datasheets/2322501.pdf>`_,
`Phoenix exact plug coding description <https://docs.rs-online.com/07f7/0900766b812c6820.pdf>`_.

Mounting and assembly
---------------------

The case body is 170 × 150 × 90 mm with the lid installed. Buttons, glands,
antenna and cable bend space extend beyond it. The main PCB is 100 × 97 mm
and sits 20 mm above the inside floor with output headers facing right.
Four corner supports and a fifth support H5 beside the output plugs take the
connector insertion load. Use M3 insulating fasteners, an insulating washer
within the 8 mm boss diameter, and a head within the underside recess
(6.4 mm diameter, 3.0 mm deep). Check actual fastener length and clearance.
Four independent internal M4 mounting points accept wall anchors. Fit all
mounting hardware or seal the penetrations for the intended installation.

Mount the board and its wired plugs with supplies isolated. Secure the guard
on its four independent M3 supports and captive nuts, arranging the dressed
cores in their individual lower-edge notches. Seat each jacket in its gland.
Bring the panel loom from J32 through the near guard notch to the OLED panel
on the lid. Provide a service loop and support the lid while unplugging it.
Retain the panel with four M2.5 fasteners, the OLED and 38 × 16 × 1 mm clear
window with the retainer, and the lid with four M3 fasteners.

Five panel buttons
------------------

From left to right the panel carries **START, STOP, MODE, SET/RESET and NEXT**.
The default lid uses the original 60 × 45 mm Rev E panel, with its STOP
microswitch actuator at panel x = 20 mm. Its solder-footprint origin is
1.83 mm to the left of the actuator. All five bore, stem and switch centres
are checked against the native panel and the assembled lid. The panel STOP
contact operates the controller's hardware permission path. Keep the starter's
original hardwired STOP and overload effective as specified in the starter
wiring drawing.

The stems and top caps are separate printed pieces. Each stem can pass up
through its 6.5 mm lid bore before the top cap is fitted. Its 8 mm shoulder
retains it under the lid. Use **one M2 × 6 mm, 90° countersunk machine screw
and one ruthex RX-M2x4 heat-set threaded insert per button**. Each cap has a
2.2 mm clearance bore and a 4.3 mm nominal top countersink. The matching
stem has a 3.2 mm diameter, 5 mm deep insert pocket. Heat-set all inserts
flush into the stems away from the electronics. The body through the lid is
6.2 mm in diameter. Verify the finished bore and free sliding on the print.
Trim the overlay’s common row opening so all five cap shoulders land on
the bare lid. Install stems from below with the panel removed, place the overlay,
secure each cap from above with the screw head flush, and then install the
panel assembly. Match the STOP stem to the individually labeled STOP cap.
The five-button print set supplies each identified stem and cap separately.
If the chosen printing process cannot accept this insert, use a
supplier-approved compatible insert/fit and repeat the dimensional check.
`ruthex RX-M2x4 insert and bore drawing <https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf>`_.

The nominal rest gap is 0.15 mm. STOP has 0.85 mm maximum button travel
(0.70 mm after the gap). The four tactile buttons have 0.40 mm travel
(0.25 mm after the gap). These allowances depend on assembled switch free
height, print tolerances and the tightened lid. Verify repeatable switching
and return, no preload and no actuator bottoming with each actual switch.
The controller's panel STOP and the original starter STOP must both pass a
functional test. The `native panel and electrical wiring guide
<../../hardware/panel-rev-e/README.rst>`_ identifies the optional button and
key sockets as well as the hardwired NC panel STOP.

Optional maintained AUTO/MANUAL key
----------------------------------

Install the 44 × 44 mm solid blank for the normal lid. The interchangeable
adapter takes a key through a **22.5 mm bore** with **5.2 mm** material
at the centre. Four M3 fasteners retain either plate. Under the lid's 34 mm
square service opening, the CAD reserves 35 × 35 × 25 mm for the assembled
key body and measures 7.8 mm from that reservation to the guard. Check the
barrel, nut, anti-rotation feature, acceptable clamping thickness, terminal
boots and wire bend against the actual key. For a deeper key, use its own
remote station and the dedicated M12 **MODE KEY** entry at x = 93 mm,
z = 68 mm on the near wall. That passage feeds the space above the guard.
Blank it when unused. The button mode toggle also works without a fitted key.

The optional gold-contact, maintained, break-before-make SPDT selector uses
**panel J8.1 common (+5 V), J8.2 MANUAL, J8.3 AUTO**. Select contacts for the
approximately 2.7 mA load and use a three-core jacket if it leaves the case.
Use either a lid selector or a remote selector on J8. A separately enabled
maintained key takes precedence over MODE. **Main J36** serves the independent
physical HOST/LOCAL transfer at the starter, through the TRANSFER SENSE entry.

The far wall takes the AC supply. The left wall takes the captive mains-
referenced CT cable, tank cable and inlet cable through separate glands. A
fixed divider separates the CT entry from the probe entries. The near wall
takes the optional float, the transfer feedback, remote mode key and antenna bulkhead.
Select glands that match each installed jacket or fit closed blanking plugs.
The CAD allows a 29.7 mm maximum M20 locknut corner diameter, 24.2 mm for M16
and 18.7 mm for M12. Check each gland's panel stack and exterior tool access.
The M12 spaces allow at most 9.5 mm thread length including the 3.2 mm wall.

Fit and reproduction
--------------------

The native PCB supplies all five mounting centres and the connector pad
locations. Interference checks cover the printed base, PCB guard, lid parts,
populated KiCad STEP solids including the project body envelopes for the power
supply, varistor, relays and other packages, both plug envelopes, plug extraction and tool
access, and the gland barrel and locknut envelopes. With the guard removed,
each plug has 8 mm of checked withdrawal plus a further 14.9 mm to the outer
wall. Each installed plug envelope clears the guard by 6.1 mm. Actual wire
dress, bend radius, insertion force, gland retention, enclosure material,
finger access, ingress protection and electrical qualification require a first
article. The printed assembly has no established rating for mains installation.

`Body and connector checks <../../output/enclosure-compact-dual/fit-checks.json>`_,
`populated STEP fit <../../output/enclosure-compact-dual/populated-fit.json>`_,
`print-part hashes and lid fit <../../output/enclosure-compact-dual/print-manifest.json>`_.

``base.step`` and ``main_board_guard.step`` use the case assembly origin.
The print ZIP contains seventeen individually oriented STLs in mm. Print
sixteen pieces for an assembly, selecting either the blank or the optional
key adapter. The retained lid, panel carrier, display retainer and both
key plates with their original STEP shapes and transforms are frozen in
``five-button-lid.zip``. The ten movable button pieces come from
``panel_controls.py``. To
regenerate from the project root with the KiCad and OCP environments installed::

  .tools/3d-modern/bin/python mechanical/compact-dual/build.py --board hardware/main-compact-dual/pump-controller-compact.kicad_pcb
  .tools/3d-modern/bin/python mechanical/compact-dual/check_assembly.py hardware/main-compact-dual/pump-controller-compact.kicad_pcb output/enclosure-compact-dual
  .tools/3d-modern/bin/python mechanical/compact-dual/package_print.py output/enclosure-compact-dual
  .tools/3d-modern/bin/python mechanical/compact-dual/draw.py output/enclosure-compact-dual
