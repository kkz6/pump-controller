# Order checklist — R4 prototype

This list is for two complete controllers. That is the JLCPCB assembly minimum. JLC makes five bare boards of each design and assembles two of each.

Quantities in the tables are for **two sets**. Stock was checked on the JLCPCB/LCSC parts library on 2026-11-21. Re-check stock on the day you order.

The enclosure, the USB cable, board standoffs and the panel front are left for later. They are not needed to get a working board on the bench.

## 1. JLCPCB — boards and assembly

| Board | Upload | Options |
| --- | --- | --- |
| Main R4, 100 × 118.5 mm | [Gerbers](main-gerbers.zip) · [BOM](main-BOM.csv) · [Placement](main-CPL.csv) | 6 layers, FR-4 1.6 mm, 1 oz outer copper, 5 pcs. **Standard PCBA, both sides**, 2 boards. 226 placements on 63 BOM lines, with relays and output terminals factory-fitted. Confirm the new relay reservation/lead time. |
| OLED panel F, 60 × 45 mm | [Gerbers](panel-gerbers.zip) · [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv) | 2 layers, FR-4 1.6 mm, 5 pcs. **Economic PCBA, bottom side only**, 2 boards. 19 parts on 11 lines. |

Check the layer count, size and part placement on JLC's preview before paying. R4 is 20.5 mm shorter than R3. All four corner mounting holes moved to suit the compact outline. Relay outputs face out of the bottom edge; tank and inlet ports face out of the top edge. Relays are G5RL-1-E-HR DC5 / C1563288 (4 pieces for two boards); terminal blocks are 1711738 / C91156 (4 pieces). The old two-position output plugs are obsolete.

### Rotation corrections made in JLC's placement viewer (order of 2026-11-21)

JLC's library models for these parts are rotated against KiCad's footprints. With the uploaded `main-CPL.csv`, they would be soldered sideways or back to front. Each one was corrected in the viewer by checking JLC's pin-1 dot against the silkscreen pin-1 mark and the copper pads. The saved order carries the corrections. R4 retains all 21 exact-part corrections automatically in `tools/prepare_jlc_assembly.py`, using `tools/data/jlc-placement-corrections.json`. Do not apply this table a second time to the revised CPL. The native footprints and pads retain their physical orientation; these are supplier-library angle offsets. Reconfirm the revised DFM preview, particularly the new relay and transistor models.

| Side | Parts | Correction in the viewer |
| --- | --- | --- |
| Top | U21, U22, U33, U41, D42 | Rotate right (clockwise) 90° |
| Top | U40, Q30, Q31, Q40 | 180° |
| Bottom (viewed from below) | U11, U20, U34 | Rotate left (anticlockwise) 90° |
| Bottom | U10, U31, U37, U42, D10, D31, D32, D43, D113 | 180° |

All other parts matched as uploaded. D40, D60 and D61 have no model in JLC's viewer, so the order remark asks JLC to check their polarity: the cathode is pad 1, on the side with the silkscreen bracket. The panel needed no corrections. Its single-row connectors only need their leads on the pads and their openings facing the board edge.

The panel uses Economic PCBA, which does not accept OSP finish, so the panel is ordered with lead-free HASL.

### Assembly tooling and stencil

For the main board's Standard PCBA, select **Edge Rails/Fiducials: Added by JLCPCB** and have JLC provide suitable tooling holes. The supplied Gerbers describe the finished 100 × 118.5 mm board, not a manufacturing panel. Request at least 5 mm process rails and ask JLC to keep panel tabs/rails clear of the outward-facing J30/J35 bodies, USB-C J40 and the other edge connectors. Confirm the panel/depaneling arrangement in the engineering preview. These corner mounting holes are for nylon enclosure hardware, not a substitute for assembly fiducials.

Use the supplied paste layers as the stencil basis. Main-board minimum paste aperture width is 0.25 mm; a 0.12 mm stencil gives a minimum rectangular area-ratio screening estimate of 0.735. Have JLC finalize stencil thickness/aperture treatment for the exact process, including the exposed pads at U2 and U10. Do not add paste to the through-hole-only components or DNP R2. R246's supply via is now outside its solder land, avoiding an unfilled via beneath that paste aperture.

