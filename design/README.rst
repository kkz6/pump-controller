Design sources and revisions
============================

The current compact circuit, layout, BOM, manufacturing archive and checks
are indexed in the `compact board directory <../hardware/main-compact/README.rst>`_.

Historical Rev E design
-----------------------

**100 x 80 mm main board on hold.** The optional AUTO key is connected to
MCP23017 GPB7. Microchip restricts this pin to output use because transitions
during reads can corrupt the shared I2C bus. The Rev E Gerbers and test records
below preserve the historical layout. Use the corrected compact design for
further engineering. See the `Microchip pin advisory
<https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_.

The verified Rev E baseline comprises a 100 x 80 mm six-layer main PCB and a
separate 60 x 45 mm two-layer OLED/button panel. Both boards have passing
native/CAM records, including the main input-conditioning correction, and
matching prototype archive checks. Compact alternatives remain under evaluation;
the baseline does not select a final board size, layer count or purchase.
Fabricator acceptance, firmware, assembled electrical performance and installation
qualification remain pending.

Current circuit and evidence
----------------------------

* `Main schematic PDF <../hardware/main-rev-e/exports/schematic.pdf>`_ and
  `KiCad project <../hardware/main-rev-e/pump-controller-main-rev-e.kicad_pro>`_.
  ``main-rev-e.json`` defines component/pin interfaces and placements. The
  current BOM is ``../hardware/main-rev-e/bom.csv``.
  `Capacitor sourcing <rev-e-capacitor-sourcing.rst>`_ records exact parts,
  C1 installed dimensions and effective-capacitance acceptance limits.
* `Panel KiCad project <../hardware/panel-rev-e/pump-panel-rev-e.kicad_pro>`_,
  ``panel-rev-e.json`` and its native BOM define the five-button panel,
  optional external contacts, active NPN key conditioning and PH4 OLED socket.
* `Electrical/reset review <rev-e-electrical-review.rst>`_,
  `signal and analog layout review <rev-e-signal-integrity-review.rst>`_,
  `return-path geometry <../hardware/main-rev-e/checks/signal-return-paths.json>`_, and
  `bench acceptance plan <rev-e-bench-acceptance.rst>`_ distinguish corrected
  defects, calculation limits and outstanding physical tests. T00–T09 are NOT RUN.
* `Main native checks <../hardware/main-rev-e/checks/independent-summary.json>`_,
  `main CAM checks <../hardware/main-rev-e/checks/independent-gerbers.json>`_
  and `panel checks <../hardware/panel-rev-e/checks/summary.json>`_ are tied to
  their source hashes. Main ERC/DRC/parity/unconnected counts are zero; all
  twelve isolation controls pass. The CAM reference matches 613 connected
  main pins plus 35 exact NC aliases, and the panel matches 81 connected pins.
  No layout pass is product-safety or EMC qualification.
* `Two-board baseline package receipt <../hardware/main-rev-e/checks/two-board-baseline-packages.json>`_
  records archive checksums and matching source evidence. The
  `integration review <../hardware/panel-rev-e/checks/integration-review.json>`_
  passes the host/OLED/key mapping and 128 STOP-contact path cases.
* `Hardwired-control audit <../hardware/main-rev-e/checks/hardwired-control-review.json>`_
  verifies current pin maps and ideal contact topology.
  `Unpowered fixture procedure <rev-e-unpowered-harness-acceptance.rst>`_ and
  `669-case matrix <rev-e-unpowered-harness-acceptance.json>`_ define future
  physical continuity tests; every result begins unrun.

Prototype manufacturing
-----------------------

* Main `bare-board ZIP <../hardware/main-rev-e/pump-controller-main-rev-e-gerber-prototype.zip>`_
  and `stencil ZIP <../hardware/main-rev-e/pump-controller-main-rev-e-stencil-prototype.zip>`_:
  the `package manifest <../hardware/main-rev-e/package-manifest.json>`_
  records successful current source/evidence/CAM checks and matching archive hashes.
* Panel `bare-board review ZIP <../hardware/panel-rev-e/pump-panel-rev-e-gerber-review.zip>`_
  and `stencil review ZIP <../hardware/panel-rev-e/pump-panel-rev-e-stencil-review.zip>`_.
* `Fabrication specification <../hardware/fabrication/rev-e/README.rst>`_ and
  `package procedure <../hardware/main-rev-e/PACKAGING.rst>`_. Main and panel
  are separate fabrication designs; paste files are separate stencil files. The
  proposed six-layer dielectric stackup remains subject to vendor confirmation.

Connections, operation and radio
--------------------------------

* `Rev E integration <rev-e-integration.rst>`_,
  `preassembled harness schedule <rev-e-harness-order.rst>`_ and
  `panel pin assignments <../hardware/panel-rev-e/parts-and-interface.rst>`_
  define direct numbered GH12/PH4 cables. Main J33/J34 and main SET/NEXT keys
  are removed; J2 is the internal 2.54 mm service header. Old fanout looms do
  not apply. Actual starter coil/capacitor/overload identification remains open.
* ``oled-selection.txt`` defines the small display, 150 mm host plus 100 mm
  OLED cable target, shared 400 kHz acquisition schedule and measured bus limits.
* ``programmability.txt`` and ``operation-and-bringup.txt`` specify future local
  protection, reset/re-arm, settings, updates and calibration. An internal CPU
  reset may retain the ARM latch; a fresh session must establish hardware clear.
* `Wireless architecture <wireless-architecture.rst>`_ and
  `variant manifest <wireless-variants.json>`_ specify native Zigbee as primary
  and separate Matter/Thread and Matter/Wi-Fi images. Custom Zigbee pairing
  directly to Aqara M200 is unsupported; Matter is the planned M200/Apple path.
  Antenna selection, RF/EMC and actual hub interoperability remain untested.
* `Mechanical prototype <../mechanical/rev-e/README.rst>`_ describes the separate
  170 x 150 x 90 mm case, printable parts and fit limits. It does not establish
  fit inside any starter or an electrically qualified enclosure. Main-board
  insulating standoffs are 18 mm minimum; verify C1 Panasonic EEUFR1E470
  installed clearance using the 13.5 mm allowance (12.5 mm maximum body
  plus 1 mm mounting allowance) and trimmed top-side leads.

Sources and regeneration
------------------------

``../tools/build_main_rev_e.py`` transforms the retained earlier circuit into
current Rev E. It includes connector changes, four mounts, the revised reset
biases, U36/C77 clear conditioning, U37/C78 control-input conditioning and
the six-layer layout setup. The panel's
focused builder is ``../tools/build_panel_rev_e.py``. Build stages overwrite
native schematics and placement/routing inputs; preserve reviewed changes
before regeneration. A placement-only DRC is not a routed-board pass.

``core.json``, ``power-mcu.json``, ``probe-front-end.json``, ``assemble.py`` and
``circuit.json`` remain inputs to the earlier circuit and Rev E transformation.
They are not independently current connector/placement definitions.
``parts-complete.csv`` is historical; use current native BOMs. The retained
``core-review.txt`` and ``power-budget-review.txt`` explain earlier calculations
but contain superseded references. Current reset findings, 5.81 W allocation
and actual qualification requirements are in the Rev E reviews and bench plan.

Rev D used the older main board with a three-header panel fanout. Rev C PDFs,
``wiring-guide.rst`` and earlier report generators retain that hardware unless
explicitly revised. Their connectors, dimensions and acceptance records must
not be used for Rev E. The older main project retains a ``rev-b`` filename
despite later Rev C metadata. LED/rotary-selector versions are archived.
