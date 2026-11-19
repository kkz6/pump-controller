R4 field wiring and independent pump shutdown
============================================

R4 has two custom PCBs, the integrated main board and the OLED/button board. The
separately powered 24 V cabinet still carries the protection, service transfer and
motor switching. Use the `wiring drawing <starter-wiring.pdf>`_ for the cabinet
connections and the `native schematic <starter-guard-r4.kicad_sch>`_ or
`schematic PDF <guard-schematic.pdf>`_ for terminal-level detail. Main and
cabinet references in the field drawing identify mating connector cavities.

How the pump stops
------------------

The original starter STOP continues to open its own factory control circuit.
Its mechanically linked, electrically separate NC auxiliary S3.11–12 goes to
XF2.1–2. The separate overload NC goes to XF2.3–4. The independent high-high
float, LS1 COM–NC, goes to XF2.5–6. Verify it **opens as water rises**. One
broken float core opens the loop. Tank probes and the inlet probe go to the main
board separately. They cannot substitute for LS1. On an electronic starter the
auxiliary must positively track pressing the original STOP; an undocumented
membrane keypad alone cannot provide this contact.

Both STOP and LS1 are in the common cabinet SR1 sensing chain before the
HOST/LOCAL branches. SR1 opens two separate inputs of SR2. SR2 drops KS1 and
KS2 through separate outputs. Their main contacts are in series in the motor
feeder. Thus a trip interrupts motor power even if the PCB is unpowered, an
output is welded, the controller falsely reports a healthy panel or heartbeat,
or one of these two power contactors sticks. This assumes independent working
cabinet hardware and **every source of motor energy passes through the two
contactors**. Provide suitable branch protection and continuous protective earth.
Preserve the factory overload protection, capacitor and start-winding cutout.

A welded/stuck float or a short directly across its two wires looks healthy
to this single-channel input. A short across the STOP auxiliary hides that
auxiliary. Two welded power contactors can keep the feeder energized. The trip
time, stopping/coast time and residual pumped volume must be measured against
the available overflow margin. No installation-level PL or SIL is assigned.

Connections at the main PCB
---------------------------

* **J52** is a keyed JST PH three-position plug. Pin 1 goes only to the
  common of the two isolated transfer indication contacts (XF3.2/4).
  Pin 2 goes to HOST (XF3.1), pin 3 to LOCAL (XF3.3). The onboard logic
  supplies the pull-ups. Keep cabinet 0 V, 24 V, PE and shields off this plug.
* **J54** is a keyed JST VH five-position plug. Pins 1 and 2 go to the
  protected cabinet +24 V and return. Pin 3 goes to the DD2503 pulse input
  WD1.4. Pin 4 goes to KPS1 coil terminal 0 (+), with terminal 1 at cabinet
  0 V and D9 across the remote coil, cathode toward 0 (+). Pin 5 takes
  +24 V only through KS1.13–14, KS2.13–14 and the independent HOST-seated
  contact XF3.17–18. It energizes the onboard KFB1 feedback coil. All
  five wires stay within the cabinet power domain. Maintain physical
  segregation from probes, selector and USB, and strain-relieve both looms.
* **J30** and **J35** are dry outputs. Pin 1 of each takes protected cabinet
  +24 V. Pin 2 drives KCA1 coil 0 or KCB1 coil 0, respectively. Return each
  coil terminal 1 to cabinet 0 V. D4 and D5 cathodes face the positive
  coil terminals. The interposers provide dry contacts for the selected
  OEM profile and guided release proof before re-arm.
* **J1** takes the independently protected AC controller supply. **J10**
  accepts the specified current transformer on one insulated motor conductor.
  The CT secondary belongs to the mains-referenced meter circuit in this
  design. Motor and capacitor power stay off the PCB. J20/J21 remain
  isolated electrode connectors. Keep OEM coil, pilot, AC and feeder cabling
  segregated from panel, selector and probe wiring.
* **J54.1 shorted to J54.5** can falsely energize KFB1. A fused supply wire
  touching the heartbeat or panel line can also defeat an individual indication.
  These lines cannot energize KS1 or KS2 directly. The independent STOP/float
  path remains necessary even when the panel and both command contacts appear
  healthy. The cabinet 24 V supply and its branch protection remain necessary
  for LOCAL operation with a dead main PCB.

Starter profiles and transfer
-----------------------------

The original pushbuttons remain usable. Select an OEM-documented profile and
a physically keyed harness. An equivalent original STOP auxiliary and complete
idle/off proofs are prerequisites in every profile.

