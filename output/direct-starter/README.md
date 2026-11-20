# Two-board controller for one existing starter

**₹22,040.97 is the priced portion for one installed controller**, using one main board, one OLED/button board, one display, one CT and the two starter plugs. No 24 V cabinet, external voltage monitor, extra motor contactors or cabinet timers are on the purchase list. Reuse the existing starter, motor, capacitors, STOP, overload and compatible probes. [One-starter parts](parts-one-starter.csv) · [Cost calculation](costs.json) · [Which starter input to use](../../hardware/main-direct/README.md)

| One installation | Priced amount |
| --- | ---: |
| Main board including both sockets, two plug-in relays, two clips and input fuse F1 | ₹15,396.37 |
| Five-button OLED panel PCB | ₹3,762.43 |
| Field materials including the plug-in OLED, CT and connector materials | ₹2,398.33 |
| Two starter-side mating plugs for J30/J35 | ₹483.84 |
| **Total priced** | **₹22,040.97** |

The installed set shares each design's setup charge with the planned shelf spare. Only the installed set is included in the total. If manufacturing one pair alone, assigning the full setup and stencil charges gives **₹28,345.57** before any change to component minimums. The calculation uses the project's historical ₹93.3461/US$ purchase basis. Removing the obsolete main-board parts reduces its previous estimate by ₹859.61. Lots shared with retained components keep their full allowance. The two complete starter plugs were previously priced with the external cabinet and are included here.

The outstanding costs include main J1 and the U3 radio, bare-board fabrication, placement and through-hole assembly, the antenna, completed CT burden and harness, factory-specific control loom or manual restoration insert, mounting/enclosure, taxes, freight and fitting. The optional key switch and external button station are customer choices. The enclosure, control loom and starter interface depend on the actual installation. This is a parts estimate for the prototype. [Board pricing](../jlc-r4/parts-cost-review.md) · [Field items and pricing conditions](../jlc-r4/field-one-starter.csv)

| Board | Fabrication | Assembly |
| --- | --- | --- |
| Main, 100 × 117 mm, 6 layers | [Main Gerbers](main-gerbers.zip) | [BOM](main-BOM.csv) · [Placement](main-CPL.csv) · [Paste](main-stencil.zip) |
| Panel F, 60 × 45 mm, 2 layers | [Panel Gerbers](panel-gerbers.zip) | [BOM](panel-BOM.csv) · [Placement](panel-CPL.csv) · [Paste](panel-stencil.zip) |

The factory solders P6B-04P sockets at K1 and K2. Insert one G6B-1114P-US-P6B DC5 and one P6B-C2 retaining clip at each socket after soldering. The full parts list counts all six pieces. The panel's field kit includes one local STOP loop plug when the optional external station is absent.

The main and panel passed KiCad ERC, board DRC, schematic parity and independent Gerber connectivity comparison. The comparator detected deliberate open and short controls. The schematic checks compare the retained pin assignments against the socketed parent, check the physical panel STOP loop and document the stuck-START limitation. Host firmware tests exercise all three control profiles, voltage trips and rearm. A disabled test image builds for ESP32-C6. Starter interface compatibility, actual relay release, contact behavior and voltage calibration need checking on the physical unit before deployment. [Fabrication and KiCad checks](verification.json) · [Circuit checks](direct-checks.json) · [Control tests](control-tests.json) · [ESP32-C6 build](esp32c6-build.json)
