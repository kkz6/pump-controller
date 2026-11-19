R3 service gate and trapped-key interface
=========================================

The R3 main board has a front-mounted GCT USB4110-GF-A service receptacle. This cartridge adds a captive, laterally translating stainless blade at its mouth. The same rigid carriage moves an Omron D4DS-K1 actuator in the D4NS-4BF switch, SG1, and the single-window striker for access lock AL1. Both direct-opening NC contacts remove their respective electrical permissions when the carriage opens. The separate motor-feeder isolator QISO1 and matched commercial access lock AL1 enforce isolation before USB can be reached.

Installed operating sequence
---------------------------

* Apply STOP and open QISO1, upstream of both the original and auxiliary motor contactors. QISO1 releases its unique key only in the positively isolated OFF position. The corresponding lock AL1 accepts only this key. Key-controlled AUTO/MANUAL selection, transfer accessories and SG1 use separate mechanisms.
* Retract AL1's bolt with the key, which remains trapped in AL1. Move the carriage from RUN to SERVICE. The SG1 tongue withdraws on the straight guide before the plug opening appears. Connect the USB cable on either roll orientation through the single isolated tunnel. The hardware keeps the motor feeder isolated while USB is in use. Where motion presents a hazard, confirm the installed pump has come to rest before access.
* Remove the plug fully. Push the blade back to the independent RUN stop. The bolt can extend fully through its single strike hole into the stationary keeper only here; only full extension releases the key. Return the key to QISO1. Restore the motor feeder under the separate reset and restart policy. On the bench, use a disconnected motor feeder.

Drawings and machining
----------------------

`service-shutter-sections.svg` shows the sequence and geometry. `usb-service-closed.step` and `usb-service-open.step` contain fixed and moving custom parts, actuator/socket envelopes and a local PCB section. `custom-fixed-parts.step` and `custom-moving-carriage.step` isolate the two fabricated assemblies. All STEP locations are assembly coordinates in mm. Separate 1:1 DXF files contain case-X/vertical-Z profiles for five flat parts, with distinct cut, locator, clearance and tapping layers. A laser-cut tap pilot still requires tapping. Buy the actual Omron and trapped-key devices.

Use the existing case origin, with X = 112 − board y and Y = 125 − board x. The PCB underside is at Z24 and its front at Z25.60. The actual KiCad J40 Fab rectangle ends at native x100, centred on y20. GCT places the mating axis 1.68 ±0.20 above PCB front. The nominal case mouth is (92, 25, 27.28), facing −Y. The case wall is at Y0. Place the machine's isolated service passage on this side. Only the continuous 16 × 9 bore reaches the receptacle. All slide linkage and switch wiring are enclosed behind a fixed tool-fastened cover. The captive handle's restricted slot has a moving metal overlap plate.

The cartridge is a metal-fabrication prototype for a revised enclosure. Its outer switch/strike guard spans X−2 to 170, Y−54 to 0, Z46 to 90 mm before the vendor's external lock body or conduit clearance. Reserve space for the purchased lock, cable entry, fasteners, tool sweep and removable covers. The original compact R2 guard and printed case have neither this passage nor this envelope. Relocate the old near-wall mode-key gland from the switch/lock zone or use a separate enclosure bay for the complete cartridge. Close and segregate all alternate entry paths to J40. The supplied STEP depicts this cartridge and its interface only. Full enclosure fit, bonding, touch access, ingress and mains segregation require review of the completed enclosure. The cartridge is excluded from plastic print orders.

=========  ======================================================================
Part       Material, sizing and assembly
=========  ======================================================================
Blade      0.60 ±0.03 thick stainless 301 half-hard, 46 × 20. Break and polish edges. Attach rigidly to the moving drive. Check flatness after assembly.
Drive      3 mm steel crosshead and riser with welded joints, rigid return arm and tapped key plate, per STEP. Independent hard stops limit travel to 0 and 40 ±0.5. Secure guides against lift, rotation and fastener loosening.
Guides     Front guide, 0.30 rear retaining strips, guide rails and cartridge flange enclose the blade and restrain it in Y and Z. Gauge and shim to the actual connector at both ends of travel. Locate and mechanically pin after adjustment.
SG1        D4NS-4BF one-conduit body, D4DS-K1 key. Two M4 fixings, optional two locating studs and controlled stop. Top insertion along −X with no curved travel. Use manufacturer's mounting pattern, torques and wiring instructions.
AL1        Commercial trapped-key access bolt and supplier-matched QISO1. This interface assumes a 9.90–10.05 diameter solid bolt, single 10.60 mm strike bore (10.70 max), 5 mm steel plate moving between a fixed lock face and a 3 mm fixed rear keeper. Supplier must confirm engagement, housing mounting and captive-key release behavior.
Housing    Tool-fastened metal enclosure and mounting flange, 16 × 9 internal passage; preserve the independent motor isolator and SELV barriers. Guard and restrain gland, cable and handle. Bolt support and enclosure fastening depend on actual case structure.
=========  ======================================================================

