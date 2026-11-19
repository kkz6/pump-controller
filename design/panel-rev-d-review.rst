Rev D panel electrical review
============================

Scope: proposed low-voltage button/OLED daughterboard and optional maintained
AUTO/MANUAL key selector. This review does not release the hardware for
manufacture or establish electrical, mechanical or EMC performance.

Harness and momentary contacts
------------------------------

The proposed 12-way panel harness preserves these ten main-board signals and
adds the two existing expansion inputs. Final connector numbering must agree
with the released schematic and cable drawing.

==== ==================== =============================================
Pin  Panel signal         Main-board connection
==== ==================== =============================================
1    +5V                  J32.1
2    STOP_RETURN          J32.2
3    MAN_RETURN / MODE    J32.3
4    AUTO_RETURN / NEXT   J32.4
5    START_N              J32.5
6    RESET_N / SET        J32.6
7    GND                  J32.7; J33.2 is the same PCB net, unwired
8    +3V3                 J33.1
9    I2C_SDA              J33.3
10   I2C_SCL              J33.4
11   KEY_MAN_N            J34.5 / SPARE_B6
12   KEY_AUTO_N           J34.6 / SPARE_B7
==== ==================== =============================================

Local STOP is normally closed. Connect +5V through local STOP, then through
the external STOP NC loop, to STOP_RETURN. If no external STOP is installed,
fit the explicitly identified link in that external loop only. A link must
never bridge the local STOP contact. Additional STOP contacts go in series.
No series resistor, diode or hold-up capacitor belongs in this relay-coil
permission path.

The other local buttons and corresponding external dry-contact connections
are normally open and parallel:

* START: START_N to GND.
* SET/RESET: RESET_N to GND.
* MODE: MAN_RETURN to STOP_RETURN.
* NEXT/+: AUTO_RETURN to STOP_RETURN.

Existing starter actuators may supply these signals only through verified
separate isolated auxiliary contacts. Keep their original mains and
capacitor-start contacts separate. No mains or capacitor lead belongs on
the panel or these headers.

Button selection
----------------

STOP: Omron D2F-01F, pin-plunger SPDT with straight PCB terminals. Facing the
marked side with the plunger toward the left, terminals run COM, NO, NC from
left to right. The proposed footprint convention is pad 1 COM, pad 2 NO,
pad 3 NC, at 0, 5.08 and 10.16 mm. These numeric pad assignments are a design
convention; the manufacturer identifies the contacts by function. Leave NO
electrically unconnected. Manufacturer reference mounting uses three 1.2 mm
holes; the housing envelope is approximately 12.8 x 5.8 mm. Actuator height,
travel and the insulating push-cap require mechanical review.

The gold-alloy D2F-01 contact has a 0.1 A / 30 VDC resistive rating and a
minimum-load reference of 1 mA / 5 VDC. Add 2.2 kohm, 1%, 0.1 W from the
final STOP_RETURN to GND. This supplies approximately 2.3 mA wetting current
while K1 is off, instead of relying on the existing approximately 91 uA
sense-divider current. At 5.5 V this resistor dissipates under 14 mW.
K1's existing flyback diode remains at its coil. Contact operation with the
actual coil and mechanical assembly requires testing.

The four NO buttons can retain Omron B3U-1000P. Contacts 1 and 2 close on
press; orientation is electrically interchangeable. Its 3 x 2.5 mm body,
1.6 mm top-actuated height and small travel require suitable insulating
push-caps. The minimum-load reference is 10 uA at 1 V; estimated existing
START/SET and MODE/NEXT currents exceed that reference. Debounce remains a
firmware responsibility; do not debounce or delay the physical STOP path.

Primary drawings, including terminal diagrams, were inspected:

* https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf, pages 2-4.
* https://omronfs.omron.com/en_US/ecb/products/pdf/en-b3u.pdf, pages 1-2.

Optional maintained key selector
--------------------------------

Use a break-before-make maintained SPDT selector with contacts suitable for
the actual low-voltage load: common +5V, throws KEY_MAN_RAW and KEY_AUTO_RAW.
Each raw throw gets 2.2 kohm to GND for wetting current. The selector is a
mode request; it has no connection that bypasses STOP, high-high protection
or the relay permission logic.

