# Cost and availability for one installed starter and one spare board set

Prices checked on 20 November 2026. One set runs the existing DOL starter. The second is a shelf spare. The factory build consists of **two R4 main boards and two F button panels**. The single installed kit includes one plug-in display, one CT harness, one high-high float and one cabinet assembly. Together they have 592 fitted positions across 110 unique manufacturer part numbers. The installation inventory separately lists 60 lines, including assemblies, retained equipment, optional controls and hardware selected for the actual starter. [All 170 purchasing lines](complete-parts-index.csv) · [Board quantities](component-quantity-plan.csv) · [Installation quantities and applicability](offboard-parts.csv)

## Board components

| Scope | Quantity covered | USD | Meaning |
|---|---:|---:|---|
| Parts selected on the two JLC assembly drafts | 490 fitted pieces, 88 unique part numbers | 102.06 | Supplier-priced quantities include extra pieces for assembly. Main components account for $93.6730 and panel components $8.3849. |
| Conventional JLC preorder preview for 17 additional exact parts | 90 fitted pieces, 3,162 pieces across the displayed purchase lots | 218.42 | Indicative sourcing spend if those entire lots are required. |
| Selected parts plus these 17 preorder lots | 580 fitted pieces, 105 unique part numbers | 320.47 | Two disjoint groups added before rounding. Five further part numbers remain outside this scenario. |
| Reference catalog value for the same 580 fitted pieces | 105 unique part numbers | 171.69 | Multiplies only the fitted count by catalog price, without supplier purchase minima or assembly losses. |

Board fabrication, factory setup, feeder loading, soldering, tests, freight, tax and field equipment are additional. Both assemblies are double-sided and contain through-hole parts. JLC publishes $51.12 setup and $16.42 stencil per Standard double-sided design, or $135.08 across the two designs at published rates. The final factory quote determines fees. [Prices on the two assembly drafts](factory-parts-pricing.csv) · [Preorder lots](sourcing-minimums.csv) · [JLC assembly pricing](https://jlcpcb.com/help/article/pcb-assembly-price)

J40 on the main board matched the correct GCT USB4110-GF-A but initially showed zero pieces. The updated draft includes **two USB-C sockets for $2.7960**. The auto-suggested Samsung capacitor at C303/C304 is deselected. The 22 original outstanding part numbers are covered by the existing exact-parts inquiry. [Factory selections](factory-parts-pricing.csv) · [Original sourcing request](exact-parts-rfq.csv)

## Lower prices for the specified board parts

JLC’s Global Sourcing marketplace showed cheaper component lots on 11 lines. Ten exact part-number spellings reduce the comparison by $64.39. The eleventh is Panasonic EEU-FR1E470, which the supplier also identifies as EEUFR1E470. Including this alias brings the potential saving to **$71.15** and the 105-part-number scenario to **$249.32** before warehouse charges, assembly and delivery. Lot size and stock can change. The quote request asks the factory to confirm its quantities for complete assembly. [Supplier offers and lead times for all 22 outstanding numbers](board-sourcing-comparison.csv) · [JLC Global Sourcing terms](https://jlcpcb.com/help/article/how-to-use-jlcpcb-global-sourcing-parts-service)

| Part | Two-set comparison in USD | Sourcing decision |
|---|---:|---|
| RECOM RACM06E-05SK/277 isolated supply | $36.37 for two via Mouser through JLC, versus $45.88 conventional preorder | Global Sourcing showed 1,350 available and 10–20 business days. |
| Würth 74438357022 power inductor | $3.88 for two via RS through JLC, versus $9.69 for three | Global Sourcing showed 59 available and 8–16 business days. |
| ADUM6421ABRNZ5 metering isolator | $34.65 for two on conventional preorder, versus $61.55 via Global Sourcing | The lower conventional price is provisional. Final price and availability are pending. |

Mouser India lists the exact Bel fuse at ₹188.22 each. The factory marketplace has a conflicting manufacturer label for that SKU. For the METZ terminal the integrated route displayed a 485-piece lot for a two-piece need. The exact Espressif radio, Murata C303/C304 and named TI comparator still need resolution. TI lists LM393BIDR as an active SOIC-8 ordering code. Its use in the guard circuit requires review. [Full source and identity checks](board-sourcing-comparison.csv) · [TI part record](https://www.ti.com/product/LM393B/part-details/LM393BIDR)

## Capacitor options for engineering review

Three original Murata capacitor lines have conventional JLC preorder lots costing $27.0817 combined. JLC lists three same-footprint Yageo candidates in stock. At the catalog price the 28 pieces fitted across both sets would total $0.1660 before placement allowance and fees. This is a comparison of supplier minimum lots with net material. The exact-part inquiry may produce a cheaper route using the original parts. Check the crystal load, effective capacitance, reset timing and analogue filters at the applicable operating conditions before any BOM revision. The current build uses the original specifications. [Candidate parts, datasheets, stock and price](capacitor-options-for-review.csv)

## Cabinet and field equipment for the installed starter

One cabinet includes both specified motor isolation contactors, both Pilz safety relays, the ifm monitor, the independent high-high float and the original starter STOP interface. The shelf spare reuses this equipment when installed. A cabinet quantity of one still requires every device in its safety circuit. [Cabinet items and purchasing conditions](cabinet-one-starter.csv)

| Active purchase scope | Partial catalog amount | Coverage |
|---|---:|---|
| Common cabinet hardware for one starter | **₹2,01,757.50** | 15 priced INR lines. Includes two Pilz 750104 relays, one ifm DD2503, three forced-guided relays and two motor isolation contactors. Stock and tax treatment vary by supplier. |
| Independent high-high float | **US$114.00** | One SJE 1062686 at the overseas reference price, before delivery. |
| Field materials for one starter | **₹2,398.33** | Nine priced material lines with the local-only external-button plug. Includes one Waveshare 14657 OLED at ₹513.30 and one Talema AC1020 CT body at ₹611.52. The installed set uses one of each. |

The smaller quantities change some supplier price breaks. The three Omron G7SA-2A2B DC24 relays use the ₹4,982.07 unit tier. The previous two-cabinet basket qualified for the ₹4,859.36 tier at five or more. One starter reduces the same 15 priced cabinet lines by **₹2,01,021.24**. A domestic seller also advertises the same relay at ₹1,999 before GST, subject to quantity, traceability and delivery confirmation. [Single-starter cabinet pricing](cabinet-one-starter.csv) · [Distributor tiers](https://in.element14.com/omron-sti/g7sa-2a2b-dc24/relay-safety-2no-nc-250vac-6a/dp/1221753) · [Domestic offer](https://www.industrybuying.com/safety-relay-omron-IND.OMR.93892282)

The field subtotal includes material for the leads. The CT burden and completed harness, finished panel cables, cabinet mechanics and installation labor still need prices. The 254 mm stock-lead combination requires verification against the 250 mm bus target. Optional remote buttons and the key-switch loom depend on the fitted controls. The spare panel is fully populated with its buttons and socket and can use the installed plug-in OLED and cabling. [Single-starter field pricing](field-one-starter.csv)

The remaining installation selections include the original starter’s linked auxiliary contacts, the matched transfer and trapped-key hardware, a DC-rated cabinet fuse/holder combination, the antenna and the enclosure dimensions. Existing motor gear and probes can be reused after checking compatibility. A complete delivered price requires the exact-part factory reply and the site-specific cabinet selections. The lower-priced sourcing routes and proposed capacitor changes have no purchase or production commitment.
