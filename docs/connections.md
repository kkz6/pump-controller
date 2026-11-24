# Connectors and relay selection

R3 exposes two independent changeover relay contacts at fixed screw terminals J30 and J35. Both terminal blocks sit at the top edge with wire-entry openings facing out of the board, clear of the relay bodies. Each terminal block is **1 NO, 2 COM, 3 NC**, matching the printed labels. The former two-way plugs do not fit. NC connects to COM while the relay coil is de-energized; NO connects to COM while energized. Use COM/NO for the existing firmware profiles below. Exposing NC does not establish power-loss STOP behavior for an undocumented starter. The factory starter retains motor overload protection and its capacitor-disconnect function.

| Verified starter interface | K1 → J30, channel A | K2 → J35, channel B |
| --- | --- | --- |
| Conventional three-wire DOL with automatic capacitor starting and a self-holding contactor | Maintained run permission in the starter control circuit | Momentary pickup request |
| Electronic starter accepting separate normally open commands | START pulse | STOP pulse |
| Documented maintained RUN input | Maintained RUN | Leave open |

A conventional DOL must keep its original NC STOP and overload in the coil supply path, ahead of every local, remote and holding branch. Opening either device interrupts the coil even if a controller contact is held. The installation must require a fresh START after STOP release or overload reset, including with START held or its relay contact welded. The current direct wiring can pick up again under those conditions. Qualify an existing restart inhibit on the exact starter and input, or provide an independent hardware inhibit. A CT reports motor current after the fact. The optional mode key selects firmware behavior. Independent operation with the controller unplugged requires a suitable transfer arrangement in the existing starter. [Direct controller audit](../verification/direct-controller-audit.md)

Confirm what the original START actually switches. An 8 A motor reading is consistent with substantially higher starting current. A coil-only START input lets that surge stay entirely within the starter. A start button that also switches the start capacitor, an electronic keypad matrix, and an undocumented RUN input each need a separate interface assessment. A self-latching electronic starter can continue running when controller power disappears.

## Relays

Printed assembly marks use three conventions: a filled triangle points toward numbered pin 1 on ICs, transistors and multi-pin diode packages; a bar/bracket identifies the cathode of an LED or single diode; a `+` identifies C1's positive lead. Pin-1 arrows are not a generic positive-voltage indication. The marks appear on each component's mounted side, so the bottom view is naturally mirrored. Ceramic capacitors, resistors and bidirectional PESD5V0S1BA TVS parts are non-polarized.

K1 and K2 are Omron G5RL-1-E-HR DC5 high-inrush SPDT relays, soldered to eight-pin lands and included in JLC assembly (C1563288). Each has a 5 V, 80 mA nominal coil. Connect both physical terminals of each contact: 3/6 COM, 4/5 NO, 2/7 NC. Manufacturer component ratings are 16 A NO and 5 A NC at 250 V AC resistive; the published inrush tests have specified peak, RMS and endurance conditions. These figures are not a tested board-level or unrestricted capacitor rating. [Manufacturer datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5rl.pdf)

All six field nets use 2.8 mm traces on both outer copper layers, with through-hole terminals connecting the layers. No field-current path depends on the old 0.3 mm vias. J30/J35 are Phoenix Contact 1711738 screw terminals (C91156), with a 24 A component rating. Actual allowable board current and starter pulse duty need temperature and waveform verification on the assembled first article.

Q50 (AO3401A P-MOSFET) supplies K1 from +5V_CMD. Q51 and R247 turn it on only while the panel STOP loop returns its permissive. R246 pulls Q50 off and R248 pulls Q51 off when the loop opens. The panel switch carries sensing/base current rather than the larger relay coil current; U42 retains its original 110–150 mA loom current limit. The low-side watchdog/arm gating and USB inhibit remain in the circuit. D31 is across the K1 coil at K1_5V/K1_LOW, so high-side interruption has a flyback path without forcing a semiconductor load-switch output below its absolute minimum voltage.

