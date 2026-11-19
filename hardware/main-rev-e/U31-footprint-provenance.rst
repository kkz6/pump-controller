U31 manufacturer-derived footprint
==================================

Part: Texas Instruments SN74LVC1G74DCUR, package DCU0008A.
Library identifier: ``PumpRevE:SN74LVC1G74_DCU_TI``.
Reviewed 19 November 2026.

Primary source
--------------

https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf

The visually checked package outline and example board layout are PDF pages
22 and 23, respectively, drawing 4225266/A (09/2014). The downloaded PDF SHA-256
was ``e46a5a867fec742290000dca5ed3b291535f3c4418ef2ae267acc4ab51b26d8a``. Page numbering can change if TI revises the document;
the drawing identifier is the controlling reference.

Land pattern and numbering
--------------------------

* Eight copper lands: 0.85 mm along X by 0.30 mm along Y.
* Row centre coordinates: X = -1.55 mm and +1.55 mm, separation 3.10 mm.
* Pitch: 0.50 mm; Y centres -0.75, -0.25, +0.25, +0.75 mm.
* Corner radius: 0.05 mm, encoded as a one-sixth short-side ratio.
* Pin 1 is upper left, 4 lower left, 5 lower right, and 8 upper right when
  viewed from the component side. No electrical pin-number changes are made.
* Non-solder-mask-defined pads, with 0.05 mm mask expansion on each edge,
  follow TI's preferred example. Adjacent copper gap is 0.20 mm and nominal
  solder-mask web is 0.10 mm. No footprint-level mask-bridge exception is used.
* Paste is 1:1 with the copper lands: zero absolute and ratio reduction.
  Stencil thickness and assembly process remain assembler-controlled.
* There are no drilled holes or exposed-pad lands in this package.

Mechanical presentation
-----------------------

The fabrication outline is the nominal 2.30 x 2.00 mm body, with a pin-1 chamfer.
The rectangular courtyard is 4.50 x 2.90 mm. It includes the copper lands and
allows at least 0.25 mm beyond the TI maximum body plus its stated 0.15 mm per
side mould-flash allowance. Silkscreen strokes are 0.16 mm and reference text
is 1.0 mm high; the pin-1 circle and top/bottom lines clear mask openings by at
least 0.17 mm. The reference field may need relocation for final board placement.

The stock KiCad ``VSSOP-8_2.3x2mm_P0.5mm.step`` model is retained for nominal
package-body visualization with unit scale and zero offset/rotation. Its model
name does not define this footprint's land sizes. Enclosure and assembly fit
must use the component drawing and final populated-board dimensions.

Integration requirements
------------------------

Replacing the old U31 footprint must preserve each pad number, net, board side,
centre and orientation. Its row centres move outward by 0.15 mm compared with
the previous KiCad library land pattern, so every adjoining route must be
reconnected and the final board checked for connectivity, clearances, mask
webs and courtyard conflicts. A footprint review does not constitute a final
board manufacturing or mains-product qualification.
