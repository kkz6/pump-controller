Compact single-phase pump controller
===================================

The current Rev D assembly combines the Rev C main controller with a separate
low-voltage OLED/button panel for a 1 HP single-phase pump operated through an
existing DOL contactor. It combines local water-level control, motor metering,
load-based dry-run protection, physical controls and planned Matter connectivity.

**Status: detailed schematic and routed prototype PCB complete. Not released
for fabrication or mains installation. Firmware and physical validation are
not complete.**

The final native checks report zero ERC violations, zero DRC errors or
warnings, and zero unconnected items. All 208 main-board components match the
electrical source. An independent native DRC run confirms the layout result;
these checks cover the CAD design, not an assembled controller.

Start here
----------

* `Rev D panel and harness <design/panel-rev-d-integration.rst>`_:
  all five user buttons and OLED on the separate board, optional external
  buttons, and an optional maintained AUTO/MANUAL key switch. Main-board
  SW3/SW4 are not populated in this assembly.
* `Panel KiCad project <hardware/panel-rev-d/pump-panel-rev-d.kicad_pro>`_
  and `panel parts list <hardware/panel-rev-d/bom.csv>`_.
* `Panel Gerbers <hardware/panel-rev-d/pump-panel-rev-d-gerber-review.zip>`_,
  `panel 3D STEP <hardware/panel-rev-d/exports/pump-panel-rev-d.step>`_
  and `model coverage <hardware/panel-rev-d/checks/model-coverage.json>`_.
  Physical prototype tests and manufacturer acceptance are still pending.
* `Current panel connection image <output/panel-rev-d/connection-overview.png>`_:
  separate panel, optional buttons/key switch, STOP loop and the full cable map.
* `Robu fabrication review <hardware/fabrication/README.rst>`_:
  Gerber/drill data, independent export checks and unresolved manufacturer
  requirements. The archive is for review, not an approved board order.
* `Rev C wiring reference <output/pdf/pump-controller-rev-c-wiring-guide.pdf>`_:
  main PCB terminals and the limits of mapping the photographed starter.
  Use the Rev D panel/harness document above for the new control arrangement.
* `3D models and offline viewer <output/3d/>`_: native PCB models,
  the earlier Rev C assembly using the photographed starter style, and fit
  notes. The separate Rev D panel is documented in its own project.
* `Earlier starter connection image <output/images/starter-controller-rev-c.png>`_:
  the Rev C visual concept; its panel arrangement is superseded by Rev D.


* `Design pack PDF <output/pdf/pump-controller-rev-c-design-pack.pdf>`_:
  readable overview, integration diagrams, detailed KiCad circuit sheets,
  complete parts list and PCB review drawings.
* `KiCad project <hardware/pump-controller-rev-b.kicad_pro>`_:
  editable main-board project.
* `OLED selection <design/oled-selection.txt>`_:
  compact display selection, cable mapping and bus timing.
* `Main-controller parts list <design/parts-complete.csv>`_: Rev C main-board
  and external components, values, procurement requirements and source links.
  Use the separate panel BOM above and omit main SW3/SW4 for the Rev D assembly.
* `Verification records <hardware/checks/>`_: native electrical/layout checks and layout status.
* ``design/core-review.txt``, ``design/power-budget-review.txt`` and
  ``design/probe-front-end.txt``: calculations, decisions and remaining tests.
* ``design/operation-and-bringup.txt``: proposed firmware behavior and
  commissioning sequence. This is a specification, not implemented firmware.

Architecture
------------

* RECOM RACM06E-05SK/277 isolated 6 W AC/DC module, 25.4 x 25.4 x 16.7 mm.
  Its high-frequency transformer replaces a bulky line-frequency transformer.
  TPS62162 supplies the isolated 3.3 V electronics.
* ESP32-C6-MINI-1U with external antenna. Matter over Wi-Fi is the initial
  connectivity choice. Local app operation needs the LAN but not WAN access
  after setup. Local physical and automatic operation must not depend on Wi-Fi.
* ADE7953 reads voltage, RMS current, real power and power factor in the live
  domain. ADuM6421A isolates its SPI interface and supply. External Talema
  AC1020 CT has a permanently attached 6.8-ohm burden.
* AC-excited tank/inlet probes, TLV9004 buffers, TMUX1208 and ADS1115 ADC.
  Five tank wires are assumed to mean common plus four levels. These provide
  level bands, not continuous litres. An inlet electrode requires a valid
  reference electrode in the same water body.
* Two normally open relays in series control the existing contactor coil.
  Motor power does not pass through the controller PCB. Physical STOP
  and an optional independent high-high float interrupt the health relay.
* Separate hardware ARM latch, watchdog and supply supervisor. Normal
  watchdog servicing cannot re-arm a cleared latch.
