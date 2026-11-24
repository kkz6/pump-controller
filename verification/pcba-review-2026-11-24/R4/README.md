# R4 compact PCBA review — SMT026112161707_Y2

The main board is now **100 × 118.5 mm**, 20.5 mm shorter than R3. Relays lie horizontally along the bottom; J30/J35 face outward from that edge. J20 tank and J21 inlet headers moved to the top. Electrical pinouts, component selections and panel design are retained.

Request **Replace File** for the held order and upload the complete matching R4 Gerber, BOM and CPL set. The self-contained R3 bundle remains historical. No supplier message, upload, purchase or production approval has been performed here.

K1/K2 remain Omron G5RL-1-E-HR DC5 / C1563288; J30/J35 remain Phoenix 1711738 / C91156. All four are factory-fitted THT parts. Terminals are **1 NO, 2 COM, 3 NC**; both pins of each relay contact connect through 2.8 mm routes on both outer layers. The main assembly remains 226 placements, 63 BOM lines and 11 hand-fitted parts.

R4 retains Sunlord L1 C36409 with corrected 1.10 × 3.70 mm pads, R2's no-paste footprint, R246's via escape, printed IC/transistor/diode pin-1 arrows, LED/diode cathode bars and C1's positive mark. The thirteen supplier orientation queries are covered by assembly-check.json and the top/bottom orientation PNG/PDF sheets in this folder. Those parts did not move.

The CPL retains 21 exact-part supplier angle corrections and recalculates body centres for the rotated relays and terminals. Do not repeat the historical viewer corrections. Actual supplier Top/Bottom DFM images have not been reviewed; compare them before production, including new relay poses. Component reservation, lead fit, solder coverage, process rails/fiducials/tooling, stencil acceptance and physical first-article checks remain pending.

[Layout record](../../compact-layout-2026-11-24.md) · [Current manufacturing review](../../dfm-review-2026-11-24/R4/README.md). Rebuild the matching bundle with `python3 tools/package_pcba_review.py` after its required release checks pass.