The Omron key screw centres are 15.0 mm apart. Set the key fastening line against the switch body datum in Omron's top-insertion drawing to 55.75 ±0.50 at the RUN hard stop, within the 54.5–57.0 mm window. The STEP uses datum X65 and screw line X120.75, with z57.5 and z72.5 screw centres. Locate the purchased body-and-key pair on a jig before drilling permanent dowels. Keep transverse misalignment below 0.5 mm, within the published 1 mm limit, and confirm backlash, alignment, weld/wear and fastening effects. Mount with tamper-resistant retained fasteners. Use 2.4–2.8 N·m for key fasteners and 0.5–0.7 N·m for the switch body. The switch and USB plug are never travel stops. Handle/striker loads are carried by guides, frame and hard stops.

Set AL1's bolt axis at X52/Z65, parallel to Y. In the dimensioned arrangement the strike occupies Y−49 to −44 and the keeper Y−43 to −40; require the locked tip to reach Y−40.7 or farther into the keeper with the strike fully engaged. Require a retracted tip at or short of Y−50.5. Only the extended bolt may release the service key. Require the selected lock to seat completely in a fixed adapter that seals the cover opening. Verify the supplier's locking stroke, body envelope, retention force, tamperproof mounting and end-position tolerances against this interface. Obtain a correctly matched QISO1 and AL1 set before machining the lock adapter. Other bolt diameters require a matching plate/keeper redesign and rerun of the two checks. No carried lock or loose key substitutes for this interlock.

Axial and travel acceptance
---------------------------

Set the blade centre 0.95 mm forward of the installed receptacle face. The budget permits ±0.18 for fitted location, ±0.08 axial guide play and ±0.10 for loaded flatness. With blade thickness tolerance this leaves at least 0.275 mm to the receptacle and 0.225 mm to the end of GCT's 1.85 mm minimum exposed mated-shell zone. The metal blade therefore intercepts the plug's shell while it is seated regardless of cable overmould shape or the two mating orientations. Inspect the full swept face under load. Reject housings that allow tail-entered, angled or side access around the blade. Qualify each supported cable and its bend at the assembled passage.

At worst case the SG1 positive opening is complete by 13.1 mm of carriage motion. This includes its published 10 mm opening travel, full 2.5 mm insertion window and 0.60 mm lost motion. Earliest aperture visibility is 17.3 mm. A returning gate contacts a retained plug before reaching 24.7 mm. The return cannot reach the possible SG1 remake region or AL1 key-release position with the plug seated. The key-release window is at most 0.7 mm from the closed stop. These mechanical bounds establish sequencing. Actual relay dropout and rotor rundown take additional time. Installed service relies on QISO1/AL1 before moving the gate.

Evidence and first article
--------------------------

`check_j40.py` reads the native port outline and direction. `check_kinematics.py` evaluates worst-case dimensions and targeted failing examples. `check_solids.py` steps the OCC assemblies across ten travel positions, checks retained-plug corners, and verifies obstruction of a projected AL1 bolt at seven off-position samples. Reports sit alongside the scripts. The 3D model approximates purchased components and omits vendor-specific lock hardware, fasteners, wiring and mounts to an actual machine.

Before field use, record the supplied QISO1/AL1 key codes, body and bolt dimensions, and the supplier's release logic. Fixture-test both SG1 contacts with a continuity logger; record each opening and closing point under tolerance, lateral and end loads. Verify the specified direct-opening force and allowable operating speed per Omron; the structure must transfer direct-opening force even in the worst case. Record gauge measurements on the installed J40 and slide, shell engagement and key retention through attempted closure with different cables, both orientations and partial insertion. Check that pulling the trapped key with shutter open, opening the cover with QISO1 ON, restoring QISO1 while the plug is seated, or defeating one SG1 channel cannot energize the motor. Verify contactor dropout, safe state of the original STOP/high-high chain and the fresh-start requirement with a qualified commissioning team. Physical prototype and installation tests remain outstanding.

Manufacturer drawings and system description
-------------------------------------------

* Omron D4NS/D4NS-SK, pages 5, 7, 8, 10 and 12. https://assets.omron.eu/downloads/latest/datasheet/en/d4ns_d4ns-sk_safety-door_switch_datasheet_en.pdf
* GCT USB4110 drawing, sheet 1, including B4 mating section. https://gct.co/files/drawings/usb4110.pdf
* Fortress trapped-key system sequence. https://fortress-safety.com/news/understanding-trapped-key-systems/
