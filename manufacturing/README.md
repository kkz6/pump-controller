# Manufacturing package

Use one Gerber ZIP per board. Each includes the outline, copper, solder masks, both silkscreens and plated and non-plated drill files. Request standard FR-4, 1.6 mm thickness, 1 oz outer copper and electrical testing. Verify the displayed layer count and dimensions on the fabricator's preview.

| Board | Bare PCB | Assembly | Optional paste stencils |
| --- | --- | --- | --- |
| Main R2, 100 × 117 mm, six layers | [Gerbers and drills](main-gerbers.zip) | [BOM](main-BOM.csv) · [Placement](main-CPL.csv) | [Both sides](main-stencil.zip) |
| OLED panel F, 60 × 45 mm, two layers | [Gerbers and drills](panel-gerbers.zip) | [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv) | [Both sides](panel-stencil.zip) |

The panel assembly BOM has a catalogue ID for every line. Four main-board lines still require sourcing confirmation for full assembly: F1 (fuse), J1 (mains connector), K1/K2 (sockets) and U3 (radio module). Obtain written confirmation that all four will be fitted before paying for full assembly.

Two published JLCPCB entries can be used for the quote. The U3 entry gives the exact module number and lists JLCPCB Assembly as the manufacturer. Confirm genuine Espressif supply and availability. The socket entry shows zero stock and describes an SMT operation for a through-hole socket. Confirm the fitting process and supply before accepting it. [Radio catalogue entry](https://jlcpcb.com/partdetail/ESPRESSIF-ESP32_C6_MINI_1UH8/C9900163889) · [Relay socket catalogue entry](https://jlcpcb.com/partdetail/OmronElectronics-P6B_04P_FORG6B/C2756282)

The assembly BOM fits **sockets** at main K1 and K2. Buy two G6B-1114P-US-P6B DC5 relays and two P6B-C2 clips for each populated main board. Insert the relays after soldering and cleaning. A functional installation also needs the plug-in display, CT and burden, antenna and harnesses. [One-starter parts list](parts-one-starter.csv) · [Field parts and sourcing](field-parts.csv)

## One-starter budget

| Item | Priced portion |
| --- | ---: |
| Populated main board, including both removable relay assemblies | ₹15,468.06 |
| Populated OLED/button PCB | ₹3,762.43 |
| Display, CT and other priced field materials | ₹2,398.33 |
| Two mating starter plugs | ₹483.84 |
| **One installed controller, with setup shared with a spare pair** | **₹22,112.66** |

The two programming buttons add ₹35.06 per controller. The two green USB indicators and their 1 kΩ resistors add ₹36.63. These are fitted component costs using the recorded supplier rates. The two relays, sockets and clips together are ₹2,071.52 and are included above. For manufacture of only one pair, allocating the entire setup and stencil fees gives **₹28,417.26** before any changes to lot minimums. Radio U3, main J1, board fabrication, placement and through-hole assembly, full harnesses, enclosure, tax, delivery and fitting still need quotes. The existing starter, motor and compatible tank probes are reused. [Cost assumptions](costs.json)

Check the connector orientation, relay removal clearance, part availability, capacitor DC-bias margin and the actual starter interface before assembly. Design-file verification and first-article tests are tracked separately. [Design checks](../verification/README.md)

### Cost target for the next revision

Target ₹10,000 delivered for one complete controller on one existing starter, including both populated boards, display, CT and burden, harnesses, enclosure, fitting and tax. The present budget allocates ₹12,609.20 in setup and stencil fees when buying one pair. Even with those fees removed, the priced items come to ₹15,808.06 before unquoted items.

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
