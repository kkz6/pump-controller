Compact controller review for an existing pushbutton starter
============================================================

**Hold the compact main PCB purchase for this retrofit.** The installation
requires the automatic controller to operate the existing START and STOP
circuit. The 100 x 75 mm main board exposes one maintained contact path.
The 60 x 45 mm panel accepts isolated button inputs. The present pair does
not provide independent START and STOP outputs for a three-wire DOL starter.

Starter and local controls
--------------------------

The compact netlist connects J30.1 to K1 COM, K1 NO to K2 COM, and K2 NO to
J30.2. The contact between the two relays stays on the PCB. In a conventional
starter, the holding contact keeps the contactor energized after the operator
releases START. A controller contact across START cannot interrupt that
holding path. A contact in series can interrupt the coil but cannot initiate
a start with the START button and holding contact both open.

The proposed interface needs independent start and stop functions at the
verified starter control terminals. The physical STOP and motor overload must
remain effective in manual and automatic operation. The current circuit has
no direct feedback from the external overload. If it trips while RUN remains
asserted, reclosing it can restart the pump. Verify that releasing STOP,
resetting the overload or restoring power cannot cause an unintended start.

The RMG DFAWLC-044 manual shows separate ON and OFF connections for a
single-phase starter. Automatic starting with the installed RMG confirms that
the existing installation handles startup. Identify the installed model,
control voltage, holding circuit, overload and start-capacitor cutout from
its wiring diagram or a qualified electrician's de-energized trace before
choosing output contacts. See the `RMG manual, figure 3
<https://rmgautomation.com/Downloads/UserManual/DFAWLC-044.pdf#page=3>`_ and
`Schneider Electric's holding-contact description
<https://www.se.com/us/en/faqs/FA117145/>`_.

Panel J2 and J3 accept optional voltage-free START and STOP auxiliary
contacts. Keep live starter contacts off these inputs. The onboard START and
STOP are also functional. For an external NC STOP, JP1 must be removed or
that external button is bypassed. An unplugged panel opens the K1 permission
path. The panel can remain a prototype candidate once the required physical
controls are settled. See the `panel contact diagram
<../hardware/panel-rev-e/README.rst>`_.

Load, voltage and water sensors
-------------------------------

* J10 measures motor current with the specified 1000:1 CT around one insulated
  conductor carrying the total motor current. Its 6.8 ohm burden stays at the
  CT. The secondary wiring is mains-referenced. J1 supplies the controller
  and measures incoming voltage. The PCB does not carry motor current.
  Dry-run shutdown still needs firmware, wet-running calibration on the
  installed pump and a controlled underload trip test.
* J20 accepts a common and four tank electrodes, giving five discrete level
  bands. J21 has a separate drive for the inlet reference. RMG's manual
  describes a two-rod inlet sensor that shares the tank common, allowing six
  field wires. Verify the installed return and qualify that loading to reuse
  the six conductors. Do not jumper the two excitation outputs or use earth
  or neutral as an electrode. See `RMG step 6
  <https://rmgautomation.com/Downloads/UserManual/DFAWLC-044.pdf#page=4>`_
  and the `probe circuit and acquisition model <probe-front-end.txt>`_.
* J31 is a separate, normally closed high-high float input in the relay
  permission path. Leaving it open inhibits starting. A link removes the
  independent overflow trip. The four tank probes do not provide that
  independent contact.

KiCad electrical-rule and all-track layout checks on both boards recorded
zero violations, zero unconnected items and zero schematic/layout
differences. Physical starter operation, dry-run shutdown, noise immunity
and mains insulation still require tests on hardware. See the
`compact netlist <../hardware/main-compact/checks/control-main-netlist.xml>`_
and `bench test plan <rev-e-bench-acceptance.rst>`_.
