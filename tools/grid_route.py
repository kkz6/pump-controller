from pathlib import Path
import json,math,heapq,time
import numpy as np
B=Path(__file__).resolve().parents[1];data=json.load(open(B/'hardware/checks/routing-geometry.json'));shapes=data['shapes'];targets=data['targets'];G=.05;W=1801;H=1401
HV={'MAINS_L','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT'}
def live(n):return n in HV or n=='MAINS_N' or n.startswith('M_')
def gap(a,b):
 if live(a)!=live(b) and b:return 8
 if {a,b}=={'L_PROTECTED','M_VDIV_0'}:return .6
 if a in HV or b in HV:return 2
 volts={'M_VDIV_0':3,'M_VDIV_1':2,'M_VDIV_2':1}
 if a in volts and b in volts:return abs(volts[a]-volts[b])*.6
 return max(.15,.6*max(volts.get(a,0),volts.get(b,0)))
def occ(net,radius):
 arr=np.zeros((4,H,W),dtype=np.bool_)
 def limits(x1,y1,x2,y2):return max(0,math.ceil(x1/G)),max(0,math.ceil(y1/G)),min(W-1,math.floor(x2/G)),min(H-1,math.floor(y2/G))
 for s in shapes:
  if s['net']==net:continue
  c=gap(net,s['net'])+radius+.01
  if s.get('ref','').startswith('H'):c=max(c,.3+radius)
  if s['kind']=='pad' and not s['circle']:
   xx1,yy1,xx2,yy2=s['bbox'];x1,y1,x2,y2=limits(xx1-c,yy1-c,xx2+c,yy2+c)
   if x1<=x2 and y1<=y2:
    for l in s['layers']:arr[l,y1:y2+1,x1:x2+1]=True
   continue
  if s['kind']=='pad':
   aa=s['point'];zz=aa;r=(s['bbox'][2]-s['bbox'][0])/2+c
  else:aa=s['point'];zz=s.get('end',aa);r=s['width']/2+c
  x1,y1,x2,y2=limits(min(aa[0],zz[0])-r,min(aa[1],zz[1])-r,max(aa[0],zz[0])+r,max(aa[1],zz[1])+r)
  if x1>x2 or y1>y2:continue
  yy,xx=np.ogrid[y1:y2+1,x1:x2+1];xx=xx*G;yy=yy*G;dx=zz[0]-aa[0];dy=zz[1]-aa[1];dd=dx*dx+dy*dy
  if dd:
   t=np.clip(((xx-aa[0])*dx+(yy-aa[1])*dy)/dd,0,1);mask=(xx-aa[0]-t*dx)**2+(yy-aa[1]-t*dy)**2<=r*r
  else:mask=(xx-aa[0])**2+(yy-aa[1])**2<=r*r
  for l in s['layers']:arr[l,y1:y2+1,x1:x2+1]|=mask
 edge=math.ceil((.3+radius)/G);arr[:,:edge,:]=True;arr[:,-edge:,:]=True;arr[:,:,:edge]=True;arr[:,:,-edge:]=True
 arr[:,:,math.ceil((32-radius)/G):math.floor((40+radius)/G)+1]=True
 if net not in ['GND','+5V']:arr[3,math.ceil((2-radius)/G):math.floor((18+radius)/G)+1,math.ceil((46-radius)/G):math.floor((68+radius)/G)+1]=True
 if net in ['M_IAP','M_RESET_N']:
  arr[:,math.ceil((41.0-radius)/G):math.floor((42.25+radius)/G)+1,math.ceil((20.2-radius)/G):math.floor((22.2+radius)/G)+1]=True
 return arr
