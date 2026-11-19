#!/usr/bin/env python3
"""Replace only J10's footprint block, preserving routing, zones and pad UUIDs.

Run with the KiCad Python wrapper. This can be reapplied to a routed Rev E board.
The project file is retained byte-for-byte; all text outside J10 is unchanged.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import tempfile

BASE = Path(__file__).resolve().parents[1]
NAME = 'TerminalBlock_Phoenix_MKDS-1-2-3.81_1x02_P3.81mm_Horizontal'
FID = 'TerminalBlock_Phoenix:' + NAME
VALUE = 'LIVE CT / FIXED'
MPN = 'Phoenix Contact 1727010 / MKDS 1/2-3,81'
DATASHEET = 'https://www.phoenixcontact.com/en-us/products/printed-circuit-board-terminal-mkds-1-2-381-1727010'
DESCRIPTION = ('Fixed CT-secondary terminal; factory-captive mains-referenced lead, no removable plug. '
               '1 M_CT_HI, 2 M_GND. Support housing during 0.22-0.25 Nm tightening; '
               '5 mm strip; separate strain relief. Disconnect only with pump supply isolated.')


def footprint_span(text):
    for match in re.finditer(r'^\t\(footprint ', text, re.MULTILINE):
        start = match.start() + 1
        depth, quoted, escaped = 0, False, False
        for i in range(start, len(text)):
            char = text[i]
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    if re.search(r'\(property "Reference" "J10"\s', text[start:i+1]):
                        return start, i + 1
                    break
    raise ValueError('Exactly located native J10 footprint required')


def patch(board_path):
    import wx
    app = wx.GetApp() or wx.App(False)
    import pcbnew as p
    board_path = board_path.resolve()
    original = board_path.read_text()
    project_path = board_path.with_suffix('.kicad_pro')
    project_bytes = project_path.read_bytes() if project_path.exists() else None
    board = p.LoadBoard(str(board_path))
    old = board.FindFootprintByReference('J10')
    if old is None:
        raise ValueError('J10 missing')
    pads = {pad.GetNumber(): pad for pad in old.Pads()}
    assert set(pads) == {'1', '2'}
    expected = {'1': (30., 71., 'M_CT_HI'), '2': (33.81, 71., 'M_GND')}
    for number, (x, y, net) in expected.items():
        pad = pads[number]
        assert (p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y), pad.GetNetname()) == (x, y, net)
    assert not old.IsFlipped() and old.GetOrientationDegrees() == 0
    footprint_path = BASE / 'hardware/main-rev-e/libraries/TerminalBlock_Phoenix.pretty'
    new = p.FootprintLoad(str(footprint_path), NAME)
    assert new is not None
    new.SetFPID(p.LIB_ID('TerminalBlock_Phoenix', NAME))
    new.SetUuid(p.KIID(old.m_Uuid.AsString()))
    new.SetReference('J10')
    new.SetValue(VALUE)
    new.SetPath(old.GetPath())
    new.SetSheetname(old.GetSheetname())
    new.SetSheetfile(old.GetSheetfile())
    new.SetLocked(old.IsLocked())
    new.SetPosition(old.GetPosition())
    for name, text in [('MPN', MPN), ('Datasheet', DATASHEET), ('Description', DESCRIPTION)]:
        new.SetField(name, text)
    for field in new.GetFields():
        field.SetVisible(False)
    for graphic in new.GraphicalItems():
        if isinstance(graphic, p.PCB_SHAPE) and graphic.GetLayer() == p.F_SilkS:
            graphic.SetLayer(p.F_Fab)
    for pad in new.Pads():
        old_pad = pads[pad.GetNumber()]
        pad.SetUuid(p.KIID(old_pad.m_Uuid.AsString()))
        pad.SetNet(old_pad.GetNet())
        assert pad.GetPosition() == old_pad.GetPosition()
    board.Remove(old)
    board.Add(new)
    new.BuildCourtyardCaches()
    courtyard = new.GetCourtyard(p.F_CrtYd)
    assert courtyard.OutlineCount() == 1
    overlaps = []
    for other in board.GetFootprints():
        if other.GetReference() == 'J10':
            continue
        other.BuildCourtyardCaches()
        other_courtyard = other.GetCourtyard(p.F_CrtYd)
        if other_courtyard.OutlineCount() and courtyard.Collide(other_courtyard):
            overlaps.append(other.GetReference())
    assert not overlaps, 'Replacement courtyard overlaps: ' + str(overlaps)
    bbox = courtyard.BBox()
    with tempfile.TemporaryDirectory(prefix='pump-e-j10-') as folder:
        candidate = Path(folder) / board_path.name
        p.SaveBoard(str(candidate), board)
        candidate_text = candidate.read_text()
        ns, ne = footprint_span(candidate_text)
        start, end = footprint_span(original)
        replacement = candidate_text[ns:ne]
        updated = original[:start] + replacement + original[end:]
        # Only the explicit J10 footprint expression is substituted.
        board_path.write_text(updated)
    if project_bytes is not None:
        assert project_path.read_bytes() == project_bytes, 'Project unexpectedly changed'
    check = p.LoadBoard(str(board_path))
    actual = check.FindFootprintByReference('J10')
    assert actual.m_Uuid.AsString() == new.m_Uuid.AsString()
    for pad in actual.Pads():
        before = pads[pad.GetNumber()]
        assert pad.m_Uuid.AsString() == before.m_Uuid.AsString()
        assert pad.GetPosition() == before.GetPosition() and pad.GetNetname() == before.GetNetname()
    return {'board': str(board_path.relative_to(BASE)) if board_path.is_relative_to(BASE) else str(board_path),
            'original_pcb_sha256': hashlib.sha256(original.encode()).hexdigest(),
            'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(), 'footprint': FID,
            'outside_J10_text_unchanged': True, 'project_unchanged': True,
            'footprint_and_pad_uuids_preserved': True,
            'pad_centres_and_nets': expected, 'pad_diameter_mm': 2.0, 'drill_mm': 1.1,
            'annulus_mm': .45, 'body_bounds_mm': [28.1, 67.3, 35.71, 74.6],
            'courtyard_bounds_mm': [27.6, 66.8, 36.21, 75.11], 'body_height_mm': 8.5,
            'native_courtyard_polygon_bounds_mm': [p.ToMM(bbox.GetX()), p.ToMM(bbox.GetY()), p.ToMM(bbox.GetRight()), p.ToMM(bbox.GetBottom())],
            'native_courtyard_overlaps': overlaps, 'requires_zone_refill': True,
            'routing_and_clearance_validation_required': True}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board', type=Path, default=BASE / 'hardware/main-rev-e/pump-controller-main-rev-e.kicad_pcb')
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    result = patch(args.board)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
