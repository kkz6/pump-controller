"""Check L1 and both PCBA orientation query lists; draw each board side.

Run with KiCad's Python (pcbnew module), from any directory. This checks native
pad geometry/net assignments, not the assembler's proposed component pictures.
The default output is verification/pcba-review-2026-11-24/R4. Nothing is sent to JLC.
"""
import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path

import pcbnew
from prepare_jlc_assembly import rotation_offset

ROOT = Path(__file__).resolve().parents[1]
# Manufacturer top-view pinouts, reviewed 2026-11-24. Grounds on U2 pins 1/4/5
# are PGND/AGND/FB respectively for the fixed-output TPS62162.
PARTS = {
    'U22': ('ADS1115IDGSR', {1: 'GND', 3: 'GND', 8: '+3V3', 9: 'I2C_SDA', 10: 'I2C_SCL'},
            (-1.5, -1.5, 1.5, 1.5)),
    'D35': ('BAT54WS-7-F', {1: 'INTERLOCK_OK', 2: 'SAFE_CLEAR_N'}, (-0.85, -0.65, 0.85, 0.65)),
    'U33': ('MCP23017-E/SS', {1: 'START_FILTER', 9: '+3V3', 10: 'GND', 12: 'I2C_SCL', 13: 'I2C_SDA'},
            (-2.65, -5.1, 2.65, 5.1)),
    'U21': ('TMUX1208PWR', {1: 'MUX_A0', 2: '+3V3', 8: 'PROBE_MUX_OUT', 13: '+3V3', 14: 'GND'},
            (-2.2, -2.5, 2.2, 2.5)),
    'U3': ('ESP32-C6-MINI-1U-H4', {1: 'GND', 3: '+3V3', 8: 'MCU_EN', 17: 'USB_DM_MCU', 18: 'USB_DP_MCU', 53: 'GND'},
           (-6.6, -6.9, 6.6, 5.6)),
    'U2': ('TPS62162DSGR', {1: 'GND', 2: '+5V', 3: '+5V', 4: 'GND', 5: 'GND', 6: '+3V3', 7: 'BUCK_SW', 9: 'GND'},
           (-1, -1, 1, 1)),
    'L1': ('SWPA4030S2R2MT', {1: 'BUCK_SW', 2: '+3V3'}, (-2, -2, 2, 2)),
    'U10': ('ADE7953ACPZ', {2: 'M_RESET_N', 4: 'M_GND', 7: 'M_3V3', 8: 'M_3V3',
                         14: 'M_GND', 16: 'M_GND', 17: 'M_3V3', 29: 'M_GND'}, (-2.5, -2.5, 2.5, 2.5)),
    'D32': ('1N4148W', {1: '+5V_CMD', 2: 'K2_LOW'}, (-1.8, -0.85, 1.8, 0.85)),
    'D31': ('1N4148W', {1: 'K1_5V', 2: 'K1_LOW'}, (-1.8, -0.85, 1.8, 0.85)),
    'D30': ('BAT54WS-7-F', {1: 'MCU_EN', 2: 'SAFE_CLEAR_N'}, (-0.85, -0.65, 0.85, 0.65)),
    'U31': ('SN74LVC1G74DCUR', {1: 'ARM_CMD', 2: '+3V3', 4: 'GND', 5: 'ARM_Q',
                             6: 'ARM_CLEAR_N', 7: '+3V3', 8: '+3V3'}, (-1.1, -1.25, 1.1, 1.25)),
    'U20': ('TLV9004IPWR', {1: 'PROBE_BIAS_RAW', 4: '+3V3', 11: 'GND'}, (-2.2, -2.5, 2.2, 2.5)),
    'U37': ('74LVC3G17DC,125', {1: 'STOP_SENSE_RAW', 2: 'AUTO_SENSE', 3: 'MAN_SENSE_RAW',
                              4: 'GND', 5: 'MAN_SENSE', 6: 'AUTO_SENSE_RAW',
                              7: 'STOP_SENSE', 8: '+3V3'}, (-1.1, -1.25, 1.1, 1.25)),
}
BOTTOM_REFS = ['U10', 'D32', 'D31', 'D30', 'U31', 'U20', 'U37']


def mm(point):
    return [pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)]


def transform(point, origin, angle):
    a = math.radians(angle)
    x, y = point
    return [origin[0] + x * math.cos(a) + y * math.sin(a),
            origin[1] - x * math.sin(a) + y * math.cos(a)]


def close(a, b):
    return abs(a - b) < 0.00001


