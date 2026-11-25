"""Render preview images of the in-starter enclosure.  Run after build.py."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / 'out'
sys.path.insert(0, str(HERE))
import build as b  # noqa: E402

lay = json.loads((OUT / 'manifest.json').read_text())['_layout']
CX, CY = lay['board_to_box']['centre']
LZ = lay['lid_inner_z']


def load(name, dz=0.0):
    m = trimesh.load(OUT / f'{name}.stl')
    m.apply_translation([0, 0, dz])
    return m


def glb(path, xform):
    s = trimesh.load(path)
    meshes = []
    for node in s.graph.nodes_geometry:
        T, g = s.graph[node]
        m = s.geometry[g].copy()
        m.apply_transform(T)
        v = m.vertices * 1000.0
        m.vertices = xform(v)
        meshes.append(m)
    return trimesh.util.concatenate(meshes)


def main_board(dz=0.0):
    return glb(REPO / 'docs/3d/main.glb',
               lambda v: np.c_[v[:, 0] - CX, CY - v[:, 2], v[:, 1] + b.BOARD_UNDERSIDE + dz])


def panel(dz=0.0):
    px, py = b.PANEL_AT
    front = LZ - b.PANEL_DEPTH
    m = glb(REPO / 'mechanical/panel/pump-panel-rev-f-with-display.glb',
            lambda v: np.c_[px + v[:, 0] - CX, CY - (py + v[:, 2]), front - 1.6 + v[:, 1] + dz])
    # the OLED module moves to the door bezel
    c = m.triangles_center
    pxs, pys = c[:, 0] + CX - px, CY - c[:, 1] - py
    keep = ~((pxs > 11.9) & (pxs < 48.1) & (pys > 3.9) & (pys < 16.6) & (c[:, 2] > front + 0.9 + dz))
    m.update_faces(keep)
    return m


def faces(mesh, color, alpha=1.0, light=(0.3, -0.5, 0.8)):
    """Triangles and shaded colours. Large faces are split so depth sorting works."""
    v, f = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=3.0, max_iter=12)
    m = trimesh.Trimesh(v, f, process=False)
    n = m.face_normals
    shade = 0.45 + 0.55 * np.clip(n @ (np.array(light) / np.linalg.norm(light)), 0, 1)
    rgb = np.array(matplotlib.colors.to_rgb(color))
    cols = np.c_[np.clip(rgb[None, :] * shade[:, None], 0, 1), np.full(len(f), alpha)]
    return m.triangles, cols


def frame(ax, pts, elev, azim, title):
    lo, hi = pts.min(0), pts.max(0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    ax.set_title(title, fontsize=13, color='#1f2d3a', pad=0)


def render(name, items, elev, azim, title, size=(9, 9)):
    fig = plt.figure(figsize=size, dpi=130)
    ax = fig.add_subplot(111, projection='3d')
    pts, tris, cols = [], [], []
    for mesh, color, alpha in items:
        t, c = faces(mesh, color, alpha)
        tris.append(t); cols.append(c)
        pts.append(mesh.bounds)
    # one collection so matplotlib depth-sorts every triangle together
    ax.add_collection3d(Poly3DCollection(np.vstack(tris), facecolors=np.vstack(cols), edgecolors='none'))
    frame(ax, np.vstack(pts), elev, azim, title)
    fig.savefig(OUT / f'{name}.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


BOX = '#d9dee3'
LID = '#5b6b78'
PCB = '#2f6b3a'


def main():
    base, lid, caps = load('base'), load('lid', LZ), load('button_caps', LZ)
    mb, pn = main_board(), panel()
    lift = 55.0
    render('assembly-exploded', [(base, BOX, 1), (mb, PCB, 1), (pn.copy().apply_translation([0, 0, lift]), PCB, 1),
                                 (load('lid', LZ + lift), LID, 1), (load('button_caps', LZ + lift), '#c0392b', 1)],
           24, -58, 'In-starter box: base, main board, panel, lid (exploded)')
    render('assembly-closed', [(base, BOX, 1), (lid, LID, 1), (caps, '#c0392b', 1)],
           32, -55, f"Closed box  {lay['outer_mm'][0]} x {lay['outer_mm'][1]} x {lay['outer_mm'][2]} mm")
    render('base-with-board', [(base, BOX, 1), (mb, PCB, 1)], 58, -70, 'Base with R4 board: wall openings at each connector')
    render('lid-inside', [(load('lid'), LID, 1), (pn.copy().apply_translation([0, 0, -LZ]), PCB, 0.9),
                          (load('button_caps'), '#c0392b', 1)], -60, -60, 'Lid underside with panel F and caps')
    bez, hol, lens = load('door_bezel'), load('door_holder'), load('door_lens')
    render('door-bezel', [(bez.copy().apply_translation([0, 0, 14]), LID, 1), (lens.copy().apply_translation([0, 0, 8]), '#9fd3e6', 0.7),
                          (hol.copy().apply_translation([0, 0, -6]), BOX, 1)], 28, -60, 'Door display bezel (exploded): bezel, lens, holder', (8, 6))
    render('door-bezel-front', [(bez, LID, 1), (lens, '#9fd3e6', 1)], 60, -90, 'Door bezel from outside', (7, 5))


def section_polys(mesh, z):
    path = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    planar, T = path.to_2D()
    return [np.c_[p, np.zeros(len(p)), np.ones(len(p))] @ T.T for p in planar.discrete]


def lid_drawing():
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    lid = load('lid')
    loops = section_polys(lid, b.LID_T - 0.25)
    verts, codes = [], []
    for p in loops:
        verts += p[:, :2].tolist(); codes += [MPath.MOVETO] + [MPath.LINETO] * (len(p) - 2) + [MPath.CLOSEPOLY]
    fig, ax = plt.subplots(figsize=(8, 8.6), dpi=140)
    ax.add_patch(PathPatch(MPath(verts, codes), facecolor='#5b6b78', edgecolor='#2c3a45', lw=0.6))
    px, py = b.PANEL_AT
    for label, kx, ky, d, _ in b.KEYS:
        x, y = px + kx - CX, CY - (py + ky)
        ax.add_patch(plt.Circle((x, y), d / 2, color='#c0392b' if label == 'STOP' else '#2e8b57' if label == 'START' else '#d0d6db'))
    ow, oh, oz = lay['outer_mm']
    ax.annotate('', xy=(-ow / 2, -oh / 2 - 6), xytext=(ow / 2, -oh / 2 - 6), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text(0, -oh / 2 - 10, f'{ow} mm', ha='center', fontsize=9)
    ax.annotate('', xy=(ow / 2 + 6, -oh / 2), xytext=(ow / 2 + 6, oh / 2), arrowprops=dict(arrowstyle='<->', lw=0.8))
    ax.text(ow / 2 + 9, 0, f'{oh} mm', va='center', rotation=90, fontsize=9)
    ax.set_xlim(-ow / 2 - 8, ow / 2 + 16); ax.set_ylim(-oh / 2 - 14, oh / 2 + 6)
    ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(f'Lid front  ·  box {ow} × {oh} × {oz} mm  ·  buttons used with the starter door open', fontsize=10)
    fig.savefig(OUT / 'lid-front.png', bbox_inches='tight', facecolor='white')
    plt.close(fig)


def door_template():
    """Full-size door cut-out template. Print at 100 % and check the 50 mm scale bar."""
    w, h = b.DOOR_CUTOUT
    mm = 1 / 25.4
    fig = plt.figure(figsize=(120 * mm, 70 * mm))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-60, 60); ax.set_ylim(-35, 35); ax.set_aspect('equal'); ax.axis('off')
    bw, bh, _ = b.BEZEL
    ax.add_patch(plt.Rectangle((-bw / 2, -bh / 2), bw, bh, fill=False, ls='--', lw=0.4, ec='#888'))
    ax.add_patch(plt.Rectangle((-w / 2, -h / 2), w, h, fill=False, lw=0.6, ec='black'))
    for sx in (-b.BEZEL_SCREW_X, b.BEZEL_SCREW_X):
        ax.add_patch(plt.Circle((sx, 0), 1.7, fill=False, lw=0.6, ec='black'))
        ax.plot([sx - 3, sx + 3], [0, 0], lw=0.3, c='black'); ax.plot([sx, sx], [-3, 3], lw=0.3, c='black')
    ax.text(0, h / 2 + 2, f'CUT {w:g} × {h:g} mm', ha='center', fontsize=6)
    ax.text(0, -bh / 2 - 3.5, f'2 holes Ø3.4 at {2 * b.BEZEL_SCREW_X:g} mm centres  ·  dashed: bezel outline', ha='center', fontsize=5)
    ax.plot([-50 / 2, 50 / 2], [-31, -31], lw=0.8, c='black')
    ax.text(0, -30, '50 mm scale check', ha='center', fontsize=5)
    ax.text(0, 31, 'Starter door display cut-out  ·  print at 100 %', ha='center', fontsize=6)
    fig.savefig(OUT / 'door-cutout-template.pdf')
    fig.savefig(OUT / 'door-cutout-template.png', dpi=200, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
    lid_drawing()
    door_template()
