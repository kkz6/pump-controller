# Cost for one 1 HP starter

The installed controller's two boards and field parts have **₹22,416.74 of priced items**. The separate conventional 24 V DC cabinet accounts for another **₹89,325.28** on the project's exchange-rate basis. The full reference design therefore has **₹1,11,742.02 priced** before unquoted items, fitting, and delivery. The site starter's control voltage is unknown. Defer purchase of cabinet hardware until the starter interface is identified.

| Included in one installed set | Estimated INR |
| --- | ---: |
| Main board with both socketed relay assemblies and F1 | 16,255.98 |
| Five-button panel PCB | 3,762.43 |
| Field parts including one plug-in OLED and one CT | 2,398.33 |
| **Board pair and priced field items** | **22,416.74** |
| Conventional 24 V DC reference cabinet, ₹89,131.12 + US$2.08 | 89,325.28 |
| **Priced portion of the installed reference configuration** | **1,11,742.02** |

Only one installed set is counted above. The two-board-per-design sourcing plan shares the production setup between the installed PCBs and their shelf spares. The historical reference rate is ₹93.3461/US$. The main uses US$118.1238 in previously priced parts, less US$1.9546 for the two superseded soldered relays, plus US$33.77 allocated setup and stencil. Add ₹2,071.52 for two new relay assemblies and ₹188.22 for one previously unpriced Bel 0ADKP1000-RE fuse. The panel uses US$6.5362 in parts and US$33.77 in setup and stencil. The spare board pair adds approximately ₹20,018.41 in priced items if purchased with the installed set. A factory run of one pair alone would carry the full setup charges and may have different component minimums. [Original component and setup estimates](../jlc-r4/parts-cost-review.md) · [Factory pricing by part](../jlc-r4/factory-parts-pricing.csv) · [Fuse listing](https://www.mouser.in/en/ProductDetail/Bel-Fuse/0ADKP1000-RE?qs=sGAEpiMZZMsIz3CjQ1xegQaWavv5npkeMm1%2FYpYkx%2FwNDj8OEHNLjQ%3D%3D)

| Replaceable assembly | Qty per main | Unit INR | Extended INR |
| --- | ---: | ---: | ---: |
| G6B-1114P-US-P6B DC5 relay | 2 | 424.24 | 848.48 |
| P6B-04P socket | 2 | 403.22 | 806.44 |
| P6B-C2 clip | 2 | 208.30 | 416.60 |

[Relay](https://www.digikey.in/en/products/detail/aratas-formerly-omron-components/G6B-1114P-US-P6B-DC5/2755299) · [Socket and clip series](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6b.pdf) · [Retaining clip](https://www.digikey.in/en/products/detail/aratas-formerly-omron-components/P6B-C2/1828742)

## Where the cost comes from

| External cabinet hardware | Estimated INR | Function in this particular cabinet |
| --- | ---: | --- |
| Schneider RM17UBE15, KV1 | 16,550.39 | Opens permission if the protected motor supply downstream of the cabinet isolator leaves its voltage window. |
| Schneider RM17UBE16, KC1 | 16,550.39 | Independently supervises the factory 24 V DC pilot supply. Verify that the starter actually has this supply. |
| Five Omron G7SA guided relays and five sockets | 17,565.00 | Provide hardwired command checks, reset and permission. |
| Two Omron high-speed DC gates | 9,674.00 | Interrupt the cabinet and pilot permission paths. |
| USB shutter switch and actuator | 8,264.35 | Detect service access. |

The two monitors together account for ₹33,100.78, about 37% of the reference cabinet. For display and firmware-controlled voltage limits the main PCB already has an ADE7953 measuring the AC supply at J1. The existing two command relays can request STOP and block a new start when measurements are out of range. The separate CT monitors motor current. Verify that J1 represents the desired pump supply, especially if the board has a separate feed. Calibrate against a meter under load. Use distinct trip/recovery thresholds and time qualification, and inhibit automatic starts when readings are missing. Voltage recovery alone must not clear a physical STOP or overload lockout. Firmware-controlled voltage behavior requires working firmware and a functioning stop interface. [Voltage and current metering](https://www.analog.com/en/products/ade7953.html)

No additional voltage parts are required for this firmware feature. Both external monitors are part of the older cabinet's hardwired enable circuit. Removing them from that diagram would change its behavior. Its ₹89,325.28 estimate is a reference, and ₹22,416.74 is a controller-and-field subtotal only. A lean installed configuration needs a documented starter interface and verification of original STOP, overload and restart behavior before it can be priced or released. [Cabinet circuit and monitor locations](../../hardware/starter-budget-r4/README.rst) · [Cabinet sourcing by part](../jlc-r4/budget-cabinet-one-starter.csv)

Unpriced main positions are J1, U3, C303/C304 and U301. Other exclusions include final fabrication, placement, through-hole assembly, source handling, inspection, tax differences, freight, finished harnesses and antenna, applicable cabinet transfer, lock and isolation hardware, enclosure, fitting and commissioning. One-off retail prices and factory consignment require confirmation at order. [Field kit and pricing conditions](../jlc-r4/field-one-starter.csv)
