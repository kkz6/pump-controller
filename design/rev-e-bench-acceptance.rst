Rev E assembled-prototype bench acceptance plan
==============================================

Status: NOT RUN. No assembled controller, firmware image, instrument records
or installation test results are represented by this plan. CAD checks and
component approvals do not establish product safety or compliance. Record
results against the actual six-layer main PCB, panel, firmware and enclosure
being tested; do not transfer results between revisions without review.

Manufacturer conditions checked
-------------------------------

U1 is RECOM RACM06E-05SK/277. Its 5 V version is rated 6 W/1.2 A; the
115..277 VAC derating curve permits full power only through 50 C local
ambient. The below-10%-load regulation caveat justifies retaining R2 even
though no-load operation is allowed. External fusing is required. The module's
EMC claims depend on the stated load/filter arrangement; its suggested surge
network is not identical to this board's R1/TMOV selection. Its equipment
category and reinforced-isolation approvals are component conditions, not
approval of this controller. Repeat dielectric testing requires the supplier's
reduced voltage/time guidance. Keep its output floating as designed. [1]

R2's Bourns CRM2512 2 W rating requires 300 mm2 combined solder-pad/trace
copper and derating above 70 C. The checked local copper area is a geometry
requirement, not proof of thermal performance. [2] Vishay AC03-CS is rated
3 W at 40 C and 2.7 W at 70 C; its fusible behavior does not replace the
specified F1 or installation fault coordination. [3] Bel's 0ADKP family lists
200 A interruption at 600 VAC; that is not a general branch-circuit rating. [4]

ADI's ADuM6421A emission results depend on its PCB, ferrites, decoupling and
operating conditions. [5] Omron G5Q contact-life figures quoted for resistive
loads cannot be applied directly to an unidentified inductive contactor coil;
diode suppression also changes release behavior. [6] The independent motor
overload, short-circuit protection and residual-current protection serve
different purposes and must be coordinated for the site. [7, 8]

Build record and test controls
------------------------------

Before testing, record the main/panel serial numbers and PCB hashes, actual
BOM and substitutions, firmware hash and settings, harness cavity continuity,
CT/burden identity, contactor/coil and overload part numbers, enclosure material
and print process, ambient range, supply range, instrument IDs/calibration and
operator. Resolve generic BOM selections such as the actual electrolytic
capacitor before accepting the assembly. Photograph the finished cable routing.

Use an isolated, current-limited low-voltage fixture first, with J1/J30 and the
motor disconnected. U1 must be absent or its output isolated by the approved
fixture before injecting +5 V: AC being off does not establish reverse-feed
compatibility. No ordinary earthed scope ground or USB lead may touch M_GND,
the live meter, CT lead, coil circuit or mains. Mains, insulation, surge and
installation testing belongs on a qualified electrical test bench with suitable
probes, guarding, disconnection and protection. A generic printed box is not
an accepted mains test guard by itself.

For every case below, retain setup photographs, measured values/waveforms,
limits, deviations, result and reviewer. A missing limit or instrument record
means NOT RUN/INCOMPLETE, not PASS. If firmware is absent, only the hardware
portion can be exercised; the application portion stays NOT RUN.

T00 — Unpowered assembly and wiring inspection — NOT RUN
---------------------------------------------------------

Setup: inspect the assembled boards and every supplied cable before applying
power. Check component orientation/identity, solder bridges, contamination,
isolation slots/corridor, fasteners, leads and enclosure clearance. Confirm the
J10 fixed 1727010 termination and its separate strain relief; test every GH/PH
cable by numbered cavity, including OLED 1=SCL, 2=SDA, 3=GND, 4=3V3.

Observe: continuity agrees with the exact schematic; live-domain conductors
have no connection to isolated GND or probes. External NC STOP is in series
and JP1 is absent when that STOP is installed. Original starter auxiliary
contacts used by the panel have no connection to the mains/capacitor contacts.

Fail: unexplained continuity, substitute parts without rating/fit review,
conductive mounting intrusion, an interchangeable live-CT plug, incorrect
STOP bypass, loose termination or an unidentified capacitor-start function.

T01 — DC rails, reset and hardware permission — NOT RUN
------------------------------------------------------

