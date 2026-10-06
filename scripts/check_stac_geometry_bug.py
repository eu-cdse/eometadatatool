#!/usr/bin/env python3
r"""Scan generated STAC item NDJSONs for the "complemented near-global bbox" bug.

Background
----------
A near-global CLMS extent (e.g. ``globe_80s80n``: lon -180..180, lat -80..80)
covers ~89% of the globe. The geometry normaliser used to misclassify any
polygon larger than ~half the Earth as an *inverted* orbital footprint and take
its complement against the world box. The intended solid band therefore came
out as a thin **frame**: two polar-cap strips plus an antimeridian sliver,
hugging the bounding box with a huge *empty interior*.

This script samples a few items from each NDJSON file and flags items whose
geometry shows that signature: a large bounding box that the geometry barely
fills, with an empty centre.

Detection (no third-party deps — pure stdlib)
---------------------------------------------
For each sampled item, using its declared ``bbox`` as the rectangle the
geometry is *expected* to fill (falling back to the geometry's own bounds):

  * coverage          = geometry_area / bbox_area
  * interior_coverage = fraction of a grid of points inside ``bbox`` that fall
                        inside the geometry

  * interior_vtx_frac  = fraction of geometry vertices that sit deep inside the
                        bbox (more than ``edge_inset`` of the way from any edge)

A healthy rectangular product has coverage ~1.0. A real orbital swath (S3/S5P/
S6) also barely fills its near-global bbox, but its boundary crosses the
interior, so interior_vtx_frac is high (~0.6-0.9). The bug's "frame" hugs the
bbox border on all sides: coverage ~0.0001 *and* interior_vtx_frac ~0.0.

An item is flagged only when the bbox is large AND coverage is tiny AND the
interior is empty AND essentially all vertices hug the bbox border — the last
gate is what distinguishes the bug from legitimate thin orbital footprints.
Thresholds are CLI-configurable; every metric is printed so borderline cases
can be judged by a human.

The geometry maths (shoelace area, ray-cast point-in-polygon with holes) is
implemented inline so the script is fully self-contained and portable.

Usage
-----
    python3 check_stac_geometry_bug.py PATH [PATH ...]
    python3 check_stac_geometry_bug.py /data/stac/*.ndjson --sample 10
    python3 check_stac_geometry_bug.py /data/stac --json report.json
    python3 check_stac_geometry_bug.py --selftest

    # Windows (cmd/PowerShell do not expand wildcards — quote the glob):
    python check_stac_geometry_bug.py "F:\clms-gen\*.json.1"
    python check_stac_geometry_bug.py F:\clms-gen --pattern "*.json.1"

PATHs may be NDJSON files, directories, or shell-style globs. Globs are expanded
by the script itself (so they work on Windows too) and every match is read
regardless of extension. Plain file paths are also read regardless of extension.
Directories are scanned recursively for known extensions (``.ndjson``,
``.ndjson.gz``, ``.jsonl``, ``.jsonl.gz``, ``.json``, ``.json.gz``) unless you
pass ``--pattern``. Files ending in ``.gz`` are transparently decompressed.

Exit code is 1 if any suspect item is found, 0 otherwise (2 on usage error),
so it can gate a CI / validation pipeline.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

# ----------------------------------------------------------------------------
# Geometry primitives (pure Python, GeoJSON [lon, lat] coordinate order)
# ----------------------------------------------------------------------------

Ring = list[tuple[float, float]]
# A polygon is (exterior_ring, [hole_ring, ...]); coords are (lon, lat).
PolyRings = tuple[Ring, list[Ring]]


def _ring_signed_area(ring: Ring) -> float:
    """Signed planar area of a ring via the shoelace formula (degrees²)."""
    n = len(ring)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area / 2.0


def _polygon_area(poly: PolyRings) -> float:
    """Absolute area of a polygon: exterior minus holes."""
    exterior, holes = poly
    area = abs(_ring_signed_area(exterior))
    for hole in holes:
        area -= abs(_ring_signed_area(hole))
    return max(area, 0.0)


def _point_in_ring(x: float, y: float, ring: Ring) -> bool:
    """Ray-casting point-in-ring test (boundary result is unspecified)."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def _point_in_polygon(x: float, y: float, poly: PolyRings) -> bool:
    exterior, holes = poly
    if not _point_in_ring(x, y, exterior):
        return False
    return not any(_point_in_ring(x, y, hole) for hole in holes)


