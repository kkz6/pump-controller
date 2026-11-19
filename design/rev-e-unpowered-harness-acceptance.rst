Rev E unpowered harness and STOP fixture acceptance
===================================================

``rev-e-unpowered-harness-acceptance.json`` contains 669 individually numbered
measurement cases. It is a test specification: every result starts as
``not_run`` and every measurement is blank. There are no physical test passes
in this file. Copy it into a serial-numbered assembly record when executing it.

Scope and test equipment
------------------------

Unpowered means no mains, motor, coil supply, USB, programmer, battery or other
operating supply is connected. Verify absence of stored energy before removing
the leads or connecting the fixture. The main PCB, live CT assembly and OLED
module are excluded from the fixture. A bounded resistance-meter stimulus is
allowed; this is not literally zero electrical energy.

Use a verified resistance-test range with at most 0.2 V open-circuit stimulus
and 1 mA short-circuit current. Zero the fixture leads. Do not use a diode-test
range, insulation tester or megohmmeter on the populated panel. The limits
below are engineering assembly screens; they are not contact-life, dielectric
withstand or installation-insulation specifications.

* Closed wire/contact path: at most 2 ohm, including the zeroed fixture.
* Open disconnected cable or mechanical contact: at least 1 Mohm.
* Different nets on the populated panel: at least 100 ohm for the specified
  copper-bridge screen, after settling for at least three seconds in both
  meter polarities. The panel has intentional resistor and semiconductor paths;
  a blanket megohm criterion across its connectors would be incorrect.

The matrix specifies exceptions where contacts deliberately join different
net names. Do not infer powered logic state or safe coil release from an
unpowered resistance reading. Contact wetting and switching remain separate
operating-load tests.

Fixture sequence
----------------

1. Test the GH12 and PH4 cables disconnected at both ends. The matrix includes
   every pair of endpoints, not only adjacent cavities. GH12 cavities 1–12
   and PH4 cavities 1–4 must be one-to-one. Test the two cable assemblies for
   unintended joins while all four ends remain detached from electronics.
   Identify cavities using the manufacturer drawing and mating orientation;
   wire colours and apparent left-to-right order are insufficient.
2. Test each fitted external NO button lead, NC STOP lead and NC high-high
   float independently. Test the maintained key's two stable positions at its
   detached GH3 plug: 1 common, 2 MANUAL, 3 AUTO. Only the selected throw may
   close. The empty-fixture case is not a requirement for a center-off key.
3. Test the populated panel at rest, with host, display, key and external
   contact leads absent. Fit JP1 for this stage. It checks the GH12/PH4 routing
   and absence of direct cross shorts; it does not check powered I2C or key
   conditioning. The OLED module remains disconnected.
4. Attach the accepted GH12 cable to the panel only. Probe its free main-end
   breakout, cavities 1 and 2. Test local STOP with JP1 fitted, then local and
   external STOP in series with JP1 removed. Test an absent external STOP with
   JP1 absent: it must leave the path open. Other NO keys must not restore a
   broken STOP path. A fitted JP1 with an operational external STOP is a
   prohibited assembly because it bypasses that external contact.
5. Test local and optional external START, MODE, SET and NEXT in parallel,
   one option at a time, with every other NO button released. Use the connector
   numbers in the matrix; similar GH2 housings do not prevent mis-mating.
6. For the detached STOP/high-high fixture, connect the free host cavity 2
   through a labelled fixture jumper to high-high lead cavity 1. Measure from
   host cavity 1 to high-high lead cavity 2. Exercise both STOP contacts and
   the float in all eight combinations. This models the main board's series
   connection; it does not measure the main PCB or energize a relay.

Record serial numbers, revision, instrument/fixture identification, operator,
date, measured resistance and polarity, and each result. Mark absent optional
leads not applicable with a reason. A failure stops acceptance; repeat the
complete affected stage after rework. A fixture pass does not authorize mains
connection or unattended pumping.

Independent schematic check
---------------------------

``../tools/check_rev_e_controls.py`` exports the current native schematics,
checks 200 explicit control pins, 34 critical values and exact membership of
16 critical nets, evaluates 1,024
contact-only STOP combinations and all four relay-contact combinations, and
writes ``../hardware/main-rev-e/checks/hardwired-control-review.json``.
The graph excludes resistors, semiconductors, stored charge and component
failures. It verifies series/parallel wiring; it is not a transient simulation.

The panel is materialized as a native schematic and routed PCB. It contains
two NPN key-conditioning stages and is not a purely passive panel. Neither
that fact nor a CAD pass establishes that a board has been assembled or tested.
Powered key thresholds, watchdog/reset/latch behavior, actual STOP timing,
relay/contactor interruption, thermal behavior and EMC remain in the separate
``rev-e-electrical-review.rst`` and bench qualification records.
