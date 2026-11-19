Rev C wiring drawings
=====================

Start with the `six-page illustrated guide
<../../output/pdf/pump-controller-rev-c-wiring-guide.pdf>`_ and the fuller
`terminal guide <../../design/wiring-guide.rst>`_.

* ``connector-map.svg`` / ``.png``: actual main-board connector positions and
  PCB pad numbering, viewed from the top component side.
* ``panel-controls.svg`` / ``.png``: three external controls, two internal PCB keys and J32 wiring.
* ``power-and-coil.svg`` / ``.png``: functional power/coil connections, with
  the capacitor-start compatibility condition clearly marked.
* ``oled-harness.svg`` / ``.png``: exact J33-to-display signal/pin mapping.
* ``connector-locations.json``: connector pad positions and nets extracted
  from the final Rev C native PCB, with its SHA-256 hash.
* ``reference-starter.png``: installation reference photograph for visible
  component identification. It does not establish exact terminal functions,
  coil voltage, overload protection or a safe mounting/wiring arrangement.

The existing RMG AUTO mode starts without a green START press. The device
performing the capacitor-start sequence is still unidentified; the Rev C
single series coil interface is not yet a verified drop-in RMG replacement.
Do not infer wiring from colours or relocate capacitor/motor wiring from these
concept drawings. The exact controller terminals and the unverified starter
integration are deliberately distinguished in the guide.

Reproduction
------------

Refresh positions with ``python tools/export_wiring_locations.py`` using a
Python environment with KiCad 10 ``pcbnew`` bindings. Then run
``python design/build_wiring_guide.py`` with ReportLab installed. It writes
the SVG figures, final guide PDF and temporary single-figure PDFs under
``tmp/pdfs``. PNG previews can be regenerated with Poppler, for example::

    pdftoppm -r 96 -singlefile -png tmp/pdfs/wiring-panel-controls.pdf hardware/wiring/panel-controls

Refresh ``connector-locations.json`` from the native PCB if its placement,
connector definitions or source hash changes. Verify the printed pad numbers
against the actual connector mating drawings before making harnesses.