Use one onsemi MMBT3904LT1G per channel: base pin 1 from RAW through 10 kohm;
100 kohm from base to emitter; emitter pin 2 to GND; collector pin 3 to the
key sense signal. Pull the collector up to +3V3 through 10 kohm and filter it
with 10 nF to GND. All resistors are 1%, 0.1 W. The existing main-board
100 kohm pull-down remains. Do not enable GPIO internal pull-ups or configure
these signals as outputs.

Closed key contacts produce LOW. With neither channel asserted, the 10 kohm
pull-up and 100 kohm pull-down produce 0.909 x VDD nominal, or at least
0.9074 x VDD from resistor tolerance alone. MCP23017 specifies VIH >= 0.8 x
VDD and input leakage up to 1 uA. The approximately 0.35 mA collector load
has ample base drive at nominal supply; verify low voltage and leakage over
the intended temperature range. Nominal release filter time is 91 us.

Key input truth table, ordered MAN then AUTO:

* 01: MANUAL selected.
* 10: AUTO selected.
* 11: neither contact closed; invalid in configured key mode.
* 00: both selected, or panel/harness unavailable; invalid in key mode.

Key mode must be explicitly configured. Invalid states and mode changes
remove permission; a change must not start the pump. MODE-button arbitration,
contact transitions, disconnection and rearming require firmware tests.

The proposed passive 10 kohm / 15 kohm divider was rejected. Including the
existing 100 kohm pull-down, its minimum 1% ratio is 0.561118. A conservative
25 C static 5 V estimate of 4.835 V from 2% accuracy, 0.3% line and 1% load
terms gives only 2.713 V HIGH. TPS62162 power-save +4% allows 3.432 V, making
MCP23017 VIH 2.7456 V. This already lacks margin before temperature,
transients and leakage. The NPN arrangement makes logic HIGH track +3V3.

Sources:

* https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf, pages 1-2.
* https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf, pages 3-4.
* https://www.ti.com/lit/ds/symlink/tps62160.pdf, page 6. Initial output
  accuracy excludes line/load regulation; power-save limits are -3.5/+4%.
* https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf, pages 2-4.
  The arithmetic above is an engineering worst-case combination, not a
  separately guaranteed assembled-system supply tolerance.

OLED, filtering and cable validation
------------------------------------

Provide 100 nF and 4.7 uF local X7R bypassing across panel +3V3 and GND.
Do not add another I2C pull-up set without checking the actual OLED module;
the main board already has 3.3 kohm pull-ups. The Waveshare module terminal
order is SCL, SDA, GND, VCC; connect by signal name, not cable order.

Existing main-board SET/START inputs have 1 kohm series, 10 kohm pull-up and
100 nF filtering. MODE/NEXT use 22 kohm / 33 kohm dividers with 10 nF filters.
These are signal-conditioning networks, not proof of ESD immunity.

Optional panel TVS footprints may use TI TPD1E10B06 in its exact selected
package: 5.5 V working voltage, bidirectional shunt to GND, 12 pF typical
capacitance. Keep the return short and near the exposed connection. Its
clamp voltage and the complete downstream protection need validation;
component ESD ratings do not establish system immunity. Do not place a
TVS across STOP in a way that could feed STOP_RETURN from +5V.
Primary source: https://www.ti.com/lit/ds/symlink/tpd1e10b06.pdf.

For the proposed internal cable up to approximately 300 mm, begin bus
qualification at 100 kHz. This is a proposed test length, not a guaranteed
I2C range. With 3.3 kohm pull-ups, the 0.8473*R*C approximation gives about
358 pF total for 1 us rise time, versus 107 pF for 300 ns. Include main-board
devices, OLED, cable, connectors and TVS capacitance, and measure both ends.
NXP permits 1 us rise time in Standard-mode and 300 ns in Fast-mode:
https://www.nxp.com/docs/en/user-guide/UM10204.pdf, pages 44 and 50.

Required prototype checks include each local/external contact, STOP-loop
open circuit, unplugged panel, key invalid states, held buttons through
power-up, no automatic restart after STOP, I2C rise time, transient/ESD
behavior and service access with the starter closed.
