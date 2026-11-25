"""Export both enclosure versions as one GLB with a named, coloured node per part (mm, z up)."""
import trimesh
from trimesh.visual.material import PBRMaterial

import render as r

GREY, SLATE, PCB, RED, GLASS = (0.78, 0.81, 0.84, 1), (0.33, 0.40, 0.46, 1), (0.16, 0.42, 0.23, 1), (0.75, 0.22, 0.17, 1), (0.62, 0.83, 0.90, 0.55)


def tint(mesh, name, rgba):
    m = mesh.copy()
    m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
        name=name, baseColorFactor=rgba, metallicFactor=0.0, roughnessFactor=0.65,
        alphaMode='BLEND' if rgba[3] < 1 else 'OPAQUE', doubleSided=True))
    return m


def main():
    lz = r.LZ
    scene = trimesh.Scene()

    def add(name, mesh, rgba):
        scene.add_geometry(tint(mesh, name, rgba), node_name=name, geom_name=name)

    add('base', r.load('base'), GREY)
    add('main_board', r.main_board(), PCB)
    for v in ('buttons', 'display'):
        add(f'panel_{v}', r.panel(v), PCB)
        add(f'lid_{v}', r.load(f'lid_{v}', lz), SLATE)
        add(f'button_caps_{v}', r.load(f'button_caps_{v}', lz), RED)
    add('lid_lens', r.load('lid_lens', lz + 0.0).apply_translation(lens_offset()), GLASS)
    dx = r.lay['outer_mm'][0] / 2 + 55
    for name, rgba in [('door_bezel', SLATE), ('door_lens', GLASS), ('door_holder', GREY)]:
        add(name, r.load(name).apply_translation([dx, 0, 20]), rgba)
    out = r.OUT / 'enclosure-assembly.glb'
    scene.export(out)
    print(out, round(out.stat().st_size / 1e6, 2), 'MB')


def lens_offset():
    b = r.b
    (gx0, gy0), (gx1, gy1) = b.PANEL_OLED_GLASS
    px, py = b.VARIANTS['display']['panel_at']
    return [px + (gx0 + gx1) / 2 - r.CX, r.CY - (py + (gy0 + gy1) / 2), 0]


if __name__ == '__main__':
    main()
