#!/usr/bin/env python3
"""Independently parse final Rev E CAM, drills, netlist and mask geometry.

Requires Python >=3.10, gerbonara==0.13.0 and shapely==2.1.2. Reads native
geometry evidence produced from the same frozen PCB. Does not alter CAD/CAM.
This validates serialization and nominal mask geometry, not conductive CAM
net extraction, fabrication tolerances or a physical board's electrical safety.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import warnings

from package_main_rev_e import add_board_options, board_variant

from gerbonara import ExcellonFile, GerberFile
from gerbonara import graphic_primitives as gp
from gerbonara.apertures import ApertureMacroInstance
from gerbonara.graphic_objects import Flash, Line
from gerbonara.ipc356 import Netlist, PadType
from gerbonara.layers import LayerStack
from gerbonara.utils import MM
from shapely.geometry import GeometryCollection, Point, Polygon, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

BASE = Path(__file__).resolve().parents[1]
CURVE_ERROR = .000001  # maximum arc chord error, mm
WEB_ROUNDING = .00001  # Gerber coordinate/polygon rounding, not process allowance
NATIVE_CONTOUR_TOLERANCE = .01  # native polygon curve approximation, mm


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arc_points(start, end, center, clockwise):
    radius = math.dist(start, center)
    if radius == 0:
        raise ValueError('Zero-radius Gerber arc')
    first = math.atan2(start[1] - center[1], start[0] - center[0])
    last = math.atan2(end[1] - center[1], end[0] - center[0])
    sweep = (last - first) % (2 * math.pi)
    if clockwise:
        sweep = -((first - last) % (2 * math.pi))
    if math.dist(start, end) < 1e-12:
        sweep = -2 * math.pi if clockwise else 2 * math.pi
    step = 2 * math.acos(max(-1, min(1, 1 - CURVE_ERROR / radius)))
    count = max(1, math.ceil(abs(sweep) / step))
    return [start] + [(center[0] + radius * math.cos(first + sweep * i / count),
                      center[1] + radius * math.sin(first + sweep * i / count))
                     for i in range(1, count)] + [end]


def quad_segments(radius):
    if radius <= 0:
        return 1
    return max(8, math.ceil(math.pi / (4 * math.acos(max(-1, 1 - CURVE_ERROR / radius)))))


def primitive_shape(primitive):
    if isinstance(primitive, gp.Circle):
        return Point(primitive.x, primitive.y).buffer(primitive.r, quad_segs=quad_segments(primitive.r))
    if isinstance(primitive, gp.Rectangle):
        # Avoid a third-party rectangle-to-polygon shortcut: rotate the four
        # actual corners explicitly, including non-axis-aligned rectangles.
        co, si = math.cos(primitive.rotation), math.sin(primitive.rotation)
        return Polygon([(primitive.x + x * co - y * si, primitive.y + x * si + y * co)
                        for x, y in [(-primitive.w/2, -primitive.h/2),
                                     (primitive.w/2, -primitive.h/2),
                                     (primitive.w/2, primitive.h/2),
                                     (-primitive.w/2, primitive.h/2)]])
    if isinstance(primitive, gp.ArcPoly):
        points = []
        for start, end, arc in primitive.segments:
            points.extend(arc_points(start, end, arc[1], arc[0])[:-1] if arc else [start])
        shape = Polygon(points)
        if not shape.is_valid:
            raise ValueError('Invalid parsed Gerber polygon; no automatic geometry repair applied')
        return shape
    if isinstance(primitive, gp.Line):
        return LineString([(primitive.x1, primitive.y1), (primitive.x2, primitive.y2)]).buffer(
            primitive.width / 2, quad_segs=quad_segments(primitive.width / 2))
    if isinstance(primitive, gp.Arc):
        return LineString(arc_points((primitive.x1, primitive.y1), (primitive.x2, primitive.y2),
                                     (primitive.cx, primitive.cy), primitive.clockwise)).buffer(
            primitive.width / 2, quad_segs=quad_segments(primitive.width / 2))
    raise ValueError('Unsupported Gerber primitive: ' + type(primitive).__name__)


def image_geometry(gerber):
    """Resolve aperture exposure locally, then layer polarity in file order."""
    image = GeometryCollection()
    pending_dark = []
    primitive_count = 0
    for obj in gerber.objects:
        if isinstance(getattr(obj, 'aperture', None), ApertureMacroInstance):
            raise ValueError('Export with aperture macros disabled: Gerbonara 0.13 macro rotation is not used for mask evidence')
        aperture = GeometryCollection()
        aperture_dark = []
        for primitive in obj.to_primitives(unit=MM):
            shape = primitive_shape(primitive)
            primitive_count += 1
            if primitive.polarity_dark == obj.polarity_dark:
                aperture_dark.append(shape)
            else:
                aperture = unary_union([aperture, *aperture_dark]).difference(shape)
                aperture_dark = []
        aperture = unary_union([aperture, *aperture_dark])
        if obj.polarity_dark:
            pending_dark.append(aperture)
        else:
            image = unary_union([image, *pending_dark]).difference(aperture)
            pending_dark = []
    return unary_union([image, *pending_dark]), primitive_count


def polygons(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape]
    return [part for child in shape.geoms for part in polygons(child)]


def mask_review(parsed, native):
    reviews = {}
    for extension, side in [('GTS', 'F.Mask'), ('GBS', 'B.Mask')]:
        actual, primitive_count = image_geometry(parsed[extension])
        openings = polygons(actual)
        expected_groups = defaultdict(list)
        smt_groups = defaultdict(list)
        for pad in native['inventory']['mask_pads']:
            if pad['side'] != side:
                continue
            contours = []
            for contour in pad['copper_contours_mm']:
                flip = lambda pts: [(x, -y) for x, y in pts]
                contours.append(Polygon(flip(contour['outline']), [flip(h) for h in contour['holes']]))
            shape = unary_union(contours).buffer(pad['expansion_mm'], quad_segs=128)
            key = pad['ref'] + '.' + pad['pin']
            expected_groups[key].append(shape)
            if pad['smd']:
                smt_groups[key].append(shape)
        expected = {key: unary_union(value) for key, value in expected_groups.items()}
        expected_union = unary_union(list(expected.values()))
        # Native curved contours are approximations. The independent web test
        # below uses only exported Gerber geometry at a much tighter precision.
        extra = actual.difference(expected_union.buffer(NATIVE_CONTOUR_TOLERANCE)).area
        missing = expected_union.difference(actual.buffer(NATIVE_CONTOUR_TOLERANCE)).area
        tree = STRtree(openings)
        assignments = defaultdict(set)
        absent = []
        for key, shape in expected.items():
            hits = [int(i) for i in tree.query(shape, predicate='intersects')
                    if openings[int(i)].intersection(shape).area > 1e-8]
            if not hits:
                absent.append(key)
            for index in hits:
                assignments[index].add(key)
        merged = [{'opening': i, 'pins': sorted(keys)} for i, keys in assignments.items() if len(keys) > 1]
        gaps = []
        minimum_web = None
        for i, shape in enumerate(openings):
            for j in tree.query(shape.buffer(.11)):
                j = int(j)
                if j <= i:
                    continue
                gap = shape.distance(openings[j])
                minimum_web = gap if minimum_web is None else min(minimum_web, gap)
                if gap + WEB_ROUNDING < .10:
                    gaps.append({'openings': [i, j], 'gap_mm': gap,
                                 'pins': [sorted(assignments[i]), sorted(assignments[j])]})
        # Map actual openings to SMT lands, then check every physical hole.
        smt_openings = [(i, shape) for i, shape in enumerate(openings)
                        if assignments[i] & set(smt_groups)]
        hole_overlaps = []
        for hole in native['holes']:
            center = Point(hole['xy_mm'][0], -hole['xy_mm'][1])
            radius = max(hole['drill_mm']) / 2
            for i, shape in smt_openings:
                if center.distance(shape) < radius - WEB_ROUNDING:
                    hole_overlaps.append({'hole_uuid': hole['uuid'], 'opening': i,
                                          'pins': sorted(assignments[i])})
        passed = not (extra > 1e-8 or missing > 1e-8 or absent or merged or gaps or hole_overlaps)
        reviews[side] = {'passed': passed, 'parsed_primitive_count': primitive_count,
                         'actual_connected_openings': len(openings), 'expected_physical_pin_groups': len(expected),
                         'unmatched_native_pins': absent, 'merged_distinct_pin_openings': merged,
                         'extra_area_outside_native_tolerance_mm2': extra,
                         'missing_area_outside_native_tolerance_mm2': missing,
                         'minimum_web_within_0p11mm_search': minimum_web,
                         'mask_web_violations': gaps, 'holes_overlapping_actual_smt_openings': hole_overlaps}
    return reviews


def ipc_pin_review(source_pins, source, actual):
    """Compare IPC pins with the frozen source, including exact KiCad NC names.

    An unconnected net alias belongs to one reference, pin name and pad number.
    A generic 'unconnected-*' prefix must never authorize another pad's net.
    """
    expected = {(p['ref'], p['pin']): p['net'] for p in source_pins}
    if len(expected) != len(source_pins):
        raise ValueError('Duplicate pin keys in native source inventory')
    source_expected, nc_aliases = {}, {}
    for sheet in source['sheets']:
        for component in sheet['components']:
            if not component.get('on_board', True):
                continue
            for pin in component.get('pins', []):
                key = (component['ref'], str(pin['num']))
                if key in source_expected:
                    raise ValueError('Duplicate component/pin in source: ' + repr(key))
                source_expected[key] = pin.get('net') or ''
                if not source_expected[key]:
                    name = pin.get('name')
                    if not name:
                        raise ValueError('NC source pin has no explicit name: ' + repr(key))
                    nc_aliases[key] = f'unconnected-({key[0]}-{name}-Pad{key[1]})'
    if expected != source_expected:
        raise ValueError('Native inventory pin mapping differs from the same hashed source')
    differences, normalized = [], []
    for (ref, pin), net in expected.items():
        nets = actual.get((ref, pin), set())
        if net:
            valid = nets == {net}
        else:
            alias = nc_aliases[ref, pin]
            # Standard explicit NC tokens are accepted as single states only.
            # Missing records, mixed names and another pad's NC alias fail.
            valid = nets in ({''}, {'N/C'}, {alias})
            if nets == {alias}:
                normalized.append({'ref': ref, 'pin': pin, 'source_net': '',
                                   'exact_native_nc_alias': alias})
        if not valid:
            differences.append({'ref': ref, 'pin': pin, 'expected': net,
                                'actual': sorted(nets)})
    return {'connected_source_pins_checked': sum(bool(x) for x in expected.values()),
            'unconnected_source_pins_checked': len(nc_aliases),
            'source_inventory_pin_maps_identical': True,
            'nc_alias_policy': 'Exact reference + source pin name + pad number only; no prefix wildcard. Missing NC records and mixed net names fail.',
            'normalized_nc_aliases': normalized,
            'pin_net_differences': differences,
            'unexpected_pins': sorted(set(actual) - set(expected))}


def audit(args):
    for name in ['board', 'source', 'native', 'cam', 'stencil', 'previews', 'output']:
        setattr(args, name, getattr(args, name).resolve())
    native = json.loads(args.native.read_text())
    before = sha(args.board)
    if native['pcb_sha256'] != before or native['source_sha256'] != sha(args.source):
        raise ValueError('Native inventory is stale for this PCB/source')
    source = json.loads(args.source.read_text())
    expected_revision = source['revision'] if source['board'].get('variant') == 'compact-dual' else None
    errors, caught_warnings, parsed, files, layers = [], [], {}, {}, {}
    roles = {'GTL': ('Copper,L1,Top', ('top', 'copper')),
             'G2L': ('Copper,L2,Inr', ('inner1', 'copper')),
             'G3L': ('Copper,L3,Inr', ('inner2', 'copper')),
             'G4L': ('Copper,L4,Inr', ('inner3', 'copper')),
             'G5L': ('Copper,L5,Inr', ('inner4', 'copper')),
             'GBL': ('Copper,L6,Bot', ('bottom', 'copper')),
             'GTS': ('Soldermask,Top', ('top', 'mask')), 'GBS': ('Soldermask,Bot', ('bottom', 'mask')),
             'GTO': ('Legend,Top', ('top', 'silk')), 'GBO': ('Legend,Bot', ('bottom', 'silk')),
             'GKO': ('Profile,NP', ('mechanical', 'outline')),
             'GTP': ('Paste,Top', ('top', 'paste')), 'GBP': ('Paste,Bot', ('bottom', 'paste'))}
    def parse(path, parser, **kwargs):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always')
            warnings.simplefilter('ignore', DeprecationWarning)
            result = parser.open(path, **kwargs)
        caught_warnings.extend({'file': path.name, 'message': str(w.message).replace(str(BASE) + '/', '')} for w in ws)
        files[str(path.relative_to(BASE))] = {'sha256': sha(path)}
        return result
    for ext, (role, key) in roles.items():
        directory = args.stencil if ext in {'GTP', 'GBP'} else args.cam
        candidates = [p for p in directory.iterdir() if p.is_file()
                      and p.suffix.lower() not in {'.zip', '.pdf', '.png'}
                      and '%TF.FileFunction,' + role + '*%' in p.read_text(errors='replace')]
        if len(candidates) != 1:
            raise ValueError('Expected exactly one Gerber with role ' + role)
        path = candidates[0]
        content = path.read_text()
        if '%TF.FileFunction,' + role + '*%' not in content or '%MOMM*%' not in content:
            errors.append('Unexpected layer role/units: ' + ext)
        if expected_revision:
            project_ids = re.findall(r'^%TF\.ProjectId,([^*]+)\*%$', content, re.MULTILINE)
            if len(project_ids) != 1 or project_ids[0].split(',')[-1] != expected_revision:
                errors.append('Incorrect embedded Gerber project revision: ' + ext)
        if not content.rstrip().endswith('M02*'):
            errors.append('Gerber end marker absent: ' + ext)
        parsed[ext] = parse(path, GerberFile)
        if any(isinstance(getattr(obj, 'aperture', None), ApertureMacroInstance)
               for obj in parsed[ext].objects):
            errors.append('Aperture macros require a macro-disabled export for reliable geometry/preview: ' + ext)
        layers[key] = parsed[ext]
        files[str(path.relative_to(BASE))].update(objects=len(parsed[ext].objects), layer_function=role)
    ends = []
    for obj in parsed['GKO'].objects:
        if not isinstance(obj, Line):
            errors.append('Unsupported non-line outline object')
            continue
        ends += [(MM(obj.x1, obj.unit), MM(obj.y1, obj.unit)), (MM(obj.x2, obj.unit), MM(obj.y2, obj.unit))]
    corners = Counter((round(x, 6), round(y, 6)) for x, y in ends)
    bounds = ((min(x for x, y in ends), min(y for x, y in ends)),
              (max(x for x, y in ends), max(y for x, y in ends)))
    size = [round(bounds[1][i] - bounds[0][i], 6) for i in (0, 1)]
    expected_size = native['outline_size_mm']
    if size != expected_size or len(corners) != 4 or set(corners.values()) != {2}:
        errors.append(f'Gerber outline must match the closed {expected_size} mm native profile')
    drill_checks, drills = {}, []
    for kind, plated in [('PTH', True), ('NPTH', False)]:
        candidates = [p for p in args.cam.iterdir() if p.suffix.lower() in {'.xln', '.drl'}
                      and p.stem.endswith('-' + kind)]
        if len(candidates) != 1:
            raise ValueError('Expected exactly one ' + kind + ' drill file')
        drill = parse(candidates[0], ExcellonFile, plated=plated)
        actual = []
        for obj in drill.objects:
            if not isinstance(obj, Flash):
                errors.append('Unsupported non-round drill feature: ' + kind)
                continue
            actual.append((MM(obj.x, obj.unit), MM(obj.y, obj.unit), MM(obj.aperture.diameter, obj.aperture.unit)))
        expected = [(h['xy_mm'][0], -h['xy_mm'][1], h['drill_mm'][0]) for h in native['holes'] if h['plated'] == plated]
        remaining, missing, max_error = actual.copy(), [], 0
        for hit in expected:
            match = next((i for i, other in enumerate(remaining)
                          if abs(hit[0]-other[0]) <= .000501 and abs(hit[1]-other[1]) <= .000501
                          and abs(hit[2]-other[2]) <= .000001), None)
            if match is None:
                missing.append(hit)
            else:
                other = remaining.pop(match)
                max_error = max(max_error, abs(hit[0]-other[0]), abs(hit[1]-other[1]))
        drill_checks[kind] = {'count': len(actual), 'expected': len(expected), 'missing': missing,
                              'extra': remaining, 'max_coordinate_rounding_error_mm': max_error}
        if missing or remaining:
            errors.append('Native/Excellon drill registration differs: ' + kind)
        drills.append(drill)
    ipc_candidates = list(args.cam.glob('*.d356'))
    if len(ipc_candidates) != 1:
        raise ValueError('Expected exactly one IPC-D-356 reference netlist')
    ipc_path = ipc_candidates[0]
    ipc = parse(ipc_path, Netlist)
    aliases = dict(re.findall(r'^P\s+NNAME(\S+)\s+(\S+)\s*$', ipc_path.read_text(), re.MULTILINE))
    actual = defaultdict(set)
    # A receptacle can have unnumbered mechanical locator holes. Match each
    # to its native NPTH by reference, centre and tool diameter, once only.
    locators = [h for h in native['holes'] if h['ref'] and not re.fullmatch(r'H\d+', h['ref'])
                and h['kind'] == 'npth' and not h['pin'] and not h['net']]
    located = []
    for record in ipc.test_records:
        if not record.ref_des or re.fullmatch(r'H\d+', record.ref_des):
            continue
        pin = getattr(record, 'pin', None) or record.pin_num
        if (pin is None and record.pad_type == PadType.NONPLATED_HOLE
                and record.is_plated is False and not record.is_connected
                and not record.net_name and record.hole_dia is not None):
            dimensions = [MM(record.x, record.unit), -MM(record.y, record.unit),
                          MM(record.hole_dia, record.unit)]
            # IPC-D-356A rounds coordinates and diameter to the nearest 0.1 mil.
            match = next((i for i, h in enumerate(locators)
                          if h['ref'] == record.ref_des and all(abs(x-y) <= .001271 for x, y
                          in zip(dimensions, [*h['xy_mm'], h['drill_mm'][0]]))), None)
            if match is not None:
                located.append(locators.pop(match)['uuid'])
                continue
        actual[(record.ref_des, str(pin))].add(aliases.get(record.net_name, record.net_name) or '')
    if locators:
        errors.append('IPC-D-356 omits native unnumbered mechanical locating holes')
    ipc_review = ipc_pin_review(native['source_pins'], source, actual)
    ipc_review['nonconductive_locators_matched'] = located
    if ipc_review['pin_net_differences'] or ipc_review['unexpected_pins']:
        errors.append('IPC-D-356 pin/net assignments differ from source')
    job_candidates = list(args.cam.glob('*.gbrjob'))
    if len(job_candidates) != 1:
        raise ValueError('Expected exactly one Gerber job file')
    job_path = job_candidates[0]
    job = json.loads(job_path.read_text())
    job_size = job.get('GeneralSpecs', {}).get('Size', {})
    if [job_size.get('X'), job_size.get('Y')] != expected_size:
        errors.append('Job dimensions differ from the native outline')
    board_gerber_names = sorted(Path(path).name for path, details in files.items()
                               if 'layer_function' in details and not details['layer_function'].startswith('Paste,'))
    if sorted(x['Path'] for x in job['FilesAttributes']) != board_gerber_names:
        errors.append('Job manifest does not contain exactly the eleven board Gerbers')
    files[str(job_path.relative_to(BASE))] = {'sha256': sha(job_path)}
    masks = mask_review(parsed, native)
    if not all(x['passed'] for x in masks.values()):
        errors.append('Final exported mask registration/web/opening audit failed')
    args.previews.mkdir(parents=True, exist_ok=True)
    stack = LayerStack(layers, drills, netlist=ipc, board_name=args.name)
    for side in ['top', 'bottom']:
        (args.previews / (side + '-registration.svg')).write_text(str(stack.to_pretty_svg(side=side, margin=1, force_bounds=bounds)))
    for ext in ['GTL', 'G2L', 'G3L', 'G4L', 'G5L', 'GBL', 'GTS', 'GBS']:
        (args.previews / (ext + '.svg')).write_text(str(parsed[ext].to_svg(margin=1, force_bounds=bounds)))
    if sha(args.board) != before:
        errors.append('Native PCB changed during CAM check')
    report = {'pcb_sha256': before, 'source_sha256': sha(args.source), 'native_inventory_sha256': sha(args.native),
              'parser_versions': {x: importlib.metadata.version(x) for x in ['gerbonara', 'shapely']},
              'aperture_macros_required_disabled': True,
              'macro_rotation_reference': 'https://www.ucamco.com/en/guest/downloads/gerber-format',
              'gerber_files_parsed': len(parsed), 'outline_centerline_size_mm': size,
              'outline_bounds_mm': bounds, 'drills': drill_checks,
              'ipc_d356': {'records': len(ipc.test_records), **ipc_review},
              'mask_geometry': masks, 'mask_minimum_web_mm': .10, 'curve_chord_error_mm': CURVE_ERROR,
              'mask_web_rounding_mm': WEB_ROUNDING, 'native_contour_registration_tolerance_mm': NATIVE_CONTOUR_TOLERANCE,
              'file_checks': files, 'parser_warnings': caught_warnings,
              'serialization_registration_and_mask_passed': not errors, 'errors': errors,
              'gerber_conductive_netlist_extracted': False, 'manufacturer_accepted': False,
              'hardware_tested': False, 'release_ready': False,
              'limitations': ['IPC-D-356 is a native-board reference, not extracted Gerber connectivity.',
                              'Nominal mask web/drill geometry does not prove process registration tolerances.',
                              'Preview bottom layers retain unmirrored manufacturing coordinates.']}
    if expected_revision:
        report['x2_project_revision'] = expected_revision
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': not errors, 'errors': errors, 'drill_counts': {k: v['count'] for k, v in drill_checks.items()},
                      'mask_passed': {k: v['passed'] for k, v in masks.items()}}, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    add_board_options(ap)
    for option in ('board', 'source', 'native', 'cam', 'stencil', 'previews', 'output'):
        ap.add_argument('--' + option, type=Path)
    ap.add_argument('--name')
    args = ap.parse_args()
    variant = board_variant(args.compact, args.compact_dual)
    folder = BASE / 'hardware' / variant.directory
    args.board = args.board or folder / (variant.native_name + '.kicad_pcb')
    args.source = args.source or BASE / variant.design
    args.native = args.native or folder / 'checks/independent-geometry.json'
    args.cam = args.cam or folder / 'gerber'
    args.stencil = args.stencil or folder / 'exports/stencil'
    args.previews = args.previews or folder / 'checks/cam-previews'
    args.output = args.output or folder / 'checks/independent-gerbers.json'
    args.name = args.name or variant.cam_name
    raise SystemExit(audit(args))
