"""Package the validated R3 main-board release and its current review evidence."""
import csv
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MF = ROOT/'manufacturing'
REVIEW = ROOT/'verification/pcba-review-2026-11-24'
RELAY = ROOT/'verification/relay-upgrade-2026-11-24'
DFM = ROOT/'verification/dfm-review-2026-11-24'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    release = read(MF/'verification.json')
    checks = 0
    for name, board in release['boards'].items():
        for path, expected in board['source_sha256'].items():
            assert digest(ROOT/path) == expected, path
            checks += 1
        erc, drc = [read(MF/(name+'-'+kind+'.json')) for kind in ('erc','drc')]
        assert not any(sheet['violations'] for sheet in erc['sheets'])
        assert not any(drc[k] for k in ('violations','unconnected_items','schematic_parity'))
        assert board['connectivity']['opens_shorts'] == 0
        assert len(board['injected_faults_detected']) == 2
    for name, expected in release['output_sha256'].items():
        assert digest(MF/name) == expected, name
        checks += 1
    assembly = read(REVIEW/'assembly-check.json')
    relay = read(RELAY/'relay-check.json')
    dfm = read(DFM/'manufacturing-check.json')
    markers = read(DFM/'ic-pin1-check.json')
    polarity = read(DFM/'polarity-check.json')
    current = digest(ROOT/'hardware/main/pump-direct.kicad_pcb')
    assert assembly['board_sha256'] == relay['board_sha256'] == dfm['main']['board_sha256'] == current
    assert markers['board_sha256'] == current and markers['all_ICs_marked']
    assert polarity['main']['board_sha256'] == current
    assert polarity['panel']['board_sha256'] == digest(ROOT/'hardware/panel/pump-panel-rev-f.kicad_pcb')
    assert not assembly['errors'] and not relay['errors']
    assert not any(d['via_drills_beneath_paste'] or d['DNP_paste_pads'] for d in dfm.values())
    with (MF/'main-BOM.csv').open() as stream:
        bom = list(csv.DictReader(stream))
    with (MF/'main-CPL.csv').open() as stream:
        cpl = list(csv.DictReader(stream))
    assert len(bom) == 63 and len(cpl) == 226
    assert all(r['JLCPCB Part #'] for r in bom)
    with zipfile.ZipFile(MF/'main-stencil.zip') as stencil:
        assert b'%TO.C,R2*%' not in stencil.read('main.GBP')
    summary = {
        'date':'2026-11-24', 'revision':'DIRECT-R3-PROTOTYPE',
        'board_sha256':current, 'board_dimensions_mm':[100,139],
        'release_source_and_output_hashes_match':True,
        'release_source_and_output_hashes_checked':checks,
        'main_erc_drc_parity_creepage':'PASS', 'panel_erc_drc_parity':'PASS',
        'gerber_drill_connectivity':'PASS', 'cam_injected_fault_controls':'PASS',
        'named_interface_checks':read(RELAY/'r3-interface-check.json'),
        'hardware_redesign_implemented':True,
        'relay':'G5RL-1-E-HR DC5', 'relay_JLC_code':'C1563288',
        'relay_reserved_stock_and_lead_time':'UNCONFIRMED',
        'terminal_pin_map':{'1':'NO','2':'COM','3':'NC'},
        'terminal_wire_entry':'OUTWARD / top edge',
        'L1_manufacturer_land_corrected':True,
        'orientation_pin_maps_checked':13,
        'printed_IC_pin1_arrows':markers['marked_IC_count'],
        'other_printed_pin1_arrows':sum(p['multi_pin_device_arrows'] for p in polarity.values()),
        'LED_and_single_diode_cathode_marks':len(polarity['main']['cathode_bar_parts']),
        'polarized_capacitor_positive_mark':polarity['main']['positive_marks'],
        'supplier_rotation_corrections_automated':21,
        'manufacturing_paste_via_and_DNP_screen':'PASS; both injected controls detected',
        'assembler_images_reviewed':False,
        'supplier_production_approval':'PENDING actual revised DFM, lead fit, stencil/tooling acceptance and relay sourcing',
        'usb_c_J40_in_JLC_BOM':any('J40' in r['Designator'].split(',') for r in bom),
        'external_starter_interface':'Deferred; direct capacitor switching not qualified by PCB checks',
        'internal_motor_feed_CT_integrated_in_this_release':False,
        'external_supplier_message_purchase_or_upload_performed':False,
        'main_JLC_placements':226, 'main_JLC_BOM_lines':63, 'main_hand_fitted_parts':11,
        'firmware_profile_host_tests':'PASS (simulated hardware only)',
    }
    (REVIEW/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    bottom = ['U10','D32','D31','D30','U31','U20','U37']
    (REVIEW/'additional-assembly-check.json').write_text(json.dumps({
        'assembler_images_reviewed':False, 'board_sha256':current,
        'parts':{r:assembly['parts'][r] for r in bottom},
        'bottom_orientation_sheet':'assembly-orientation-bottom.png'},indent=2)+'\n')
    for kind in ('erc','drc'):
        shutil.copy2(MF/('main-'+kind+'.json'),REVIEW/('main-'+kind+'.json'))
    files = {n:(MF/n).read_bytes() for n in ['main-gerbers.zip','main-BOM.csv','main-CPL.csv','main-stencil.zip']}
    for n in ['panel-gerbers.zip','panel-BOM.csv','panel-CPL.csv','panel-stencil.zip']:
        files['panel/'+n] = (MF/n).read_bytes()
    files['READ-ME-FIRST.txt'] = (
        'DIRECT-R3-PROTOTYPE — matching main PCB files, 2026-11-24\n\n'
        'Extract this outer ZIP. Upload main-gerbers.zip as Gerbers, main-BOM.csv\n'
        'as BOM and main-CPL.csv as placement data. The outer review bundle is\n'
        'NOT the Gerber archive. main-stencil.zip contains revised paste layers.\n\n'
        'The panel/ folder contains matching panel files with added transistor\n'
        'pin-1 arrows. Upload those separately for a panel-board order.\n\n'
        'Finished main board: 100 x 139 mm, six layers. J30/J35 face outward:\n'
        '1 NO, 2 COM, 3 NC. K1/K2: G5RL-1-E-HR DC5 / C1563288 (SPDT, not 1A).\n'
        'Both relays and Phoenix 1711738 / C91156 terminals require factory THT\n'
        'assembly. 226 factory placements, 63 BOM lines, 11 hand-fitted parts.\n'
        'Request JLC-supplied process rails, fiducials and tooling holes; review\n'
        'panel tabs against overhanging edge connectors. Use nylon enclosure mounts.\n\n'
        'L1 retains Sunlord C36409 on corrected lands. R246 via is outside its\n'
        'paste pad. DNP R2 has no paste openings. CPL already includes the 21\n'
        'historical supplier rotations: do NOT apply those offsets again.\n'
        'Four new THT parts have nominal body-centre pick coordinates.\n\n'
        'ERC, full DRC/parity/8 mm isolation targets, CAM and manufacturing\n'
        'screens passed. Supplier placement previews, exact relay stock/lead\n'
        'time, lead fit, L1 solder coverage and stencil/tooling review remain\n'
        'pending. This engineering prototype release does not approve unseen\n'
        'DFM or establish physical insulation, temperature or switching life.\n'
        'External starter/interface selection and internal motor-feed/CT changes\n'
        'are outside this revision. No supplier order action has been performed.\n'
    ).encode()
    for base, names in [
        (REVIEW,['README.md','assembler-reply-draft.txt','assembly-check.json','additional-assembly-check.json',
                 'additional-orientation-reference.txt','assembly-orientation.png','assembly-orientation.pdf',
                 'assembly-orientation-bottom.png','assembly-orientation-bottom.pdf','validation-summary.json',
                 'main-erc.json','main-drc.json']),
        (RELAY,['design-status.txt','relay-check.json','r3-interface-check.json','firmware-profile-check.txt',
                'rotation-guard-negative-controls.json','outward-ports-3d.png']),
        (DFM,['README.md','manufacturing-check.json','body-spacing.json','ic-pin1-check.json','polarity-check.json']),
    ]:
        prefix = 'review/dfm/' if base == DFM else 'review/'
        for name in names:
            files[prefix+name] = (base/name).read_bytes()
    files['review/verification.json'] = (MF/'verification.json').read_bytes()
    for target, source in [('jlc-placement-corrections.json','tools/data/jlc-placement-corrections.json'),
                           ('connections.md','docs/connections.md'),('main-schematic.pdf','docs/main-schematic.pdf')]:
        files['review/'+target] = (ROOT/source).read_bytes()
    manifest = {name:hashlib.sha256(data).hexdigest() for name,data in sorted(files.items())}
    files['SHA256.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    bundle = MF/'pump-controller-R3-JLC-upload.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files.items()):
            archive.writestr(name,data)
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        for name,expected in manifest.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == expected, name
    shutil.copy2(bundle,REVIEW/'pcba-correction-review-package.zip')
    print('PASS:',checks,'release hashes;',len(files),'bundled files;',bundle.name)


if __name__ == '__main__':
    main()
