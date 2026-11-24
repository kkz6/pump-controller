# R3 PCBA correction review - SMT026112161707_Y2

Updated 2026-11-24. The native relay redesign is implemented. The held order has not been fabricated. Request **Replace File**, upload the complete matching R3 set and have JLC review the revised placement previews before production approval. No external message, purchase or order action has been performed.

The final [PCB manufacturing review](../dfm-review-2026-11-24/README.md) also moves R246's supply via outside its paste land, removes the DNP R2 stencil openings and aligns the revision metadata. The order checklist now explicitly requests JLC-supplied Standard-PCBA tooling. Regenerate the review bundle after the checks with `python3 tools/package_pcba_review.py`.

## Revised hardware

- K1/K2: Omron G5RL-1-E-HR DC5 high-inrush SPDT, C1563288, included in JLC assembly. Component ratings: 16 A NO / 5 A NC at 250 V AC resistive.
- J30/J35: Phoenix 1711738 / C91156 fixed three-way power terminals, included in JLC assembly. **1 NO, 2 COM, 3 NC.** Old mating plugs are obsolete.
- Eight 1.3 mm relay holes; both physical pins of each contact connected. All six field paths use 2.8 mm copper on both outer layers, without a separate small via carrying field current.
- Q50/Q51 and R246–R248 supply K1 separately from the panel STOP sensing loop. The panel switch no longer carries the relay coil current. The existing U42 current limit, low-side arm/watchdog gate and USB inhibit are retained.
- Main outline is now **100 x 139 mm**, 22 mm taller. The two upper corner holes moved; the centre mount was removed. USB-C J40, BOOT/EN recovery and J41 bench supply are retained.
- 226 JLC placements, 63 BOM lines, 11 hand-fitted parts. Exact new relay reservation/lead time still needs JLC confirmation.

Detailed circuit changes, ratings, remaining application qualification and primary sources: [relay revision report](../relay-upgrade-2026-11-24/design-status.txt).

## L1 land correction

Retain **Sunlord SWPA4030S2R2MT / C36409**, 2.2 uH. The former Würth land was a mismatch. The corrected `Inductor_SMD:L_Sunlord_SWPA4030S` uses two 1.10 x 3.70 mm pads at X +/-1.50 mm: 3.00 mm centre spacing, 1.90 mm gap and 4.10 mm overall copper span. L1 remains BUCK_SW to +3V3; it is non-polarized.

Source: Sunlord SWPA1102230000 Rev.11, page 4, Fig.4-1/Table4-1. [Detailed manufacturer specification](https://www.alfatec.de/fileadmin/productfiles/datasheets/sunlord_swpa4030s_series.pdf). The L1 3D model is a nominal body envelope.

## Orientation and CPL corrections

Both supplier query lists are covered by printed pin-1/cathode marks and the native pin-net checker:

| Side | References | Expected physical reference |
| --- | --- | --- |
| Top | U22, U33, U21, U2 | Pin 1 upper-left in the supplied top-view sheet |
| Top | D35 | Cathode band left; pad 1 K = INTERLOCK_OK |
| Top | U3 | Antenna edge left; pad 1 near lower-left. Corner GND pad 53 is separate |
| Bottom | U10, U20 | Pin 1 lower-right in the X-mirrored bottom-view sheet |
| Bottom | U31, U37 | Pin 1 lower-left in that bottom view |
| Bottom | D31, D32 | Cathode band right in that bottom view; D31 cathode is now K1_5V |
| Bottom | D30 | Cathode band bottom in that bottom view |

`assembly-orientation.png/.pdf` and `assembly-orientation-bottom.png/.pdf` show the expected **physical** pad orientation. Their coordinate labels remain native KiCad coordinates (Y down). Register the board outline before comparing a rotated or mirrored supplier image.

**Automatic supplier corrections:** all 21 JLC viewer rotations recorded in `manufacturing/order-checklist.md` at commit `a4e8bbc` are now in `tools/data/jlc-placement-corrections.json`. `tools/prepare_jlc_assembly.py` applies them to the CPL with exact MPN, footprint and side guards. The physical KiCad footprints are not rotated. The four new through-hole parts also have guarded, nominal package-centre CPL offsets, so a coil/first-pin datum is not incorrectly used as the pick point. Clockwise 90-degree viewer corrections are encoded as -90 and counterclockwise as +90 under JLC's positive-counterclockwise convention. **Do not repeat the old manual viewer corrections on this new CPL.** The native assembly checker now checks these recorded angle offsets as well as positions and sides.

JLC's angle convention: [Pick & Place File requirements](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly). Supplier libraries can change, so compare the revised DFM again, particularly the new relay and transistor models. New Q50 requires G1/S2/D3; Q51 requires B1/E2/C3. U3's native footprint datum (66.50,29.00 mm) differs from its body centre (65.85,29.00 mm); align the actual pads, not an assumed body centroid.

The supplied email link was inspected and contains only an attachment-list screenshot, not the actual Top/Bottom placement images. Therefore the supplier's actual proposed placement has not been approved. Source references for the thirteen parts are recorded in the orientation check and the previous review's linked datasheets.

## Release checks and deliverables

- `manufacturing/verification.json`: ERC, full DRC including parity/creepage, Gerber/drill connectivity and deliberately injected fault controls. Source/output hashes bind the release to its native design and assembly-correction data.
- `assembly-check.json`: L1 and all thirteen queried orientation pin maps, physical coordinates, sides and corrected CPL rotations.
- `../relay-upgrade-2026-11-24/relay-check.json`: eight-pin relay geometry, both pins of each contact, terminal order, dual-layer field paths, STOP supply and exact JLC BOM selections.
- `../relay-upgrade-2026-11-24/r3-interface-check.json`: 291 main and 45 panel named terminals, with all 190 main copper nets assigned to exactly one isolation domain.
- `../relay-upgrade-2026-11-24/firmware-profile-check.txt`: existing host profile tests. These use simulated hardware and do not validate physical coil or capacitor behavior.
- `assembler-reply-draft.txt`: unsent Replace File request and supplier review instructions.
- `pcba-correction-review-package.zip`: latest revised main fabrication/assembly files, review notes and orientation sheets. Superseded replacement-part BOMs are excluded.

The initial local R2 snapshots and `existing-order-*` files are historical only. They are not the R3 release and were not independently retrieved from JLC's uploaded order.

## Application limits

The redesign is complete as an engineering prototype. The user's actual 1.5 HP / 220 V starter still needs its capacitor-disconnect function, switching waveform, temperature rise, STOP/overload, power-loss and welded-contact behavior checked. Relay and terminal current markings do not qualify arbitrary capacitor switching or establish a continuous board-current rating. Production approval of actual DFM images and first-article application qualification remain separate from generating correct revised files.
