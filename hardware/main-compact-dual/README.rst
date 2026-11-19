Dual-output main PCB for single-phase pump starters
===================================================

J30 and J35 provide two independently controlled, normally open dry contacts.
Use the fitted series harness for a starter with one maintained RUN input,
or use the two contact pairs separately for a starter with dedicated inputs.
The starter continues to carry motor current and operate its own capacitor
and overload. Changing the installation profile requires a matching harness.
Select the profile from the starter's documented control inputs. The presence
of a starting capacitor alone does not identify a maintained RUN input.
Start with the `illustrated wiring drawing <exports/starter-wiring.pdf>`_.

The main PCB measures 100 × 97 mm and uses six copper layers. Four corner
mounts and a fifth mount behind the output plugs support the PCB during
insertion and removal. The extra 22 mm of board depth compared with the
LED revision provides a separate area for starter wiring and relay contacts.

Starter cable and contact selection
-----------------------------------

=============================  ========================  =================================
Verified starter interface     J30 A (K1)                J35 B (K2)
=============================  ========================  =================================
Maintained RUN                 Both contacts in series   Both contacts close for RUN
Close START, open STOP         Maintained permission     Momentary START closure
Close START, close STOP        Momentary START closure   Momentary STOP closure
=============================  ========================  =================================

Each header uses pin 1 COM and pin 2 NO. Its two contacts are voltage-free.
The board supplies no voltage to these four terminals. Both outputs serve
one starter control circuit. Keep the starter's physical STOP and overload
effective in every mode. Viewed from the component side with the output
headers at the top, the PCB terminals run left to right as A NO, A COM,
B NO, B COM. Match the connector pin numbers when working from the wire side.

* **Two wires:** The RUN harness links J30.2 to J35.1 and presents J30.1
  and J35.2 to the single RUN input. This link is inside the removable
  harness. Either relay opening breaks RUN.
* **Four wires:** Carry both complete pairs separately. This also covers a
  conventional holding circuit where START needs a parallel contact and the
  existing STOP path needs a series interruption.
* **Three wires:** Use only a documented shared common on the OEM remote
  interface. A terminated splice in the loom joins J30.1 and J35.1 to the
  single OEM common. J30.2 and J35.2 remain independent. Never assume a
  common from wire color, or join it to controller GND, neutral or earth.
  A local NC STOP must still interrupt every permitted start/holding path.

The two front-side output headers at the starter cable edge are Phoenix
1836189, each with a removable 1836079 screw plug. Fit Phoenix CP-MSTB
1734634 coding elements at pole 1 for A and pole 2 for B. With power
isolated, verify each plug mates only with its intended header, and check
the assembled loom for continuity against the drawing. The `harness parts list
<starter-harness-parts.csv>`_ identifies the mating parts. The `enclosure and cable entry
<../../mechanical/compact-dual/README.rst>`_ provides a separate opening
for the round starter-control cable.
`Phoenix header and mating parts <https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-2-g-508-1836189>`_.

OLED panel and programming
--------------------------

The `60 × 45 mm secondary board <../panel-rev-e/README.rst>`_ carries every
operator button. Its five lid positions are START, STOP, MODE, SET/RESET
and NEXT/+. In MANUAL a fresh START press requests a protected start. In
AUTO a fresh START press enables filling when the tank requests water. An
operator STOP clears that permission until another deliberate START.
The normally closed STOP
opens K1's coil supply directly. In the electronic pulse-STOP profile
the controller also has to issue the separate K2 STOP command. The two
settings buttons stay available to acknowledge a fault or edit settings
without commanding a start. Optional external buttons
terminate on the same panel at J2 through J6.

One 12-way cable connects main J32 to panel J1. With the optional
maintained AUTO/MANUAL key enabled, panel J8 selects the operating mode.
Pin 1 is the isolated 5 V common, pin 2 is MANUAL and pin 3 is AUTO. Use
voltage-free switch contacts. Neither or both positions active inhibit
starting. The key takes precedence over MODE. A mode change stops and
disarms the controller. The separate physical service transfer at main J36
selects whether the controller can command the starter at all.

Main J2 retains programming access with the boot and reset switches
removed. J2.7 and J2.8 carry native USB D− and D+, J2.1 is isolated
logic ground, and J2.5 and J2.6 expose EN and BOOT for recovery. J2.2 is
3.3 V. Never connect USB's 5 V VBUS to this pin. Leave J2.4 (ARM_CMD)
open when using native USB. A future detachable USB-C
service adapter would save space and preserve recovery access. Use an
isolated bench setup with mains and starter control disconnected for flashing.
`Espressif native USB guide <https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html>`_.

Manual override and indications
-------------------------------

