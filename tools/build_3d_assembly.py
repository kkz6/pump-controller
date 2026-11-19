"""Illustrative assembly matching the supplied single-phase starter style.

Retains the two capacitors, 2-pole contactor, meters and bottom terminal strip.
All external volumes and cable paths are illustrative, not measured parts.
Requires numpy/trimesh. No electrical CAD is modified.
"""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/3d'
parser=argparse.ArgumentParser();parser.add_argument('--board',default='pump-controller-rev-c.glb')
args=parser.parse_args();source=OUT/args.board
GRAY=[181,185,180,255];DARK=[45,49,49,255];BLACK=[22,27,29,255]
WHITE=[226,227,221,255];GREEN=[31,117,72,255];BLUE=[37,104,174,255]
RED=[183,43,43,255];YELLOW=[210,181,41,255];BROWN=[113,71,36,255]

# Native GLB is metres/Y-up. The assembly is first built in millimetres/Z-up.
board=trimesh.load(source,force='scene')
to_mm=np.eye(4);to_mm[:3,:3]*=1000
to_z=trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0])
position=trimesh.transformations.translation_matrix([165,130,18])
scene=board.copy();scene.apply_transform(position@to_z@to_mm)

def add(mesh,name,color):
    mesh.visual.vertex_colors=color;scene.add_geometry(mesh,node_name=name,geom_name=name)
def box(name,center,size,color):
    m=trimesh.creation.box(extents=size);m.apply_translation(center);add(m,name,color)
def cylinder(name,center,radius,height,color,axis=(0,0,1)):
    m=trimesh.creation.cylinder(radius,height,sections=32)
    m.apply_transform(trimesh.geometry.align_vectors([0,0,1],axis));m.apply_translation(center);add(m,name,color)
def cable(name,points,color,r=1.1):
    for i,(a,b) in enumerate(zip(points,points[1:])):
        a=np.array(a,dtype=float);b=np.array(b,dtype=float)
        m=trimesh.creation.cylinder(r,np.linalg.norm(b-a),sections=10)
        m.apply_transform(trimesh.geometry.align_vectors([0,0,1],b-a));m.apply_translation((a+b)/2)
        add(m,f'{name}_{i}',color)

# 270x270x110 is only the representative modeling envelope, not a measurement.
box('enclosure_base',[135,135,-2],[270,270,4],GRAY)
box('enclosure_back_wall',[135,268,54],[270,4,112],GRAY)
box('enclosure_left_cutaway',[2,135,16],[4,266,36],GRAY)
box('enclosure_right_cutaway',[268,135,16],[4,266,36],GRAY)
box('enclosure_front_cutaway',[135,2,7],[270,4,18],GRAY)
box('mounting_backplate',[135,135,2],[256,256,2],GRAY)

# Retained single-phase starting components in the observed arrangement.
# Capacitor dimensions and mounting are approximate; ratings/wiring unchanged.
cylinder('retained_yellow_capacitor',[57,166,29],21,113,YELLOW,(0,1,0))
cylinder('retained_white_capacitor',[113,188,30],23,126,WHITE,(0,1,0))
box('capacitor_support_1',[57,166,7],[45,18,6],DARK)
box('capacitor_support_2',[113,188,7],[49,18,6],DARK)
box('retained_2pole_contactor_body',[213,203,32],[61,66,48],BLACK)
box('retained_contactor_face',[213,203,58],[58,30,4],WHITE)
for y in [175,231]:
    for x in [196,230]:
        cylinder(f'contactor_terminal_{x}_{y}',[x,y,53],4.3,2,[160,145,99,255])
        box(f'contactor_terminal_block_{x}_{y}',[x,y,47],[14,13,10],DARK)
# Bottom strip, not a newly assigned terminal numbering scheme.
box('retained_bottom_terminal_strip',[115,31,14],[100,22,21],BLACK)
for x in [76,92,108,124,140,156]:
    for y in [25,37]:cylinder(f'terminal_strip_screw_{x}_{y}',[x,y,25.5],3.4,1.7,[175,178,173,255])
# CT shown on a single motor conductor only, clear of capacitor components.
torus=trimesh.creation.torus(major_radius=10,minor_radius=3.5,major_sections=32,minor_sections=10)
torus.apply_translation([191,29,22]);add(torus,'proposed_motor_current_transformer',DARK)
cable('one_motor_conductor_through_CT',[[191,29,-4],[191,29,42],[156,37,42]],BROWN,1.4)
cable('other_motor_conductor_beside_CT',[[217,29,-4],[217,29,37],[140,37,37]],BLUE,1.4)

# Model shows only two current PCB mounting points. Additional restraint,
# insulation shields and screw clearances are a separate mechanical design.
for y in [63,127]:cylinder(f'proposed_pcb_standoff_{y}',[252,y,9],3.4,18,WHITE)

