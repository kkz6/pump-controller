#!/usr/bin/env python3
"""Depth-buffered orthographic renders of the actual exported CAD meshes."""
from pathlib import Path
import math,json,textwrap
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/enclosure-rev-e'
REG='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(n,b=False):return ImageFont.truetype(BOLD if b else REG,n)
def load(name):
 s=trimesh.load(OUT/(name+'.glb'),force='scene');s.apply_scale(1000);s.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));return s

def render(name,exploded=False):
 scene=load(name);width,height=1450,1150
 direction=np.array([-.65,-.85,.68]);direction/=np.linalg.norm(direction)
 right=np.cross([0,0,1],direction);right/=np.linalg.norm(right);up=np.cross(direction,right)
 camera=np.stack([right,up,direction],axis=1)
 geometry=[]
 for node in scene.graph.nodes_geometry:
  if node=='clear_window_PURCHASED':continue # transparent purchased window
  transform,g=scene.graph[node];m=scene.geometry[g].copy();m.apply_transform(transform)
  faces=m.vertices[m.faces];norm=m.face_normals;keep=None
  if False and exploded and node=='base':
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
  light=np.array([-.25,-.4,.9]);light/=np.linalg.norm(light)
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
 canvas=Image.new('RGB',(2100,1500),(237,242,245));canvas.paste(Image.fromarray(rgb),(20,210));draw=ImageDraw.Draw(canvas)
 draw.text((90,42),'PUMP CONTROLLER · REV E',font=font(48,True),fill='#153a49')
 draw.text((90,112),'Separate enclosure — exploded assembly' if exploded else 'Standalone enclosure with small OLED and five buttons',font=font(30),fill='#496572')
 if exploded:
  notes=[('LID + CAPTIVE BUTTONS','Different STOP and tactile stems; fit and travel need bench adjustment.'),('OLED + WINDOW','Plug-in module, screw-fastened retainer and clear window. Cyan screen is illustrative.'),('PANEL + CARRIER','Native Rev E panel geometry; four corner bolts and removable harness.'),('MAIN BOARD GUARD','Separate screw-retained cover above the populated main-board CAD.'),('BASE + CABLE CLAMPS','Four main PCB standoffs, 18 mm tall. Separate mains, live-CT and sensor entries.')]
 else:
  notes=[('170 ×150 ×90 mm','Body dimensions; glands and raised controls add to the outside size.'),('FIVE FRONT BUTTONS','START · STOP · MODE · SET · NEXT. Existing buttons need isolated auxiliary contacts.'),('OPTIONAL KEY POSITION','Blank plate is fitted. A separate 22.5 mm adapter is supplied for fit review.'),('PLUG-IN OLED','0.91in Waveshare 14657, PH2.0 cable. Cyan screen is illustrative; no user soldering.'),('MECHANICAL PROTOTYPE','Material, temperature and electrical enclosure qualification remain unverified.')]
 for i,(title,body) in enumerate(notes):
  y=265+i*204;draw.text((1510,y),title,font=font(25,True),fill='#17566a')
  for j,line in enumerate(textwrap.wrap(body,40)):draw.text((1510,y+42+j*35),line,font=font(22),fill='#49616b')
 footer='Current Rev E PCB body preview; approximate bodies and physical fit still need verification. '
 footer+=('Upper base walls are cut away in this image only.' if exploded else 'No measured DOL fit or enclosure rating is asserted.')
 draw.text((90,1435),footer,font=font(22),fill='#6b4f36')
 canvas.save(OUT/(name+'-preview.png'))
render('assembled');render('exploded',True)
print('Rendered assembled-preview.png and exploded-preview.png')
