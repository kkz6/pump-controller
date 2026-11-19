Guarded R2 system audit
=======================

**Hold the PCB order for an installed controller. Withdraw the R2 cabinet
wiring drawing from installation use.** Three cabinet relay coils have their
polarity reversed. The starter control software also accepts two sequences
that can keep the motor running or issue START at the wrong time. This review
applies to design commit ``d8a4d995fc12ff316d73df2e0b7db6624b6f45d5``
of 19 November 2026. The hardware files remain the evidence for these findings.

Faults requiring correction
---------------------------

1. **Three polarized cabinet relays are wired backwards.** The cabinet
   symbol connects switched positive to terminal 1 and return to 0 on KPS1,
   KCA1 and KCB1. Omron's G7SA-2A2B drawing and P7SA-10F socket view show
   terminal 0 positive and 1 negative. Omron states that reversing these
   connections prevents operation. This affects the panel permission relay
   and both command relays. Revise the cabinet symbols, pin schedule, wiring
   drawing, receiver field instructions and remote suppression-diode markings
   together. Prove pickup, release and feedback on the actual sockets.
   See the `cabinet source <../tools/build_starter_guard.py>`_ and
   `Omron drawings and wiring precautions, pp. 8, 10 and 13 <https://assets.omron.eu/downloads/latest/datasheet/en/j120_g7sa_relays_with_forcibly_guided_contacts_datasheet_en.pdf#page=8>`_.

2. **An ignored automatic STOP can leave the controller reporting healthy.**
   With a simulated electronic starter running, normal fill demand went away.
   The sequencer sent one STOP. Ten seconds of fresh feedback continued to
   report running, yet the sequencer reached IDLE, AUTO remained authorized,
   and the heartbeat made 100 transitions. A closed high-high float is normal
   below the backup level, so it cannot substitute for stopping at the normal
   fill level. Define the allowable stopping time for the pump. On expiry or
   loss of trustworthy feedback, latch a fault, withdraw the heartbeat and
   require deliberate recovery. Preserve coast-down allowance. See the
   `executable feedback fault cases <review-fixtures/r2-stop-feedback.c>`_
   and `starter sequencer <../firmware/components/starter_outputs/starter_outputs.c>`_.

3. **The DOL profile can issue START after stopped feedback goes away.** A
   second test authorized a start with the motor stopped, then changed the
   feedback during relay settling. The software still asserted START on the
   next sample. This matters particularly if the OEM START contact also engages
   a start capacitor. Recheck stopped and healthy at the actual output edge,
   abort on a changed indication, and constrain pulse durations to the verified
   OEM range. The configuration currently accepts positive durations up to
   2,147,483,647 ms. An independently functioning capacitor cutout remains
   necessary on starters that switch this circuit.

4. **The two motor contactors share a single trip path.** With wiring intact,
   opening the float removes permission from SR1 in HOST and LOCAL, and a
   single welded motor contactor leaves the other available. With SR2 already
   energized, an external short across SR1's output wires can keep SR2's
   holding contact and both motor-contactor outputs energized after the float
   opens. A bench-free graph check using the released contact schedule found
   SR2.S11 to S12 open with the float tripped, and conductive after adding one
   connection between SR2.S11 and RUN_PERMITTED. The existing sequence model
   also forces SR2 off whenever SR1's input is unhealthy. That extra software
   condition masks the wiring fault. The independent original OEM STOP path
   still exists. Reconcile the model with the wiring and establish whether
   protected wiring with justified fault exclusions or independent monitored
   trip channels meet the installation requirements. See the
   `contact schedule <../hardware/starter-guard/contacts.csv>`_,
   `sequence model <../tools/check_independent_starter_guard.py>`_ and
   `Pilz single-channel connection information <https://www.pilz.com/download/open/PNOZ_s4_Operat_Man_21396-EN-20.pdf>`_.

