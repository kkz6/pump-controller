# Socketed R4 prototype for one pump starter

The main board uses two replaceable 5 V command relays. The separate front panel has five buttons and a plug for the OLED. This package is for the existing R4 cabinet interface. The installed starter's pilot voltage, control inputs, STOP and overload behavior, and clearance for removing the relays still require verification. The separate onboard restart latch was deferred. The prototype has no stand-alone installation release.

| Board | Outline and layers | Fabrication | Assembly |
| --- | --- | --- | --- |
| Main | 100 × 117 mm, 6 layers | [Gerbers and drills](main-gerbers.zip) | [Bill of materials](main-BOM.csv) · [Placement](main-CPL.csv) · [Paste](main-stencil.zip) |
| OLED/button panel F | 60 × 45 mm, 2 layers | [Gerbers and drills](panel-gerbers.zip) | [Bill of materials](panel-BOM.csv) · [Placement](panel-CPL.csv) · [Paste](panel-stencil.zip) |

K1 and K2 are through-hole P6B-04P sockets. Solder the sockets, then insert one G6B-1114P-US-P6B DC5 and fit one P6B-C2 clip at each position. Factory or consigned supply of the exact sockets and the manual insertion step need confirmation. The factory placement list has 272 positions on the main and 24 on the panel. The plug-in OLED and current transformer are field items. [Relay assemblies](post-assembly-parts.csv) · [One-starter purchase list](parts-one-starter.csv) · [One-starter cost](cost-one-starter.md)

KiCad 10.0.8 electrical rules, board rules and schematic-to-board parity reported zero violations and zero unrouted connections on both boards under the project rules. The exported copper and plated barrels were compared to the IPC electrical netlist at 2,085 layer locations on the main and 139 on the panel. Each passed with zero opens or shorts. The same checker detected both an injected open and an injected short on each board. A separate drill and outline comparison found no missing or additional features. Bench fault tests, loaded calibration, installed insulation and fit, EMC and assembly house review remain open. [KiCad, archive and connectivity records](verification.json) · [Drill and outline checks](drill-outline-check.json) · [Relay service and starter fault test](../../hardware/main-socketed/README.md)
