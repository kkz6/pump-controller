#!/usr/bin/env python3
"""Constraint-based prototype placement. Final routing remains independently DRC checked."""
import argparse,json,math,os
from pathlib import Path
import wx
app=wx.App(False)
import pcbnew as p
BASE=Path(__file__).resolve().parents[1]
MM=p.FromMM
def v(x,y):return p.VECTOR2I(MM(x),MM(y))
def live(net):return net in {'MAINS_L','MAINS_N','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT'} or net.startswith('M_')
def electrical_gap(a,b):
    if not a or not b:
        return 2 if (a or b) in {'MAINS_L','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT'} else .15
    if not live(a) or not live(b):return .15
    hv={'MAINS_L','L_FUSED','L_PROTECTED','CTRL_IN','CTRL_MID','CTRL_OUT'}
    if {a,b}=={'L_PROTECTED','M_VDIV_0'}:return .6
    volts={'M_VDIV_0':3,'M_VDIV_1':2,'M_VDIV_2':1}
    if a in hv or b in hv:return 2
    if a in volts and b in volts:return abs(volts[a]-volts[b])*.6
    return max(volts.get(a,0),volts.get(b,0))*.6
def overlap(a,b,gap=0):return a[0]<b[2]+gap and a[2]>b[0]-gap and a[1]<b[3]+gap and a[3]>b[1]-gap
def shift(b,x,y):return b[0]+x,b[1]+y,b[2]+x,b[3]+y
def bbox(f):
    items=[i.GetBoundingBox() for i in f.GraphicalItems() if i.GetLayer() in (p.F_CrtYd,p.B_CrtYd)]
    if not items:items=[f.GetBoundingBox(False,False)]
    return (min(p.ToMM(b.GetX()) for b in items),min(p.ToMM(b.GetY()) for b in items),max(p.ToMM(b.GetRight()) for b in items),max(p.ToMM(b.GetBottom()) for b in items))
def orientation(f,rot,side):
    f.SetPosition(v(0,0))
    if f.GetLayer()==p.B_Cu:f.Flip(v(0,0),False)
    f.SetOrientationDegrees(0)
    if side=='B':f.Flip(v(0,0),False)
    f.SetOrientationDegrees(rot)

