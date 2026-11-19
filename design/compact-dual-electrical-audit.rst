Electrical design review of the dual-output pump controller
==========================================================

19 November 2026. **Hold the main PCB order for the next layout revision.
Unattended pumping is unqualified in all three starter profiles.** The OLED
panel passed the connectivity review. One of its connectors can accept the
wrong field harness. Decide the keying for both boards before ordering them
as a set.

The review covers main PCB ``7edc2d5db5a9``, panel PCB ``21f6c8f9cc8d``
and the firmware components at Git revision ``02abb5e``. Evidence comes from
the routed copper, native netlists, manufacturer data and host-side fault
injection. No populated controller, actual starter, pump or cabinet was
available for electrical measurements.

Pumping and stopping
--------------------

**1. The electronic pulse-STOP profile can lose STOP while the processor
continues running.** The OLED, ADC and U33 input expander share I²C. U33
also reads the physical HOST/LOCAL position. A stuck bus makes that position
unknown. The sequencer releases both outputs. A starter that latched the
preceding START needs a positive pulse from K2 to stop. Opening the panel
STOP or high-high loop directly cuts K1, which cannot cancel the OEM latch
in this profile.

The `fault fixture <review-fixtures/pulse-stop-bus-loss.c>`_ produced a
startup synchronization STOP and an accepted START. It then fed 120 failed
reads over six seconds while continuing to execute the control loop.
It observed **zero STOP events and zero K2 drive samples** during the fault.
At the same starting state, pressing STOP with valid panel readings produced
a K2 STOP pulse.
The fixture measures the board's command output. Whether the exact starter
keeps running depends on its independent shutdown circuit.

For unattended use, require an independently enforced, de-energize-to-stop
inhibit that drops on controller power loss **and** loss of valid control
or protection inputs. A watchdog serviced by a still-running loop and the
firmware configuration flag cannot establish that behavior. If the starter
only exposes two momentary buttons and no qualified independent shutdown
is available, exclude this profile from unattended service. Verify the
original STOP, inhibits, overload and capacitor cutout on the exact starter.
See the `input handling <../firmware/components/starter_outputs/panel_controls.c>`_
and `relay sequencer <../firmware/components/starter_outputs/starter_outputs.c>`_.

**2. A broken tank common can request water when the tank is full.** An
open J20.1 or a disconnected probe harness can give the same electrode
readings as an empty tank. The excitation self-check is on the PCB, upstream
of the cable break. A pump delivering water can draw normal current and
watts throughout an overflow. The supplied J31 link bypasses the independent
high-high float input.

Use a separately wired high-high cutoff effective for the chosen starter
profile, or redesign the level loop to detect a break and provide independent
overfill protection where required. Prove that a break at the tank common,
with the simulated tank full, prevents an unsafe start or terminates the fill.
Check the real inlet probe's return path. One existing inlet wire does not
establish a usable two-electrode J21 circuit. See the
`probe front end <probe-front-end.txt>`_ and
`starter interface requirements <compact-starter-compatibility.rst>`_.

**3. The effects of a welded relay depend on the starter circuit.**

* In the two-wire maintained RUN harness, the two board contacts are in
  series. Either healthy contact opening removes the RUN request.
* In the open-to-stop DOL harness, K1 alone provides the series permission.
  If K1 welds while the OEM contactor is holding itself on, de-energizing
  K1 or releasing K2 cannot break that holding path. The original hardwired
  STOP and overload must independently interrupt the coil. This arrangement
  cannot promise a single-weld-tolerant stop from the OLED panel.
* With separate momentary START and STOP inputs, verify an independent
  shutdown as described above. Verify the actual keypad input current
  against the G5Q contact's minimum-load reliability reference of 10 mA
  at 5 V DC. A scanned keypad may need a starter-specific signal interface.

