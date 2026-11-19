Guarded R3 controller and Panel F
=================================

R3 is a bare-board prototype for a single-phase 1 HP starter. The motor and
starting capacitor stay in the OEM starter. The electronic controller, its
isolated guard receiver and its button panel are three separate PCBs. The
cabinet drawing adds a 24 V supply, two motor contactors and guard equipment.
The reference OEM pilot circuit is 24 V DC. Identify and qualify the actual
starter interface before connecting any command wires. The supplied photos
do not establish those terminal assignments.

What changed after the R2 audit
-------------------------------

1. **Cabinet relay polarity.** The schedules and receiver instructions put
   switched positive on socket terminal 0 and return on terminal 1 of Omron
   KPS1, KCA1 and KCB1. Fit each suppression diode with its cathode at 0.
   Verify pickup, release and auxiliary contacts on the actual socket.
2. **Ignored STOP.** The sequencer waits for fresh stopped feedback up to
   the commissioned coast-down deadline. Continued running trips the
   sequencer, clears AUTO permission and suppresses the heartbeat. The
   cabinet receiver then releases the guard. In the 10-second R2 replay
   there is one STOP command and no heartbeat transitions in the final
   second. Recovery needs stopped proof, the guard feedback open and a new
   SET action with START released, followed by the cabinet reset/enable
   sequence. A maintained AUTO key does not restart the pump.
3. **START after the motor begins running.** The open-STOP profile rechecks
   motor feedback during permission-contact settling, including the output
   edge. Loss of stopped proof cancels START and trips. Pulse profiles now
   require commissioned timing bounds. Choose them from documented OEM
   pulse requirements and measured contact timing, including long-press
   functions. A missing range disables the affected profile. The defaults
   in the test fixtures are solely for simulation.
4. **Single bridge between guard stages.** SR2 now has separately routed
   input channels controlled by distinct SR1 contacts. A single bridge over
   either SR1 output leaves a second trip path. The regression closes the
   run seal before introducing the bridge and computes the remaining paths
   from the cabinet contacts. The original STOP retains its OEM path and
   an independently operated contact on the same actuator trips the guard.
   A separate NC high-high float, wired to the guard, works in HOST and
   LOCAL even if the processor freezes. The single float and its cable
   cannot detect a stuck contact or a short directly across its two wires.
5. **Motor and command terminals.** XM1 and XM2 carry the motor feeder.
   XC1 carries only four interposer command contacts. The receiver's J4
   serves its own 24 V signals. The installation drawing identifies each end
   and both HOST and LOCAL transfer positions. The native cabinet diagram,
   contact list and field drawing describe the same revision.

See the `cabinet schematic and parts <../hardware/starter-guard/README.rst>`_,
`terminal and wiring drawing <../hardware/main-compact-dual/exports/starter-wiring.pdf>`_,
`cabinet fault results <../hardware/main-compact-dual/checks/independent-starter-guard.json>`_
and `firmware fault results <../hardware/main-compact-dual/checks/guard-firmware.json>`_.

AC inlet, metering and isolation
--------------------------------

J1 is a 7.50 mm pitch METZ CONNECT Type 171 terminal. The board enforces a
3.20 mm projected-copper design target between the **incoming, pre-fuse
line** and neutral on all six layers. The post-fuse and post-inrush paths also meet a
3.20 mm same-layer design target, with one identified exception at the
fixed input lands on the AC–DC converter (U1.1/U1.2). Their target is
2.80 mm. The protected line and neutral cross on different copper layers.
Qualify that solid insulation using the fabricator's actual stack-up.
The native geometry report gives a separate minimum for each segment. The live-to-isolated
and starter-contact boundaries have their own 8.00 mm design rule. These
values describe copper in the files. Final creepage and clearance also
depend on connector bodies, board material, component insulation, mounting
hardware, contamination, altitude and assembly tolerances. The 8 mm boundary
cannot be credited between every pair of conductors on the mains side.

The minimum copper gaps on the released layout are 3.650 mm from
incoming line to neutral, 3.510 mm after the fuse,
and 3.258 mm after the inrush resistor outside the fixed converter input lands.
The U1 input land pair itself measures 2.880 mm. Across all layers,
the projected onboard mains/meter to isolated control separation is 8.400 mm.
The smallest separation including the starter contacts is 8.060 mm. The starter
contacts are 9.425 mm from the onboard mains/meter circuit.

Metering capacitors C51–C54 use the 0805 TDK C2012C0G1H333J125AA, 33 nF,
50 V, C0G, ±5%. Current is measured with the specified CT on one complete
motor-current conductor. The CT secondary on this design is mains-referenced.
Voltage is measured at the controller's AC branch. Calibrate voltage and
current against reference instruments, then establish loaded, stopped,
start-up and dry-run thresholds on the selected motor. The firmware component
takes a qualified, fresh stopped indication as an input. A broken CT or an
invalid measurement must never be interpreted as confirmed stopped.

