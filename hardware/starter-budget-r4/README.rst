Budget cabinet for a conventional 24 V DC DOL starter
======================================================

This engineering reference uses the integrated main R4 and OLED panel F with
one specific factory interface: a separately powered 24 V DC three-wire
START/STOP circuit with a contactor holding contact. Select
``STARTER_OPEN_STOP`` only after qualifying the actual pilot. The original
STOP and overload operate independently of the smart board in HOST and LOCAL.
The reference replaces the two PNOZ s4 modules and the DD2503 frequency monitor
with a manual permission latch. A person can operate the original STOP if the
controller freezes. There is no independent tank-full or heartbeat-frequency
trip in this cabinet.

* `Cabinet schematic (six pages, PDF) <cabinet-schematic.pdf>`_
* `Editable KiCad project <starter-budget-r4.kicad_pro>`_,
  `parts and terminal descriptions <bom.csv>`_ and `contact paths <contacts.csv>`_
* `KiCad electrical rules <checks/erc.json>`_, `native connectivity <checks/guard-netlist.xml>`_
  and `modeled shutdown and restart cases <checks/faults.json>`_

How the original controls operate
---------------------------------

The factory STOP and overload each retain their normally closed pole in the
contactor coil supply. A second isolated, mechanically linked STOP pole and a
second overload contact open the cabinet's TRIP_RAW bus. The fast gate KH1
loses its source and the separate reclose timer restarts. This removes power
from the KEN1 latch and both series motor-feed contactors KS1 and KS2. In
HOST, KCA1 gives permission in the coil return and KCB1 pulses START. A
welded board contact can hold one of these interposers on. It cannot carry
current around the factory STOP or overload. Neither weld gives the cabinet
a reset command. On physical LOCAL the transfer disconnects the two board
command paths, and the original START/STOP operates the factory coil.

The two permission memories use mechanical NO contacts. S1 is a single
spring-return cabinet RESET with linked, break-before-make NC and NO contacts.

- **Trip:** A physical STOP, overload or other break in TRIP_RAW takes the
  supply away from KH1. A previously armed KEN1 can still have closed contacts
  while its coil releases. The KH1 interruption takes the supply away from the
  downstream KS coils during that interval. Semiconductor switch KO1, fed
  from those same coil terminals, opens the actual factory contactor coil in
  both modes.
- **After release:** KT1 detected the interruption independently and now
  requires one continuous second of healthy signal before it permits KH1
  to conduct again. During this off time KEN1 loses its mechanical seal.
  Re-establishing TRIP_OK permits the idle checks; it cannot close the
  factory coil gate or energize the motor contactors.
- **Deliberate re-enable:** A released S1 and proven idle allow KREADY1 to
  energize and seal through 33–34. Press S1 to pick KEN1 through KREADY1
  43–44 and D12. KEN1 seals at 33–34 and enables KS1/KS2 and KO1 at 43–44.
  Holding S1 throughout a trip blocks KREADY1 from picking when idle proof
  returns. A stuck command denies the idle proof in HOST.

A guarded reset restores permission with the factory contactor off, its seal
open and the physical START button released. A separate START is required for
normal pickup. A stuck board RUN can still prevent normal software shutdown
of an already running pump. A person must notice the fault and press the
original STOP. A controller issuing a new command after reset lies outside
the hardwired idle proof. In LOCAL, a stuck board contact is disconnected and
does not inhibit deliberate use of the factory controls.

The original pickup circuit across P and D has an independent differential
open-path detector (OC3). Its output powers KID1 only through released KS
mirror contacts, the factory off/holding/START-release proofs and the
selected transfer branch. HOST additionally requires the guided NC contacts
of KCA1 and KCB1. The interposer coils are fed from the cabinet supply via
J30/J35 even before permission is granted. The KID1 NO passes RAW_IDLE to
the reset stages only after qualification. During a run KEN1 seals directly
from TRIP_OK, allowing KID1 and KREADY1 to release as the motor contactors
pick up. D12 prevents the seal supply feeding backward into the proof circuit
while RESET is held. D10 and D11 suppress the two memory relay coils.

Fast stop and reclose inhibit
-----------------------------

KT1 is an always-powered **Autonics CT6S-1P2**, the version with transistor
OUT and no RS485 suffix. Terminal 5 takes fused +24 V, 4 takes cabinet 0 V,
6 is the raw healthy input INA, 9 is input/output common at cabinet 0 V and
12 sinks the KH1 input. The electromechanical output 1–3, 12 V accessory
supply and unused inputs have no harness wires. Use the manufacturer's
standard one-stage wiring diagram.

