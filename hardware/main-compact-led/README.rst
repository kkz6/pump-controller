Compact controller with START and STOP command LEDs
==================================================

This engineering revision adds two front-side 0603 surface-mount LEDs
beside the relay area on the isolated logic side. Each LED has its own
1 kΩ current-limiting resistor and returns to isolated GND. The expander
drives the LEDs directly. Neither LED is wired across a relay coil or a
starter button. The water-level display remains on the separate OLED panel.

=========  ==========  ====================  ========================
Indicator  Color       Expander output       Meaning of one flash
=========  ==========  ====================  ========================
D40        Green       U33 GPB7, pin 8       START command issued
D41        Red         U33 GPA7, pin 28      STOP command issued
=========  ==========  ====================  ========================

At 3.3 V, typical data-sheet forward voltages give about 1.4 mA for D40
and 1.5 mA for D41. The actual current depends on output voltage,
temperature and the LED. See the `green LED data sheet
<https://www.kingbrightusa.com/images/catalog/SPEC/APTD1608LCGCK.pdf>`_
and the `red LED data sheet
<https://www.kingbrightusa.com/images/catalog/SPEC/APT1608LSECK-J3-PRV.pdf>`_.

Starter behavior
----------------

A starter that explicitly accepts one maintained RUN contact and manages
its own starting capacitor can use one field output. Closing RUN issues START
and opening RUN issues STOP. A starter with separate commands needs an
independent START and STOP interface with the contact behavior and timing
specified for that model. The lights mean the same thing in either case.
An actuator change must take priority over any indicator write.

The relays K1 and K2 in this revision still provide one accessible contact
path at J30. The LEDs do not add the second physical output. The independent
`START/STOP relay interface <../../design/compact-starter-compatibility.rst>`_
and the `LOCAL MANUAL transfer <../../design/manual-transfer.rst>`_ are
separate designs. Keep the main-board purchase on hold for the button retrofit.
The earlier compact Gerber ZIP does not contain these LEDs.

Firmware behavior
-----------------

The `command LED component
<../../firmware/components/command_leds/command_leds.c>`_ generates a
250 ms flash for each issued command. A STOP preempts a START. Both LEDs
are normally off. The flashes do not set relay pulse duration. Measure
motor current through the CT to check the motor's response. A welded relay,
controller reset or lost I²C communication can make the lights misleading.

For integration with the future pump-control firmware:

* Clear bit 7 in both output latches before enabling those pins as outputs.
  Keep both internal pull-ups disabled. Preserve every other pin's settings.
  GPA0 and GPB6 are still the AUTO and MANUAL key inputs.
* After dispatching the actual relay command, call
  ``pump_command_leds_record`` once with the command events for that cycle.
  Ignore rejected requests. A hardware-only trip or a press on a disconnected
  starter keypad does not generate an issued-command indication by itself.
* Call ``pump_command_leds_render`` regularly with a monotonic millisecond
  counter and the expander owner's two desired output-latch bytes. Only
  bit 7 of each byte is updated. The I²C owner schedules the resulting
  OLATA/OLATB writes in the existing bus budget, outside probe acquisition
  windows. Serialize updates with other expander users, retain dirty bytes
  for retry and never construct the write from a GPIO input read.
* Initialize the component to zero at boot, clear it on entry to LOCAL
  MANUAL, and flush the off state after expander initialization or recovery.
  A pending LED update must never delay a STOP. Safety behavior for failure
  of the shared sensor bus is independent of the indicator.

See `Microchip's output-only pin advisory
<https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_
and the `MCP23017 register description
<https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf>`_.

Review files
------------

* `KiCad project <pump-controller-compact.kicad_pro>`_,
  `board layout <pump-controller-compact.kicad_pcb>`_ and
  `parts list <bom.csv>`_.
* `LED placement beside K2 <exports/relay-indicators.png>`_. The main
  board retains its 100 x 75 mm outline. Routing the red LED added about
  0.58 mm to the existing mode-sense trace on its original layer.
* `Editable circuit source <../../design/main-compact-led.json>`_ and
  `schematic PDF, LED circuit on page 8 <exports/schematic.pdf#page=8>`_.
* `Native CAD and isolation checks <checks/independent-summary.json>`_
  and `native copper and hole measurements <checks/independent-geometry.json>`_.
* `Command light timing and output-mask tests
  <../../firmware/components/command_leds/tests/command_leds_test.c>`_.

The command indicator component can run in a host test without hardware.
From the project root::

    cd firmware/components/command_leds
    cc -std=c11 -Wall -Wextra -Werror -Iinclude command_leds.c tests/command_leds_test.c -o /tmp/pump-command-led-test
    /tmp/pump-command-led-test

Full pump firmware, actual LED visibility, starter operation and electrical
noise performance still need bench verification.
