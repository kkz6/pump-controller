Rev E electrical, reset and noise review
========================================

Reviewed 19 November 2026 for the 100 x 80 mm six-layer Rev E main PCB and
60 x 45 mm two-layer panel. This reviews circuit specifications and engineering
limits; it does not record measurements of a manufactured controller. Three
confirmed circuit defects were corrected. The E11 source/schematic review
passes; final routed-board and CAM acceptance
must be refreshed after the input-conditioning ECO. Prototype-package use
remains conditional on matching source/evidence/archive hashes and fabricator
acceptance.
It is not a released mains product.

The circuit is defined by ``main-rev-e.json`` and ``panel-rev-e.json`` and the
`native schematic PDF <../hardware/main-rev-e/exports/schematic.pdf>`_. Exact
reviewed file hashes are recorded in the
`native summary <../hardware/main-rev-e/checks/independent-summary.json>`_ and
`CAM review <../hardware/main-rev-e/checks/independent-gerbers.json>`_; use those
records rather than an earlier placement snapshot. The main source has 212
board components, including mounting holes. Panel key conditioning is present
in native CAD; no physical assembly or firmware has been qualified.

The `bench acceptance plan <rev-e-bench-acceptance.rst>`_ defines T00–T09, all
NOT RUN. The `unpowered fixture plan <rev-e-unpowered-harness-acceptance.rst>`_
contains separate wiring/contact screens and cannot close powered reset,
coil, insulation or EMI conditions. The
`signal-layout review <rev-e-signal-integrity-review.rst>`_ and final
`return-path measurements <../hardware/main-rev-e/checks/signal-return-paths.json>`_
add geometry evidence with explicit electrical limitations.

Corrections implemented
-----------------------

E01 — reset pull-ups could request relay operation or re-arm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Confirmed design defect; stronger external bias now fitted in the design.**
U3 GPIO19/RUN_CMD, GPIO20/PERMIT_D and GPIO21/HEARTBEAT have weak pull-ups
in their documented reset state. GPIO17/ARM_CMD has a weak pull-up after reset.
The prior 100 kohm pull-downs were not sufficient: the data sheet's typical
45 kohm pull-up gives approximately 2.28 V at a 3.3 V supply, a valid HIGH
for the latch/gate inputs and potentially enough to turn on Q31.

R71, R72, R78 and R77 are now 2.2 kohm, 1%; R76 is 22 ohm, 1% so the stronger
Q31 gate pull-down does not unnecessarily reduce its driven HIGH. R75 remains
100 kohm because its source is U34's push-pull output. The resulting typical
reset level is approximately 0.154 V. No firmware convention can substitute
for this electrical bias.

The MCU specifies 45 kohm as typical, without a resistance minimum; therefore
the new ratio is not a guaranteed worst-case proof. Q31 also needs a measured
HIGH gate voltage under its approximately 1.5 mA bias load. Check external EN,
power-on, brownout, CPU/system resets, watchdog resets, download mode and
firmware update at temperature. A low CPU-reset pin cannot be assumed:
internal reset domains do not necessarily pull the external MCU_EN net low.
See the `ESP32-C6 data sheet, Tables 2-2 and 5-4 and reset domains
<https://documentation.espressif.com/esp32-c6_datasheet_en.pdf>`_ and
`AO3400A specifications
<https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf>`_.

E02 — slow wired-clear release fed a non-Schmitt latch input
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Confirmed design defect; a conditioning stage is now included.**
U31 CLR previously connected directly to SAFE_CLEAR_N. Apart from its pull-up
RC edge, D30 can make it follow the slow R20/C22 MCU_EN release. That does not
meet the SN74LVC1G74's 10 ns/V input transition specification at 3.3 V.
U36, SN74LVC1G17DBVR, now converts SAFE_CLEAR_N into ARM_CLEAR_N before U31.6.
C77 is its local 100 nF bypass. U36 is non-inverting and has a Schmitt input;
the raw wired-OR fault functions retain their polarity. Its output must have
a short, clean route to CLR. See `U31 recommended operating conditions
<https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf>`_ and `U36 characteristics
<https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf>`_.

