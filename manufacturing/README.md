# Manufacturing package

Use one Gerber ZIP per board. Each includes the outline, copper, solder masks, both silkscreens and plated and non-plated drill files. Request standard FR-4, 1.6 mm thickness, 1 oz outer copper and electrical testing. Verify the displayed layer count and dimensions on the fabricator's preview.

| Board | Bare PCB | Assembly | Optional paste stencils |
| --- | --- | --- | --- |
| Main R2, 100 × 117 mm, six layers | [Gerbers and drills](main-gerbers.zip) | [BOM](main-BOM.csv) · [Placement](main-CPL.csv) | [Both sides](main-stencil.zip) |
| OLED panel F, 60 × 45 mm, two layers | [Gerbers and drills](panel-gerbers.zip) | [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv) | [Both sides](panel-stencil.zip) |

The panel assembly BOM has a catalogue ID for every line. Four main-board lines still require sourcing confirmation for full assembly: F1 (fuse), J1 (mains connector), K1/K2 (sockets) and U3 (radio module). Obtain written confirmation that all four will be fitted before paying for full assembly.

As of 2026-11-21, several more parts have no JLC stock:
- **Main board:** U1, U11, U32, C51–C54 and RV1
- **Panel:** J2 and J7

Arrange those through global sourcing or consignment before ordering. [Stock status](../verification/bom-and-cost-review.md)

Two published JLCPCB entries can be used for the quote. The U3 entry gives the exact module number and lists JLCPCB Assembly as the manufacturer. Confirm genuine Espressif supply and availability. The socket entry shows zero stock and describes an SMT operation for a through-hole socket. Confirm the fitting process and supply before accepting it. [Radio catalogue entry](https://jlcpcb.com/partdetail/ESPRESSIF-ESP32_C6_MINI_1UH8/C9900163889) · [Relay socket catalogue entry](https://jlcpcb.com/partdetail/OmronElectronics-P6B_04P_FORG6B/C2756282)

The assembly BOM fits **sockets** at main K1 and K2. Buy two G6B-1114P-US-P6B DC5 relays and two P6B-C2 clips for each populated main board. Insert the relays after soldering and cleaning. A functional installation also needs the plug-in display, CT and burden, antenna and harnesses. [One-starter parts list](parts-one-starter.csv) · [Field parts and sourcing](field-parts.csv)

The fully populated board supports the six-core shared-common inlet harness with J21.2 left open. For a separately identified bench prototype dedicated to that harness, the unused J21.2 excitation branch can be left unpopulated at R118, R119, R120, C107, C109, D101 and D103. Keep U20 and its local feedback, the J20.1 protection, and the entire J21.1 sense path. The inlet driver output still reaches the ADC multiplexer, so its reading alone cannot confirm excitation at the probes. Qualify the shared driver with fresh readings on all five channels at the intended cable lengths, water conductivity and contactor switching conditions before approving a production assembly variant. [Inlet wiring options](../docs/connections.md#inlet-sensing-on-a-six-core-cable)

## One-starter budget

Priced 2026-11-21 for one JLCPCB order of two complete sets, which is the assembly minimum. Every fee is split evenly between the two sets.

| Item, per installed controller | Priced portion |
| --- | ---: |
| Populated main board, including both removable relay assemblies and half the board's fees | ₹19,846.92 |
| Populated OLED/button PCB, including half its fees | ₹4,604.14 |
| Shipping, half of one order | ₹1,213.03 |
| Display, CT and other priced field materials | ₹2,398.33 |
| Two mating starter plugs | ₹483.84 |
| **One installed controller** | **₹28,546.26** |

Of that total, ₹12,874.29 is JLC setup, stencil and per-line loading fees. Both boards are double-sided, so both need Standard assembly. Its fees are charged per order, not per board, so they shrink per controller as the order quantity grows.

How the parts are priced:
- **Main board:** $81.21 of components and a $40.60 bare-board quote for five 6-layer boards.
- **Panel:** $3.48 of components and a $4.00 bare-board quote.
- **Relays:** the two relays and clips are ₹1,406.26.

Still unpriced: customs duty and GST, the antenna, the CT burden, harness labour, the enclosure and site fitting. U1 and U11 have no JLC stock and are priced at JLC's estimate. The existing starter, motor and compatible tank probes are reused. [Cost assumptions](costs.json) · [Parts and cost review](../verification/bom-and-cost-review.md)

Check the connector orientation, relay removal clearance, part availability, capacitor DC-bias margin and the actual starter interface before assembly. Design-file verification and first-article tests are tracked separately. [Design checks](../verification/README.md)

### Cost target for the next revision

Target ₹10,000 delivered for one complete controller on one existing starter, including both populated boards, display, CT and burden, harnesses, enclosure, fitting and tax. The present budget allocates ₹12,874.29 in assembly fees per controller when buying two sets. Even with those fees removed, the priced items come to ₹15,671.97 before unquoted items. Moving the panel to single-sided assembly, or hand-fitting it, removes most of its share of those fees.

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
