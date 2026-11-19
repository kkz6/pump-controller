Compact single-phase pump controller
====================================

The current **compact main board measures 100 x 75 mm**, with a modeled
populated thickness of 25.68 mm and a separate 60 x 45 mm OLED/button panel.
The compact version moves the power capacitor to the front and corrects
the optional AUTO-key input. See the
`compact PCB, schematic, fabrication files and validation <hardware/main-compact/README.rst>`_.
Physical electrical and thermal qualification and firmware remain pending.

Historical 100 x 80 mm Rev E baseline
-------------------------------------

**100 x 80 mm main board on hold.** The optional AUTO key is connected to
MCP23017 GPB7. Microchip restricts this pin to output use because transitions
during reads can corrupt the shared I2C bus. The Rev E Gerbers and test records
below preserve the historical layout. Use the corrected compact design for
further engineering. See the `Microchip pin advisory
<https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_.

The verified Rev E baseline uses a **100 x 80 mm six-layer main PCB** and a separate
**60 x 45 mm OLED/button panel** to control a 1 HP single-phase pump through its existing DOL contactor.
The design combines local water-level control, motor metering, load-based
dry-run protection and programmable settings. Motor power and the original
capacitor-start circuit stay in the starter.

**Engineering prototype; not qualified for mains installation or unattended
pumping. Firmware and assembled-board testing remain pending.** Both boards have
passing native and independent CAD/export records, including the main's U37/C78
input-conditioning correction. The baseline prototype archives pass their
source and content checks. These records apply only to the historical 100 x 80 mm layout. No manufacturer
acceptance, PCB order or physical qualification is recorded.

Start here
----------

* `Main circuit diagram PDF <hardware/main-rev-e/exports/schematic.pdf>`_.
* `Controller beside the supplied starter <output/rev-e/starter-and-controller.png>`_:
  an installation illustration, not verified terminal identification or proof of fit.
* `Rev E connection overview <output/rev-e/connection-overview.png>`_ and
  `editable SVG <output/rev-e/connection-overview.svg>`_: main/panel connections,
  the direct GH12 cable, OLED, optional buttons/key and retained DOL coil path.
* `Rev E wiring and integration <design/rev-e-integration.rst>`_: exact terminal
  assignments, original-button reuse and outstanding starter checks.
* `Electrical and reset-fault review <design/rev-e-electrical-review.rst>`_ and
  `physical test plan <design/rev-e-bench-acceptance.rst>`_.
* `Preassembled harness order <design/rev-e-harness-order.rst>`_ and
  `unpowered fixture procedure <design/rev-e-unpowered-harness-acceptance.rst>`_
  with its `669-case matrix <design/rev-e-unpowered-harness-acceptance.json>`_.
  Physical results are unrun; they are not CAD test passes.
* `Main KiCad project <hardware/main-rev-e/pump-controller-main-rev-e.kicad_pro>`_
  and `main BOM <hardware/main-rev-e/bom.csv>`_.
  `Capacitor sourcing and installed clearances <design/rev-e-capacitor-sourcing.rst>`_
  specify exact C1/C3/C5 candidates and remaining measurement gates.
* `Panel KiCad project <hardware/panel-rev-e/pump-panel-rev-e.kicad_pro>`_,
  `panel BOM <hardware/panel-rev-e/bom.csv>`_ and
  `panel parts/harness specification <hardware/panel-rev-e/parts-and-interface.rst>`_.
* `Rev E enclosure <mechanical/rev-e/README.rst>`_,
  `assembled preview <output/enclosure-rev-e/assembled-preview.png>`_,
  `exploded preview <output/enclosure-rev-e/exploded-preview.png>`_ and
  `offline 3D viewer <output/enclosure-rev-e/viewer.html>`_.
  `STEP/STL prototype package <output/enclosure-rev-e/enclosure-rev-e-mechanical-prototype.zip>`_
  includes separate printable parts; actual fit and electrical enclosure
  qualification remain required.
* `Wireless architecture <design/wireless-architecture.rst>`_ and
  `variant manifest <design/wireless-variants.json>`_: native Zigbee primary,
  with separate Matter/Thread and Matter/Wi-Fi targets on the same hardware.
* `Programmability <design/programmability.txt>`_,
  `operating contract <design/operation-and-bringup.txt>`_ and
  `OLED timing/harness <design/oled-selection.txt>`_: firmware requirements,
  recovery, settings, re-arm behavior and shared-bus deadlines.

Current verification and fabrication files
------------------------------------------

The main's `independent native summary <hardware/main-rev-e/checks/independent-summary.json>`_
records zero ERC, DRC, unconnected and schematic-parity findings, with passing
source, geometry and twelve isolation-rule controls across all six copper layers. Its
`independent CAM review <hardware/main-rev-e/checks/independent-gerbers.json>`_
parses eleven board Gerbers, two paste layers, both drill files and the IPC
reference. All 529 plated and four non-plated holes match native coordinates;
613 connected pins and 35 exact pad-specific NC aliases match the source.
Both exported solder-mask checks pass.
The `hardwired-control review <hardware/main-rev-e/checks/hardwired-control-review.json>`_
checks the STOP/HH path, series relay contacts and panel mapping. These records
are bound to particular source hashes and must match the final package manifest.
The `two-board baseline receipt <hardware/main-rev-e/checks/two-board-baseline-packages.json>`_
binds the checked main and panel archives to these results. Main/panel integration
also passes all 128 STOP-contact path cases and the 12-pin host mapping.

Panel evidence is the `native summary <hardware/panel-rev-e/checks/summary.json>`_,
`circuit review <hardware/panel-rev-e/checks/integration-review.json>`_,
`spacing audit <hardware/panel-rev-e/checks/independent-spacing-review.json>`_
and `CAM review <hardware/panel-rev-e/checks/gerber-parser-review.json>`_.
Its native ERC/DRC/parity/unconnected counts are also zero. None of these
checks measures an assembled circuit or extracts connectivity from final
Gerber copper polygons. Request the fabricator's electrical board test.

Prototype archive paths are:

* Main `bare-board prototype ZIP <hardware/main-rev-e/pump-controller-main-rev-e-gerber-prototype.zip>`_
  and `stencil prototype ZIP <hardware/main-rev-e/pump-controller-main-rev-e-stencil-prototype.zip>`_.
  The `package manifest <hardware/main-rev-e/package-manifest.json>`_ records
  successful baseline source/evidence/CAM checks and matching archive checksums.
* Panel `bare-board review ZIP <hardware/panel-rev-e/pump-panel-rev-e-gerber-review.zip>`_
  and `stencil review ZIP <hardware/panel-rev-e/pump-panel-rev-e-stencil-review.zip>`_.

This baseline has two separate PCB designs and separate stencil files. The
`Rev E fabrication specification <hardware/fabrication/rev-e/README.rst>`_
and `main package procedure <hardware/main-rev-e/PACKAGING.rst>`_ define the
files and gate. For the main, confirm the proposed six-layer, 1.6 mm FR-4
stackup, 1 oz outer/0.5 oz inner copper and ENIG process with
`Robu <https://robu.in/product/online-pcb-manufacturing-service/>`_ before ordering.
No exact dielectric construction or controlled-impedance result is established.
Ordinary through vias are used; no filled/capped via-in-pad process is specified.

