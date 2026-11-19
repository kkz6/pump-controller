Guarded R2 electrical review
============================

The R2 prototype consists of the main PCB, the existing five-button OLED
panel, the two-layer signal receiver and the independent cabinet guard. In AUTO or front-panel MANUAL the
starter transfer is in HOST. In LOCAL the mechanical transfer isolates the
controller command contacts. Both positions share the same physical trip
path. The original starter still handles its motor, overload and capacitor
sequence. Preserve its original STOP circuit, adding a mechanically operated
NC contact on the same actuator for the guard.

Changes since the electrical audit
----------------------------------

1. **Missed electronic STOP.** A latched starter can keep running after both
   board outputs open. An external monitor now requires a changing heartbeat
   from valid control and protection samples. Loss of that signal removes
   power from the starter through two series contactors. Neither coil relies
   on an electronic STOP pulse or the main PCB to hold the motor off.
2. **Overflow after a broken probe common.** A separately wired, normally
   closed high-high float interrupts the cabinet guard in both transfer
   positions. Its cable does not share the tank electrode common. The
   float is mandatory. Main J31 receives the guard's isolated permit contact.
   A stuck float or a short across the float contacts still requires an
   additional independent sensor to detect. Mount the float low enough that
   the volume above it exceeds the measured water delivered during shutdown,
   including coast-down and any post-stop pipe flow.
3. **Welded output and restart.** The original STOP and overload directly
   interrupt the guard. In HOST the OLED STOP also withdraws a hardwired
   permission independently of K1. A single welded series motor contactor
   leaves a second means of interruption. Mirror contacts inhibit re-enable.
   Power restoration requires supervised reset, separate enable with neutral
   proof, and a fresh start. An upstream motor-feeder voltage contact covers
   loss of the starter supply while the controller or cabinet stays powered.
4. **Interchangeable field plugs.** J21 uses two-way JST XH and J31 uses
   two-way Phoenix MC 3.81. J36 uses five-way JST ZE and panel J8 uses
   three-way JST GH. Pin maps and footprint identities are checked in CAD.
   Verify actual cable dressing and physical rejection on the first assembly.
5. **Long local supply connections.** U11 has direct connections to its four
   high-frequency bypass capacitors. U20, U21 and U22 each have a local
   100 nF capacitor. The layout check follows the routed copper, measures its
   length outside the mounting lands and checks the ground paths in their
   proper voltage domains. The detailed report gives the measured endpoints
   and criteria. Each U11 pair measures 1.9702 mm combined at the modeled
   package terminations. Exposed supply traces to U20, U21 and U22 measure
   0.662, 0.969 and 0.675 mm respectively. The dense U11 layout assumes the specified Murata 0402
   capacitors and at most ±0.04 mm effective registration per component,
   including placement and rotation. Obtain that assembly capability or inspect
   the actual terminal locations on the prototype before accepting the lead
   lengths. The available tolerance is smaller than a typical hand-placement
   allowance. Assembled contactor-noise immunity needs measurement.
   See the `bypass report <../hardware/main-compact-dual/checks/bypass-routing.json>`_
   and the `isolator layout guidance, p. 29 <https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf#page=29>`_.

A wrong OEM command harness is another hazard from the original review.
The component rejects an uncommissioned guard or a requested profile that
differs from the separately recorded harness profile. A physical change
requires isolation, fresh proof of A/B functions and renewed commissioning.
The firmware has no electrical identification of the OEM loom.

Power return acceptance
-----------------------

Test with a disconnected motor and a low-voltage load first. Record the
actual signals and release times on the specific guard, starter and supplies.

* Interrupt the controller feed alone in HOST. The external monitor must
  release within the specified timeout. A stuck-high or stuck-low GPIO and
  a frozen panel bus must produce the same loss of permission.
* Interrupt cabinet power with the starter feeder present. Both independent
  contactors must drop. Restore the supply with RESET, ENABLE or START held,
  one at a time. The load must stay off.
