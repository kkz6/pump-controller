#!/usr/bin/env python3
"""Build a connection overview; mechanical placement is conceptual."""

from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/panel-rev-d"
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads((ROOT / "design/panel-rev-d.json").read_text())
components = {c["ref"]: c for s in data["sheets"] for c in s["components"]}
host = {int(p["num"]): p["net"] for p in components["J1"]["pins"] if p["num"].isdigit()}
assert host == {
    1: "+5V", 2: "STOP_RETURN", 3: "MAN_RETURN", 4: "AUTO_RETURN",
    5: "START_N", 6: "RESET_N", 7: "GND", 8: "+3V3", 9: "I2C_SDA",
    10: "I2C_SCL", 11: "KEY_MAN_N", 12: "KEY_AUTO_N",
}, "Panel connector changed: review the main-board cable map before redrawing."

navy = "#132b3c"
muted = "#526976"
teal = "#007f79"
red = "#a53935"
gold = "#b1802e"
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1460" viewBox="0 0 1800 1460">
<title>Rev D panel and DOL starter connection overview</title>
<desc>Conceptual mechanical overview with verified panel connector signals. Main board retains guarded mains circuitry. Separate panel uses isolated 3.3 and 5 volt circuits. Local and external STOP contacts are series connected.</desc>
<defs>
 <pattern id="hazard" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="12" height="12" fill="#fff4dc"/><rect width="4" height="12" fill="#ebcf8c"/></pattern>
 <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="{teal}"/></marker>