Setup: use the isolated fixture with contactor/motor absent. Apply the planned
4.75/5.00/5.25 V static corners, startup/shutdown, slow ramps and fast dips;
log the actual edge rates. Exercise radio/OLED load steps after firmware exists.
Scope +5V, +3V3, SAFE_CLEAR_N, ARM_CLEAR_N, ARM_Q, PERMIT_Q and both relay drives.
Include external EN, CPU/system/watchdog reset, download mode and firmware
update. An internal MCU reset need not assert the external MCU_EN line, so
record ARM_Q retention separately from the relay-command pins' reset behavior.
Also test +5V present with +3V3 absent, controlled buck-output collapse and
rail recovery; measure back-fed rail voltage/input current with the fixture's
current limits in place. These interfaces are not hot-plug or separate-supply
interfaces.

Observe: steady 3V3 regulation, the supervisor transition and a clean U36
Schmitt output. No relay pickup occurs at boot, brownout, held START, settings
exit, network restoration or supply recovery. Sweep STOP/HH opening duration,
including contact bounce and the shortest intended button press. Record the
minimum opening that both releases K1 and clears ARM, because C86/R87 and the
coil diode delay the response. Above that accepted minimum, restoring the
contact alone must not re-arm. Do not infer an every-pulse guarantee from the
schematic. Where an internal reset retains ARM_Q, firmware must still start
with both commands LOW and require the defined fresh arming sequence.
Loss of heartbeat must trip within the watchdog's documented worst-case time
plus measured logic/relay release delay. Use 2.24 s for the watchdog component
bound, not as a claim about total motor stopping time.

Fail: unintended pickup, repeated arm-clear edges, chatter, failure to remain
disarmed, a required interlock bypass, or a rail outside a connected part's
operating range while the controller still permits running. Establish and
record the actual stop latency, including the real coil, before pump testing.

T02 — AC supply, inrush and load allocation — NOT RUN
----------------------------------------------------

Setup: after T00/T01, use the protected mains bench with the final F1/R1/RV1
and U1 fitted. Test the declared operating supply endpoints and nominal line,
cold/hot starts and repeated interruptions. Initially use simulated loads;
then both relays, full OLED pattern/highest permitted contrast, metering and
the most demanding implemented radio mode together. Capture inrush and rail
dips with suitable instrumentation.

Observe: output current and output power separately, input current, minimum
load, startup recovery and component heating. The current design reserves
5.80 W including R2, panel/key and revised reset-bias loads. It is an allocation,
not a measured maximum. Check both 1.2 A and 6 W ceilings over relevant corners;
also apply the input/temperature derating. Verify 3V3 buck efficiency instead
of silently relying on the budget's 80% assumption.

Fail: exceeded rating, unexplained peak/droop, nuisance fuse operation,
hiccup/chatter, unstable startup or thermal damage. Do not remove R2, uprate
the fuse or increase permitted load just to make the test pass. Any replacement
requires a revised protection/load review and repeat tests.

T03 — Closed-enclosure temperature — NOT RUN
-------------------------------------------

Setup: test the actual mounting, guard, harnesses and closed enclosure at the
declared ambient extremes, using T02's worst sustained load and repeated coil
operation. Instrument air immediately around U1 separately from its case;
also measure R1/R2, their nearby PCB, U2/inductor, U11, relays, electrolytics,
terminal joints and nearby insulation/plastic. Use electrically suitable
isolated temperature measurement. Soak until temperature changes by less than
1 C over 30 minutes; this is an engineering equilibrium criterion.

Observe: U1 local ambient stays at or below the design's 50 C limit, its case
below its specified 110 C maximum, and every other part below its individual
derated limit. Evaluate R2 dissipation using measured voltage/resistance and
its actual copper. Check the lowest allowable temperature among PCB, wiring,
window, printed material and adjacent components, not just the resistor rating.

Fail: any exceeded/unknown material limit, continued temperature rise,
softening, odor, discoloration, calibration drift or loss of STOP/re-arm
behavior. Passing in free air does not accept a closed starter or printed case.

T04 — Contactor coil switching and contact condition — NOT RUN
--------------------------------------------------------------