Set the CTS internal input-logic switch and parameter to PNP voltage input.
Select timer operation, plain **OND** (signal on-delay), sustained output
(HOLD), 1 ms minimum signal width, the power-loss clear setting for PV, and
a 1.000 s delay. Check the actual settings after cycling power and use key
lock on the commissioned unit. INA low must clear elapsed time and turn OUT
off. OND.1, OND.2 and pulse-output modes implement different sequences.
`Autonics model and manufacturer documentation <https://www.autonics.com/in/model/CT6S-1P2>`_
and `CT instruction manual and terminal drawing <https://cdn1.npcdn.net/userfiles/19838/attachment/1757402/20170927_b83fad5a363748af85cc31f56dd2a1ca/1456305242_CT_manu_eng_EP-KE-01-043_160224.pdf>`_.

R44 discharges TRIP_RAW; R46 connects across the input of KH1. KH1 takes
its optical input AND its switched power from the raw bus. Its output
supplies TRIP_OK. R45 discharges that bus. KO1 takes its optical input from
the enabled KS coils. Its isolated DC output connects the factory pickup
node D to KOF1.A1. Thus the pickup proof still sees P and D with KO1 open,
and the motor cannot be energized merely by KT1 recovering. D14 clamps the
actual OEM 24 V coil. D15 clamps the pair of parallel KS coils at their
terminals. KEN1 supplies the mechanical memory. Neither semiconductor gate
has feedback to its own input.

Main board and service interfaces
---------------------------------

J54 positions 1 and 2 supply the isolated field side, position 3 is unpopulated
on the cabinet harness, 4 operates panel permit KPS1, and 5 is genuine HOST
feedback through both motor contactor auxiliary NO poles and the HOST selector.
KFB1 on the PCB uses that feedback to gate K1. J52 remains a separate dry
position-feedback connector. Restore permission by resetting the cabinet;
a permanent +24 V connection to J54.5 would defeat its purpose.

Both shutter NC contacts are in the trip bus. The QISO1/AL1 trapped-key
disconnector must physically isolate the motor feeder before the USB shutter
opens, including when a cable has no VBUS power. The smart board and the
separate 24 V pilot can remain powered during motor isolation. The existing
J20 level inputs, J21 inlet and J10 CT stay on the main PCB. The motor wiring
and original start/run capacitors stay in the factory starter assembly. XO1
marks that assembly boundary. Protective earth remains continuous. The
site-specific protective conductor, capacitor and winding layout comes from
the actual starter's factory diagram.

Ratings and timing limits
-------------------------

* PS2 is the existing 24 V, 2.5 A supply. Each four-pole G7SA coil draws
  about 15 mA at rated voltage. KREADY1 and KEN1 add about 30 mA or 0.72 W
  combined when both are energized. Two LC1D09BD coils at 5.4 W each draw
  about 0.45 A at 24 V and 20 °C. KEN1's output has a 1 A DC-13 rating at
  24 V. The trip bus also carries the enabling/proof load. Check every
  series contact, connector, fuse, supply margin and voltage drop, including
  D12 under pickup and cold-coil current, for the actual conditions.
  `Omron contact and coil ratings <https://www.ia.omron.com/products/family/386/specification.html>`_ and
  `Schneider contactor ratings <https://eshop.se.com/sg/contactor-tesys-deca-3p3-no-ac-3-ac-3e-0-to-440v-9a-24vdc-coil-lc1d09bd.html>`_.
* KV1 monitors the protected motor source after QISO1. KC1 monitors the
  independent factory pilot source. RM17UBE15 covers 65–260 V and
  RM17UBE16 covers 20–80 V. Set and verify the in-range window and trip
  delay for the actual sources. A sustained loss of either must collapse
  TRIP_OK. Loss of the cabinet supply drops the memory coils directly.
  `Schneider voltage monitor ranges and functions <https://productinfo.se.com/nadigest/5c51d645347bdf0001f1f280/Master/17723_MAIN%20%28bookmap%29_0000064354.xml/%24/_17723034_Heading2_3>`_.
* KH1 and KO1 must be **G3RV-ST500-D-H DC24**, the high-speed **DC-input**
  model. At 24 V the cited ratings are 0.2 ms maximum operate, 0.4 ms maximum
  release, 0.3 Ω maximum output on-resistance and 10 µA maximum off leakage.
  The 24 VAC/DC version of the same -H family can take 21 ms to release.
  Ambient-temperature output derating, induced voltages, cable capacitance
  and contact travel apply to the assembled system.
  `Omron SSR specifications <https://www.ia.omron.com/products/family/3869/specification.html>`_.