R70 is now 47 kohm, 1%. Its maximum pull-up current at 3.432 V is 73.8 uA;
allowing specified logic leakage keeps the D35 sink calculation below 100 uA.
At 25 C, D35's 0.24 V maximum forward drop at 100 uA plus U35's 0.10 V maximum
LOW gives about 0.34 V at the raw clear input. U36's minimum falling threshold
at the 3.0 V test point is 0.89 V. A conservative 7 uA raw-node sink leakage
gives about 2.85 V HIGH at the 3.1845 V minimum static rail.

The diode's quoted forward limit is specified at 25 C. Its temperature curves
are typical, so cold/hot LOW margin remains a test requirement. Diode leakage,
surface contamination and coupled transients must be included. U36 is specified
for operation from 1.65 V; its presence is not a guarantee about every output
state while the rail collapses through lower voltages. Verify D30 and D35
assertions independently, slow release, 5 V present with 3.3 V collapsing, and
U31/Q30/Q31 waveforms. The exact two-pin diode remains BAT54WS-7-F, pin 1 K,
pin 2 A; the three-pin BAT54W is not interchangeable.
See `BAT54WS electrical limits
<https://www.diodes.com/datasheet/download/BAT54WS.pdf>`_.

The reset-bias and clear-stage source, schematic and BOM changes are repeatable
through ``../tools/patch_main_rev_e_bias.py`` and
``../tools/patch_main_rev_e_safe_clear.py``. Native ERC and schematic-to-board
parity passed after those changes. The later E11 input-conditioning change
requires a fresh routed-board record with zero DRC and unconnected findings.
Final archives must match that record. These checks establish net/layout
consistency, not the transient behavior discussed
above. Do not rerun a placement builder over the reviewed routing.

Protection behavior that must be implemented and demonstrated
-------------------------------------------------------------

E03 — an internal MCU reset is not automatically a hardware latch clear
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Remaining architectural condition.** U32 monitors the 3.3 V rail; D30 monitors
the external EN pin. Neither is a direct indication of every internal CPU or
system reset. During a reset with a healthy rail, U31 can retain ARM_Q until
U30 times out, even though the new bias should pull PERMIT_D and RUN_CMD low.
Early resumption of HEARTBEAT must not preserve a previously armed session.
Firmware must start inhibited, invalidate the previous operating session,
establish a hardware-clear event, and require a fresh permitted user action.
A verified implementation can deliberately withhold the heartbeat for longer
than the maximum watchdog timeout before permitting re-arm; merely writing
ARM_CMD low does not clear U31. No such firmware has been qualified.

U30's selected timeout is 1.6 s nominal, 2.24 s maximum, followed by the real
relay and contactor release time. Noise or faulty software that continues
valid WDI edges can postpone that timeout. Do not generate HEARTBEAT from an
independent timer or peripheral that can continue after the control loop fails.
It must certify a completed healthy control cycle. See `STWD100 timing and
input pulse behavior <https://www.st.com/resource/en/datasheet/stwd100.pdf>`_.

E04 — dry-run protection is a software safety function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Qualification blocker for unattended pumping.** U10's IRQ, CF and zero-cross
outputs are not used as an independent trip. Meter readings pass through U11
to the MCU, which decides PERMIT_D/RUN_CMD. A plausible frozen SPI response,
incorrect calibration or control loop that keeps servicing the watchdog can
therefore defeat load-based dry-run detection. The inlet probe adds information
but does not establish a separately certified flow interlock.

The implementation needs data-freshness bounds, expected meter configuration
checks, communication fault handling, a bounded priming interval and latched
dry-run shutdown. Test frozen-but-plausible readings as well as disconnection.
Calibrate with this pump at normal delivery, low water, blocked inlet and
loss of prime. Default to no automatic dry-run retry. The watchdog is a
separate response to missing execution; it is not proof that the load decision
is correct. All radio transports must submit requests to this local control
logic and never directly drive relay GPIOs.

The 1000:1 CT with 6.8 ohm burden has an ideal single-ended unclipped limit of
about 26 A rms at ADE7953 gain 1. A 60 A starting sample exceeds that range.
Clipped starting samples must not become underload evidence. Load thresholds
must use calibrated real power/current with the documented voltage-sampling
offset after R1, rather than a claimed fixed accuracy from resistor values.
See `ADE7953 analog-input limits and measurement behavior
<https://www.analog.com/media/en/technical-documentation/data-sheets/ade7953.pdf>`_
and the calculations in ``core-review.txt``.