The target application is a 1.5 HP, 220 V capacitor-start starter. A suitably rated external starter interface/contactor is allowed if the actual START contacts carry capacitor current; its selection and wiring are outside this PCB revision. Direct capacitor switching has not been qualified by these layout checks. Retain the OEM disconnect function and verify the selected control input's bounded start pulse, stop, power loss and welded-contact behavior before connecting the pump. A larger relay and NC terminal do not independently disconnect a welded start-capacitor contact.

Treat all six output contacts and their cables as live mains, including unused NC terminals. Each contact net connects only its relay's two contact pins and its field screw terminal. None connects to the relay coil supply, controller ground, ESP32, USB, panel or probes. The PCB rules require 8 mm copper clearance and surface creepage from LIVE to isolated control nets across the board; the G5RL itself specifies 8 mm coil/contact insulation distance. The separate AC input, voltage meter and J10 CT circuit are intentionally mains-referenced and must also stay segregated from user-accessible wiring. Use the specified nylon mounting hardware and an insulated enclosure. These design checks do not establish immunity to every fault, contamination, surge or wiring mistake.

Capacitor switching must also remain within the relay's voltage rating: a 220 V supply alone does not establish the voltage and transient stress across a start-capacitor contact. Verify that stress on the actual starter before commissioning.

If the starter contactor coil needs additional suppression, use the starter manufacturer's accessory rated for that coil and verify actual dropout time with it fitted. Any suppressor placed across a command contact needs an off-state leakage check against the electronic input's assertion threshold. [Omron contact protection guidance](https://www.ia.omron.com/support/faq/answer/36/faq02804/)

## Main board connections

| Marking | Use |
| --- | --- |
| J1 MAINS | Protected supply ahead of the contactor, on the same supply as the motor. The onboard meter reads this voltage with the motor on or off. |
| J10 LIVE CT | Fixed-burden CT harness around one insulated motor-feed conductor. J10 is mains-referenced. Fit the burden and verify the insulated harness before using the CT. |
| J20 TANK | Five tank wires. Pin 1 is common, with levels 1–4 on pins 2–5. |
| J21 INLET / RET | Pin 1 is the inlet sense electrode. Pin 2 is the separately driven return for a dedicated inlet pair. Leave pin 2 empty when the inlet shares J20.1. |
| J32 PANEL | Straight 12-way keyed loom to panel J1. Use only a pinned and continuity-checked harness. Pin 1 is fed through U42, a TPS2553 limited to 110–150 mA. The returned STOP permissive controls Q50 rather than carrying K1 coil current, so a short in the loom, STOP chain or external station drops K1 and the panel inputs and leaves the board's 5 V rail up. Pin 8 carries the processor's +3.3 V without a limiter: a short there resets the controller, and U32 then clears the arm latch. |
| J30 A, J35 B | Two changeover outputs. Each block is 1 NO, 2 COM, 3 NC. Six terminals support independent inputs. Share a common only where the starter diagram specifies it. |
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

## Proposed internal CT and power feed

An internal CT can remove the installer-fitted external sensor. A possible enclosure arrangement is: protected incoming live branches to the controller supply and to a rated internal motor-feed conductor; that conductor passes once through an internal CT and leaves for the existing starter. Neutral uses its own rated feed-through terminal, and protective earth remains continuous to the required exposed metal and motor. Only the monitored live passes through the CT aperture. The starter retains motor switching, overload protection and capacitor disconnection. Measuring upstream of the starter also includes its coil and other downstream loads.

For the first version, an insulated internal conductor or suitable busbar through the CT is preferable to carrying the motor current through this controller's supply traces. PCB-mount CTs also exist, including [Talema's AC family](https://talema.com/products/low-cost-current-transformers-ac/); a board-mounted secondary still needs an appropriately designed primary conductor. Choose the CT ratio, permanent burden, input scaling and insulation for the motor nameplate current, startup behavior and metering range. Rate terminals, wiring, protection and thermal performance for that complete power path.

This is a proposed next architecture, **not implemented in the R3 Gerbers**. J1 remains the controller's own AC supply input, and J10 remains an external CT-secondary input. Do not route the motor feed through either existing input.
