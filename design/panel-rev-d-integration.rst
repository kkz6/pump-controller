Rev D detachable low-voltage control panel
=========================================

This panel carries all five user controls (START, STOP, MODE, SET/RESET and
NEXT/+) and the small OLED. Optional connectors accept external buttons and
a maintained AUTO/MANUAL key switch. A single keyed 12-way cable connects the
panel to the isolated side of the controller.

The main-board copper remains Rev C. In this assembly, **do not populate
main-board SW3 or SW4**: SET/RESET and NEXT/+ are now on the panel. The existing
main-board J32 pins4 and6 are used by this harness; their earlier reserved-pin
instruction applies only to the previous Rev C panel arrangement. MCU recovery
BOOT/RESET facilities on the main board remain service features.

The active panel design is in ``hardware/panel-rev-d/``. The earlier Rev C
wiring PDF and assembled images remain references for the main controller;
their front-panel arrangement is superseded by this document.

Panel cable (panel J1)
-----------

Pins below are electrical cavity numbers, not a left-to-right drawing viewed
from the wire side. Use the connector manufacturer's pin1 marker and mating
drawing. Verify continuity before applying power. Plug/unplug only with the
controller isolated from its mains and coil supplies.

========== ===================== ==============================
J1 pin     Signal                Main-board destination
========== ===================== ==============================
1          +5V                   J32.1
2          STOP_RETURN           J32.2
3          MODE / MAN_RETURN     J32.3
4          NEXT / AUTO_RETURN    J32.4
5          START_N               J32.5
6          SET / RESET_N         J32.6
7          isolated GND          J32.7
8          OLED +3V3             J33.1
9          OLED SDA              J33.3
10         OLED SCL              J33.4
11         KEY_MAN_N             J34.5 / SPARE_B6
12         KEY_AUTO_N            J34.6 / SPARE_B7
========== ===================== ==============================

J32.7, J33.2 and J34.2 are already the same isolated ground on the main PCB.
The panel cable takes its one ground return from J32.7. Leave J33.2 and the
unused J34 pins unconnected in this harness; do not create an unqualified
double-wire crimp. The board-side fanout is retained under the controller
cover. There is one disconnect at the panel.

Use a short, restrained cable within the cabinet, initially no longer than
300 mm. Keep it away from contactor, capacitor, motor and mains wiring. The
direct I2C connection is intended for this short panel harness, not remote
building wiring. Validate I2C rise time/noise with the actual cable at 100 kHz.

The selected Waveshare14657 OLED has a separate PH2.0 connector: pin1 SCL,
pin2 SDA, pin3 GND, pin4 VCC. Supply it with 3.3 V from the panel. It is not
a straight-through copy of main-board J33's numeric order.

Local and external buttons
--------------------------

All five local buttons work without external controls. External button
connectors are isolated dry-contact inputs; never apply mains or another
power supply to them.

============== =================== ========================
Panel connector Pin1                Pin2
============== =================== ========================
J2 START       START_N              GND
J3 STOP        STOP_LOCAL_NC        STOP_RETURN
J4 MODE        MAN_RETURN           STOP_RETURN
J5 SET         RESET_N              GND
J6 NEXT        AUTO_RETURN          STOP_RETURN
============== =================== ========================

JP1 is the external-STOP bypass link. J7 is the OLED connector and J8 is
the optional key-switch connector.

* STOP: normally closed local contact and optional normally closed external
  contact are in series. Either STOP opens the hardware relay-permit path.
  If no external STOP is fitted, install the explicitly marked external-STOP
  bypass link. Remove that link when fitting an external STOP. An empty
  unbridged external-STOP connector prevents operation.
* START: normally open external button in parallel with local START,
  connecting START_N to GND.
* MODE: normally open external button in parallel with local MODE,
  connecting MAN_RETURN to STOP_RETURN.
* SET/RESET: normally open external button in parallel with the local key,
  connecting RESET_N to GND. This is a user-interface input, not MCU reset.
* NEXT/+: normally open external button in parallel with the local key,
  connecting AUTO_RETURN to STOP_RETURN.

MODE and NEXT use the STOP_RETURN rail. They cannot register a press while
STOP is held open. Stop and disarm first, then release STOP to use settings.
The hardware arm latch must remain disarmed until a separate fresh START.

To reuse the starter's original actuators, fit and verify suitable isolated
auxiliary contacts. Preserve any original contacts required for capacitor
starting. Contact blocks shared with mains need rated separation between
circuits; do not assume every spare contact provides it. The actual starter's
capacitor-start sequence still requires tracing before installation.

