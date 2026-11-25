"""Compact in-starter enclosure for the R4 main board, button lid and door display bezel.

Run:  .venv/bin/python mechanical/enclosure-r4/build.py

The box sits inside the starter cabinet. Field connectors are reached
through openings in its walls. The panel PCB hangs under the lid and its five
buttons come through the lid as printed caps; the buttons are used with the
starter door open. The OLED moves to a small bezel in the starter door so it is
visible with the door closed, wired to panel J7 by a longer 4-way PH lead.

Coordinates: KiCad board coordinates (x right, y down, mm). Box z is measured
from the outside of the floor (mounting face, z = 0) toward the lid.
"""
from pathlib import Path
import json

import numpy as np
import trimesh
from build123d import (Align, Axis, Box, Cylinder, Pos, Rot, Rectangle, RectangleRounded, Text,
                       extrude, export_step, export_stl, fillet)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
C = (Align.CENTER, Align.CENTER, Align.MIN)

# ------------------------------------------------------------------ main board
BOARD_X0, BOARD_X1, BOARD_Y0, BOARD_Y1 = 0.0, 100.0, -14.5, 104.0
BOARD_T = 1.6
BOARD_HOLES = [(4.0, -10.5), (96.0, -10.5), (96.0, 100.0), (4.0, 100.0)]
# Field connectors reached through the walls: ref, wall, (lo, hi) along the wall
# in board coordinates, extra margin either side.
PORTS = [
    ('J1', 'left', (5.7, 21.8), 1.0, 'AC IN  L / N'),
    ('J10', 'left', (68.8, 77.4), 1.0, 'CT'),
    ('J21', 'top', (19.5, 28.0), 1.0, 'INLET'),
    ('J20', 'top', (64.6, 86.2), 1.0, 'TANK  C 1 2 3 4'),
    ('J30', 'bottom', (13.9, 30.2), 1.0, 'A: NO COM NC'),
    ('J35', 'bottom', (58.9, 75.2), 1.0, 'B: NO COM NC'),
    ('J40', 'right', (13.3, 26.7), 1.5, 'USB'),
]

# ------------------------------------------------------------------ box
WALL, FLOOR, LID_T = 2.5, 3.0, 2.5
GAP = 0.75                      # board edge to wall on the three tight sides
RIGHT_BAY = 12.0                # room for the J32 panel loom plug and display lead
R_OUT = 4.0
STANDOFF_H, STANDOFF_D = 6.5, 7.0
M3_INSERT_D, M3_INSERT_DEPTH = 4.0, 5.0
SPACERS = [20, 25, 30, 35]      # standard M3 male-female hex spacers
MIN_PANEL_CLEARANCE = 3.0       # panel rear (incl. connectors) above any main-board part
MOUNT_HOLES = [(50.0, -5.0), (50.0, 95.0)]   # M4 countersunk, fitted before the PCB

BOARD_UNDERSIDE = FLOOR + STANDOFF_H
BOARD_TOP = BOARD_UNDERSIDE + BOARD_T
IN_X0, IN_X1 = BOARD_X0 - GAP, BOARD_X1 + RIGHT_BAY
IN_Y0, IN_Y1 = BOARD_Y0 - GAP, BOARD_Y1 + GAP

# ------------------------------------------------------------------ panel F under the lid
# Two lid variants share the base. Panel (0, 0) in board coordinates for each,
# chosen so the visible controls sit at the centre of the lid (within 0.7 mm)
# while the panel and its plugs keep >= 3 mm above every main-board part.
VARIANTS = {
    'buttons': dict(panel_at=(25.5, 14.75), display=False),   # button row centred; OLED in the door
    'display': dict(panel_at=(25.5, 24.75), display=True),    # display + buttons group centred
}
PANEL_W, PANEL_H = 60.0, 45.0
PANEL_HOLES = [(3, 3), (57, 3), (3, 42), (57, 42)]
PANEL_REAR_DEPTH = 3.3 + 1.0    # rear SMD connectors 3.3 mm + 1 mm plug lip
PANEL_DEPTH = 8.5               # lid inner face to the panel's front face
KEYS = [  # label, panel x, panel y, cap diameter, switch top above panel face
    ('START', 7.5, 30.0, 9.0, 1.6),
    ('STOP', 20.0, 30.0, 11.0, 7.4),
    ('MODE', 34.5, 30.0, 7.0, 1.6),
    ('SET', 45.0, 30.0, 7.0, 1.6),
    ('NEXT', 54.0, 30.0, 7.0, 1.6),
]
KEY_CLEAR, FLANGE_LIP, FLANGE_T, CAP_PROUD, STEM_GAP = 0.4, 0.7, 1.0, 2.0, 0.3
LOOM_SLOT = (43.0, 8.0)        # (centre y in board coords, width) display lead exit, right wall top

