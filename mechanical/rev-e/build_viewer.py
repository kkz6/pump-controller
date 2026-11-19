"""Offline WebGL enclosure viewer using the project's existing renderer."""
from pathlib import Path
import ast,base64,json,re
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/enclosure-rev-e'
source=(ROOT/'tools/build_3d_viewer.py').read_text();tree=ast.parse(source)
def pack(path):
 scene=trimesh.load(path,force='scene');rows=[]
 to_z=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])
 for node in scene.graph.nodes_geometry:
  transform,g=scene.graph[node];m=scene.geometry[g]
  v=trimesh.transform_points(m.vertices,to_z@transform);tri=v[m.faces]
  n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
  normals=np.repeat(np.round(n,6),3,axis=0)
  if getattr(m.visual,'kind',None)=='vertex':colors=np.asarray(m.visual.vertex_colors)[m.faces,:3].reshape(-1,3)/255
  else:
   mat=getattr(m.visual,'material',None);c=np.asarray(getattr(mat,'baseColorFactor',getattr(mat,'main_color',[155,160,165,255])))[:3].astype(float)
   if c.max()>1:c/=255
   colors=np.tile(c,(len(tri)*3,1))
  rows.append(np.column_stack([tri.reshape(-1,3),normals,colors]))
 data=np.concatenate(rows).astype('<f4');unique,indices=np.unique(data,axis=0,return_inverse=True)
 lo=unique[:,:3].min(axis=0);hi=unique[:,:3].max(axis=0);unique[:,:3]-=(lo+hi)/2;unique[:,:3]*=2/np.max(hi-lo)
 return {'vertices':base64.b64encode(unique.astype('<f4').tobytes()).decode(),'indices':base64.b64encode(indices.astype('<u4').tobytes()).decode(),'triangles':len(indices)//3}
html=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='html' for t in n.targets)))
data={'board':pack(OUT/'assembled.glb'),'assembly':pack(OUT/'exploded.glb')}
html=html.replace('Pump controller — 3D model','Rev E enclosure — 3D model').replace('Pump controller · Rev B','Pump controller · Rev E enclosure').replace('Rotate the model to see the top, underside and assembly concept.','Rotate the standalone enclosure and exploded assembly; all models are embedded.')
html=html.replace('Controller PCB','Assembled enclosure').replace('Starter assembly concept','Exploded enclosure').replace('90 × 70 mm · 208 component bodies','170 × 150 × 90 mm case body').replace('Representative starter · fit not verified','Exploded view · walls sectioned')
html=re.sub(r'<footer>.*?</footer>','<footer><strong>Mechanical prototype.</strong> Print parts have watertight meshes and modeled clearances against the current Rev E PCB bodies; material, actual plug fit and switch travel still need validation. Some component bodies are approximate. The case has no claimed flame or ingress rating. Cyan OLED content is illustrative. <span id="assembly-note" hidden>The exploded view moves parts apart and sections the upper front/left base walls for visibility.</span><div id="error"></div></footer>',html,flags=re.S)
(OUT/'viewer.html').write_text(html.replace('__DATA__',json.dumps(data,separators=(',',':'))))
print('Offline viewer created:',OUT/'viewer.html')
