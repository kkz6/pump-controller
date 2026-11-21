# Parts, ratings and cost review

Reviewed 2026-11-21 against the main board with the U42 panel-supply limit, and the panel F board. JLC stock and prices come from the JLCPCB parts library on the same day at quantity 1. Prices marked *est* are JLC's estimate for parts with no stock.

## Result

The design is internally consistent. Every part has a sound rating, and the decoupling is adequate. The blocking problem is supply: about 20 BOM lines have no JLC stock, including the two most expensive parts. As released, the main board can't be ordered for JLC assembly.

## What was checked

| Check | Result |
| --- | --- |
| Schematic BOM, PCB footprints, JLC BOM and placement file | All 240 main and 28 panel parts appear in every file with matching values, footprints, MPNs and sides. |
| Unnamed pads | U2 and U10 have paste-only windows. J40 has its plastic locating pegs. None of these carries copper. |
| Capacitor voltage ratings | Every capacitor is rated at least 2.9× its net voltage. The lowest margin is a 16 V part on a 5.5 V rail. The probe coupling capacitors are 50 V. |
| Decoupling distance | Every IC has a same-net capacitor. The analog, isolator, converter and USB parts are within 1.2–4.8 mm. The slow logic parts U30–U34 are 6–10 mm away, but they sit on the In4 +3V3 plane, so this is acceptable. U2's input and output capacitors are 1.8 mm and 2.3 mm from its power pins. |
| U42 (new) | TI requires ≥0.1 µF at IN, which C243 provides. No output capacitor is required. |
| R2 33 Ω "minimum load" | Not needed. The RECOM RACM06E datasheet gives minimum load as 0%, and says running below 10% load "will not harm the converter". R2 dissipates 0.76 W continuously, and that heat is why the module ambient limit was lowered to 50 °C. |

## Parts that block a JLC order

| Ref | Part | JLC stock | Fix |
| --- | --- | --- | --- |
| U1 | RACM06E-05SK/277 | 0 (est $22.09) | Global sourcing or consign. Alternatives are discussed under larger options. |
| U11 | ADuM6421ABRNZ5 | 0 (est $16.68) | Replaced by Chipanalog CA-IS3641HW (C2890052). See U11 below. |
| U3 | ESP32-C6-MINI-1U-H8 | Not in library | Consign. JLC stocks the -H4 (C20627095, $4.19), but it has 4 MB flash and the bench build uses 8 MB. |
| U32 | STM1001TWX6F | 0 | Alternate source, or a pin-compatible open-drain 3.08 V supervisor. |
| U34 | SN74LVC1G08DBVR | 5 | Nexperia 74LVC1G08GV,125 C282347: same SOT-23-5 pinout, 794 in stock. |
| U37 | SN74LVC3G17DCUR | 5 | Nexperia 74LVC3G17DC,125 C458193, 2992 in stock. Confirm the VSSOP-8 pinout before swapping. |
| Y1 | ABLS-3.579545MHZ-B2-T | 6 | YXC X49SM3579545MSD2SC C2237: same HC-49S SMD package, 20 pF load, 9299 in stock. The existing 27 pF caps then pull it a few ppm high, which doesn't matter for metering. |
| L1 | Würth 74438357022 | 1 ($3.11) | Sunlord SWPA4030S2R2MT C36409: 4×4 mm, $0.058. Confirm saturation current ≥ 1.5 A against TPS62162 peaks. |
| RV1 | TMOV14RP320EL2B7 | 0 | Source the L2B7 lead form elsewhere. Straight-lead TMOV14RP320E (C444866) is in stock, but the footprint notes require the crimped inline L2B7 leads. |
| C1 | EEUFR1E470 | 0 | NXB 25V 47µF 5×11 C371231, 105 °C. |
| C3, C5, C20 | 22 µF 1210 TDK | 0 | Samsung CL32B226KOJNNNE C55530: 16 V X7R 1210. |
| C51–C54 | 33 nF C0G 0805 | 0 | No in-stock 0805 C0G was found. Keep C0G for V/I phase matching: either source this part or move to 1206 (C2443230). |
| 9 × C106–C128 | 1 µF 50 V 0805 | 0 | Samsung CL21B105KBFNNNE C28323, Basic. |
| 8 × C80–C113 | 10 nF 0603 | 0 | C57112, Basic, 50 V. |
| C48, C74, C101, C240 | 1 µF 0603 | 0 | C15849, Basic. This is X5R 50 V, which is adequate for these decoupling and RC positions. |
| C49, C50 | 27 pF C0G | 0 | C107045 NP0. |
| R2 | 33 Ω 2 W | 24 | Remove the part (DNP) and keep the footprint. |
| Panel J2, J7 | SM10B-GHS-TB, S4B-PH-SM4-TB | 0 | Alternate source needed. Both are field-wiring connectors, so the mating housings must stay the same. |