Panel `STEP <hardware/panel-rev-e/exports/pump-panel-rev-e.step>`_ and
`GLB <hardware/panel-rev-e/exports/pump-panel-rev-e.glb>`_ contain available
component models. `Model coverage <hardware/panel-rev-e/checks/model-coverage.json>`_
identifies missing bodies; the mechanical assembly uses explicitly documented
allowances for those items. A rendered model does not establish enclosure fit.

Architecture and controls
-------------------------

* RECOM RACM06E-05SK/277 isolated 6 W switching supply, 25.4 x 25.4 x 16.7 mm,
  followed by TPS62162 for isolated 3.3 V. A compact high-frequency transformer
  remains inside the module; this is not a transformerless live supply.
* ESP32-C6-MINI-1U-H8 with 8 MiB flash and an external 2.4 GHz antenna.
  USB recovery is provided through the internal 2.54 mm service header J2.
  Firmware, signed updates, rollback and configuration migration are specified
  but not implemented.
* ADE7953 measures voltage, RMS current, real power and power factor in the
  live domain. ADuM6421A isolates its SPI interface and supply. The selected
  Talema AC1020 CT has a permanent 6.8-ohm burden; its input is in the live
  metering domain and is not an isolated sensor terminal.
* AC-excited tank/inlet probes, TLV9004, TMUX1208 and ADS1115. Five tank wires
  are assumed to mean common plus four level electrodes. These indicate bands;
  estimated volume depends on tank geometry and electrode positions. The inlet
  electrode needs a valid water-side reference, not protective earth.