# ------------------------------------------------------------------ door bezel (OLED)
OLED_PCB = (36.0, 12.5, 1.2)
OLED_GLASS = (29.0, 9.0, 1.0)
OLED_ACTIVE = (22.4, 5.5)
OLED_GLASS_OFFSET = (-0.5, 0.0)  # glass centre relative to module PCB centre
DOOR_CUTOUT = (31.0, 12.0)
BEZEL = (54.0, 26.0, 2.5)
BEZEL_WINDOW = (25.0, 8.0)
LENS = (34.0, 15.0, 1.5)
BEZEL_SCREW_X = 22.5
HOLDER_DEPTH = 7.0
# display lid: OLED module on the panel front (panel coordinates)
PANEL_OLED_ACTIVE = ((18.8, 7.5), (41.2, 13.0))
PANEL_OLED_GLASS = ((15.5, 5.8), (44.5, 14.8))
LID_WINDOW = (25.0, 8.0)
LID_LENS = (36.0, 13.0, 1.5)     # clear lens in a pocket on the lid's inner face


def load_main_heights():
    """Bounding box of every face group in the KiCad 3D export.

    Large parts are exported as hollow envelopes, so vertices alone would miss
    their interiors; boxes do not. Columns: x0, x1, y0, y1 (board coordinates)
    and the top above the board underside.
    """
    scene = trimesh.load(REPO / 'docs/3d/main.glb')
    boxes = []
    for node in scene.graph.nodes_geometry:
        T, g = scene.graph[node]
        m = scene.geometry[g].copy()
        m.apply_transform(T)
        b = m.bounds * 1000.0
        if b[1][1] > BOARD_T + 0.05:
            boxes.append((b[0][0], b[1][0], b[0][2], b[1][2], b[1][1]))
    return np.array(boxes)


def height_in(v, x0, x1, y0, y1):
    sel = (v[:, 0] < x1) & (v[:, 1] > x0) & (v[:, 2] < y1) & (v[:, 3] > y0)
    return float(v[sel, 4].max()) if sel.any() else BOARD_T


# Panel rear plug envelopes (panel coordinates): mated plug plus 7 mm of wire run.
PANEL_PLUGS = [(20.9, -7.0, 39.1, 4.9),    # J1 loom to main J32
               (22.0, 40.1, 38.0, 52.0),   # J2 STOP loop plug
               (51.6, 15.0, 67.0, 27.0)]   # J7 display lead


def place(x, y, z=0.0):
    """Board coordinates -> centred CAD position (y flipped so the front view matches KiCad)."""
    cx, cy = (IN_X0 + IN_X1) / 2, (IN_Y0 + IN_Y1) / 2
    return Pos(x - cx, cy - y, z)


def panel_heights(v, panel_at):
    px0, py0 = panel_at
    slab = height_in(v, px0, px0 + PANEL_W, py0, py0 + PANEL_H)
    plugs = max(height_in(v, px0 + a, px0 + c, py0 + b, py0 + d) for a, b, c, d in PANEL_PLUGS)
    return slab, plugs


def layout():
    v = load_main_heights()
    tallest = float(v[:, 4].max())
    need = tallest + 2.0
    for var in VARIANTS.values():
        slab, plugs = panel_heights(v, var['panel_at'])
        need = max(need, slab + MIN_PANEL_CLEARANCE + BOARD_T + PANEL_DEPTH,
                   plugs + MIN_PANEL_CLEARANCE + PANEL_REAR_DEPTH + BOARD_T + PANEL_DEPTH)
    need_lid_inner = BOARD_UNDERSIDE + need
    spacer = next(s for s in SPACERS if BOARD_TOP + s >= need_lid_inner)
    lid_inner = BOARD_TOP + spacer
    clear = {}
    for name, var in VARIANTS.items():
        slab, plugs = panel_heights(v, var['panel_at'])
        clear[name] = dict(
            panel_at=list(var['panel_at']),
            panel_pcb_to_parts=round(lid_inner - PANEL_DEPTH - BOARD_T - (BOARD_UNDERSIDE + slab), 2),
            panel_plugs_to_parts=round(lid_inner - PANEL_DEPTH - BOARD_T - PANEL_REAR_DEPTH - (BOARD_UNDERSIDE + plugs), 2))
    ports = []
    for ref, wall, (lo, hi), margin, label in PORTS:
        if wall in ('left', 'right'):
            xs = (BOARD_X0, BOARD_X0 + 12) if wall == 'left' else (BOARD_X1 - 10, BOARD_X1 + 2)
            h = height_in(v, xs[0], xs[1], lo, hi)
        else:
            ys = (BOARD_Y0 - 2, BOARD_Y0 + 14) if wall == 'top' else (BOARD_Y1 - 13, BOARD_Y1 + 2)
            h = height_in(v, lo, hi, ys[0], ys[1])
        ports.append(dict(ref=ref, wall=wall, span=[lo - margin, hi + margin],
                          z=[BOARD_TOP - 0.8, min(BOARD_UNDERSIDE + h + 1.0, lid_inner - 0.01)], label=label))
    return dict(tallest_part_above_underside=round(tallest, 2),
                spacer_mm=spacer, lid_inner_z=round(lid_inner, 2), ports=ports,
                panel_front_z=round(lid_inner - PANEL_DEPTH, 2), variants=clear,
                clearance_lid_to_tallest=round(lid_inner - BOARD_UNDERSIDE - tallest, 2))


