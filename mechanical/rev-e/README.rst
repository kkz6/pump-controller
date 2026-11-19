Rev E enclosure and mounting prototype
======================================

This is a separate enclosure for the controller when the existing DOL starter
has insufficient space. The case body is 170 x 150 x 90 mm. The front controls,
key blank and purchased cable glands project beyond that body. The controller
main PCB is 100 x 80 mm, and the separate OLED/button panel is 60 x 45 mm.
Neither this enclosure nor its dimensions establish fit inside an existing
starter. The original contactor, capacitors and overload protection stay in the
starter; they are not components of this enclosure.

The CAD solids are supplied as STEP and individually oriented STL parts under
``output/enclosure-rev-e``. ``assembled.step`` contains the full mechanical
assembly and reference electronics. ``assembled.glb`` and ``exploded.glb`` are
viewing models; ``viewer.html`` is an offline rotate/zoom viewer. ``manifest.json`` identifies each part, quantity, dimensions,
file checksum and its assembly transform. STL numbers are millimetres; glTF
viewing files use metres and Y-up as required by that format.

Design status
-------------

The printed parts are mechanical prototypes. They are not a certified mains
housing, a flame-rated assembly or an ingress-rated enclosure. The wire
openings and display/button interfaces have no claimed finger-access or IP
rating. A separate full-board cover is provided to retain a physical barrier
when the lid is removed, but it does not establish an electrical safety rating.
Keep the existing starter and this controller isolated from power during
assembly, adjustment and service.

The main component-space allowance is 22 mm above the PCB, including the
20 mm MOV allowance used by the earlier mechanical model. It is deliberately
larger than the 16.7 mm PSU body. Each final rebuild imports the populated
main STEP and binds it to the checked native PCB's checksum. Rerun this review
after any native PCB or model change. Actual mating plugs still require
measurement. The panel geometry
comes from the frozen native Rev E STEP, with separately modeled D2F/OLED
allowances for parts not present in that STEP. The missing PH4 J7 connector
uses its native fabrication outline and an explicit 8 mm rear-height allowance;
this is an engineering reserve, not an exact manufacturer body model.

Mounting and retention
----------------------

* Main PCB: four M3 clearance holes at native board coordinates (4,4), (96,4),
  (96,76), (4,76) mm. Integral insulating standoffs are 18 mm tall, with 4.4 mm
  nominal clearance below the 13.6 mm underside model allowance. This
  includes the exported surface offset and rear-mounted C1's 12.5 mm maximum
  can with a maximum 1 mm mounting gap. Its 6 x 6 mm modeled XY envelope includes the 5.5 mm maximum diameter
  and 0.25 mm installation allowance on each side. Trim its leads to at most
  3 mm above the opposite board face. The actual
  native main STEP bounds and underside depth are recorded in fit-checks.json.
  Use nylon screws, washers and nuts; retain the full 4.2 mm copper keepout
  radius around every main mounting hole.
* Main guard: separate four-point screw fixing to base bosses. It covers the
  whole main board and has separate wire paths for the mains/coil, live CT,
  sensor and panel harnesses. Its internal roof is 3.4 mm above the current
  22 mm main component allowance. No guard fixing depends on a PCB component
  or a cable for support.
* Panel: four M2.5 fasteners at native coordinates (3,3), (57,3), (3,42),
  (57,42) mm. The carrier's corner columns support the PCB; the carrier is
  separately secured to four lid posts. Its rails allow 10.2 mm below the
  PCB rear plane, compared with the native panel's 8.625 mm largest modeled
  rear projection. This does not include every possible mating connector.
* OLED: Waveshare 14657, 36 x 12.5 mm PCB, with a PH2.0 four-position socket.
  A screw-fastened rear retainer supports its PCB edges. Separate retainer
  fingers hold the clear window; the window is not loaded against the OLED
  glass. The center of the PCB remains open for rear electronics and its plug.
  A purchased 38 x 16 x 1 mm clear window is shown; do not print it in opaque
  material. Verify the actual glass offset, PCB thickness, rear parts and
  bearing locations on the received OLED before final retainer production.
* Buttons: all five caps are captive between lid and panel. STOP has its own
  shorter stem for the D2F. The other four use the B3U stem. Positive shoulders
  limit nominal cap motion to 0.85 mm for STOP and 0.40 mm for the tactile keys.
  These are prototype fit settings, not validated actuation tolerances.
