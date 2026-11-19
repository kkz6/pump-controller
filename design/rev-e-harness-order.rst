Rev E preassembled loom and installation boundary
=================================================

The control panel needs two completed leads. All five buttons are soldered to
the panel by the PCB assembler. Ship the enclosure with the panel, OLED,
current sensor lead and internal wiring already fitted and restrained. Leave
unused external-button and key sockets empty. A bare PCB order supplies none
of these assemblies.

Lead schedule for the harness shop
----------------------------------

* PANEL, quantity one. Main J32 to panel J1, JST GH 12 positions, 150 mm
  nominal, 28 AWG stranded. Use two GHR-12V-S housings. Connect numbered
  cavities 1 through 12 straight through. The harness carries two supplies
  and the hardware STOP loop. Require a full continuity and insulation/short
  matrix on each finished *disconnected* lead.
* DISPLAY, quantity one. Panel J7 to Waveshare 14657, 100 mm PH 2.0 four-way
  cable. Both ends are numbered 1 SCL, 2 SDA, 3 GND, 4 VCC. Check the four
  cavities on the actual module and cable before applying power. Use a verified
  finished cable or order the same schedule from the harness shop. Never
  assign voltage by insulation colour. The target shared-bus length is 250 mm.
* CT, quantity one. Supply CT1 and RB1 as one insulated, strain-relieved
  assembly. Solder the 6.8 ohm burden across the secondary **at CT1** during
  assembly. Keep the burden across the winding when the lead is disconnected
  at the controller. Fit the lead captive at main J10 under the live guard.
  Its two leads belong to the live metering domain. Route them only in that
  compartment. Mark the CT primary direction and lead polarity for real
  power measurements. Prove polarity with a known load before calibration.
* STARTER, sized to the verified starter. Prepare labelled power and coil
  pairs in the shop after recording the actual terminal style, conductor
  ratings, lengths and coil data. Terminate the board ends before delivery,
  protect and identify both ends, and leave the starter ends suitable for its
  specified terminal and torque. Retain its protective earth, overload,
  hardwired STOP and capacitor-start mechanism. Confirm every possible coil
  energizing path, including the holding contact and original controller,
  before assigning connector terminals. A parallel holding or remote-start
  branch bypassing the controller's stop contacts defeats its trip.
* TANK and INLET. Fit J20 and J21 mating plugs to the identified existing
  sensor leads once. Mark COM and each electrode by terminal number. Verify
  the independent inlet return or actual shared water reference with the
  old controller disconnected. Use insulated low-voltage sensor routes away
  from the motor, coil and capacitor wiring.
* HIGH-HIGH. Supply J31 with the selected normally closed float already wired
  to its plug. The float provides an independent high-level stop. A test link
  removes that protection and belongs only on an identified test assembly.
* Optional starter button contacts. Use a shop-made, end-labelled pair to
  panel J2 (START, NO) and another to J3 (STOP, NC) from independent,
  suitably insulated auxiliary contact blocks. Remove panel JP1 when J3 is
  used. The existing power-rated contacts retain their original functions.
  With no external STOP, fit JP1 in the shop and verify panel SW1 still
  interrupts the stop loop. Do not share a mains contact terminal with the
  panel electronics. Optional MODE, SET, NEXT and key leads follow the
  panel parts-and-interface schedule.

The numbered unpowered acceptance matrix is
``rev-e-unpowered-harness-acceptance.json``; its fixture procedure and limits
are in ``rev-e-unpowered-harness-acceptance.rst``. All physical results remain
unrun until recorded against a particular completed harness/panel.

Commissioning boundary
----------------------

There is no universal starter-side mating plug. A qualified electrician must
identify the actual starter terminals, isolate the supply, deal with stored
capacitor energy, and make and verify the remaining fixed connections. A cable
shop can preterminate the wires once those terminals are identified. No user
soldering, crimping or individual jumper wires should be needed between the
two PCBs or the OLED. Guard access is required to service the live section.

Before connecting mains, inspect routing at full door travel, clamps, bends
and covers. Check for wrong-position plugs, swapped wires, a bridged external
STOP, open returns and shorts between adjacent cavities using the disconnected
loom and a low-voltage test fixture. Check each optional button and both key
positions individually. Record the measured result against the harness serial
number. A connector's latch establishes orientation, not the function of a
similar adjacent socket.

Drawings and sources
--------------------

* Panel connector and option pinouts: ../hardware/panel-rev-e/parts-and-interface.rst
* Drawing: ../output/rev-e/connection-overview.png
* JST GH: https://www.jst-mfg.com/product/pdf/eng/eGH.pdf
* OLED module: https://www.waveshare.com/product/ai/displays/oled/0.91inch-oled-module.htm
* Candidate finished OLED lead: https://www.pololu.com/product/5623
