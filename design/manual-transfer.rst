Manual override for the starter's original buttons
==================================================

One keyed service socket selects who can command the pump. In **CONTROLLER**
the replacement controller has access to the starter's command inputs. In
**LOCAL MANUAL** the original starter buttons operate even with the replacement
controller unpowered or its command relay contacts welded. The mode button,
optional key, saved AUTO setting and wireless requests have no authority over
that physical selection. A loss of controller power alone must never select
LOCAL MANUAL.

Four-contact adapter for an open-to-stop DOL starter
----------------------------------------------------

The `editable KiCad schematic <../hardware/manual-transfer/manual-transfer.kicad_sch>`_
and `drawing <../hardware/manual-transfer/manual-transfer.pdf>`_ show one fixed
socket and two alternative mating assemblies. A technician fits either the
CONTROLLER harness or a passive LOCAL MANUAL insert with the pump stopped,
all supplies isolated and absence of voltage verified. Only one assembly
fits at a time. Use a keyed, shrouded, retained connector with touch protection
on both accessible halves and ratings for the actual control circuit. The
connector carries starter control signals only. Its voltage can be mains.

================  ===============================  =============================
Adapter cavities  CONTROLLER harness               LOCAL MANUAL insert
================  ===============================  =============================
1 and 2           Independent START relay contact  Both open
3 and 4           Series controller permission     Internal insulated link
================  ===============================  =============================

The cavity numbers belong to this adapter design. The local link restores
only the section of the original control loop occupied by the added
controller permission. It cannot bridge the original START, STOP, overload
or any required independent protective contact. The original START and
holding branch stays intact. All external automatic-start sources must be
accounted for when tracing that branch. Removing the controller harness
disconnects its entire START and permission circuits, including a contact
stuck closed. An empty socket opens permission in the illustrated DOL circuit.
The existing J30, panel JP1, float J31 and mode-key J8 have different functions.
None is the manual transfer socket.

Mode indication and protection
------------------------------

The physical transfer selects the command path without electronics. For a
powered controller, provide two independent position indications on the
isolated logic side, actuated by a fully seated, coded plug. Keep these
contacts electrically separate from all four field cavities. Indication
of LOCAL alone means display **LOCAL MANUAL**, continue available telemetry
and discard all pump commands. Indication of CONTROLLER alone permits the
normal arming sequence. Neither or both indications means **CHECK PLUG** and
inhibits controller output. On return to CONTROLLER, discard outstanding
requests and require a fresh deliberate arm. Plug-position indication is a
requirement for the next controller revision, separate from the optional
AUTO/MANUAL key input.

The original hardwired STOP, overload and start-capacitor mechanism remain
effective in both positions. Any additional operator button marked STOP and
any high-high or dry-run trip required in LOCAL MANUAL need a hardware path
independent of the replacement board or equivalent verified starter
protection. On the current boards, panel STOP and J31 act through K1.
The software dry-run trip, high-level stop and remote STOP cannot stop the
pump through a disconnected controller. Enable attended local operation only
when all protections required for the installation work in that position.
A welded starter power contactor is a separate fault that the plug cannot clear.

Transfer and return to service
------------------------------

With the correct independent protections operating, verify that a fresh
local START runs the pump, local STOP drops it and releasing STOP leaves it
stopped. Repeat with the controller unpowered and its START contact simulated
stuck closed on an unpowered or isolated test fixture. Then test restoration
of supply, resetting overload and returning to CONTROLLER, including a held
original START. Ordinary three-wire holding contacts alone can restart on a
held START. Qualify the starter's release-before-restart function or add
independent anti-restart protection where that test fails.

The `contact continuity model <../tools/check_manual_service_plug.py>`_
checks all 128 combinations of the modeled DOL contacts and all 16 button
combinations for a separate electronic keypad, each in three plug positions.
It also exercises STOP and release after a welded controller START and
demonstrates the held original START limitation. With KiCad CLI available,
the same tool independently compares the exported schematic netlist with the
expected fixed wiring, harness and manual insert, including both unused START
cavities. Run ``python3 tools/check_manual_service_plug.py -v`` from the
project root. The `KiCad electrical-rule report
<../hardware/manual-transfer/erc.rpt>`_ records zero errors and warnings.
The schematic and calculations cannot establish contact ratings, connector
assembly, switch timing, run feedback or the actual starter response.

An electronic starter with momentary START and STOP inputs needs a different,
incompatibly keyed adapter. In LOCAL its original keypad must work and both
controller command pairs must be physically disconnected. Applying the
DOL link to a keypad pair could hold a command or enter a settings menu.
An electronic starter can keep running with both pairs open. Confirm its
supported stop/inhibit and power-restoration behavior for the exact model.
Any automatic-start or retry inside the starter itself must also be disabled
and stay disabled after a power cycle before this position can be called
LOCAL MANUAL.
The adapter drawing is an engineering design for review. No connector
rating, physical installation or updated main-board fabrication release has
been qualified.
