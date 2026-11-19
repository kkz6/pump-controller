Independent starter guard
=========================

**R3 cabinet wiring, engineering prototype.** Use the native diagram and
field schedule below for assembly and bench tests. The earlier R2 terminal
numbers are withdrawn. No installed starter, trip timing or USB shutter has
been physically qualified. The `R2 findings <../../design/guarded-r2-system-audit.rst>`_
identify the superseded wiring.

Alongside the main PCB and OLED panel, the cabinet uses the isolated receiver PCB
and an independent 24 V guard assembly.
The original STOP and the separate high-high float both drop the feed to the whole
OEM starter even with the pump controller unpowered, its processor frozen, both
command relays welded or the OEM START latch held. The high-high float must be a
separate normally closed contact that opens on rising water. A single stuck float
or a short across its cable can defeat that input. Where that fault must also be
covered, use independent level devices with separately routed, monitored channels
and qualify that arrangement separately. Provide a dedicated float cable.
For potable tanks, the specified SJE MilliAmpMaster WPS 1062686 requires at
least 950 L per float for its cited approval. Check tether clearance, actual
switching level and available run-on volume against measured stopping time.
See the `SJE specification <https://www.sjerhombus.com/wp-content/uploads/2020/05/9500460A-MilliAmpMaster-WPS.pdf>`_.

Power and trip circuits
-----------------------

* Retain the original STOP, overload, START, holding and starting-capacitor
  circuits. Fit a mechanically operated second NC contact on the **same original
  STOP actuator** and a separate healthy-closed overload contact. If the original
  keypad has no provision for such a contact or the specified feedback below,
  hold that starter profile. Never connect a keypad scan line to a guard input.
* Feed main J1 and the fused cabinet 24 V SELV supply from the protected,
  always-on side of the contactors. In the protected motor feeder, connect
  KS1 and KS2 main NO contacts in series ahead of the whole starter. Each
  can interrupt the entire motor feed. Select switched conductors, protection,
  fault-current rating, wiring and insulation for the actual installation.
  Maintain continuous protective earth. Route one total motor-current
  conductor through the CT. Keep motor, capacitor and CT secondary wiring off
  J30/J35 and every isolated sensor/control harness.
* KV is an energized-healthy line-voltage monitor with dry NO 11-14 in the
  common SR1 trip chain. Sample the **motor branch after its last independent
  disconnect/protection device and before KS1 and KS2**. A 230 V reference
  part is Schneider RM17UBE15, powered/measuring on A1-A2. Use an in-range
  window consistent with motor/OEM data, shortest fault delay, guarded settings
  and correctly protected sense leads. If the OEM controls use another supply,
  insert KC's energized-healthy NO in series, sensing that independent supply
  after its last disconnect and ahead of the controlled feed. Where both are
  permanently the identical node, one KV suffices and the common-source identity
  must be verified. Neither monitor senses the intentionally disconnected load
  side. Record thresholds, hysteresis, relay release and worst-case total
  detection time against the fastest sag that can reset the starter, drop
  its contactor or stall the load. The RM17's measuring cycle can be 150 ms
  before its trip delay. It cannot guarantee capture of a shorter dip.
  If the OEM can drop or resume before the guard recognises an event, add a
  coordinated fast undervoltage release with mechanically latched breaker
  or use a verified no-voltage-release starter. Keep that installation
  uncommissioned until the disturbance tests pass.
* SR1 and SR2 use Pilz PNOZ s4 24VDC 750104. Feed each A1/A2 from fused
  +24 V/0 V. Select monitored rising-edge start on both. SR1 uses **In2+**
  single channel with S12 linked to S22. SR2 uses **In2−** dual channel with
  cross-short detection. Keep SR2.S12 and SR2.S22 independent. Each Pilz
  requires its end terminator. The single-channel sensor wiring into SR1
  limits the installation. The circuit has no installation-level PL/SIL rating.
* Start at SR1.S11. Pass through SG1.11–12 (USB shutter closed), original STOP
  second NC, overload auxiliary NC, supply monitor(s) and high-high float NC
  in series. From there go through the transfer and HOST
  health contacts shown in contacts.csv to SR1.S12. All transfer contacts
  are distinct poles of positively linked, full-seat actuators. HOST and LOCAL
  each require the other position's NC. The selector physically breaks both
  command pairs during transfer. Require power isolation during transfer.
  The LOCAL route bypasses the host heartbeat and OLED circuitry only.
