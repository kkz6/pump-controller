#!/usr/bin/env python3
"""Measure native KiCad tracks and filled ground planes for the seven local bypasses."""
import argparse
from collections import defaultdict
import hashlib
from heapq import heapify, heappop, heappush
import json
import math
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "hardware/main-compact-dual"
ADUM = {"C56": (11, 10), "C57": (1, 2), "C59": (18, 19), "C60": (28, 27)}
PROBES = {"C102": ("U20", 4, 11), "C103": ("U21", 13, 14), "C104": ("U22", 8, 3)}
SUPPLY = {"C56": "+5V", "C57": "+3V3", "C59": "M_ISO_RAW", "C60": "M_3V3"}
GROUND = {"C56": "GND", "C57": "GND", "C59": "M_ISO_GND", "C60": "M_GND"}


def xy(point):
    return point.x, point.y


def point(position):
    return pcb.VECTOR2I(*position)


def covered(start, end, pad):
    """Length inside a convex endpoint land, rounded down to native coordinate accuracy."""
    at_start, at_end = pad.HitTest(point(start)), pad.HitTest(point(end))
    length = math.dist(start, end)
    if at_start and at_end:
        return length
    if not (at_start or at_end):
        return 0
    if at_end:
        start, end = end, start
    low, high = 0.0, 1.0
    for _ in range(25):
        t = (low + high) / 2
        pos = tuple(round(a + t * (b - a)) for a, b in zip(start, end))
        if pad.HitTest(point(pos)):
            low = t
        else:
            high = t
    return max(0, low * length - 2)