</defs>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:{navy};font-size:20px}} .small{{font-size:17px;fill:{muted}}}.tiny{{font-size:15px;fill:{muted}}}.heading{{font-size:26px;font-weight:700}} .label{{font-weight:700}} .mono{{font-family:Menlo,Consolas,monospace;font-size:18px}} .light{{fill:white}} .live{{fill:{red}}}</style>
<rect width="1800" height="1460" fill="#f3f5f6"/>
''']


def rect(x, y, w, h, fill, stroke="none", r=0, sw=1):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def text(x, y, value, cls="", anchor="start", fill=None):
    parts.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"'+(f' style="fill:{fill}"' if fill else '')+f'>{escape(value)}</text>')


def line(x1, y1, x2, y2, color=teal, width=3, dash=None):
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')


def path(d, color=teal, width=3, dash=None):
    parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')


def circle(x, y, r, fill, stroke="none", sw=1):
    parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def labelbox(x, y, w, h, label, fill="#e7eeee", size="label"):
    rect(x, y, w, h, fill, "#a9b9bf", 5)
    text(x+w/2, y+h/2+7, label, size, "middle")


text(42, 63, "A separate control panel, one low-voltage cable", "heading")
text(42, 102, "Rev D • 1 HP single-phase pump controller • Connection overview, not an installation or enclosure-fit approval", "small")
rect(1480, 34, 278, 51, "#fff3d8", "#ddbc77", 9)
text(1619, 66, "ENGINEERING PROTOTYPE", "small label", "middle", "#865d17")

# Existing starter cabinet and main board.
rect(40, 140, 785, 600, "white", "#ccd6dc", 15)
text(66, 181, "01  Inside the existing starter", "heading")
text(66, 213, "Main PCB 90 × 70 mm • guarded power section", "small")
rect(65, 235, 735, 425, "#e9edef", "#aab7bf", 8, 2)
rect(83, 254, 198, 384, "#f7e8e4", "#d9a79e", 7)
text(182, 283, "EXISTING LIVE PARTS", "small label", "middle", red)
rect(106, 309, 57, 99, "#d9d8c8", "#8f927e", 14)
rect(176, 309, 69, 99, "#d3d6d9", "#8d979e", 14)
text(176, 431, "Start / run capacitors", "tiny", "middle")
rect(112, 454, 131, 89, "#39464e", "#25353f", 7)
for x in [130, 163, 196, 228]:
    circle(x, 466, 5, "#c7b584")
    circle(x, 530, 5, "#c7b584")
text(177, 503, "CONTACTOR", "small label light", "middle", "white")
text(182, 578, "Mains / meter backs", "tiny", "middle", red)
text(182, 603, "remain behind guards", "tiny", "middle", red)

bx, by, bw, bh = 310, 278, 420, 327
rect(bx, by, bw, bh, "#e3f0e9", "#628d79", 7, 2)
rect(bx+2, by+2, 150, bh-4, "#f4e6e0")
rect(bx+152, by+2, 37, bh-4, "url(#hazard)")
text(385, 305, "MAIN / LIVE", "small label", "middle", red)
text(594, 305, "ISOLATED CONTROL", "small label", "middle", teal)
labelbox(327, 326, 116, 100, "AC/DC", "#d6d3cf")
text(385, 449, "Fuse • metering", "tiny", "middle", red)
labelbox(328, 469, 116, 65, "COIL RELAYS", "#e5dbcf", "tiny label")
text(385, 559, "Mains stays here", "tiny", "middle", red)
parts.append('<text x="483" y="571" class="tiny label" transform="rotate(-90 483 571)">8 mm copper isolation corridor</text>')
labelbox(510, 329, 132, 66, "ESP32 + I/O", "#c6e2d4", "small label")
text(510, 427, "SW3 / SW4: DNP", "tiny label")
text(510, 449, "Settings move to panel", "tiny")
for y, name, detail in [(466, "J32", "Buttons"), (517, "J33", "Display"), (568, "J34", "Key I/O")]:
    labelbox(657, y-19, 99, 37, name, "#d4e9e6", "small label")
    text(642, y+5, detail, "tiny", "end")
text(66, 695, "Motor power and capacitor-start wiring stay in the starter.", "small")
text(66, 722, "Main-board and original meter terminals need insulating covers.", "small")

# Separate panel board: controls follow the current logical left-to-right order.
rect(955, 140, 805, 600, "white", "#ccd6dc", 15)
text(981, 181, "02  Separate front-panel PCB", "heading")
text(981, 213, "60 × 45 mm • only isolated 3.3 V / 5 V circuits", "small")
px, py, pw, ph = 1060, 247, 600, 450
rect(px, py, pw, ph, "#dcf0e6", "#578e77", 10, 2)
for hx, hy in [(px+30, py+30), (px+570, py+30), (px+30, py+420), (px+570, py+420)]:
    circle(hx, hy, 9, "white", "#6c9c87", 2)

# OLED is raised above the board; conceptual placement avoids claiming verified clearance.
rect(1180, 266, 360, 125, "#1a3a3e", "#476f6e", 6, 2)
rect(1202, 282, 315, 80, "#091b22", r=4)
text(1217, 309, "AUTO          READY", "mono", fill="#7ee5df")
text(1217, 339, "LEVEL 3/4    230 V", "mono", fill="#7ee5df")
text(1360, 383, "0.91 in OLED • above PCB", "tiny", "middle", "#c2e5dd")
labelbox(1545, 311, 92, 38, "J7 OLED", "#f9fbfa", "tiny label")
line(1540, 330, 1545, 330, muted, 2)
labelbox(1087, 312, 82, 38, "J8 KEY", "#f9fbfa", "tiny label")
text(1128, 376, "Optional", "tiny", "middle")
text(1128, 399, "MAN / AUTO", "tiny", "middle")

labelbox(1240, 427, 174, 40, "J1 • 12-way", "#d0e6e2", "small label")
text(1435, 451, "Key input circuits", "tiny")
labelbox(1435, 476, 76, 36, "JP1", "#fff1d4", "tiny label")
text(1524, 500, "Ext STOP link", "tiny")

buttons = [(1135, "START", "SW2", "#007d62"), (1293, "STOP", "SW1 NC", "#a63a36"),
           (1405, "MODE", "SW3", "#24759c"), (1510, "SET", "SW4", "#596e80"), (1600, "NEXT", "SW5", "#596e80")]
for x, label, ref, color in buttons:
    rect(x-26, 535, 52, 42, "#253b47", r=6)
    circle(x, 556, 15, color, "#f5f6f7", 2)
    text(x, 604, label, "tiny label", "middle")
    text(x, 625, ref, "tiny", "middle")
for x, label in [(1140, "J2 START"), (1250, "J3 STOP"), (1360, "J4 MODE"), (1470, "J5 SET"), (1580, "J6 NEXT")]:
    labelbox(x-48, 647, 96, 28, label, "#f9fbfa", "tiny label")
text(981, 724, "Push-caps, OLED mounting and connector clearance require fit checks.", "small")

# One cable with a three-header main-board fanout; the panel connector is real J1.
for y in [466, 517, 568]:
    path(f'M756 {y} H785 Q805 {y} 805 477 V447 H850', teal, 4)
path('M850 447 H1240', teal, 12)
path('M850 447 H1240', "#59b7ac", 5)
text(891, 362, "ONE CABLE", "small label", "middle", teal)
text(891, 388, "12 conductors", "tiny", "middle")
text(891, 414, "J1 at panel", "tiny", "middle")
text(891, 487, "Fanout at main", "tiny", "middle")
text(891, 513, "J32 + J33 + J34", "tiny", "middle")

# STOP must remain hardware series connected.
rect(40, 778, 810, 605, "white", "#ccd6dc", 15)
text(66, 821, "Either STOP opens the hardware permission path", "heading")
text(66, 855, "The external link substitutes only for an unused external STOP.", "small")

text(77, 956, "+5V", "mono label")
line(132, 949, 202, 949, red, 4)
circle(202, 949, 5, "white", red, 2)
circle(306, 949, 5, "white", red, 2)
line(202, 949, 306, 949, red, 4)
line(254, 910, 254, 939, red, 2, "4 3")
line(235, 910, 273, 910, red, 3)
text(254, 889, "SW1 local STOP", "small label", "middle")
text(254, 983, "NC • opens on press", "tiny", "middle")
line(311, 949, 435, 949, red, 4)
circle(435, 949, 5, "white", red, 2)
circle(550, 949, 5, "white", red, 2)
line(435, 949, 550, 949, red, 4)
line(492, 910, 492, 939, red, 2, "4 3")
line(473, 910, 511, 910, red, 3)
text(492, 889, "J3 external NC STOP", "small label", "middle")
text(435, 981, "1", "tiny", "middle")
text(550, 981, "2", "tiny", "middle")
path('M409 949 V1034 H574 V949', gold, 3, "7 5")
text(492, 1066, "JP1 link only if J3 is unused", "small label", "middle", "#8c621d")
line(555, 949, 792, 949, red, 4)
text(680, 924, "STOP_RETURN", "mono label", "middle")
text(680, 982, "to main J32.2", "tiny", "middle")
text(680, 1005, "then high-high loop / K1", "tiny", "middle")

line(66, 1090, 824, 1090, "#dde5e9", 1)
text(66, 1126, "Reuse or add external momentary buttons", "label")
text(66, 1158, "J2 START, J4 MODE, J5 SET and J6 NEXT use NO contacts", "small")
text(66, 1185, "in parallel with the corresponding local button.", "small")
text(66, 1229, "Optional maintained key selector → J8", "label")
text(66, 1261, "1 = +5V common    2 = MAN throw    3 = AUTO throw", "small")
text(66, 1288, "Mode request only; it cannot bypass STOP or other protection.", "small")
rect(66, 1311, 758, 50, "#fff2df", r=5)
text(83, 1343, "Existing starter buttons: separate isolated auxiliary contacts only.", "small label", fill="#835a1e")

# Exact wire map generated from the panel source, not generic connector numbering.
rect(880, 778, 880, 605, "white", "#ccd6dc", 15)
text(906, 821, "12-way panel cable: exact signal map", "heading")
text(906, 852, "One conductor per listed signal; common ground uses J32.7.", "small")
rect(906, 873, 828, 36, "#e8eff1", r=4)
text(926, 898, "PANEL J1", "small label")
text(1069, 898, "SIGNAL / FUNCTION", "small label")
text(1563, 898, "MAIN END", "small label")
names = {1:"+5V", 2:"STOP_RETURN", 3:"MODE  /  MAN_RETURN", 4:"NEXT  /  AUTO_RETURN",
         5:"START_N", 6:"SET / RESET_N", 7:"GND", 8:"+3V3", 9:"I2C_SDA", 10:"I2C_SCL",
         11:"KEY_MAN_N", 12:"KEY_AUTO_N"}
main = {**{i:f'J32.{i}' for i in range(1, 8)}, 8:'J33.1', 9:'J33.3', 10:'J33.4', 11:'J34.5', 12:'J34.6'}
for i in range(1, 13):
    y = 911+(i-1)*31
    if i % 2 == 0:
        rect(906, y, 828, 31, "#f5f8f9")
    text(959, y+22, str(i), "mono", "middle")
    text(1069, y+22, names[i], "mono")
    text(1563, y+22, main[i], "mono")
text(906, 1312, "J33.2 is the same main-board GND: leave its wire cavity empty", "small")
text(906, 1339, "in this fanout. No double-crimped ground terminal is required.", "small")
text(906, 1366, "J7 OLED order: 1 SCL • 2 SDA • 3 GND • 4 +3V3", "small label")

text(42, 1422, "Conceptual component placement and wiring paths • Not to scale • Wire identities must be verified on the actual starter before installation", "small")
parts.append('</svg>')
target = OUT / "connection-overview.svg"
target.write_text("\n".join(parts))
print(target)
