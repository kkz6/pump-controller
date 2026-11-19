#!/usr/bin/env python3
"""Generate native editable KiCad design from design/circuit.json.

Run with a Python environment that provides KiCad pcbnew and wx: python generate_cad.py [--export].
This creates an initial component placement, not an autorouted board.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import subprocess
import shutil
import uuid
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
NS = uuid.UUID('65033db8-a70f-4e73-a9d7-049c9a7c8f95')
def uid(value): return str(uuid.uuid5(NS, str(value)))
def q(value): return json.dumps(str(value), ensure_ascii=False)
def num(value): return ('%.4f' % value).rstrip('0').rstrip('.') or '0'
def effects(size=1.0, justify='', hide=False):
    return '(effects (font (size %s %s))%s%s)' % (num(size),num(size),(' (justify '+justify+')') if justify else '', ' (hide yes)' if hide else '')
def prop(name,value,x=0,y=0,size=1,hide=False):
    return '(property %s %s (at %s %s 0) %s)' % (q(name),q(value),num(x),num(y),effects(size,hide=hide))
def safe(value): return re.sub(r'[^A-Za-z0-9_-]','_',str(value))
def shape_line(x1,y1,x2,y2,width=.254):
    return '(polyline (pts (xy %s %s) (xy %s %s)) (stroke (width %s) (type default)) (fill (type none)))' % tuple(num(v) for v in [x1,y1,x2,y2,width])
def rectangle(x1,y1,x2,y2):
    return '(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background)))' % tuple(num(v) for v in [x1,y1,x2,y2])

TYPES = {'input','output','bidirectional','tri_state','passive','free','unspecified','power_in','power_out','open_collector','open_emitter','no_connect'}

def geometry(component):
    """Library coordinates: +y upward; pin ends and their facing direction."""
    pins = component.get('pins',[])
    kind = component.get('kind','ic').lower()
    simple = len(pins)==2 and kind in ('r','resistor','c','capacitor','capacitor_polarized','fuse','inductor','diode','led')
    if simple:
        end = [(-5.08,0,0),(5.08,0,180)]
        if kind in ('c','capacitor','capacitor_polarized'):
            draw = [shape_line(-.762,-2.54,-.762,2.54,.508),shape_line(.762,-2.54,.762,2.54,.508),shape_line(-2.54,0,-.762,0),shape_line(.762,0,2.54,0)]
            if kind=='capacitor_polarized': draw += [shape_line(-2,-4,-2,-2.8),shape_line(-2.6,-3.4,-1.4,-3.4)]
        elif kind in ('diode','led'):
            # Anode on pin 2, cathode pin 1; symbol polarity follows pin names.
            flip = -1 if str(pins[0].get('name','')).upper() in ('A','ANODE') else 1
            draw = [shape_line(-flip*1.27,-1.9,-flip*1.27,1.9),shape_line(-flip*1.27,0,flip*1.27,-1.9),shape_line(flip*1.27,-1.9,flip*1.27,1.9),shape_line(flip*1.27,1.9,-flip*1.27,0),shape_line(-2.54,0,-1.27,0),shape_line(1.27,0,2.54,0)]
        else:
            draw = [rectangle(-2.54,1.016,2.54,-1.016)]
            if kind=='fuse': draw += [shape_line(-2.54,0,2.54,0)]
        return 10.16,5.08,end,draw,True
    count = max(1,math.ceil(len(pins)/2))
    width = float(component.get('symbol_width',35.56))
    height = max(10.16,(count-1)*2.54+7.62)
    end=[]
    for i,p in enumerate(pins):
        right=i>=count; row=i-count if right else i
        y=(count-1)*1.27-row*2.54
        end.append(((width/2+2.54) * (1 if right else -1),y,180 if right else 0))
    return width,height,end,[rectangle(-width/2,height/2,width/2,-height/2)],False

def symbol_definition(c, library=True):
    ref=c['ref']; stem=safe(ref); name=('Pump:'+stem) if library else stem
    w,h,end,draw,simple=geometry(c)
    lines=['(symbol '+q(name), '(pin_names (offset 0.508))', '(exclude_from_sim no)', '(in_bom yes)', '(on_board yes)', prop('Reference',ref,0,h/2+5.08),prop('Value',c.get('value',ref),0,h/2+2.54),prop('Footprint',c.get('footprint',''),hide=True),prop('Datasheet',c.get('datasheet',''),hide=True),prop('Description',c.get('description',''),hide=True)]
    lines += ['(symbol '+q(stem+'_0_1')+' '+' '.join(draw)+')']
    pintext=[]
    for p,(x,y,a) in zip(c['pins'],end):
        typ=p.get('type','passive')
        if typ not in TYPES: raise ValueError('%s pin %s invalid type %s'%(ref,p['num'],typ))
        nm='~' if simple else p.get('name',str(p['num']))
        pintext.append('(pin %s line (at %s %s %d) (length 2.54) (name %s %s) (number %s %s))' % (typ,num(x),num(y),a,q(nm),effects(.95),q(p['num']),effects(.95)))
    lines += ['(symbol '+q(stem+'_1_1')+' '+' '.join(pintext)+')',')']
    return '\n'.join(lines)

def text(value,x,y,size=1.27):
    return '(text %s (at %s %s 0) %s (uuid %s))' % (q(value),num(x),num(y),effects(size,'left'),q(uid('text'+value+str(x)+str(y))))

def instance(c,x,y,project,hierarchy):
    ref=c['ref']; suid=uid('component:'+ref)
    w,h,ends,draw,simple=geometry(c)
    header_y=y-h/2-5.08
    lines=['(symbol (lib_id '+q('Pump:'+safe(ref))+') (at %s %s 0) (unit 1)'%(num(x),num(y)), '(exclude_from_sim no) (in_bom yes) (on_board %s) (dnp %s)'%('yes' if c.get('on_board',True) else 'no','yes' if c.get('dnp',False) else 'no'), '(uuid '+q(suid)+')',prop('Reference',ref,x,header_y,1.27),prop('Value',c.get('value',ref),x,header_y+2.54,1.05),prop('Footprint',c.get('footprint',''),x,y,hide=True),prop('Datasheet',c.get('datasheet',''),x,y,hide=True),prop('MPN',c.get('mpn',''),x,y,hide=True),prop('Description',c.get('description',''),x,y,hide=True)]
    for i,p in enumerate(c['pins']): lines.append('(pin %s (uuid %s))'%(q(p['num']),q(uid('pin:'+ref+':'+str(i)))))
    lines.append('(instances (project %s (path %s (reference %s) (unit 1)))))'%(q(project),q(hierarchy),q(ref)))
    for i,(p,(dx,dy,a)) in enumerate(zip(c['pins'],ends)):
        px=x+dx; py=y-dy; net=p.get('net')
        if net is None or net=='':
            lines.append('(no_connect (at %s %s) (uuid %s))'%(num(px),num(py),q(uid('nc:'+ref+':'+str(i)))))
            continue
        ex=px+(-7.62 if a==0 else 7.62)
        lines.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0.1524) (type default)) (uuid %s))'%(num(px),num(py),num(ex),num(py),q(uid('wire:'+ref+':'+str(i)))))
        # Global-label anchor faces wire, text extends away from component.
        angle=0 if a==0 else 180
        justify='right' if a==0 else 'left'
        lines.append('(global_label %s (shape passive) (at %s %s %d) %s (uuid %s) %s)'%(q(net),num(ex),num(py),angle,effects(.95,justify),q(uid('label:'+ref+':'+str(i))),prop('Intersheetrefs','${INTERSHEET_REFS}',ex,py,hide=True)))
    return '\n'.join(lines)

def schematic_header(sheet_uid,title,page='A3',project='pump-controller'):
    return ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")', '(uuid '+q(sheet_uid)+')', '(paper '+q(page)+')','(title_block (title '+q(title)+') (rev "B-DRAFT") (company "1 HP single-phase pump controller") (comment 1 "Engineering prototype; mains review and bench tests pending"))']

def page_layout(comps):
    # A3: 4 columns, automatic rows with pin count-dependent heights.
    placements=[]; y=30.48; row=[]; rowh=0; col=0
    for c in comps:
        w,h,*_=geometry(c); ch=max(30.48,h+17.78)
        if col==4:
            y+=rowh; col=0; rowh=0
        if y+ch>266.7: raise ValueError('Sheet too dense near %s; split it into additional functional sheets'%c['ref'])
        placements.append((c,50.8+col*101.6,y+ch/2))
        rowh=max(rowh,ch); col+=1
    return placements

def write_schematics(data,out,project):
    rootuid=uid(project+':root'); definitions=[]; root=schematic_header(rootuid,data.get('title','Pump controller - detailed circuit'))
    root += ['(lib_symbols)',text('REV B / ENGINEERING PROTOTYPE',20,20,2),text('Functional sheets below. Global net labels connect between sheets.',20,27,1.27)]
    for n,s in enumerate(data['sheets'],2):
        sid=safe(s['id']); sheetuid=uid(project+':sheet:'+sid); fileuid=uid(project+':file:'+sid)
        filename=sid+'.kicad_sch'; path='/'+rootuid+'/'+sheetuid
        lines=schematic_header(fileuid,s['title'])
        lines += ['(lib_symbols']+[symbol_definition(c) for c in s['components']]+[')']
        lines += [text(s['title'],15.24,15.24,2.0)]
        if s.get('notes'): lines += [text(str(s['notes']),15.24,22.86,1.0)]
        for c,x,y in page_layout(s['components']): lines.append(instance(c,x,y,project,path))
        lines += [')']
        (out/filename).write_text('\n'.join(lines)+'\n')
        x=25.4+((n-2)%3)*127; y=48.26+((n-2)//3)*40.64
        root.append('(sheet (at %s %s) (size 111.76 25.4) (stroke (width 0.1524) (type default)) (fill (color 0 0 0 0)) (uuid %s) %s %s (instances (project %s (path %s (page %s)))))'%(num(x),num(y),q(sheetuid),prop('Sheetname',s['title'],x+55.88,y-2.54,1.27),prop('Sheetfile',filename,x+55.88,y+27.94,1.0),q(project),q('/'+rootuid),q(n)))
        definitions += [symbol_definition(c,False) for c in s['components']]
    root += ['(sheet_instances (path "/" (page "1")))',')']
    (out/(project+'.kicad_sch')).write_text('\n'.join(root)+'\n')
    (out/'Pump.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(definitions)+'\n)\n')
    (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Pump")(type "KiCad")(uri "${KIPRJMOD}/Pump.kicad_sym")(options "")(descr "Project embedded symbols")))\n')

def write_bom(data,out):
    fields=['Reference','Value','MPN','Description','Footprint','Datasheet','Sheet','DNP']
    with (out/'bom.csv').open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=fields); w.writeheader()
        for s in data['sheets']:
            for c in s['components']:
                if not c.get('on_board',True):continue
                w.writerow(dict(zip(fields,[c['ref'],c.get('value',''),c.get('mpn',''),c.get('description',''),c.get('footprint',''),c.get('datasheet',''),s['id'],c.get('dnp',False)])))

def make_board(data,out,project):
    import wx
    app=wx.GetApp() or wx.App(False)
    import pcbnew as p
    mm=p.FromMM
    def pos(x,y):return p.VECTOR2I(mm(x),mm(y))
    board=p.BOARD(); board.SetCopperLayerCount(int(data.get('board',{}).get('layers',2)))
    board.SetFileName(str(out/(project+'.kicad_pcb')))
    settings=board.GetDesignSettings()
    settings.m_MinClearance=mm(.2); settings.m_TrackMinWidth=mm(.2)
    comps=[c for s in data['sheets'] for c in s['components'] if c.get('on_board',True)]
    nets={}
    for name in sorted({str(pin['net']) for c in comps for pin in c['pins'] if pin.get('net')}):
        net=p.NETINFO_ITEM(board,name); board.Add(net); nets[name]=net
    libs=Path(os.environ.get('KICAD10_FOOTPRINT_DIR',str(BASE/'hardware/libraries')))
    custom=BASE/'hardware'/'Pump.pretty'
    # A project may supply custom libraries by name/path through circuit.json.
    customlibs={'Pump':custom}
    customlibs.update({k:(BASE/v).resolve() for k,v in data.get('footprint_libraries',{}).items()})
    report=[]; board_config=data.get('board',{}); bw=float(board_config.get('width',80)); bh=float(board_config.get('height',60))
    shelf_x=3.; shelf_y=3.; shelf_h=0.; max_y=bh
    for c in comps:
        fid=c.get('footprint','')
        if ':' not in fid:raise ValueError(c['ref']+': footprint needs Library:Name, got '+repr(fid))
        lib,name=fid.split(':',1); libdir=customlibs.get(lib,libs/(lib+'.pretty'))
        filename=libdir/(name+'.kicad_mod')
        if not filename.exists():raise FileNotFoundError(c['ref']+': missing footprint '+str(filename))
        fp=p.FootprintLoad(str(libdir),name)
        if fp is None:raise ValueError('KiCad cannot load '+str(filename))
        fp.SetReference(c['ref']); fp.SetValue(c.get('value',''))
        for key,value in [('MPN',c.get('mpn','')),('Datasheet',c.get('datasheet',''))]:
            fp.SetField(key,value);fp.GetField(key).SetVisible(False)
        fp.SetFPID(p.LIB_ID(lib,name)); fp.SetPath(p.KIID_PATH())
        for sid,s in enumerate(data['sheets']):
            if any(x is c for x in s['components']):
                # Tie this placement to the hierarchical schematic instance.
                root_id=uid(project+':root'); sheet_id=uid(project+':sheet:'+safe(s['id']))
                fp.SetPath(p.KIID_PATH('/'+root_id+'/'+sheet_id+'/'+uid('component:'+c['ref'])))
                break
        pinmap={str(pin['num']):pin.get('net') for pin in c['pins']}
        padnums={pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        missing=set(pinmap)-padnums
        if missing:raise ValueError('%s: schematic pins missing from footprint: %s'%(c['ref'],sorted(missing)))
        unmapped=padnums-set(pinmap)
        if unmapped:raise ValueError('%s: footprint pads not in schematic pins: %s'%(c['ref'],sorted(unmapped)))
        for pad in fp.Pads():
            netname=pinmap.get(pad.GetNumber())
            if netname:pad.SetNet(nets[str(netname)])
        board.Add(fp)
        placement=c.get('placement')
        if placement:
            fp.SetPosition(pos(float(placement['x']),float(placement['y'])))
            if placement.get('side','F').upper()=='B':fp.Flip(fp.GetPosition(),False)
            fp.SetOrientationDegrees(float(placement.get('rotation',0)))
        else:
            # Shelf packing is only a readable starting placement, never a routing claim.
            bb=fp.GetBoundingBox(False,False); fw=p.ToMM(bb.GetWidth()); fh=p.ToMM(bb.GetHeight())
            if shelf_x+fw>bw-3:
                shelf_x=3; shelf_y+=shelf_h+1.5; shelf_h=0
            x=shelf_x-p.ToMM(bb.GetX()); y=shelf_y-p.ToMM(bb.GetY())
            fp.SetPosition(pos(x,y)); shelf_x+=fw+1.5; shelf_h=max(shelf_h,fh)
            max_y=max(max_y,shelf_y+fh+3)
        report.append({'ref':c['ref'],'footprint':fid,'x':p.ToMM(fp.GetPosition().x),'y':p.ToMM(fp.GetPosition().y),'rotation':fp.GetOrientationDegrees(),'pads':{pad.GetNumber():{'x':p.ToMM(pad.GetPosition().x),'y':p.ToMM(pad.GetPosition().y),'net':pad.GetNetname()} for pad in fp.Pads() if pad.GetNumber()}})
    bh=max_y
    for a,b in [((0,0),(bw,0)),((bw,0),(bw,bh)),((bw,bh),(0,bh)),((0,bh),(0,0))]:
        edge=p.PCB_SHAPE(); edge.SetShape(p.SHAPE_T_SEGMENT); edge.SetStart(pos(*a));edge.SetEnd(pos(*b));edge.SetLayer(p.Edge_Cuts);edge.SetWidth(mm(.05));board.Add(edge)
    p.SaveBoard(str(out/(project+'.kicad_pcb')),board)
    (out/'placement.json').write_text(json.dumps({'width':bw,'height':bh,'routed':False,'components':report},indent=2)+'\n')
    fp_table=['(fp_lib_table (version 7)']
    for lib in sorted({c['footprint'].split(':')[0] for c in comps}):
        path=customlibs.get(lib)
        uri=os.path.relpath(path,out) if path else '${KICAD10_FOOTPRINT_DIR}/'+lib+'.pretty'
        if path:uri='${KIPRJMOD}/'+uri
        fp_table.append('(lib (name %s)(type "KiCad")(uri %s)(options "")(descr ""))'%(q(lib),q(uri)))
    fp_table.append(')');(out/'fp-lib-table').write_text('\n'.join(fp_table)+'\n')

def validate_netlist(data,filename):
    tree=ET.parse(filename)
    comps=[c for s in data['sheets'] for c in s['components'] if c.get('on_board',True)]
    actualrefs={c.attrib['ref'] for c in tree.findall('.//components/comp')}
    expectedrefs={c['ref'] for c in comps}
    if not expectedrefs<=actualrefs:raise ValueError('Native netlist omitted components: '+repr(sorted(expectedrefs-actualrefs)))
    actual={}
    for net in tree.findall('.//nets/net'):
        for node in net.findall('node'):actual[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name']
    errors=[]
    for c in comps:
        for pin in c['pins']:
            expected=pin.get('net')
            if expected and actual.get((c['ref'],str(pin['num'])))!=str(expected):
                errors.append((c['ref'],str(pin['num']),expected,actual.get((c['ref'],str(pin['num'])))))
    if errors:raise ValueError('JSON-to-native netlist mismatch: '+repr(errors))
    print('Native netlist verified: %d components, %d connected pins'%(len(comps),len(actual)))

def export_native(data,out,project):
    cli=os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or str(BASE/'.tools/kicad-cli'); root=str(out/(project+'.kicad_sch')); pcb=str(out/(project+'.kicad_pcb'))
    reports=out/'checks'; reports.mkdir(exist_ok=True)
    exports=out/'exports'; exports.mkdir(exist_ok=True)
    jobs=[['sch','erc','--format','json','-o',str(reports/'erc.json'),root],['sch','export','netlist','--format','kicadxml','-o',str(exports/'netlist.xml'),root],['sch','export','pdf','-o',str(exports/'schematic.pdf'),root],['sch','export','svg','-o',str(exports/'schematic-svg')+'/',root],['pcb','drc','--format','json','-o',str(reports/'drc.json'),pcb],['pcb','export','svg','--layers','F.Cu,F.Silkscreen,Edge.Cuts','-o',str(exports/'pcb-svg')+'/',pcb]]
    for args in jobs:
        result=subprocess.run([cli]+args,text=True,capture_output=True)
        print(' '.join(args[:3])+': '+str(result.returncode))
        if result.stdout:print(result.stdout.strip())
        if result.stderr:print(result.stderr.strip())
        if result.returncode:raise RuntimeError('KiCad command failed: '+repr(args))
    validate_netlist(data,exports/'netlist.xml')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=BASE/'design/circuit.json');ap.add_argument('--output',type=Path,default=BASE/'hardware');ap.add_argument('--export',action='store_true');ap.add_argument('--schematic-only',action='store_true');args=ap.parse_args()
    data=json.loads(args.input.read_text()); out=args.output.resolve();out.mkdir(parents=True,exist_ok=True); project=data.get('project','pump-controller')
    refs=[c['ref'] for s in data['sheets'] for c in s['components']]
    if len(set(refs))!=len(refs):raise ValueError('Component references must be globally unique')
    write_schematics(data,out,project);write_bom(data,out)
    if not args.schematic_only:make_board(data,out,project)
    pro=out/(project+'.kicad_pro')
    if not pro.exists():pro.write_text(json.dumps({'meta':{'filename':pro.name,'version':1},'net_settings':{'classes':[{'name':'Default','clearance':.2,'track_width':.25,'via_diameter':.6,'via_drill':.3}],'meta':{'version':3}}},indent=2)+'\n')
    if args.export:export_native(data,out,project)
    print('Generated '+str(out))

if __name__=='__main__':main()