* Wire a momentary NO maintenance RESET between SR1.S12 and S34. SR1.13-14
  is the first contact from SR2.S11. Then wire in series the KS1/KS2 NC
  mirror contacts, all three XF2.7/8 proofs, OEM START release and, in HOST,
  both guided command-relay NC contacts. Terminate at SR2.S12. Bridge only
  this downstream start-only proof branch with SR2's own internally monitored
  safety contact 33-34. Its RUN seal closes when SR2 energizes and opens
  when SR2 drops. Wire **channel B** from SR2.S21 through SR1.23–24,
  then SG1.21–22, to SR2.S22. Route its outgoing and return conductors
  separately from channel A. A bridge across either SR1 output contact
  still permits the other channel to interrupt SR2. Check each conductor
  independently on the actual cabinet; fit barriers between channels at
  terminals and protect the sensor loop against mechanical damage.
  Verify closure precedes opening of any active-state proof.
  On the separate start circuit wire **only** a dedicated momentary NO
  guard ENABLE from SR2.S12 to S34. Delayed neutral/mirror recovery qualifies
  the input first; it cannot manufacture a new start-button edge. Verify the
  120 ms input waiting period, 30 ms minimum press and both held-button rejection cases. It is an attended action after the SR1 reset.
  Install both actions on the low-voltage side of the enclosure or use an
  equivalent protected service station. Operate them with all other controls
  neutral. The controller's five ordinary buttons keep their functions.
* Feed +24 V to SR2.13, 23 only. SR2.14 drives KS1.A1 and SR2.24 drives KS2.A1.
  Return each A2 to 0 V. Fused +24 V through both KS1 and KS2 auxiliary NOs
  (13-14) in series with a separate HOST-seated NO operates a low-level auxiliary KFB. KFB's isolated NO alone connects
  J31.1 to J31.2. Use a low-level gold contact suitable for the sense current,
  the K1 coil current and 5 V DC. Use Omron G5V-2-H1 DC24, coil
  1+/16-, contact COM4 to NO8, with a reverse diode across the coil.
  Never inject cabinet voltage into J31. LOCAL and dropped outputs leave J31 open.
* KS1 and KS2 may each be Schneider LC1D09BD when the actual motor, starter
  and branch coordination permit. It is rated 1 HP single phase at 230/240 V,
  with a 24 V DC coil. Its 21-22 NC mirror contact proves main poles open.
  Include appropriate coil suppression and count pickup/inrush of all coils
  when sizing the supply. Preserve the OEM overload and branch coordination.

USB service access and terminal schedule
---------------------------------------

Route the protected dedicated motor L and N through QISO1 before XM1. Use a
motor-duty, positively isolating two-pole switch-disconnector with a factory
engineered trapped-key mechanism (for example a Fortress mGard bolt-interlocked
disconnector). Select the motor rating, inrush, voltage, utilisation category,
branch fault-current coordination, neutral switching and matched key code for
the site. QISO1 must trap its unique key whenever ON and release it only with
both motor conductors mechanically isolated OFF. Install its matched access
lock AL1 with a retained actuator on the sole USB shutter. AL1 traps this same
key while unlocked/open or with a cable inserted. No duplicate or master key
may be available at the installation. The operator returns this key to QISO1
only after unplugging and relocking the shutter. KS1/KS2 release time and the
presence of VBUS therefore have no part in the prior positive isolation of the
motor branch. Keep the controller and cabinet PSU on their protected supplies
upstream of QISO1. For detached bench work physically disconnect the motor
feeder and starter interfaces before applying an isolated logic supply.

Mount Omron D4NS-4BF on a fixed protected frame and retain the D4DS-K1
tongue on the sole USB access shutter with tamper-resistant fasteners. An
independent stop must take the door force. The shutter must withdraw its
tongue past the specified positive-opening travel before a plug can reach
USB-C. Prove zero feeder voltage before any USB access, including with both KS contactors simulated closed. A connected cable must physically prevent the tongue from reseating,
including when the upstream USB source is unpowered. Enclose any other access
to the socket. An external extension, an exposed panel jack or a loose tongue
defeats this arrangement. Verify the cable sizes, mounting tolerances and
approach paths against the switch drawing and the installed cabinet. Use
the motor and control disconnects for cabinet work. The shutter only removes
motor permission; it does not isolate mains or discharge capacitors.

