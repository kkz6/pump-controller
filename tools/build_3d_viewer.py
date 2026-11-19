"""Create a standalone offline WebGL viewer from the two GLB deliverables.

Requires numpy and trimesh. Geometry is embedded; no web requests, package
CDNs, local server or browser plug-in are needed at viewing time.
"""
from pathlib import Path
import argparse,base64,json
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/3d'
parser=argparse.ArgumentParser();parser.add_argument('--board',default='pump-controller-rev-c.glb');parser.add_argument('--revision',default='Rev C');parser.add_argument('--components',type=int,default=208)
args=parser.parse_args()

def pack(path):
    scene=trimesh.load(path,force='scene')
    vertices=[];indices=[];offset=0
    for node in scene.graph.nodes_geometry:
        transform,geom=scene.graph[node];mesh=scene.geometry[geom]
        if not isinstance(mesh,trimesh.Trimesh):continue
        # Both GLB exports are metres/Y-up; display them in a Z-up orbit view.
        to_z=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])
        transform=to_z@transform
        p=trimesh.transform_points(mesh.vertices,transform)
        tri=np.asarray(mesh.vertices)[np.asarray(mesh.faces)]
        face_normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        local_normal=np.zeros_like(np.asarray(mesh.vertices))
        for corner in range(3):np.add.at(local_normal,np.asarray(mesh.faces)[:,corner],face_normal)
        normal=local_normal@np.linalg.inv(transform[:3,:3])
        normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
        material=getattr(mesh.visual,'material',None)
        color=getattr(material,'baseColorFactor',None)
        if color is None:color=getattr(material,'main_color',[155,160,165,255])
        color=np.asarray(color)[:3].astype(float)
        if np.max(color)>1:color/=255
        colors=np.tile(color,(len(p),1))
        if getattr(mesh.visual,'kind',None)=='vertex':colors=np.asarray(mesh.visual.vertex_colors)[:,:3]/255
        vertices.append(np.column_stack([p,normal,colors]))
        indices.append(np.asarray(mesh.faces).ravel()+offset);offset+=len(p)
    v=np.concatenate(vertices);idx=np.concatenate(indices).astype('<u4')
    minimum=v[:,:3].min(axis=0);maximum=v[:,:3].max(axis=0)
    v[:,:3]-=(minimum+maximum)/2;v[:,:3]*=2/np.max(maximum-minimum)
    return {'vertices':base64.b64encode(v.astype('<f4').tobytes()).decode(),
            'indices':base64.b64encode(idx.tobytes()).decode(),
            'triangles':len(idx)//3}

data={'board':pack(OUT/args.board),
      'assembly':pack(OUT/'starter-assembly-concept.glb')}
html=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pump controller — 3D model</title><style>
*{box-sizing:border-box}body{margin:0;background:#e8edf1;color:#173347;font:15px system-ui,sans-serif}header{padding:22px 30px;background:#fff;border-bottom:1px solid #ccd6df;display:flex;gap:18px;align-items:center;flex-wrap:wrap}h1{font-size:22px;margin:0}header p{margin:5px 0 0;color:#566775;font-size:13px}nav{display:flex;gap:7px;flex-wrap:wrap;margin-left:auto}button,select{font:inherit;border:1px solid #bacad4;border-radius:8px;background:#fff;padding:9px 13px;color:#173347;cursor:pointer}button:hover{background:#e8f3f4}select{background:#173347;color:white}main{position:relative;height:calc(100vh - 190px);min-height:420px}canvas{width:100%;height:100%;display:block;touch-action:none}.hint{position:absolute;left:25px;top:18px;color:#4c6374;font-size:13px;pointer-events:none}.badge{position:absolute;right:25px;top:18px;background:white;padding:10px 14px;border-radius:8px;color:#14756e;pointer-events:none}footer{padding:16px 30px;background:#fff;border-top:1px solid #ccd6df;font-size:13px;line-height:1.5}footer strong{color:#a6601e}#error{color:#a12222;font-size:15px}</style>
<header><div><h1>Pump controller · Rev B</h1><p>Rotate the model to see the top, underside and assembly concept.</p></div><nav><select id="choice"><option value="board">Controller PCB</option><option value="assembly">Starter assembly concept</option></select><button id="iso">Perspective</button><button id="top">Top</button><button id="bottom">Bottom</button><button id="reset">Reset zoom</button></nav></header>
<main><canvas id="view"></canvas><div class="hint">Drag to rotate · Scroll or pinch to zoom</div><div class="badge" id="badge">90 × 70 mm · 208 component bodies</div></main>
<footer><strong>Engineering visualization — not a fabrication or installation release.</strong> The PCB uses its actual placement; 198 bodies come from the KiCad library and 10 are simplified envelopes. Connector plugs, lead forming and installed clearances need checking. <span id="assembly-note" hidden>The 270 × 270 × 110 mm enclosure envelope, retained capacitors, 2-pole contactor, meters, buttons and cable paths are illustrative; actual starter fit is unknown. Front: green START, red STOP and gray MODE. SET/RESET and NEXT/+ stay on the PCB. OLED carrier: 36 × 12.5 mm. The exploded front cover shows the controls without hiding the board. Wire paths show destinations only; use the wiring guide for terminal connections. The illustrated OLED cable length is unverified and exceeds the earlier provisional100mm allowance.</span><div id="error"></div></footer>
<script>const DATA=__DATA__;
const canvas=document.getElementById('view'),gl=canvas.getContext('webgl2',{antialias:true});
function fail(s){document.getElementById('error').textContent=s;throw Error(s)}if(!gl)fail('This browser needs WebGL 2 enabled to display the model. The STEP and GLB files can also be opened in a CAD/3D viewer.');
const vertex=`#version 300 es
in vec3 p;in vec3 n;in vec3 c;uniform mat4 view;uniform mat4 projection;out vec3 color;out vec3 normal;void main(){gl_Position=projection*view*vec4(p,1.);normal=mat3(view)*n;color=c;}`;
const fragment=`#version 300 es
precision highp float;in vec3 color;in vec3 normal;out vec4 outColor;void main(){vec3 n=normalize(normal);float diffuse=max(dot(n,normalize(vec3(.4,.6,1.))),0.);float fill=max(dot(n,normalize(vec3(-.8,-.4,.5))),0.);outColor=vec4(color*(.48+.45*diffuse+.22*fill),1.);}`;
function shader(type,source){let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))fail(gl.getShaderInfoLog(s));return s}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))fail(gl.getProgramInfoLog(program));gl.useProgram(program);
const vb=gl.createBuffer(),ib=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);
for(const [i,name] of ['p','n','c'].entries()){let l=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,36,i*12)}
function decode(s){let bytes=atob(s),a=new Uint8Array(bytes.length);for(let i=0;i<bytes.length;i++)a[i]=bytes.charCodeAt(i);return a.buffer}
let count=0,ax=-.75,az=-.6,distance=4.2;
function load(name){const d=DATA[name];let v=new Float32Array(decode(d.vertices)),i=new Uint32Array(decode(d.indices));gl.bufferData(gl.ARRAY_BUFFER,v,gl.STATIC_DRAW);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,i,gl.STATIC_DRAW);count=i.length;document.getElementById('badge').textContent=name==='board'?'90 × 70 mm · 208 component bodies':'Representative starter · fit not verified';document.getElementById('assembly-note').hidden=name!=='assembly';ax=-.75;az=-.6;distance=4.2;render()}
function multiply(a,b){let r=new Float32Array(16);for(let c=0;c<4;c++)for(let row=0;row<4;row++)for(let k=0;k<4;k++)r[c*4+row]+=a[k*4+row]*b[c*4+k];return r}
function render(){const ratio=Math.min(devicePixelRatio,2),w=Math.round(canvas.clientWidth*ratio),h=Math.round(canvas.clientHeight*ratio);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}gl.viewport(0,0,w,h);gl.clearColor(.91,.93,.95,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);let x=[1,0,0,0,0,Math.cos(ax),Math.sin(ax),0,0,-Math.sin(ax),Math.cos(ax),0,0,0,0,1],z=[Math.cos(az),Math.sin(az),0,0,-Math.sin(az),Math.cos(az),0,0,0,0,1,0,0,0,0,1],m=multiply(x,z);m[14]=-distance;let f=1/Math.tan(Math.PI/8),aspect=w/h,near=.1,far=30,p=new Float32Array([f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);gl.uniformMatrix4fv(gl.getUniformLocation(program,'view'),false,m);gl.uniformMatrix4fv(gl.getUniformLocation(program,'projection'),false,p);gl.drawElements(gl.TRIANGLES,count,gl.UNSIGNED_INT,0)}
let pointers=new Map(),pinch=0;canvas.onpointerdown=e=>{canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,[e.clientX,e.clientY])};canvas.onpointerup=canvas.onpointercancel=e=>{pointers.delete(e.pointerId);pinch=0};canvas.onpointermove=e=>{if(!pointers.has(e.pointerId))return;let old=pointers.get(e.pointerId);pointers.set(e.pointerId,[e.clientX,e.clientY]);if(pointers.size===1){az+=(e.clientX-old[0])*.008;ax+=(e.clientY-old[1])*.008}else{let a=[...pointers.values()],d=Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);if(pinch)distance=Math.max(1.7,Math.min(12,distance*pinch/d));pinch=d}render()};canvas.addEventListener('wheel',e=>{e.preventDefault();distance=Math.max(1.7,Math.min(12,distance*Math.exp(e.deltaY*.001)));render()},{passive:false});window.addEventListener('resize',render);document.getElementById('choice').onchange=e=>load(e.target.value);document.getElementById('iso').onclick=()=>{ax=-.75;az=-.6;render()};document.getElementById('top').onclick=()=>{ax=0;az=0;render()};document.getElementById('bottom').onclick=()=>{ax=Math.PI;az=0;render()};document.getElementById('reset').onclick=()=>{distance=4.2;render()};const initial=new URLSearchParams(location.search).get('model')==='assembly'?'assembly':'board';document.getElementById('choice').value=initial;load(initial);</script></html>'''
html=html.replace('Rev B',args.revision).replace('208 component',str(args.components)+' component').replace('198 bodies',str(args.components-10)+' bodies')
(OUT/'viewer.html').write_text(html.replace('__DATA__',json.dumps(data,separators=(',',':'))))
print('Offline viewer:',OUT/'viewer.html')
print({k:v['triangles'] for k,v in data.items()})