# Exploded front cover beside the case, exterior visible; meter backs extend
# below the cover. This is not a hinge-clearance or close-door simulation.
# Four plate pieces leave a real rectangular OLED aperture. Its 26x9mm size
# is illustrative, not a cutting template; actual bezel/window needs measuring.
box('front_cover_left_of_OLED_cutout',[-164.5,135,5],[231,270,4],GRAY)
box('front_cover_right_of_OLED_cutout',[-16.5,135,5],[13,270,4],GRAY)
box('front_cover_below_OLED_cutout',[-36,79.75,5],[26,159.5,4],GRAY)
box('front_cover_above_OLED_cutout',[-36,219.25,5],[26,101.5,4],GRAY)
for y in [202,113]:
    box(f'retained_analog_meter_back_{y}',[-193,y,-12],[59,62,34],BLACK)
    box(f'retained_analog_meter_bezel_{y}',[-193,y,11],[64,64,8],BLACK)
    box(f'retained_analog_meter_face_{y}',[-193,y,15.2],[54,54,.4],WHITE)
    cable(f'meter_needle_{y}',[[-193,y-16,15.6],[-207,y+14,15.6]],DARK,.55)
box('retained_front_breaker',[-113,214,16],[28,50,19],WHITE)
box('retained_breaker_toggle',[-113,214,29],[18,17,8],BLUE)
# Small OLED shown near the hinge edge; no large tablet-like display.
box('OLED_carrier_36x12p5_behind_cover',[-36,164,.5],[36,12.5,1.6],GREEN)
box('OLED_glass_approximate_behind_cover',[-36,164,2.1],[30,11,1.6],BLACK)
box('OLED_active_22p38x5p58',[-36,164,3.0],[22.38,5.58,.2],[53,176,208,255])
buttons=[('START',-94,102,GREEN,11),('STOP',-43,102,RED,11),
         ('MODE',-69,49,GRAY,8)]
for label,x,y,color,radius in buttons:
    cylinder(label+'_bezel',[x,y,9.5],radius+2,4,DARK)
    cylinder(label+'_button',[x,y,13],radius,4,color)

# Existing and proposed cable bundles are destination illustrations only;
# they do not identify the photographed wiring or provide electrical pin maps.
cable('retained_capacitor_bundle_illustrative',[[57,109,25],[58,65,18],[92,37,29]],DARK,2)
cable('retained_second_capacitor_bundle_illustrative',[[113,125,25],[119,65,18],[124,37,29]],DARK,2)
cable('retained_contactor_bundle_illustrative',[[213,174,38],[150,148,20],[140,38,30]],DARK,2)
cable('proposed_controller_power_branch_illustrative',[[156,25,29],[170,48,16],[172,123,28]],BROWN,1.1)
cable('proposed_coil_control_pair_illustrative',[[232,175,35],[258,156,19],[182,111,27]],BLUE,1.1)
cable('proposed_CT_pair_illustrative',[[200,29,22],[227,45,13],[191,70,26]],BLACK,.8)
cable('proposed_panel_control_loom_illustrative',[[242,100,28],[248,145,23],[7,145,23],[-14,127,12],[-90,111,12]],DARK,2.1)
cable('proposed_OLED_harness_LENGTH_UNVERIFIED',[[247,98,27],[256,155,25],[0,155,20],[-18,164,.5]],BLUE,.9)
cable('probe_cable_exit',[[227,68,25],[235,20,15],[235,-16,15]],DARK,1.8)
cable('RF_coax',[[227,106,22],[258,158,20],[285,246,22]],BLACK,.7)
cylinder('external_antenna_base',[285,246,25],5,10,BLACK)
cylinder('external_antenna',[285,246,62],3,66,BLACK)

scene.metadata={'title':'Single-phase starter retrofit assembly concept',
 'board_source':args.board,'external_geometry':'Illustrative volumes based on starter style; dimensions are not measured',
 'enclosure_modeling_envelope_mm':[270,270,110],
 'retained_components':['Two starting/running capacitors','Two-pole contactor','Bottom terminal strip','Two analog meters','Front breaker'],
 'panel_buttons':['START','STOP','MODE'],
 'settings_controls':'SET/RESET and NEXT/+ are on the controller PCB only',
 'oled_module_mm':[36,12.5],
 'oled_mount':'Behind an illustrative26x9mm cover aperture; not a cutting template',
 'board_position':'Lower right concept only; fit, depth, barriers and access unverified',
 'cover':'Exploded beside enclosure with exterior visible; hinge/mating geometry not designed',
 'cables':'Destination illustration only, not electrical routing; OLED cable exceeds the earlier provisional100mm allowance in this concept and needs redesign or timing validation',
 'unknowns':['Actual enclosure dimensions','Capacitor/control wiring','Coil voltage','Overload implementation','Earth-bond routing','Door closure','OLED harness length and signal integrity']}
scene.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]));scene.apply_scale(.001)
(OUT/'starter-assembly-concept.glb').write_bytes(scene.export(file_type='glb'))
manifest=dict(scene.metadata);manifest['board_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest();manifest['not_for_fabrication']=True
(ROOT/'hardware/3d/assembly-concept.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(OUT/'starter-assembly-concept.glb')