5. **The cabinet terminal schedule mixes motor power and starter commands.**
   Cabinet J4 is called “Dry OEM command contacts”, but the native netlist
   assigns its fifth terminal to the switched motor line. The field drawing
   shows a four-cavity control-only transfer with its own pin order. The
   receiver PCB also has a J4, a separate five-way **24 V** connector. An
   installer cannot use one pin schedule for these interfaces. Give the motor
   feeder its own rated power terminal, assign unique field identifiers and
   publish an end-to-end map covering both transfer positions before issuing
   a wiring drawing. See the `field netlist <../hardware/starter-guard/checks/guard-netlist.xml>`_
   and `receiver interfaces <../hardware/guard-receiver/README.rst>`_.

PCB, panel and fabrication
--------------------------

* The main board's measured live-to-isolated copper gap is **8.060 mm**.
  At the AC inlet, the supply-side line trace approaches the neutral pad of
  J1 to **2.015 mm** on the front before F1. The J1 pad gap on the rear is
  **2.480 mm**. KiCad checks a 2 mm rule between those nets. An example for
  230 V category III basic insulation uses a 4 kV impulse and 3.0 mm clearance
  up to 2,000 m. Whether that criterion applies to line-to-neutral functional
  insulation depends on the end equipment, site and fault protection. Establish
  the requirement and upstream fault capacity before releasing the connector
  and layout. See the `board rules <../hardware/main-compact-dual/pump-controller-compact.kicad_dru>`_
  and `TI insulation coordination guide, Tables 4–5 <https://www.ti.com/lit/ml/slup419/slup419.pdf#page=8>`_.
* Meter filters C51–C54 specify 33 nF, C0G, 50 V, ±5% on 0603 pads. The
  main BOM gives a generic specification for all four. Obtain an orderable
  part with those ratings and dimensions or revise the footprints and check
  phase matching before assembly. U11's four specified 0402 bypass parts
  also rely on ±0.04 mm effective registration. Have the assembler verify
  placement. See the `main BOM <../hardware/main-compact-dual/bom.csv>`_
  and `bypass measurements <../hardware/main-compact-dual/checks/bypass-routing.json>`_.
* The 0.91-inch OLED plugs into panel J7 and the optional mode key into J8.
  All five optional remote-button sockets J2–J6 use the same two-pin housing.
  Moving a remote SET or MODE plug into START makes that physical button a
  valid START input when the system is ready. Give START and STOP distinct
  keying, use an indexed multicore harness, or commission and secure every
  installed lead against interchange. Panel JP1 must be removed when an
  external STOP is used. See the `panel BOM <../hardware/panel-rev-e/bom.csv>`_.
* The printed 170 × 150 × 90 mm case houses the main board and OLED. The
  separate receiver and cabinet devices need additional space. Each Pilz
  750104 alone is **120 mm deep** and requires at least an **IP54** cabinet,
  −10 to +55 °C operating ambient and no condensation. Cabinet fit, gland
  sealing, terminal access, heat from the 5 V supply and resistor, fuse
  coordination, protective-earth continuity, insulation and switching-noise
  immunity still need qualified physical verification. See the
  `enclosure scope <../mechanical/compact-dual/README.rst>`_ and
  `Pilz environmental and mechanical data <https://www.pilz.com/download/open/PNOZ_s4_Operat_Man_21396-EN-20.pdf#page=26>`_.

Programming and end-user functions
----------------------------------

* **R2 has no USB-C receptacle.** The main PCB and BOM specify J2 as a
  vertical unshrouded 2 × 4, 2.54 mm header. GPIO12 and GPIO13 pass through
  two 22 Ω resistors to its USB data pins 7 and 8. Pin 1 is logic ground,
  2 is 3.3 V sense only, 3 is transmit log output, 4 is the arm-latch signal,
  5 is reset and 6 is boot. There is no USB 5 V input. Keep pin 4 open on
  the service fixture. Programming assumes disconnected mains and starter
  wiring and a separately powered isolated bench setup. Plug-in consumer
  USB-C programming requires a new port or a purpose-built keyed adapter.
  For an integrated next revision, put the socket in the low-voltage service
  area, include connector ESD and Type-C attachment circuitry, define VBUS
  sensing and power isolation against backfeed, and verify firmware recovery
  in both plug orientations. The nominal routed D−/D+ lengths are 25.036 and
  24.677 mm, each with two vias, excluding the resistor body and via barrels.
  Enumeration, ESD and differential impedance remain unmeasured. See the
  `released main BOM <../hardware/main-compact-dual/bom.csv>`_ and
  `Espressif USB layout guidance <https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html#usb>`_.
