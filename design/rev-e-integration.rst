Rev E installation and enclosure interfaces
==========================================

This revision uses a 100 x 80 mm six-layer main PCB and a 60 x 45 mm
low-voltage control panel. Native Zigbee is the primary firmware target;
Matter over Thread and Matter over Wi-Fi are separate planned builds on the
same ESP32-C6-MINI-1U-H8 hardware. Firmware is not implemented or bench-tested.
See wireless-architecture.rst for the Aqara M200 compatibility restriction.

Board edges and harnesses
------------------------

* Left main-board edge: J1 AC input and J30 contactor-coil control contacts.
* Bottom-left: J10 fixed current-transformer terminal. Its factory-captive
  lead belongs to the live metering domain; keep it separate from isolated
  sensor cables. There is no removable CT plug to fit into J31 or J21.
* Bottom-right: J31 high-high float loop, J20 tank probes and J21 inlet probes.
* Right main-board edge: J32 keyed GH12 cable to control-panel J1.
* Upper-right: J2 internal programming/service header, now 2.54 mm pitch.
* Panel top: J1 host cable. Panel bottom: optional external button contacts
  J2 through J6. Panel left: optional key J8. Panel right: plug-in OLED J7.

The panel cable is a factory-assembled JST GH 1.25 mm twelve-way female-to-
female harness, numbered 1-to-1, nominal 150 mm. Specify matching GHR-12V-S
housings and compatible crimp contacts; installer crimping is not required.
Its connection is:

====  ===================  ==========================================
Pin   Main J32 signal      Panel J1 purpose
====  ===================  ==========================================
1     +5V                  Hardwired normally closed STOP supply
2     STOP_RETURN          STOP return and MODE/NEXT common
3     MAN_RETURN           Momentary AUTO/MANUAL toggle
4     AUTO_RETURN          NEXT / increase button
5     START_N              START request, normally open to GND
6     RESET_N              SET / acknowledge request, normally open
7     GND                  Isolated logic ground
8     +3V3                 OLED / key conditioning supply
9     I2C_SDA              OLED data
10    I2C_SCL              OLED clock
11    SPARE_B6             KEY_MAN_N, active low
12    SPARE_B7             KEY_AUTO_N, active low
====  ===================  ==========================================

The optional key input has explicit enabled/disabled configuration. It does
not replace hardware STOP, high-high protection or the overload trip. Both
key positions asserted, neither asserted, and a disconnected panel are not
valid AUTO commands. A mode change disarms the pump and requires the defined
STOP acknowledgement and fresh start sequence.

Plug-in OLED
------------

Use Waveshare 14657, 0.91 inch, 128 x 32, with its PH2.0 connector. Panel J7
uses cavity 1 SCL, 2 SDA, 3 GND and 4 +3V3. Use a factory-crimped PH2.0 four-
way plug-to-plug cable, numbered 1-to-1, nominal 100 mm. A procurement
candidate is Pololu 5623:
https://www.pololu.com/product/5623

The supplier calls it PH-style; verify mating fit and numbered continuity
on the first assembly. Wire colours do not define supply polarity. A cable
with PH on one end and loose Dupont sockets on the other does not meet this
retained harness specification. GH1.25, SH1.0, XH2.5 and Grove connectors
are not substitutes. No OLED soldering is required during installation;
PCB assembly must fit the specified board receptacles beforehand.

Use 3.3 V for this display even though its module also accepts 5 V. Retain the shared 400 kHz I2C schedule required by the probe acquisition
slots and bounded OLED updates. Target at most 250 mm total main-to-panel-
to-OLED cable length (150 mm host plus 100 mm display); this is a layout
target, not a qualified cable-length limit. Measure Fast-mode rise time
against 300 ns and verify switching immunity on the actual harness. With
a single nominal 3.3k pullup, the simple RC estimate allows approximately
107 pF total bus capacitance at that rise-time limit. Include every module,
connector, trace and cable; account for any pullups on the purchased OLED.
Do not reduce the shared bus to 100 kHz without revising and validating the
probe time slots and OLED transfer budget. The rise-time estimate follows
TI SLVA689: https://www.ti.com/lit/an/slva689/slva689.pdf
The connectors are keyed but are not intended for live hot plugging.

