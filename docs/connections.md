# Connectors and relay selection

The main PCB is a pilot controller. The starter's contactor and its factory capacitor circuitry carry the motor current. The two output connectors each expose an independent normally open contact. At both plugs pin 1 is COM and pin 2 is NO. The front labels are ordered as viewed at the connector. Follow the cavity numbering when assembling a plug.

| Verified starter interface | K1 → J30, channel A | K2 → J35, channel B |
| --- | --- | --- |
| Conventional three-wire DOL with automatic capacitor starting and a self-holding contactor | Maintained run permission in the starter control circuit | Momentary pickup request |
| Electronic starter accepting separate normally open commands | START pulse | STOP pulse |
| Documented maintained RUN input | Maintained RUN | Leave open |

A conventional DOL must keep its original NC STOP and overload in the coil supply path, ahead of every local, remote and holding branch. Opening either device interrupts the coil even if a controller contact is held. The installation must require a fresh START after STOP release or overload reset, including with START held or its relay contact welded. The current direct wiring can pick up again under those conditions. Qualify an existing restart inhibit on the exact starter and input, or provide an independent hardware inhibit. A CT reports motor current after the fact. The optional mode key selects firmware behavior. Independent operation with the controller unplugged requires a suitable transfer arrangement in the existing starter. [Direct controller audit](../verification/direct-controller-audit.md)

Confirm what the original START actually switches. An 8 A motor reading is consistent with substantially higher starting current. A coil-only START input lets that surge stay entirely within the starter. A start button that also switches the start capacitor, an electronic keypad matrix, and an undocumented RUN input each need a separate interface assessment. A self-latching electronic starter can continue running when controller power disappears.

## Replaceable relays

K1 and K2 each take one Omron G6B-1114P-US-P6B DC5 in one P6B-04P socket with a P6B-C2 clip. The board drives their 5 V DC coils and provides local flyback diodes. Omron rates these contacts at 2 A at 250 V AC for an inductive load at power factor 0.4, or 2 A at 30 V DC with L/R of 7 ms. Its low-level switching reference is 10 mA at 5 V DC. Verify the actual starter coil's AC/DC voltage, pickup, holding burden, permissible switching duty and the starter manufacturer's coil suppression. For an electronic input verify its contact current and command polarity. The PCB relay flyback diodes protect the PCB's own coils only. [Omron G6B](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6b.pdf)

If the starter contactor coil needs additional suppression, use the starter manufacturer's accessory rated for that coil and verify actual dropout time with it fitted. Any suppressor placed across a command contact needs an off-state leakage check against the electronic input's assertion threshold. [Omron contact protection guidance](https://www.ia.omron.com/support/faq/answer/36/faq02804/)

## Main board connections

| Marking | Use |
| --- | --- |
| J1 MAINS | Protected supply ahead of the contactor, on the same supply as the motor. The onboard meter reads this voltage with the motor on or off. |
| J10 LIVE CT | Fixed-burden CT harness around one insulated motor-feed conductor. J10 is mains-referenced. Fit the burden and verify the insulated harness before using the CT. |
| J20 TANK | Five tank wires. Pin 1 is common, with levels 1–4 on pins 2–5. |
| J21 INLET / RET | Pin 1 is the inlet sense electrode. Pin 2 is the separately driven return for a dedicated inlet pair. Leave pin 2 empty when the inlet shares J20.1. |
| J32 PANEL | Straight 12-way keyed loom to panel J1. Use only a pinned and continuity-checked harness. Pin 1 is fed through U42, a TPS2553 limited to 110–150 mA, so a short in the loom, STOP chain or external station drops only K1 and the panel inputs and leaves the board's 5 V rail up. |
| J30 A, J35 B | Starter control contacts. Four terminals support independent inputs. Share a common only where the starter diagram specifies it. |
| J40 USB, J41 supply selection, J2 debug | Bench service and programming. [USB guide](programming.md) |

### Inlet sensing on a six-core cable

The AC excitation from U20 reaches J20.1 through R115, C106/C108, R116 and R117. Water between the common and the inlet sense electrode completes the sensing path through J21.1, R170/R171 and C128 into U21 channel 5 and the ADC. Leave the second driven output on J21.2 open in this arrangement.

The existing single inlet electrode can share the tank common through the water when there is a continuous conductive path. Air gaps, falling droplets and an exposed tank common can interrupt it. A six-core alternative adds a physical return electrode beside the inlet sense tip. Branch the J20.1 conductor at the tank to both the tank common and the new inlet return. The long cable still carries COM, L1–L4 and INLET. Place the inlet pair where pumped water bridges the tips and drains when delivery stops. Keep both driven outputs isolated from each other, protective earth, neutral and metal piping.

Commission the pair with the real cable and water, including an empty tank and all four tank levels wet. A wet film, standing water or a shorted pair can all look wet without delivery. Use the inlet reading alongside independently measured motor load for dry-run protection. For a dedicated two-wire inlet run, connect the inlet return to J21.2 and keep it separate from J20.1.

## Panel connections

| Connector | Use |
| --- | --- |
| J1 | Host loom to main J32. |
| J2 | Optional external button station. Pairs 1–2 START (NO), 3–4 STOP (NC), 5–6 MODE (NO), 7–8 SET (NO), 9–10 NEXT (NO). Use the captive 3–4 loop plug for local-only operation. |
| J7 | Four-wire plug-in OLED. 1 SCL, 2 SDA, 3 GND, 4 +3.3 V. Verify the selected display cable's pin order. |
| J8 | Optional break-before-make key switch. 1 common +5 V, 2 MAN, 3 AUTO. |

For an enclosure with only MODE, SET/RESET and NEXT exposed on its lid, the factory START and STOP actuators can also signal panel J2 through separate, electrically isolated, low-level auxiliary contacts. Use J2 pins 1–2 for NO START and pins 3–4 for NC STOP. Keep the original starter's power-rated contacts in their original circuits. The auxiliary contact arrangement depends on the actual starter button blocks and needs a first-article fit and continuity check. Base any lid or carrier on the current panel F board and its connector clearances. [Panel mechanical interface](../hardware/panel/connector-mechanical-interface.json) · [Panel harness parts](../hardware/panel/harness-parts.csv)

The green START CMD and red STOP CMD lights report firmware commands. Motor current from the CT provides separate running feedback. USB TX and USB RX are a separate pair of green indicators. [Panel harness parts](../hardware/panel/harness-parts.csv)