Optional maintained key switch
-------------------------------

Panel J8 has three contacts: 1=+5V common, 2=MANUAL return, 3=AUTO return. Use a
maintained SPDT, break-before-make switch with contacts suitable for the small
5 V sensing load. This connector is for isolated contacts only.

Each return has a 2.2 kohm wetting resistor and an NPN level shifter. The GPIO
side is pulled up to the controller's 3.3 V rail; 5 V does not feed J34 directly.
Each selected contact produces an active-low input. The two key inputs use the
previously spare MCP23017 GPB6/GPB7 pins, so those pins are no longer available
for unrelated expansion when the key option is installed.

============= ============== ==========================================
KEY_MAN_N     KEY_AUTO_N     Meaning when key-switch mode is enabled
============= ============== ==========================================
0             1              MANUAL
1             0              AUTO
1             1              Invalid: neither contact selected
0             0              Invalid: both asserted / panel disconnected
============= ============== ==========================================

The external key connector unplugged produces both inputs high. The whole
panel cable unplugged leaves the main-board pulldowns low on both inputs and
also opens the physical STOP loop. This does not detect every possible single
wire fault; it is not a safety-rated key-switch interface.

Power allocation
----------------

Reserve an additional 0.06 W for the STOP/key wetting resistors and two key
level shifters. This includes the both-key-contacts-closed fault case, 5.5 V
at the 5 V rail, 3.465 V at the logic rail, resistor tolerance and an allowance
for incremental buck-converter loss. The OLED's existing 100 mA allowance is
not added a second time. The conservative system reservation rises from
5.70 W to 5.76 W on the 6 W supply. The remaining nominal rating margin is
0.24 W; retain the <=50 C local PSU ambient constraint and measure startup,
transient and closed-enclosure temperature performance.

Firmware requirements (not yet implemented)
--------------------------------------------

* Configure the two MCP23017 key pins as inputs with internal pull-ups disabled.
  The external circuit supplies the required bias; do not enable output drivers.
* Default configuration is ``mode_source=button``. Leave panel J8 empty if unused;
  ignore key inputs in this configuration. MODE toggles MANUAL/AUTO only while
  disarmed after a physical STOP acknowledgement.
* ``mode_source=key`` gives the maintained key priority. MODE displays the
  selected source/mode and cannot override the key. Enable this setting only
  while stopped, with a valid stable key state detected.
* Any key-state change first cancels the run request and disarms the pump.
  A valid new mode must be stable before the UI accepts it. Require physical
  STOP acknowledgement and a fresh START before allowing operation again.
* An invalid state while the key option is enabled inhibits starting and
  latches a key-input fault. In a running system it requests a stop immediately;
  debounce may delay accepting a valid new mode, not suppress the stop request.
* Startup, power recovery, reconnecting a panel, or selecting AUTO must not
  automatically re-arm the pump. Mode selection is never a START command.
* Manual and automatic modes retain dry-run, level, voltage and other protections.
  The physical STOP chain remains independent of mode-selection firmware.
* Settings changes and fault acknowledgement do not assert ARM. SET/RESET
  retains short select/save/acknowledge and long enter/back semantics; NEXT
  retains short next/increment and long decrement semantics.

Physical segregation
--------------------

The panel board carries only the controller's isolated 5 V/3.3 V circuits.
Its connector is not the isolation barrier: the isolated power/interface design
and verified physical separation establish that boundary.

Put the main PCB and all live terminals behind a secured insulating cover.
Route the panel cable through a restrained low-voltage passage, preserving the
main-board isolation corridor. Keep SET/NEXT accessible from the panel without
opening the live compartment. Retain enclosure/door protective-earth bonding;
do not use protective earth as a sensor or panel signal return.

The photographed starter also has live meter backs, breaker terminals,
capacitor terminals and contactor wiring. Those require their own guarded
compartment or covers. Moving the controls does not make the entire open
starter safe to touch. Cover dimensions, actuator travel, display window and
clearances need measurements of the actual enclosure before mechanical release.

The D2F STOP and the small NO tactiles have different heights and travel.
Provide suitable insulated plungers and an unobstructed STOP action; do not
assume a flat faceplate can press all five bare switches correctly.

Validation before use
---------------------

Check every harness cavity against the table; verify that either STOP and a
disconnected panel remove relay permission without software. Test local and
external buttons, every key code and cable reconnect with the pump isolated.
Measure rail levels, I2C edges and contact reliability in the final harness.
No CAD result establishes those physical behaviors or completes the firmware.