def _iter_polygons(geometry: dict[str, Any]) -> Iterator[PolyRings]:
    """Yield (exterior, holes) for each polygon in a GeoJSON geometry.

    Supports Polygon, MultiPolygon, and GeometryCollection of those.
    """
    if not isinstance(geometry, dict):
        return
    gtype = geometry.get('type')
    coords = geometry.get('coordinates')
    if gtype == 'Polygon' and coords:
        rings = [[(float(p[0]), float(p[1])) for p in ring] for ring in coords]
        if rings:
            yield rings[0], rings[1:]
    elif gtype == 'MultiPolygon' and coords:
        for poly in coords:
            rings = [[(float(p[0]), float(p[1])) for p in ring] for ring in poly]
            if rings:
                yield rings[0], rings[1:]
    elif gtype == 'GeometryCollection':
        for sub in geometry.get('geometries', []) or []:
            yield from _iter_polygons(sub)


def _all_coords(polys: list[PolyRings]) -> Iterator[tuple[float, float]]:
    for exterior, holes in polys:
        yield from exterior
        for hole in holes:
            yield from hole


# ----------------------------------------------------------------------------
# Bug detection
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Thresholds:
    """Tunable detection thresholds."""

    min_bbox_area: float = 30000.0  # deg²; ~half the globe (360*180/2 = 32400)
    max_coverage: float = 0.10  # geometry must fill <10% of bbox to be suspect
    max_interior_coverage: float = 0.20  # <20% of interior sample points inside
    max_interior_vtx_frac: float = 0.10  # <10% of vertices off the bbox border
    edge_inset: float = 0.02  # a vertex is "interior" if >2% of bbox from any edge
    grid: int = 7  # NxN interior sampling grid


@dataclass
class ItemResult:
    is_suspect: bool
    reason: str
    bbox: tuple[float, float, float, float] | None
    bbox_area: float
    geom_area: float
    coverage: float
    interior_coverage: float
    interior_vtx_frac: float
    geom_type: str | None
    num_polygons: int


def _bbox_of(polys: list[PolyRings]) -> tuple[float, float, float, float] | None:
    xs_ys = list(_all_coords(polys))
    if not xs_ys:
        return None
    xs = [c[0] for c in xs_ys]
    ys = [c[1] for c in xs_ys]
    return (min(xs), min(ys), max(xs), max(ys))