def check(path, cpl_path):
    board = pcbnew.LoadBoard(str(path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    with cpl_path.open(newline='') as stream:
        cpl = {row['Designator']: row for row in csv.DictReader(stream)}
    result = {'board': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
              'board_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'assembler_images_reviewed': False, 'parts': {}, 'errors': []}
    errors = result['errors']
    for ref, (mpn, expected, body) in PARTS.items():
        fp = footprints[ref]
        pos, angle = mm(fp.GetPosition()), fp.GetOrientationDegrees()
        pads = {p.GetNumber(): p for p in fp.Pads() if p.GetNumber()}
        actual_mpn = fp.GetFieldText('MPN')
        if actual_mpn != mpn:
            errors.append('{}: wrong MPN {}'.format(ref, actual_mpn))
        for pin, net in expected.items():
            actual = pads[str(pin)].GetNetname()
            if actual != net:
                errors.append('{}.{}: expected {}, got {}'.format(ref, pin, net, actual))
        row = cpl[ref]
        side = 'Bottom' if ref in BOTTOM_REFS else 'Top'
        offset = float(rotation_offset('main', ref, mpn, str(fp.GetFPID().GetLibItemName()), side))
        if (row['Layer'] != side or not close(float(row['Mid X']), pos[0]) or
                not close(float(row['Mid Y']), -pos[1]) or
                not close(float(row['Rotation']) % 360, (angle + offset) % 360)):
            errors.append('{}: CPL disagrees with native datum/side plus recorded JLC rotation correction'.format(ref))
        if fp.GetLayerName() != ('B.Cu' if side == 'Bottom' else 'F.Cu'):
            errors.append('{}: unexpected board side'.format(ref))
        info = {'mpn': mpn, 'side': side, 'native_datum_xy_mm': pos, 'native_rotation_deg': angle,
                'jlc_rotation_correction_deg': offset, 'jlc_CPL_rotation_deg': (angle+offset)%360,
                'pin1_or_cathode_xy_mm': mm(pads['1'].GetPosition()),
                'pin1_or_cathode_net': pads['1'].GetNetname(),
                'body_corners_xy_mm': [transform(p, pos, angle) for p in
                                      [(body[0], body[1]), (body[2], body[1]),
                                       (body[2], body[3]), (body[0], body[3])]],
                'pads': [{'number': p.GetNumber(), 'xy_mm': mm(p.GetPosition()),
                          'size_mm': mm(p.GetSize()), 'angle_deg': p.GetOrientationDegrees(),
                          'net': p.GetNetname()} for p in fp.Pads() if p.GetNumber()]}
        if ref == 'L1':
            ident = fp.GetFPID()
            if (ident.GetLibNickname(), ident.GetLibItemName()) != ('Inductor_SMD', 'L_Sunlord_SWPA4030S'):
                errors.append('L1: incorrect footprint identity')
            for number, local in [('1', [-1.5, 0]), ('2', [1.5, 0])]:
                pad = pads[number]
                wanted = transform(local, pos, angle)
                if not all(close(a, b) for a, b in zip(mm(pad.GetPosition()), wanted)):
                    errors.append('L1.{}: wrong manufacturer pad position'.format(number))
                if not all(close(a, b) for a, b in zip(mm(pad.GetSize()), [1.1, 3.7])):
                    errors.append('L1.{}: wrong manufacturer pad size'.format(number))
            info['manufacturer_pad_gap_mm'] = 1.9
        result['parts'][ref] = info
    return result


def svg(result, bottom=False):
    esc = html.escape
    parts = result['parts']
    height = 1640 if bottom else 1230
    text = ['<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="{}" viewBox="0 0 1560 {}">'.format(height, height),
            '<rect width="1560" height="{}" fill="#f2f5f7"/>'.format(height),
            '<g font-family="Arial,Helvetica,sans-serif" fill="#163044">',
            '<text x="45" y="48" font-size="28" font-weight="bold">R4 PCBA orientation reference - SMT026112161707_Y2</text>',
            '<text x="45" y="80" font-size="18">{} VIEW. Every card keeps the same board direction. Orange identifies pin 1 or the cathode.</text>'.format('BOTTOM (X mirrored)' if bottom else 'TOP'),
            '<text x="45" y="108" font-size="17" fill="#9b4b00">Expected native design only. Assembler pictures are still required before production approval.</text>']
    for index, ref in enumerate(BOTTOM_REFS if bottom else ['U22', 'D35', 'U33', 'U21', 'U3', 'U2']):
        p = parts[ref]
        x0, y0 = 35 + (index % 3) * 510, 130 + (index // 3) * 440
        text += ['<rect x="{}" y="{}" width="490" height="420" rx="12" fill="white" stroke="#ccd6de"/>'.format(x0, y0),
                 '<text x="{}" y="{}" font-size="24" font-weight="bold">{}</text>'.format(x0 + 18, y0 + 34, ref),
                 '<text x="{}" y="{}" font-size="16">{}</text>'.format(x0 + 18, y0 + 60, esc(p['mpn']))]
        all_xy = p['body_corners_xy_mm'] + [q['xy_mm'] for q in p['pads']]
        xmin, xmax = min(q[0] for q in all_xy), max(q[0] for q in all_xy)
        ymin, ymax = min(q[1] for q in all_xy), max(q[1] for q in all_xy)
        scale = min(330 / (xmax - xmin + 2), 220 / (ymax - ymin + 2))
        cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
        def xy(pt):
            return [x0 + 245 + (pt[0] - cx) * scale * (-1 if bottom else 1), y0 + 205 + (pt[1] - cy) * scale]
        polygon = ' '.join('{:.2f},{:.2f}'.format(*xy(pt)) for pt in p['body_corners_xy_mm'])
        text.append('<polygon points="{}" fill="#e5edf2" stroke="#537083" stroke-width="2"/>'.format(polygon))
        if ref == 'U3':
            connector = transform([-4.9, -5.35], p['native_datum_xy_mm'], p['native_rotation_deg'])
            ax, ay = xy(connector)
            text.append('<circle cx="{:.2f}" cy="{:.2f}" r="7" fill="white" stroke="#537083" stroke-width="2"/>'.format(ax, ay))
        for pad in p['pads']:
            x, y = xy(pad['xy_mm']); w, h = [n * scale for n in pad['size_mm']]
            color = '#ed8a23' if pad['number'] == '1' else '#8aa7b8'
            text.append('<rect x="{:.2f}" y="{:.2f}" width="{:.2f}" height="{:.2f}" fill="{}" stroke="white" stroke-width="1" transform="rotate({:.2f} {:.2f} {:.2f})"/>'.format(x-w/2, y-h/2, w, h, color, pad['angle_deg'] if bottom else -pad['angle_deg'], x, y))
        px, py = xy(p['pin1_or_cathode_xy_mm'])
        label = 'K / pin 1' if ref.startswith('D') else 'Pin 1'
        text.append('<circle cx="{:.2f}" cy="{:.2f}" r="13" fill="none" stroke="#c76700" stroke-width="3"/>'.format(px, py))
        text.append('<text x="{}" y="{}" font-size="17" fill="#ae5900" font-weight="bold">{} - {}</text>'.format(x0+18, y0+345, label, esc(p['pin1_or_cathode_net'])))
        px, py = p['pin1_or_cathode_xy_mm']
        text.append('<text x="{}" y="{}" font-size="16">Native X {:.4f}, Y {:.4f} mm (Y down)</text>'.format(x0+18, y0+373, px, py))
        note = 'Antenna edge faces LEFT; pad 53 is a separate corner GND.' if ref == 'U3' else ('Cathode band faces BOTTOM in this view.' if ref == 'D30' else ('Cathode band faces RIGHT in this bottom view.' if ref in ['D31', 'D32'] else ('Cathode band faces LEFT; anode is on the RIGHT.' if ref == 'D35' else 'Pin-1 corner must align with the orange pad.')))
        text.append('<text x="{}" y="{}" font-size="13">{}</text>'.format(x0+18, y0+400, esc(note)))
    if bottom:
        text += ['<text x="45" y="1490" font-size="21" font-weight="bold">Latest seven references: all on the BOTTOM side.</text>',
                 '<text x="45" y="1525" font-size="18">X is mirrored for the physical bottom view. Coordinate labels remain native KiCad coordinates.</text>',
                 '<text x="45" y="1560" font-size="18">Register the board outline before comparing a supplier image; do not infer polarity from text direction.</text>',
                 '<text x="45" y="1600" font-size="16">Expected design only. The actual supplier DFM images and final placement still require review.</text>', '</g></svg>']
        return '\n'.join(text)
    text += ['<text x="45" y="1063" font-size="23" font-weight="bold">L1 - revised board only: Sunlord SWPA4030S2R2MT (C36409)</text>',
             '<text x="45" y="1097" font-size="19">Two 1.10 x 3.70 mm pads; centres 3.00 mm apart; gap 1.90 mm. Inductor has no electrical polarity.</text>',
             '<text x="45" y="1130" font-size="18">Held order is not fabricated: submit the corrected Gerbers, BOM, CPL and stencil through JLC file replacement.</text>',
             '<text x="45" y="1163" font-size="18">Keep the Sunlord inductor. Confirm pad coverage and BOTH orientation query lists before production.</text>',
             '<text x="45" y="1200" font-size="15">Coordinates are from the KiCad design; they do not establish the assembler library\'s zero-angle convention.</text>', '</g></svg>']
    return '\n'.join(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT/'hardware/main/pump-direct.kicad_pcb')
    parser.add_argument('--cpl', type=Path, default=ROOT/'manufacturing/main-CPL.csv')
    parser.add_argument('--output', type=Path, default=ROOT/'verification/pcba-review-2026-11-24/R4')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = check(args.board.resolve(), args.cpl.resolve())
    (args.output/'assembly-check.json').write_text(json.dumps(result, indent=2)+'\n')
    (args.output/'assembly-orientation.svg').write_text(svg(result))
    (args.output/'assembly-orientation-bottom.svg').write_text(svg(result, bottom=True))
    if result['errors']:
        raise SystemExit('\n'.join(result['errors']))
    print('PASS: L1 and thirteen orientation queries, native pin nets, board sides, CPL consistency and L1 dimensions.')
    print('Assembler images reviewed: NO. Production approval: PENDING.')


if __name__ == '__main__':
    main()
