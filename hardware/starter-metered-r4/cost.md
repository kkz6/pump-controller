# What one starter needs

The priced portion for one installed 1 HP starter is **₹78,641.24**. The two external voltage monitors have been removed, saving **₹33,100.78** against the socketed reference. The ADE7953 voltage input already belongs to the main PCB. Price assumptions and setup allocation are carried over from the previous estimate for a like-for-like comparison. A delivered installation price requires a site and assembly quote. [One-starter bill of materials](parts-one-starter.csv) · [Cabinet purchasing lines and supplier prices](cabinet-purchases.csv) · [Calculated totals](costs.json)

| For one installation | Priced INR |
| --- | ---: |
| Main PCB with two replaceable relays, two sockets, two clips and input fuse | 16,255.98 |
| Five-button panel PCB | 3,762.43 |
| Field parts, including one plug-in OLED, CT and connector materials | 2,398.33 |
| Cabinet parts, ₹56,030.34 + US$2.08 converted at ₹93.3461/US$ | 56,224.50 |
| **One installed set, priced portion** | **78,641.24** |

The installed-set estimate allocates half of each design's assembly setup to the shelf spare, as planned. It includes one board pair, one OLED, one CT and one cabinet. If manufacturing **only one pair**, allocating both full setup fees gives **₹84,945.83** before open costs and changes to component minimums. [PCB cost basis and exclusions](../../output/socketed-r4/cost-one-starter.md)

| Included cabinet items | Purpose | Estimated INR |
| --- | --- | ---: |
| 5 × G7SA-2A2B DC24 and 5 × P7SA-10F sockets | Check relay release and store stop/reset permission | 17,565.00 |
| 2 × G3RV-ST500-D-H DC24 | Interrupt cabinet enable and factory coil quickly on a trip | 9,674.00 |
| D4NS-4BF and D4DS-K1 | Detect USB service shutter opening | 8,264.35 |
| 2 × LC1D09BD | Series motor isolation contactors and feedback | 5,076.40 |
| 1 × RE17RAMU and 1 × CT6S-1P2 | Prove released pickup and keep the starter off after a short STOP | 9,446.50 |
| 1 × HDR-60-24 | One isolated supply for the cabinet and compatible factory pilot | 1,987.80 |
| Reset button and contact block, plugs, terminals, diodes, resistors and pickup detector | Reset, wiring and contact feedback | 4,210.45 |
| **Priced cabinet** | | **56,224.50** |

Reuse one verified compatible DOL starter, its original START/STOP, overload, motor, capacitors and existing tank probes. Four level wires plus the common go to the tank. The inlet input on the stocked socketed board uses its documented separate electrode interface. Retain the existing inlet sensor only after verifying its return arrangement. Order one OLED and one CT. The optional key switch and external button station can be added if wanted. The R4 panel requires the correct local-only mating plug with its STOP loop when there is no remote station. [Plug and field material details](../../output/jlc-r4/field-one-starter.csv)

**Still open for pricing** are the properly rated F3 auxiliary AC protection and F2 DC protection, covered distribution terminals, required branch protection if the existing unit is unsuitable, matched service isolator and lock, transfer assembly, finished looms and burden, antenna, enclosure and mounts, factory placement/through-hole work, unmatched board parts, delivery, tax differences and qualified installation/testing. Unpriced main placements are J1, U3, C303/C304 and U301. If the compatible factory contactor and feedback accessory need to be bought, the existing conditional estimates add ₹4,887.77. This figure does not price conversion of an unidentified starter. [Per-part price basis](cabinet-purchases.csv) · [Single-site field inventory](../../output/jlc-r4/field-one-starter.csv)

The ₹56,224.50 cabinet is specific to the retained R4 stop/reset and service circuit and its verified-host-feedback requirement. It is a separate purchase from the programmable controller. No cabinet purchase or conversion should be based on this estimate until the installed starter's pilot and original controls have been identified.