def analyze_item(item: dict[str, Any], th: Thresholds) -> ItemResult:
    """Classify a single STAC item dict."""
    geometry = item.get('geometry')
    polys = list(_iter_polygons(geometry)) if isinstance(geometry, dict) else []
    geom_type = geometry.get('type') if isinstance(geometry, dict) else None

    if not polys:
        return ItemResult(
            is_suspect=False,
            reason='no polygonal geometry',
            bbox=None,
            bbox_area=0.0,
            geom_area=0.0,
            coverage=0.0,
            interior_coverage=0.0,
            interior_vtx_frac=0.0,
            geom_type=geom_type,
            num_polygons=0,
        )

    # Reference rectangle the geometry is expected to fill: the declared bbox
    # (the "expected geometry" for these rectangular products) when present and
    # 2D, otherwise the geometry's own bounds.
    declared = item.get('bbox')
    ref: tuple[float, float, float, float] | None = None
    if isinstance(declared, (list, tuple)) and len(declared) >= 4:
        try:
            vals = [float(v) for v in declared]
        except (TypeError, ValueError):
            vals = []
        if len(vals) == 6:  # 3D bbox: [w, s, minz, e, n, maxz]
            ref = (vals[0], vals[1], vals[3], vals[4])
        elif len(vals) >= 4:
            ref = (vals[0], vals[1], vals[2], vals[3])
    if ref is None:
        ref = _bbox_of(polys)

    assert ref is not None
    minx, miny, maxx, maxy = ref
    bbox_w = maxx - minx
    bbox_h = maxy - miny
    bbox_area = bbox_w * bbox_h
    geom_area = sum(_polygon_area(p) for p in polys)
    coverage = geom_area / bbox_area if bbox_area > 0 else 0.0

    # Sample a grid of points strictly inside the reference bbox.
    inside = 0
    total = 0
    g = max(th.grid, 2)
    for i in range(1, g + 1):
        for j in range(1, g + 1):
            px = minx + bbox_w * i / (g + 1)
            py = miny + bbox_h * j / (g + 1)
            total += 1
            if any(_point_in_polygon(px, py, p) for p in polys):
                inside += 1
    interior_coverage = inside / total if total else 0.0

    # Fraction of vertices that sit *off* the bbox border (deep in the interior).
    # The bug's frame hugs the border (~0.0); a real orbital swath crosses the
    # interior (~0.6-0.9), which is what lets us tell them apart.
    verts = list(_all_coords(polys))
    interior_vtx = 0
    for x, y in verts:
        dx = min(x - minx, maxx - x) / bbox_w if bbox_w > 0 else 0.0
        dy = min(y - miny, maxy - y) / bbox_h if bbox_h > 0 else 0.0
        if min(dx, dy) > th.edge_inset:
            interior_vtx += 1
    interior_vtx_frac = interior_vtx / len(verts) if verts else 0.0

    is_suspect = (
        bbox_area >= th.min_bbox_area
        and coverage < th.max_coverage
        and interior_coverage < th.max_interior_coverage
        and interior_vtx_frac < th.max_interior_vtx_frac
    )
    if is_suspect:
        reason = (
            f'large bbox ({bbox_area:.0f} deg²) barely filled '
            f'(coverage={coverage:.4%}, interior={interior_coverage:.0%}) '
            f'with all vertices on the border (interior_vtx={interior_vtx_frac:.0%}) '
            f'-> looks like a complemented "frame"'
        )
    else:
        reason = 'ok'

    return ItemResult(
        is_suspect=is_suspect,
        reason=reason,
        bbox=ref,
        bbox_area=bbox_area,
        geom_area=geom_area,
        coverage=coverage,
        interior_coverage=interior_coverage,
        interior_vtx_frac=interior_vtx_frac,
        geom_type=geom_type,
        num_polygons=len(polys),
    )


# ----------------------------------------------------------------------------
# File handling & sampling
# ----------------------------------------------------------------------------


def _open_text(path: Path):
    if path.suffix == '.gz' or path.name.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, encoding='utf-8')


def sample_lines(path: Path, k: int, rng: random.Random) -> list[tuple[int, str]]:
    """Reservoir-sample up to ``k`` lines (uniformly) in a single streaming pass.

    Returns (line_number, raw_line) pairs, sorted by line number. O(k) memory,
    so it copes with the 10000-item files without loading them whole.
    """
    reservoir: list[tuple[int, str]] = []
    with _open_text(path) as fh:
        for lineno, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            if len(reservoir) < k:
                reservoir.append((lineno, line))
            else:
                r = rng.randint(0, lineno)
                if r < k:
                    reservoir[r] = (lineno, line)
    reservoir.sort(key=lambda t: t[0])
    return reservoir


_DEFAULT_EXTS = ('.ndjson', '.ndjson.gz', '.jsonl', '.jsonl.gz', '.json', '.json.gz')
_GLOB_CHARS = ('*', '?', '[')