* XSG1.1 → SG1.11, XSG1.2 → SG1.12, XSG1.3 → SG1.21 and XSG1.4 → SG1.22.
  Four insulated wires, separately protected channels, no shared common.
  Opening either direct-opening contact removes a required permission even in
  LOCAL with the main PCB unplugged. Closing the cover after service requires
  fresh attended RESET and ENABLE, then a new START. The Pilz can latch a
  channel discrepancy; repair the fault, verify both inputs opened together,
  and follow the manual's recovery sequence. Never bridge an input to recover.
* QISO1 L-IN/N-IN take the protected branch L/N. L-OUT/N-OUT go to XM1.1/2.
  These functional IDs require the selected disconnector terminal diagram. XM2.1/2 are switched L and continuous
  N downstream of QISO1 to the OEM motor feeder. Each group uses Phoenix UT 4 grey (3044102)
  and UT 4 BU blue (3044115), with D-UT 2,5/10 end covers and rail end stops.
  The selected single-phase arrangement switches line through both KS devices.
  Confirm the supply arrangement and applicable all-pole isolation on site.
  PE passes through its own continuous bonded bar. XT1.1/2 are the separate
  cabinet PSU L/N. XP1.1/2 are the separately protected pilot source/return.
* XC1 is the four-cavity command transfer. HOST order is **1 B COM (KCB1.33),
  2 B NO (KCB1.34), 3 A COM (KCA1.33), 4 A NO (KCA1.34)**. For conventional
  open-to-stop DOL, LOCAL leaves 1/2 open and links 3/4 to restore the added
  pilot permission only. For maintained RUN and keypad profiles LOCAL leaves
  all four open. Use mechanically incompatible profile inserts. Follow pages
  1–3 of the field drawing for the installed OEM interface and proof conditions.
* XF2 serves the original controls, float and off proofs. XF3 is the transfer
  position auxiliary group. XP10 carries the three supervised 24 V pilot taps.
  RX.J4 stays the five-way receiver SELV plug. It has no motor or keypad wire.

Commands and restart proof
--------------------------

Drive two 24 V Omron G7SA-2A2B DC24 relays (KCA, KCB) as command interposers.
Fused +24 V goes to J30.1 and J35.1. J30.2 and J35.2 return to their respective
positive coil terminal **0** on non-indicating P7SA-10F bases. Terminal
**1** returns to cabinet 0 V. Fit D4 (KCA1) and D5 (KCB1) at the sockets,
with the banded cathodes to terminal **0**. Use 33-34 for the command NO and
11-12 for its NC off proof. Their voltage-free NOs, **downstream** of this interface, take
the A and B roles shown on the starter drawings; their separate force-guided NCs
go in the start-only SR2.S11-S12 proof branch. This gives a welded PCB relay or a welded interposer
NO a physical means to hold off rearming. The field transfer disconnects the
interposer output contacts before inserting the local profile adapter. Never
put the 24 V coil drive across the OEM keypad. Check contact voltage,
current and minimum load at the OEM terminals. A scanned keypad below the
interposer's low-load limit requires a separately qualified monitored interface.

The OEM-off input must establish a real deenergized state, including absence
of any stored run request that could resume when the contactors close. For a
conventional three-wire starter, fit the complete XF2.7/8 proof chain described
below and a separate mechanically linked NC on the START actuator at XF2.9/10. A latching electronic starter also needs
an OEM-documented disabled/power-restoration behavior and an independently
available, powered, isolated state contact if needed. Never infer memory contents
from a contactor whose power was just removed. Disable OEM automatic restart
and retry. Without the required contacts and power-up evidence, keep the motor
disconnected and do not commission that model. Electronic keypad pulse control
by itself cannot meet the independent-stop requirement.

When SR1 drops, SR2 loses its input and both series motor contactors drop.
Reclosing any contact or restoring either supply cannot rearm the cascade.
Resetting SR1 alone leaves both motor contactors open. A separate fresh guard
ENABLE enables the motor feeder only after the off proofs are present. Require
a fresh OEM START or newly armed controller START to actually run. J31 reports
HOST authority separately, allowing the controller to discard stale requests.
In LOCAL, the original controls and the common float/overload/STOP remain
available with the PCB disconnected. Controller-derived voltage, load and
dry-run trips are unavailable in that state; retain any required OEM protection.

