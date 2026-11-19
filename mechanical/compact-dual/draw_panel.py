"""Draw the five-button lid and the 1:1 cut-to-fit front overlay."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

COLORS={'START':'#257451','STOP':'#ae3d39','MODE':'#435666','SET':'#435666','NEXT':'#435666'}


def draw(output):
    report=json.loads((output/'print-manifest.json').read_text())
    rows=report['five_button_fits'];W=170.;D=150.
    # The face SVG gives two trim-out labels. All coordinates are manufactured case mm.
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="170mm" height="150mm" viewBox="0 0 170 150">',
         '<title>Five-button controller face labels at 1:1</title>',
         '<rect x="46" y="57" width="79" height="49" rx="2" fill="white" stroke="#707b81" stroke-width="0.2"/>',
         '<text x="85" y="62.7" text-anchor="middle" font-family="sans-serif" font-size="2.5" fill="#243541">PUMP CONTROLLER</text>',
         '<rect x="72" y="66.25" width="26" height="8" rx="0.3" fill="white" stroke="#62707a" stroke-width="0.2"/>',
         '<rect x="57.5" y="85" width="56.5" height="10" rx="5" fill="white" stroke="#62707a" stroke-width="0.2"/>']
    for name,details in rows.items():
        x,y=details['case_xy_mm'];y=D-y;c=COLORS[name]
        top=name
        svg.append(f'<text x="{x}" y="{y+7.4}" text-anchor="middle" font-family="sans-serif" font-size="2.0" font-weight="bold" fill="{c}">{top}</text>')
        if name=='SET':svg.append(f'<text x="{x}" y="{y+10}" text-anchor="middle" font-family="sans-serif" font-size="1.65" fill="{c}">RESET</text>')
    svg.extend(['<rect x="118" y="4" width="38" height="5" rx="1" fill="white" stroke="#707b81" stroke-width="0.2"/>',
                '<text x="137" y="7.4" text-anchor="middle" font-family="sans-serif" font-size="2.1" fill="#243541">AUTO / MANUAL KEY</text>',
                '<path d="M46 118h20m-20 -1v2m20 -2v2" fill="none" stroke="#384950" stroke-width="0.2"/>',
                '<text x="70" y="118.8" font-family="sans-serif" font-size="2.4">20 mm scale check</text>',
                '<text x="46" y="124" font-family="sans-serif" font-size="2.3">Print at actual size. Trim the two label outlines and the marked apertures.</text>', '</svg>'])
    (output/'front-label-template.svg').write_text('\n'.join(svg)+'\n')
    fig=plt.figure(figsize=(9.5,6.25),facecolor='#fff');ax=fig.add_axes([.01,.02,.7,.92],aspect='equal')
    ax.add_patch(FancyBboxPatch((0,0),170,150,boxstyle='round,pad=0,rounding_size=3',fc='#e9ebeb',ec='#485965',lw=1.25))
    ax.add_patch(Rectangle((46,44),79,49,fc='#f8f9fa',ec='#c8cdcd',lw=.7))
    ax.text(85,87.6,'PUMP CONTROLLER',ha='center',va='center',fontsize=6.3,color='#354651',weight='bold')
    ax.add_patch(Rectangle((72,75.75),26,8,fc='#27363d',ec='#687984',lw=.65));ax.text(85,79.75,'OLED',fontsize=6,ha='center',va='center',color='#e0f1f0')
    for x,y in [(8,8),(162,8),(8,142),(162,142)]:
        ax.add_patch(Circle((x,y),2.5,fc='#c2cbcc',ec='#7f8d90',lw=.75));ax.plot([x-1,x+1],[y-1,y+1],lw=.65,color='#6d7b80')
    ax.add_patch(FancyBboxPatch((57.5,55.),56.5,10.,boxstyle='round,pad=0,rounding_size=5',fc='#e9ebeb',ec='#c8cdcd',lw=.6))
    for name,v in rows.items():
        x,y=v['case_xy_mm'];color=COLORS[name];ax.add_patch(Circle((x,y),4,fc=color,ec='#384851',lw=.65))
        ax.add_patch(Circle((x,y),1.8,fc='#d0d6d6',ec='none'));ax.plot([x-.85,x+.85],[y,y],lw=.75,color='#58666c');ax.plot([x,x],[y-.85,y+.85],lw=.75,color='#58666c')
        ax.text(x,y-8,name if name!='SET' else 'SET\nRESET',ha='center',va='top',color=color,fontsize=5.65,weight='bold',linespacing=1.)
    # The keyed mounting option is shown empty. Purchased barrel geometry depends on selection.
    kx,ky=137,117
    ax.add_patch(Rectangle((115,95),44,44,fc='#f4f5f5',ec='#7e8b8f',lw=.8))
    ax.add_patch(Circle((kx,ky),11.25,fc='#879197',ec='#505d61',lw=.75))
    for x in (119,155):
        for y in (99,135):ax.add_patch(Circle((x,y),1.7,fc='#c8d0d2',ec='#67777d',lw=.45))
    ax.text(kx,143.5,'AUTO / MANUAL KEY',ha='center',va='center',size=5.8,color='#465860')
    ax.set(xlim=(-4,174),ylim=(-4,154));ax.axis('off')
    fig.text(.735,.79,'Five-button lid',size=17,color='#20353e',weight='bold')
    fig.text(.735,.70,'The original DOL buttons\nstay in service. These five\ncontrols sit on the OLED\npanel PCB.',size=9.3,color='#415660',linespacing=1.45,va='top')
    fig.text(.735,.42,'Optional key',size=12,color='#20353e',weight='bold')
    fig.text(.735,.35,'The 22.5 mm adapter is\nshown here. Fit the solid\nblank when a lid key is\nunused. A remotely fitted\nkey can enter through the\nseparate MODE KEY gland.',size=9.3,color='#415660',linespacing=1.45,va='top')
    fig.savefig(output/'five-button-panel.png',dpi=150);plt.close(fig)

if __name__=='__main__':
    import sys
    draw(Path(sys.argv[1]))
