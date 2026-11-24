# R4 manufacturing review — 2026-11-24

The compact 100 × 118.5 mm main board retains the R3 circuit and DFM corrections. This folder contains current source-hash-bound manufacturing, body-spacing, IC pin-1 and other polarity checks. The R3 records remain in the parent folder.

- Native DRC checks the complete routing, keepouts, courtyard fit, silkscreen, hole spacing and schematic parity; the release also enables 8 mm LIVE-to-control clearance and creepage targets.
- Manufacturing screens check via holes beneath paste, DNP paste, PTH rings and stencil apertures. The original R246 via-in-paste and R2 paste defects are deliberately reintroduced in memory to prove detection.
- Body screening merges closed nominal fabrication-body compartments before checking same-side intersections. This avoids treating a terminal's internal compartment as its entire body. Maximum package/lead tolerances and physical solderability remain outside that screen.
- All 19 main-board ICs have arrows to actual pad 1. The additional transistor/diode arrows, LED/diode cathode marks and C1 positive mark are retained and checked on their mounted sides.

JLC must still review actual revised placements, L1 coverage, THT lead fit, process rails, fiducials, tooling and stencil/panel-tab clearance. Software checks are not a physical insulation, current, EMC or switching-endurance qualification. Exact relay stock and reservation remain unconfirmed. No supplier production approval is issued by these records.

[Compact-layout record](../../compact-layout-2026-11-24.md) · [Assembly review](../../pcba-review-2026-11-24/R4/README.md).
