Rev E capacitor sourcing and installed-envelope review
======================================================

Reviewed 19 November 2026. These are exact prototype sourcing candidates;
neither purchased-lot performance nor the assembled supply has been tested.
Do not substitute a generic capacitance/voltage match without repeating this
review. The PCB package remains a bare-board engineering prototype.

C1: Panasonic EEUFR1E470, straight leads
---------------------------------------

Select the unsuffixed bulk part ``EEUFR1E470``: 47 uF, 25 V, +/-20%,
-40..105 C. The FR-A catalogue lists 5000 h endurance, 280 mA ripple at
100 kHz/105 C and maximum 0.300 ohm impedance at 100 kHz/20 C. The product
web table's impedance unit is inconsistent; the catalogue's ohm unit controls.
Nominal body is 5 x 11 mm, but its tolerances allow diameter 5.5 mm and length
12.5 mm. Straight leads are 0.50 +/-0.05 mm diameter and 2.0 +/-0.5 mm pitch.
Do not order B/H formed-lead variants, whose pitches differ. [1, 2]

The native C1 is on B.Cu, centred at approximately (57.5,26) mm. The retained
footprint is ``PumpRevE:CP_Radial_D5_P2_Pads1p5`` with existing 0.8 mm drills,
1.5 mm pads and 2 mm pitch. Lead fit must be checked with the finished hole;
the nominal drill is not a guaranteed finished-hole diameter. Seat without
forcing leads or damaging the seal; control the can-to-board gap to at most
1 mm and trim leads to at most 3 mm above the opposite board face.

The conservative model uses a 6 x 6 mm XY box (maximum can plus 0.25 mm
installation allowance per side), extending 13.5 mm below the rear mounting
face. A 6.5 mm square courtyard adds 0.25 mm per side. A temporary native
board check found no same-side courtyard overlaps. C22 is the nearest
existing courtyard: the installed body box has approximately 0.275 mm X
clearance; final native DRC and model interference checks must be repeated
after routing. This result does not establish a soldering-process tolerance.

The old 12 mm mounting gap is insufficient. Use 18 mm insulating main-board
standoffs; the enclosure is now 170 x 150 x 90 mm with a raised guard. The
13.5 mm installed body plus the exported PCB surface offset is rounded to
a 13.6 mm underside model allowance, leaving 4.4 mm nominal space to the
floor. A DOL retrofit needs the same rear clearance and a separately verified
front guard/wiring envelope. Do not reuse the old generic 7 mm-high C1 model as fit evidence.

``tools/patch_main_rev_e_c1.py`` updates only C1's courtyard/model reference
in a caller-selected board. It preserves pad UUIDs, pad/drill sizes, positions,
nets and all routing outside that footprint. Source/BOM fields are separate.

C3 and C5: TDK C3225X7R1C226M250AC
-----------------------------------

Use this exact 22 uF, 16 V, +/-20%, X7R, 1210 candidate for both positions;
C5's voltage rating increases from the generic 10 V entry. It is listed as
Production; the +/-10% ``...K250AC`` alternative is NRND. Maximum body is
3.6 x 2.8 x 2.8 mm. The parts fit the existing package class, but assembler
land/paste-process review and purchased-part inspection remain necessary. [3]

TDK's characterization shows approximately 7% loss at 5 V and 3..5% loss
around 3..4 V. These are reference curves, explicitly not guaranteed product
characteristics. They support a prototype choice, not a production minimum
capacitance guarantee. [3, 4]

For screening, use deliberately larger bias-loss allowances: 15% for C3 at
up to 5.5 V and 10% for C5 at up to 3.432 V. Combining the nominal value with
20% tolerance, 15% temperature allowance and a further 10% engineering aging
reserve gives these estimates::

  C3: 22 x 0.80 x 0.85 x 0.85 x 0.90 = 11.44 uF
  C5: 22 x 0.80 x 0.85 x 0.90 x 0.90 = 12.12 uF

Those allowances are engineering assumptions, not TDK guaranteed combined
temperature/bias/aging limits. C3's acceptance target remains at least 10 uF
effective. For C5, retain the 22 uF nominal design and use at least 11 uF
effective as the prototype screening target for the selected 2.2 uH filter;
this follows TI's nominal22/effective11 comparison, not a universal stability
limit. TI recommends evaluating capacitance and inductance together and
checking application-specific stability/transient behavior. Include all other
3V3 capacitors and the real radio/load wiring in that test. [5, 6]

Outstanding purchasing and bench gates
--------------------------------------

* Confirm authentic exact MPNs and manufacturer lot specifications, including
  combined DC bias/temperature behavior and aging. A zero-bias LCR reading
  alone does not close the C3/C5 requirement.
* Measure sample capacitance with a suitable DC-bias fixture at the actual
  rail limits and declared temperatures; use manufacturer measurement and
  conditioning procedures. Confirm C3 >=10 uF and C5 >=11 uF with the
  measurement uncertainty included, or obtain guaranteed supplier limits.
* Verify the C1 can/lead envelope and controlled mounting gap, electrolyte
  temperature, ripple stress, startup, relay switching and buck load steps.
  Retain the NOT RUN status in the bench acceptance plan until measured.

Primary sources
----------------

[1] Panasonic product page:
https://na.industrial.panasonic.com/products/capacitors/aluminum-electrolytic-capacitors/lineup/aluminum-electrolytic-capacitors-radial-lead-type/series/83367/model/83711

[2] Panasonic catalogue 2025.9, FR-A dimensions p15, impedance p16 and part p19:
https://industry.panasonic.eu/storage/imported/industrial.panasonic.com/cdbs/www-data/pdf/RDF0000/ast-ind-152839.pdf

[3] TDK current product/status/specification:
https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3225X7R1C226M250AC

[4] TDK characterization sheet, 4 January 2016:
https://product.tdk.com/info/en/documents/chara_sheet/c3225x7r1c226m250ac.pdf

[5] TI TPS6216x data sheet, recommended filter/capacitor selection:
https://www.ti.com/lit/ds/symlink/tps62160.pdf

[6] TI SLVA463A, effective-capacitance filter comparison and application limits:
https://www.ti.com/lit/an/slva463a/slva463a.pdf
