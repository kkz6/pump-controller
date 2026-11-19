Where every wire connects — Rev C
=================================

Rev D panel update: this is the earlier control arrangement. For the separate
OLED/five-button board, optional external buttons and key selector, use
``design/panel-rev-d-integration.rst``. In that assembly main SW3/SW4 are not
populated, J32 pins4/6 are used, and J34 pins5/6 carry the optional key inputs.

This guide maps the **proposed controller terminals**. It is not a verified
wiring drawing for the existing starter: the starter model, coil voltage and
button construction have not been identified. The PCB is an unbuilt prototype
and firmware is not implemented. Have the final starter wiring checked before
energizing it.

Reference starter integration
----------------------------------------

The reference box has two large capacitors, a two-pole contactor, front-panel
meters/MCB, a terminal strip and an external RMG water controller. It is a
capacitor-equipped single-phase submersible starter, so the motor starting
circuit must be identified before replacing its controls. The existing START
button may also engage a starting capacitor temporarily. Recorded existing
operation confirms that RMG AUTO starts the pump without pressing the green
START button. This confirms an automatic starting path exists; it does not
identify whether the start-capacitor switching is inside the starter, in the
RMG controller, or in another component. **J30 alone cannot
replace an unknown start-capacitor engagement/disconnection sequence.** Retain
the correct capacitor/motor circuit and identify how the existing RMG starts
and releases it before applying the coil-switch example below.

A related official RMG DFAWLC-044 manual uses separate relay wire pairs for
starter control, and the product catalogue distinguishes start/stop from
start/run/stop relay variants. The installed model/output arrangement is not
identified by that related manual. **This Rev C coil interface is not yet a
verified drop-in replacement for the RMG wiring.** [4]_ [5]_

The photo does not establish coil voltage or the precise function of each
terminal/colour. Nor does the visible MCB establish that suitable motor overload
protection is present: identify and verify that protection separately. Do not
move the capacitor, motor or terminal-strip wires from a visual guess. The
labelled PCB terminals are exact; mapping them to this starter remains pending
verification of its circuit.

START, STOP, power and screen
-----------------------------------

* **START button:** a separate isolated normally open auxiliary contact
  between **J32 pin 5 and J32 pin 7**. It closes only while pressed.
* **STOP button:** a separate isolated normally closed auxiliary contact
  between **J32 pin 1 and J32 pin 2**. It opens while pressed. J32 pin 2 also
  feeds MODE, the internal NEXT key and the high-high loop.
* **Controller power:** **J1 pin 1 = incoming L; J1 pin 2 = incoming N**,
  after the starter's upstream isolator/protection but before the contactor.
  The controller must remain powered when the motor stops.
* **Small OLED screen:** **J33**, using four wires to the display behind the
  starter's front-panel window. Its cable pin order is reversed numerically:
  **J33 1→OLED 4, 2→3, 3→2, 4→1**. Follow signal labels, not wire colours.

J1, J30 and J10 are hazardous-voltage connections. J32 button wiring and J33
display wiring belong to the isolated low-voltage side. They must not share
mains, neutral, protective earth or an old mains button common.

See `connector location drawing <../hardware/wiring/connector-map.svg>`_,
`button wiring <../hardware/wiring/panel-controls.svg>`_ and
`power / coil wiring <../hardware/wiring/power-and-coil.svg>`_.

Keep the existing START and STOP actuators
------------------------------------------

The front panel retains the existing START and STOP actuators and adds **one
MODE button**. Settings buttons are on the PCB, not on the front panel.

Preserve the original power/capacitor-start contacts and their required
function. For J32, fit separate isolated auxiliary contacts operated by the
same START/STOP actuators where mechanically and electrically compatible:
START needs NO and STOP needs NC. A contact carrying mains or a capacitor-start
feed must never also connect to J32. If suitable additional contacts cannot
be fitted, the mechanical contact arrangement needs revision; sharing the
existing power contacts is not an acceptable shortcut.

