"""Export the assembled enclosure as one GLB with a named, coloured node per part (mm, z up)."""
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

import render as r

COL = {
    'base': (0.78, 0.81, 0.84, 1.0),
    'main_board': (0.16, 0.42, 0.23, 1.0),
    'panel': (0.16, 0.42, 0.23, 1.0),
    'lid': (0.33, 0.40, 0.46, 1.0),
    'button_caps': (0.75, 0.22, 0.17, 1.0),
    'door_bezel': (0.33, 0.40, 0.46, 1.0),
    'door_lens': (0.62, 0.83, 0.90, 0.55),
    'door_holder': (0.78, 0.81, 0.84, 1.0),
}


def tint(mesh, name):
    m = mesh.copy()
    m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
        name=name, baseColorFactor=COL[name], metallicFactor=0.0, roughnessFactor=0.65,
        alphaMode='BLEND' if COL[name][3] < 1 else 'OPAQUE', doubleSided=True))
    return m


def main():
    lz = r.LZ
    scene = trimesh.Scene()
    scene.add_geometry(tint(r.load('base'), 'base'), node_name='base', geom_name='base')
    scene.add_geometry(tint(r.main_board(), 'main_board'), node_name='main_board', geom_name='main_board')
    scene.add_geometry(tint(r.panel(), 'panel'), node_name='panel', geom_name='panel')
    scene.add_geometry(tint(r.load('lid', lz), 'lid'), node_name='lid', geom_name='lid')
    scene.add_geometry(tint(r.load('button_caps', lz), 'button_caps'), node_name='button_caps', geom_name='button_caps')
    dx = r.lay['outer_mm'][0] / 2 + 55
    for name, dz in [('door_bezel', 0.0), ('door_lens', 0.0), ('door_holder', 0.0)]:
        m = r.load(name)
        m.apply_translation([dx, 0, 20 + dz])
        scene.add_geometry(tint(m, name), node_name=name, geom_name=name)
    out = r.OUT / 'enclosure-assembly.glb'
    scene.export(out)
    print(out, round(out.stat().st_size / 1e6, 2), 'MB')


if __name__ == '__main__':
    main()
