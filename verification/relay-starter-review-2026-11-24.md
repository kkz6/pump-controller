# Relay alternatives and starter load review - 2026-11-24

## Result

The existing board remains a pilot controller for a verified starter coil or command input. Typical small 230 V AC contactor coils are comfortably below the existing relay's published 2 A / 250 V AC inductive current rating. This is a voltage/current screening result, not completed switching-life or installed-starter qualification.

A higher contact-current marking on a replacement relay does not qualify this PCB for direct motor or start-capacitor switching. Other-brand candidates exist, but none is approved here as a complete drop-in capacitor-starter solution. No BOM, schematic, PCB or firmware was changed.

## Existing hardware, checked from the native board and BOM

- K1 and K2: Omron G6B-1114P-US DC5, soldered directly; 5 V DC, nominal 40 mA coils; SPST normally open contacts.
- Actual land pattern: pin 1 at (0, 0), pin 6 at (0, -7.62), pin 3 at (10.16, 0), pin 4 at (17.78, 0), in local footprint coordinates. All four holes are 1.1 mm. Pin 6 is coil positive, pin 1 coil negative, pins 3/4 are the switched contact.
- J30/J35 expose dry contacts. An external contactor requires its own correctly rated control supply.
- K1's supply shares the panel/STOP current-limited branch. U42 is specified for a 110-150 mA current limit, including the panel and external station. A substantially higher-current replacement coil needs a new worst-case supply budget.
- The fitted relay has 5 A / 250 V AC resistive and 2 A / 250 V AC inductive ratings at power factor 0.4. These are different load ratings.

Native routing inspection (tracks, vias and zones):

| Net | Track width | Layers | Total routed track length | Separate vias |
| --- | --- | --- | --- | --- |
| CTRL_A_COM | 0.5 mm | F.Cu | 36.66 mm | 0 |
| CTRL_A_NO | 0.5 mm | F.Cu, B.Cu | 45.61 mm | 1 |
| CTRL_B_COM | 0.5 mm | In3.Cu | 37.74 mm | 0 |
| CTRL_B_NO | 0.5 mm | In3.Cu, B.Cu | 46.45 mm | 1 |

Each separate via has a 0.65 mm pad and 0.3 mm drill. No copper zones were found for these four nets. Through-hole component pads also connect layers; the separate-via count excludes those pads. The fabrication instructions request 1 oz outer copper; the native PCB does not declare an inner copper stackup. No temperature-rise, via-plating or pulse-I-squared-t qualification was performed. Consequently no new 8 A, 10 A or 16 A board-output rating is established by this review.

Sources in this repository: `hardware/main/bom.csv`, `hardware/main/pump-direct.kicad_pcb`, `manufacturing/README.md`, `docs/connections.md`.

## Representative DOL control-coil loads

These are manufacturer examples, not measurements of the photographed EURO contactor or a guarantee for all DOL starters. Values below assume the appropriate 230 V AC coil variant at 50 Hz. Coil current is calculated as apparent power VA divided by voltage; no extra power-factor division is appropriate.

| Contactor family | Pickup burden | Holding burden | Calculated pickup current at 230 V | Calculated holding current at 230 V |
| --- | --- | --- | --- | --- |
| Schneider LC1K / LC2K | 30 VA | 4.5 VA | 0.130 A | 0.020 A |
| Schneider LC1D09 through LC1D38 | 70 VA | 7 VA at 50 Hz | 0.304 A | 0.030 A |
| Lauritz Knudsen / L&T MNX 9-22 | 68 VA | 11 VA | 0.296 A | 0.048 A |

The existing Omron's 2 A inductive rating exceeds these representative pickup currents by about 6.6-15.3 times. This arithmetic is not a certified pilot-duty or endurance margin: the actual making waveform, power factor, interruption duty, suppression, supply sag and dropout must still fit the selected relay and starter specifications.

Do not generalize this result to other coil voltages. For example, a 70 VA coil at 24 V AC draws approximately 2.92 A during pickup. A 415 V AC coil also exceeds the current Omron relay's 250 V AC rated-load voltage; its 380 V AC maximum switching voltage does not authorize 415 V operation.

Manufacturer sources:

