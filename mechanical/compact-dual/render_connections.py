"""Produce the guarded main board view and the cabinet command plug pinout from the native PCB."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from matplotlib import get_data_path
from PIL import Image, ImageDraw, ImageFont, ImageOps

from build import ROOT


def compose(top_file, angled_file, out, revision):
    width, height = 1400, 790
    background, ink, blue, accent = '#f3f5f3', '#182f33', '#215859', '#eaad25'
    im = Image.new('RGB', (width,height), background)
    draw = ImageDraw.Draw(im)
    def label(x,y,value,size,bold=False,anchor='la',fill=ink):
        family = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
        draw.text((x,y),value,font=ImageFont.truetype(str(Path(get_data_path())/'fonts'/'ttf'/family),size),anchor=anchor,fill=fill)
    label(44,25,'Cabinet guard command connections',38,True)
    label(46,79,f'{revision}  /  main PCB, component side',22,fill=blue)
    top = Image.open(top_file).convert('RGBA')
    top = top.crop(top.getbbox())
    top.thumbnail((610,565),Image.Resampling.LANCZOS)
    tx,ty=60,148
    im.paste(top,(tx,ty),top)
    # The top view is orthographic with board x=0..100 and y=-17..80.
    tw,th=top.size
    draw.rectangle((tx+.205*tw,ty,tx+.48*tw,ty+.139*th),outline=accent,width=4)
    label(679,151,'J30  /  A',28,True)
    label(1010,151,'J35  /  B',28,True)
    angled=Image.open(angled_file).convert('RGBA')
    w,h=angled.size
    crop=angled.crop(tuple(round(k*v) for k,v in zip((.214,.083,.478,.26),(w,h,w,h))))
    # Keep the two mouths at readable scale. The front faces point toward
    # the top of the drawing. On both headers pin 1 is on the right.
    crop=ImageOps.fit(crop,(635,365),method=Image.Resampling.LANCZOS)
    im.paste(crop,(682,202),crop)
    label(722,572,'2 NO       1 COM',22,True)
    label(1058,572,'2 NO       1 COM',22,True)
    label(680,640,'Four insulated cores to the guard',25,True)
    label(680,681,'One dedicated pair per 24 V command coil.',22,fill=blue)
    draw.line((44,732,1356,732),fill='#aac0bd',width=2)
    label(45,749,'NO = normally open    ·    COM = common    ·    Wire the OEM starter on the interposer output side.',18,fill=blue)
    im.save(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,default=ROOT/'hardware/main-compact-dual/pump-controller-compact.kicad_pcb')
    parser.add_argument('--fit',type=Path,help='Optional enclosure fit record for the exact board revision')
    parser.add_argument('--validated',type=Path,help='Independent native PCB geometry report')
    parser.add_argument('--out',type=Path,default=ROOT/'hardware/main-compact-dual/exports')
    args=parser.parse_args()
    digest=hashlib.sha256(args.board.read_bytes()).hexdigest()
    if args.fit:
        assert json.loads(args.fit.read_text())['pcb_hash']==digest
    report=args.validated or args.board.parent/'checks/independent-geometry.json'
    geometry=json.loads(report.read_text())
    assert geometry['pcb_sha256']==digest and geometry['geometry_and_source_passed']
    revision=json.loads((ROOT/'design/main-compact-dual.json').read_text())['revision']
    with tempfile.TemporaryDirectory() as temp:
        work=Path(temp)
        visual=work/'render.kicad_pcb'
        subprocess.run([ROOT/'.tools/kicad-python', ROOT/'tools/prepare_compact_3d.py',
            '--board',args.board,'--visual',visual,'--expected-sha256',digest,
            '--coverage',work/'coverage.json','--private-inputs',work/'paths.json'],check=True)
        top=args.out/'board-top.png'
        angled=work/'angled.png'
        for rotation,path in [('0,0,0',top),('32,0,0',angled)]:
            subprocess.run([ROOT/'.tools/kicad-cli','pcb','render','--side','top','--rotate',rotation,
                '--width','1800','--height','1760','--background','transparent','--quality','basic',
                '-o',path,visual],check=True,stdout=subprocess.DEVNULL)
        compose(top,angled,args.out/'main-starter-contacts.png',revision)


if __name__=='__main__':
    main()