class Board:
    def __init__(self, path):
        self.board = pcb.LoadBoard(str(path))
        self.parts = {f.GetReference(): f for f in self.board.GetFootprints()}
        self.traces = defaultdict(list)
        self.vias = defaultdict(list)
        for trace in self.board.GetTracks():
            if isinstance(trace, pcb.PCB_VIA):
                self.vias[trace.GetNetname()].append(trace)
            else:
                self.traces[trace.GetLayer(), trace.GetNetname()].append(trace)

    def pad(self, ref, pin):
        return self.parts[ref].FindPadByNumber(str(pin))

    def route(self, start_pad, layer, end_pad=None):
        """Shortest same-face copper path from an endpoint land to another land or GND via."""
        net = start_pad.GetNetname()
        if end_pad and end_pad.GetNetname() != net:
            raise ValueError(f"Expected matching nets, found {net} and {end_pad.GetNetname()}")
        graph = defaultdict(list)
        for t in self.traces[layer, net]:
            a, b = xy(t.GetStart()), xy(t.GetEnd())
            length = math.dist(a, b)
            if not length:
                continue
            free = length - covered(a, b, start_pad)
            if end_pad:
                free -= covered(a, b, end_pad)
            weight = max(0, free) / 1e6
            graph[a].append((b, weight, length / 1e6))
            graph[b].append((a, weight, length / 1e6))
        starts = [q for q in graph if start_pad.HitTest(point(q))]
        if end_pad:
            ends = {q for q in graph if end_pad.HitTest(point(q))}
            planes = {}
        else:
            planes = self.ground_plane_vias(layer)
            ends = set(planes)
        queue = [(0, math.dist(q, xy(start_pad.GetPosition())) / 1e6, q) for q in starts]
        # All starting nodes have equal weight, so their tuple order must be heapified.
        heapify(queue)
        visited = set()
        while queue:
            free, traced, q = heappop(queue)
            if q in visited:
                continue
            visited.add(q)
            if q in ends:
                if end_pad:
                    traced += math.dist(q, xy(end_pad.GetPosition())) / 1e6
                result = {"land_edge_trace_mm": round(free, 4),
                          "pad_center_route_mm": round(traced, 4)}
                if not end_pad:
                    result.update(via_mm=[round(x / 1e6, 4) for x in q],
                                  plane_island=planes[q])
                return result
            for other, cost, length in graph[q]:
                if other not in visited:
                    heappush(queue, (free + cost, traced + length, other))
        raise ValueError(f"No same-layer route from {start_pad.GetParentFootprint().GetReference()}."
                         f"{start_pad.GetNumber()} on {net} to the required endpoint")

    def ground_plane_vias(self, layer):
        """Require the via centre to occur in a filled polygon on the first inner GND plane."""
        out = {}
        for zone in self.board.Zones():
            if zone.GetNetname() != "GND" or not zone.IsOnLayer(pcb.In1_Cu):
                continue
            fill = zone.GetFilledPolysList(pcb.In1_Cu)
            for via in self.vias["GND"]:
                if not via.IsOnLayer(layer) or not via.IsOnLayer(pcb.In1_Cu):
                    continue
                pos = via.GetPosition()
                for polygon in range(fill.OutlineCount()):
                    if fill.Contains(pos, polygon):
                        out[xy(pos)] = f"{zone.m_Uuid.AsString()}/{polygon}"
                        break
        return out

    def package_lead(self, cap, pin, number):
        """Measure along trace copper between two guaranteed terminal-contact regions.

        The IC metal reaches at least half the minimum 10.11 mm lead span. The 0402
        has 0.45 mm minimum width and a common metallized band from 0.375 to
        0.475 mm from its centre, from Murata's 0.95–1.05 mm length and e >=0.15.
        Accept independent effective terminal registration within +/-0.04 mm on
        each axis, including placement and rotation at each of the eight IC toes.
        """
        part, body = self.parts[cap], self.parts["U11"]
        if (str(part.GetFPID().GetLibItemName()) != "C_0402_1005Metric" or
                str(body.GetFPID().GetLibItemName()) != "ADuM6421A_RN28_Dense"):
            raise ValueError(f"Unexpected package geometry for {cap}")
        mpn = next((f.GetText() for f in part.GetFields() if f.GetName() == "MPN"), None)
        if mpn != "GRM155R71C104KA88D":
            raise ValueError(f"Missing dimensional qualification for {cap}: {mpn}")
        a, c = self.pad("U11", pin), self.pad(cap, number)
        xx, yy = xy(part.GetPosition())
        bx, _ = xy(body.GetPosition())
        sx = 1 if xx > bx else -1
        sy = 1 if c.GetPosition().y > yy else -1
        registration = 0.04
        min_ic_lead_span = 10.11
        min_cap_width = 0.45
        min_cap_length, max_cap_length, min_band = 0.95, 1.05, 0.15
        band_low = max_cap_length / 2 - min_band + registration
        band_high = min_cap_length / 2 - registration
        if band_low > band_high:
            raise ValueError("Specified registration leaves no guaranteed terminal landing")
        start = bx + sx * pcb.FromMM(min_ic_lead_span / 2 - registration), a.GetPosition().y
        # Centre of the surviving 20 micron-wide common lengthwise contact band.
        end = (xx - sx * pcb.FromMM(min_cap_width / 2 - registration),
               yy + sy * pcb.FromMM((band_low + band_high) / 2))
        # A native track endpoint must lie at each physical contact witness point.
        vertices = defaultdict(list)
        for t in self.traces[body.GetLayer(), a.GetNetname()]:
            v, w = xy(t.GetStart()), xy(t.GetEnd())
            vertices[v].append((w, math.dist(v, w)))
            vertices[w].append((v, math.dist(v, w)))
        source = next((v for v in vertices if math.dist(v, start) <= 3), None)
        target = next((v for v in vertices if math.dist(v, end) <= 3), None)
        if source is None or target is None:
            raise ValueError(f"{cap}.{number} lacks a trace endpoint in its guaranteed contact region")
        queue = [(0, source)]
        seen = set()
        while queue:
            distance, v = heappop(queue)
            if v in seen:
                continue
            seen.add(v)
            if v == target:
                return round(distance / 1e6, 6)
            for w, length in vertices[v]:
                if w not in seen:
                    heappush(queue, (distance + length, w))
        raise ValueError(f"{cap}.{number} has no continuous same-face terminal-to-terminal path")

    def measure(self, cap, ref, vpin, gpin):
        supply, ret = self.pad(cap, 1), self.pad(cap, 2)
        layer = self.parts[ref].GetLayer()
        if self.parts[cap].GetLayer() != layer or self.parts[cap].GetValue() != "100nF":
            raise ValueError(f"{cap} must be a local 100 nF capacitor on the IC side")
        if supply.GetNetname() != SUPPLY.get(cap, "+3V3"):
            raise ValueError(f"{cap} connects to the wrong supply domain")
        if ret.GetNetname() != GROUND.get(cap, "GND"):
            raise ValueError(f"{cap} connects to the wrong return domain")
        gnd_pin = self.pad(ref, gpin)
        result = {"ic": ref, "pins": [vpin, gpin], "layer": self.board.GetLayerName(layer),
                  "supply_net": supply.GetNetname(), "return_net": ret.GetNetname(),
                  "supply": self.route(supply, layer, self.pad(ref, vpin))}
        if ref == "U11" or ref == "U21":
            result["return"] = self.route(ret, layer, gnd_pin)
            total = result["supply"]["land_edge_trace_mm"] + result["return"]["land_edge_trace_mm"]
            result["sum_land_edge_trace_mm"] = round(total, 4)
            if ref == "U21":
                result["ic_ground_via"] = self.route(gnd_pin, layer)
            if ref == "U11":
                physical = [self.package_lead(cap, vpin, 1), self.package_lead(cap, gpin, 2)]
                body_to_center = abs(self.parts[cap].GetPosition().x - self.parts[ref].GetPosition().x) / 1e6
                result["min_package_to_package_gap_mm"] = round(body_to_center - 10.51 / 2 - 0.55 / 2 - 2 * 0.04, 4)
                result["package_lead_lengths_mm"] = physical
                result["sum_package_lead_lengths_mm"] = round(sum(physical), 6)
                if sum(physical) > 2 or total > 2:
                    raise ValueError(f"{cap} exceeds the 2 mm bypass layout limit: {result}")
        else:
            result["capacitor_ground_via"] = self.route(ret, layer)
            result["ic_ground_via"] = self.route(gnd_pin, layer)
            if result["capacitor_ground_via"]["plane_island"] != result["ic_ground_via"]["plane_island"]:
                raise ValueError(f"{cap} and {ref} return to different filled ground islands")
            if max(result[k]["land_edge_trace_mm"] for k in ("capacitor_ground_via", "ic_ground_via")) > 2:
                raise ValueError(f"{cap} or {ref} ground via exceeds the 2 mm project target: {result}")
        if ref != "U11" and result["supply"]["land_edge_trace_mm"] > 2:
            raise ValueError(f"{cap} supply trace exceeds the 2 mm project target")
        return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", type=Path, default=MAIN / "pump-controller-compact.kicad_pcb")
    ap.add_argument("--output", type=Path, default=MAIN / "checks/bypass-routing.json")
    args = ap.parse_args()
    board = Board(args.board)
    result = {"board_sha256": hashlib.sha256(args.board.read_bytes()).hexdigest(),
              "kicad_version": pcb.Version(),
              "method": "Land-edge distances follow same-face track centrelines outside endpoint copper. Centre-to-centre figures include the distance through each land to its centre. Ground vias must meet filled In1.Cu copper. Figures exclude barrel length, component-internal leads and assembled parasitics.",
              "adum_criterion": "Both PCB leads together <=2 mm between package terminal witnesses allowing ±0.04 mm effective registration per component on each axis. Verify registration on first articles. ADuM6421A Rev. C pp.29,32 and Murata GRM155R71C104KA88-01 dimensional drawing.",
              "package_sources": [
                  "https://www.analog.com/media/en/technical-documentation/data-sheets/adum6420a-6421a-6422a_6423a_6424a.pdf",
                  "https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71C104KA88-01.pdf",
              ],
              "physical_assembly_verified": False,
              "probe_criterion": "Project placement target <=2 mm exposed supply and local ground-to-plane traces, or a direct return to the IC.",
              "measurements": {}, "failures": []}
    for cap, (ref, vpin, gpin) in {**{k: ("U11", *v) for k, v in ADUM.items()}, **PROBES}.items():
        try:
            result["measurements"][cap] = board.measure(cap, ref, vpin, gpin)
        except ValueError as error:
            result["failures"].append(str(error))
    result["passed"] = not result["failures"]
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for failure in result["failures"]:
        print(failure)
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