E05 — external coil-loop interruptions do not all latch the board off
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Installation restriction.** The starter's overload contact remains in the external
coil circuit in series with J30, and has no trip feedback to this board. Its opening does not
directly clear ARM_Q. If it recloses before software detects and latches the
interruption, a still-commanded pump can restart. Use a manual-reset overload
and require physical STOP before resetting it. A guarantee for every such
external interruption requires a separately verified hardware interlock or
isolated auxiliary feedback design; current sensing alone does not provide it.
GPB6/GPB7 are occupied by the optional mode key, not available unassigned inputs.

Likewise, opening K1/K2 cannot interrupt motor power through welded main
contactor contacts. The design has no force-guided feedback and no independent
series power contactor. Do not label it an emergency-stop system or assign a
safety integrity/performance level. Retain the starter's properly rated motor
overload and upstream protective equipment.

E06 — physical STOP removes coil power, but short taps need qualification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Panel SW1 and the optional external STOP are normally closed contacts in
series with K1's positive supply; J31's NC high-high float is in that same
path. These contacts can stop K1 with a stalled MCU. However, C86/R87 store
the high-high sense level briefly, and D31 delays relay-current decay. An
extremely short contact opening might end before the latch clears and K1
mechanically releases. Measure the shortest intended STOP press, contact
bounce, cable break/reconnection and high-high chatter. The accepted minimum
opening time and total motor-stop delay must be recorded, not inferred from
the logic diagram. A J31 bypass link removes independent high-high protection.

Actual starter and contact ratings
----------------------------------

E07 — automatic capacitor starting remains unverified
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installed arrangement starts automatically, but the component that
engages and disconnects the starting capacitor has not been identified. This
is a concrete installation blocker, not a feature supplied by the new board.
J30 offers only two series normally open relay contacts for the contactor
coil loop; it does not provide a timed second capacitor-start contact.
Identify and preserve the installed sequencing function before disconnecting
the old controller. Photograph colors and a generic starter illustration do
not establish terminal functions. Verify the actual coil voltage and the
overload/stop/hold-in paths, including every branch that could bypass J30.
Existing START/STOP actuators may be reused only with separately rated,
electrically isolated low-voltage contacts; no mains contact is connected to
the GH12 panel harness.

E08 — the relay contacts are not yet qualified for this contactor coil
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

K1/K2 are G5Q-1A4 DC5 devices, controlling the coil rather than motor current.
Their resistive switching figures and maximum voltage are not an AC-15 coil
application qualification. Obtain the installed coil's pickup/inrush and
holding VA and its suppression arrangement; verify electrical endurance and
release with that load. Each relay must independently interrupt the entire
coil voltage. Series contacts do not double the permissible switching rating.
No blanket 10 A motor-switching claim is justified. Record coil frequency,
duty and cold/hot pickup/release, then establish the load-specific service-life
programme. T04's initial cold/hot cycle screen is not an endurance rating.
See `Omron G5Q characteristics and load ratings
<https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf>`_.

Power, insulation and noise constraints
---------------------------------------

E09 — the 6 W supply has a small allocation margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reserve 5.81 W after the panel/key, bias/clear-stage and U37 input-buffer
allowances. The reset
biases reserve another 7 mA on 3.3 V plus 0.5 mA during U36's slow-input region,
approximately 0.032 W at an assumed 80% buck efficiency. These are allocations,
not measured current or a guarantee of efficiency. Both the 1.2 A output-current
and 6 W output-power limits apply. The local module ambient requirement remains
at most 50 C for the full allocation. R2 continuously dissipates roughly
0.68–0.84 W and requires the specified copper area and thermal verification.

C3/C5 are now TDK C3225X7R1C226M250AC, 22 uF/16 V X7R, 1210. Their
reference bias curves support preliminary selection but do not guarantee
combined bias/temperature/aging minima. The prototype sourcing gate is at
least 10 uF effective for C3 and 11 uF for C5, including measurement
uncertainty, followed by startup/load-step checks. These are the selected
filter's screening targets, not a general stability proof. See the
`capacitor sourcing review <rev-e-capacitor-sourcing.rst>`_ for sources and
conditions.

