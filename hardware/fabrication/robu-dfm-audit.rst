Robu manufacturing-rule audit
============================

19 November 2026. Revision C, 90 x 70 mm, four copper layers, 1.6 mm overall
thickness. Native PCB SHA-256:
``6f991556083c578a128364c8498850fce7301d18344051a5d814eb829f6d0b85``.

Robu standard-service compatibility is **not established**. The native design
checks pass under the project's existing rules, but those checks are not a
substitute for the manufacturer's process acceptance. The source PCB and its
mains/isolation rules were not modified by this audit.

Published reference and interpretation
--------------------------------------

Reference: https://robu.in/pcb-manufacturing-capabilities/ (19 November 2026).

Robu lists multilayer via holes down to 0.20 mm and via outer diameters of
0.45 mm, with a 0.40 mm limit. Its separate annulus table is not fully consistent
with this limiting pair; clarify the applicable rule. The via/PTH-to-track
entries also need clarification as to whether they measure from the drilled
hole or from copper. Mask expansion is listed as 0.05 mm. Small printed legends
need at least 1.0 mm height and 0.153 mm stroke. These are manufacturer review
items, not accepted deviations.

Actual board geometry
---------------------

* 329 through vias: 23 at 0.40/0.20 mm outer/drill, 19 at 0.45/0.20 mm,
  and 287 at 0.55/0.25 mm.
* 42 nominal via annuli are below 0.13 mm; minimum is 0.10 mm.
* 52 plated footprint holes and two nonplated mounting holes. All holes are
  round; all 2,608 routed track objects are straight segments.
* Eight J2 header pads have a 0.175 mm minimum nominal annulus. The two U2
  thermal holes have a 0.15 mm annulus. These need process-specific treatment,
  rather than automatic enlargement near existing routing.
* All 655 mask-bearing footprint pads currently have 0.00 mm effective mask
  expansion. Mask openings must be reviewed against the selected process.
* SW3, SW4, SET and NEXT visible legends are 0.8 mm high with 0.12 mm stroke.
  Other reference text is hidden or not on silkscreen. These four items need
  enlargement or omission in a final manufacturing revision.

Independent round-hole/straight-track measurements
-------------------------------------------------

======================================= ===============
Measured edge-to-edge gap               Minimum (mm)
======================================= ===============
Different-net via hole to track         0.259873
Different-net via copper to track       0.151653
Different-net PTH hole to track          0.326700
NPTH hole to track                      1.798800
Different-net hole to hole              0.364026
Same-net via hole to hole               0.467423
======================================= ===============

Measurements include through holes and routed tracks; they do not include
filled zones or arbitrary pad copper shapes. Exact UUIDs/coordinates are in the
JSON report. Nominal dimensions do not include drill or registration tolerance.

Temporary KiCad checks
----------------------

Both checks used copies of the board/project, preserved the original mains and
8 mm isolation rules, and retained zero unconnected items. They did not save
changes to the source board.

A conservative copper-edge interpretation of via-to-track 0.254 mm and
pad-to-track 0.20 mm generated 499 clearance reports: 383 for the via rule and
116 for the pad rule. This interpretation has not been confirmed by Robu.

An alternative hole-edge interpretation, with additional drilled-pad and
hole-separation checks, generated 313 reports:

* 250 pad-to-track clearances below 0.20 mm.
* 44 drilled-pad-to-drilled-pad clearances below 0.50 mm.
* One PTH hole-to-track clearance of 0.3267 mm below 0.33 mm.
* 18 different-net hole separations below 0.50 mm.
* No via hole-to-track gaps below 0.254 mm.

KiCad classified 295 as errors and 18 as warnings using the copied project's
severity settings. Counts are reported DRC findings, not independent electrical
faults or a count of required edits. Different rule sets can change which rule
owns a reported pair. The JSON contains the exact second rule set and all
findings; the first added two clearance rules ahead of the unchanged native
mains rules.

Release consequence
-------------------

The manufacturing package may be used for Robu engineering review. Do not label
it ready to order. Robu must clarify applicable limits and accept the documented
fine-feature/via-in-pad process, or the board must be revised and all affected
exports and validation repeated. Filled and plated-over via treatment remains
an independent requirement from the existing via-overlap audit. A supplier's
bare-board electrical test also cannot validate controller firmware, pump dry-run
behavior, thermal performance, or installation in the starter.