class Packer:
    def __init__(self,board,data,width,height,barrier):
        self.b=board;self.data=data;self.w=width;self.h=height;self.bs=barrier;self.be=barrier+8
        self.fps={f.GetReference():f for f in board.GetFootprints()}
        self.meta={c['ref']:dict(c,sheet=s['id']) for s in data['sheets'] for c in s['components'] if c.get('on_board',True)}
        self.occupied={'F':[((width-6,0,width,6),'H1'),((width-6,height-6,width,height),'H2')],'B':[((width-6,0,width,6),'H1'),((width-6,height-6,width,height),'H2')]};self.placed={};self.boxes={};self.cache={};self.padcache={};self.placedpads=[]
        self.netmembers={}
        for c in self.meta.values():
            for pin in c['pins']:
                if pin.get('net'):self.netmembers.setdefault(pin['net'],set()).add(c['ref'])
    def candidate(self,ref,rot,side):
        key=ref,rot,side
        if key not in self.cache:
            f=self.fps[ref];orientation(f,rot,side);b=bbox(f)
            pads=[]
            for d in f.Pads():
                if d.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH):
                    z=d.GetBoundingBox();pads.append(tuple(p.ToMM(k) for k in [z.GetX(),z.GetY(),z.GetRight(),z.GetBottom()]))
            self.padcache[key]=[(d.GetNetname(),tuple(p.ToMM(k) for k in [d.GetBoundingBox().GetX(),d.GetBoundingBox().GetY(),d.GetBoundingBox().GetRight(),d.GetBoundingBox().GetBottom()]),d.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH)) for d in f.Pads()]
            self.cache[key]=(b,pads)
        return self.cache[key]
    def valid(self,ref,rot,side,x,y,bridge=False):
        b,pads=self.candidate(ref,rot,side);b=shift(b,x,y)
        if b[0]<.6 or b[1]<.6 or b[2]>self.w-.6 or b[3]>self.h-.6:return False
        if not bridge:
            islive=any(live(pin.get('net') or '') for pin in self.meta[ref]['pins'])
            if islive and b[2]>self.bs-.25:return False
            if not islive and b[0]<self.be+.25:return False
        for ob,other in self.occupied[side]:
            if overlap(b,ob,.18):return False
        opp='B' if side=='F' else 'F'
        for pb in pads:
            pb=shift(pb,x,y)
            for ob,other in self.occupied[opp]:
                if ref=='U2' and other=='R2:heat_spreader':continue
                if overlap(pb,ob,.25):return False
        for net,pb,th in self.padcache[(ref,rot,side)]:
            if net and not live(net):continue
            pb=shift(pb,x,y)
            for onet,ob,oth,oside in self.placedpads:
                if net==onet or (side!=oside and not th and not oth):continue
                clr=electrical_gap(net,onet)
                if clr<=.15:continue
                dx=max(0,pb[0]-ob[2],ob[0]-pb[2]);dy=max(0,pb[1]-ob[3],ob[1]-pb[3])
                if dx*dx+dy*dy<(clr+.02)**2:return False
        return True
    def put(self,ref,x,y,rot=0,side='F',bridge=False):
        if not self.valid(ref,rot,side,x,y,bridge):raise ValueError('Invalid fixed placement '+str((ref,x,y,rot,side)))
        f=self.fps[ref];orientation(f,rot,side);f.SetPosition(v(x,y))
        b,pads=self.candidate(ref,rot,side);b=shift(b,x,y)
        self.occupied[side].append((b,ref));opp='B' if side=='F' else 'F'
        for pb in pads:self.occupied[opp].append((shift(pb,x,y),ref+':hole'))
        self.placedpads.extend((net,shift(pb,x,y),th,side) for net,pb,th in self.padcache[(ref,rot,side)])
        self.placed[ref]={'x':x,'y':y,'rotation':rot,'side':side};self.boxes[ref]=b
    def targets(self,ref):
        c=self.meta[ref];sheet=c['sheet'];x=self.be;w=self.w;h=self.h
        targets={'J20':(w-29,h-8),'J21':(w-7,h-8),'J32':(w-17,7),'J33':(w-10,36),'J31':(x+9,h-9),'J2':(w-5,25),'U3':(w-24,24),'U2':(x+12,12),'U33':(x+15,40),'U20':(w-23,h-22),'U21':(w-10,h-22),'U22':(w-18,h-30),'U10':(self.bs/2,44),'J1':(7,7),'J30':(self.bs-8,8),'J10':(self.bs-7,h-7),'F1':(5,28),'R1':(13,26),'RV1':(self.bs/2,h-13),'R2':(x+14,6)}
        if ref in targets:return targets[ref]
        points=[]
        for pin in c['pins']:
            net=pin.get('net');members=self.netmembers.get(net,set())
            if 1<len(members)<=6:
                for n in members:
                    if n!=ref and n in self.placed:points.append((self.placed[n]['x'],self.placed[n]['y']))
        if points:return sum(t[0] for t in points)/len(points),sum(t[1] for t in points)/len(points)
        if sheet.startswith('probes'):return (w-20,h-22)
        if sheet.startswith('meter'):return (self.bs/2,44)
        if sheet.startswith('relay'):return (x+9,32)
        if sheet.startswith('local'):return (x+19,39)
        if sheet=='power':return (x+10,11)
        return (w-23,23)
    def packone(self,ref,front_only=False):
        c=self.meta[ref];f=self.fps[ref]
        islive=any(live(pin.get('net') or '') for pin in c['pins'])
        target=self.targets(ref);minx=.8 if islive else self.be+.5;maxx=self.bs-.5 if islive else self.w-.8
        options=[]
        for side in (['F'] if front_only else ['F','B']):
            for rot in [0,90,180,270]:
                bb,pads=self.candidate(ref,rot,side)
                left=math.ceil((minx-bb[0])*2)/2;right=math.floor((maxx-bb[2])*2)/2
                top=math.ceil((.8-bb[1])*2)/2;bottom=math.floor((self.h-.8-bb[3])*2)/2
                for ix in range(round(left*2),round(right*2)+1):
                    x=ix/2
                    for iy in range(round(top*2),round(bottom*2)+1):
                        y=iy/2
                        score=(x-target[0])**2+(y-target[1])**2+(0 if side=='F' else 22)
                        options.append((score,rot,side,x,y))
        options.sort()
        for score,rot,side,x,y in options:
            if self.valid(ref,rot,side,x,y):self.put(ref,x,y,rot,side);return
        raise ValueError('Cannot pack '+ref+' '+c.get('value',''))
    def run(self):
        # All four barriers bridge the same track/via/plane-free corridor.
        self.put('U1',self.bs-7,5,0,'F',True)
        self.put('K1',self.be+1.1,35,180,'F',True)
        self.put('K2',self.be+1.1,48,180,'F',True)
        self.put('U11',self.bs+4,18,180,'B',True)
        self.put('R2',self.be+17,10,180,'B')
        self.occupied['B'].append(((self.be+6,2,self.be+28,18),'R2:heat_spreader'))
        # Tight buck and isolator local groups preserve high-frequency loop geometry.
        for ref,x,y,rot,side in [('U2',55.75,14.5,0,'F'),('C3',51.5,14.5,180,'F'),('C4',55.5,11.5,0,'F'),('L1',60,14.5,0,'F'),('C5',65,14.5,0,'F'),('C6',65,11.5,0,'F'),('C55',44,23.5,0,'B'),('C56',44,20.275,0,'B'),('C57',44,12.5,0,'B'),('C58',27.9,23.5,180,'B'),('C59',28.25,20.275,180,'B'),('C60',28.25,14.5,180,'B'),('FB1',26,17,90,'B'),('FB2',25,22,90,'B')]:
            self.put(ref,x,y,rot,side)
        big=[r for r in ['J1','F1','R1','RV1','R43','R44','R45','R46','J30','J10','J32','J20','J21','J31','J33','J2','U3','U10','U33','U20','U21','U22','U2','R2'] if r in self.meta and r not in self.placed]
        for ref in big:
            self.packone(ref,front_only=ref in ['J1','F1','R1','RV1','R43','R44','R45','R46','J30','J10','J32','J20','J21','J31','J33','J2','U3'])
        pending=set(self.meta)-set(self.placed)
        while pending:
            def score(ref):
                c=self.meta[ref];connected=sum(1 for pin in c['pins'] for n in self.netmembers.get(pin.get('net'),set()) if n!=ref and n in self.placed and len(self.netmembers.get(pin.get('net'),set()))<=6)
                b,_=self.candidate(ref,0,'F');area=(b[2]-b[0])*(b[3]-b[1])
                return (0 if ref.startswith('U') else 1,-connected,-area,ref)
            ref=min(pending,key=score);self.packone(ref);pending.remove(ref)
        return self.placed

