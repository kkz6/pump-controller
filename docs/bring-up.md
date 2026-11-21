# First power-up and bring-up checks

Work through these on each new board before it goes near a starter. Use the isolated 5 V bench supply on J41 for every step except step 6.

## 1. Before power

- **Fit check:** inspect the hand-soldered mains parts (J1, F1, R1, RV1, U1, C1) for solder bridges and flux. Confirm the 8 mm gap between the mains area and the low-voltage area is clean.
- **Shorts:** measure resistance from +5 V to GND and from +3.3 V to GND. Neither should read near 0 Ω.
- **Fuse:** F1 is soldered in, not in a holder. It is a last-line T1A fuse for a failed power module. If it ever opens, check U1, RV1 and R1 before fitting a new one.

## 2. Bench power (J41 BENCH plug, no mains)

- **Rails:** +5 V should read 4.9–5.1 V, +3.3 V 3.2–3.4 V, and the meter side M_3V3 (relative to M_GND) 3.0–3.56 V.
- **Firmware:** flash the bench image (see [programming](programming.md)) and check that the USB TX and RX LEDs follow the traffic.

## 3. Arm latch test

The arm latch (U31 with U34) is the hardware gate in front of K1. This board revision cannot read the latch back in software, so test every way it clears by hand. Measure ARM_Q at U31 pin 5 and PERMIT_Q at U34 pin 4 against GND.

Setup:
- Unplug USB. VBUS removes the relay supply by design.
- Connect the panel with its STOP loop plug, or a remote station with STOP closed.
- Load a test build that drives GPIO17 (ARM), GPIO20 (PERMIT_D) and GPIO21 (heartbeat) from serial commands. The bench image holds these pins low.
- Keep J30 and J35 disconnected from any starter.

| Step | Action | Expected |
| --- | --- | --- |
| 1 | Power up | ARM_Q low, PERMIT_Q low, K1 off |
| 2 | Pulse ARM (GPIO17), then set PERMIT_D (GPIO20) high, with the panel STOP loop closed | ARM_Q high; PERMIT_Q high; K1 clicks on |
| 3 | Press panel STOP | ARM_Q low at once; K1 off; stays off after STOP is released |
| 4 | Re-arm. Stop the GPIO21 heartbeat. | ARM_Q low within 2.24 s; K1 off |
| 5 | Re-arm. Press EN RESET. | ARM_Q low; K1 off after reboot |
| 6 | Re-arm. Lower the bench supply until +3.3 V falls below 2.85–3.00 V. | ARM_Q low (U32 trips); K1 off |
| 7 | Re-arm. Unplug the panel loom. | K1 off; ARM_Q low |
| 8 | Plug in USB VBUS with K1 commanded | K1 and K2 coil supply removed |

Do not connect anything to J2 pin 4 (ARM_TEST). It drives the latch clock directly, and a serial adapter's TX line will arm the latch.

## 4. Meter and sensors

- **Meter clock:** the crystal Y1 should start, and an ADE7953 register read over SPI should return valid data.
- **CT channel:** with the burden fitted and a known resistive load, compare the current reading with a clamp meter and calibrate.
- **Probes:** with the real cable, check all five channels dry, then each level wet in turn, then the inlet probe.

## 5. Status LEDs

The firmware drives all four main-board LEDs. Until dedicated status LEDs arrive in revision 2, use these patterns:

| LED | Steady | Pattern |
| --- | --- | --- |
| D40 green, START CMD | Pump running | Slow blink: AUTO mode, waiting for low water |
| D41 red, STOP CMD | Stopped by STOP or tank full | Fast blink: fault (dry run, voltage out of range, timeout) |
| D60 green, USB TX | Flicker: USB data out | USB idle: Wi-Fi/Matter state. Slow blink connecting, steady connected. |
| D61 green, USB RX | Flicker: USB data in | USB idle: 1 s heartbeat blink, which doubles as a power indicator |

## 6. First connection to a starter

Only after steps 1–5 pass. Follow [connections](connections.md) for the starter type. Check that the starter's own STOP and overload still interrupt the contactor coil with the controller unplugged.
