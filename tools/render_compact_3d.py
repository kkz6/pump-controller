#!/usr/bin/env python3
"""Depth-buffered orthographic renders of the actual exported CAD meshes."""
from pathlib import Path
import math,json,textwrap
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/compact';OUT.mkdir(parents=True,exist_ok=True)
REG='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,b=False):return ImageFont.truetype(BOLD if b else REG,n)
def load():
 s=trimesh.load(ROOT/'hardware/main-compact/exports/pump-controller-compact.glb',force='scene');s.apply_scale(1000);s.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));return s

def render(side):
 scene=load();width,height=1000,750
 direction=np.array([-.65,-.85,.68] if side=='front' else [.65,.85,-.68]);direction/=np.linalg.norm(direction)
 right=np.cross([0,0,1],direction);right/=np.linalg.norm(right);up=np.cross(direction,right)
 camera=np.stack([right,up,direction],axis=1)
 geometry=[]
 for node in scene.graph.nodes_geometry:
  if node=='clear_window_PURCHASED':continue # transparent purchased window
  transform,g=scene.graph[node];m=scene.geometry[g].copy();m.apply_transform(transform)
  faces=m.vertices[m.faces];norm=m.face_normals;keep=None
  if False:
   c=faces.mean(axis=1);keep=(c[:,2]<29)|((c[:,0]>24)&(c[:,1]>22));faces=faces[keep];norm=norm[keep]
  if len(faces)==0:continue
  col=np.array([.55,.60,.64])
  if getattr(m.visual,'kind',None)=='vertex':
   col=np.asarray(m.visual.face_colors)[:,:3]/255
   if keep is not None:col=col[keep]
  else:
   mat=getattr(m.visual,'material',None)
   if mat is not None:
    cc=getattr(mat,'baseColorFactor',getattr(mat,'main_color',None))
    if cc is not None:
     col=np.asarray(cc)[:3].astype(float)
     if col.max()>1:col/=255
  light=np.array([-.25,-.4,.9] if side=='front' else [.25,.4,-.9]);light/=np.linalg.norm(light)
  shade=.52+.46*np.maximum(norm@light,0)
  colors=np.clip(col*shade[:,None]+.04,0,1)*255
  geometry.append((faces@camera,colors))
 allpoints=np.concatenate([a.reshape(-1,3) for a,c in geometry]);lo=allpoints.min(axis=0);hi=allpoints.max(axis=0)
 scale=min((width-100)/(hi[0]-lo[0]),(height-100)/(hi[1]-lo[1]));offset=np.array([width/2-(lo[0]+hi[0])*scale/2,height/2+(lo[1]+hi[1])*scale/2])
 zbuf=np.full((height,width),-np.inf,dtype=np.float32);rgb=np.full((height,width,3),[237,242,245],dtype=np.uint8)
 for tris,colors in geometry:
  xy=tris[:,:,:2]*[scale,-scale]+offset
  for tri,depth,color in zip(xy,tris[:,:,2],colors):
   x0=max(0,int(np.floor(tri[:,0].min())));x1=min(width-1,int(np.ceil(tri[:,0].max())))
   y0=max(0,int(np.floor(tri[:,1].min())));y1=min(height-1,int(np.ceil(tri[:,1].max())))
   if x1<x0 or y1<y0:continue
   a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
   if abs(den)<1e-8:continue
   yy,xx=np.ogrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
   wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
   wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
   zz=wa*depth[0]+wb*depth[1]+wc*depth[2];sub=zbuf[y0:y1+1,x0:x1+1]
   mask=(wa>=-1e-6)&(wb>=-1e-6)&(wc>=-1e-6)&(zz>sub)
   sub[mask]=zz[mask];rgb[y0:y1+1,x0:x1+1][mask]=color.astype(np.uint8)
 return Image.fromarray(rgb)

front=render('front');back=render('back');front.save(OUT/'pcb-front.png');back.save(OUT/'pcb-back.png')
c=Image.new('RGB',(2100,1220),(237,242,245));d=ImageDraw.Draw(c)
d.text((60,36),'COMPACT PUMP CONTROLLER',font=font(42,True),fill='#153a49')
d.text((60,94),'100 × 75 mm · six-layer main PCB · component-body preview',font=font(27),fill='#496572')
d.text((65,160),'FRONT',font=font(24,True),fill='#17566a');d.text((1100,160),'REAR',font=font(24,True),fill='#17566a')
c.paste(front,(25,195));c.paste(back,(1075,195))
r=json.loads((ROOT/'hardware/main-compact/exports/model-verification.json').read_text())
notes=[f"Modeled populated thickness: {r['modeled_populated_thickness_mm']:.2f} mm. Main PCB is 1.6 mm thick.",'C1 is on the front; its box represents the conservative installed capacitor envelope.',"Y1’s nominal model is shorter than its 4.2 mm maximum drawing. These bounds are not an installed maximum.",'Connectors, received parts, lead trimming and assembly tolerances still require physical verification.']
for i,t in enumerate(notes):d.text((65,970+i*49),t,font=font(24),fill='#49616b')
c.save(OUT/'pcb-preview.png');print('Rendered compact front, rear and combined preview')