Power and DOL connections
------------------------

J1 pin 1 is the protected installation line supply and pin 2 is neutral.
The controller is a small auxiliary load; the motor's power conductors do
not pass through this PCB. Maintain the installation's upstream isolation,
protective device, protective earth and existing motor overload protection.
Protective earth bonds the metal starter enclosure, not the isolated sensor
or button ground. The PCB has no protective-earth terminal.

J30 pin 1 CTRL_IN and pin 2 CTRL_OUT are the series dry-contact path through
two normally open relays. An electrician must integrate this path into the
verified contactor-coil circuit so either relay opening removes coil power.
The existing mains STOP and overload NC contacts remain in that coil chain.
Do not bridge them or route motor current through J30. The actual contactor
coil voltage and capacitor-start sequencing must be confirmed before the
old water controller is removed; the photograph alone does not establish
the terminal identities or the start-capacitor control method.

Existing START/STOP actuators can also operate the new panel through verified
isolated auxiliary contacts: external START to panel J2 and external NC STOP
to panel J3. Never connect a mains-switched contact wire to the low-voltage
panel. Fit the panel's external-STOP bypass shunt only when no external NC
STOP contact is installed. The onboard STOP remains in series in either case.
The single external MODE button connects to panel J4; SET and NEXT are J5
and J6. All four are normally open dry contacts, with pin maps in the panel
interface document. Existing capacitor-start contacts must remain functional.

J10 is Phoenix 1727010, a fixed screw terminal: pin 1 M_CT_HI, pin 2 M_GND.
Terminate and strain-relieve its live-domain lead during assembly; isolate
the pump supply before servicing it. Support the housing while tightening
at the manufacturer's 0.22..0.25 Nm torque. Do not add an interchangeable
inline plug. J10 accepts the selected CT with its permanent burden. Place the CT around
one motor supply conductor, never around both line and neutral together.
The existing analogue ammeter wiring is not an interchangeable CT signal.
J20 is common plus four level electrodes. J21 provides inlet and inlet-common
terminals: an existing single inlet lead is usable only if a valid water-side
reference can be established. Protective earth is not a probe-return shortcut.
J31 is a normally closed high-high float loop or its documented fitted link.

Mechanical retention and electrical noise
-----------------------------------------

The main PCB has four 3.2 mm NPTH mounts at (4,4), (96,4), (96,76), (4,76) mm.
Use insulating M3 fasteners and 18 mm minimum standoffs. The rear-mounted
C1 reservoir capacitor can project 13.5 mm below the board once installed.
Keep mounting hardware away from live copper. The panel has four 2.7 mm holes at (3,3), (57,3), (3,42), (57,42).
The standalone case files provide a screwed lid, board guard, panel carrier,
OLED retainer, captive button plungers and cable clamps. Plug and cable bend
clearances are included; actual printed fit remains a first-article check.

Keep the live and low-voltage cable groups in their separate entries and
channels. Keep the OLED/host cable away from the contactor, motor and capacitor
leads. Use the external 2.4 GHz antenna outside the metal starter or in the
plastic case's isolated area, with its RF cable kept away from live wiring.
A provisional bulkhead opening is not a specification for an unselected
antenna connector.

The PCB retains input protection, isolated power and signal paths, local
supply bypass capacitors, relay-coil flyback diodes, filtered protected inputs,
and separate live/isolated reference planes. The main board reserves layer 2 for the two ground domains, and layer 5 for the 3.3 V control supply and live meter ground. Interconnects use layers 1, 3, 4 and 6. Add the contactor manufacturer's
correct coil suppressor at the actual coil; its rating depends on the coil
voltage and type. Firmware must reject inconsistent probe sequences, debounce
contacts, limit automatic restarts, and keep dry-run/voltage/load decisions
local. Network loss must not disable these protections.

These measures reduce susceptibility; a CAD pass does not establish immunity.
Qualification includes repeated contactor starts/stops, brownouts, sensor
open/short faults, network loss, I2C errors, thermal soak and appropriate ESD/
EFT/surge testing. Do not describe the controller as noise-free or the printed
case as a certified mains enclosure on the basis of these files.
