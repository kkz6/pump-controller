# Connectors and relay selection

The main PCB is a pilot controller. The starter's contactor and its factory capacitor circuitry carry the motor current. The two output connectors each expose an independent normally open contact. At both plugs pin 1 is COM and pin 2 is NO. The front labels are ordered as viewed at the connector. Follow the cavity numbering when assembling a plug.

| Verified starter interface | K1 → J30, channel A | K2 → J35, channel B |
| --- | --- | --- |
| Conventional three-wire DOL with automatic capacitor starting and a self-holding contactor | Maintained run permission in the starter control circuit | Momentary pickup request |
| Electronic starter accepting separate normally open commands | START pulse | STOP pulse |
| Documented maintained RUN input | Maintained RUN | Leave open |

A conventional DOL must keep its original NC STOP and overload in the coil supply path, ahead of every local, remote and holding branch. Opening either device interrupts the coil even if a controller contact is held. If K2 welds while K1 is closed, releasing the original STOP or resetting the overload can cause another pickup. A CT reports motor current after the fact. The optional mode key selects firmware behavior. Independent operation with the controller unplugged requires a suitable transfer arrangement in the existing starter.

Confirm what the original START actually switches. An 8 A motor reading is consistent with substantially higher starting current. A coil-only START input lets that surge stay entirely within the starter. A start button that also switches the start capacitor, an electronic keypad matrix, and an undocumented RUN input each need a separate interface assessment. A self-latching electronic starter can continue running when controller power disappears.

## Replaceable relays

K1 and K2 each take one Omron G6B-1114P-US-P6B DC5 in one P6B-04P socket with a P6B-C2 clip. The board drives their 5 V DC coils and provides local flyback diodes. Omron rates these contacts at 2 A at 250 V AC for an inductive load at power factor 0.4, or 2 A at 30 V DC with L/R of 7 ms. Its low-level switching reference is 10 mA at 5 V DC. Verify the actual starter coil's AC/DC voltage, pickup, holding burden, permissible switching duty and the starter manufacturer's coil suppression. For an electronic input verify its contact current and command polarity. The PCB relay flyback diodes protect the PCB's own coils only. [Omron G6B](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6b.pdf)

## Main board connections

| Marking | Use |
| --- | --- |
| J1 MAINS | Protected supply ahead of the contactor, on the same supply as the motor. The onboard meter reads this voltage with the motor on or off. |
| J10 LIVE CT | Fixed-burden CT harness around one insulated motor-feed conductor. J10 is mains-referenced. Fit the burden and verify the insulated harness before using the CT. |
| J20 TANK | Five tank wires. Pin 1 is common, with levels 1–4 on pins 2–5. |
| J21 INLET / RET | Inlet electrode and dedicated inlet return. This revision drives the return separately. A single inlet wire that depends on tank common needs a compatible sensing interface. |
| J32 PANEL | Straight 12-way keyed loom to panel J1. Use only a pinned and continuity-checked harness. |
| J30 A, J35 B | Starter control contacts. Four terminals support independent inputs. Share a common only where the starter diagram specifies it. |
| J40 USB, J41 supply selection, J2 debug | Bench service and programming. [USB guide](programming.md) |

## Panel connections

| Connector | Use |
| --- | --- |
| J1 | Host loom to main J32. |
| J2 | Optional external button station. Pairs 1–2 START (NO), 3–4 STOP (NC), 5–6 MODE (NO), 7–8 SET (NO), 9–10 NEXT (NO). Use the captive 3–4 loop plug for local-only operation. |
| J7 | Four-wire plug-in OLED. 1 SCL, 2 SDA, 3 GND, 4 +3.3 V. Verify the selected display cable's pin order. |
| J8 | Optional break-before-make key switch. 1 common +5 V, 2 MAN, 3 AUTO. |

The green START CMD and red STOP CMD lights report firmware commands. Motor current from the CT provides separate running feedback. USB TX and USB RX are a separate pair of green indicators. [Panel harness parts](../hardware/panel/harness-parts.csv)