OEM pickup proof before restoring power
---------------------------------------

The field harness returns the following **three isolated contacts in series
between XF2.7 and XF2.8**. XF2.9/10 separately monitors the physical START
actuator. These functions apply whenever SR2 can pick up, in HOST and LOCAL.

* KOF1 confirms the OEM power stage is stopped. For a compatible conventional
  contactor use its verified main-pole mirror NC.
* KHL1 confirms that the actual holding demand has released. In a conventional
  DOL the NO **actually carrying the seal-in circuit** and the monitored NC
  must be a manufacturer-declared mechanically linked pair. One documented
  example is a compatible Schneider TeSys D contactor fitted with a LADN11
  auxiliary block. Put its 53–54 NO in the actual holding rung and its 61–62 NC from
  that same pair in the XF2.7/8 chain. Trace the stamped terminal markings
  on the selected block. A separate existing seal-in contact left in parallel
  defeats this proof. For an electronic profile the equivalent feedback
  must prove that the controller has cleared its retained run/restart demand.
* KID1 closes its isolated NO only when independent powered supervision proves
  that the complete OEM pickup demand circuit, including its field wires,
  is open. Include the parallel physical START, holding, remote and bypass
  paths in the installed transfer position. This function must observe a
  copper bridge across the actual START terminals with both buttons released
  **before** KS1/KS2 restore the OEM supply. Loss of monitor power, its
  invalid measurement or an open return lead must open the KID1 output.
  A guarded isolated test interface must be approved for the exact OEM
  circuit, including its open-circuit supervision while the feeder is off,
  maximum test energy, isolation from live circuits, alternate supplies and
  the transition back to normal service. It must not pick the OEM coil.

The cabinet schematic implements one example for the separately powered 24 V
DC pilot below. For other profiles the three XF2.7/8 proofs are a field
acceptance interface: select and qualify independent hardware that can observe
the actual command while the motor feeder is off. With only a
released actuator, a contactor mirror, a screen that says OFF, or an unpowered
OEM logic output, the starter is **ineligible for either guarded mode**.
Leave XF2.7/8 open and the installation uncommissioned if the required off-state
proofs and retained-command behavior cannot be established. Do not bridge
any missing proof contact.
`Schneider LADN mechanically linked contact guidance <https://www.se.com/ca/en/faqs/FA115177/>`_.

Separately powered 24 V DC conventional pilot
---------------------------------------------

The native **pilot** sheet and field drawing page 7 cover a conventional
LC1D09BD **24 V DC coil** with an independently fused, continuously live
21.6–26.4 V SELV pilot. KS1 and KS2 interrupt every motor-energy path.
They do not switch this pilot supply. KV1 monitors the motor feeder and
KC1 (RM17UBE16 for this profile) monitors the pilot supply before the OEM
STOP. The motor's 230 V rating does not identify its pilot voltage. Keep a
mains coil, electronic keypad, or retained-command starter uncommissioned
under this profile. The field adapter and qualified key loom are separate
from the three PCBs.

* Take **P** after the original NC STOP and overload. The original START
  NO, the actual linked seal NO of KHL1, and the switched HOST KCB START
  NO all span **P–D**. **D** connects directly to OEM coil A1. From coil
  A2 use KCA NO in HOST or its dedicated restoration link in LOCAL to **pilot
  0 V**. Disconnect the KCB branch in LOCAL. Route XP10.1 to P and XP10.2 to D
  at the actual switch ladder, and XP10.3 to pilot 0 V. A series KCA on the
  P side could hide a bridged START. Trace and exclude every alternate feed.
* R42 (680 ohms, 1%, 5 W) from D to pilot 0 V provides a return even with
  the KCA contact open. The branch P–R40 (1.60 k, 1%, 0.6 W)–OC3 LED
  (AQY212EH pins 1 to 2)–R41 (same value)–D lights only when every pickup
  contact is open. D8 is antiparallel to the LED, cathode at pin 1. Wire the
  two limiting resistors at opposite ends of the sense path. Inject a measured
  0–0.5 ohm bridge across the actual START terminals in the isolated test fixture. Enclose this
  SELV adapter and thermally derate R42. Disconnect both supplies before service.