- [Schneider LC1K coil burden](https://www.se.com/ca/en/faqs/FA108156/)
- [Schneider LC1D09-38 coil burden](https://www.se.com/ca/en/faqs/FA112524/)
- [Lauritz Knudsen contactor coil table](https://www.lk-ea.com/blogs/control-transformer-sizing-for-contactor-actuation), MNX Power Contactors section
- [Omron G6B datasheet](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6b.pdf), PDF pages 4, 7-8

## Other-brand candidates

| Candidate | Relevant load evidence | Coil / mechanical assessment | Disposition |
| --- | --- | --- | --- |
| Omron G6B-1174P-US DC5 | 8 A resistive, but still 2 A inductive at 250 V AC | Same nominal four-pin layout and 40 mA coil; body height 12.5 mm rather than 10 mm | Closest family upgrade; does not qualify capacitor duty or increase the PCB current rating |
| Hongfa HF33F-G, 5 V sensitive-coil Form A version | 10 A / 250 V AC resistive; AgSnO2 contacts; VDE table includes 4.4 A making / 2.2 A breaking at 277 V AC | 125 ohm, 40 mA nominal coil. Approx. 20.5 x 10.2 x 15.7 mm. Nominal pitches 10.2 / 7.6 / 7.6 mm, close to the present 10.16 / 7.62 / 7.62 mm. Manufacturer recommends 1.3 mm holes, versus this PCB's 1.1 mm | Promising sample candidate; hole tolerance, insertion, height, insulation and switching-life checks remain. Not an approved drop-in |
| Panasonic ALQ305 / ALQ3F05 | General rating 5 A / 250 V AC. Catalog also lists 240 V AC pilot-duty approvals and VDE 10 A / 250 V AC at PF 0.4 for 10,000 operations | 5 V, 40 mA; nominal four-pin pitches match. Body 20 x 10 x 16 mm; recommends 1.3 mm holes | Pilot-control candidate requiring fit and duty qualification; the headline 10 A figure does not give blanket capacitor suitability |
| Panasonic ALQ6F12 / ALQ6F24 | Specifically offers capacitive-inrush capability, 40 A for 100 microseconds, with defined application conditions | Same nominal pin layout; available in 12 V / 24 V coils, not the present 5 V drive | Not electrically interchangeable on this board; does not establish suitability for a motor-start capacitor waveform |
| TE Connectivity RT314005 | 16 A contact rating at 250 V AC; separate making-current constraints apply | 5 V, 62 ohm coil, about 80.6 mA; body 29 x 12.7 x 15.7 mm, different pin pattern | Requires PCB/layout and supply-budget review; not a same-hole replacement |

Hongfa's standard 5 V coil is approximately 91 mA (55 ohms), versus 40 mA for the sensitive coil. Its TV-5 approval is explicitly for the standard coil type, so that approval must not be silently transferred to the sensitive variant. An exact order code, currently available genuine part and matching approval must be established before purchasing.

Manufacturer sources:

- [Hongfa HF33F-G datasheet](https://source.hongfa.com/Uploads/Product/PDF/HF33F-G_en.pdf), 2025 Rev. 1.00, all three pages inspected
- [Panasonic LQ catalog](https://industry.panasonic.com/ac/cdn/e/control/relay/power/catalog/mech_eng_lq.pdf), 2026.7, especially PDF pages 3-5 and 8-10
- [Panasonic LQ inrush version](https://industry.panasonic.eu/products/components/relays/power-relays/lq-power-relay)
- [TE RT314005 product specifications](https://www.te.com/en/product-9-1393239-1.html)

Similar pin-center geometry is not a manufacturer-certified substitution. Recommended hole diameters, tolerances, body clearance, insulation, contact function and coil behavior all matter. Do not enlarge plated holes on the finished board to force an alternate part to fit.

## Capacitor and motor loads

The motor's full-load current is carried by the starter's power circuit, not by a verified coil-only START command. If a green-button contact also inserts a start capacitor, its load is a separate winding/capacitor circuit; motor running amps do not determine that contact's required making capability.

For scale only, an ideal standalone capacitor directly across a 230 V, 50 Hz sine source would draw I = 2*pi*f*C*V:

| Capacitance shown in the supplied illustrative drawing | Calculated ideal-capacitor RMS current |
| --- | --- |
| 36 microfarads | 2.60 A |
| 120 microfarads | 8.67 A |
| 150 microfarads | 10.84 A |

These are not measured or predicted currents for this motor: the actual winding circuit, capacitor voltage, remaining charge, series impedance, rotor speed and switching instant alter the waveform. They must not be used as a relay-selection calculation. Capacitive inrush can be much higher than steady current; Panasonic specifically calls for measuring the actual load waveform and assessing contact welding and electrical life. Its generic inrush multipliers are not a prediction for this particular motor capacitor.

- [Panasonic load-selection guidance](https://tp.industry.panasonic.com/en/products/control/relay/cautions_use)
- [RMG capacitor-starter interface guidance](https://rmgautomation.com/Downloads/Manual/WWLC-Tank%20%26%20Sump.pdf#page=4): PDF page 4 describes an additional AC contactor for capacitor-type starters.

## Installation decision

1. Verified 230 V coil-only START/STOP: retain the existing Omron relays unless actual duty or endurance data indicate a reason to change; representative coils pass initial voltage/current screening.
2. Dedicated electronic command inputs: qualify dry-contact compatibility, wetting current, pulse/maintained behavior and power-loss stop behavior. A larger power relay is not automatically better for a low-current input.
3. START contact switching the capacitor branch: do not approve direct J35 connection from an 8 A / 10 A / 16 A headline rating. Use an appropriately selected external starter interface/contactor, or redesign and qualify the PCB load path.
4. The actual photographed starter still needs its motor HP, contactor model, coil voltage and traced button functions. Its existing large current marking is not proof of coil voltage or current. No energized measurements were made.
5. Adding a contactor or changing relay brand does not itself prevent a restart after a welded/held START contact. The independent restart-inhibit issue from the previous review remains separate.

This review is limited to documented specifications, arithmetic and native layout inspection. It does not claim an assembled-board thermal, dielectric, EMC, endurance or motor-start test pass.