def search(net,a,b):
 width=.25 if net in HV else .15;vw=.4 if a.get('ref')=='U10' or b.get('ref')=='U10' else .45;ob=occ(net,width/2);vo=occ(net,vw/2).any(axis=0)
 ax,ay=[round(n/G) for n in a['point']];bx,by=[round(n/G) for n in b['point']];goals={(l,by,bx) for l in b['layers'] if not ob[l,by,bx]};starts=[(l,ay,ax) for l in a['layers'] if not ob[l,ay,ax]]
 if not starts or not goals:return None,'blocked endpoint'
 def heur(x,y):dx=abs(x-bx);dy=abs(y-by);return max(dx,dy)+.4142*min(dx,dy)
 heap=[];cost={};prev={};counter=0
 for s in starts:cost[s]=0;heapq.heappush(heap,(heur(s[2],s[1])*1.15,0,s))
 begin=time.monotonic();dirs=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)]
 while heap:
  _,g,s=heapq.heappop(heap)
  if g!=cost.get(s):continue
  counter+=1
  if counter>450000 or (counter%1000==0 and time.monotonic()-begin>20):return None,'search limit'
  if s in goals:
   route=[s]
   while s in prev:s=prev[s];route.append(s)
   route.reverse();return (route,width,vw),str(counter)
  l,y,x=s
  for dx,dy,c in dirs:
   xx=x+dx;yy=y+dy
   if not(0<=xx<W and 0<=yy<H) or ob[l,yy,xx]:continue
   if dx and dy and (ob[l,y,xx] or ob[l,yy,x]):continue
   z=(l,yy,xx);gg=g+c
   if gg<cost.get(z,1e99):cost[z]=gg;prev[z]=s;heapq.heappush(heap,(gg+1.15*heur(xx,yy),gg,z))
  if not vo[y,x]:
   for ll in range(4):
    if ll==l:continue
    z=(ll,y,x);gg=g+30
    if gg<cost.get(z,1e99):cost[z]=gg;prev[z]=s;heapq.heappush(heap,(gg+1.15*heur(x,y),gg,z))
 return None,'no path'
def simplify(path):
 out=[path[0]]
 for i in range(1,len(path)-1):
  a,z,n=path[i-1:i+2]
  if a[0]!=z[0] or z[0]!=n[0] or (z[1]-a[1],z[2]-a[2])!=(n[1]-z[1],n[2]-z[2]):out.append(z)
 out.append(path[-1]);return out
routes=[];fail=[]
(B/'hardware/checks/proposed-routes.json').write_text(json.dumps({'routes':routes,'failed':fail})+'\n')
# Short local connections first; supply/coil paths are also reviewed separately.
targets.sort(key=lambda t:math.dist(t['a']['point'],t['b']['point']))
for i,t in enumerate(targets):
 if t['net'] in ['CTRL_IN','CTRL_MID','CTRL_OUT','M_MISO','M_MOSI','L_PROTECTED','M_XIN','M_XOUT','M_VP']:continue
 result,reason=search(t['net'],t['a'],t['b'])
 if not result:fail.append({'net':t['net'],'reason':reason,'a':t['a']['point'],'b':t['b']['point']});print('FAIL',t['net'],reason,flush=True);continue
 path,width,vw=result;path=simplify(path);points=[{'layer':l,'xy':[round(x*G,6),round(y*G,6)]} for l,y,x in path]
 points=[{'layer':points[0]['layer'],'xy':t['a']['point']}]+points+[{'layer':points[-1]['layer'],'xy':t['b']['point']}]
 route={'net':t['net'],'width':width,'via_width':vw,'points':points};routes.append(route)
 for a,z in zip(points,points[1:]):
  if a['layer']!=z['layer']:shapes.append({'kind':'via','net':t['net'],'point':a['xy'],'width':vw,'layers':[0,1,2,3]})
  elif a['xy']!=z['xy']:shapes.append({'kind':'track','net':t['net'],'point':a['xy'],'end':z['xy'],'width':width,'layers':[a['layer']]})
 print('ROUTED',t['net'],len(points),'points',reason,flush=True)
 (B/'hardware/checks/proposed-routes.json').write_text(json.dumps({'routes':routes,'failed':fail},indent=2)+'\n')
print('RESULT',len(routes),'routes',len(fail),'failed')