* OC3 pins 3–4 switch cabinet fused +24 V to KID1.A1; A2 returns to cabinet
  0 V. R43 (2.20 k, 1%, 1 W) shunts A1–A2. Use Schneider RE17RAMU power-on
  delay A, 1 s continuously valid, Y1 open. Its timed dry 15–18 contact is
  the third proof in XF2.7/8. Both sensing leads, optical drive and cabinet
  supply must be present. An actual P–D bridge extinguishes the LED with
  KCA either open or closed. The separate OEM stage mirror and linked
  holding NC remain in the proof chain. With a live pilot a tripped motor
  can leave its OEM seal picked up: press and release original STOP to drop
  that seal before RESET and fresh ENABLE.
* Calculations use 21.6–26.4 V at P, 1% resistors, LED 0–1.5 V and an OEM
  coil with measured 70–150 ohms over the cabinet temperature range.
  At 384 calculated corners LED current is 5.129–8.170 mA with both resistors intact.
  The stopped coil stays below 0.988 V, or below 1.905 V with one limiting
  resistor shorted (minimum specified dropout 2.4 V). Even at a 0.5 ohm
  START bridge the detector current is below 0.066 mA in both transfer states,
  below the device's 0.4 mA minimum turn-off threshold. The extra closed-START
  load through R42 is at most 39.22 mA and 1.036 W. R43 limits the timer
  supply to 2.23 mV for 1 µA of OC3 off leakage. The RE17 dry contact
  minimum is 10 mA at 5 V; the PNOZ input circuit is nominally 50 mA at 24 V. Bench qualification must
  verify cold/hot continuous current, actual release from a previously
  energized coil, any connected suppressor, timer input leakage and pulse
  response, loading, cable pickup, and actual wetting at the guard input.
  Require the motor feeder and J31 inhibited for a bridged START in both
  transfer positions over every power-return order. Verify loss of each
  sense lead, both supplies independently, and KID1 output opening when
  START is made. Repeat with STOP/OL open. If a lingering or false idle can
  admit an ENABLE, leave the installation disabled. No PL/SIL is assigned.

J36 signal receiver
-------------------

Use the five-position JST ZE loom. Pins 2 and 3 use separate low-level contacts
to pin 1 for HOST and LOCAL. Pins 4 and 5 enter the floating dual receiver
specified below. The cabinet's other transfer contacts have separate insulation.
The main PCB supplies no 24 V. The `dedicated receiver PCB <../guard-receiver/README.rst>`_
implements this interface. Its keyed J2, J3 and J4 looms connect the
position contacts, floating supply and 24 V cabinet equipment.

* Power the receiver island from a Mean Well DDR-15G-5 isolated converter,
  input from the cabinet 24 V. Adjust to 5.00 V and verify 4.75 to 5.25 V over
  load and temperature. Its floating -V connects **only** to J36.1 on the
  controller side. Keep cabinet 0 V, cable shields and earth off this island.
* Use one half of a TI LM393B per signal, 100 nF at VCC, 1 uF local bulk.
  From each J36 output enter a single forward diode of a Nexperia BAV199W
  (anode toward J36; unused second junction open), then 10.0 k to comparator
  IN+. Connect IN+ to island -V through 10.0 k and 10 nF in parallel.
  Incoming R196/R197 on the main board are 1.0 k. Both blocking diodes
  block return through the other analog signal. HOST/LOCAL sense inputs on
  the main are pulled up to 3.3 V and remain inputs. A lifted common can float
  toward that rail through a seated position contact. Test J36.1 disconnected
  in both positions with both signal levels and power sequencing. Verify loss
  of valid HB and no persistent HOST permit, including cable coupling.
  Only this isolated receiver may share the two signal wires.
* From +5 V to IN- use 115 k on HB and 33.0 k on PANEL. Each IN- has
  10.0 k to -V. Use 1% resistors. Each open-collector output has 4.7 k to
  +5 V and drives a 2N7002 gate with 100 k to -V. Each source goes to -V.
  Its drain sinks an optocoupler LED from +5 V through 560 ohms. Use
  Vishay VO617A-3. Logic low holds the corresponding LED off.