# ================================================================== base
def build_base(lay):
    wall_top = lay['lid_inner_z']
    iw, ih = IN_X1 - IN_X0, IN_Y1 - IN_Y0
    ow, oh = iw + 2 * WALL, ih + 2 * WALL
    base = extrude(RectangleRounded(ow, oh, R_OUT), wall_top)
    base -= Pos(0, 0, FLOOR) * extrude(RectangleRounded(iw, ih, max(R_OUT - WALL, 0.5)), wall_top)
    for hx, hy in BOARD_HOLES:
        base += place(hx, hy, FLOOR) * Cylinder(STANDOFF_D / 2, STANDOFF_H, align=C)
        base -= place(hx, hy, BOARD_UNDERSIDE - M3_INSERT_DEPTH) * Cylinder(M3_INSERT_D / 2, M3_INSERT_DEPTH + 1, align=C)
    for hx, hy in MOUNT_HOLES:   # M4 countersunk, flush with the floor
        base -= place(hx, hy, -1) * Cylinder(2.25, FLOOR + 2, align=C)
        base -= place(hx, hy, FLOOR - 2.3) * Cylinder(4.1, 2.31, align=C)
        base -= place(hx, hy, FLOOR - 2.3) * extrude(Rot(0, 0, 0) * __import__('build123d').Circle(2.25), 2.3, taper=-41)
    for p in lay['ports']:
        lo, hi = p['span']
        z0, z1 = p['z']
        # windows sized to each connector; the board still drops in from above
        if p['wall'] in ('top', 'bottom'):
            y = IN_Y0 - WALL / 2 if p['wall'] == 'top' else IN_Y1 + WALL / 2
            base -= place((lo + hi) / 2, y, z0) * Box(hi - lo, WALL * 3, z1 - z0, align=C)
        else:
            x = IN_X0 - WALL / 2 if p['wall'] == 'left' else IN_X1 + WALL / 2
            base -= place(x, (lo + hi) / 2, z0) * Box(WALL * 3, hi - lo, z1 - z0, align=C)
    # display-lead exit at the top of the right wall, closed by the lid
    y, w = LOOM_SLOT
    base -= place(IN_X1 + WALL / 2, y, wall_top - 5) * Box(WALL * 3, w, 6, align=C)
    return base, (ow, oh)