Low stock, but enough for a prototype run: ADE7953 (107), TS3USB30E (151), J20 Phoenix 1803303 (41) and the P6B-04P sockets (10).

## Cost

Both boards carry parts on both sides. JLC's Economic assembly is single-sided, so both boards go through Standard assembly. Standard charges a loading fee of about $1.53 for every unique BOM line, whether the part is Basic or Extended ([JLC assembly pricing](https://jlcpcb.com/help/article/pcb-assembly-price)). Every current part except AO3400A is Extended.

Two levers follow from this:
- **Fewer unique lines:** each removed line saves about $1.53 per order.
- **Cheaper equivalent parts:** pick lower-priced parts with the same footprint.

### Same-footprint changes

None of these needs a layout change.

| Change | Effect |
| --- | --- |
| Remove R2 | One line fewer and 0.76 W less heat. |
| R100 and R101 from 0.1% to 1% 10k | The probe bias is measured on ADS1115 AIN1, so its absolute accuracy doesn't matter. One line fewer. |
| R103 27k → 22k and R104 43k → 33k | Both values are already on the BOM. The probe drive swing moves from 0.64–2.66 V to 0.66–2.64 V. Two lines fewer. |
| C22 1 µF 0805 16 V → the 1 µF 0805 50 V line | One line fewer. |
| Swap the passives to JLC Basic equivalents | Applies to the 0603, 0805 and 1206 resistors, the 100 nF, 10 nF, 1 µF, 4.7 µF and 10 µF capacitors, and 1N4148W. The swaps also fix most of the stock problems above. |
| L1, Y1 and the 4.7 µF 0805 caps | Together the largest per-part savings, about $4.10. |

Main board totals at quantity 1:
- **Parts:** $79.89 → $72.45.
- **BOM lines:** 88 → 83, saving about $7.65 per order in loading fees.

The panel board would get the same treatment: Basic resistors, capacitors and MMBT3904 (C20526).

### Options with trade-offs

| Option | Saves per board | Trade-off |
| --- | --- | --- |
| R43–R46 0.1% thin film → 1% thick film (applied, with R47) | about $3.00 | Divider drift rises from about 25 to 100 ppm/K. The voltage reading is calibrated, but it will drift about 0.4% over 40 K. |
| Merge C2, C4, C6, C21 (100 nF 0805) into the 1 µF 0805 line | One line | None significant: 1 µF X7R decouples at least as well. |
| Merge D102 and D103 BAT54S into the BAS70-04 line | One line | BAS70 has a higher forward voltage and lower surge rating. Acceptable behind the 2.2 k drive resistors. |

### Larger changes for a later revision

These need layout work and safety review, so they belong in a later revision. Get JLC quotes before deciding.

- **AC-DC module:** U1 is about $22 and has no JLC stock. A 5 W, 5 V module certified for reinforced isolation in a different package, such as Mornsun LS05 series, typically costs a fraction of that. It needs a new footprint, a new clearance check, and confirmation of the safety certification.
- **Meter isolation:** U11 is about $17, the single largest IC. Before redesigning, compare the price of an isolated power module plus a reinforced digital isolator. The SELV side is USB-accessible, so the isolation must stay reinforced.
- **Six-layer board:** layer count is usually the biggest fabrication cost on a board this size, so compare a quote for a 4-layer re-layout.
- **Double-sided assembly:** both boards are assembled on both sides. Moving the panel's 19 bottom-side parts to the top would make the panel eligible for Economic assembly.

`manufacturing/costs.json` and the budget in `manufacturing/README.md` were repriced after the changes below were applied. The model is one order of two sets with every fee split evenly, which gives ₹27,278.84 per installed controller. ₹12,945.70 of that is assembly fees.

## Applied

These changes were applied the same day and are carried through the schematic, symbol libraries, `bom.csv`, PCB fields, the parts catalog, `tools/prepare_jlc_assembly.py` and `parts-one-starter.csv`. None of them changes copper. Both boards pass ERC, DRC with schematic parity, the named pin checks and the CAM comparison.

- **R2:** marked DNP. Its footprint is kept.
- **Out-of-stock and low-stock parts:**
  - C1 → C371231
  - C3, C5, C20 → C55530
  - L1 → Sunlord C36409
  - Y1 → YXC C2237, value changed to CL20pF
  - U34 → Nexperia C282347
  - U37 → Nexperia C458193
  - the 1 µF 0805 group → C28323
  - the 10 nF and 1 µF 0603 groups → Basic parts
  - 27 pF and 1 nF → Yageo NP0