* On the cabinet side use one BC807-40 PNP per optocoupler, emitter to protected
  +24 V. Connect a 10 k base-emitter resistor, 10 k between base and opto
  collector, opto emitter to cabinet 0 V. HB's PNP collector drives DD2503.4
  with 10 k to 0 V. PANEL's PNP collector drives KPS (G7SA-2A2B DC24) coil
  terminal **0**. Return terminal **1** to cabinet 0 V. D3 (S1M) stays at the
  driver. D9 (1N4007) goes at the remote coil, band to terminal **0**. KPS NO closes in
  the HOST trip branch. Verify this contact drops for an open OLED STOP or
  panel cable even when K1 and K2 command contacts are bridged on a fixture.
  Confirm 24 V supply tolerance, optocoupler drive, pickup/dropout and dark
  leakage at service temperature. Use sealed, segregated terminals for the
  two sides of the adapter.
* Fit one ifm DD2503 FR-1. Connect cabinet 0 V to 1, fused +24 V DC
  through F1 (315 mA time-lag) to 2 and the receiver's PNP pulse output to
  4. Leave reset terminals 17 and 18 unwired. A held +24 V reset signal
  can override monitoring. Keep AC supply terminals 7/8 unused.
* Wire the two dry NO outputs in series in the HOST chain: enter 13, link
  14 to 19 and leave from 20 to the panel permit. Both contacts open
  on loss of WD1 power. They share one measuring unit. Set DIM=1 (Hz)
  before entering setpoints, NC1=1, FO1=FO2=5 (energized inside window),
  SP1=SP2=5.0 Hz, HY1=HY2=40%, and ST1/2, DT1/2, FT1/2, SO1/2 all zero.
  These settings give a nominal 3–7 Hz passband. With the load isolated,
  read back every setting against the `monitor configuration
  <heartbeat-window.json>`_ and lock the controls. Verify the contacts remain
  open on cold start without qualified edges. After the controller boot quiet
  time, require both NOs to pick up within 1 s of a continuous 5 Hz train
  on a powered monitor. Guard RESET and ENABLE remain attended. Test both NOs individually
  and verify both open if F1 is removed while the receiver remains powered.
  The Pilz input is rated 50 mA at 24 V. Verify the complete S11/S12 loop
  resistance against the Pilz limit of 30 ohms and check the separate
  dual-channel, cross-short-detecting SR2 cable circuits against the same
  limit (750104 manual, p. 23).
* Nominal heartbeat is 5 Hz. Timing is a measured acceptance criterion.
  With data acquisition on the dummy load, stop the pulse high and low,
  or replace it with a signal below/above the window. Require loss of load
  energy within 1 s of the last valid edge, including receiver, WD1,
  SR1/SR2 and both contactors. The manufacturer's parameter values alone
  do not establish this end-to-end time. An in-band false pulse train can
  imitate valid operation. The independent physical STOP, overload and float
  remain in series with the guard in both modes.
* The 1% resistor corner check uses board high minima of 2.40 V (HB) and
  4.40 V (PANEL), low max 0.40 V, diode drop budget 0 to 1.0 V and 10 mV
  comparator error allowance. Pulldowns leave both inputs inactive on an
  unplugged cable. Measured cold/hot diode drop, cabinet noise and physical
  GND-lift behavior must agree with the calculation before field release.

Open the `external KiCad project <starter-guard.kicad_pro>`_ or the
`pin-by-pin schematic <guard-schematic.pdf>`_. The `BOM <bom.csv>`_ includes
specific receiver passives and nonpolar capacitors, cabinet relays and OEM-
specific field interfaces. Cabinet connectors S1/S2 and XF2/XF3 represent separate
physical contacts. Match the harness IDs to the actual installed pole markings.
PNOZ terminal diagrams show the used terminals; leave unused outputs insulated.
The `native ERC <checks/erc.json>`_ and `netlist <checks/guard-netlist.xml>`_
cover the receiver and cabinet schedule. The `receiver checks
<../guard-receiver/checks/geometry.json>`_ also cover the routed PCB, nominal
clearances and drilled features. Physical assembly qualification is outstanding. The field cable to the high-high
device and its return must stay segregated from motor power.

The complete dry-contact schedule is in `contacts.csv <contacts.csv>`_.
The test switches below are logical names; exact OEM terminal IDs require
the installed starter diagram. SR1/SR2 contacts and the cabinet main feed
are independent of any firmware, J31 setting or wireless protocol.

