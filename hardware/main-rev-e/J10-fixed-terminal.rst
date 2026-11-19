J10 fixed live-CT termination
============================

J10 uses Phoenix Contact 1727010, MKDS 1/2-3,81, a fixed PCB screw terminal.
The CT lead is terminated during assembly and retained by its separate cable
clamp. There is no removable CT plug that can be inserted into the isolated
J31 or J21 sockets. Do not add an interchangeable inline plug to this lead.
This change prevents that specific plug mismatch; it does not prevent every
possible wiring error or establish electrical-insulation qualification.

Pin 1 remains M_CT_HI at (30,71) mm; pin 2 remains M_GND at (33.81,71) mm.
Both conductors belong to the live metering domain. The fixed lead requires
insulation appropriate to that domain, its own cable entry and strain relief,
and separation from isolated sensor wiring. Its installation/service work
requires the pump supply to be isolated. Keep the selected CT's permanent
burden in place; this is not the analogue ammeter connection.

Land pattern and fit
--------------------

The KiCad 10 land pattern is cached under
``libraries/TerminalBlock_Phoenix.pretty/TerminalBlock_Phoenix_MKDS-1-2-3.81_1x02_P3.81mm_Horizontal.kicad_mod``.
It agrees with the manufacturer's dimensional and drilling drawings:

* Pitch 3.81 mm; two 1.1 mm drilled holes. Lands are 2.0 mm across, giving
  a 0.45 mm nominal annulus. Pad 1 is a rounded rectangle and pad 2 a circle.
* Body 7.61 x 7.3 mm, installed height 8.5 mm, solder pins 3.5 mm long.
* At the existing location, the nominal body spans x28.1..35.71 and
  y67.3..74.6 mm. Its wire-entry face points toward the bottom board edge.
* The nominal courtyard spans x27.6..36.21 and y66.8..75.11 mm. The native
  courtyard polygon's tolerance-expanded bounds are recorded in the patch
  report; no neighbouring footprint courtyard intersects it.

Phoenix specifies 5 mm stripping and 0.22..0.25 Nm tightening torque. Support
the terminal housing while tightening because two solder pins alone must
not take the screwdriver load. Select the conductor/ferrule combination from
the actual part's connection table and verify pull retention during assembly.
Its published voltage ratings depend on installation category and pollution
degree; this record does not elevate them to a completed-device rating.

Repeatable routed-board update
------------------------------

Run with KiCad's Python runtime::

  .tools/kicad-python tools/patch_main_rev_e_j10.py --board PATH --report REPORT.json

The patch replaces only the J10 footprint expression. It preserves all bytes
outside that expression, the footprint UUID, both pad UUIDs, pad centres,
pin/net assignments and the project file. It rejects unexpected pin placement
or a courtyard overlap. It does not refill or delete existing copper zones.
Refill zones after applying it, then rerun full source/parity, clearance and
CAM checks. The new 2.0 mm land needs a larger zone opening than the original
1.8 mm land. A preserved old fill is not valid final clearance evidence.

The normal Rev E builder also selects the fixed part. Source JSON, schematic
properties, cached symbol and BOM are updated together. The updated PCB model
must be re-exported before refreshing the enclosure assembly.

Primary sources reviewed 19 November 2026
-----------------------------------------

* Product, dimensions, wire data and application note:
  https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mkds-1-2-381-1727010
* Manufacturer dimensional drawing, visually inspected:
  https://caas.phoenixcontact.com/caas/v1/stable/media/51904/full/b1500?format=jpg
* Manufacturer drilling drawing, visually inspected:
  https://caas.phoenixcontact.com/caas/v1/stable/media/20652/full/b1500?format=jpg
