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
The initial session is archived as ``pump-controller-rev-b-fast.ses``;
the final native board also contains subsequent checked local repairs.
To import a newly created session explicitly::

    python tools/import_routing.py --session path/to/new-session.ses

This imports the session, refills the planes, runs native KiCad DRC, and
compares every board pad against the final circuit JSON. Read the resulting
``hardware/checks/layout-summary.json`` and ``main-drc.json``; a generated
file alone is not evidence of an electrically complete or production-ready
board. The native KiCad rule file is the authoritative spacing check.

``cache_footprints.py`` refreshes the portable cache from an installed
standard library and records hashes. Standard libraries retain their own
license, described in ``hardware/FOOTPRINT-PROVENANCE.rst``.

Checks and local routing repairs
--------------------------------

For a read-only manufacturing export and checks, use::

    python3 tools/export_fabrication.py
    python3 tools/validate_gerbers.py
    python3 tools/package_fabrication.py

The exporter requires KiCad 10 and a Python interpreter with ``pcbnew``;
set ``KICAD_CLI`` and ``KICAD_PYTHON`` where necessary. The Gerber validator
requires Python 3.10 or newer and Gerbonara 0.13.0. It creates SVG CAM previews;
PNG rendering is optional. The package is labelled for Robu engineering review
and includes the outstanding vendor-rule audit. It does not change the routed
board, create an order, or waive any manufacturing requirement.

To validate the existing routed board without importing an earlier router
session, run::

    python tools/import_routing.py --check-only
    python tools/audit_vias.py

Unlike the read-only exporter, ``import_routing.py --check-only`` refreshes
fields, refills zones and saves the PCB. Use it only when that update is intended.

``audit_vias.py`` uses native pad geometry to inventory via-drill overlap
with SMT copper. Listed overlaps require filled and plated-over processing
or rerouting; ordinary via tenting is not an accepted substitute.

``apply_route_patch.py PATCH.json`` applies a narrowly specified set of
track/via removals and additions, then refills zones. Coordinates are in mm.
The accepted repair patches are preserved under
``archive/layout-iterations/``. Do not replay them on the final board: those
changes are already incorporated, and removal matches must be unique.

``export_routing_geometry.py`` reads the current native board and its latest
``main-drc.json`` report to create ``hardware/checks/routing-geometry.json``.
It is read-only. ``grid_route.py`` uses Python 3 with NumPy to propose routes
in ``hardware/checks/proposed-routes.json``; it does not edit the PCB. Its
occupancy model intentionally overestimates rectangular pad corners and
ignores copper pours during search. All proposals must be checked after
native zone refill using the project-specific KiCad rules. A route-search
success is not a DRC or manufacturing acceptance result.

``record_board.py`` records actual final coordinates, side and rotation in
``design/pcb-placement.json`` and ``hardware/placement.json`` and refreshes
the DSN from the native board. Run it after ``import_routing.py --check-only``
so its routed status comes from the latest native connectivity result.

Rev C control change
--------------------

The active native filenames retain their original basename; title blocks and
``design/circuit.json`` identify revision C. ``apply_rev_c_controls.py`` is a
one-time incremental ECO helper for a Rev B board after generating the Rev C
source. It removes D33/D34 and merges their former coil-feed rail into
STOP_RETURN. ``design/rev-c-control-route.json`` records the separately
checked added connection. Both changes are already present in the final
board; do not replay the ECO or route patch on it.

The final Rev C interface also adds SW3 SET/RESET and SW4 NEXT/+ on the top
of the isolated PCB area. ``add_rev_c_settings.py`` adds their footprints to
the existing routed design after the coil-feed ECO; the checked settings
connections are recorded in ``design/rev-c-settings-route.json``. Those
additions are already incorporated in the final native board. External
wiring uses STOP, START and one MODE button; J32 pins4 and6 are reserved.
