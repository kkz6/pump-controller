# Main PCB with replaceable pilot relays

Open `pump-controller-integrated.kicad_pro` in this folder. This revision derives from the integrated R4 design and retains its cabinet guard interface. It is a prototype for the relay change. Physical fit, service clearance and starter compatibility still require verification before ordering.

The relay edge projects 1.5 mm beyond the original outline between the relay positions. The overall cut outline is 100 × 117 mm. The four corner mount positions are preserved. The socket footprint includes its body and courtyard. The installed relay and retaining clip still need a physical cover and withdrawal check.

KiCad 10.0.8 reported zero schematic violations, zero layout violations, zero open connections and zero schematic-to-board discrepancies under the project's existing rules. Both coil polarities, diode connections, contact nets and 1.1 mm finished drills were also cross-checked against the socket and relay drawings. These checks cover the design files. The starter fault test below is outstanding. [Schematic check](checks/erc.json) · [Layout and connectivity check](checks/drc.json)

## Assembly and servicing

| Position on the main board | Fit at each position | Installation |
| --- | --- | --- |
| K1 and K2 | P6B-04P | Solder the four socket terminals to the PCB. |
| Into each socket | G6B-1114P-US-P6B DC5 | Plug in one relay. Specify the 5 V, non-latching socket version including the P6B suffix. |
| Over each relay | P6B-C2 | Fit one retaining clip. Allow space above the board for removal. |

The socket uses a 1.1 mm finished drill. With this relay, terminal 6 is coil positive, 1 is coil negative, 3 is contact common and 4 is normally open. The two coil-suppression diodes follow the new polarity. Keep the socketed contacts on a qualified starter control input. The manufacturer's low-level switching reference is 10 mA at 5 V DC. Check the actual electronic input current or contactor coil inrush, and the insulation rating of the complete relay/socket for the pilot voltage. A technician should isolate all supplies and verify discharge of the starter capacitors before opening the cover to service a relay. [Manufacturer drawings and specifications, pp. 3–4, 7, 10](https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6b.pdf)

## Restart behavior

The lowest additional parts cost is zero for a starter that already requires START to open and then close again after STOP. Qualify this on the exact starter and on the terminals used. A conventional seal-in contactor circuit accepts a continuously closed START path when its STOP supply returns. For that circuit retain the independent hardware restart inhibit. If a cheaper inhibit is substituted, it must interrupt permission on the original STOP or overload, reject a START held across release, reset or supply restoration, and require a fresh START. A timer expiring or a controller changing mode must never clear a held START. The socketed relay itself has one normally open output and provides no contact-position feedback. [Three-wire starter control](https://www.se.com/uk/en/faqs/FA147367/)

For a bench acceptance test, use a motor-disconnected test fixture with a visible contactor-coil indicator. Simulate the controller's START contact stuck closed. Check that a brief original STOP drops the contactor, that release leaves it off and that overload reset and power restoration also leave it off with the fault present. Repeat with the controller halted. After removing the simulated fault, confirm a separate valid START is required. The actual starter still awaits this test.

## OLED diagnostics using the existing current transformer

During controller operation, an independently observed STOP event starts the check. Fresh RMS current above a commissioned threshold after the measured release/measurement delay warrants **Current after STOP**. A verified off interval followed by current with no permitted local or automatic start warrants **Unexpected motor current**. Latch the fault and inhibit automatic starts until deliberate reset after inspection. In physical LOCAL, account for legitimate starts on the factory button. Missing or stale readings warrant **Current sensor unavailable**. A zero reading during STOP also occurs with a welded START contact. Identifying that fault before movement requires independent contact or command-path feedback. These messages specify proposed behavior. [ADE7953 metering functions](https://www.analog.com/en/products/ade7953.html)

The fabrication package includes the separate OLED panel, factory socket placement lists, post-assembly relay quantities, one-starter budget and archive verification. The external cabinet enable interface is still required on this revision. [Prototype fabrication and procurement files](../../output/socketed-r4/README.md)
