Rev E prototype PCB fabrication
================================

**100 x 80 mm main board on hold.** The optional AUTO key is connected to
MCP23017 GPB7. Microchip restricts this pin to output use because transitions
during reads can corrupt the shared I2C bus. The Rev E Gerbers and test records
below preserve the historical layout. Use the corrected compact design for
further engineering. See the `Microchip pin advisory
<https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_.

Order the main PCB and control panel as two separate designs. Do not combine
their Gerbers into one board upload. The standalone enclosure is a separate
3D-printing job. The fabrication manifest and independent check results must
refer to the exact files in the chosen archive.

Main board settings
-------------------

* Finished outline: 100 x 80 mm; six copper layers; 1.6 mm thickness.
* Copper order: GTL / G2L / G3L / G4L / G5L / GBL, corresponding to
  F.Cu / In1.Cu / In2.Cu / In3.Cu / In4.Cu / B.Cu.
* Green solder mask on both sides; white legend; 1 oz outer and 0.5 oz inner
  copper; ENIG finish; FR4 Tg155 or a confirmed equivalent offered by Robu.
* Standard plated through vias only. Nominal vias are at least 0.65 mm
  diameter with 0.30 mm drills; no filled/capped via-in-pad process required.
* Four non-plated 3.2 mm mounting holes. Keep the separate NPTH drill file.
* Request bare-board electrical testing against the supplied IPC-D356 netlist.
* At K1 and K2, the nominal distance between the edges of contact pad 2
  and coil pad 1 is 8.06 mm. The project target is 8.00 mm minimum. Obtain
  the fabricator's final copper tolerance and any pad edits, then inspect the
  finished first article. The assembly review must also include leads and solder
  fillets at these same positions.

Control panel settings
----------------------

* Finished outline: 60 x 45 mm; two copper layers; 1.6 mm thickness.
* GTL / GBL; green mask, white legend, 1 oz copper, ENIG finish.
* Four non-plated 2.7 mm mounting holes. Keep the separate NPTH drill file.
* This board carries isolated low voltage only. It uses the GH12 host harness,
  five optional GH2 external-button connectors, GH3 key and PH2.0 OLED socket.

The PCB vendor's process offerings can change. Match these actual settings in
the quotation; do not silently substitute 2 oz copper, a different mask colour,
blind vias or a different drill/pad process. No exact dielectric ply schedule
or controlled impedance stackup is assumed or supplied. The proposed six-layer
dielectric construction requires confirmation by the fabricator before an order.

File roles
----------

GTL/GBL and G2L/G3L/G4L/G5L are copper, GTS/GBS mask, GTO/GBO legend, GKO/GM1 the
finished outline. PTH and NPTH Excellon files are metric, absolute and
unmirrored, with the same origin as every Gerber layer. The gbrjob file records
layer roles and finished dimensions. D356 is the board electrical-test netlist.
Drill maps are visual aids, not replacements for Excellon data.

Paste layers GTP/GBP are in separate stencil archives; do not treat them as
PCB copper. Component placement, BOM and assembly drawings belong to the
assembly package. PCB manufacture alone does not fit the sockets or components.

Checks and their scope
----------------------

Native KiCad ERC, DRC, schematic/PCB parity and unconnected-item checks must all
pass. Independent geometry additionally checks the conservative Robu pad,
track, via and hole dimensions; every drill against SMT solder-mask openings;
true mounting-hole clearance; live/isolated net domains on all copper layers;
and the local R2 heat-spreading area. Injected 7.9 mm / 8.1 mm test pairs confirm
that the 8 mm isolation rule actually triggers at the intended boundary.

Independent CAM parsing checks the exported layers, closed outline, holes,
IPC pin/net mapping and actual solder-mask webs. It does not reconstruct a
conductive CAM netlist from copper polygons. The fabricator's electrical test
and first assembled board tests remain necessary.

This is a bare-PCB engineering prototype package, not a released mains product.
Firmware, assembled electrical performance, insulation qualification, thermal
rise, contactor compatibility and electrical-noise immunity are not established
by successful CAD checks. The 3D-printed case is a mechanical prototype and
has no claimed electrical enclosure, fire or ingress rating.

Primary process references
--------------------------

* https://robu.in/product/online-pcb-manufacturing-service/
* https://robu.in/pcb-manufacturing-capabilities/
* https://robu.in/pcb-file-preparation/
* https://robu.in/product/3d-printing-service1/
* https://robu.in/3d-printing-guide/
