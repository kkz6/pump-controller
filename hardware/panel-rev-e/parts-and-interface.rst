Panel parts and pin assignments
==============================

The native BOM in ``bom.csv`` is authoritative for individual references.
No MCU, motor relay or AC/DC converter is fitted to this panel.

Main parts
----------

====================== ======== ==============================================
References             Qty      Part / value
====================== ======== ==============================================
SW1                    1        Omron D2F-01F, SPDT gold-contact pin plunger
SW2, SW3, SW4, SW5      4        Omron B3U-1000P, normally open tactile
J1                     1        JST SM12B-GHS-TB(LF)(SN), GH12 horizontal
J2, J3, J4, J5, J6      5        JST SM02B-GHS-TB(LF)(SN), GH2 horizontal
J7                     1        JST S4B-PH-SM4-TB(LF)(SN), PH4 horizontal SMT
J8                     1        JST SM03B-GHS-TB(LF)(SN), GH3 horizontal
JP1                    1        Samtec TSW-102-07-G-S, 2-pin 2.54 mm header
R1, R2, R6             3        2.2k,1%,0.1W0603; Yageo RC0603FR-072K2L
R3, R5, R7, R9         4        10k,1%,0.1W0603; Yageo RC0603FR-0710KL
R4, R8                 2        100k,1%,0.1W0603; Yageo RC0603FR-07100KL
C1                     1        100nF16VX7R0603; Murata GRM188R71C104KA01D
C2                     1        4.7uF6.3VX5R0603; Murata GRM188R60J475KE19D
C3, C4                 2        10nF50VX7R0603; Murata GRM188R71H103KA01D
Q1, Q2                 2        onsemi MMBT3904LT1G, SOT-23:1B,2E,3C
OLED, external         1        Waveshare14657,0.91inch128x32,36x12.5 mm
====================== ======== ==============================================

Supply one removable 2.54 mm JP1 shunt when J3 has no external STOP contact.
Mating GH housings are GHR-12V-S, GHR-02V-S and GHR-03V-S, with appropriate
SSHL-002T-P0.2 contacts and wire gauges. The PH4 harness uses PHR-4 housings
with appropriate PH-series contacts. Select crimp contacts for the actual wire;
verify housing keying and connector drawings before purchasing. Mating cable
parts and the external OLED are not included in the bare PCB order.

J1 host cable
-------------

======== ========================== ===============================
J1 pin   Panel net                  Rev E main-board connection
======== ========================== ===============================
1        +5V                        J32.1
2        STOP_RETURN                J32.2
3        MAN_RETURN (MODE)          J32.3
4        AUTO_RETURN (NEXT)         J32.4
5        START_N                    J32.5
6        RESET_N (SET/RESET)        J32.6
7        GND                        J32.7
8        +3V3                       J32.8
9        I2C_SDA                    J32.9
10       I2C_SCL                    J32.10
11       KEY_MAN_N                  J32.11 / SPARE_B6
12       KEY_AUTO_N                 J32.12 / SPARE_B7
======== ========================== ===============================

Use one factory-crimped 12-way GH cable, all cavities one-to-one: panel J1.n
connects to main Rev E J32.n, n=1 through 12. Nominal length 150 mm; specify
GHR-12V-S housings at both ends, SSHL-002T-P0.2 contacts, 28 AWG stranded wire.
A cable assembler must supply completed, labelled, continuity-tested cables.
No field soldering or crimping is required. Reject reversed pin order, crossed
wires, or shorts. Cavity numbers refer to the mating connector drawing, not
wire colors or an assumed left/right view. The Rev D fanout is incompatible
with this Rev E interface and must not be used.

External buttons and OLED
-------------------------

========= ===== ========================= ===========================
Connector Type  Pin1                      Pin2
========= ===== ========================= ===========================
J2 START  NO    START_N                   GND
J3 STOP   NC    STOP_LOCAL_NC             STOP_RETURN
J4 MODE   NO    MAN_RETURN                STOP_RETURN
J5 SET    NO    RESET_N                   GND
J6 NEXT   NO    AUTO_RETURN               STOP_RETURN
========= ===== ========================= ===========================

JP1 pins 1/2 bridge J3 pins 1/2 only when the optional external STOP is absent.
Do not fit JP1 with an external STOP that must remain operational.

J7 OLED pins:1=SCL,2=SDA,3=GND,4=3.3 V. Connect the Waveshare14657 numeric pins
one-to-one. Do not assume a bought four-wire lead is wired1-to1; verify it.
No panel I2C pullups are fitted because the main board already supplies them.
Use a short internal harness and verify bus waveform/operation after assembly.

J8 KEY pins:1 = +5Vcommon,2 = MANUALraw,3 = AUTOraw. The key contacts never carry mains.
Keep the optional key feature disabled until its wiring and logic are tested.

Factory OLED cable and harness acceptance
-----------------------------------------

The candidate ready-made OLED lead is Pololu item 5623: a 100 mm, 24 AWG,
four-way PH-style female-to-female cable. Its product listing identifies
2.00 mm-pitch connectors at both ends. Verify numeric continuity 1-to-1,
2-to-2, 3-to-3 and 4-to-4 before acceptance; the product text does not provide
a full pin-to-pin drawing. Its colors do not follow the usual power-color
assumption in this circuit. The product listing allowed backorders when
reviewed; availability in India and delivery are unconfirmed.

If the candidate fails acceptance or is unavailable, order a factory harness:
two PHR-4 housings, eight JST SPH-002T-P0.5S contacts for suitable 24 AWG wire,
100 mm nominal finished length, cavities 1-through-4 wired one-to-one, labelled
OLED at both ends. The assembler supplies crimped housings and performs all
four continuity and six pairwise short checks. Installer action is plugging
in the keyed completed cable; there are no loose wire ends to solder.

Target total main-to-panel plus panel-to-OLED wire length is at most 250 mm.
This is a layout target, not a demonstrated I2C limit. Preserve 400 kHz shared
bus scheduling and measure Fast-mode rise time<=300 ns, low levels, noise and
probe/OLED deadlines on the populated harness with the motor operating. Add
no panel pullups; the main 3.3k and OLED module pullups already load the bus.
Slowing the entire bus requires requalification of the 2 ms probe slots.

External button leads use GHR-02V-S at the PCB end and the selected button's
approved terminal attachment at the other end. The maintained key lead uses
GHR-03V-S. Have these leads factory assembled and labelled for START, NC STOP,
MODE, SET and NEXT. Unused external button connectors remain empty, with JP1
fitted only for the absent external STOP. No mains voltage belongs on these
contacts or cable assemblies.

Primary sources
---------------

* JST GH connector drawing: https://www.jst-mfg.com/product/pdf/eng/eGH.pdf
* JST PH connector drawing: https://www.jst-mfg.com/product/pdf/eng/ePH.pdf
* OLED cable: https://www.pololu.com/product/5623
* OLED cable dimensions: https://www.pololu.com/product/5623/specs
* STOP switch: https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf
* Key transistor: https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf
