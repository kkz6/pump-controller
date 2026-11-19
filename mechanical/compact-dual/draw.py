"""Case layout and 1:1 external right-wall template from the checked body."""
from pathlib import Path
import argparse
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

MM = 25.4
INK, MUTED = '#233544', '#50616a'
FIELD, LIVE, LOGIC = '#6c477d', '#aa5818', '#167a78'


def layout(d):
    fig=plt.figure(figsize=(11.7,7.8),facecolor='white')
    fig.text(.055,.947,"Cabinet guard cable entry",size=23,weight='bold',color=INK)
    fig.text(.056,.902,"GUARD-R2 enclosure  ·  Top view with lid and PCB guard removed",size=11,color=MUTED)
    ax=fig.add_axes([.04,.17,.57,.65],aspect='equal')
    ax.add_patch(Rectangle((0,0),170,150,fc='#f4f7f8',ec=INK,lw=1.5))
    ax.add_patch(Rectangle((3.2,3.2),163.6,143.6,fc='white',ec='#c2cccf'))
    ax.add_patch(Rectangle((32,25),97,100,fc='#eaf4ed',ec='#41815d',lw=1.6))
    ax.text(79,112,'MAIN PCB',ha='center',va='center',size=12,weight='bold',color='#286440')
    ax.text(79,105,'100 × 97 mm',ha='center',size=9,color='#286440')
    for name,(x,y) in d['mount_centres_case_mm'].items():
        ax.add_patch(Circle((x,y),1.6,fc='white',ec='#2d7651'))
        ax.text(x+(2.5 if x<100 else -2.5),y-3.2,name,ha='left' if x<100 else 'right',fontsize=7,color='#19583a')
    def case(p): return 112-p[1],125-p[0]
    def route(points,color,lw=1.5):
        ax.plot(*zip(*points),lw=lw,color=color,solid_capstyle='round')
    control=d['ports_case_coordinates']['STARTER CONTROL']
    for ref,p in d['starter_plug_checks'].items():
        x,y=p['mating_face_case_x_mm'],p['centre_case_y_mm']
        ax.add_patch(Rectangle((x-8,y-5.08),8,10.16,fc=FIELD,alpha=.86))
        ax.add_patch(Rectangle((x,y-5.08),15.5,10.16,fc='#e8dfee',ec=FIELD,lw=1))
        ax.text(x-10,y,ref,ha='right',va='center',fontsize=9,color=FIELD,weight='bold')
        route([(x+15.5,y),(153,y),(159,control['centre_along_wall_mm'])],FIELD)
    for name,p in d['ports_case_coordinates'].items():
        pos=p['centre_along_wall_mm']; bore=p['hole_diameter_mm']
        if p['wall']=='right':
            ax.add_patch(Rectangle((167,pos-bore/2),7,bore,fc=FIELD,ec='white',lw=.7))
            route([(159,pos),(169,pos)],FIELD,3)
        elif p['wall']=='far':
            ax.add_patch(Rectangle((pos-bore/2,147),bore,6,fc=LIVE))
            loc=case(d['ports']['J1']['position'])
            route([(pos,147),(pos,134),loc],LIVE);ax.text(loc[0]-2,loc[1]-8,'J1',size=8,color=LIVE)
            ax.text(pos,158,'AC SUPPLY',size=8,weight='bold',ha='center',color=LIVE)
        elif p['wall']=='left':
            col=LIVE if name=='LIVE CT' else LOGIC
            ax.add_patch(Rectangle((-3,pos-bore/2),6,bore,fc=col))
            ax.text(5,pos,name,ha='left',va='center',size=7,weight='bold',color=col)
        else:
            ax.add_patch(Rectangle((pos-bore/2,-3),bore,6,fc=LOGIC))
            ax.text(pos,-8,name,ha='center',va='center',size=7,weight='bold',color=LOGIC)
    ax.text(82.5,7,'Near wall',ha='center',fontsize=8,color=MUTED)
    ax.set_xlim(-6,178);ax.set_ylim(-11,164);ax.set_axis_off()
    def t(y,main,size=10,col=INK,weight='normal'):
        fig.text(.64,y,main,ha='left',va='top',fontsize=size,color=col,fontweight=weight,linespacing=1.5)
    t(.805,"Guard command entry",14,FIELD,'bold')
    t(.748,"One round, insulated, jacketed cable\nthrough a 20.1 mm M20 gland hole.")
    t(.622,"J30  ·  OUT A   |   Key at pole 1",12,FIELD,'bold')
    t(.584,"J35  ·  OUT B   |   Key at pole 2",12,FIELD,'bold')
    t(.509,"Both removable plugs face the right wall.\nIsolate both supplies before termination\nor service.")
    t(.363,"4 cores to the guard: two independent pairs.\nJ30 drives 24 V command interposer A.\nJ35 drives 24 V command interposer B.\nOEM profile wiring is at the guard.")
    t(.190,"J31 PERMIT AUX carries guard feedback.\nJ36 GUARD I/O carries the five-core logic loom.\nOEM STOP and high-high wire to the external guard.",9,MUTED)
    fig.text(.055,.065,"Footprints and mounting centres follow the KiCad PCB. Plug bodies show conservative fit envelopes.  ·  Dimensions in mm",size=9,color=MUTED)
    return fig


