Compact pump controller main board
=================================

The single-phase controller fits on a 100 x 75 x 1.6 mm, six-layer board. The
four isolated mounting points, grouped edge connectors, independent relay
contacts, metering and level-probe circuits are retained. Motor current flows
through the existing starter. The 60 x 45 mm two-layer user panel connects
through the existing keyed harness.

Circuit and layout changes
--------------------------

* The upper edge moved inward by 5 mm. The upper mounting holes moved with
  their copper keepouts. Their native centres are (16, 8.8) and (96, 8.8) mm.
  The lower holes remain at (4, 76) and (96, 76) mm. The board's upper-left
  corner is (0, 5) in those same KiCad coordinates.
* C1, the 47 µF/25 V Panasonic reservoir capacitor, now sits beside the
  isolated supply output on the front. A 5.68 mm long, 0.5 mm wide trace
  connects its positive pad to U1. The change makes the rear-mounted metering
  crystal the tallest modeled item on the back. The PCB area is 7,500 mm²,
  a 6.25% reduction. The modeled populated thickness falls from 35.18 to
  25.68 mm. Lead trimming, component tolerances, plugs and wire bends affect
  installed size. Measure C1 temperature beside the supply during load testing.
* U1 is a 6 W isolated AC/DC module, 25.4 x 25.4 x 16.7 mm. The
  electrical review budgets 5.81 W. The end product still requires thermal,
  mains insulation and switching-noise tests. The nominal minimum
  live-to-isolated copper spacing is 8.06 mm at the relay footprint. Review
  finished pad geometry and solder fillets against the 8.00 mm project target.
  See the `RECOM data sheet <https://recom-power.com/pdf/Powerline_AC-DC/RACM06E-K_277.pdf>`_.
* The optional AUTO-key input on J32 pin 12 now reaches U33 pin 21 (GPA0).
  MAN remains on J32 pin 11 to U33 pin 7 (GPB6). The harness label
  SPARE_B7 identifies the original wire. Firmware must read AUTO from GPIOA
  bit 0 and MAN from GPIOB bit 6, with the internal pull-ups on these two
  inputs disabled. U33 pins 8 and 28 (GPB7 and GPA7) are unconnected. Set both
  as outputs with their latches low during initialization. On a mode change,
  stop and disarm the controller. A fresh START is required. See the
  `Microchip pin advisory <https://support.microchip.com/s/article/GPA7---GPB7-Cannot-Be-Used-as-Inputs-In-MCP23017>`_.

Prototype files
---------------

* `KiCad project <pump-controller-compact.kicad_pro>`_,
  `PCB layout <pump-controller-compact.kicad_pcb>`_,
  `circuit diagram <exports/schematic.pdf>`_ and `parts list <bom.csv>`_.
* `Main bare-board Gerbers <pump-controller-compact-gerber-prototype.zip>`_,
  `separate stencil <pump-controller-compact-stencil-prototype.zip>`_ and
  `package checksums <package-manifest.json>`_.
* `Native checks <checks/independent-summary.json>`_,
  `copper and hole geometry <checks/independent-geometry.json>`_,
  `critical signal routing <checks/signal-return-paths.json>`_ and
  `parsed manufacturing files <checks/independent-gerbers.json>`_.
* `Populated board preview <../../output/compact/pcb-preview.png>`_,
  `STEP assembly <exports/pump-controller-compact.step>`_ and
  `model dimensions <exports/model-verification.json>`_.
* `Hardwired stop and relay checks <checks/hardwired-control-review.json>`_ and
  `main-to-panel checks <checks/panel-integration/integration-review.json>`_.
* `Interactive OLED, buttons and cable view <../../output/compact/panel-connections.html>`_
  and `connection preview <../../output/compact/panel-connections.png>`_.
  Follow the 12-way panel lead from J32 on the main board's right edge to J1
  on the rear top edge of the button panel. The separate 4-way display lead
  connects J7 on the rear right edge of the panel to the OLED.
* `OLED/button panel <../panel-rev-e/README.rst>`_ and
  `connector assignments <../../design/rev-e-integration.rst>`_.
  The board-side key input assignment above supersedes the Rev E GPIO assignment.

Fabrication uses green mask, white silkscreen, ENIG, 1 oz outer copper,
0.5 oz inner copper and a proposed 1.6 mm FR-4 Tg155 stackup. Submit the
panel as a separate design. Ask the fabricator to confirm the stackup,
relay-pad tolerance and electrical test against the supplied IPC-D-356
netlist. Robu lists special pricing for individual boards up to 102 x 102 mm.
The exact four-layer and six-layer prices for five boards, tax and delivery
are unquoted. `Robu manufacturing service <https://robu.in/product/online-pcb-manufacturing-service/>`_.

The two inner reference layers each carry uninterrupted copper within their
own live or isolated domains. Four-layer routing trials and the 8-bit input
expander alternative are recorded in the
`size and layer comparison <../../design/compact-layout-comparison.json>`_.
Six layers provide routing space around the two reference layers. The
demonstrated size savings come from placement and the revised board outline.

Use the compact manufacturing package only for engineering prototypes.
Pump operation, firmware, cabinet fit, heat, immunity and insulation
qualification remain untested. The earlier standalone enclosure has a
different upper mounting pattern.
