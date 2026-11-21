# Design review, 2026-11-21

Three independent reviews checked the main and panel schematics pin by pin against the part datasheets:
- power, processor and USB
- metering, isolation barrier and analog sensing
- relay output stage, safety interlock and panel

None found a wiring error, a part wired to the wrong pin, or a signal outside its rated limits. The automated checks also pass:
- ERC is 0 and DRC is 0/0/0 with schematic parity on both boards.
- The Gerber connectivity check finds no opens or shorts, and it catches deliberately injected faults.
- The named-pin interface checks pass.
- All firmware host tests pass.

## Fixed in revision 1

| Ref | Change | Why |
| --- | --- | --- |
| C49, C50 | 27 pF → 33 pF C0G (C91368) | Gives Y1 about 21 pF load against its 20 pF rating, so the meter clock runs on frequency. |
| R110, R112 | 100 Ω → 1 kΩ | More stability margin for U20C/U20B driving the 10 nF ADC filter capacitors. The isolation zero moves to 16 kHz, well below the op-amp's 1 MHz bandwidth. |
| U11 | Description | Available VISO current at VDD = 3.3 V is about 73 mA, not 130 mA. The meter needs about 10 mA. |
| C60, FB1, FB2 | Descriptions | Pin numbers corrected. FB1/FB2 stay 0 Ω: a ferrite there would isolate C58 rather than filter VISO. |
| Firmware | Comment | On the direct main board, expander pins A2/A3 drive the USB LEDs. A1 and A4–A6 are unused and must be configured as inputs with pull-ups. |

## Deferred to revision 2

These need new copper. The logic area around U31, U34, U33 and the lower edge of U3 has no free track channel or via site left. Fitting them means moving existing tracks with an interactive push-and-shove router, so they are deferred rather than squeezed in by script.

| Item | Benefit | Revision 1 mitigation |
| --- | --- | --- |
| Read ARM_Q and PERMIT_Q back into the processor (spare ESP32 GPIO4/GPIO5 or U33 GPA1/GPA4) | Software can confirm that the latch cleared at reset, took each arm pulse, and keeps K1's gate low when it should | Test every clear path at bring-up ([bring-up test](../docs/bring-up.md#3-arm-latch-test)) |
| 10–22 µF bulk next to U11 VDD (C57) | Lower supply ripple for the isolated DC-DC | C57 100 nF is local; 44 µF on +3V3 is reached through the In4 plane |
| 100 nF next to U32 VDD | Transient immunity for the supervisor | C241 is 7.7 mm away through the planes |
| 0.1–1 µF on PANEL_5V at J32.1 | ESD and hot-plug margin on the panel loom | U42 limits current to 110–150 mA |
| Dedicated status LEDs (power, Wi-Fi/Matter, AUTO/MANUAL, running, fault, dry run) | Each state visible at a glance | The four existing LEDs use the patterns in [bring-up](../docs/bring-up.md#5-status-leds) |
| C106/C108 and C107/C109 in series instead of in parallel | A single shorted capacitor could no longer put DC on the probes | 50 V X7R parts working at about 3 V |
| Label J2 pin 4 "ARM_TEST — no UART" in silkscreen | Prevents a serial adapter arming the latch | Noted in the bring-up guide |

## Firmware still to write

Items the reviews found missing in firmware. None of them needs a hardware change:
- **Meter:** current, power and energy readings from the ADE7953 (only voltage is read today), phase calibration, and locking the communication interface.
- **Probes:** excitation on GPIO0, TMUX1208 channel selection and ADS1115 reads.
- **Display:** OLED driver and menus.
- **Expander:** MCP23017 setup, with A1 and A4–A6 as pulled-up inputs.
- **Wireless:** Matter over Wi-Fi or Thread, and over-the-air updates.
- **Brown-out:** set the ESP32-C6 brown-out detector high enough that the processor resets before U32's 2.85–3.00 V trip.

## Open safety items carried from the audit

[direct-controller-audit.md](direct-controller-audit.md) still lists five restart scenarios on DOL and self-latching starters. Among them are a welded K2 contact, and STOP being released while a pickup pulse is active. The starter's own STOP and overload must interrupt the contactor coil independently, and each installation needs a fresh-start inhibit qualified for the actual starter.