* **Voltage and motor load measure different points.** J1 measures the
  controller's supply after its series input resistor. It cannot reveal
  voltage lost downstream at the motor terminals. The external Talema 1000:1
  CT surrounds one motor conductor, with a permanent 6.8 Ω burden at the CT.
  Its secondary becomes mains-referenced at J10. The logic PCB carries no
  motor current. Compare RMS volts, amps and real watts to a reference meter
  through start, wet running and a controlled underload. Starting current can
  exceed the modeled input range. Confirm zero/stopped detection against
  independent feedback and distinguish a failed CT from a stopped motor.
  See the `metering review <compact-dual-electrical-audit.rst>`_.
* **Power return and manual operation.** On the compatible reference
  starter, healthy wiring requires physical RESET, separate ENABLE with the
  starter proved idle, then a fresh START. A retained AUTO selection cannot
  reauthorize the motor after a detected outage. An upstream voltage monitor
  can miss a brief dip that resets the OEM starter. Measure this on the
  actual pilot and motor supplies independently. LOCAL retains the original
  STOP, overload and hardwired float. Controller-derived undervoltage and
  dry-run protection are unavailable in LOCAL with the controller disconnected.
  The cabinet voltage monitor still serves its own hardwired function.
  See the `power-return acceptance cases <compact-dual-guard-r2.rst>`_.
* Four tank electrodes and a common give **five level bands**. Litres require
  probe heights and tank calibration and remain a range between contacts.
  The single existing inlet wire needs a verified return. The independent
  float needs its own cable. For potable water, the selected SJE 1062686's
  cited approval begins at **950 L per float**. Check tank capacity, tether
  movement and free volume above trip against the actual stopping time.
  See the `probe interface <probe-front-end.txt>`_ and
  `SJE float specifications <https://www.sjerhombus.com/wp-content/uploads/2020/05/9500460A-MilliAmpMaster-WPS.pdf>`_.
* **Firmware and wireless readiness.** The ESP32-C6 build links the guard
  components in a disabled test application. There is no integrated pump
  application for metering, probe acquisition, calibrated dry-run thresholds,
  display/settings, updates or radio commissioning. Aqara documents M200
  bridging for Aqara Zigbee products. A custom Zigbee endpoint and its Apple
  Home controls have no demonstrated pairing path here. Native Matter over
  Thread or Wi-Fi is a separate candidate to implement and test on the M200
  and HomePod with the internet disconnected. Check each required reading in
  the actual apps. See the `target build record <../hardware/main-compact-dual/checks/guard-target-build.json>`_
  and `Aqara M200 device support <https://www.aqara.com/en/product/hub-m200/>`_.

Verification and release decision
---------------------------------

Fresh KiCad 10.0.8 checks on the three PCBs reported zero schematic, layout,
unconnected-item and schematic-to-PCB differences. The cabinet schematic
also passed ERC. The 37 existing Python tests and five firmware host tests
passed. The published PCB and package hashes matched. The archived independent
copper extraction matched 169 main-board and 35 receiver named nets. The new
host fixture reproduced both hazardous firmware responses with address and
undefined-behavior sanitizers enabled. It returns status 1 on this revision.
See the `Gerber comparison <../hardware/main-compact-dual/checks/gerber-copper-connectivity.json>`_
and `fixture with run instructions <review-fixtures/r2-stop-feedback.c>`_.

Resolve the cabinet and firmware faults, source the four filter capacitors
and settle the inlet spacing before ordering the intended installation boards.
Prove the exact OEM coil voltage, supported command interface, capacitor
cutout, independent STOP path and behavior after an outage. The documented
reference uses a 24 V DC pilot for a 230 V motor. The photos do not establish
that pilot interface. Verify supply dips, hardwired stops and prevention of
restart on an isolated dummy load first. The 1 s heartbeat-to-load cutoff
is an acceptance target. No measured stop time, electrical-noise test or
assembled pump result exists for this revision.