* Interrupt the starter feeder while cabinet and controller remain powered.
  Repeat for any separately powered OEM control that can reset the starter.
  Reapply power in each order. Qualify the fastest undervoltage event that
  changes the OEM run state against the actual voltage-monitor response.
  If its timing or off-state cannot be verified, keep that model disabled.
* With AUTO selected, tank demand present and a previous run latched, restore
  power. Release of STOP, float return, RESET alone and restoration of
  feedback while ENABLE is already held must all leave the motor off.
  With commands released, perform a new guard ENABLE. Verify an additional
  fresh START is required. LOCAL must obey the same hardwired restart rules.
* Hold one command closed and restore the other proofs late. The change of
  a proof contact must never count as a new press. Repeat with one simulated
  welded power contactor, a bridged K1 and a bridged K2. Use an isolated
  test fixture for welded-contact simulation. Separately bridge the original
  starter's START or holding contact with its actuator released. A motor
  contactor can be physically off while that electrical demand remains active.
  Verify the OEM command-idle proof blocks enable until the bridge is removed.

A scanned keypad or starter that remembers RUN may lack an accessible,
independently meaningful off proof. The R2 profile is then ineligible for
that starter. An OEM internal auto-restart on restored supply must be
disabled and its state proven across a power cycle.

Verification records
--------------------

* `KiCad rule checks and source consistency <../hardware/main-compact-dual/checks/independent-summary.json>`_,
  `panel and cable <../hardware/main-compact-dual/checks/panel-integration.json>`_
  and `CAM checks <../hardware/main-compact-dual/checks/independent-gerbers.json>`_.
* `Straight-through guard cables and distinct field plugs <../hardware/main-compact-dual/checks/guard-looms.json>`_
  and `receiver fabrication checks <../hardware/guard-receiver/checks/cam-package.json>`_.
* An `independent check of the exported copper <../hardware/main-compact-dual/checks/gerber-copper-connectivity.json>`_
  found zero opens or shorts across 169 main-board nets and 35 receiver nets.
  It detected a cut on an inner main-board layer and both a cut and a short
  on the receiver in deliberately altered copies of the artwork.
* `Cabinet and receiver schematic <../hardware/starter-guard/guard-schematic.pdf>`_,
  `external guard BOM <../hardware/starter-guard/bom.csv>`_,
  `external contact and fault sequences <../hardware/main-compact-dual/checks/independent-starter-guard.json>`_
  and `guarded firmware tests <../hardware/main-compact-dual/checks/guard-firmware.json>`_.
  The latter include AUTO held over reboot, stale panel or process data,
  GPIO driver error and loss of a latching starter's STOP pulse. The separate
  `ESP32-C6 compile and link check <../hardware/main-compact-dual/checks/guard-target-build.json>`_
  exercises the target SDK with a disabled test application.
* `Guard assembly and manufacturer manuals <../hardware/starter-guard/README.rst>`_,
  `OEM interface drawing <../hardware/main-compact-dual/exports/starter-wiring.pdf>`_
  and `prototype enclosure <../mechanical/compact-dual/README.rst>`_.

Engineering release boundary
----------------------------

The nominal main-board gap from live to isolated copper is 8.060 mm across
all six layers. The starter command contacts are at least 9.425 mm from the
onboard mains and metering domain. On the separate two-layer receiver the
two low-voltage domains are at least 3.10 mm apart across both copper layers.

These records support fabrication and evaluation of a bare-board prototype.
The CAD and logic tests cannot establish a physical stop time, insulation,
noise immunity, wetting current, motor temperature or available fault current.
The PCB, monitor receiver and exact OEM starter require qualified electrical
review and supervised first-article tests. A working application must acquire
fresh metering and sensor data and enforce calibrated thresholds. Qualify
the pump's dry-run response, capacitor cutout, voltage dips, RF and contactor
transients, fuse coordination and closed-case temperature before unattended
operation. The permanent installation has no verified PL, SIL or enclosure
rating. The `previous electrical audit <compact-dual-electrical-audit.rst>`_
records the original measurements and remaining calibration and thermal work.
