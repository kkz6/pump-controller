# Cost of the manual-reset DOL cabinet

For one installed 1 HP starter, the revised cabinet has **₹89,131.12 plus US$2.08** of priced parts. Adding one populated main board, one populated OLED/button board and one field kit brings the priced portion to **₹1,09,470.45 plus US$2.08**. Adding the spare populated board pair brings it to **₹1,27,411.45 plus US$2.08**. The matched isolator and lock, cabinet wiring, installation and final PCB assembly charges still require quotes. [Revised cabinet purchase lines](budget-cabinet-one-starter.csv) · [Cabinet design](../../hardware/starter-budget-r4/README.rst)

## What changed in the cabinet

| Conventional 24 V DC pilot, one cabinet | Priced parts |
|---|---:|
| Earlier R4 with the purchasing file’s original suppliers | ₹2,23,385.66 + US$2.08 |
| Earlier R4 with the three Omron relays and sockets at the Indian retailer’s rates used below | ₹2,02,923.17 + US$2.08 |
| Revised cabinet with five guided relay assemblies, a restart-inhibit timer and two fast electronic relay modules | **₹89,131.12 + US$2.08** |
| Reduction from the circuit change on the same sourcing basis | **₹1,13,792.05** |

The previously published **₹2,01,757.50** covered only common cabinet hardware. For the same conventional pilot as the new schematic, add the independent 24 V pilot voltage monitor (₹16,550.39) and the priced pickup-detection parts (₹5,077.77 plus US$2.08) to either design’s common scope. The original programmable heartbeat monitor and two Pilz units account for ₹1,32,784.21 of the earlier cost. Removing their fuse and the second enable button, then fitting two guided relays with sockets, a restart-inhibit timer, two fast electronic relay modules, five diodes, three bleed resistors and an NC block on RESET, gives the same-source reduction above. Switching the three existing Omron relays and sockets to the local offers accounts for another ₹20,462.49 against the original estimate. [Earlier purchase lines and supplier evidence](cabinet-one-starter.csv)

| Major purchases retained in the revised profile | Amount counted |
|---|---:|
| Feeder voltage monitor and independent OEM pilot voltage monitor | ₹33,100.78 |
| Five Omron G7SA-2A2B DC24 relays and five plain P7SA-10F sockets | ₹17,565.00 |
| Two fast Omron G3RV-ST500-D-H DC24 relay modules, each with base | ₹9,674.00 |
| USB shutter switch and actuator | ₹8,264.35 |
| Two motor-feed isolation contactors | ₹5,076.40 |
| Pilot open-command timer | ₹4,863.50 |
| Autonics CT6S-1P2 restart-inhibit timer | ₹4,583.00 |
| Other priced cabinet items | ₹6,004.09 + US$2.08 |

The five guided relays are ₹2,359 each and their sockets are ₹1,154 each. The two high-speed G3RV modules are ₹4,837 each. All three retailer prices include GST. Stock for the full quantities, traceability, matching terminal versions and delivery to 560072 require confirmation. Apple Automation and Sensor lists the CT6S-1P2 in stock at ₹4,583 with GST treatment to confirm. Its terminal block connects directly. The added NC contact block is provisionally ₹271.75 with GST. Other lines use the catalog and tax basis recorded for each supplier. No uniform GST, freight or duty assumption has been applied. Prices reviewed 20 November 2026. [Omron relay offer](https://www.industrybuying.com/safety-relay-omron-IND.OMR.93892282) · [Matching socket offer](https://www.industrybuying.com/power-socket-omron-IND.OMR.83893856) · [Exact high-speed DC relay module](https://www.industrybuying.com/solid-state-relay-omron-IND.SOL.728415644) · [Autonics timing unit](https://www.sensorindia.co.in/ct6s-1p2-autonics) · [Reset contact block](https://www.eleczo.com/nc-screw-terminal-contact.html)

## Boards, field kit and outstanding costs

| Item | One installed | Shelf spare |
|---|---:|---:|
| Main R4, partial component and setup estimate | ₹14,179 | ₹14,179 |
| OLED/button panel F, partial component and setup estimate | ₹3,762 | ₹3,762 |
| Field materials, including one OLED and one CT | ₹2,398.33 | Shared on exchange |
| Priced cabinet materials | ₹89,131.12 + US$2.08 | Shared on exchange |
| Priced portion | **₹1,09,470.45 + US$2.08** | **₹17,941** |

The site must have a compatible conventional 24 V DC pilot, the necessary original STOP, START and overload contacts, and verified contactor and holding-circuit feedback. For a confirmed TeSys D installation that needs them, the earlier purchasing file lists ₹2,538.20 for a compatible contactor and ₹2,349.57 for a compatible additional contact block. Their possible ₹4,887.77 is outside the headline and cannot price conversion of an unidentified starter. [OEM reference lines](budget-cabinet-one-starter.csv)

Outstanding cabinet prices include the matched key-trapped disconnector and USB access lock, transfer assembly, finished looms, control supply and protection as fitted, rail accessories, enclosure, fabrication and electrical fitting/testing. The field kit still needs a price for its antenna, completed CT and cable work. The PCB figures are provisional component lots and an allocated share of factory setup and stencil charges. Five main-board part numbers, fabrication, placement, through-hole work, inspection and delivery charges are open. The physical starter’s coil, auxiliary contacts and model compatibility and the delivered price of each board must be verified before purchasing. [Field kit](field-one-starter.csv) · [PCB estimate breakdown](parts-cost-review.md)