Select fault tolerance according to the installation. Simulate a welded
contact using an isolated low-voltage contactor fixture and check STOP,
release and re-arm for each profile. On a starter whose START also energizes
a starting capacitor, validate timed cutout independently of the programmable
START duration. See the `starter wiring drawing
<../hardware/main-compact-dual/exports/starter-wiring.pdf>`_ and
`Omron G5Q data sheet <https://components.omron.com/eu-en/system/files/2025-07/datasheet_pdf/J155-E1.pdf>`_.

Harness and installation errors
-------------------------------

**4. Two pairs of plugs can be interchanged.**

* Main J21 (inlet electrodes) and J31 (high-high float/relay permission)
  use the same two-position 3.81 mm Phoenix header. The J31 shunt can mate
  with J21 and simulate a continuously wet inlet. Shorting J31 separately
  removes high-high protection. Make these connectors mechanically
  incompatible. Verify correct mating and both rejected combinations with
  the actual plugs and shunt. `Phoenix connector <https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-2-g-381-1803277>`_.
* Panel J8 (AUTO/MANUAL key) and main J36 (HOST/LOCAL feedback) both accept
  a GHR-03V-S plug. Both switches have their common on pin 1. If the harnesses
  reach the opposite sockets, a swap can produce plausible positions. The
  mode key can then falsely indicate LOCAL while the relay harness is still
  connected in HOST. For a pulse-STOP starter this can suppress the STOP
  command. Use non-interchangeable connectors or permanently captive harnesses
  with verified physical separation. A physically disconnected LOCAL insert
  still isolates the controller outputs. `JST GH connector <https://www.jst.com/products/crimp-style-connectors-wire-to-board-type/gh-connector/>`_.

**5. HOST confirms plug position, not starter profile.** The two relay outputs
change roles between profiles. For example, a close-to-stop electronic
harness coupled to open-to-stop firmware holds the OEM START input closed
because A is driven as a maintained permission. The A/B plug coding does
not encode the selected operating profile. Bind the profile to the harness
or use a locked commissioning procedure that verifies every output, including
the startup STOP pulse, against an isolated fixture before enabling control.
With an external panel STOP at J3, remove JP1 and check that opening the
external STOP interrupts the chain. A fitted JP1 bridges that contact.

Metering, power and noise
-------------------------

**6. The metering isolator bypass exceeds the manufacturer's layout guidance.**
At U11, the return path from C59.2 to GNDISO pin 17 measures approximately
7.76 mm along routed track centres and uses two through-vias at board
coordinates (31.5, 26.9) and (34.7, 27.3) mm. The length
excludes vertical travel. The nearest pad-edge separation is already
2.475 mm, even before routing. The conservative minimum return pad-edge
separations at C56, C57 and C60 are 2.725, 2.998 and 2.475 mm respectively.
Analog Devices warns that long bypass connections can corrupt data and gives
a 2 mm layout constraint. The circuit uses the prescribed capacitor values
but its present routing leaves excessive high-frequency return inductance.

Relocate and rotate the bypass capacitors next to their respective supply
and return pads. Preserve the isolation boundary and the separate ground
domains on either side of the ferrites. Recheck the routed loops, then
compare supply ripple and meter readings during contactor operation and
radio transmission. Actual corruption has not been measured.
`ADuM6421A layout guidance, page 29 <https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf#page=29>`_.

**7. The probe ADC and multiplexer lack close supply bypasses.** On the
fabrication PCB, the nearest 100 nF power pad is 8.93 mm from U22 (ADS1115)
pin 8, 14.59 mm from U21 (TMUX1208) pin 13 and 6.35 mm from U20 (TLV9004)
pin 4. These are straight-line pad-centre distances. Reroute a local
100 nF capacitor directly at each IC and provide a short return. Test
borderline wet/dry readings with the intended cable lengths while switching
the contactor. `TI ADS1115 <https://www.ti.com/lit/ds/symlink/ads1115.pdf>`_
and `TI TMUX1208 <https://www.ti.com/lit/ds/symlink/tmux1208.pdf>`_.

