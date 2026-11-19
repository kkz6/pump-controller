Fabrication review files
========================

The selected PCB service is Robu. The main-board package is **for engineering
review only**. It is not an approved manufacturing order. No board has been
ordered or physically tested.

Main board: Rev C
----------------

``rev-c/board/`` contains nine Gerber X2 layers, the Gerber job file, separate
plated and nonplated Excellon drills, and an IPC-D-356 electrical-test reference.
``rev-c/drill-maps/`` contains drill drawings and the tool/count report.
``rev-c/stencil/`` contains the two paste layers separately from the bare-board
data. Paste apertures still need assembly-process review.

The PCB is 90 x 70 mm, four copper layers, 1.6 mm nominal thickness. All files
use the same absolute origin. Nothing is mirrored. Copper order is GTL, G2L,
G3L, GBL. There are 381 plated holes and two nonplated holes. The native
filenames retain ``rev-b``; their content and title blocks identify Rev C.

The finished outline is its 90 x 70 mm centreline. KiCad's job-file Size field
includes the 0.05 mm outline stroke and reads 90.05 x 70.05 mm; do not use that
stroke-inclusive value to enlarge the manufactured board.

For the separate Rev D panel assembly, leave main-board SW3 and SW4 unpopulated.
Their functions move to the panel through J32.6 and J32.4. This population
choice does not change the main-board copper or Gerbers. Use the panel harness
document rather than the earlier instruction to leave those pins reserved.

Robu quotation settings
-----------------------

These are requested settings for review, not accepted production parameters:

* FR-4, four layers, one design, individual routed 90 x 70 mm boards.
* 1.6 mm thickness; 1 oz outer / 0.5 oz inner copper.
* Green mask, white legend, ENIG finish; Tg155 material proposed.
* No impedance-control claim, blind vias, buried vias or V-scoring.
* Smallest nominal drilled hole 0.20 mm. Separate PTH and NPTH files supplied.
* Request electrical testing against the supplied IPC netlist and a comparison
  with the connectivity extracted from the manufacturing artwork.

The native project specifies overall thickness, but has no qualified dielectric
stackup, copper weights, laminate/CTI or finish. The settings above must be
confirmed with the fabricator. They do not certify the mains insulation system.

Items preventing a manufacturing release
----------------------------------------

Read ``robu-dfm-audit.rst`` and its coordinate-level JSON companion. In
particular, the current board has small via annuli, zero pad-mask expansion,
small legend features and spacing that needs Robu-specific resolution.
Robu's published via/PTH clearance and annulus entries are not fully consistent;
the audit records both plausible interpretations instead of declaring vendor
acceptance from the general KiCad result.

Sixteen routing vias intersect nineteen SMT pads. These need filled and
plated-over treatment or rerouting. The board currently encodes ordinary via
tenting, not filling/capping. Two additional U2 thermal holes also need assembly
review. Do not substitute tenting for the required treatment. Robu's public
capabilities do not establish that this filled/plated-over service is available.

Do not allow automatic enlargement of holes/pads or deletion of copper to
resolve these items without checking the revised data against the circuit and
the retained 8 mm live-to-isolated design corridor.

Verification
------------

``rev-c/checks/`` contains fresh KiCad electrical and layout reports, a
read-only comparison of the native board and schematic with the circuit source,
and an independent Gerber/drill parser check. ``manifest.json`` records source
and exported-file hashes. The original CAD was not changed by the export.

The electrical-rule check and native layout-rule check have zero violations;
there are zero unrouted connections. The source comparison covers 208 electrical
components and 606 connected schematic pins. The full native schematic-parity
check separately reports 235 findings: 199 description-field differences,
34 intentionally unused pins represented differently, and two mechanical
mounting footprints absent from the schematic. This parity check is not a
zero-finding result. All connected pins match the circuit source.

Gerber parsing checks format, layer mapping, the closed 90 x 70 mm outline,
drill coordinates/counts and the IPC pin/net reference. It does not extract
conductive connectivity from the Gerber copper. Native DRC, IPC generation and
an artwork preview do not replace fabricator CAM analysis or bare-board testing.

The controller still requires independent circuit/footprint review, insulation,
thermal and EMC testing, firmware, and verification of the actual starter's
coil and capacitor-start circuit before installation.

References
----------

* Robu order service: https://robu.in/product/online-pcb-manufacturing-service/
* Robu capabilities: https://robu.in/pcb-manufacturing-capabilities/
* Robu file naming: https://robu.in/pcb-file-preparation/
* KiCad CLI checks/exports: https://docs.kicad.org/10.0/en/cli/cli.html

Manufacturer pages checked 19 November 2026. The archive contains the design
data and review notes; it has not been submitted to Robu.