# ================================================================== lid (z = 0 inner face)
def build_lid(lay, outer, variant):
    ow, oh = outer
    var = VARIANTS[variant]
    lid = extrude(RectangleRounded(ow, oh, R_OUT), LID_T)
    lid = fillet(lid.edges().group_by(Axis.Z)[-1], 1.0)
    # locating skirt just inside the walls; open at the display-lead slot
    iw, ih = IN_X1 - IN_X0, IN_Y1 - IN_Y0
    lid += extrude(RectangleRounded(iw - 0.4, ih - 0.4, 1.0) - RectangleRounded(iw - 3.6, ih - 3.6, 0.5), -3.0)
    y, w = LOOM_SLOT
    lid -= place(IN_X1 - 1, y, -4) * Box(6, w + 1, 5, align=C)
    for hx, hy in BOARD_HOLES:   # screws into the M3 spacers
        lid -= place(hx, hy, -5) * Cylinder(1.7, LID_T + 10, align=C)
        lid -= place(hx, hy, LID_T - 1.7) * Cylinder(3.1, 2, align=C)
    px0, py0 = var['panel_at']
    for hx, hy in PANEL_HOLES:   # panel bosses, M2.5 heat-set from below
        x, y = px0 + hx, py0 + hy
        lid += place(x, y, 0) * Cylinder(3.3, PANEL_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MAX))
        lid -= place(x, y, -PANEL_DEPTH) * Cylinder(1.75, 6.0, align=C)
    key_y = py0 + KEYS[0][2]
    for label, kx, ky, d, _ in KEYS:
        x, y = px0 + kx, py0 + ky
        lid -= place(x, y, -1) * Cylinder((d + KEY_CLEAR) / 2, LID_T + 2, align=C)
        lid -= place(x, y + 8.2, LID_T - 0.5) * extrude(Text(label, 2.6), 1)
    cx = (IN_X0 + IN_X1) / 2
    top_of_group = key_y - 8
    if var['display']:
        (ax0, ay0), (ax1, ay1) = PANEL_OLED_ACTIVE
        (gx0, gy0), (gx1, gy1) = PANEL_OLED_GLASS
        wx, wy = px0 + (ax0 + ax1) / 2, py0 + (ay0 + ay1) / 2
        lid -= place(wx, wy, -1) * extrude(Rectangle(*LID_WINDOW), LID_T + 2)
        lid -= place(wx, wy, LID_T + 0.001) * extrude(Rectangle(LID_WINDOW[0] + 1.6, LID_WINDOW[1] + 1.6), -0.8, taper=45)
        lid -= place(px0 + (gx0 + gx1) / 2, py0 + (gy0 + gy1) / 2, -0.01) * \
            extrude(RectangleRounded(LID_LENS[0] + 0.3, LID_LENS[1] + 0.3, 1.5), LID_LENS[2] + 0.01)
        top_of_group = wy - LID_WINDOW[1] / 2
    lid -= place(cx, top_of_group - 12, LID_T - 0.5) * extrude(Text('PUMP CONTROLLER R4', 5.0), 1)
    lid -= place(cx, key_y + 22, LID_T - 0.5) * extrude(Text('ISOLATE SUPPLY BEFORE OPENING', 2.6), 1)
    return lid


def build_lid_lens():
    return extrude(RectangleRounded(*LID_LENS[:2], 1.5), LID_LENS[2])


def build_caps(variant):
    caps = None
    px0, py0 = VARIANTS[variant]['panel_at']
    for label, kx, ky, d, sw_top in KEYS:
        x, y = px0 + kx, py0 + ky
        hole = d + KEY_CLEAR
        top = LID_T + CAP_PROUD
        cap = place(x, y, 0) * Cylinder(d / 2, top, align=C)
        cap = fillet(cap.edges().group_by(Axis.Z)[-1], min(1.0, d / 6))
        cap += place(x, y, -FLANGE_T) * Cylinder(hole / 2 + FLANGE_LIP, FLANGE_T, align=C)
        stem_bottom = -PANEL_DEPTH + sw_top + STEM_GAP
        if -FLANGE_T - stem_bottom > 0.05:
            cap += place(x, y, stem_bottom) * Cylinder(1.5, -FLANGE_T - stem_bottom, align=C)
        caps = cap if caps is None else caps + cap
    return caps