The external keyed transfer socket physically disconnects the controller
outputs in LOCAL MANUAL. In the open-to-stop DOL harness the manual insert
restores only the segment of the original permission loop inserted for K1.
For a maintained RUN input or a two-button close-to-command keypad use
the corresponding blank local insert. Bridging the RUN pair could start
the pump. The OEM must support operation from its original buttons with
remote RUN removed. Change inserts only while stopped with all supplies
isolated. The three-wire position indication is electrically separate from
all starter conductors. For LOCAL MANUAL, disable any automatic start or
retry in the original starter and verify that it stays disabled after a
power cycle. Disconnect any independent automatic start source.

J36.1 is isolated GND. J36.2 senses HOST (U33 GPA3) and J36.3 senses
LOCAL (U33 GPA2). Each
confirmed position closes its own contact to pin 1. Use low-level contacts
suitable for approximately 0.30 mA with a 3.3 V supply. Confirmed HOST alone
allows controller commands. LOCAL, an open cable, contradictory inputs or
stale readings inhibit them. The PCB's optional AUTO/MANUAL key and mode
button keep their earlier functions. They cannot override the physical transfer.
With the controller disconnected, any required dry-run, overflow and operator
STOP protection must work through the starter or an independent protection path.

Green **START CMD** and red **STOP CMD** flash on issued commands. CT current
is separate evidence of motor response. Use the `profile sequencer
<../../firmware/components/starter_outputs/starter_outputs.c>`_ with the
`command LED component <../../firmware/components/command_leds/command_leds.c>`_.
GPIO20 PERMIT_D controls A through the existing hardware arm/STOP/watchdog
chain. GPIO19 RUN_CMD controls B. The sequencer exposes an accepted arm
event for the GPIO17 hardware latch. Startup must clear that latch and
validate fresh inputs before accepting an arm. Apply a STOP before display or radio work.
Use the starter's documented pulse times and measured relay release/operate
times. The sequencer ships disabled until explicitly configured. It settles
the stop/permission path before issuing START, drops START before pulsing
STOP, suppresses commands in LOCAL, and requires a fresh arm after a stop,
fault or transfer. The pulse-STOP profile issues a synchronization STOP when
HOST is first established, even when the motor state is unknown.

Electrical limits and qualification
-----------------------------------

A latching electronic starter that requires a STOP pulse can keep running
if the replacement controller loses power. Use that profile for unattended
operation only with an independently qualified OEM shutdown/inhibit path.
The software timer cannot limit a welded contact or a stalled output driver.
Any button that engages a starting capacitor needs independently enforced
cutout. Keep the original overload, hardwired STOP and anti-restart functions
effective and verify that a stuck START cannot restart after STOP release.
The pictured Crompton/RMG models have no verified drop-in pin assignment.
The G5Q power relay's published minimum-load reliability reference is
10 mA at 5 V DC. Verify the actual input voltage/current and inductive
rating. A very low-current scanned keypad may require a rated signal adapter.
`Omron G5Q data sheet <https://components.omron.com/us-en/system/files/2025-06/datasheet_pdf/J155-E1.pdf>`_.

The physical PCB, harness and starter have not been powered or tested together.
The minimum nominal PCB copper gap from the four starter terminals and their
nets to onboard mains/metering is 9.425 mm. The minimum nominal
live-to-isolated gap is 8.060 mm at a relay pad pair. Both measurements project
all six layers onto the same plane. Component insulation, wiring, board
material and finished production tolerances need separate qualification.
This is an engineering prototype. Confirm the finished copper dimensions,
PCB dielectric construction, connector barriers, cable insulation, dielectric
withstand, heating, EMC, contact behavior and pump protection before a mains
installation. The earlier Robu archives correspond to other board revisions.

Design and verification files
-----------------------------

* `KiCad project <pump-controller-compact.kicad_pro>`_, `PCB
  <pump-controller-compact.kicad_pcb>`_, `schematic PDF <exports/schematic.pdf>`_
  and `parts list <bom.csv>`_.
* `Populated top view from KiCad <exports/board-top.png>`_. The two green
  headers at the top edge are A and B. The drawing includes approximate
  component bodies. Mating plugs belong to the cable harness.
* `Native CAD validation <checks/independent-summary.json>`_,
  `clearances and mounting geometry <checks/independent-geometry.json>`_
  and `isolation rule tests <checks/isolation-negative-tests.json>`_.
* `OLED panel and cable validation <checks/panel-integration.json>`_,
  `five-button front view <../../output/enclosure-compact-dual/five-button-panel.png>`_
  and `panel control component <../../firmware/components/starter_outputs/panel_controls.c>`_.
* `Main board prototype Gerbers and drills <pump-controller-compact-dual-gerber-prototype.zip>`_,
  `separate stencil <pump-controller-compact-dual-stencil-prototype.zip>`_
  and `independent CAM inspection <checks/independent-gerbers.json>`_.
* `Starter harness continuity result <checks/starter-harness.json>`_,
  `harness tests <../../tools/check_dual_starter.py>`_
  and `firmware profile tests
  <../../firmware/components/starter_outputs/tests/starter_outputs_test.c>`_.