**Some DOL STOP buttons are mechanical plungers that press the overload.**
A plunger has no electrical terminals for J32. Its mechanism must be inspected
to provide the additional isolated NC STOP function. Similarly, a START actuator
that directly pushes a mechanism is not automatically a separate NO contact.
Keep necessary original functions, but no manual actuator or holding circuit
may defeat the verified J30 stop/permission chain. Schneider documents the
mechanical STOP distinction and device-dependent terminal arrangements. [1]_

The old auxiliary-contact holding loop must not bypass the board's two series
relay contacts. Placing J30 only in parallel with the old START button could
allow an old holding path to defeat a controller stop. Reconcile the exact
coil/capacitor circuit before connecting the replacement controller.

Three external buttons: J32
---------------------------

.. list-table:: Isolated low-voltage harness; no mains connections here
   :header-rows: 1
   :widths: 15 25 60

   * - PCB pin
     - Signal
     - External wire goes to
   * - 1
     - +5 V
     - One terminal of the isolated NC STOP auxiliary contact.
   * - 2
     - STOP return
     - Other isolated STOP terminal AND one terminal of the new MODE button.
   * - 3
     - MODE input
     - Other terminal of the normally open MODE button.
   * - 4
     - Internal NEXT signal
     - Reserved; leave externally unwired.
   * - 5
     - START input
     - One terminal of the isolated NO START auxiliary contact.
   * - 6
     - Internal SET/RESET signal
     - Reserved; leave externally unwired.
   * - 7
     - Isolated GND
     - Other isolated START terminal.

External contacts: **STOP = 1-2 (NC), MODE = 2-3 (NO), START = 5-7 (NO)**.
J32.4 and J32.6 have no external wires. STOP is not wired to J32.7, and START
is not wired to +5 V. MODE is a momentary sense input, not a rotary selector.
J32.2 directly supplies the high-high loop through J31.1; the former D33/D34
selector diode-OR is removed. MODE does not supply relay-coil power.

Small settings keys on the PCB
------------------------------

* **SW3 SET/RESET:** a built-in NO key between RESET_N and isolated GND.
* **SW4 NEXT/+:** a built-in NO key between AUTO_RETURN and STOP_RETURN.

SW1 MCU RESET and SW2 BOOT are separate programming/service buttons; they
are not the SW3/SW4 settings keys.

The legacy internal net names do not mean separate external MANUAL/AUTO
buttons. The PCB keys replace extra front-panel settings controls. They are
internal service keys: operate them using isolated low-voltage service/bench
power with mains and coil supplies disconnected, unless a separately verified
insulated access/cover arrangement has been provided. Do not reach into an
exposed powered starter to press them.

How to operate the controls
---------------------------

1. **Press and release STOP** before changing mode or entering settings.
   STOP physically removes permission and clears ARM. Release restores power
   to MODE/NEXT but does not re-arm or restart. Do not keep STOP held while
   selecting a mode or navigating: those inputs use its return supply.
2. Press **MODE** to toggle MANUAL/AUTO while stopped and unarmed. The OLED
   shows the selection. MODE alone never starts the motor.
3. Press **START** to deliberately arm and run/enable the selected mode,
   subject to all healthy inputs and protection.
4. A **short internal SET/RESET** press acknowledges a displayed cleared
   fault only. It never starts or re-arms; fresh START is still required.
5. For settings, press/release STOP, then **hold internal SET** while confirmed
   stopped/unarmed. NEXT short = next/increase; NEXT held = previous/decrease;
   SET short = select or validate/save; SET held = back/exit. Neither front
   START nor MODE navigates a menu. Saving/exiting never resumes pumping.