* Two normally open relays in series control the contactor-coil circuit.
  Physical STOP and independent high-high interrupt permission. A hardware
  ARM latch, watchdog, supervisor and U36 Schmitt clear stage prevent ordinary
  watchdog servicing from re-arming a cleared latch. Stronger GPIO reset biases
  and U37 conditioning of STOP/MODE/NEXT sense inputs are included. Internal CPU resets can retain ARM_Q: firmware must establish
  hardware clear before a fresh arming session. Existing overload protection
  remains essential.
* Panel SW1 STOP, SW2 START, SW3 MODE, SW4 SET/RESET and SW5 NEXT/+. Optional
  external contacts parallel the NO keys; external NC STOP is in series with
  local STOP. Existing starter actuators require suitable separate isolated
  auxiliary contacts. JP1 bridges only an absent external STOP.
* One numbered 1-to-1 GH12 cable connects main J32 to panel J1. Main J33/J34
  and the old main SW3/SW4 are removed. Optional key sensing uses host GPB6/7;
  those inputs are not spare while key mode is enabled. The 25 mA spare/key
  allocation is a power reservation, not a separate expansion outlet.
* Waveshare 14657, 0.91-inch 128 x 32 OLED on a 36 x 12.5 mm module, connected
  through panel J7 with a PH4 plug-to-plug lead. Target cable lengths are
  150 mm GH12 plus 100 mm PH4; actual bus timing remains to be measured.
  Page content is programmable;
  separate status LEDs are omitted. Shared I2C remains 400 kHz with scheduled
  display chunks and measured signal/timing acceptance.

Wireless choices
----------------

Native Zigbee is the primary firmware target. Matter over Thread and Matter
over Wi-Fi remain separate targets on the same ESP32-C6 hardware. Exactly one
operational transport is selected per build; no concurrent-stack operation,
runtime transport switching or working radio firmware is claimed.

The Aqara M200 supports a Matter controller and Thread border router, while
its published Zigbee child support is limited to Aqara devices. Direct pairing
of this custom Zigbee controller is therefore unsupported. Matter/Thread is
the planned M200 and Apple Home integration path, pending endpoint and hub
validation. Native Zigbee needs a coordinator accepting the custom device.
See the `M200 specification <https://www.aqara.com/us/product/hub-m200/>`_ and
`child-device FAQ <https://www.aqara-shop.co.uk/product/aqara-hub-m200/>`_.

Every network adapter submits requests to local control and cannot drive relay
GPIO directly. Local controls, armed AUTO operation and protection must work
without a network. Mode changes stop/disarm and require the defined physical
STOP acknowledgement and fresh START. The OLED is intended to provide detailed local
telemetry; a browser dashboard is planned only for the Wi-Fi build. Native
Apple Home/Aqara tiles for arbitrary litres, volts, amps and watts are not
promised.

The external antenna, coax and final mounting position still require selection
and RF verification in the actual enclosure. A reserved bulkhead opening is
not an approved antenna installation. Test each implemented transport under
maximum permitted radio traffic while local control meets its deadlines, then
exercise hub/network/WAN loss. See the wireless acceptance requirements and
T08 in the physical test plan; no range, RF compliance or hub pairing result
is claimed.

Remaining qualification
-----------------------

The electrical design assumes nominal 230 V single-phase mains and evaluates
normal voltage sensing up to 264 V. Coil voltage, pickup/holding VA, available
space and local enclosure temperature still require confirmation. The supplied
starter starts automatically, but the exact capacitor-start switching provider
and motor overload path remain untraced. J30 is a coil-loop switch, not a proven
replacement for every output of the old RMG controller.

The main PCB dimensions exclude plugs, cable bends, antenna, spacers and covers.
The separate 170 x 150 x 90 mm case is a mechanical prototype for installations
where the starter has insufficient room; it is not proof of fit inside any
starter or a certified mains enclosure. Main-board insulating standoffs are
18 mm minimum. C1 is Panasonic EEUFR1E470; allow 13.5 mm installed height
(12.5 mm maximum body plus 1 mm mounting allowance), trim top-side leads and measure
the assembled clearance. Original meter terminals and live components need
retained protection against accidental contact.