def discover_files(paths: list[str], pattern: str | None = None) -> list[Path]:
    """Resolve CLI path arguments into a list of files.

    Handles three forms, so it behaves the same on Windows (cmd/PowerShell,
    which do NOT expand wildcards) as on a Unix shell:

      * an explicit glob (``F:\\clms-gen\\*.json.1``) -> expanded here; every
        match is trusted regardless of extension.
      * a directory -> scanned recursively for ``pattern`` (default: known
        NDJSON/JSON extensions).
      * a plain file path -> used as-is, regardless of extension.
    """
    found: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        key = str(p)
        if key not in seen:
            seen.add(key)
            found.append(p)

    for raw in paths:
        # 1. Explicit shell-style glob (Windows shells leave these unexpanded).
        if any(ch in raw for ch in _GLOB_CHARS):
            matches = [Path(m) for m in glob.glob(raw, recursive=True)]
            file_matches = [m for m in matches if m.is_file()]
            if not file_matches:
                print(f'WARNING: glob matched no files: {raw}', file=sys.stderr)
            for m in sorted(file_matches):
                add(m)
            continue

        p = Path(raw)
        # 2. Directory: scan recursively.
        if p.is_dir():
            if pattern:
                children = p.rglob(pattern)
            else:
                children = (
                    c for c in p.rglob('*')
                    if c.name.endswith(_DEFAULT_EXTS)
                )
            for child in sorted(children):
                if child.is_file():
                    add(child)
        # 3. Plain file: trust it regardless of extension.
        elif p.is_file():
            add(p)
        else:
            print(f'WARNING: path not found: {p}', file=sys.stderr)
    return found


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------


@dataclass
class Suspect:
    file: str
    line: int
    item_id: str | None
    collection: str | None
    result: ItemResult


@dataclass
class FileReport:
    path: str
    sampled: int = 0
    parse_errors: int = 0
    suspects: list[Suspect] = field(default_factory=list)


def scan_file(path: Path, k: int, th: Thresholds, rng: random.Random) -> FileReport:
    report = FileReport(path=str(path))
    try:
        lines = sample_lines(path, k, rng)
    except OSError as e:
        print(f'ERROR reading {path}: {e}', file=sys.stderr)
        return report

    for lineno, raw in lines:
        report.sampled += 1
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            report.parse_errors += 1
            continue
        if not isinstance(item, dict):
            report.parse_errors += 1
            continue
        res = analyze_item(item, th)
        if res.is_suspect:
            report.suspects.append(
                Suspect(
                    file=str(path),
                    line=lineno,
                    item_id=item.get('id'),
                    collection=item.get('collection'),
                    result=res,
                )
            )
    return report


def print_report(reports: list[FileReport], th: Thresholds) -> int:
    total_files = len(reports)
    total_sampled = sum(r.sampled for r in reports)
    total_errors = sum(r.parse_errors for r in reports)
    suspect_items = [s for r in reports for s in r.suspects]
    files_with_suspects = [r for r in reports if r.suspects]

    print('=' * 78)
    print('STAC geometry-bug scan (complemented near-global bbox -> "frame")')
    print('=' * 78)
    print(f'Files scanned        : {total_files}')
    print(f'Items sampled        : {total_sampled}')
    print(f'Parse/skip errors    : {total_errors}')
    print(
        'Thresholds           : '
        f'bbox_area>={th.min_bbox_area:g}, coverage<{th.max_coverage:g}, '
        f'interior<{th.max_interior_coverage:g}, interior_vtx<{th.max_interior_vtx_frac:g}'
    )
    print(f'Suspect items        : {len(suspect_items)}')
    print(f'Files with suspects  : {len(files_with_suspects)}')
    print('-' * 78)

    if not suspect_items:
        print('No items matching the bug signature were found in the sample.')
        return 0

    for r in files_with_suspects:
        print(f'\nFILE: {r.path}  ({len(r.suspects)}/{r.sampled} sampled flagged)')
        for s in r.suspects:
            res = s.result
            bbox = (
                '[' + ', '.join(f'{v:.4f}' for v in res.bbox) + ']'
                if res.bbox
                else 'n/a'
            )
            print(f'  line {s.line}: id={s.item_id!r} collection={s.collection!r}')
            print(f'      geom={res.geom_type} parts={res.num_polygons} bbox={bbox}')
            print(
                f'      bbox_area={res.bbox_area:.1f} geom_area={res.geom_area:.4f} '
                f'coverage={res.coverage:.4%} interior_coverage={res.interior_coverage:.0%} '
                f'interior_vtx_frac={res.interior_vtx_frac:.0%}'
            )
            print(f'      -> {res.reason}')

    print('\n' + '=' * 78)
    print(f'RESULT: {len(suspect_items)} suspect item(s) found — investigate above.')
    print('=' * 78)
    return 1