* **Conventional 24 V DC DOL:** the pilot sheet shows the full working profile.
  Pilot + passes through the factory NC STOP and overload to P. Factory START
  NO, linked hold NO and the HOST START interposer span P–D. D drives the
  OEM coil A1. The added A permission is in the A2 return; the dedicated
  LOCAL insert restores only this return. All HOST connections open during
  transfer. XPF1 is the functional pin-pair view of XC1 in this profile.
  OEM-IN/OUT on S3/S4/S5 are functional names for existing terminals,
  not universal manufacturer numbers. The 21.6–26.4 V DC pilot and measured
  70–150 ohm coil limits are part of this profile. Keep the pilot powered
  independently while KS1/KS2 interrupt all motor power. If its original
  seal stays energized after a feeder trip, release it using the factory
  STOP before RESET and ENABLE.
* **Electronic START/STOP:** two separate bounded dry closures. XC1.3/4
  (KCA1) spans the approved START input. XC1.1/2 (KCB1) spans the approved
  STOP input. Use a captive common splice only where the OEM specifies a
  shared common. LOCAL opens all added commands; factory controls remain.
  Require independent actual idle, released-command and stopped-stage proof.
  The conventional XP10 optical adapter does not establish these signals for
  an electronic keypad or retained-demand starter.
* **Maintained RUN input:** use A only on an OEM-documented maintained command
  input. Keep B unused. LOCAL opens the added command. A maintained RUN
  wired across a momentary factory START can restart the pump after STOP is
  released; that topology is outside the supported profile.
* Select the exclusive HOST or LOCAL position physically. The user-interface
  Auto/Manual selection handles software behavior. The service transfer
  physically changes the command wiring. The transfer selector on J52 only
  reports its position. Both modes retain the independent hardwired trips.

Protection, reset and servicing
-------------------------------

Use factory-approved isolated auxiliaries for S3/S4/S5, a proven transfer,
and a load-rated, short-circuit-coordinated motor isolator and contactors.
Fit motor-rated contacts with verified mirror feedback, prove the original
power stage and actual seal released, and prove all command paths open before
re-enable. A stuck command or mismatched service insert must inhibit startup.
With all inputs healthy, first release and press cabinet RESET S1. Then
release and press ENABLE S2. A returning supply or a held button gives no new
valid sequence. RESET and ENABLE here are guarded cabinet commissioning
controls, separate from the OLED interface.

Use the two-pole key-trapped QISO1 upstream of the motor feeder, the
matched AL1 USB access lock and the positive-opening two-channel SG1 shutter.
The key is removable only when QISO1 positively isolates both poles. The
shutter holds it captive while open or while any USB cable prevents closure.
J1 and the guard supply can remain live during programming. The USB shutter
is not a means to isolate the entire cabinet for service.

WD1 uses the `DD2503 configuration <../starter-guard/heartbeat-window.json>`_
with both qualifying contacts in series in HOST. WD1 terminals 1/2 take cabinet
0 V and +24 V through the 315 mA time-delay F1 on terminal 2. Leave reset
terminals 17/18 open. Exercise 0, 1, 2.5, 4, 5, 6, 7.5, 10, 50, 60, 100 and
120 Hz; only 4, 5 and 6 Hz are interior pass test points. Existing settings
use nominal 3–7 Hz window; an in-band spurious train can look valid. Verify
actual timing with a calibrated stimulus and a motor-isolated dummy load.

Verification and release
------------------------

`Cabinet BOM <bom.csv>`_, `contact model <contacts.csv>`_, `KiCad ERC
<checks/erc.json>`_, `native netlist <checks/guard-netlist.xml>`_ and
`cross-board fault results <checks/faults.json>`_ accompany this revision.
The prototype requires a panel builder to identify the real OEM pilot voltage,
permitted connections, motor current and all possible energy sources. The image
of a starter does not establish terminal identity, a spare STOP contact or the
correct response of an electronic starter.

With all energy isolated and verified, check harness pin numbering and continuity,
STOP's two independent poles, float travel and cable, isolation between mains,
logic and cabinet 24 V, feeder routing and unswitched PE. First commission with
a current-limited dummy load. Exercise actual STOP and high-high in HOST and
LOCAL with A/B commands forced on, main power removed, a correctly controlled
single retained power contact, open float wire, each supply restored in turn and
a dead USB cable trapped. Establish measured contact release, commanded restart
inhibition, insulation, temperature, noise immunity, and adequate water headroom
before operation on a pump. Only an assembled test can demonstrate the stop
time. See the `Pilz PNOZ s4 manual <https://www.pilz.com/download/open/PNOZ_s4_Operat_Man_21396-EN-20.pdf>`_
and `SJE float ratings <https://www.sjerhombus.com/wp-content/uploads/2020/05/9500460A-MilliAmpMaster-WPS.pdf>`_.

From the repository root, regenerate the native cabinet sources with
``python3 tools/build_integrated_cabinet.py --check``, then validate both
current native exports with ``python3 tools/check_integrated_cabinet.py``.
Generate the cabinet wiring PDF with ``python3 tools/draw_integrated_wiring.py``
and ReportLab. The native KiCad PDF shows all field terminals. The companion
wiring PDF identifies the field interfaces used by the integrated main board.