def side_template(d):
    # Drawing at true millimetre scale on A4. Print at 100%, check the scale box.
    fig=plt.figure(figsize=(210/MM,297/MM),facecolor='white')
    ax=fig.add_axes([0,0,1,1],xlim=(0,210),ylim=(0,297),aspect='equal');ax.axis('off')
    def t(x,y,label,size=10,**kw):
        ax.text(x,y,label,size=size,color=INK,ha='left',va='top',**kw)
    t(19,275,'Right wall • starter cable gland',18,weight='bold')
    t(19,261,'Standalone case. External view. Use the near wall and underside as datums.')
    t(19,244,'Print actual size. Check the 20 mm square with a ruler before using this template.',9)
    # Looking at the right wall from outside, near is on the left.
    x0,y0=29,115; h=86.8
    y_c=d['ports_case_coordinates']['STARTER CONTROL']['centre_along_wall_mm']
    z_c=d['ports_case_coordinates']['STARTER CONTROL']['height_mm']
    cx,cy=x0+y_c,y0+z_c
    ax.add_patch(Rectangle((x0,y0),150,h,fill=False,ec=INK,lw=.9))
    ax.add_patch(Circle((cx,cy),10.05,fill=False,ec=FIELD,lw=.75))
    ax.plot([cx-14,cx+14],[cy,cy],color=FIELD,lw=.4);ax.plot([cx,cx],[cy-14,cy+14],color=FIELD,lw=.4)
    t(x0+3,y0+h-4,'NEAR',7);t(x0+133,y0+h-4,'FAR',7)
    t(x0,y0-3,'CASE UNDERSIDE',8)
    ax.annotate('',xy=(cx,y0+12),xytext=(x0,y0+12),arrowprops={'arrowstyle':'<->','color':MUTED,'lw':.7})
    t(x0+32,y0+11,f'{y_c:.1f} mm',8)
    ax.annotate('',xy=(cx+23,cy),xytext=(cx+23,y0),arrowprops={'arrowstyle':'<->','color':MUTED,'lw':.7})
    t(cx+25,cy-9,f'{z_c:.1f} mm',8)
    t(cx-18,cy+23,'Ø20.1 mm',10,weight='bold')
    t(29,96,'STARTER CONTROL • thread M20 × 1.5',12,weight='bold')
    t(29,82,'LAPP 53017030 gland, jacket OD 5–12 mm. Locknut 53119020.\nFinished gland bore 20.0–20.2 mm. Measure the part after printing.\nUse a gland selected for the installed cable and panel material.',9)
    ax.add_patch(Rectangle((29,37),20,20,fill=False,ec=INK,lw=.65));t(55,51,'20 mm scale check',9)
    t(29,22,'Case label',8)
    ax.add_patch(Rectangle((55,14),47,10,fill=False,ec=MUTED,lw=.55))
    ax.text(78.5,19,'STARTER CONTROL',size=8,ha='center',va='center',color=FIELD,weight='bold')
    return fig


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
    checks=json.loads((a.output/'fit-checks.json').read_text())
    overview=layout(checks);template=side_template(checks)
    overview.savefig(a.output/'wire-entries.png',dpi=130)
    with PdfPages(a.output/'wire-entries.pdf') as pdf:
        pdf.savefig(overview);pdf.savefig(template)
    plt.close('all')
