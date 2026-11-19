Intermediate layout validation
==============================

These reports record superseded placement stages and an intentional positive
control test of the reinforced-isolation DRC rule. The positive-control copy
raises the required clearance from 8 mm to 9 mm and is expected to fail.
Use hardware/checks/main-drc.json and layout-summary.json for final status.

The checks/ directory contains transient routing and cleanup reports. Their
nonzero counts describe superseded states. The fast router session and
pre-route DSN are historical inputs; importing them into the final native
board would discard later checked repairs. Accepted local repair patches
are retained for review and must not be replayed on the already repaired
final board.