**8. Measurement-dependent protection still needs implementation and calibration.**
J1 measures supply voltage after the controller branch's 22 Ω R1. Its load
changes the voltage drop ahead of the divider. J10 measures current through
an external 1000:1 CT with a permanent 6.8 Ω burden. Its secondary becomes
mains-referenced when connected. The ideal single-ended measurement ceiling
at gain 1 is approximately 26 A RMS for a sine wave. Starting inrush may
clip. The firmware accepts a process-health flag. It still needs the actual
meter driver, data-freshness checks, calibrated voltage and power thresholds,
priming interval and latched dry-run handling. A responsive SPI port alone
does not prove a fresh conversion.

U10 RESET has only R40/C48 and U11's converter enable is fixed. The MCU
cannot independently hardware-reset a stalled meter while the board remains
powered. Inhibit unattended starts on invalid or frozen readings and define
the recovery policy. If autonomous hardware recovery is required, provide
a qualified reset path across the existing isolation boundary. Y1's routed
clock legs to U10 are 15.02 and 23.63 mm. Verify reliable oscillator startup
at temperature and under switching noise during the layout revision. Check true
RMS voltage, amps and real watts against a reference instrument on this pump.
`ADE7953 data sheet <https://www.analog.com/media/en/technical-documentation/data-sheets/ade7953.pdf>`_.

**9. Closed-box thermal margin and mains fault coordination remain open.**
R2 dissipates 0.76 W continuously at nominal 5 V (0.84 W at the design's
upper tolerance). The previous conservative allocation is about 5.7 W
against a nominal 6 W module and includes a legacy expansion allowance.
This is a budget, not measured consumption. The 5 V model's own derating
curve shows 5 W at 65 °C local ambient on 115–277 VAC. Measure actual
radio, display and two-relay demand and temperatures in the closed case,
including a hot cabinet and low supply. Bel lists 200 A interrupt capacity
at 600 VAC and 500 A at 500 VAC for the 1 A fuse under the respective approvals.
Establish the applicable rating, available fault current and upstream coordination before any
installed mains trial. Obtain qualified review of insulation, creepage,
enclosure material, touch protection and surge immunity at the installation.
`RECOM power module data sheet, pages 4–7 <https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_
and `Bel F1 ratings, page 1 <https://www.belfuse.com/media/datasheets/products/circuit-protection/ds-cp-0adkx-series.pdf>`_.

Verification and next revision
------------------------------

Fresh KiCad 10.0.8 ERC, all-track DRC and schematic parity returned zero
findings on both boards, with zero unconnected items. The independent
sweep passed all 108 copper-isolation rule controls, found 9.425 mm from
starter copper to onboard mains/meter copper and 8.060 mm minimum projected
live-to-isolated copper gap. It checked 635 connected source pins on the
main and 81 on the panel. All 280 ideal harness cases, 128 panel contact cases
and three host firmware test suites passed. The U1 converter, U2 regulator,
U10 meter, U11 isolator, watchdog/latch and ESP32/probe ICs had their relevant
package pin assignments cross-checked. Copper rules and pin mapping cannot
measure assembled insulation, switch behavior or immunity.
`Main validation <../hardware/main-compact-dual/checks/independent-summary.json>`_
and `panel validation <../hardware/main-compact-dual/checks/panel-integration.json>`_.

Resolve stop and overflow behavior for the intended starter, proof the mating
connectors and reroute U11 and the probe IC bypasses before regenerating the
Gerbers. Use an isolated low-voltage starter simulator first for the loss
of bus, power, probe common, welded relay and wrong-profile cases. Follow
with supervised first-article metering, immunity, insulation and thermal
tests before considering unattended use. The
`bench acceptance plan <rev-e-bench-acceptance.rst>`_ gives additional tests.

The pulse-STOP observation can be reproduced from the repository root::

  cc -std=c11 -Wall -Wextra -Werror -Ifirmware/components/starter_outputs/include \
    design/review-fixtures/pulse-stop-bus-loss.c \
    firmware/components/starter_outputs/panel_controls.c \
    firmware/components/starter_outputs/starter_outputs.c -o /tmp/pump-bus-loss
  /tmp/pump-bus-loss