U11's four 0402 bypass capacitors depend on the specified placement and
effective registration within ±0.04 mm. Get assembly confirmation and measure
the mounted parts on the first article. See the `bypass routing measurements
<../hardware/main-compact-dual/checks/bypass-routing.json>`_.

See the `PCB measurements <../hardware/main-compact-dual/checks/independent-geometry.json>`_,
`metering capacitor specification <https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C2012C0G1H333J125AA>`_
and `insulation coordination guide <https://www.ti.com/lit/ml/slup419/slup419.pdf>`_.

USB programming and button plugs
--------------------------------

J40 provides native USB Serial/JTAG using the ESP32-C6 data pins GPIO12
(D−) and GPIO13 (D+). The normal service sequence starts by isolating motor
and mains power. On the bench the dedicated J41 harness supplies isolated,
regulated 5 V at pin 2 with return on pin 3. Cavity 1 is empty, separating
the converter output from the injected supply. Remove the bench harness
before fitting the operating link, which bridges pins 1–2 only. A laptop
alone cannot power the controller. J2 remains available internally for
BOOT and EN recovery.

For installed programming, the trapped-key motor-feeder isolator QISO1 releases
its unique service key only in OFF. The matching access lock AL1 traps the
key while the shutter is open. The separately protected J1 controller supply
and 24 V cabinet supply may remain live behind the touch barriers during service. The installed plug physically blocks closing
the shutter and returning the key. This directly disconnects the motor feeder
before J40 is accessible, including if a contactor is slow to release. The
separate mode key on panel J8 cannot serve as the isolation key.

In addition, the service shutter directly opens two cabinet channels. Access therefore
removes motor permission in LOCAL as well as HOST, including an unpowered
or charge-only cable. Host VBUS separately operates a hardware load switch
that disables both command coil paths and the panel permissive feed, and
enables the USB data switch. The series blocking diode on the ESD reference
prevents the device data pull-up from holding the command inhibit active
after a powered USB host disconnects. Verify hot-unplug on the prototype. Physical motor coast-down follows contactor
opening. Prove contactor release before a plug can reach J40, verify a
mated plug prevents rearming, and isolate energy before servicing the
motor itself. An isolated bench with the motor feeder disconnected needs no running motor
service fixture. A bare main board cannot interrupt an independent LOCAL starter. The old R2 printed case does not implement this service guard.

J40 uses two nominal 0.65 mm non-plated locating holes. GCT specifies
±0.05 mm on the recommended PCB pattern. Robu publishes a general ±0.20 mm
finished NPTH tolerance. At its lower limit a 0.45 mm hole could interfere
with a 0.55 mm maximum locating peg. **Before approving a prototype order,
obtain written DFM confirmation of the 0.60–0.70 mm finished holes, their
registration to the land row and acceptance of the relieved copper corners.**
If the supplier cannot hold the connector pattern, the main order remains
on hold. Inspect fit, shell solder joints and both data orientations on the
first article. See the `GCT USB4110 mechanical drawing
<https://gct.co/files/drawings/usb4110.pdf>`_ and `Robu published capabilities
<https://robu.in/pcb-manufacturing-capabilities/>`_.

On the final board the two USB plug orientations have projected D+/D− route length
differences of 12.725 and 10.176 mm. The longest measured local
gap in the adjacent copper reference is 0.561 mm. The manufacturer recommends a
parallel equal-length pair with 90 Ω ±10% differential impedance. The prototype has no
verified impedance control. Test signal quality, enumeration and programming with both
orientations and the intended cable before accepting USB operation. See the
`ESP32-C6 USB routing guidance <https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html#usb>`_.

Panel F retains five local buttons. Its optional remote buttons share one
indexed 10-position plug with permanently terminated switch leads. With
only local buttons fitted, insert the fixed-loop plug at J2 to complete
the NC STOP path. Removing it drops permission. The OLED and optional
key use different connectors. A new short on a released START wire can
look exactly like a button press while manual control is enabled. A short
across remote STOP can mask that switch. A bridge between host-loom pins
1 (+5V_CMD) and 2 (STOP_RETURN) on main J32/panel J1 can mask both panel
STOP contacts. It leaves the separately wired OEM STOP and high-high float
effective. A stuck key contact can still encode a valid mode. A held START through reset cannot rearm, and an
invalid HOST/LOCAL transfer reading removes HOST permission. Retain the
independent OEM STOP and float in every installed profile. See the `panel and harness drawing
<../hardware/panel-rev-f/README.rst>`_, `mechanical service guard
<../mechanical/guarded-r3/README.rst>`_, the `trapped-key exchange principle <https://fortress-safety.com/news/understanding-trapped-key-systems/>`_
and `ESP32-C6 USB programming guide
<https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html>`_.

Robu prototype fabrication files
---------------------------------