References: [JLC assembly tooling](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order), [JLC assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service), [via-in-pad guidance](https://jlcpcb.com/help/article/via-in-pad-pofv-guide).

## 2. Hand-soldered parts — LCSC (can ship with the JLC order)

These parts are left out of the JLC assembly files on purpose. Solder them after the boards arrive.

| Board | Ref | Part | LCSC | Qty (2 sets) |
| --- | --- | --- | --- | ---: |
| Main | C1 | SamYoung NXB 47 µF 25 V | C371231 | 2 |
| Main | J1 | Kefa KF128-7.5-2P mains terminal | C474954 | 2 |
| Main | J2 | Samtec TSW-103-07-G-D service header | C6339671 | 2 |
| Main | J10 | Phoenix 1727010 CT terminal | C89123 | 2 |
| Main | J20 | Phoenix 1803303 tank-probe header | C480548 | 2 |
| Main | J21 | JST S2B-XH-A inlet header | C157931 | 2 |
| Main | J41 | JST B3B-XH-A RUN/BENCH header | C144394 | 2 |
| Main | R1 | 22 Ω 3 W fusible resistor | C1364992 | 2 |
| Main | RV1 | Littelfuse TMOV14RP320EL2T7 | C22815876 | 2. Only 3 in stock; buy both at once. |
| Panel | SW1 | Omron D2F-01F STOP switch | C403989 | 2 |
| Panel | SW2–SW5 | Omron B3U-1000P buttons | C231329 | 8 |

## 3. Hand-soldered parts — DigiKey (not stocked at LCSC)

| Board | Ref | Part | Qty (2 sets) |
| --- | --- | --- | ---: |
| Main | U1 | RECOM RACM06E-05SK/277 AC-DC 5 V module (945-RACM06E-05SK/277-ND, about $10) | 2 |
| Main | F1 | Bel Fuse 0ADKP1000-RE, T1A 5×20 mm axial fuse | 4 (2 spare) |

## 4. Cables and plugs — needed for a working controller

| Item | Parts | Source | Qty (2 sets) |
| --- | --- | --- | ---: |
| **Panel loom** (main J32 to panel J1), 12-way JST GH, about 150 mm, wired pin 1→1 … 12→12 | 2× GHR-12V-S housing (LCSC C489720) + 12× JST AGHGH28K152 pre-crimped lead | Housings: LCSC. Leads: DigiKey. | 2 looms |
| **OLED cable** (panel J7), 4-way JST PH, about 100 mm. Pin order: 1 SCL, 2 SDA, 3 GND, 4 +3.3 V | 2× PHR-4 (LCSC C111514) + 4× JST ASPHSPH24K102 pre-crimped lead | LCSC + DigiKey | 2 cables |
| **STOP loop plug** (panel J2), needed when no remote button station is fitted. Without it STOP reads as pressed and the pump never runs. | 1× GHR-10V-S (LCSC C485359) + 1× AGHGH28K51 lead, looped from cavity 3 to cavity 4 only | LCSC + DigiKey | 2 |
| **Starter output wiring** (J30, J35) | Fixed Phoenix 1711738 screw terminals, included in main PCBA. Each block: 1 NO, 2 COM, 3 NC. Use identified wires/ferrules; no mating plugs. | JLC assembly | 4 terminal blocks already in BOM |
| **Tank probe plug** (J20) | Phoenix 1803604 (LCSC C480513) | LCSC | 2 |
| **Inlet probe plug** (J21) | JST XHP-2 + SXH crimps or a pre-crimped XH lead | LCSC / DigiKey | 2 |
| **RUN plug** (J41), links pins 1–2 for normal running | JST XHP-3 (LCSC C144402) + 1 pre-crimped XH lead | LCSC / DigiKey | 2 |

GH and PH crimps are very small. Pre-crimped leads only need to be pushed into the housing, so no crimp tool is required.

## 5. Field parts

| Item | Part | Source | Qty |
| --- | --- | --- | ---: |
| OLED display | Waveshare 14657 | Hubtronics, about ₹513 | 2 |
| Current transformer | Talema AC1020, 20 A, 1000:1 | DigiKey, about ₹612 | 2 |
| CT burden RB1 | 6.8 Ω, 1 %, ≥0.25 W metal film, soldered across the CT leads. Firmware calibration removes the tolerance. | Any | 2 |
| Antenna | Flat flexible 2.4 GHz antenna with a U.FL (IPEX MHF1) plug, for example Molex 146153-0100 (100 mm cable). Stick it inside the plastic lid, away from relays, mains wiring and metal. | Mouser / DigiKey | 2 |

## 6. Programming (once per bench)

- A USB-C **data** cable.
- An isolated, regulated 5 V supply (≤5.5 V) wired to an XHP-3 bench plug: pin 2 +5 V, pin 3 GND, pin 1 empty.

See [programming](../docs/programming.md).

## Later

- Enclosure with cable glands
- Nylon standoffs: 5× M3 for the main board, 4× M2.5 for the panel
- Panel front: OLED window and button caps
- Optional AUTO/MANUAL key switch with a GHR-03V-S plug
