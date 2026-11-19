CAD source helpers
==================

The checked-in native KiCad project opens directly in KiCad 10; the local
``hardware/fp-lib-table`` and ``hardware/libraries/`` make footprints portable.
Scripts are optional regeneration tools. They require a Python interpreter
with KiCad 10 ``pcbnew`` and ``wx`` bindings, and ``kicad-cli`` on PATH (or set
``KICAD_CLI`` to its path). Set ``KICAD10_FOOTPRINT_DIR`` to an installed KiCad
footprint library if adding packages not in the local cache.

Regeneration replaces the routed PCB. Preserve a copy before rebuilding.
The final hand-checked placement is stored in ``design/pcb-placement.json``.
To regenerate the source and reuse that placement::

    python tools/generate_cad.py --schematic-only
    python tools/reuse_placement.py
    python tools/prepare_routing.py
    python tools/add_mains_rules.py
    python tools/finalize_routing_input.py

``layout_board.py`` recalculates placement instead of reusing it. The
90 x 70 mm, four-layer outline, 8 mm barrier, buck/isolator local groups,
mounting-hole reservations and resistor heat-spreader reservation are
explicit in that helper. It does not certify the physical design.

``finalize_routing_input.py`` exports ``hardware/pump-controller-rev-b.dsn``.
The recorded routing used Freerouting 2.5.0, a separate open-source program.
Its session output is ``hardware/pump-controller-rev-b.ses``. After routing::

    python tools/import_routing.py

This imports the session, refills the planes, runs native KiCad DRC, and
compares every board pad against the final circuit JSON. Read the resulting
``hardware/checks/layout-summary.json`` and ``main-drc.json``; a generated
file alone is not evidence of an electrically complete or production-ready
board. The native KiCad rule file is the authoritative spacing check.

``cache_footprints.py`` refreshes the portable cache from an installed
standard library and records hashes. Standard libraries retain their own
license, described in ``hardware/FOOTPRINT-PROVENANCE.rst``.