Bench acceptance
----------------

1. Use an isolated low-voltage dummy motor feed. With the load running, simulate
   K1, K2 and both welded. For each profile, press the **original** STOP and
   lift the physical float, separately, in HOST and LOCAL. Open either float
   lead. Verify both contactors drop, the test load loses energy and J31 opens.
   Simulate a single welded KS main pole with a fixture, confirm the other
   still interrupts the load, and the NC mirror vetoes re-enable.
2. In HOST, unplug the panel and J36 pins 1, 4 and 5 separately. Hold heartbeat
   continuously high, then low. Freeze the I2C bus while leaving the radio
   and processor scheduling active. Capture heartbeat, SR1/SR2 outputs, both
   main-contact states and load voltage. Verify the 1 s deadline and immediate
   raw panel intervention with K1 shorted. Reject isolated noise edges that
   cause a persistent false permit or allow startup with frozen software.
   Inject low-voltage test pulses at the receiver, then validate the installed
   loom during contactor switching. Test 1, 2.5, 7.5, 10, 50, 60, 100 and
   120 Hz and static high/low as rejected, 4, 5 and 6 Hz as permitted.
   Sweep both window boundaries, record capture and release frequencies,
   verify loss of F1/power and fresh manual re-arm after recovery. Capture
   the pulse and both WD1 contact states starting from cold, including
   connection of an intermittent pulse train. Keep mains frequency and
   harmonics out of the HOST permit. Never inject mains into the logic input.
3. Reapply each supply first, retain the old software demand, hold OEM START,
   short each command contact and separately simulate a held guard RESET and
   ENABLE. Verify no operation on fault clearance, reset, overload reset,
   transfer to either position or restoration. Confirm off and command proof
   prevent enable while held. Hold ENABLE, then independently restore each
   delayed command-neutral, mirror, original START-release and OEM-off proof.
   SR2 must require release and a subsequent distinct press. Hold RESET and
   restore SR1 input; SR1 must likewise require a new press. Prove the guard will reset from a healthy idle
   controller with J31 still open. Press RESET and ENABLE at the same instant
   from that state. RESET may arm SR1; SR2 must wait for its inputs to settle
   and for ENABLE to be released and pressed afresh. Verify with the actual
   Pilz settings and capture both contacts. Enable, then issue a new START.
4. Leave cabinet 24 V and the main controller energized. Interrupt only the
   starter branch, then independently interrupt only the OEM control supply.
   Check KS1 and KS2 release, J31 opens, and restoration with demand still
   asserted leaves the dummy motor deenergized pending attended reset, enable
   and a new start. Sweep dip depth and pulse duration around the fastest OEM
   dropout, including a held START and both transfer positions. Record actual
   thresholds, dropout times and short dips for which protection is unproven.
5. With an isolated dummy load, trip the feeder and release both physical buttons.
   In both modes separately simulate a welded holding NO at the actual seal-in
   element and a copper bridge across the actual OEM START terminal pair.
   Preserve the available mirror and released-actuator indications. Verify
   each relevant proof at XF2.7/8, restore each supply in turn, reset SR1, and
   press/release guard ENABLE. Both contactors must stay open, J31 must stay
   open and the test load must remain deenergized. For a holding-contact weld
   prove KHL1 itself cannot close. A jumper across an otherwise healthy NO
   exercises KID1; it cannot demonstrate mechanical linkage. Remove monitor
   power and lift its return lead separately. For an electronic starter repeat
   with a retained run/retry request. After removal of each fault release ENABLE,
   press it afresh and verify that a subsequent new START is needed. Record
   the monitor part, configuration, traced pickup circuit and captured results.
6. Verify keying, earth continuity, actual motor and capacitor contact release,
   short-circuit protection, insulation, wetting currents, thermal margin and
   switching noise with the exact enclosure and equipment. Test stuck float/
   shorts separately if additional independent sensor channels are specified.
   Record measured times and OEM revision before enabling unattended service.

7. With every live motor conductor isolated, admit a dummy load. In each
   transfer position, while running, bridge SR1.13–14 and SR1.23–24 **one
   at a time** and trip LS1, original STOP and the service shutter separately.
   Repeat with each shutter contact individually bypassed, then with each
   conductor individually open. A single interstage bypass must still drop
   both KS coils. Restore the original wiring and test that both channels
   open together, reset and enable while neutral, then issue a new start.
   Use a monitored test fixture for cross-channel shorts per the Pilz manual.
