U37 manufacturer-derived footprint
===================================

SN74LVC3G17DCUR uses TI DCU0008A, drawing 4225266/A (09/2014).
The manufacturer example layout on PDF page 25 was visually checked on
19 November 2026: eight 0.85 x 0.30 mm lands, 0.50 mm pitch and 3.10 mm row
spacing, with pin 1 upper left and pin 4 lower left. It matches the existing
U31 custom geometry. ``PumpRevE:SN74LVC3G17_DCU_TI`` is a part-specific copy
with identical pad geometry. The cached copy uses the same fabrication-layer
and text policy as the cached U31 footprint. Native load and all eight pad
coordinates/sizes were compared; no electrical pin-number substitution is
implied by footprint reuse.

Primary source:
https://www.ti.com/lit/ds/symlink/sn74lvc3g17.pdf

Electrical caveat: the documented Ioff limits apply at VCC=0. They do not
establish defined output logic through the 0..1.65 V supply-ramp interval.
Keep input excursions within the recommended 5.5 V limit and verify rail
sequencing and downstream inhibition on the assembled board.
