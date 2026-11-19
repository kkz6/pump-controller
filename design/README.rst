Design sources and revisions
============================

The native KiCad project is the editable hardware deliverable. The JSON
definitions and Python helpers preserve the component/net source used to
produce this revision and its review documents.

The current assembly uses the unchanged Rev C main PCB plus the separate
Rev D panel. ``panel-rev-d.json`` is the panel circuit source;
``panel-rev-d-main-assembly.json`` records the main-board population and
12-wire harness. Main SW3/SW4 are omitted. Follow
``panel-rev-d-integration.rst`` for the current controls; earlier main-board
documents describe the original Rev C panel arrangement.

Source order
------------

``build_core.py`` produces ``core.json`` for metering, protection, physical
controls and OLED connections. ``build_probe_data.py`` produces the probe
front end. ``power-mcu.json`` holds the power supply and MCU definitions.
``assemble.py`` combines these into ``circuit.json`` and ``parts-complete.csv``.

The native circuit includes external CT/burden and OLED symbols, while the
main PCB includes only parts marked ``on_board``. External switches, antenna
and harness requirements also appear in the complete BOM.

Regeneration overwrites native schematic files. PCB regeneration also
overwrites routing unless the schematic-only option is used. Preserve reviewed
native changes first. For later revisions, either update these definitions
before regeneration, or make the native KiCad project authoritative and stop
regenerating it from the older definitions. Do not silently maintain two
different versions of the electrical circuit.

Review documents
----------------

* ``wiring-guide.rst`` explains external wiring and the photographed starter.
* ``revision-findings.txt`` records corrections and remaining validation.
* ``core-review.txt``, ``power-budget-review.txt`` and
  ``probe-front-end.txt`` retain electrical decisions and calculations.
* ``oled-selection.txt`` gives module size, exact harness mapping and timing.
* ``programmability.txt`` and ``operation-and-bringup.txt`` specify future
  firmware behavior. They do not contain implemented firmware.
* ``fabrication-constraints.txt`` records geometry and supplier-review needs.

The old LED-panel circuit and its completed PCB are superseded and kept under
``archive/led-panel-rev-b``. The current design has an OLED and no discrete
indicator panel. Rev C uses one external MODE button and two onboard settings
keys; the earlier selector documentation is in archive/rev-b-selector.

PDF production
--------------

The report helpers require Python 3 with ``reportlab`` and ``pypdf``. First
export the current native KiCad schematic to
``hardware/exports/schematic.pdf``. After a finalized layout report and PCB
proof exports exist, ``build_layout_report.py`` prepares their review pages.
Then ``build_report.py`` builds the combined design pack under ``output/pdf``.
Review rendered pages after regenerating; successful export alone is not a
visual or electrical validation.

CAD setup and routing helpers are described in ``tools/README.rst``. The
checks in ``hardware/checks`` govern the recorded revision; historical
iteration reports under ``archive`` are not current acceptance evidence.