U1's overvoltage shutdown tolerance is much wider than a tight 5 V regulator
limit; it must not be described as a clamp protecting every 5 V semiconductor.
Actual startup, RF load steps, relay pickup, brownout and fault behavior need
recorded waveforms. The manufacturer's suggested surge/filter network is not
identical to this board's R1/TMOV choice, so module-level EMC results cannot
simply be transferred. R1's AC03-CS power rating also derates with temperature;
its fusible function does not replace F1 or upstream fault coordination.

Follow T02/T03 in the `bench plan <rev-e-bench-acceptance.rst>`_ for AC input,
inrush, simultaneous loads, startup, efficiency and closed-enclosure thermal
measurement. Measure local air separately from U1 case temperature and respect
the lower applicable limit among components, wire insulation and printed
material. R2's minimum-load function must not be removed to cure overheating.
For injected low-voltage bench power, U1 must be absent or its output isolated
by the approved fixture; AC-off alone does not establish back-feed compatibility.
See `RACM06E-K/277 limits and derating
<https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_ and
`Bourns CRM thermal conditions
<https://www.bourns.com/docs/product-datasheets/crm.pdf>`_.

E10 — F1 does not establish a system short-circuit rating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bel 0ADKP1000-RE has a published 200 A interrupting figure at 600 VAC.
Its former description incorrectly attributed that figure to TUV; the Rev E
source description was corrected. Prospective installation fault current and
the complete upstream protective arrangement still need coordination. R1 is
downstream of F1 and cannot limit a short between those parts. Satisfying an
AC/DC module's external-fuse condition does not by itself qualify the starter
assembly's fault interruption. Site acceptance also requires identified
line/neutral/PE, a verified protective-earth path to metalwork/motor, the actual
motor overload setting/trip path, and appropriately selected/tested residual-
current protection. Neither motor-current metering nor the relay output
provides earth-leakage protection. An upstream MCB, an RCD test-button result
or a successful fill cycle alone does not establish the complete protective
arrangement. T07/T09 in the bench plan define the required records; the site
and applicable equipment requirements determine device selection and limits.
See `Bel 0ADKC/0ADKP data sheet
<https://www.belfuse.com/resources/Datasheets/CircuitProtection/ds-CP-0adkx-series.pdf>`_.

E11 — control sense inputs now have voltage-tolerant Schmitt conditioning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Confirmed margin and partial-power defect; U37/C78 correct the interface.**
The former direct 22k/33k dividers into U33 had only about 82 mV calculated
HIGH margin at the 50 C static corner; a source transient could cross the
threshold. Increasing the ratio would trade that weakness for input
overvoltage at low U33 VDD. Any direct positive divider output also needed
an input-clamp path when U33 was unpowered. Absolute-maximum clamp ratings
did not make that a qualified operating mode.

U37 is SN74LVC3G17DCUR, a triple non-inverting Schmitt buffer, powered from the
same +3V3/GND as U33. C78 is 100 nF X7R, 10%, 16 V, 0603, next to pins 8/4.
R80/R82/R84 change to 10 kohm, 1%; the 33 kohm pull-downs and 10 nF capacitors
remain on new RAW nets:

.. list-table:: Control input conditioning
   :header-rows: 1

   * - Raw input
     - U37 input
     - U37 output
     - Conditioned net
     - Destination
   * - STOP_SENSE_RAW
     - 1 / 1A
     - 7 / 1Y
     - STOP_SENSE
     - U33.3 / GPB2
   * - MAN_SENSE_RAW
     - 3 / 2A
     - 5 / 2Y
     - MAN_SENSE
     - U33.4 / GPB3
   * - AUTO_SENSE_RAW
     - 6 / 3A
     - 2 / 3Y
     - AUTO_SENSE
     - U33.5 / GPB4

