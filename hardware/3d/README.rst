3D model scope and provenance
=============================

The current exported controller is Rev C. The native electrical board keeps
its existing ``pump-controller-rev-b.kicad_pcb`` filename; its revision metadata
and current circuit are Rev C. ``model-coverage-rev-c.json`` records the exact
board SHA-256 used for the 3D exports. No electrical geometry is changed by
the visualization process.

Open ``output/3d/viewer.html`` in a browser for an offline rotatable view.
Everything needed is embedded in that file. Drag to rotate; scroll or pinch
to zoom. The model selector switches between the PCB and the starter concept.

Deliverables
------------

* ``output/3d/pump-controller-rev-c.step``: solid CAD assembly for mechanical
  inspection/import. It contains the board and the component bodies.
* ``output/3d/pump-controller-rev-c.glb``: portable colored mesh assembly,
  including pads. It uses the glTF metre/Y-up convention.
* ``output/3d/pcb-rev-c-isometric.png`` and ``pcb-rev-c-underside.png``:
  native PCB renders showing the two assembled sides.
* ``output/3d/starter-assembly-concept.glb``: editable scene showing a
  representative retrofit with the retained two capacitors, 2-pole contactor,
  bottom terminal strip, analog meters and front breaker. The cover is
  exploded beside the case with its exterior visible.

The front concept retains START and STOP and adds one MODE button to toggle
AUTO/MANUAL. SET/RESET and NEXT/+ are small buttons on the controller PCB,
not extra front-panel controls. The OLED carrier is 36 x 12.5 mm; its active area is 22.38 x 5.58 mm.
It does not contain a rotary selector or a large display. The old external
water controller is omitted from the proposed integrated arrangement.

What is accurate, and what is illustrative
-----------------------------------------

The PCB outline, mounting-hole locations, component positions, rotations and
side assignments come from the checked native board. All 208 electrical
components are represented: 198 use the installed KiCad standard 3D bodies,
and 10 use project-created simplified bodies. The two mounting holes do not
include a qualified fastener assembly.

``approximate-bodies.json`` identifies the simplified PSU, MCU, relays,
fusible resistor, fuse, MOV, metering IC, isolated interface and buck package.
These envelopes are for visualization. Their pin shapes, lead forming,
tolerances, solder joints and some heights are approximate. They are not
manufacturer-approved mechanical models. Mating terminal plugs are absent.

The starter enclosure, capacitors, contactor, meters, buttons, CT, antenna and
all cable paths are illustrative volumes. The 270 x 270 x 110 mm enclosure
envelope is a modeling assumption, not a measurement or a required box size.
The proposed lower-right board position has not been checked for depth,
insulation barriers, screw access, wire bends, capacitor servicing or closed
door clearance. Do not use this scene to order an enclosure or drill holes.

The cable paths show destinations only, not electrical connections. Use the
wiring guide for terminal assignments. The illustrated OLED cable crosses
the enclosure and exceeds the earlier provisional 100 mm allowance; its
length, lid movement and signal integrity need redesign or validation with
the actual starter. The scene does not qualify that longer harness.

Sources
-------

The standard package models come from the official KiCad 10.0.8 distribution,
maintained by the KiCad library contributors. They are embedded in generated
assembly exports; a raw standard-model collection is not redistributed.
See ``hardware/KICAD-LIBRARY-LICENSE.md`` for the CC-BY-SA 4.0 notice and
KiCad's generated-design exception. Upstream:
https://gitlab.com/kicad/libraries/kicad-packages3D

Project-created body dimensions use the current footprint drawings and
manufacturer information linked in the BOM, including:

* RECOM supply: https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf
* Espressif module: https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf
* Omron relay dimensions: https://components.omron.com/eu-en/system/files/2025-04/ds_related_pdf/Y225-E1.pdf

Reproduction
------------

Use Python 3.12 with ``cadquery-ocp`` for the body builder, and ``numpy`` plus
``trimesh`` for the assembly/viewer builders. A Python interpreter with
KiCad 10 ``pcbnew`` is needed for ``prepare_3d_board.py``. Standard model paths
must resolve through ``KICAD10_3DMODEL_DIR``. Tested helper versions are listed
in ``hardware/3d/requirements.txt``. Run in repository root::

    python tools/build_3d_bodies.py
    kicad-python tools/prepare_3d_board.py --board hardware/pump-controller-rev-b.kicad_pcb --tag rev-c
    kicad-cli pcb export step --force -o output/3d/pump-controller-rev-c.step tmp/3d/pump-controller-rev-c-visualization.kicad_pcb
    kicad-cli pcb export glb --force --include-pads -o output/3d/pump-controller-rev-c.glb tmp/3d/pump-controller-rev-c-visualization.kicad_pcb
    python tools/build_3d_assembly.py --board pump-controller-rev-c.glb
    python tools/build_3d_viewer.py --board pump-controller-rev-c.glb --revision "Rev C" --components 208

``kicad-python`` above means the locally chosen Python interpreter containing
KiCad bindings; it is not a command installed by every KiCad distribution.
The authoritative board is never overwritten. The temporary visualization
copy gets local model paths and is intentionally excluded from version control.

Native PNG export example::

    kicad-cli pcb render --width 1800 --height 1350 --background opaque --quality high --floor --perspective --rotate 330,0,30 --zoom 0.72 -o output/3d/pcb-rev-c-isometric.png tmp/3d/pump-controller-rev-c-visualization.kicad_pcb

Earlier Rev B render/export files are archived under ``archive/rev-b-3d``.
They do not include the revised pushbutton interface and are not the current
mechanical reference.
