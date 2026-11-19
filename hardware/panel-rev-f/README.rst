Panel F — OLED, five buttons and keyed external station
=====================================================

The four rear sockets have different physical keys. J1 is the 12-circuit host loom to main J32. J2 is the only external button loom. J7 is the four-circuit 2 mm JST PH socket for the Waveshare 14657 OLED. J8 is the three-circuit 1.25 mm JST GH socket for a maintained, break-before-make AUTO/MANUAL key. All four carry isolated low voltage. The starter's original STOP and the separate high-high guard retain their hardwired functions.

Remote station
--------------

J2 is a side-entry JST SM10B-GHS-TB(LF)(SN). The single GHR-10V-S latched housing can go on in one orientation. Use SSHL-002T-P0.2 contacts and a wire construction within the JST GH contact specification. The station builder permanently terminates the leads at the labelled switch plate, insulates them individually and strain-relieves the loom. Supply one captive assembly with the selected buttons. A loose collection of switch-end plugs defeats the indexing.

========  ===========  ===========================================
J2 pair   Label        Contact and two nets
========  ===========  ===========================================
1–2       START        NO, START_N to GND
3–4       STOP         NC, STOP_LOCAL_NC to STOP_RETURN
5–6       MODE         NO, MAN_RETURN to STOP_RETURN
7–8       SET / RESET  NO, RESET_N to GND
9–10      NEXT         NO, AUTO_RETURN to STOP_RETURN
========  ===========  ===========================================

Use numbers moulded in the housing and the manufacturer's cavity drawing. Empty both cavities of each omitted NO branch. With a remote STOP, populate 3 and 4 only through its captive NC contact. Without a remote STOP, purchase a station assembly with a fixed insulated 3–4 loop. The local-only plug contains just that loop; remove it completely to install a remote station. There is no station-bypass shunt on the PCB. Both plug variants feed the local NC STOP in series. Unplugging J2 opens the command permit. A short across 3–4 can mask a remote STOP; this simple two-wire NC input cannot detect a wiring short. A short between J1.1 (+5V_CMD) and J1.2 (STOP_RETURN) can also mask both panel STOP contacts. Inspect and continuity-test the host loom. The original starter STOP and high-high float have separate cabinet trip wiring.

Harness inspection and first article
-----------------------------------

1. With the loom detached from both the PCB and any supply, meter every cavity pair, using a mating breakout and the numbered manufacturer view. The station at rest must show continuity only at 3–4. For each populated NO control held separately, only its specified pair may close in addition to the resting STOP. Hold remote STOP while each other button is pressed: 3–4 must stay open. All omitted NO cavities must be empty. Pull-test every crimp and record each measured value and fixture ID.
2. Inspect the fully assembled switch end and both orientations of the keyed housing. Switch labels must stay attached to the terminated station plate. Reject a harness that can reassign two switch functions by exchanging detachable ends. Sample wrong-size J1, J7 and J8 housings under normal mating force. They must not engage J2. Reject damage and never force a housing.
3. With motor power isolated, case closed as required, and outputs connected only to a low-voltage test load, mate J1 and the verified J2. Confirm SW1 or remote STOP drops the command permit with every other operator button held. Unplug J2 under the same test and confirm the command permit drops. Reinsert it and release STOP; prove the fresh-start/rearm policy for each configured starter profile. Repeat with the local-only plug.
4. Repeat the shutdown tests with the actual OEM STOP, physical high-high float, service gate, mode/key and independent receiver under a qualified commissioning procedure. Record contact order, actual dropout and any coasting. PCB checks do not measure these responses.

Panel geometry and models
-------------------------

The PCB is 60 × 45 × 1.6 mm, two copper layers. The four 2.7 mm mounting holes accept M2.5 hardware. J2 faces the lower edge at (30, 41.7) mm in front-view board coordinates. J1 faces the upper edge, J7 the right and J8 the left. Physical actuator centres are (7.5, 30), (20, 30), (34.5, 30), (45, 30) and (54, 30) mm. The placement for SW1 uses Omron's plunger dimension, including the 3.13 mm nominal offset from its COM pin. The STOP microswitch needs a different plunger height from the four tact switches.

See `connector-mechanical-interface.json`, the STEP models and the front and rear PNGs in `exports/`. The separate OLED is represented by its published 36 × 12.5 mm footprint and 22.38 × 5.58 mm active area. Display elevation, window offset, switch overtravel, cable bend and connector mating space need first-article measurements. The native switch and OLED-header STEP bodies are nominal design envelopes. The models omit the crimp housing and cable bundle.

Prototype files
---------------

Use `pump-panel-rev-f-gerber-prototype.zip` for the bare PCB and `pump-panel-rev-f-stencil-prototype.zip` only if ordering stencils for both populated faces. Select two-layer FR-4, nominal 1.6 mm and 1 oz outer copper. Quote and review Gerbers in Robu's viewer. PCB manufacture does not supply the loom, module, switches or the independent guard assembly. Native design, BOM, placement, schematic PDF, test reports and SHA-256 archive identifiers are alongside these files.

JST GH and PH component drawings: https://www.jst-mfg.com/product/pdf/eng/eGH.pdf and https://www.jst-mfg.com/product/pdf/eng/ePH.pdf.
Omron D2F drawing, pages 3–4: https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf.
OLED dimensions: https://www.waveshare.com/product/displays/0.91inch-oled-module.htm.