* Cable clamps: five screw-retained saddles support the mains, coil, live-CT,
  probe and auxiliary bundles. Nominal saddle diameters are 9/9/7/9/7 mm.
  Use compatible soft liners and check actual cable diameter and retention;
  these printed clamps are not a certified cord anchorage.
* Case: four internal M4 wall-mount positions, plus four independent M3 lid
  fasteners with side-loading captive nuts. Use suitable external wall anchors
  for the mounting surface. No enclosure wall screw passes through a PCB.

Native KiCad coordinates increase down the board drawing. Mechanical CAD is
right-handed and Z-up, so native Y is reflected about the board height when
positioning it in the enclosure. The main origin is (35,37) mm and the panel
origin is (55,45) mm at their lower-left CAD corners. Hole coordinates and
calculated clearances are included in ``fit-checks.json``.

Connectors and cable entries
----------------------------

The main's left edge carries the incoming power and coil-control connections.
The bottom-left live-CT cable has its own gland, physically separate from the
isolated probes and auxiliary inputs on the bottom-right. A molded divider in
that external wiring vestibule preserves their routing separation. The
12-position panel cable exits the main's isolated right side. Do not route
mains or live-CT conductors through the panel compartment.

J10 is a fixed Phoenix 1727010 terminal, with the CT lead terminated during
assembly and retained by the live-CT clamp. No removable CT plug is used;
this prevents its insertion into an isolated sensor socket. Support the
terminal housing while tightening its screws. Its 8.5 mm installed body
height fits within the main-board height allowance. The populated STEP used
for final enclosure fit review must include this fixed terminal.

Candidate entries are 20.5 mm holes for the mains, coil and probe glands, and
16.5 mm holes for the live CT and auxiliary glands. These suit an initial
M20/M16 gland selection only. Confirm the purchased gland's specified mounting
hole, thread length, nut diameter, cable range and required wall thickness
before printing. Install appropriate blanks in unused openings. The case does
not acquire a gland manufacturer's IP rating merely by fitting that gland.

The panel has outward-facing connectors: GH12 host at the top, five GH2
external-button connectors at the bottom, GH3 key at the left, and PH4 OLED
at the right. Leave 15 mm outside those PCB edges as an initial plug/wire-bend
reservation; validate with the actual plugs and cable gauge. The OLED uses a
preassembled PH2.0 harness with verified pin-to-pin continuity. No OLED soldering
is required by the user. The cable must follow the electrical pin map, not
unverified cable colors. A separate isolated-side guard opening and a provisional 6.5 mm right-wall
bulkhead aperture reserve an RF-coax route. Confirm the selected antenna
connector mounting drawing and cap an unused hole.

The lid is removable, not hinged: support it while
unplugging the panel cable, and do not hang it from the cable.

Optional maintained key
-----------------------

Fit ``key_blank_plate`` by default. ``key_22p5_adapter_OPTIONAL`` is an
alternative with a 22.5 mm bore; do not install both. The reserved internal key
body is 35 x 35 x 25 mm beneath the lid. There is 9.8 mm nominal clearance from
that depth reservation to the main guard roof. An unspecified key may need a
different bore, anti-rotation notch, panel thickness or a deeper case. Verify
its manufacturer's drawing before replacing the blank.

Hardware allowance
------------------

The quantities below are a starting assembly allowance. Verify actual screw
engagement, head and washer diameters with the printed first article; no screw
may project into a component or across the live/isolated separation.

============================= ======== ======================================
Position                      Quantity Initial hardware
============================= ======== ======================================
Main PCB                      4        M3 x 25 nylon, nylon washers/nuts
Main guard                    4        M3 x12 nylon, captured nuts; trim flush
Case lid                      4        M3 x12, washers and captured M3 nuts
Panel to carrier              4        M2.5 x16, washers and captured nuts
Carrier to lid posts          4        M3 x10, side-loaded captive M3 nuts
OLED retainer                 2        M2.5 x8, side-loaded captive nuts
Optional-key blank/adapter     4        M3 x10, washers/nuts
Five cable clamps             10       M3 x12, washers/captured nuts
Wall mounting                 4        M4 hardware to suit mounting surface
============================= ======== ======================================

Print and first-article checks
-----------------------------

Use ``parameters.json`` to change dimensions, retaining the frozen PCB hole
patterns. The build script uses OpenCascade solid booleans and exports true
STEP geometry. The mesh check verifies each printable part is a valid BREP,
one connected solid, watertight, consistently wound and nonzero in volume.
The geometric interference check covers all simultaneously fitted printed
parts and the native populated panel/main, OLED PCB/glass and clear window.
The optional key plate is excluded when the blank is fitted. A 15 mm outward/10 mm deep provisional panel plug reservation is checked
against printed parts for every connector. These checks
cannot replace a measured assembly fit or verify switch contact behavior.

