# R3 PCB manufacturing review — 24 November 2026

Scope: the current main PCB and panel, excluding external starter/interface design. This review supplements the prior circuit review with assembly geometry, solder paste, component placement and release consistency checks. It is an engineering prototype review, not approval of JLC's unseen placement previews or a physical-board qualification.

## Confirmed issues corrected

| Finding | Correction | Evidence |
| --- | --- | --- |
| R246's +5V_CMD via was centred inside its pad-1 paste aperture. Its 0.30 mm hole could draw solder away from the resistor joint. | Moved the via from (55.175, −5.500) to (55.175, −6.600) mm and added a 0.30 mm top-layer escape. Reconnected its bottom and inner-layer tracks. The final layout retains the project's 8 mm live/control separation. | `manufacturing-check.json`; full main DRC and CAM release checks. |
| DNP preload resistor R2 still had two paste apertures in the supplied stencil. | Retained its copper, mask and body geometry on `PumpRevE:R_2512_6332Metric_DNP_NoPaste`, with both paste layers removed. R2 remains excluded from assembly. | Native schematic/PCB/BOM/library agree; final bottom paste has no R2 objects. |
| Main schematic sheets, board title and Gerber metadata carried inconsistent historical revision labels. | Aligned main-board metadata to `DIRECT-R3-PROTOTYPE`; the printed board revision remains R3. | Native sources, schematic PDF and generated Gerber project attributes. |
| Printed IC orientation marks were inconsistent and covered only selected parts. | Added a consistent filled triangular arrow for every U-designated component: 19 total, eight top and eleven bottom. Each arrow points to actual pad 1 on that component's mounted side. Existing diode cathode marks remain separate. | `ic-pin1-check.json`; exact MPN/footprint/pin coordinates and silk layers are checked, with clearance verified by DRC. |
| Other polarity/orientation marks needed consistent coverage. | Verified the existing cathode brackets on all four LEDs and bars on six single-diode/unidirectional-TVS devices. Added 14 pin-1 arrows for main-board transistors/multi-pin diode packages, two for panel Q1/Q2, and a printed positive sign for C1. Seven bidirectional TVS devices remain unmarked as non-polarized. | `polarity-check.json`; single-diode bars, exact multi-pin part positions and C1's positive pad/net are checked. |
| Standard-PCBA tooling requirements were absent from the order instructions. | Added explicit JLC-supplied rails, fiducials and tooling-hole instructions, including clearance for the edge connectors. The finished board remains 100 × 139 mm. | Updated order checklist and unsent assembler reply. This is a supplier process requirement, not an added circuit. |

JLC explains the solder-wicking risk of unfilled [via-in-pad](https://jlcpcb.com/help/article/via-in-pad-pofv-guide). Its [assembly tooling guide](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order) requires rails/fiducials for Standard PCBA; its [assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service) describe supplier-added tooling. Those process features must appear in JLC's final panel preview, clear of overhanging connector bodies.

## Additional review results

- Reviewed 242 native footprints on the main board and 28 on the panel, including mounting holes and DNP R2. The fitted counts remain 226 main factory placements plus 11 hand-fitted parts, and 19 panel factory placements plus five hand-fitted buttons.
- The nominal closed body outlines on the native fabrication layers have no detected same-side body overlap. Text, polarity marks and open outline decorations were excluded from the body calculation. This is not a maximum-tolerance lead/body collision certificate. The tightest nominal body pair was U3/L1 at about 0.59 mm; actual lead envelopes and rework access still need the assembler's review. `body-spacing.json` records the screening method and source hashes.
- The final manufacturing screen finds no via drill beneath the rectangular paste envelopes and no paste openings on DNP parts on either board. Both original defects are deliberately reintroduced only in memory to prove their detection; the files are unchanged by these controls.
- The smallest fitted main-board paste-pad width is 0.25 mm. A rectangular-aperture estimate with a 0.12 mm stencil gives a minimum area ratio of approximately 0.735. This is a nominal stencil screen, not a substitute for JLC's process-specific aperture treatment. The exposed pads at U2 and U10 need appropriate stencil design and solder-joint inspection.
- Minimum native plated component-hole annular rings are 0.30 mm main and 0.40 mm panel. The via ring minimum is 0.175 mm. These are geometry results, not assertions about component lead tolerances.
- Corrected Sunlord L1 lands and the thirteen physical orientation queries remain covered by `tools/check_pcba_assembly.py`. The exact-part guarded supplier CPL rotations, four THT package-centre corrections, relay physical pin maps and outward-facing power terminals remain checked separately.
- The final ERC, full DRC/parity/creepage and Gerber/drill connectivity results, plus deliberately injected CAM shorts/opens, are recorded in `manufacturing/verification.json`. Source and output hashes bind the release to the current native files. No new definite schematic pin-assignment error was identified in the inspected paths.

Do not infer component spacing from fabrication text boxes or copper pad gaps alone. JLC's [spacing guide](https://jlcpcb.com/help/article/minimum-spacing-for-smd-components) measures component bodies/leads; a raw bounding-box scan of all fabrication text produces false collision reports. Dense custom isolator and USB lands still require exact lead alignment in the supplier preview.

## Remaining supplier and first-article checks

The actual revised Top/Bottom placement images have not been supplied; the earlier email link contained an attachment-list screenshot. JLC must confirm the exact relay reservation/lead time, L1 solder coverage, the new THT/transistor placements, stencil treatment and tooling arrangement. No supplier approval or order action is implied by this revision.

The board's electrical tests are software/geometry checks. USB enumeration, supply transients and temperature, assembled insulation and EMC, sensor calibration and operational firmware remain first-article/integration work. External contactor/capacitor selection is outside this PCB review.

Reproduce the new regression screen with KiCad's Python:

```sh
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/check_manufacturing.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/check_ic_pin1_markers.py
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/check_polarity_markers.py
```

The output includes source hashes and both negative-control results. The review did not send email, upload fabrication files, place orders or approve production.