U37 pin 4 is GND and pin 8 is +3V3. GPIO polarity is unchanged. Its DCU0008A
land pattern uses 0.85 x 0.30 mm pads, 0.50 mm pitch and 3.10 mm row centres
from the manufacturer drawing. The hardwired STOP/HH coil-supply path is unchanged.

For the screening calculation, use the 3.1845–3.432 V logic-rail envelope,
5 uA buffer-input leakage and 1% resistor corners. At a 4.5725 V source
(the 50 C low static estimate minus an illustrative 0.20 V step), the RAW
HIGH remains at least 3.454 V. This exceeds the conservative 2.74 V maximum
positive threshold listed at 4.5 V; it does not use the lower 3.0 V test-point
threshold as a guaranteed limit throughout the 3.3 V operating range. At a
5.5 V source, RAW remains at most 4.279 V, below the buffer's 5.5 V input
rating. An open contact's LOW is at most 0.167 V from leakage through 33 kohm,
below the 0.84 V falling-threshold minimum at 3.0 V. Sweep the actual 3.3 V
operating interval and temperature to confirm transitions and hysteresis.

The output-high minimum is VDD minus 0.1 V at 100 uA, and output-low maximum
is 0.1 V. Against U33's 0.8 x VDD HIGH and 0.2 x VDD LOW limits, the same-rail
static margin is at least 0.537 V for either state. U33's 1 uA input load is
within that 100 uA test condition; leave its internal pull-ups disabled.
The nominal driven filter constant is 76.7 us; an open contact discharges
through 33 kohm in 330 us. Keep software debounce and freshness requirements;
the RC and Schmitt action do not replace them.

U37 accepts input levels up to 5.5 V independently of VDD. Its input leakage
is specified down to VDD = 0; Ioff bounds powered-down backflow at 5 uA to
85 C and 10 uA to 125 C. This replaces the former direct U33 clamp path.
It is not a zero-leakage or every-ramp guarantee: normal functional operation
begins at 1.65 V, and output states throughout 0–1.65 V remain a physical-test
condition. Test 5 V present with 3.3 V absent, overshoot, slow/fast collapse
and recovery. The interface is not qualified for hot plugging or independent
supplies. U37 is not an external-cable surge clamp. See
`TI SN74LVC3G17 pinout, operating limits and power-off specifications
<https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf>`_ and
`MCP23017 input limits <https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf>`_.

Allow 1.51 mA additional 3.3 V current for U37, including a conservative
three-input transition allowance, and 0.1 mA extra 5 V divider load. At
3.432 V and 80% buck efficiency this adds about 0.0071 W. Round the total
supply allocation to 5.81 W and the 3.3 V current reservation to 665 mA;
both remain allocations requiring T02/T03 measurements. Source/schematic/BOM
changes are reproducible through ``../tools/patch_main_rev_e_e11.py``; final
routing and native/CAM acceptance must include U37, C78, all three RAW nets
and the changed resistor values. The source-bound
`static screening record <../hardware/main-rev-e/checks/input-conditioning-corners.json>`_
records the assumptions and arithmetic; it is not physical qualification.

U32's highest release threshold is only 34.5 mV below the buck's conservative
static minimum. Its lowest falling threshold coincides with the MCU module's
3.0 V minimum, and propagation delay is finite. Check ripple, oscillating
supply, fast dips and slow ramps; static threshold arithmetic is not an
all-brownout guarantee. See `STM1001 reset thresholds and delay
<https://www.st.com/resource/en/datasheet/stm1001.pdf>`_ and
`TPS62162 regulation and power-save limits
<https://www.ti.com/lit/ds/symlink/tps62160.pdf>`_.

E12 — isolation and EMI need assembly-level evidence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

M_GND is neutral-referenced, not SELV ground. The CT secondary, permanent
burden, cable and J10 are live once connected. Rev E replaces J10's easily
confused plug with the fixed terminal; insulation, strain relief and a burden
permanently attached to the CT remain required. Never bond M_GND and GND.
The pre-E11 geometric minimum was 8.06 mm at K1 contact/coil pads 2/1, only 0.06 mm
above the project's 8 mm nominal rule. Confirm that measurement against the final
board hash. It is not a guaranteed finished-board minimum. Request explicit
fabricator/assembler review of both relays' pad spacing, copper/process tolerance,
solder fillets and assembly variation; confirm the finished assembly by inspection.
Component isolation ratings and PCB clearance checks do not qualify moisture,
condensation, wiring across the barrier or a metal enclosure. Follow the
declared insulation environment and verify the assembled system, including
mounts, connector access and meter isolation converter layout. See
`ADuM6421A insulation and layout conditions
<https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf>`_.