* The allocation is 5.81 W, leaving 0.19 W below U1's 6 W rating. Check both
  the 1.2 A and 6 W limits; at most 50 C local PSU ambient is assumed. R2 can
  dissipate about 0.844 W and needs its 300 mm2 heat-spreading area. The module's
  suggested surge/filter arrangement differs from this board's R1/TMOV network;
  startup, disturbance and closed-enclosure thermal results are still required.
* F1's published interruption figure is 200 A at 600 VAC. Coordinate the full
  protective arrangement with the site's prospective fault current; R1 cannot
  limit a fault ahead of itself. Confirm independent motor overload, protective
  earth and appropriate residual-current protection. Metering is not earth-
  leakage protection.
* Obtain the actual contactor coil voltage, pickup/holding demand, suppression
  and load-specific relay suitability. A resistive contact rating does not
  qualify this inductive load. Both G5Q contacts must individually interrupt
  the full coil voltage; they do not switch motor current.
* Rev E targets an ordinary drilled-via process. The baseline geometry/export
  checks find no drill overlapping an SMT mask opening on either face.
  Manufacturer acceptance remains required; the older main board's via-in-pad process is not
  an approved shortcut for this revision.
* Preserve the original mains STOP/overload and capacitor-start functions;
  no holding branch may bypass J30. The external overload does not clear ARM_Q.
  Require manual overload reset and physical STOP first; automatic latch-off
  after every external coil interruption would need additional verified feedback.
  No controller relay can interrupt a welded main contactor's motor contacts.
* Physical STOP/HH removes K1 supply, but short-opening response and total stop
  delay need measurement. D31 and the HH sense capacitor store energy. Neither
  ordinary relays nor this logic form a certified emergency-stop system.
  Protective earth bonds the metal enclosure, not logic or probe ground.
* Load-based dry-run limits require wet-pump calibration across operating head.
  Inrush can exceed the meter's approximately 26 Arms ideal unclipped range;
  clipped startup samples cannot establish a valid underload condition.
* Open probe wiring may resemble dry water conditions. An independent high-high
  float addresses a separate overflow failure path; a fitted link does not.
* The `signal-layout review <design/rev-e-signal-integrity-review.rst>`_ and
  `return-path geometry <hardware/main-rev-e/checks/signal-return-paths.json>`_ record
  remaining analog-placement, clock and USB compromises. Six layers and ground
  planes do not establish 90-ohm USB impedance, stable crystal startup, meter
  accuracy or immunity to contactor noise.
* Contact endurance, coil suppression, thermal margins, RF, ESD/EFT/surge,
  brownout behavior, sensor faults, firmware recovery and actual motor tests
  remain required. The `bench acceptance plan <design/rev-e-bench-acceptance.rst>`_
  records T00–T09 as NOT RUN and defines the required setup/evidence. These
  functional controls are not a certified safety system.

Sources, native design and history
----------------------------------

Manufacturer URLs are included in the BOM, footprint provenance and design
reviews. The wireless documents cite official Espressif SDK and Connectivity
Standards Alliance sources. No purchased parts, downloaded binaries or assembly
images are evidence of physical qualification.

``design/main-rev-e.json`` and ``design/panel-rev-e.json`` define the current
component/pin interfaces. The focused builders are
``tools/build_main_rev_e.py`` and ``tools/build_panel_rev_e.py``. Their build
stages replace placement/routing input and must not be run casually on a
reviewed board. Native projects, project-local footprints, check records and
source hashes are retained for inspection. ``tools/prepare_main_rev_e_dsn.py``
sets explicit routing clearance matrices; native KiCad DRC remains authoritative.

Earlier Rev C main files retain the basename ``pump-controller-rev-b`` and
remain historical references. Rev D panel/fanout documents, older Rev C PDFs,
and ``output/panel-rev-d`` or ``output/3d`` images describe earlier interfaces.
They must not be used to wire the Rev E GH12/PH4 arrangement or order Rev E PCBs.
The earlier LED panel and rotary-selector designs remain archived.
