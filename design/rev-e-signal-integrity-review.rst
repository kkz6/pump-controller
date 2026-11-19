Rev E signal and analog layout review
====================================

This is a layout assessment, not an electrical or EMC qualification. The
six-layer arrangement reserves In1.Cu for the separate GND/M_GND domains and
In4.Cu for the separate +3V3/M_GND domains. The final, hash-bound trace lengths,
plane coverage and layer use are recorded by
``tools/measure_rev_e_return_paths.py`` after routing and zone fill.

USB service interface
---------------------

R27/R28 are on the module face with equally short connections to the USB pins.
The service connector keeps its existing numeric pinout. A short In2.Cu
crossover uses the same number of signal vias on D+ and D-, with nearby ground
stitching. Neither reserved reference plane is used for signal routing.

The proposed 0.20 mm track width and varying separation at the resistor,
crossover and connector transitions do not establish 90-ohm differential
impedance. That requires the fabricator's actual six-layer stackup and an
impedance calculation or field solver. The 2.54 mm service header and its cable
also introduce discontinuities. Cable length, shield/return arrangement and
USB enumeration must be checked on the assembled unit.

Espressif recommends parallel, length-matched USB routing with a continuous
reference, limited via transitions and nominal 90-ohm differential impedance:

* https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/pcb-layout-design.html
* https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c6/schematic-checklist.html

Metering clock and local bypass
------------------------------

The existing 3.579545 MHz, 18 pF crystal and two 27 pF load capacitors remain
specified. Both clock traces and the load capacitors use the ADE7953 face,
with no clock signal vias. M_GND on In4.Cu supplies the adjacent reference.
Direct local ground connections join the ADE ground pins and exposed pad.
The HC49 package forces a longer path around the IC; this is a packaging
compromise that still needs oscillator startup and stability measurements.

The crystal's specified load is not equal to the individual capacitor value.
Two equal 27 pF capacitors contribute 13.5 pF in series before pin and board
parasitics. Actual loading, frequency error and startup margin therefore need
measurement; the layout does not prove the 18 pF target is met.

C47 is the local 100 nF VDD bypass. Its fixed route should be checked together
with its ground return, not only the distance from its body to the ADE. A
short power connection with a remote return would leave a large bypass loop.
The final CAD retains off-pad holes and a direct return to the local ADE
ground structure. C43 is the smaller VINTA bypass and must stay closer to the
IC than the associated bulk capacitor C42.

Analog placement limitations
----------------------------

Several remaining components are not immediately adjacent to their ADE pins.
Straight-line signal-pad distances in the retained placement are approximately:

=================  ==================  ========================
Component          ADE destination     Pad-to-pad distance (mm)
=================  ==================  ========================
C45, REF 100 nF     REF, pin 13         7.4
C51, VP filter     VP, pin 12          5.1
C52, VN filter     VN, pin 11          6.5
C53, IAP filter    IAP, pin 5          8.3
C54, IAN filter    IAN, pin 6          7.7
=================  ==================  ========================

These distances are lower bounds on the routed paths; they are not measured
loop inductances or evidence of adequate noise rejection. REF, VINTA and
VINTD decoupling order, current-input path symmetry and the routing from each
filter capacitor to the ADE deserve particular attention in the final copper.
A continuous ground plane reduces return-path disruption but does not make
these analog connections electrically equivalent to close placement.

The ADE7953 layout guidance places the small ceramic bypasses closest to the
supply/reference pins, connects its grounds directly to the exposed pad and
uses ground around the clock network:
https://www.analog.com/media/en/technical-documentation/data-sheets/ade7953.pdf
(section ``Layout Guidelines'', pages 68-69).

Required prototype evidence
---------------------------

Before relying on load-based dry-run decisions, measure voltage, current and
active power against a reference instrument over representative pump loads;
check repeatability and false trips during contactor switching. Confirm clock
startup over the intended supply and temperature range, and evaluate ripple
at VDD, VINTA, VINTD and REF using a suitable measurement setup. Calibration
cannot by itself establish immunity to switching noise or unstable clock
startup. USB, thermal, RF, EMC and wet/dry-run behavior remain separate tests.
