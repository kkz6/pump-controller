Mounting the integrated main board and OLED panel
=================================================

The main PCB outline is **100 × 115.5 mm**, with a nominal board thickness of
1.6 mm. Panel F is **60 × 45 × 1.6 mm**. The
`1:1 mounting and connector drawing <exports/mounting-template.pdf>`_ contains
a main plan, its underside projected into the same view, and the OLED/button
panel plan. Print A4 at actual size and measure the 50 mm scale bar in each
print. Coordinates start at the upper-left corner of the board outline as
viewed from the component side. X increases right and Y increases down.

Main mounting centres
---------------------

* **H1** (4, 4) mm, diameter 3.2 mm.
* **H2** (96, 4) mm, diameter 3.2 mm.
* **H3** (96, 111.5) mm, diameter 3.2 mm.
* **H4** (4, 111.5) mm, diameter 3.2 mm.
* **H5** (50, 4.2) mm, diameter 3.2 mm.

Use the five M3 insulating supports on the main board and all four M2.5
mounts on panel F. Measure the installed dimensions
of both the screw heads and the support shoulders against adjacent copper
and component bodies. The drawing uses actual native hole bores, connector
origins, side-specific courtyards and plated through-hole lead locations.
Rear lead positions indicate possible protrusion. Circular symbols use the
larger of the two drill dimensions for a slotted hole. The copper insulation requirement also applies in
three dimensions to case walls, support hardware, nearby conductive parts
and tools. Derive required installation spacing from the cabinet environment.

Access in the starter
---------------------

Give the J54 side-entry five-way cabinet plug room to unlatch and withdraw.
The vertical J52 selector plug and J41 service connector need space above
the board. Route J10 and its strain relief in the mains-referenced wiring
area. J32 needs its own clear path to the twelve-position panel harness.
Keep the shielded USB-C entrance aligned with J40 after mounting the
populated board. Verify the actual mating cable, the captive-key isolator,
the two-channel shutter switch, full shutter travel and cable obstruction
in the finished enclosure. The radio module uses an external antenna;
include its cable, connector and the metal cabinet in the fit and RF check.

The existing enclosure, old hole pattern, wire openings and shutter case
coordinates were developed for other boards. The R4 installation needs its
own support positions, cable access, circuit barriers and shutter alignment.
For the front-side U1 converter, the manufacturer specifies 16.7 ±0.5 mm
body height. The underside Y1 package has a 4.2 mm drawing envelope. Allow
for these parts before adding solder height, seating and clearances. See the
`RECOM converter drawing <https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_
and `Abracon crystal drawing <https://abracon.com/Resonators/ABLS.pdf>`_.

The footprint-only XY drawing cannot establish the assembled Z envelope.
Measure the largest projection on each face (including lead ends), PCB
thickness, installed plugs, cable bends, insulation clearances and assembly
tolerances. Verify space to mate and withdraw every plug. The minimum
panel rear-space allowance and switch/OLED envelope come from the
`panel mechanical interface <../panel-rev-f/connector-mechanical-interface.json>`_.
Check each actuator against its actual purchased switch and check the display
window with the retained module. The two motor contactors, guard relays,
power supply, service isolator and terminal blocks also need cabinet space.
The starter dimensions, final installed depth and a complete enclosure
fit have not been measured.

Regenerate from the repository root with
``python3 tools/draw_integrated_mounting.py`` in a Python environment with
ReportLab. Set ``KICAD_PYTHON`` to a KiCad Python interpreter with pcbnew if
using a different KiCad installation.
