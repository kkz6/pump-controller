"""Build the offline inspection view from the compact board and Rev E panel CAD."""
from pathlib import Path
import base64
import json
import zlib

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/compact"
TO_MM_Z_UP = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]) * 1000
TO_MM_Z_UP[3, 3] = 1
PANEL_ORIGIN = np.array([129, -23, 10])  # exploded display, millimetres
PANEL_SHIFT = PANEL_ORIGIN - [55, 90, 72.9]
PANEL_BODIES = {
    "native_panel", "OLED_module_PCB", "OLED_glass_allowance", "OLED_active",
    "switch_STOP", "actuator_STOP", "panel_J7_PH4_allowance",
}
vertices = []
indices = []
vertex_count = 0


def append_mesh(mesh, transform, override=None):
    global vertex_count
    pos = trimesh.transform_points(mesh.vertices, transform)
    faces = np.asarray(mesh.faces)
    cached = mesh._cache.cache.get("vertex_normals")
    if cached is None:
        tri = np.asarray(mesh.vertices)[faces]
        face_normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        cached = np.zeros_like(mesh.vertices)
        for corner in range(3):
            np.add.at(cached, faces[:, corner], face_normal)
    normal = cached @ np.linalg.inv(transform[:3, :3])
    normal /= np.maximum(np.linalg.norm(normal, axis=1)[:, None], 1e-12)
    if override is not None:
        colors = np.broadcast_to(override, pos.shape)
    elif mesh.visual.kind == "vertex":
        colors = mesh.visual.vertex_colors[:, :3]
    else:
        mat = getattr(mesh.visual, "material", None)
        rgb = getattr(mat, "baseColorFactor", None)
        if rgb is None:
            rgb = getattr(mat, "main_color", [160, 165, 169])
        colors = np.broadcast_to(np.asarray(rgb)[:3], pos.shape)
    vertices.append(np.column_stack([pos, normal, colors / 255]))
    indices.append(faces.ravel() + vertex_count)
    vertex_count += len(pos)


def add_cad(path, panel=False):
    scene = trimesh.load(ROOT / path, force="scene")
    for node in sorted(scene.graph.nodes_geometry):
        if panel and node not in PANEL_BODIES and not node.startswith("plunger_"):
            continue
        transform, name = scene.graph[node]
        transform = TO_MM_Z_UP @ transform
        if panel:
            transform[:3, 3] += PANEL_SHIFT
        append_mesh(scene.geometry[name], transform)


def plug(center, size):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    append_mesh(mesh, np.eye(4), [233, 228, 202])


def cable(points, radius, color):
    # A Catmull-Rom curve keeps the end tangents aligned with the connector axes.
    knots = np.array([points[0], *points, points[-1]], dtype=float)
    smooth = []
    for a, b, c, d in zip(knots, knots[1:], knots[2:], knots[3:]):
        for t in np.linspace(0, 1, 7, endpoint=False):
            smooth.append(.5 * (2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t**2 + (-a+3*b-3*c+d)*t**3))
    smooth.append(knots[-1])
    # Sweep one continuous tube so adjacent segments share one surface.
    smooth = np.array(smooth)
    tangent = np.gradient(smooth, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    across = np.cross(tangent, [0, 0, 1])
    across /= np.linalg.norm(across, axis=1)[:, None]
    upright = np.cross(tangent, across)
    sides = 12
    angles = np.linspace(0, 2*np.pi, sides, endpoint=False)
    rings = (smooth[:, None, :] + radius *
             (across[:, None, :] * np.cos(angles)[None, :, None] +
              upright[:, None, :] * np.sin(angles)[None, :, None]))
    faces = []
    for ring in range(len(rings) - 1):
        for side in range(sides):
            a = ring * sides + side
            b = ring * sides + (side + 1) % sides
            faces.extend([[a, b, b + sides], [a, b + sides, a + sides]])
    body = trimesh.Trimesh(vertices=rings.reshape(-1, 3), faces=faces, process=False)
    append_mesh(body, np.eye(4), color)


def encode(array, dtype):
    raw = array.astype(dtype).tobytes()
    return base64.b64encode(zlib.compress(raw, 9)).decode("ascii")


add_cad("hardware/main-compact/exports/pump-controller-compact.glb")
add_cad("output/enclosure-rev-e/assembled.glb", panel=True)
# Right-facing main and rear top-edge panel GH connectors. The plastic plugs
# and bundled cable are visual guides; their geometry is not supplier CAD.
plug([101.0,-44,3.3], [4.1,15.5,2.8])
plug([159,-22.0,8.2], [15.5,3.8,2.8])
cable([[103,-44,3.3],[110,-44,3.3],[118,-37,4.2],[122,-20,6],
       [131,-8,8],[146,-5,8.2],[157,-9,8.2],[159,-15,8.2],[159,-20.1,8.2]],
      1.6, [15,164,152])
# J7 faces the right panel edge. Module-end termination remains illustrative.
plug([190.1,-44,6], [3.8,8.3,3.2])
cable([[192,-44,6],[198,-44,6],[203,-39,7],[204,-29,11],[198,-22,15],
       [189,-23,17.2],[183,-29,17.5],[178,-33,17.6],[174,-33,18.5]],
      .95, [238,145,43])
plug([173.7,-33,18.3], [3.8,5.2,1.7])
data = {"vertices":encode(np.concatenate(vertices),"<f4"),
        "indices":encode(np.concatenate(indices),"<u4")}
template = Path(__file__).with_name("compact_connection_view.html").read_text()
OUT.mkdir(parents=True, exist_ok=True)
(OUT/"panel-connections.html").write_text(template.replace("__DATA__", json.dumps(data, separators=(",", ":"))))