Long probe/float wires and the contactor are credible interference paths.
Local IC ESD ratings are not proof of field-cable ESD, burst or surge immunity.
Verify real cable lengths, common-mode exposure and appropriate installation
suppression with the pump switching. Keep probe acquisition at the specified
400 kHz shared-bus timing and 2 ms acquisition slots; bounded OLED chunks must
not compromise freshness. A stuck I2C bus compromises both probe data and
local input reads and requires fail-off. A disconnected OLED alone can be
handled separately when the bus and other devices remain healthy.

The COM coupling capacitors reduce steady DC in normal operation; parallel
capacitors are not redundant protection against a single shorted capacitor.
Do not claim fault-proof zero DC probe excitation or accurate continuous water
volume from five level wires. Sensor corrosion, conductive contamination,
crossed probes and a stuck-wet inlet need explicit fault tests and honest
display states.

E13 — six layers and RF hardware do not establish signal performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In1.Cu is reserved for separate GND/M_GND reference domains; In4.Cu carries
separate +3V3/M_GND domains. Signal routing does not use those reserved planes.
The source-bound return-path report measures geometry and plane coverage; it
does not solve actual return current, loop inductance or impedance. The
fabricator's exact dielectric construction has not been established, and no
90-ohm USB compliance is claimed. The service header/cable and route transitions
need actual USB enumeration and signal-quality checks.

The retained metering crystal package and several reference/filter bypass
placements have documented compromises in the signal-layout review. Validate
clock startup and frequency, reference/supply ripple, measurement repeatability
and contactor-noise sensitivity before using calibrated readings for protection.
More copper layers and a one-point calibration do not establish immunity.

U3 uses an external 2.4 GHz antenna. Its exact antenna/coax/mounting combination
and usable range remain unqualified. Select it under the module's antenna and
regulatory conditions, route it in the isolated compartment and validate the
actual enclosure placement; a hole reserved in the case is not that evidence.
For each implemented Zigbee, Matter/Thread or Matter/Wi-Fi image, measure control
cycle deadlines and input freshness during radio traffic, network loss,
rejoining and hub/WAN interruptions. Keep one selected operational transport
per build. Native custom Zigbee pairing to Aqara M200 remains unsupported;
Matter is the planned M200/Apple integration path, pending actual endpoint/hub
validation. See `wireless architecture <wireless-architecture.rst>`_ and T08
of the bench plan. No working radio firmware, interoperability, range or RF
compliance result is represented by the PCB or module capabilities.

Release boundary
----------------

The corrected circuit is suitable for continued prototype engineering only.
Fresh native/CAM passes after E11 are required for the bare-PCB prototype
package gate; only a matching final package manifest identifies usable archives. Main
`bare-board <../hardware/main-rev-e/pump-controller-main-rev-e-gerber-prototype.zip>`_
and `stencil <../hardware/main-rev-e/pump-controller-main-rev-e-stencil-prototype.zip>`_
archives are separate from the panel's corresponding review archives and
from any assembled-product acceptance.

Before use on a pump, close actual coil/capacitor identification, protective-
device coordination, firmware freshness/reset behavior, thermal/rail limits,
physical stop/interlock response and applicable insulation/EMC checks. Record
measurements against a particular assembled board, firmware image, starter,
antenna, cable arrangement and environment using the bench plan. The board
sizes exclude plugs, bends, guards and antenna; the separate 170 x 150 x 90 mm
printed case is a mechanical prototype without claimed mains, fire or ingress
qualification. Main-board insulating standoffs are 18 mm minimum. C1 is
Panasonic EEUFR1E470; allow 13.5 mm installed height, comprising a 12.5 mm maximum body
plus 1 mm mounting allowance. Trim protruding top-side leads and measure actual
clearance in the assembly. CAD pass results cannot close these
application-specific limits.
