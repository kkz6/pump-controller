# Manufacturing package

Use one Gerber ZIP per board. Each includes the outline, copper, solder masks, both silkscreens and plated and non-plated drill files. Request standard FR-4, 1.6 mm thickness, 1 oz outer copper and electrical testing. Verify the displayed layer count and dimensions on the fabricator's preview.

| Board | Bare PCB | Assembly | Optional paste stencils |
| --- | --- | --- | --- |
| Main R2, 100 × 117 mm, six layers | [Gerbers and drills](main-gerbers.zip) | [BOM](main-BOM.csv) · [Placement](main-CPL.csv) | [Both sides](main-stencil.zip) |
| OLED panel F, 60 × 45 mm, two layers | [Gerbers and drills](panel-gerbers.zip) | [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv), rear side only | [Both sides](panel-stencil.zip) |

The panel assembly BOM has a catalogue ID for every line. Order the panel as **single-sided Economic PCBA on the bottom (rear) side**. The five front buttons are not in the JLC files: fit SW1 (D2F-01F) and SW2–SW5 (B3U-1000P) by hand after assembly. The main board's 15 through-hole parts are also left out of the JLC files and fitted by hand after assembly: C1, F1, J1, J2, J10, J20, J21, J30, J35, J41, K1, K2, R1, RV1 and U1. Buy them with the order or separately (U1 from DigiKey).

Stock checked on JLC on 2026-11-21. Every factory-mounted line on both boards is in stock, including U3, which is now the ESP32-C6-MINI-1U-H4 (C20627095). Panel J7 is the Megastar ZX-PH2.0-WT4P (C7429691), a JST PH-compatible header on the same land, because the JST S4B-PH-SM4-TB is pre-order only.

For the hand-fitted parts:
- **U1:** no JLC stock. Buy it from DigiKey at about $10 rather than accepting JLC's $22.94 pre-order estimate.
- **RV1:** JLC lists only 3 of TMOV14RP320EL2T7 (C22815876). Buy both sets' worth at once, or buy the TMOV14RP320EL2B7 bulk pack from a distributor. Both have the same inline crimped L2 leads.
- **Everything else:** in stock. J1 is now the Kefa KF128-7.5-2P (C474954).

[Stock status](../verification/bom-and-cost-review.md#availability-check-2026-11-21)

K1 and K2 are Omron G6B-1114P-US DC5 relays (C397224) soldered directly into the P6B-04P land pattern, which matches the relay's own PCB holes. There is no socket or clip, so replacing a relay means desoldering it. A functional installation also needs the plug-in display, CT and burden, antenna and harnesses. [One-starter parts list](parts-one-starter.csv) · [Field parts and sourcing](field-parts.csv)

The fully populated board supports the six-core shared-common inlet harness with J21.2 left open. For a separately identified bench prototype dedicated to that harness, the unused J21.2 excitation branch can be left unpopulated at R118, R119, R120, C107, C109, D101 and D103. Keep U20 and its local feedback, the J20.1 protection, and the entire J21.1 sense path. The inlet driver output still reaches the ADC multiplexer, so its reading alone cannot confirm excitation at the probes. Qualify the shared driver with fresh readings on all five channels at the intended cable lengths, water conductivity and contactor switching conditions before approving a production assembly variant. [Inlet wiring options](../docs/connections.md#inlet-sensing-on-a-six-core-cable)

## One-starter budget

Priced 2026-11-21 for one JLCPCB order of two complete sets, which is the assembly minimum. Every fee is split evenly between the two sets.

| Item, per installed controller | Priced portion |
| --- | ---: |
| Populated main board, including both relays and half the board's fees | ₹14,254.95 |
| Populated OLED/button PCB, including half its fees | ₹1,469.56 |
| Shipping, half of one order | ₹1,213.03 |
| Display, CT and other priced field materials | ₹2,398.33 |
| Two mating starter plugs | ₹483.84 |
| **One installed controller** | **₹19,819.71** |

Of that total, ₹8,391.81 is JLC setup, stencil and per-line loading fees:
- **Main board:** double-sided, so it needs Standard assembly. Its through-hole parts are hand-fitted, which leaves 59 JLC lines.
- **Panel:** goes on single-sided Economic assembly, with its front buttons fitted by hand.

JLC's monthly assembly coupons are not deducted. The fees are charged per order, not per board, so the cost per controller falls quickly with order size:

| Complete sets per order | 2 | 5 | 10 | 20 |
| --- | ---: | ---: | ---: | ---: |
| Per installed controller, approximate | ₹19,820 | ₹12,810 | ₹10,560 | ₹9,410 |

Above five sets, the larger bare-board and shipping quotes are estimated.

How the parts are priced:
- **Main board:** $52.33 of components, including both relays and the hand-fitted parts, and a $40.60 bare-board quote for five 6-layer boards.
- **Panel:** $2.62 of components and a $4.00 bare-board quote.

Still unpriced: customs duty and GST, the antenna, the CT burden, harness labour, the enclosure and site fitting. U1 has no JLC stock. It is priced at DigiKey's single-unit price of $10.04 (945-RACM06E-05SK/277-ND), to be consigned or bought through JLC global sourcing; JLC's own pre-order estimate is $22.94. The existing starter, motor and compatible tank probes are reused. [Cost assumptions](costs.json) · [Parts and cost review](../verification/bom-and-cost-review.md)

Check the connector orientation, part availability, capacitor DC-bias margin and the actual starter interface before assembly. Design-file verification and first-article tests are tracked separately. [Design checks](../verification/README.md)

### Cost target for the next revision

Target ₹10,000 delivered for one complete controller on one existing starter, including both populated boards, display, CT and burden, harnesses, enclosure, fitting and tax. The present budget allocates ₹8,391.81 in assembly fees per controller when buying two sets. Even with those fees removed, the priced items come to ₹11,427.90 before unquoted items.

| Subsystem | Maximum target |
| --- | ---: |
| Main and panel PCB fabrication, assembly and all setup fees | ₹2,000 |
| Main-board components including certified isolated supply, radio and two replaceable pilot relay assemblies | ₹3,100 |
| Voltage and current measurement, including transformers and CT burden | ₹1,400 |
| Populated panel components, display, cables and mating plugs | ₹1,000 |
| Enclosure, insulation, mounting and fitting | ₹1,500 |
| Tax, freight and contingency | ₹1,000 |
| **Complete installed controller** | **₹10,000** |

These figures are design ceilings. Obtain single-set quotes from a domestic assembler for one-sided assembly on both boards. Compare two- and four-layer main layouts using the same connectors, enclosure and isolation rules. Price a suitably rated isolated voltage transformer and a CT feeding low-voltage ADC inputs against the current ADE7953 plus powered digital isolator. Specify voltage and current accuracy, mains insulation and underload performance before selecting the replacement. If reporting real power is retained, also characterize phase error. Carry the original hardwired STOP and overload, the two replaceable pilot relays and the programming inhibit into both comparisons. Approve the lower-cost design only against a delivered one-set quote with all installation parts included.
