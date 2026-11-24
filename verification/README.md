# Verification

Current revision: **DIRECT-R3-PROTOTYPE**, 100 × 139 mm main board. [R3 DFM review](dfm-review-2026-11-24/README.md) records the via/paste fixes and manufacturing limits; [PCBA orientation review](pcba-review-2026-11-24/README.md) covers L1 and the supplier's thirteen queried parts. Earlier audits below describe their recorded revisions and are retained as historical evidence.

[Independent electrical audit of the direct two-board controller](direct-controller-audit.md)

The release exporter runs KiCad schematic ERC and PCB DRC with schematic parity, checks the cut outline and dimension, verifies the assembly BOM against native placements, and compares the Gerber copper and drill connectivity with the PCB's IPC-D-356 netlist. The CAM comparison also intentionally opens and shorts each board to test the checker. [KiCad and CAM evidence](../manufacturing/verification.json) · [Named interface pin checks](interfaces.json) · [Fabrication drill and outline comparison](drills-and-outlines.json)

| Check | How to reproduce |
| --- | --- |
| Datasheet-level design review | Three subsystem reviews of every IC pin, rail and value. Findings, fixes and the revision 2 list: [design review 2026-11-21](design-review-2026-11-21.md) |
| Schematic, layout and CAM | Install KiCad 10.0.8 and make `kicad-cli` available, or set `KICAD_CLI`. Use Python with Gerbonara and Shapely. Build `tools/cam/compare.cpp` against [GerberTools](https://github.com/jvanstraten/gerbertools) at commit `7d797b51b13da8060e27d5b16444052a73c5fc32` using C++17, its `src/*.cpp` and include directories `include` and `src`. From the project root run `python3 tools/export_boards.py --compare /path/to/compare`. |
| Programming and control connections | `python3 tools/check_interfaces.py` |
| Via holes beneath paste and DNP stencil openings | Run `tools/check_manufacturing.py` with KiCad's Python. The two injected controls demonstrate detection of the corrected R246 and R2 defects. |
| Printed pin-1 arrows for all ICs | Run `tools/check_ic_pin1_markers.py` with KiCad's Python. Every native U reference must have a side-correct arrow pointing to its actual pin 1, bound to its exact MPN and footprint. |
| LED/diode/capacitor and transistor marks | Run `tools/check_polarity_markers.py` with KiCad's Python. Checks cathode bars, C1 positive and multi-pin diode/transistor pin-1 arrows; distinguishes non-polarized TVS devices. |
| Control profiles and application LED timing | `sh firmware/components/starter_outputs/tests/run-host.sh`. [Host results](firmware-host.txt) |
| Flashable bench image | Build the ESP32-C6 bench project with ESP-IDF v5.4.2. The build uses the 4 MB flash setting. [Build record](usb-bench.json) · [Flash and test](../docs/programming.md) |

The named pin checks cover the 12-way harness, five panel buttons, external station, key selector and display, both pilot contacts and flyback diode polarities, relay inhibit, tank and inlet sensors, isolated supply and meter paths. The isolation-class check requires every named main-board copper net to belong to one domain. KiCad checks the project’s 8 mm live-to-control clearance and board-surface creepage targets. This value is a layout target. Enclosure conditions, insulation construction and assembled-board performance require separate qualification.

Manufacturer references for the pin checks include the [RECOM power module](https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf), [TI regulator](https://www.ti.com/lit/ds/symlink/tps62162.pdf), [ADI voltage/current meter](https://www.analog.com/media/en/technical-documentation/data-sheets/ADE7953.pdf), [Chipanalog powered isolator](https://jlcpcb.com/partdetail/Chipanalog-CA_IS3641HW/C2890052), [TI probe multiplexer](https://www.ti.com/lit/ds/symlink/tmux1208.pdf), [Omron G5RL relay](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g5rl.pdf), [Omron panel STOP](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf) and [Waveshare display drawing](https://files.waveshare.com/upload/2/2a/0.91inch_OLED_Module_Schematic.pdf).

Before connecting a motor, verify the pilot voltage, coil inrush and suppression against the starter documentation. The first article still needs USB enumeration and boot recovery tests, physical relay-inhibit measurements, original STOP/overload and restart checks, CT burden and voltage calibration, insulation and EMC testing. The software tests operate on simulated inputs.