* This design calls for measured **23.5–24.5 V DC at both protected supplies
  under load**, ≤0.30 V loss in the applicable wire and contact path, KH1
  peak load ≤1 A, and KO1 peak load ≤0.5 A. With KT1 sink residual ≤1.5 V
  at ≤25 mA, the KH1 input receives at least 21.7 V against a 21.6 V
  guaranteed pickup specification. Its nominal sink load is about 20 mA
  including R46. At 1 A, KH1 drops up to another 0.30 V in the KO1 input
  supply. The two extra memory relay coils together draw 30 mA. KT1 alone
  can require 8 W (0.34 A at 23.5 V). R44–R46 are 2.20 kΩ 1%, 1 W;
  each dissipates under 0.28 W at 24.5 V. A 10 µA leak develops at most
  0.023 V across one resistor, below the 1 V release threshold. Check the
  installed loading, source tolerance, temperature and isolation.
* Omron lists these DC outputs for DC-12 load with a 26.4 V top operating
  limit. D14 and D15 clamp coil turnoff voltage. At 24.5 V and clamp drop
  ≤1.1 V, the static peak is 25.6 V before wiring overshoot. Verify the
  **actual** peak stays within 26.4 V, clamped coil application, current and
  fuse coordination are acceptable, wiring loops are short, and motor
  stopping time remains acceptable with the added flyback. A 33 V device
  would exceed the stated switching envelope. `Omron guidance for suppressing DC inductive loads <https://www.ia.omron.com/product/cautions/18/safety_precautions.html>`_.
* The **1 ms input setting** specifies input recognition. End-to-end response
  of the complete Autonics input, transistor, wiring and both gates is a
  separate acceptance measurement. From first effective factory STOP / OL
  break, require its linked raw trip to open within **2 ms**. Confirm INA is
  ≤2 V for at least 1 ms, KT1 output turns off, KH1 and KO1 stop conducting
  within **8 ms of the raw break**, and all paths stay inhibited for at
  least **900 ms after the last recovery edge** without a startup glitch.
  A reference effective 16 ms or longer break gives a 6 ms margin to the
  2 + 8 ms envelope. The design does not rely on cold-pickup time to
  exclude a reclose from a moving armature. Prove the fastest effective
  stroke and linkage on the installed unit. Establish the **16 ms minimum
  effective interruption** by injecting shorter pulses and checking the actual
  factory coil and contacts for drop or partial travel at different points
  in pickup, with D14 fitted. The LC1D09BD published 16–24 ms opening time
  under sustained coil de-energization cannot establish this minimum. The
  pictured starter and its pulse threshold remain unverified.
* KID1 still uses mode A with 1 s continuous idle proof after the delayed
  healthy bus returns. Its rated reset time of 120 ms is **typical**. The
  measured KT1 blank interval must exceed actual worst-case KEN1/KREADY1
  drop with suppression, KS mirror release and KID1 reset. Check all supply
  restoration orders, brownouts, slow ramps, uninterrupted held RESET,
  bounce and the shortest trip that drops the factory contactor. A dip that
  stops the OEM coil without producing a qualified raw break is outside
  this reference's timing envelope. `Schneider idle timer data <https://iportal2.schneider-electric.com/Contents/docs/SQD-RE17RAMU.PDF>`_
  and `Schneider pushbutton travel <https://www.se.com/uk/en/faqs/FA306371/>`_.

Scope of verification
---------------------

Regenerate the native design, ERC, netlist, PDF and tables with
``python3 tools/build_budget_cabinet.py``. Run
``python3 tools/check_budget_cabinet.py`` to check contact paths and modeled
sequences against the exported netlist. An installer must identify and
qualify the actual pilot, original linked contacts, motor overload, transfer,
isolation, protective devices and suppression. Use a de-energized and
appropriately isolated test setup with a simulated motor load to exercise
STOP, overload opening/reset, power return and a continuously closed command,
including with S1 held. Observe the actual factory coil, both contactors and
the motor-feed output before approving motor operation. Electronic START/STOP
keypads or different pilot voltages require a separately qualified interface.

The series motor contactors, their mirror proofs and the mechanical USB
service lock remain in this profile. Removing the original monitored restart
modules also removes their internal diagnostics and channel supervision.
For example, a welded KEN1 seal or output, a short across the trip chain or
an incorrectly coupled proof contact can defeat restart inhibition. The
ordinary permission circuit carries no determined PL/SIL rating. Automatic
FULL, dry-run and elapsed-time stops depend on correct sensing, working
firmware and a functioning starter interface. Single contact faults described
here do not establish safety with additional independent failures.
