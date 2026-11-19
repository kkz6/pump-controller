# Cost and availability for two factory-assembled controller sets

Prices checked on 20 November 2026. The factory build consists of **two R4 main boards and two F button panels**. Together they have 592 fitted positions across 110 unique manufacturer part numbers. The installation inventory separately lists 60 lines, including assemblies, retained equipment, optional controls and hardware selected for the actual starter. [All 170 purchasing lines](complete-parts-index.csv) · [Board quantities](component-quantity-plan.csv) · [Installation quantities and applicability](offboard-two-installations.csv)

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

## Cabinet and field equipment

For **two complete installations**, 15 common cabinet line items with INR extensions add to **₹4,02,778.74**, and two specified high-high floats have an overseas price of **US$228**. This is a partial reference basket at the listed suppliers’ prices. Some include taxes and others quote before GST. The basket includes an unconfirmed price for the ifm monitor and the price of a fuse awaiting DC interruption evidence. It excludes site-specific items, freight, unpriced accessories and assembly labor. [All 43 cabinet line items with price, stock, tax and alternatives](cabinet-sourcing.csv)

- Four Pilz 750104 safety relays are ₹1,49,783.92 before GST at element14. TME showed 12 units at US$266.98 each, or US$1,067.92 for four before currency conversion, freight and taxes. [element14 India](https://in.element14.com/pilz/750104/relay-safety-3pst-no-240vac-6a/dp/1704486) · [TME India](https://www.tme.com/in/en/details/pz-750104/safety-switches-control-modules/pilz/750104/)
- RS lists the ifm DD2503 monitor at ₹57,892.25 each before GST with unconfirmed stock. DigiKey India showed ₹42,806.40 each and zero stock. A lower price helps the budget only if the supplier can deliver. [RS India](https://in.rsdelivers.com/product/ifm-electronic/dd2503/ifm-electronic-monitoring-relay-din-rail-110v-ac-v/0100123) · [DigiKey India](https://www.digikey.in/en/products/detail/ifm-efector-inc/DD2503/12145362)
- The reference basket includes six Omron G7SA-2A2B DC24 relays at ₹29,156.16. An Indian seller advertises ₹1,999 each before GST, or ₹11,994 for six. Confirm stock for six, lead time and manufacturer traceability before counting that difference. [Domestic offer](https://www.industrybuying.com/safety-relay-omron-IND.OMR.93892282)
- For installations sharing one physical starter, one fitted cabinet, commissioned safety chain, float and CT can serve a replacement board set. Two independently running starters each need their own commissioned shutdown hardware. The parts index includes per-installation quantities for comparing these cases. [Installation quantities](offboard-two-installations.csv)

Nine field-material lines total **₹4,796.67** for two installations on the local-only external-button option. These include both displays and CT bodies and indicative loom materials. The two Waveshare 14657 displays come to ₹1,026.60 including GST. The two Talema AC1020 sensor bodies come to ₹1,223.04 at the listed price. Finished CT harnesses with the correct permanently fitted burden and fully terminated panel cables still require pricing. Stock GH leads add up to 254 mm against the nominal 250 mm bus target. The exact-length finished option is quote-only. [All 17 field and panel lines](field-sourcing.csv) · [OLED at Hubtronics](https://hubtronics.in/display-devices/0.91inch-oled-display) · [Talema CT at DigiKey India](https://www.digikey.in/en/products/detail/talema-group-llc/AC1020/3881394)

The remaining installation selections include the original starter’s linked auxiliary contacts, the matched transfer and trapped-key hardware, a DC-rated cabinet fuse/holder combination, the antenna and the enclosure dimensions. Existing motor gear and probes can be reused after checking compatibility. A complete delivered price requires the exact-part factory reply and the site-specific cabinet selections. The lower-priced sourcing routes and proposed capacitor changes have no purchase or production commitment.