Setup: record the actual coil's voltage/frequency, pickup and holding demand,
suppression part and permitted duty. Obtain load-specific relay suitability
before energizing it through J30. Keep the motor disconnected initially.
Measure coil current/voltage, switching transients and actual contactor release.
For an initial engineering screen, perform 100 cycles cold and 100 after the
thermal soak, at a rate allowed by the coil manufacturer. This count is not an
endurance rating; a service-life programme needs its own load-specific schedule.

Observe: clean pickup/dropout, no relay/contactor chatter, no unwanted restart,
and preserved original STOP/overload series action. Measure contact condition
before/after using the relay manufacturer's method. Repeat STOP and watchdog
events with the actual suppression fitted; do not reuse unsuppressed release
times as the acceptance limit.

Fail: welded/sticking contacts, excessive wear, intermittent pickup, insulation
damage, uncontrolled transient or a stop latency outside the approved limit.
Two series ordinary relays are not monitored safety contactors.

T05 — Wiring faults and restoration — NOT RUN
---------------------------------------------

Setup: use a documented low-voltage fault-insertion harness and dummy output
load, never ad hoc shorts on an energized installation. Exercise open panel
cable/return, open STOP/HH, held/stuck START, held SET/NEXT/MODE, both/neither
key states, OLED unplug/bus stuck, probe open/short/common loss and metering
timeout. Test each plausible interchangeable external-button plug mismatch.
Record which faults are electrically distinguishable from a valid dry tank.

Observe: no unintended run request, explicit invalid data, and required fresh
re-arm after protective faults. A common/probe failure that resembles an empty
tank cannot be credited as detected merely by software. Demonstrate independent
HH and maximum-run backup behavior and record the remaining limitation.

On the isolated dummy fixture only, simulate one relay contact stuck closed
and confirm the other opens the output path. A stuck original contactor is a
separate residual fault; there is no proof of safety-rated contact monitoring.
Never inject mains into a probe, OLED or panel connector to demonstrate a
wiring error. Assess such hazardous misconnection in the qualified lab plan.

Fail: running on stale/invalid data, a fault-restoration restart, configuration
access that disables mandatory protection, or an undocumented undetectable
fault relied upon as the sole protection against overflow/dry running.

T06 — Metering and dry-run discrimination — NOT RUN
-------------------------------------------------

Setup: first inject calibrated voltage/current equivalents in an isolated
meter test fixture, then use a water-filled supervised pump loop. Record actual
wet-running power across normal head, flow and supply variations, plus errors
and temperature drift. Keep the CT burden permanently connected. Do not run
the pump dry unless its manufacturer supplies an acceptable test procedure.

Observe: a programmed underload waveform triggers the configured delay and
latched stop; a normal startup/transient does not. The smallest normal-load
margin must exceed combined metering uncertainty, drift and hysteresis.
Exercise inlet validity, runtime limit and retries-disabled behavior separately.

Fail: no clear wet/fault discrimination, an unbounded delay, automatic fault
retry, or presenting current-only logic as protection against every loss of
water. Record calibration and final thresholds before any unattended use.

T07 — Insulation, leakage and fault coordination — NOT RUN
---------------------------------------------------------

Setup: the qualified lab first identifies the applicable equipment category,
installation overvoltage/pollution conditions, accessible parts and test matrix.
It assigns insulation-resistance, dielectric, leakage/touch-current, abnormal
operation and any protective-conductor test limits to the complete assembly.
Review the weakest parallel barrier: U1, U11, relay coil/contact insulation,
PCB, connectors, wires and enclosure. Do not simply apply a component's factory
hipot voltage to the whole board or repeat it without supplier guidance.

Observe: documented measurements before/after conditioning and fault tests,
including accessible OLED/buttons and probe wiring. Check actual separation
with screws, strands, harnesses and guard installed. Coordinate F1 with the
measured/calculated prospective fault current and upstream protective devices;
R1 cannot limit a fault occurring before R1.

Fail: flashover, breakdown, excessive leakage, damaged insulation, inadequate
fault interruption or any missing applicable limit. Printed material is still
unqualified until its actual material/process and assembly are assessed.
Routine-bench intentional mains shorts are outside this plan.

