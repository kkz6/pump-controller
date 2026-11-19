Rev E electrical, reset and noise review
========================================

Reviewed 19 November 2026. This reviews the circuit and component specifications;
it does not record measurements of a manufactured board. Two circuit defects
were corrected during the review. Final routing, physical fault injection,
electromagnetic testing and installation qualification remain necessary.

The reviewed source is ``main-rev-e.json``, SHA-256
``b3223d34f0a0ecf25b6d411dd0346add15c9ffb58dc9bfd7212b40eda30b00c1``.
The corresponding native netlist is ``../hardware/main-rev-e/exports/netlist.xml``,
SHA-256 ``8f2683145c1fdfb60f25aa77cefc1fcae7a0016e50cfdff813595ea46efb602a``.
The source has 210 board components, including mounting holes. The review
includes the Rev E panel and its optional active-low key-switch inputs.
Later routing hashes belong in the final fabrication records; these hashes
identify the electrical review snapshot, not a released manufacturing package.

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
parity passed after the changes. The placement check had zero DRC violations
and 477 unrouted connections: this is evidence of clean placement, not a
finished electrical layout. The authoritative final routing must pass again.

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
engages and disconnects the starting capacitor has not been identified.
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
No blanket 10 A motor-switching claim is justified.
See `Omron G5Q characteristics and load ratings
<https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf>`_.

Power, insulation and noise constraints
---------------------------------------

E09 — the 6 W supply has a small allocation margin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reserve 5.80 W after the panel/key and new bias/clear-stage allowances. The new
biases reserve another 7 mA on 3.3 V plus 0.5 mA during U36's slow-input region,
approximately 0.032 W at an assumed 80% buck efficiency. These are allocations,
not measured current or a guarantee of efficiency. Both the 1.2 A output-current
and 6 W output-power limits apply. The local module ambient requirement remains
at most 50 C for the full allocation. R2 continuously dissipates roughly
0.68–0.84 W and requires the specified copper area and thermal verification.

U1's overvoltage shutdown tolerance is much wider than a tight 5 V regulator
limit; it must not be described as a clamp protecting every 5 V semiconductor.
Actual startup, RF load steps, relay pickup, brownout and fault behavior need
recorded waveforms. Use the separate supply/bench acceptance review for the
manufacturer input-fuse arrangement and combined temperature/load tests.
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
assembly's fault interruption. See `Bel 0ADKC/0ADKP data sheet
<https://www.belfuse.com/resources/Datasheets/CircuitProtection/ds-CP-0adkx-series.pdf>`_.

E11 — some 5 V sense inputs have limited noise margin and partial-power paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

R80–R85 remain 22 kohm/33 kohm dividers into U33. With 1% corners and 1 uA input
leakage, the conservative static HIGH is about 2.865 V at a 4.835 V source,
or 2.827 V at a 4.7725 V source. Against 0.8 times 3.432 V = 2.7456 V, those
margins are only 119 mV and 82 mV. They exclude coupled noise and dynamic
supply drop. An illustrative 4% load transient can cross the guaranteed HIGH
boundary. Read these inputs with validation/debounce and fail off on unresolved
states; never interpret ambiguous mode data as authorization to arm.

If +5 V remains while +3V3 is absent, these dividers can inject current into
U33's input clamps. A 22 kohm source limits the illustrative current to about
0.2 mA, but the absolute-maximum clamp rating is not an operating guarantee
and does not prove absence of phantom powering. Test rail sequencing and
stalled/shorted buck output. No external interface is hot-pluggable or
independently powered. The panel key inputs use NPN level shifting and do
not share the same divider-HIGH margin. See `MCP23017 input and absolute limits
<https://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf>`_.

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

Release boundary
----------------

The corrected circuit is suitable for continued prototype engineering only.
The manufacturing package needs final native/ERC/netlist/DRC and independent
CAM checks after routing. Before use on a pump, close the actual coil/capacitor
identification, protective-device coordination, firmware freshness/reset
behavior, thermal/rail limits and physical stop/interlock tests above. Record
measured results against a particular assembled board, firmware image, starter,
cable arrangement and operating environment. CAD pass results cannot close
these application-specific conditions.