* Separate low-voltage panel carrying START, STOP, MODE, SET/RESET, NEXT/+
  and OLED. Optional external button connectors can reuse the starter's
  existing actuators through suitable isolated auxiliary contacts while
  preserving its capacitor-start circuit. An optional maintained key switch
  selects MANUAL/AUTO through two independently sensed contacts. The panel
  uses a single 12-way harness; main-board SW3/SW4 are left unpopulated.
  Manual mode keeps protection and works without the network.
* Internal J34 expansion: 3.3 V / 25 mA, I2C and two MCP23017 GPIO. The Rev D
  key-switch option uses those two GPIO; they are not then spare.
  USB recovery is available at J2; wireless updates and versioned settings
  are required by the firmware specification in ``design/programmability.txt``.
* Small 0.91-inch OLED, 128 x 32 pixels, Waveshare 14657 module. Its PCB is
  36 x 12.5 mm. Software pages show level, volts, amps, watts, mode and faults;
  separate indicator LEDs are omitted. The completed earlier LED panel is
  retained only as superseded work under ``archive/led-panel-rev-b/``.

Prototype constraints
---------------------

The electrical design assumes 230 V nominal single-phase mains and evaluates
normal voltage sensing up to 264 V. The actual starter's supply, contactor
coil voltage, inrush VA, spare space and enclosure temperature are unverified.
Do not infer universal starter compatibility from the 1 HP motor rating.

The routed layout uses a 90 x 70 mm four-layer main PCB with a
separate 36 x 12.5 mm purchased OLED module. Board dimensions exclude terminal plugs,
wiring bends, mounting spacers, antenna and protective covers. The detailed
layout reports record the checked revision; installation fit still needs
measurement in the intended starter.

The reference photographs show a capacitor-equipped submersible starter.
Its present system starts automatically, but the capacitor-start switching
provider, coil voltage and motor overload path are not yet traced. J30 is a
coil-loop switch; it is not a proven replacement for every output of the old
RMG controller. Preserve the verified motor starting circuit.

Important retained findings:

* The minimum-load resistor dissipates up to about 0.844 W. Preserve at least
  300 mm2 of specified heat-spreading copper and verify temperature in the
  closed starter. The Rev D panel increases the conservative allocation to
  5.76 W; the design still requires no more
  than 50 C local ambient around the 5 V PSU.
* The compact routing includes vias overlapping surface-mount pads. These
  require filled and plated-over vias, or rerouting before fabrication;
  ordinary tenting is insufficient. See the exact
  `via inventory <hardware/checks/via-in-pad-audit.json>`_ and
  `fabrication constraints <design/fabrication-constraints.txt>`_.
* The 200 A fuse interrupting rating is not the controller's SCCR. Prospective
  fault current and upstream protection need a coordinated assessment.
* New panel controls are isolated low voltage. Old mains START/holding wiring
  must be disconnected/reworked so it cannot bypass either board relay.
* D33/D34 are removed in Rev C; STOP_RETURN feeds the high-high loop
  directly. Relay hot pickup and field-wire losses still need validation.
* Existing overload protection remains in the coil path. There is no direct
  overload or contactor auxiliary feedback. Use a manual-reset overload and
  STOP before reset; not every external interruption is hardware-latched.
* Dry-run thresholds require wet-pump commissioning across the operating head
  range. Startup inrush can exceed the meter's approximately 26 Arms ideal
  unclipped range; it must not be mistaken for valid underload evidence.
* An open probe/common lead can look dry. An independent high-high float
  addresses a distinct overflow failure path; a fitted jumper does not.
* Apple Home's presentation of arbitrary level/energy telemetry is not
  guaranteed. Detailed telemetry is intended for a local LAN dashboard.
  Aqara capability depends on the exact controller model and firmware.
* These are functional controls, not a certified safety-rated control system.

Sources and reproducibility
---------------------------

Component-level manufacturer URLs are recorded in the BOM and review notes.
Datasheets, installers and CAD application binaries are not redistributed.
Native symbols and project-specific footprints are supplied with the design.
Derived footprints still require physical/manufacturer-land-pattern review.

``design/core.json``, ``design/power-mcu.json`` and
``design/probe-front-end.json`` hold the component/net definitions.
``design/assemble.py`` combines them into ``design/circuit.json`` and the BOM.
Native KiCad exports are checked against these definitions; ERC success is
not evidence of correct mains insulation, EMC, thermal behavior or firmware.

Earlier concept material, if present under ``archive/rev-a/``, is superseded
by Rev C. Rev B selector documentation is retained under
``archive/rev-b-selector`` and commit ``dc09030``. Native KiCad basenames
retain ``rev-b`` for existing project references; their title metadata and
current electrical content are Rev C.