# ================================================================== door bezel
def build_bezel():
    bw, bh, bt = BEZEL
    front = extrude(RectangleRounded(bw, bh, 3), bt)
    front = fillet(front.edges().group_by(Axis.Z)[-1], 0.8)
    front -= Pos(0, 0, -1) * extrude(Rectangle(*BEZEL_WINDOW), bt + 2)
    front -= Pos(0, 0, bt + 0.001) * extrude(Rectangle(BEZEL_WINDOW[0] + 1.6, BEZEL_WINDOW[1] + 1.6), -0.8, taper=45)
    front -= Pos(0, 0, -0.01) * extrude(RectangleRounded(LENS[0] + 0.3, LENS[1] + 0.3, 1.5), LENS[2] + 0.01)
    # located by its two screws; the lens covers the door cut-out with 1.5 mm overlap all round
    for sx in (-BEZEL_SCREW_X, BEZEL_SCREW_X):
        front -= Pos(sx, 0, -2) * Cylinder(1.7, bt + 4, align=C)
        front -= Pos(sx, 0, bt - 1.7) * extrude(__import__('build123d').Circle(1.7), 1.71, taper=-45)
    # rear holder: pocket for the module, captive M3 nuts, cable exit
    pw, ph, pt = OLED_PCB
    holder = Pos(0, 0, -HOLDER_DEPTH) * extrude(RectangleRounded(bw - 4, bh - 6, 2.5), HOLDER_DEPTH)
    holder -= Pos(0, 0, -HOLDER_DEPTH + 2.0) * extrude(Rectangle(pw + 0.6, ph + 0.6), HOLDER_DEPTH)
    holder -= Pos(OLED_GLASS_OFFSET[0], 0, -2) * extrude(Rectangle(OLED_GLASS[0] + 1, OLED_GLASS[1] + 1), 3)
    holder -= Pos(-pw / 2 - 2, 0, -HOLDER_DEPTH + 2.0) * Box(6, 8, HOLDER_DEPTH, align=C)
    # open floor for the module's rear connector and pins; the PCB rests on 3 mm end ledges
    holder -= Pos(0, 0, -HOLDER_DEPTH - 1) * Box(pw - 6, ph - 4, 4, align=C)
    for sx in (-BEZEL_SCREW_X, BEZEL_SCREW_X):
        holder -= Pos(sx, 0, -HOLDER_DEPTH - 1) * Cylinder(1.7, HOLDER_DEPTH + 2, align=C)
        holder -= Pos(sx, 0, -HOLDER_DEPTH - 0.01) * extrude(__import__('build123d').RegularPolygon(3.2, 6), 2.6)
    lens = extrude(RectangleRounded(LENS[0], LENS[1], 1.5), LENS[2])
    return front, holder, lens


def main():
    lay = layout()
    base, outer = build_base(lay)
    bezel, holder, lens = build_bezel()
    parts = {
        'base': (base, 'Both versions. PETG or ASA (PC-FR or ABS-FR preferred for mains), 4 perimeters'),
        'lid_buttons': (build_lid(lay, outer, 'buttons'), 'Version A, buttons only; print front face down'),
        'button_caps_buttons': (build_caps('buttons'), 'Version A, five caps; print stems up'),
        'door_bezel': (bezel, 'Version A, outside the starter door'),
        'door_holder': (holder, 'Version A, inside the door; takes two M3 nuts'),
        'door_lens': (lens, 'Version A, 1.5 mm clear acrylic or polycarbonate'),
        'lid_display': (build_lid(lay, outer, 'display'), 'Version B, display window + buttons; print front face down'),
        'button_caps_display': (build_caps('display'), 'Version B, five caps; print stems up'),
        'lid_lens': (build_lid_lens(), 'Version B, 1.5 mm clear acrylic or polycarbonate in the lid pocket'),
    }
    # one printable file per cap; the caps are identical for both lids
    for label, kx, ky, d, sw_top in KEYS:
        cap = Cylinder(d / 2, LID_T + CAP_PROUD, align=C)
        cap = fillet(cap.edges().group_by(Axis.Z)[-1], min(1.0, d / 6))
        cap += Pos(0, 0, -FLANGE_T) * Cylinder((d + KEY_CLEAR) / 2 + FLANGE_LIP, FLANGE_T, align=C)
        stem_bottom = -PANEL_DEPTH + sw_top + STEM_GAP
        if -FLANGE_T - stem_bottom > 0.05:
            cap += Pos(0, 0, stem_bottom) * Cylinder(1.5, -FLANGE_T - stem_bottom, align=C)
        parts[f'cap_{label}'] = (cap, f'Both versions, {label} button cap; print stems up')
    manifest = {}
    for name, (shape, material) in parts.items():
        export_step(shape, OUT / f'{name}.step')
        export_stl(shape, OUT / f'{name}.stl', tolerance=0.02, angular_tolerance=0.2)
        bb = shape.bounding_box()
        manifest[name] = dict(material=material, volume_cm3=round(shape.volume / 1000, 1),
                              size_mm=[round(v, 1) for v in (bb.size.X, bb.size.Y, bb.size.Z)])
    ow, oh = outer
    lay.update(outer_mm=[round(ow, 1), round(oh, 1), round(lay['lid_inner_z'] + LID_T, 1)],
               board_to_box=dict(inner_x0=IN_X0, inner_y0=IN_Y0, centre=[(IN_X0 + IN_X1) / 2, (IN_Y0 + IN_Y1) / 2]),
               board_underside_z=BOARD_UNDERSIDE, door_cutout_mm=list(DOOR_CUTOUT),
               door_screw_holes=dict(diameter=3.4, centres_x=[-BEZEL_SCREW_X, BEZEL_SCREW_X], centre_y=0))
    manifest['_layout'] = lay
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == '__main__':
    main()