8. On the isolated dummy circuit, hold both KS contacts closed in turn and
   together. Verify that the QISO1 key cannot be withdrawn ON, both conductors
   open before key release, AL1 traps the key with the door open, a cable
   prevents relocking, and neither mains pole can reclose until the USB cable
   has been removed and the unique key is returned. Check PE continuity.

9. Prove the shutter removes the guard permissions before USB access with VBUS live
   and dead, in HOST and LOCAL, with each PCB unpowered, each mode position
   selected and one SG1 pole simulated closed at a time. A plugged cable
   must prevent the cover and both contact channels from closing. Record
   both contactor release times, J31 and dummy-load voltage. With a dead USB
   cable still inserted, restore controller logic, cabinet 24 V, motor branch
   and pilot in different orders. Include a retained motor command and both
   service buttons held. Neither KS coil may pick up and neither QISO1 pole may
   close. Repeat in LOCAL with the main PCB powered separately. Confirm a new
   USB attachment, VBUS loss, cable withdrawal, or cover closure cannot
   restart the pump. Check 0-positive/1-negative polarity and diode bands
   at KPS1/KCA1/KCB1 before powering, then verify pickup and loaded release.

Manufacturer references
-----------------------

* `Panasonic optical input ratings <https://industry.panasonic.com/ap/en/products/control/relay/photomos/number/aqy212eh>`_
* `Schneider RE17RAMU timing and contact ratings <https://iportal.se.com/Contents/docs/SQD-RE17RAMU.PDF>`_
* `LADN11 auxiliary terminal identification <https://www.se.com/ca/en/faqs/FA122251/>`_
* `24 V pilot supply monitor RM17UBE16 <https://www.se.com/ww/en/product/RM17UBE16/>`_
* `Schneider voltage monitor specifications and operating curve <https://www.se.com/id/en/product/RM17UBE15/voltage-control-relay-rm17u-range-65-260-v-ac-dc/>`_
* `Pilz PNOZ s4 manual, pages 9 to 16 <https://www.pilz.com/download/open/PNOZ_s4_Operat_Man_21396-EN-20.pdf>`_
* `ifm DD2503 operating instructions, sections 6.1–6.4 and 7.1–7.2 <https://media.ifm.com/dam/01a0a55a-bd11-7558-86be-c6ddfbef891d/Original/7390953_01_GB.pdf>`_
  and `DD2503 terminal table <https://media.ifm.com/dam/9b1ea99a-fe2f-4bcc-ae14-f09c75b246f5/Original/DD2503-00_EN-GB.pdf>`_
* `Schneider motor rating <https://iportal.se.com/Contents/docs/SQD-LC1D09BD.PDF>`_ and `mirror-contact identification <https://www.se.com/nl/nl/faqs/FA142116/>`_
* `Omron G7SA relay, socket and polarized coils, pp. 8, 10, 13 <https://assets.omron.eu/downloads/latest/datasheet/en/j120_g7sa_relays_with_forcibly_guided_contacts_datasheet_en.pdf>`_
* `Fortress mGard key exchange for power isolation and door access <https://fortress-safety.com/wp-content/uploads/2022/03/EN-mGard-Overview-Brochure-October-2021-v1.6-Digital-Version.pdf>`_
* `Omron D4NS two-contact connections and D4DS-K1 operating travel <https://assets.omron.eu/downloads/latest/datasheet/en/d4ns_d4ns-sk_safety-door_switch_datasheet_en.pdf>`_
* `Phoenix UT 4 feeder terminal ratings and accessories <https://www.phoenixcontact.com/en-us/products/feed-through-terminal-block-ut-4-3044102>`_
* `Mean Well DDR-15 power supply <https://www.meanwell.com/Upload/PDF/DDR-15/DDR-15-spec.pdf>`_
* `TI LM393B <https://www.ti.com/product/LM393B>`_, `Nexperia diode characteristics <https://assets.nexperia.com/documents/data-sheet/BAV199W.pdf>`_ and `Vishay VO617A <https://www.vishay.com/docs/83430/vo617a.pdf>`_
