Compact single-phase pump controller
===================================

Rev B is a component-value engineering prototype for a 1 HP single-phase
pump operated through an existing DOL contactor. It combines local water-level
control, motor metering, load-based dry-run protection, physical controls and
planned Matter connectivity.

**Status: hardware design and PCB development; not released for fabrication or
mains installation. Firmware and physical validation are not complete.**

Start here
----------

* ``output/pdf/pump-controller-rev-b-design-pack.pdf``: readable overview,
  integration diagrams, detailed KiCad circuit sheets and complete parts list.
* ``hardware/pump-controller-rev-b.kicad_pro``: editable main-board project.
* ``design/oled-selection.txt``: compact display selection, cable mapping and bus timing.
* ``design/parts-complete.csv``: all main-board and external components,
  values, procurement requirements and manufacturer source links.
* ``hardware/checks/``: native electrical/layout checks and layout status.
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
  Motor power does not pass through the controller PCB. Physical STOP/OFF
  and an optional independent high-high float interrupt the health relay.
* Separate hardware ARM latch, watchdog and supply supervisor. Normal
  watchdog servicing cannot re-arm a cleared latch.
* MANUAL/OFF/AUTO selector, START and fault RESET. Manual mode keeps the
  controller's protections and works without the network.
* Internal J34 expansion: 3.3 V / 25 mA, I2C and two spare MCP23017 GPIO.
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

The current placement targets a 90 x 70 mm four-layer main PCB with a
separate 36 x 12.5 mm purchased OLED module. Board dimensions exclude terminal plugs,
wiring bends, mounting spacers, antenna and protective covers. The detailed
layout status and remaining routing/DRC findings govern usability.

Important retained findings:

* The minimum-load resistor dissipates up to about 0.844 W. Preserve at least
  300 mm2 of specified heat-spreading copper and verify temperature in the
  closed starter. The current 5.7 W conservative allocation requires no more
  than 50 C local ambient around the 5 V PSU.
* The 200 A fuse interrupting rating is not the controller's SCCR. Prospective
  fault current and upstream protection need a coordinated assessment.
* New panel controls are isolated low voltage. Old mains START/holding wiring
  must be disconnected/reworked so it cannot bypass either board relay.
* Relay pickup after the selector diode and field wiring needs hot-start
  validation. Room-temperature pickup specifications are insufficient.
* Existing overload protection remains in the coil path. There is no direct
  overload or contactor auxiliary feedback. Use a manual-reset overload and
  STOP/OFF before reset; not every external interruption is hardware-latched.
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
by Rev B. In particular, use the Rev B control wiring and component values.