Upload each bare-board ZIP as its own job at the `Robu PCB service
<https://robu.in/product/online-pcb-manufacturing-service/>`_. Confirm the
outline, stack-up and material in the vendor preview. The main package
specifies 1.6 mm FR-4, ENIG, 1 oz outer and 0.5 oz inner copper, and
includes the layer order and separate plated and non-plated drills.
Panel and receiver are two-layer 1.6 mm boards. Stencils are separate
archives. Request a bare-board electrical test against the included IPC-D-356
netlist. Component assembly, cable assemblies and the cabinet hardware are
separate purchases.

* `Main controller, 100 × 97 mm, six layers <../hardware/main-compact-dual/pump-controller-compact-dual-guard-r3-gerber-prototype.zip>`_
* `Panel F, 60 × 45 mm, two layers <../hardware/panel-rev-f/pump-panel-rev-f-gerber-prototype.zip>`_
* `Guard receiver A, 68 × 48 mm, two layers <../hardware/guard-receiver/guard-receiver-rev-a-gerber-prototype.zip>`_

Verification and first article
------------------------------

The `native main checks <../hardware/main-compact-dual/checks/independent-summary.json>`_,
`main-to-panel checks <../hardware/main-compact-dual/checks/panel-integration.json>`_,
`USB and hardware-inhibit checks <../hardware/main-compact-dual/checks/usb-service.json>`_
and `exported copper comparison <../hardware/main-compact-dual/checks/gerber-copper-connectivity.json>`_
identify the files examined. The copper comparison reconstructs copper islands
and plated holes from each exact ZIP and compares them with the IPC-D-356
records. It also checks that injected opens and shorts are detected. The
`ESP32-C6 target build <../hardware/main-compact-dual/checks/guard-target-build.json>`_
links the guarded control components into a disabled test application.

All three boards passed native KiCad ERC, DRC and schematic-to-PCB comparison with zero
unconnected items. On the main board 144 above/below-limit examples exercised the
clearance rules across all six layers. The fabrication copper comparison found zero opens or
shorts at 2,225 electrical test locations across the three boards and detected all
6 injected artwork faults. The panel stop loop passed 192
contact cases and the OEM harness passed 280 ideal continuity cases.

The cabinet model exercises 2,048 input combinations, 228 trip/rearm
sequences and 108 trips from a running state, including interstage bridges
and single-pole service-switch faults. Six reachable captive-key states are
checked with both motor contactors held closed. These are circuit and
mechanical models. An additional 576 sampled power-restoration states cover
all 24 supply-return orders in HOST and LOCAL with a dead USB cable, either
single service-switch channel bypassed and both contactors held closed.
Holding RESET and ENABLE through an outage or pressing them together fails
to rearm. The actual isolator and access lock must enforce the specified
key exchange on the assembled cabinet.

The board review also identified three installation limits that matter for
this pump.

* **Enclosure heat and electrical noise.** R2, the 33 Ω minimum-load resistor,
  dissipates about 0.76 W at 5 V. The converter's published 1% load regulation
  begins at 10% load. Measure the 5 V and 3.3 V rails and local temperature
  with both relays active, the display on and the radio transmitting in the
  closed enclosure. A grounded service computer changes the common-mode
  return through J40's shell and logic ground. Include that configuration
  alongside normal floating operation in the immunity and emissions tests.
  See the `RECOM supply specifications <https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_.
* **Level and motor feedback.** Four tank electrodes report level bands.
  Litres require the tank's dimensions and calibration at each probe height.
  An open common can look like an empty tank. The independent high-high float
  remains essential. The voltage channel measures the controller branch and
  the CT measures one motor conductor. Confirm real input watts and RMS
  amperes at normal load and simulated underload, as well as current clipping
  at start. An invalid or disconnected CT cannot authorize a start as proof
  of a stopped motor. See the
  `ADE7953 metering functions <https://www.analog.com/en/products/ade7953.html>`_.
* **Radio and starter compatibility.** The module uses an external antenna.
  Route it outside the metal cabinet with separation from the field wiring.
  Test local protection with the hub disconnected, and commission the exact
  Zigbee device on the M200 before promising Apple Home visibility. The
  existence of a Zigbee radio and a Matter bridge does not establish support
  for the custom pump or its telemetry.
  See the `M200 specifications <https://www.aqara.com/en/product/hub-m200/>`_.

A qualified electrician and controls engineer must verify the cabinet wiring
and protection coordination with the actual OEM starter. Exercise STOP,
high-high, shutter, power dips/restoration, held START/RESET and single-bridge
faults with the motor isolated and an instrumented dummy load first. Measure
worst-case guard dropout and mechanical coast-down, bond continuity, dielectric
withstand, component temperatures, conducted/radiated immunity, USB enumeration
and backfeed in both cable orientations before installing a mains prototype.
Verify CT/probe faults and confirm that a service reset, a cleared water demand
or restoration of any one supply cannot start the motor. The pump application,
meter/probe calibration and offline Aqara/Apple commissioning still need
implementation and tests. No first-article or EMC test results are recorded.