def decorate(board,w,h,bs):
    for f in board.GetFootprints():
        f.Value().SetVisible(False)
        f.Reference().SetVisible(False)

def strip_board_items(s,names):
    level=0;quoted=False;escaped=False;start=None;spans=[]
    for i,ch in enumerate(s):
        if quoted:
            if escaped:escaped=False
            elif ch=='\\':escaped=True
            elif ch=='"':quoted=False
        elif ch=='"':quoted=True
        elif ch=='(':
            level+=1
            if level==2:start=i
        elif ch==')':
            if level==2:
                head=s[start+1:].split(None,1)[0]
                if head in names:spans.append((start,i+1))
            level-=1
    for a,b in reversed(spans):s=s[:a]+s[b:]
    return s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--width',type=float,default=90);ap.add_argument('--height',type=float,default=70);ap.add_argument('--barrier',type=float,default=32);args=ap.parse_args()
    data=json.load(open(BASE/'design/circuit.json'));project=data['project'];file=BASE/'hardware'/f'{project}.kicad_pcb'
    board=p.LoadBoard(str(file));packer=Packer(board,data,args.width,args.height,args.barrier);result=packer.run();decorate(board,args.width,args.height,args.barrier)
    p.SaveBoard(str(file),board)
    s=strip_board_items(file.read_text(),{'gr_line','gr_rect','zone','segment','via'}); zone='''  (zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (uuid "80aec00f-5084-46dd-bb9e-73d0875f4826") (hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) (fill (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy %s 0) (xy %s 0) (xy %s %s) (xy %s %s))))\n'''%(args.barrier,args.barrier+8,args.barrier+8,args.height,args.barrier,args.height); edges=''.join('(gr_line (start %s %s) (end %s %s) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))\n'%(*a,*b) for a,b in [((0,0),(args.width,0)),((args.width,0),(args.width,args.height)),((args.width,args.height),(0,args.height)),((0,args.height),(0,0))]); file.write_text(s[:s.rfind(')')]+zone+edges+')\n')
    (BASE/'design/pcb-placement.json').write_text(json.dumps({'board':{'width':args.width,'height':args.height,'layers':4,'isolation_corridor':[args.barrier,args.barrier+8]},'components':result},indent=2)+'\n')
    print('Placed',len(result),'parts on',args.width,args.height,'mm; backs',sum(c['side']=='B' for c in result.values()))

if __name__=='__main__':main()
