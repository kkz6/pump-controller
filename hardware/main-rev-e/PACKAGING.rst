Rev E checked prototype archives
===============================

**100 x 80 mm main board on hold.** The optional AUTO key is connected to
MCP23017 GPB7. Microchip restricts this pin to output use because transitions
during reads can corrupt the shared I2C bus. The Rev E Gerbers and test records
below preserve the historical layout. Use the corrected compact design for
further engineering. See the `Microchip pin advisory
<https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_.

Generate archives only after the final board is routed, its zones are filled,
and its matching schematic/source files are fixed. From the repository root::

  .tools/3d-modern/bin/python tools/validate_main_rev_e.py
  .tools/3d-modern/bin/python tools/export_main_rev_e.py
  .tools/cam-validation-env/bin/python tools/check_main_rev_e_gerbers.py --cam hardware/main-rev-e/gerber --stencil hardware/main-rev-e/exports/stencil
  .tools/3d-modern/bin/python tools/package_main_rev_e.py

The first command runs fresh native ERC/DRC/parity checks, independent geometry
and source comparisons, and the isolation-rule negative tests. The second
exports current CAM and binds its checksums to the source files. The third
independently parses the eleven PCB Gerbers (six copper layers plus mask,
legend and outline), two paste layers, both drills,
electrical-test netlist and job file, including actual mask geometry. The
last command requires all of those matching results before producing:

* ``pump-controller-main-rev-e-gerber-prototype.zip``: eleven board Gerbers,
  separate PTH/NPTH Excellon files, job file, IPC-D-356 reference netlist,
  drill report, manufacturing notes and package manifest; 18 files total.
* ``pump-controller-main-rev-e-stencil-prototype.zip``: front/back paste,
  stencil notes and manifest; four files total. Keep it separate from the
  bare-board upload.
* ``package-manifest.json``: source/evidence hashes, proposed process settings,
  archive hashes and every archive member's checksum.

The package gate rejects missing or changed sources, failed or altered check
reports, changed CAM, unparsed extra files and changed process assumptions.
It checks ZIP contents and source stability again before publishing archives.
Running raw export or retrying packaging removes any older prototype archives
first so a failed run does not leave a stale upload file.

These are bare-PCB engineering prototype files. Fabricator acceptance,
electrical testing against the supplied IPC reference and assembled-board
testing remain separate. The CAM check does not derive connectivity from
copper polygons and does not qualify a completed mains device.

``tools/test_package_main_rev_e.py`` tests successful separation and refusal
paths using synthetic evidence confined to temporary directories. Those tests
verify the package gate; they are not pass evidence for a real board.
