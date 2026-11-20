# JLCPCB procurement for main R4 and panel F

The order covers **one installed DOL starter and one shelf-spare board set**. Factory-assemble two main R4 boards and two panel F boards, with all specified components, including all five buttons on each panel. The installed unit gets one plug-in OLED, one CT harness and one set of cabinet equipment and cables. The shelf spare consists of the populated main board and populated button panel. It uses the installed accessories when exchanged. For each design, quote five bare PCBs where fabrication requires five, with assembly on two. Specify Standard, both-side assembly including all fitted surface-mount and through-hole components. Any spare bare boards are separate from the four assembled boards requested.

Size component quantities to fill every position on both sets. The preference for small lots of two on parts at or above US$1 and five below US$1 applies only where it permits a complete build. Show unavoidable supplier minimums and assembly losses separately. Exclude discretionary extras from the estimate.

The installed starter is being considered for a lower-cost cabinet that relies on an operator pressing the original red STOP after a controller failure. Defer purchase of the external guard equipment during this review. The listed R4 assembly and its guard form a matched reference design. [Manual-stop design target and cost impact](parts-cost-review.md#manual-stop-design-target)

| Design | PCB fabrication upload | Assembly uploads | Board specification |
|---|---|---|---|
| Integrated main R4 | [Main Gerber ZIP](../../hardware/main-integrated/pump-controller-integrated-r4-gerber-prototype.zip) | [BOM](main-BOM.csv) · [Placement file](main-CPL.csv) | 100 × 115.5 mm, six layers, 1.6 mm Tg155 FR-4 or confirmed equivalent, 1 oz outer/0.5 oz inner copper, green mask, white legend, ENIG |
| OLED/button panel F | [Panel Gerber ZIP](../../hardware/panel-rev-f/pump-panel-rev-f-gerber-prototype.zip) | [BOM](panel-BOM.csv) · [Placement file](panel-CPL.csv) | 60 × 45 mm, two layers, 1.6 mm FR-4, 1 oz copper |

The BOM and placement files describe one board. Two main boards require 544 component placements and two panels require 48, for **592 placements**. For example, GRM188R71C104KA01D is used at 20 positions on the main and one on the panel, requiring 42 for two complete sets. Obtain approval for exact part, stock and orientation before release. Keep all required positions populated.

A catalog estimate prices 580 of the required 592 pieces at **US$171.69**. Five exact manufacturer part numbers, covering the other 12 pieces, still need quotes. Assembly, extra procurement quantities, freight, taxes and items installed outside the PCBs are additional. [Two-set component quantities and prices](component-quantity-plan.csv) · [Cabinet purchases for one starter](cabinet-one-starter.csv) · [Field purchases for one starter](field-one-starter.csv)

For prices at actual purchase quantities, alternatives from JLC Global Sourcing and the domestic cabinet parts, see the [cost and availability comparison](parts-cost-review.md) and the [complete parts index](complete-parts-index.csv).

## Supplier matching

The two signed-in assembly drafts specify **two assembled boards per design**. JLCPCB matched the uploaded bills and placements as shown below. The [two-set supplier matches](two-set-assembly-matches.csv) contain current per-part shortfalls. The [original five-board comparison](assembly-quote-matches.csv) is retained for reference.

| Design | Exact and available | Inventory shortage | Unmatched | Automatic substitute pending review |
|---|---:|---:|---:|---:|
| Main R4 | 81 | 16 | 4 | 1 |
| Panel F | 12 | 1 | 0 | 0 |

Main F1 (fuse), J1 (mains terminal), U3 (radio module) and U301 (guard comparator) had no match. JLC suggested Samsung CL21B103KBANNNC for Murata GRM21BR71H103KA01L at C303/C304. That suggestion is deselected. Panel J2 matched its specified JST connector but lacked stock for the quoted quantity. Other shortages include the main isolated supply and metering isolator. Review exact MPNs, supplier packaging, polarity, pin 1, connector direction and through-hole assembly before release. [Critical sourcing notes](critical-parts-sourcing.md) · [Assembly exceptions](assembly-exceptions.csv) · [Catalog snapshot](jlc-parts-verified.csv)

JLCPCB acknowledged a nonbinding assembly inquiry on 20 November 2026 covering all **22 unresolved part numbers** and their **102 fitted pieces**. The inquiry requests factory fitting of all required surface-mount and through-hole parts, details of any assembly exceptions, separate pricing for the OLED and terminated cable, and a delivered quote. Supplier pricing and production approval are pending. [Exact items submitted](exact-parts-rfq.csv) · [Supplier minimums and indicative prices](sourcing-minimums.csv)

## Fabrication and installation

Use the four-probe cabinet reference for the installed unit. J20 takes the existing tank common and four probes in ascending order. The highest probe supplies the normal FULL signal. A per-run time limit provides a second software stop condition. Both depend on a functioning controller and apply in HOST, including controller-commanded manual runs. Physical LOCAL gives control back to the factory starter. A broken FULL lead can look like a tank below FULL and the tank can overflow before the timer expires. The standalone LS1 float has a purchase quantity of zero. [Four-probe cabinet reference and test scope](../../hardware/starter-guard-r4-probes/README.rst)

- **Mains isolation and USB-C.** Have JLC confirm the six-layer stackup, the finished 8.00 mm isolation boundaries identified in the manufacturing notes, and the 3.20 mm incoming line-to-neutral gap. Ask them to retain the USB-C J40 land relief and confirm both locator holes at **0.65 ±0.05 mm finished**, including their position. Request bare-board electrical testing against the supplied IPC-D-356 netlists. [Main manufacturing requirements](../../hardware/main-integrated/README.rst)
- **Independent shutdown.** The four-probe cabinet retains the original starter STOP with its mechanically linked NC contact, overload, two external power contactors and trapped-key motor isolator/USB shutter. Prove the STOP and overload trip in both HOST and LOCAL on the actual starter, and verify the USB access interlock. The probe and timer functions also require application integration and a witnessed fill test before unattended operation. [Selected cabinet reference](../../hardware/starter-guard-r4-probes/README.rst)
- **Off-board purchasing.** The Waveshare 14657 OLED, Talema AC1020 with its fitted burden, antenna, looms, cabinet guard and installation hardware are separate purchases. Use one field kit and one cabinet bill for the installed starter. Check the retained OEM equipment before ordering model-specific accessories. [Field kit](field-one-starter.csv) · [Cabinet bill](cabinet-one-starter.csv)