T08 — EMC pre-compliance and disturbance behavior — NOT RUN
-----------------------------------------------------------

Setup: use the final enclosure, real sensor cable lengths/wet loads, antenna,
coil suppression and representative supply wiring. The lab records applicable
port-specific levels, coupling networks and performance criteria before tests.
Cover conducted/radiated emissions, ESD at accessible interfaces, EFT/burst,
surge, conducted/radiated RF, voltage dips and interruptions. Exercise standby,
armed waiting, pumping, radio transmit, settings and shutdown states. Module
test levels are supporting information, not the system test specification.

Observe: relay/contactor state with independent instrumentation, raw/validated
water and meter data, resets, fault latching, recovery and emissions. Repeat
after relevant filtering, harness, antenna or enclosure changes. Actual water
and grounded surroundings may change return paths from the module's floating
load test arrangement; never use PE as the electrode reference.

Fail: uncommanded pickup, missed hardware STOP, unsafe continued operation
with stale data, automatic re-arm after a protective reset, or emissions above
the lab's assigned limit. A controlled stop may satisfy the chosen functional
criterion only if explicitly permitted and recorded; it does not waive other
performance limits.

T09 — Site protection and supervised commissioning — NOT RUN
------------------------------------------------------------

Setup: the site electrician identifies line/neutral/PE, earthing arrangement,
prospective fault level, isolation method and branch protection. Record the
motor nameplate current and independent overload device/setting/trip curve,
plus the chosen residual-current device's type, sensitivity, delay and circuit
coverage. Selection depends on the actual installation and local requirements;
the controller's current measurement is not earth-leakage protection.

Observe: protective-earth continuity to the existing metal starter and motor,
with no neutral/PE/probe-return substitution. Test the overload's trip/control
path using its prescribed method without intentionally stalling the pump.
Test residual-current protection with the specified installation instrument
and manufacturer sequence; a test-button operation alone is not the complete
installation record. Confirm the START/capacitor sequence, STOP/overload path,
and that no holding branch bypasses J30. Demonstrate stop on high level/HH and
no restart after restored power or a qualified STOP/HH opening. The external
overload contact has no trip feedback to this board and does not directly
clear ARM_Q: reopening that coil loop can permit restart if the command
remains active. Require a manual-reset overload and physical STOP before
reset; test and document this installation restriction. Any requirement for
automatic detection and latched inhibition of every external coil-loop
interruption remains open until a separate hardware interlock or isolated
feedback design is implemented and verified.

Fail: missing independent overload/earth-leakage provisions, unverified earth
continuity or fault coordination, failed protective-device test, unknown
capacitor sequence, or a bypassed stop path. An MCB/RCCB or one successful fill
cycle alone is insufficient evidence. Retain all failed/unfinished results;
enable unattended operation only after the applicable acceptance items close.

Primary references
------------------

[1] RECOM RACM06E-K/277, Rev. 3-2025; 5 V derating graph visually reviewed:
https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf

[2] Bourns CRM2512 rating/thermal copper condition:
https://www.bourns.com/docs/product-datasheets/crm.pdf

[3] Vishay AC01/03/05-CS:
https://www.vishay.com/docs/28909/acxxcs.pdf

[4] Bel 0ADKC/0ADKP:
https://www.belfuse.com/resources/Datasheets/CircuitProtection/ds-CP-0adkx-series.pdf

[5] Analog Devices ADuM6420A..6424A, Rev. C:
https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf

[6] Omron G5Q:
https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5q.pdf

[7] Schneider Electric, motor branch-circuit overload/short-circuit coordination:
https://productinfo.se.com/9065ct9701_catalog/viewer?docidentity=ProtectionOfMotorBranchCircuits-2A717D3D&extension=xml&lang=en

[8] Schneider Electric, RCCB versus RCBO protection:
https://www.se.com/us/en/faqs/FA89258/

[9] Schneider Electric, RCD routine and instrumented checks:
https://download.se.com/files?p_Doc_Ref=CA9UG000E&p_File_Name=CA9UG000E+%28web%29.pdf&p_enDocType=User+guide

[10] STMicroelectronics STWD100 timing limits:
https://www.st.com/resource/en/datasheet/stwd100.pdf
