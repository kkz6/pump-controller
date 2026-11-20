# Manufacturing package

Use one Gerber ZIP per board. Each includes the outline, copper, solder masks, both silkscreens and plated and non-plated drill files. Request standard FR-4, 1.6 mm thickness, 1 oz outer copper and electrical testing. Verify the displayed layer count and dimensions on the fabricator's preview.

| Board | Bare PCB | Assembly | Optional paste stencils |
| --- | --- | --- | --- |
| Main R2, 100 × 117 mm, six layers | [Gerbers and drills](main-gerbers.zip) | [BOM](main-BOM.csv) · [Placement](main-CPL.csv) | [Both sides](main-stencil.zip) |
| OLED panel F, 60 × 45 mm, two layers | [Gerbers and drills](panel-gerbers.zip) | [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv) | [Both sides](panel-stencil.zip) |

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