def write_json(reports: list[FileReport], out: Path) -> None:
    payload = {
        'files_scanned': len(reports),
        'items_sampled': sum(r.sampled for r in reports),
        'suspect_count': sum(len(r.suspects) for r in reports),
        'files': [
            {
                'path': r.path,
                'sampled': r.sampled,
                'parse_errors': r.parse_errors,
                'suspects': [
                    {
                        'line': s.line,
                        'id': s.item_id,
                        'collection': s.collection,
                        'bbox': list(s.result.bbox) if s.result.bbox else None,
                        'bbox_area': s.result.bbox_area,
                        'geom_area': s.result.geom_area,
                        'coverage': s.result.coverage,
                        'interior_coverage': s.result.interior_coverage,
                        'interior_vtx_frac': s.result.interior_vtx_frac,
                        'geom_type': s.result.geom_type,
                        'num_polygons': s.result.num_polygons,
                        'reason': s.result.reason,
                    }
                    for s in r.suspects
                ],
            }
            for r in reports
        ],
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f'\nJSON report written to {out}')


# ----------------------------------------------------------------------------
# Self-test (validates the detector without needing real data)
# ----------------------------------------------------------------------------


def _selftest() -> int:
    th = Thresholds()

    # 1. Healthy near-global rectangle (globe_80s80n) — must NOT be flagged.
    healthy = {
        'id': 'healthy',
        'bbox': [-180.0, -79.9776824, 179.9776872, 80.0223214],
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-180.0, 80.0223214], [-0.0111564, 80.0223214],
                [179.9776872, 80.0223214], [179.9776872, -79.9776824],
                [-0.0111564, -79.9776824], [-180.0, -79.9776824],
                [-180.0, 80.0223214],
            ]],
        },
    }

    # 2. The bug: complement "frame" as a Polygon with a near-full-bbox hole.
    frame_hole = {
        'id': 'frame_hole',
        'bbox': [-180.0, -79.9776824, 179.9776872, 80.0223214],
        'geometry': {
            'type': 'Polygon',
            'coordinates': [
                [  # outer = full bbox
                    [-180.0, -79.9776824], [179.9776872, -79.9776824],
                    [179.9776872, 80.0223214], [-180.0, 80.0223214],
                    [-180.0, -79.9776824],
                ],
                [  # hole = almost the whole interior (the erased band)
                    [-179.9, -79.9], [179.9, -79.9],
                    [179.9, 79.9], [-179.9, 79.9], [-179.9, -79.9],
                ],
            ],
        },
    }

    # 3. The bug: thin-strip MultiPolygon frame (matches observed output).
    frame_strips = {
        'id': 'frame_strips',
        'bbox': [-180.0, -79.9776824, 179.9776872, 80.0223214],
        'geometry': {
            'type': 'MultiPolygon',
            'coordinates': [
                [[[-180, 80.021], [180, 80.021], [180, 80.022], [-180, 80.022], [-180, 80.021]]],
                [[[-180, -79.978], [180, -79.978], [180, -79.977], [-180, -79.977], [-180, -79.978]]],
            ],
        },
    }

    # 4. Legitimate small regional rectangle (eu extent) — must NOT be flagged.
    regional = {
        'id': 'regional',
        'bbox': [-11.0, 35.0, 50.0, 72.0],
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-11.0, 72.0], [50.0, 72.0], [50.0, 35.0],
                [-11.0, 35.0], [-11.0, 72.0],
            ]],
        },
    }

    # 5. Legitimate orbital swath: near-global bbox, thin diagonal footprint that
    #    crosses the interior (many off-border vertices). Must NOT be flagged.
    swath_coords = [
        [-180.0, 10.0], [-150.0, 40.0], [-120.0, 65.0], [-90.0, 80.0],
        [-60.0, 65.0], [-30.0, 40.0], [0.0, 10.0], [30.0, -20.0],
        [60.0, -45.0], [90.0, -60.0], [120.0, -45.0], [150.0, -20.0],
        [180.0, 10.0], [180.0, 12.0], [150.0, -18.0], [120.0, -43.0],
        [90.0, -58.0], [60.0, -43.0], [30.0, -18.0], [0.0, 12.0],
        [-30.0, 42.0], [-60.0, 67.0], [-90.0, 82.0], [-120.0, 67.0],
        [-150.0, 42.0], [-180.0, 12.0], [-180.0, 10.0],
    ]
    swath = {
        'id': 'orbital_swath',
        'bbox': [-180.0, -60.0, 180.0, 82.0],
        'geometry': {'type': 'Polygon', 'coordinates': [swath_coords]},
    }

    cases = [
        ('healthy near-global rectangle', healthy, False),
        ('bug: frame as polygon-with-hole', frame_hole, True),
        ('bug: frame as thin strips', frame_strips, True),
        ('legitimate regional rectangle', regional, False),
        ('legitimate orbital swath', swath, False),
    ]

    ok = True
    print('Self-test:')
    for name, item, expected in cases:
        res = analyze_item(item, th)
        status = 'PASS' if res.is_suspect == expected else 'FAIL'
        if res.is_suspect != expected:
            ok = False
        print(
            f'  [{status}] {name:38s} '
            f'suspect={res.is_suspect!s:5s} (expected {expected!s:5s}) '
            f'coverage={res.coverage:.4%} interior={res.interior_coverage:.0%} '
            f'interior_vtx={res.interior_vtx_frac:.0%}'
        )
    print('Self-test:', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Scan STAC item NDJSONs for the complemented-bbox geometry bug.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('paths', nargs='*',
                        help='NDJSON files, directories, or globs '
                             '(globs are expanded by the script, so quote them '
                             'on Windows, e.g. "F:\\clms-gen\\*.json.1")')
    parser.add_argument('--pattern', default=None,
                        help='when a directory is given, only scan files matching '
                             'this glob (e.g. "*.json.1"); default: known extensions')
    parser.add_argument('-n', '--sample', type=int, default=5,
                        help='items to sample per file')
    parser.add_argument('--seed', type=int, default=1234,
                        help='RNG seed for reproducible sampling')
    parser.add_argument('--min-bbox-area', type=float, default=Thresholds.min_bbox_area,
                        help='only flag items whose bbox is at least this many deg²')
    parser.add_argument('--max-coverage', type=float, default=Thresholds.max_coverage,
                        help='flag when geometry fills less than this fraction of bbox')
    parser.add_argument('--max-interior', type=float, default=Thresholds.max_interior_coverage,
                        help='flag when fewer than this fraction of interior points are inside')
    parser.add_argument('--max-interior-vtx', type=float, default=Thresholds.max_interior_vtx_frac,
                        help='flag only when fewer than this fraction of vertices are off the bbox border')
    parser.add_argument('--grid', type=int, default=Thresholds.grid,
                        help='interior sampling grid size (NxN)')
    parser.add_argument('--json', type=Path, default=None,
                        help='also write a JSON report to this path')
    parser.add_argument('--selftest', action='store_true',
                        help='run built-in detector self-test and exit')
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.paths:
        parser.error('no paths given (or use --selftest)')

    th = Thresholds(
        min_bbox_area=args.min_bbox_area,
        max_coverage=args.max_coverage,
        max_interior_coverage=args.max_interior,
        max_interior_vtx_frac=args.max_interior_vtx,
        grid=args.grid,
    )

    files = discover_files(args.paths, pattern=args.pattern)
    if not files:
        print('No matching files found.', file=sys.stderr)
        return 2

    rng = random.Random(args.seed)
    reports = [scan_file(f, args.sample, th, rng) for f in files]

    exit_code = print_report(reports, th)
    if args.json:
        write_json(reports, args.json)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
