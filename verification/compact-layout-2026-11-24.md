# Compact R4 layout

R4 reduces the main board from R3's 100 × 139 mm to **100 × 118.5 mm**: 20.5 mm less height and approximately 14.7% less area. Width and six-layer construction are retained.

K1 and K2 now lie horizontally in the lower bay. J30/J35 point out of the bottom edge; physical pin 1 remains NO, 2 COM, 3 NC. J20 tank and J21 inlet headers moved to the top edge and retain their original electrical pinouts. USB-C J40, BOOT/EN, panel connector and J41 bench supply remain accessible.

## Alternatives examined

Keeping the sensor headers and both relay outputs along the lower edge required a taller staggered arrangement. Moving the relay terminals to the actual left edge also requires space for both wire-insertion paths and for the contact routes. An internal left-facing block between side-by-side relays points toward the adjacent relay body. These trials were not released. The chosen arrangement follows the user's preference for the smaller board and opposite-edge sensor ports.

## Electrical and mechanical scope

The schematic's electrical connections and component selections are unchanged from R3. Coil, probe and supply traces were rerouted, unused routing tails removed, and supply/ground connections restored around the relocated headers. All six contact nets still join exactly their two relay contact pins and one field terminal, use both outer copper layers at 2.8 mm width, and have no separate power-path vias. The 8 mm LIVE-to-control clearance and creepage targets remain enabled. No internal motor-feed/CT integration was added.

Four nylon mounting holes are now at (4, −10.5), (96, −10.5), (96, 100) and (4, 100) mm in KiCad coordinates. The outline spans x = 0…100 and y = −14.5…104 mm. Matching mount exclusion zones move with the holes. Existing enclosures must use the new dimensions and hole positions.

R4 retains the L1 pad correction, R2 no-paste footprint, R246 via escape, all orientation and polarity marks, and exact-part JLC CPL corrections. Updated CPL package centres account for the relay/terminal rotations. Current evidence is under the dated review directories' R4 subfolders. The self-contained R3 ZIP and pcb-r3 tag remain historical releases.

## Validation and limits

The matching R4 package is produced only after ERC, complete DRC including 8 mm creepage, schematic parity, CAM connectivity and deliberate CAM fault controls pass. Manufacturing, assembly, polarity, interface and exact package/placement checks are recorded with the source hashes. Host firmware tests exercise simulated hardware only.

These checks do not approve unseen supplier placement previews or qualify insulation, thermal rise, motor/capacitor switching life or EMC on physical hardware. JLC component reservation, lead fit, solder coverage, tooling/stencil review and first-article bring-up remain pending. No supplier upload, purchase or production approval is performed by this revision.
