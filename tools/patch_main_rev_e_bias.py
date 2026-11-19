#!/usr/bin/env python3
"""Apply Rev E reset-bias values without altering connectivity or PCB geometry.

The GPIO pull-up resistance is only typical in the MCU data sheet. These
values improve the reset bias; they do not qualify every reset/fault waveform.
Use --source for JSON/symbol/schematic/BOM updates and --board PATH for an
existing placed or routed board. Both operations are idempotent.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re

BASE = Path(__file__).resolve().parents[1]
CHANGES = {
    'R70': ('47k', 'Raw clear pullup; limits D35 diode sink current below 100 uA for improved LOW margin at U36.'),
    'R71': ('2.2k', 'HEARTBEAT reset pulldown; overrides the typical MCU weak pullup; verify all reset modes.'),
    'R72': ('2.2k', 'PERMIT_D reset pulldown; overrides the typical MCU weak pullup; verify all reset modes.'),
    'R78': ('2.2k', 'ARM_CMD reset pulldown; overrides the typical UART RX pullup; no boot edge may re-arm.'),
    'R77': ('2.2k', 'K2 gate reset pulldown; overrides the typical RUN_CMD reset pullup; verify hot leakage and gate levels.'),
    'R76': ('22R', 'K2 gate series resistor; reduced with 2.2k R77 to retain HIGH gate voltage; qualify switching waveform.'),
}


def fields(ref):
    value, description = CHANGES[ref]
    return {'Value': value, 'MPN': f'SPEC: {value} 1%, 0.1W, 0603',
            'Description': description}


def apply_source(data):
    """Value/description-only override used by the main-board generator."""
    found = set()
    for sheet in data['sheets']:
        for component in sheet['components']:
            ref = component['ref']
            if ref in CHANGES:
                for field, value in fields(ref).items():
                    component[field.lower()] = value
                found.add(ref)
    if found != set(CHANGES):
        raise ValueError('Missing reset-bias references: ' + repr(set(CHANGES) - found))


def expression_ranges(text):
    """Return balanced expression ranges, ignoring parentheses inside strings."""
    stack, ranges = [], []
    quoted = escaped = False
    for index, char in enumerate(text):
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
            stack.append(index)
        elif char == ')':
            start = stack.pop()
            ranges.append((start, index + 1))
    if stack or quoted:
        raise ValueError('Unbalanced native CAD text')
    return ranges


def patch_native(path):
    """Update only property strings in target footprint/symbol expressions."""
    original = path.read_text()
    replacements = []
    for start, end in expression_ranges(original):
        block = original[start:end]
        if not re.match(r'\((?:footprint|symbol)\s', block):
            continue
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', block)
        if not ref_match or ref_match.group(1) not in CHANGES:
            continue
        # A containing library/schematic expression is never selected; the
        # selected symbol/footprint itself owns the Reference property.
        ref = ref_match.group(1)
        updated = block
        for key, value in fields(ref).items():
            pattern = r'(\(property "' + key + r'" )"(?:\\.|[^"\\])*"'
            updated = re.sub(pattern, lambda m: m.group(1) + json.dumps(value), updated)
        if updated != block:
            replacements.append((start, end, updated))
    # Parent and child matching would corrupt offsets; reject rather than guess.
    ordered = sorted(replacements)
    if any(a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Overlapping field update blocks')
    updated = original
    for start, end, replacement in reversed(ordered):
        updated = updated[:start] + replacement + updated[end:]
    for pattern in [r'\(uuid\s+"([^"]+)"\)', r'\(path\s+"([^"]+)"']:
        if re.findall(pattern, original) != re.findall(pattern, updated):
            raise ValueError('Identity changed during property-only patch')
    if updated != original:
        path.write_text(updated)
    return {'path': str(path.relative_to(BASE)) if path.is_relative_to(BASE) else str(path),
            'changed': updated != original,
            'sha256': hashlib.sha256(updated.encode()).hexdigest()}


def update_source_files():
    source = BASE / 'design/main-rev-e.json'
    data = json.loads(source.read_text())
    before = {c['ref']: c['pins'] for s in data['sheets'] for c in s['components']}
    apply_source(data)
    assert before == {c['ref']: c['pins'] for s in data['sheets'] for c in s['components']}
    source.write_text(json.dumps(data, indent=2) + '\n')
    native = BASE / 'hardware/main-rev-e'
    results = [patch_native(native / 'relay_protection_1.kicad_sch'),
               patch_native(native / 'Pump.kicad_sym')]
    with (native / 'bom.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        columns, rows = reader.fieldnames, list(reader)
    for row in rows:
        if row['Reference'] in CHANGES:
            row.update(fields(row['Reference']))
    with (native / 'bom.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='store_true')
    parser.add_argument('--board', type=Path, action='append', default=[])
    args = parser.parse_args()
    if not args.source and not args.board:
        parser.error('Select --source and/or --board PATH')
    results = update_source_files() if args.source else []
    for board in args.board:
        results.append(patch_native(board.resolve()))
    print(json.dumps(results, indent=2))
