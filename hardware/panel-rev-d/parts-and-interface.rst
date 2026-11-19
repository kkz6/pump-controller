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
J1                     1        JST BM12B-GHS-TBT(LF)(SN), GH12 vertical
J2, J3, J4, J5, J6      5        JST BM02B-GHS-TBT(LF)(SN), GH2 vertical
J7                     1        JST B4B-PH-SM4-TB(LF)(SN), PH4 vertical SMT
J8                     1        JST BM03B-GHS-TBT(LF)(SN), GH3 vertical
JP1                    1        Samtec TSW-102-07-G-S, 2-pin 2.54mm header
R1, R2, R6             3        2.2k,1%,0.1W0603; Yageo RC0603FR-072K2L
R3, R5, R7, R9         4        10k,1%,0.1W0603; Yageo RC0603FR-0710KL
R4, R8                 2        100k,1%,0.1W0603; Yageo RC0603FR-07100KL
C1                     1        100nF16VX7R0603; Murata GRM188R71C104KA01D
C2                     1        4.7uF6.3VX5R0603; Murata GRM188R60J475KE19D
C3, C4                 2        10nF50VX7R0603; Murata GRM188R71H103KA01D
Q1, Q2                 2        onsemi MMBT3904LT1G, SOT-23:1B,2E,3C
OLED, external         1        Waveshare14657,0.91inch128x32,36x12.5mm
====================== ======== ==============================================

Supply one removable 2.54mm JP1 shunt when J3 has no external STOP contact.
Mating GH housings are GHR-12V-S, GHR-02V-S and GHR-03V-S, with appropriate
SSHL-002T-P0.2 contacts and wire gauges. The PH4 harness uses PHR-4 housings
with appropriate PH-series contacts. Select crimp contacts for the actual wire;
verify housing keying and connector drawings before purchasing. Mating cable
parts and the external OLED are not included in the bare PCB order.

J1 host cable
-------------

======== ========================== ===============================
J1 pin   Panel net                  Existing main-board connection
======== ========================== ===============================
1        +5V                        J32.1
2        STOP_RETURN                J32.2
3        MAN_RETURN (MODE)          J32.3
4        AUTO_RETURN (NEXT)         J32.4
5        START_N                    J32.5
6        RESET_N (SET/RESET)        J32.6
7        GND                        J32.7
8        +3V3                       J33.1
9        I2C_SDA                    J33.3
10       I2C_SCL                    J33.4
11       KEY_MAN_N                  J34.5 / SPARE_B6
12       KEY_AUTO_N                 J34.6 / SPARE_B7
======== ========================== ===============================

J32.4 and J32.6 are used in this panel assembly, despite being reserved for
external wiring in the earlier Rev C front-panel arrangement. J32.7 provides
the shared ground return; J33.2 and J34.2 are already the same main-board GND
and do not require duplicate wires. Never place two wires in a contact not
rated for them. All contacts numbered by PCB pad number, not viewing direction
or cable color. Use a labelled fan-out harness; J1 is not compatible with
plugging directly into one existing main-board connector.

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

JP1 pins1/2 bridge J3 pins1/2 only when the optional external STOP is absent.
Do not fit JP1 with an external STOP that must remain operational.

J7 OLED pins:1=SCL,2=SDA,3=GND,4=3.3V. Connect the Waveshare14657 numeric pins
one-to-one. Do not assume a bought four-wire lead is wired1-to1; verify it.
No panel I2C pullups are fitted because the main board already supplies them.
Use a short internal harness and verify bus waveform/operation after assembly.

J8 KEY pins:1=+5Vcommon,2=MANUALraw,3=AUTOraw. The key contacts never carry mains.
Keep the optional key feature disabled until its wiring and logic are tested.
