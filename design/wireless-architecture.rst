Wireless architecture and firmware variants
==========================================

Native Zigbee is the primary firmware target. Matter over Thread and Matter
over Wi-Fi remain alternative targets on the same ESP32-C6-MINI-1U-H8 hardware.
Exactly one operational transport is selected per firmware build. These are
design targets: no pump application, radio adapter, commissioning flow, update
service or interoperability test has been implemented. The machine-readable
plan is ``wireless-variants.json``; it is not an SDK configuration or build file.

The ESP32-C6 supports Zigbee development through Espressif's Zigbee SDK [1].
Espressif's Matter SDK supports the C6 for Matter over Thread and Wi-Fi [2].
Hardware support alone does not demonstrate that this application fits in
flash/RAM, meets control deadlines, or pairs with a particular hub. Pin the
SDK/ESP-IDF revisions and record reproducible builds during implementation.
No simultaneous Zigbee/Thread/Wi-Fi operation, runtime protocol switching or
transparent migration of network credentials is specified.

Aqara M200 and Apple Home
------------------------

The M200 provides a Matter controller, Thread border router, and a bridge for
Aqara Zigbee devices [3]. Its published FAQ excludes third-party Zigbee child
devices [4]. Therefore the custom native Zigbee controller has no supported
direct M200 pairing path. Owning an M200 does not remove the need for a
coordinator that explicitly accepts this custom Zigbee device when selecting
the primary Zigbee build. A compatible coordinator/profile remains to be
selected and validated. Do not impersonate an Aqara product identity.

Matter over Thread is the planned integration path for using the M200 with
this controller; Matter over Wi-Fi is an alternative. Both still require a
supported endpoint/device type, commissioning and testing on the actual hub
firmware. Apple Home integration is planned through a Matter build, with a
compatible Apple home hub; native Zigbee is not directly an Apple Home
accessory. An independently validated external bridge could be a later
integration project, but no such bridge is included here.

Matter runs over local IP networks, including Thread and Wi-Fi [5]. Routine
local commands must work without WAN after commissioning while the necessary
LAN, border router/controller and power remain available. Account setup,
remote access, some voice services and vendor update delivery may need internet.
The local pump state machine, buttons, OLED and protection must work without
any network. No Zigbee-to-Matter conversion occurs inside this controller.

Control and reporting contract
------------------------------

Every adapter submits authenticated, typed requests to the same local control
state machine; only its output service writes RUN_CMD, PERMIT_D and ARM_CMD.
No radio callback, diagnostic API or dashboard may write relay GPIO directly.
STOP, high-high, overload, fault latches, sensor validity and configured dry-run
checks retain their authority regardless of transport. A mode change cancels
run demand, stops/disarms and requires the prescribed physical STOP/release
and fresh START sequence. Rejoining a network or receiving a replayed/late
command must not re-arm the pump. Network loss alone must not create a new
run request or restart; independently armed AUTO still follows local levels
and protection, and accepted OFF stays cancelled until a fresh accepted request.

Expose enabled request, selected mode, actual measured run state, inhibition
reason and freshness separately. An ON request is permission to request local
operation, not evidence that the motor runs. A full tank may keep an armed
AUTO pump off. The OLED supplies detailed water band, volts, amps, real power,
validity and fault information in every build. Five probes do not provide
continuous level precision: any litre estimate depends on the configured tank
geometry and electrode bands and must indicate its uncertainty.

For native Zigbee, define and test an on/off request endpoint plus telemetry
reporting with the chosen coordinator. Standard versus manufacturer-specific
attribute mapping remains implementation work. For Matter, select supported
endpoint types and test controllers' visible attributes. Do not promise native
Apple Home/Aqara tiles for arbitrary litres, voltage, current and power values.
The optional local browser dashboard belongs to the Matter/Wi-Fi build; it is
not a promised service in the Zigbee or Thread images. OLED and USB service
remain the common local interfaces. This does not require a cloud server.

Updates, variant selection and acceptance
----------------------------------------

A variant change is an explicit service operation with the pump stopped and
unarmed: install a compatible signed image, verify/migrate configuration,
recommission that transport and require fresh physical START. Keep meter/probe
calibration separate from network state. Never silently reuse Zigbee keys as
Matter fabric credentials or delete calibration during pairing reset.

USB recovery is required for every image, subject to the documented security
fuse policy. The Wi-Fi image may later provide an authenticated local update
page; Zigbee or Matter OTA require their own implemented server/coordinator
support and signed-image validation. None of those OTA paths exists yet.

Before a target is labelled functional, demonstrate its actual SDK build,
signed image size, RAM and task deadlines, USB recovery, rollback, correct
commissioning/removal, fresh telemetry and permissions. Test dummy relay loads
with repeated/late ON, OFF, mode changes, physical STOP, open high-high, stale
sensors, radio loss, hub loss, WAN loss, restart and interrupted update. Run
meter/probe/display and RF concurrently to prove the local timing budget.
RF, mains interference, enclosure antenna location and full motor validation
remain separate prototype checks. No certification or hub acceptance is implied.

Sources checked 2026-11-19
-------------------------

[1] Espressif Zigbee SDK, ESP32-C6 introduction:
https://docs.espressif.com/projects/esp-zigbee-sdk/en/latest/esp32c6/introduction.html

[2] Espressif Matter SDK, platform support:
https://docs.espressif.com/projects/esp-matter/en/latest/esp32c6/introduction.html

[3] Aqara M200 product specification and controller/bridge roles:
https://www.aqara.com/us/product/hub-m200/

[4] Aqara UK M200 FAQ, child-device support restriction:
https://www.aqara-shop.co.uk/product/aqara-hub-m200/

[5] Connectivity Standards Alliance, Matter and local connectivity:
https://csa-iot.org/all-solutions/matter/matter-faq/