MODE pressed while armed cancels the run request and shows PRESS STOP. Accept
a new selection only after a fresh physical STOP cycle and fresh MODE press;
the mode-button software response is not claimed to clear hardware ARM.
Require all NO inputs to be released after boot/menu exit, reject ambiguous
simultaneous events, and ensure one SET/NEXT press never triggers both short
and held actions. Fault acknowledgement has priority. Settings cannot disable
physical STOP, high-high, watchdog or mandatory protective checks. These are
firmware requirements, not implemented behaviours.

Power wires and contactor-coil control
--------------------------------------

There are three distinct paths:

1. **Motor power:** the verified supply/contactor, overload, motor and capacitor-start circuit
   remains the motor-current path. No motor power
   conductor is routed through J1 or J30. Preserve the starter manufacturer's
   single-phase pole/overload arrangement; some three-pole overloads require
   all poles to carry current even in a single-phase application. [2]_
2. **Controller supply:** a protected branch of incoming L/N, after upstream
   isolation and before the contactor, feeds J1.1 and J1.2. The onboard power
   module creates isolated 5 V and 3.3 V. J1 is not a motor output.
3. **Coil command:** J30.1 and J30.2 are a series switch made from the board's
   two normally open relay contacts. They do not generate a coil voltage.
   Put these contacts in the verified coil circuit with the existing overload
   NC trip contact, so opening either path drops the contactor.

For a **verified 230 VAC coil only**, one conceptual arrangement is::

    protected control L
       → overload NC trip contact (commonly 95–96; verify actual device)
       → J30.1 CTRL_IN
       → board K1 and K2 series contacts
       → J30.2 CTRL_OUT
       → contactor A1
    contactor A2 → control N

This example does not determine the actual starter's terminal numbers or
internal links. If the coil is 24 V, 110 V, DC, or anything else, retain its
correct control supply and redesign/qualify the coil interface accordingly;
do not connect A2 to mains neutral based on this example. Coil voltage, inrush,
holding load and suppression must be checked against the board relays.

Keep any required existing emergency-stop circuit in the verified coil chain.
This controller's STOP design is a functional stop, not a certified emergency
stop system. Keep protective earth bonded to the motor and metal enclosure;
there is no PE terminal on this PCB and isolated GND is not protective earth.

Identify and retain suitable motor overload protection and use manual reset. This board has no direct
overload-trip or contactor auxiliary feedback. Press and release physical STOP before resetting
an overload: some external interruptions would otherwise restore coil power
while the controller still requests run.

Motor-current sensor: J10
-------------------------

The external CT surrounds **one verified conductor carrying total motor
supply current**, after the contactor and before any capacitor/winding split.
Its exact location in this submersible starter must be traced; do not choose an
arbitrary START/RUN winding lead. Do not pass both supply L and N through the
same aperture: their currents would cancel. The CT is a sensor around the insulated wire, not a series
electrical connection in the motor conductor.

Connect its two secondary leads to J10.1 (CT high) and J10.2 (meter return).
The specified 6.8-ohm burden must remain permanently across the CT secondary
at the CT. Define polarity during meter calibration; swapped leads can reverse
real-power sign. Do not disconnect the secondary under load.

**J10 is mains-referenced in this design.** Its return is internally referenced
to neutral. Keep CT secondary wiring insulated and routed in the hazardous
compartment; do not join it to J32.7, OLED ground, probe common or earth.

Water sensors
-------------

.. list-table:: Existing probe connections
   :header-rows: 1
   :widths: 20 80

   * - PCB terminal
     - Sensor wire
   * - J20.1
     - Tank common electrode, below the lowest level and normally immersed.
   * - J20.2
     - L1, the lowest tank level electrode.
   * - J20.3
     - L2, next level up.
   * - J20.4
     - L3, next level up.
   * - J20.5
     - L4, the full/stop level electrode.
   * - J21.1
     - Inlet water electrode.
   * - J21.2
     - Valid inlet reference electrode in the same water body.
   * - J31.1 and J31.2
     - Two wires of a separate high-high float contact: closed normally,
       opening at excess tank level. This is not a bare conductive electrode.

