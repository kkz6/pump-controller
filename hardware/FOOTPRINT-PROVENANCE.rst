Footprint sources and review status
==================================

The standard footprints in ``libraries/`` are copied without geometry changes
from the official KiCad 10.0.8 macOS distribution (KiCad community authors).
The exact names and SHA-256 hashes are recorded in ``libraries/manifest.json``.
Upstream project: https://gitlab.com/kicad/libraries/kicad-footprints
License: Creative Commons Attribution-ShareAlike 4.0 with the KiCad library
exception; the upstream notice is retained in ``KICAD-LIBRARY-LICENSE.md``.
The same terms apply to redistributed standard-library collections and the
modified library footprints identified below. The electronic design itself
benefits from the exception stated in that notice.

Project-specific ``Pump.pretty`` footprints:

* ``Relay_G5Q_8mm`` derives from KiCad
  ``Relay_THT:Relay_SPST_Omron-G5Q-1A``. Copper pad diameter is changed from
  2.3 mm to 2.1 mm; 1.3 mm holes are retained. The resulting 0.4 mm annulus
  and nominal 8.06 mm closest coil/contact copper gap require fabrication
  and manufacturer land-pattern review before release.
* ``ADuM6421A_RN28`` is a project-created, datasheet-derived footprint:
  0.65 mm pitch, 1.3 x 0.4 mm pads at x=+/-4.95 mm, nominal 8.6 mm
  inner pad-edge gap. It is not a manufacturer-approved land pattern.
* ``RACM06E``, ``ESP32-C6-MINI-1U``, ``Fuse_Axial_5x20_P27.94``,
  ``R_Axial_L13_D6_P20.32`` and ``TMOV14_Inline_P7.5`` are project-created
  footprints derived from the component datasheets identified in the BOM.
  Confirm package variant, pin numbering, lead tolerance and recommended
  land patterns against purchase samples before manufacture.

No standard-library 3D models are redistributed in this package. Optional
model paths resolve against an installed KiCad standard 3D-model library.