- **JLC Basic parts:**
  - all spec-only and Yageo 1% resistors → UNI-ROYAL
  - the 1206 10k group → UNI-ROYAL C17902
  - 1N4148W → C81598
  - the capacitor groups that have a Basic equivalent
  - the panel's resistors, capacitors and MMBT3904 (C20526)
  - the spec text now allows X5R where the substitute is X5R
- **Value changes:**
  - R100 and R101 → 1%
  - R103 27k → 22k
  - R104 43k → 33k

### Still open

These need a decision or another supplier.

- **No JLC stock:** U1, U3 (8 MB) and U32.
- **C51–C54:** the meter's 33 nF C0G caps.
- **RV1:** the footprint needs the crimped L2B7 lead form, so the straight-lead C444866 isn't a drop-in.
- **Panel J2 and J7:** no stock.
- **Low stock:** J20, the ADE7953 and TS3USB30E, and the P6B-04P sockets.

## U1 and U11 replacement findings

Checked 2026-11-21 before any layout work.

- **Mornsun LS05-13B05R3 for U1:**
  - **Pin spacing:** its datasheet puts the input and output pins 6.6 mm apart (6.8 mm with the slot). That is certified for the module itself, but it is below this board's 8 mm mains-to-SELV target. The RECOM has 20 mm between its input and output pins.
  - **External parts:** it needs seven: a 10 µF 450 V bulk capacitor, 470 µF and 100 µF output capacitors, a 4.7 µH inductor, a 100 nF capacitor, a 1 nF Y capacitor across the barrier and an SMBJ7.0A TVS. Its datasheet also asks for extra EMC filtering, where the RECOM has class B filtering built in.
  - **Sourcing:** genuine Mornsun is not in JLC's library. The JLC listings under that part number are YLPTEC and HENIPER parts with unknown certification.
  - **Net saving:** about $17 per board before the extra BOM lines and layout work.
- **RECOM RAC05 family:** no cheaper. It has no JLC stock either, at an estimated $15–37.
- **NSi8241W in place of U11:**
  - **Isolator:** a reinforced 5 kV, wide-body part at $1.86 with 885 in stock. It can keep the 8 mm gap if it uses a pad pattern like the current ADuM6421A dense footprint.
  - **Meter supply:** it needs a separate 3.3 V supply on the mains-referenced meter side. The candidates are a half-wave capacitive dropper (an X2 capacitor, bleeders, a rectifier, a zener and an LDO) or a second small isolated AC-DC module.
  - **Saving:** about $14 per board before about six added BOM lines.

## U11 replaced with CA-IS3641HW

Applied 2026-11-21. Chipanalog CA-IS3641HW (C2890052, $3.00, 7,251 in stock) replaces the ADuM6421ABRNZ5 ($17.32, no stock).

- **What it is:** one part, like the ADuM6421A. It is a reinforced 5 kVrms digital isolator with an integrated isolated DC-DC, 3 forward and 1 reverse channel, and default-high outputs, so the meter's chip select is deselected if the processor side loses power.
- **Supply:** VDD runs from +3V3, which matches the ESP32 logic levels. SEL is tied to GNDB, giving VISO = 3.3 V (up to 130 mA; the meter needs about 10 mA). VISO feeds M_3V3 directly, and GNDB goes to M_GND, as in the datasheet's SPI application circuit.
- **Land pattern:** a new `CA-IS3641_SOIC16W_Dense` footprint keeps the ADuM footprint's 1.3 × 0.6 mm pads at ±4.95 mm, so the inner copper gap stays 8.6 mm. DRC passes the 8 mm LIVE-to-SELV clearance and creepage rules.
- **Support parts:**
  - FB1 and FB2 are now 0 Ω links. The CA-IS36xx is a low-emission part and its application circuit has no ferrites; the 0603 lands can take ferrites again if EMI testing needs them.
  - C58 is now 22 µF. With C46, VISO has about 32 µF against the datasheet's recommended 47 µF.
  - C60 now sits at the VISO and GNDB pins as their 100 nF decoupling.
  - C56 (the old 5 V isolator supply cap) and C59 (VISO decoupling) are removed.
- **Not verified on hardware:**
  - isolated-supply start-up with the meter load
  - SPI timing through the isolator
  - EMI with the ferrites shorted
  - the land pattern, which should be reviewed with the assembler
  - +3V3 decoupling: the datasheet shows 10–22 µF at VDD, but only C57 (100 nF) is local. The supply relies on the +3V3 plane and the bulk capacitors elsewhere on the rail.
- **Saving:** about $14.30 per board. Main-board parts go from $81.21 to $66.87.