STLs are already oriented with the base bottom down, the lid front down, the
guard roof down, and button heads down. Inspect the slicer orientation and
supports; do not scale parts to fit a printer. Captive nut slots and cable
saddle roofs may need process-specific supports or cleanup. Keep paint and
coatings out of sliding bores, mating lips, nut traps and clamp bearing faces.

Check these critical fits before populating the main board or applying power:

1. Measure the main and panel hole patterns, standoff heights and screw
   clearances. Insert nuts before closing inaccessible pockets.
2. Verify the 0.4 mm-per-side lid locating clearance, M3/M2.5 screw passages,
   clamp and gland holes, and the key blank's 0.3 mm-per-side spigot clearance.
3. Check each plunger slides freely in its 6.5 mm bore. Adjust its stem length
   to obtain clearance at rest and reliable actuation before its shoulder hits
   the lid. No cap may preload a switch. STOP's 7.5 mm free-height parameter
   is a fit allowance, not a guaranteed D2F dimension: its published operating
   position uses the switch drawing datum. Measure the assembled switch.
4. Confirm STOP opens and returns reliably through repeated full cycles;
   similarly verify the other four contacts. Reject a binding or overtraveling
   assembly. Do not use the printed cap to force an incorrect stack height.
5. Fit the actual OLED and its plug without pressing the glass or rear
   components. Confirm the window is retained separately and the display
   remains visible through the aperture.
6. Fit all mating plugs with latch access, strain relief and service slack.
   Inspect final closure without squeezing wires or crossing the isolation
   corridor. Keep RF antenna and cable routing clear of mains conductors.
7. Validate temperatures in the closed final assembly, especially the supply
   and continuous preload resistor; the electrical design currently requires
   local PSU ambient no greater than 50 degrees C. Material suitability,
   insulation, EMC and the complete mains installation remain separate work.

Robu service reference
----------------------

https://robu.in/product/3d-printing-service1/

https://robu.in/3d-printing-guide/

On 19 November 2026 the guide accepts STEP/STP, STL, OBJ and 3MF, and identifies
STEP as its preferred geometry format. Its displayed material lists, build
limits, wall limits and tolerance values were not populated. Therefore no
specific Robu material, process, build-envelope acceptance or printing
accuracy is asserted here. Submit the individual STEP/STL parts for a quote
with the critical fits above, and obtain the process/material details before
releasing prints intended for anything beyond isolated mechanical trials.

Component references
--------------------

* Waveshare 14657 dimensions and PH2.0 connector:
  https://www.waveshare.com/product/ai/displays/oled/0.91inch-oled-module.htm
* Omron D2F dimensions and operating travel:
  https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf
* Omron B3U dimensions:
  https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf

Rebuilding the deliverables
--------------------------

After fresh independent native checks pass, select the exact final main PCB
checksum and run the complete export/fit pipeline::

  .tools/3d-modern/bin/python mechanical/rev-e/refresh_final_outputs.py --expected-board-sha256 <selected-PCB-SHA256>

Adding ``--check-only`` verifies source/evidence freshness without exporting
or changing any deliverable. The full command exports the visualization copy,
records main STEP/GLB provenance, then runs these mechanical stages::

  .tools/3d-modern/bin/python mechanical/rev-e/build_enclosure.py
  .tools/3d-modern/bin/python mechanical/rev-e/render_previews.py
  .tools/3d-modern/bin/python mechanical/rev-e/build_label_template.py
  .tools/3d-modern/bin/python mechanical/rev-e/build_viewer.py
  .tools/3d-modern/bin/python mechanical/rev-e/package_outputs.py

The native PCB and project are read-only throughout. The builder requires
``hardware/3d/rev-e-export-manifest.json`` to match the current main PCB,
native evidence and both model files. ``fit-checks.json`` records those
checksums, the panel connector-manifest PCB hash and actual main body bounds.
Packaging checks every individual STEP/STL checksum and ZIP member, and the
pipeline seals final output checksums in ``final-output-verification.json``.
Any model/enclosure collision or source change refuses the final package.
The required local libraries are OpenCascade/OCP, NumPy, trimesh, networkx
and Pillow. Visual review and physical fit tests remain separate.
