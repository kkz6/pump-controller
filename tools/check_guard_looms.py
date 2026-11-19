"""Check native schematic cavity assignments and keyed families across the guarded R2 boards."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / 'hardware'
PROJECTS = {
    'main': HARDWARE/'main-compact-dual/pump-controller-compact.kicad_sch',
    'panel': HARDWARE/'panel-rev-e/pump-panel-rev-e.kicad_sch',
    'receiver': HARDWARE/'guard-receiver/guard-receiver.kicad_sch',
    'cabinet': HARDWARE/'starter-guard/starter-guard.kicad_sch',
}
# Family and number of positions both distinguish the mating housings.
PORTS = {
    ('main','J36'): ('JST_ZE_', ['GND','HOST_AUX_N','LOCAL_AUX_N','HB_MON','PANEL_OK_MON']),
    ('receiver','J36'): ('JST_ZE_', ['ISO_0','HOST_LOGIC','LOCAL_LOGIC','HB_MON','PANEL_MON']),
    ('main','J31'): ('PhoenixContact_MC_1,5_2-G-3.81_', ['STOP_RETURN','K1_COIL_PLUS']),
    ('receiver','J31'): ('PhoenixContact_MC_1,5_2-G-3.81_', ['J31_1','J31_2']),
    ('main','J21'): ('JST_XH_', ['PROBE_INLET','PROBE_ICOM']),
    ('panel','J8'): ('JST_GH_', ['+5V','KEY_MAN_RAW','KEY_AUTO_RAW']),
    ('receiver','J2'): ('JST_PH_', ['ISO_0','HOST_LOGIC','LOCAL_LOGIC']),
    ('receiver','J3'): ('JST_PH_', ['ISO_5','ISO_0']),
    ('receiver','J4'): ('JST_VH_', ['FUSED_24','CAB_0','HB_24','PANEL_24','KFB_A1']),
}


def check():
    ports, mating_groups, assemblies = {}, {}, {}
    with tempfile.TemporaryDirectory() as work:
        for name, root in PROJECTS.items():
            xml = Path(work) / (name + '.xml')
            subprocess.run([ROOT/'.tools/kicad-cli','sch','export','netlist','--format','kicadxml',
                            '-o',xml,root], check=True, capture_output=True)
            data = ET.parse(xml)
            nets = {(p.get('ref'),p.get('pin')):n.get('name') for n in data.findall('.//nets/net')
                    for p in n.findall('node')}
            if name in ('receiver','cabinet'):
                assemblies[name] = {
                    c.get('ref'): (c.findtext("fields/field[@name='MPN']"),
                                   {pin:net for (ref,pin),net in nets.items() if ref==c.get('ref')})
                    for c in data.findall('.//components/comp') if not c.get('ref').startswith(('J','H','#'))}
            for (board,ref),(family,expected) in PORTS.items():
                if board != name:
                    continue
                part = data.find(f".//components/comp[@ref='{ref}']")
                footprint = part.findtext('footprint').split(':')[-1]
                pins = {int(num):net for (component,num),net in nets.items() if component==ref and num.isdigit()}
                if family not in footprint or pins != dict(enumerate(expected,1)):
                    raise ValueError(f'{board}.{ref} has wrong header or pinout: {footprint}, {pins}')
                port = f'{board}.{ref}'
                ports[port] = dict(footprint=footprint, pins=pins)
                mating_groups.setdefault((family,len(pins)),set()).add(port)
    for ref, component in assemblies['receiver'].items():
        if assemblies['cabinet'].get(ref) != component:
            raise ValueError(f'Receiver {ref}: cabinet and PCB pinout or part number differ')
    pairs = [sorted(g) for g in mating_groups.values() if len(g)>1]
    if sorted(pairs) != [['main.J31','receiver.J31'],['main.J36','receiver.J36']]:
        raise ValueError('An unrelated checked port accepts a guard or inlet harness')
    source_hashes = {str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
                     for root in PROJECTS.values() for f in sorted(root.parent.glob('*.kicad_sch'))}
    report = dict(source_sha256=source_hashes, checked_ports=ports,
                  receiver_components_compared_with_cabinet=len(assemblies['receiver']), straight_through_harnesses=sorted(pairs),
                  physical_cross_mating_tested=False)
    (HARDWARE/'main-compact-dual/checks/guard-looms.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    check()