Disconnect all reused probes from the previous controller. The existing single
inlet wire cannot work on its own unless its proper water reference is
identified. Do not use mains neutral, earth or an unverified metal pipe as that
return. The high-high contact at J31 is independent of the four tank probes;
an open J31 loop prevents running. A link used in controlled bench work removes
that independent protection and is not an overflow sensor.

Small OLED screen: J33
----------------------

Mount the purchased Waveshare 14657, 0.91-inch 128×32 OLED behind a protected
window in the starter lid. Its module PCB is 36×12.5 mm. The main board mounts
inside the enclosure; the screen is a separate part joined by this cable.
No separate level LEDs are fitted in the current design.

.. list-table:: Actual signal mapping; not a straight 1-to-1 numbered cable
   :header-rows: 1
   :widths: 25 30 45

   * - Main-board J33
     - Signal
     - OLED module connector
   * - 1
     - +3.3 V
     - 4, VCC
   * - 2
     - Isolated GND
     - 3, GND
   * - 3
     - SDA, data
     - 2, SDA
   * - 4
     - SCL, clock
     - 1, SCL

J33 uses JST GH 1.25 mm; the selected display uses PH 2.0 mm. They are different
connectors, so use a correctly terminated adapter harness. Check the actual
mating-face drawings and continuity; the apparent left/right order changes
when a connector is viewed from its other side. Use the controller's 3.3 V
supply, not a separate 5 V feed. Keep this cable short, provisionally ≤100 mm,
inside the isolated area. See ``oled-selection.txt`` for the detailed mapping
and shared-bus requirements. [3]_

Finding the connectors on the PCB
--------------------------------

In the supplied connector-map drawing, look down on the main component side
with the 90 mm edge horizontal and J1 at the upper left. These directions
refer to PCB pads, not the mating face of a loose cable plug:

* J1, upper left: pin 1 left, pin 2 right.
* J30, left edge below J1: pin 1 above pin 2.
* J10, lower left: pin 1 left, pin 2 right.
* J32, upper right: pins 1 through 7 run top to bottom; leave 4 and 6 unwired externally.
* SW3 SET/RESET and SW4 NEXT/+: top component side near the right edge,
  above the J2 service header; SW3 is above SW4.
* J33, right centre: signal pads 1 through 4 run left to right.
* J31, lower centre: pin 2 above pin 1.
* J20, lower right-centre: pin 5 at the top down to pin 1 at the bottom.
* J21, lower right: pin 2 left, pin 1 right.

J2 is an internal programming/service header. J34 is reserved for internal
expansion. Neither is a field power input. Do not connect a USB cable's 5 V
wire to either header; the documented service procedure uses isolated bench
power with mains disconnected.

Sources and design authority
-----------------------------

The terminal map above is checked against ``design/circuit.json`` and the
final native PCB. ``hardware/wiring/connector-locations.json`` records the
actual pad coordinates and source-board hash. No core electrical design is
changed by this wiring guide.

.. [1] Schneider Electric, DOL contactor/overload variants and mechanical
   plunger STOP construction:
   https://www.se.com/nl/nl/faqs/FA139744/

.. [2] Schneider Electric, single-phase motor connection and overload pole
   arrangement; exact device diagrams and terminals must be checked:
   https://www.se.com/nl/en/faqs/FA141338/

.. [3] Waveshare 0.91-inch OLED module and schematic:
   https://www.waveshare.com/wiki/0.91inch_OLED_Module
   https://files.waveshare.com/upload/2/2a/0.91inch_OLED_Module_Schematic.pdf

.. [4] RMG DFAWLC-044 installation manual, related product only; installed
   model is not confirmed. See page 2 for separate starter relay connections:
   https://rmgautomation.com/Downloads/Manual/DFAWLC-044-100101.pdf

.. [5] RMG catalogue distinguishes starter relay variants:
   https://rmgautomation.com/Wired_Automatic_Water_Level_Controller
