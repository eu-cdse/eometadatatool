#!/usr/bin/env python3
"""Check STAC item geometries against the sfeos topology validator rules.

Re-implements sfeos validate_item_topology_lightweight
(cf_sfeos_fork/sfeos/stac_fastapi/core/validate.py):
- all coordinates within WGS84 bounds (+/-180 lon, +/-90 lat)
- Polygon/MultiPolygon rings: >= 4 and <= MAX_TOPOLOGY_VERTICES (5000) vertices
- no two consecutive ring vertices with abs(lon2 - lon1) > 180

Usage: uv run python scripts/check_antimeridian_rings.py DIR_OR_FILE [...]
"""

import json
import sys
from itertools import pairwise
from pathlib import Path

MAX_TOPOLOGY_VERTICES = 5000


def iter_rings(geometry: dict):
    gtype = geometry['type']
    coords = geometry['coordinates']
    if gtype == 'Polygon':
        yield from coords
    elif gtype == 'MultiPolygon':
        for poly in coords:
            yield from poly


def max_lon_jump(geometry: dict) -> float:
    worst = 0.0
    for ring in iter_rings(geometry):
        for (lon1, *_), (lon2, *_) in pairwise(ring):
            worst = max(worst, abs(lon2 - lon1))
    return worst


def sfeos_errors(geometry: dict) -> list[str]:
    """All violations of the sfeos lightweight topology validation."""
    errors: list[str] = []
    for ring in iter_rings(geometry):
        if len(ring) < 4:
            errors.append(f'ring has {len(ring)} < 4 coordinates')
        if len(ring) > MAX_TOPOLOGY_VERTICES:
            errors.append(f'ring has {len(ring)} > {MAX_TOPOLOGY_VERTICES} vertices')
        for (lon1, lat1, *_), (lon2, lat2, *_) in pairwise(ring):
            for lon, lat in ((lon1, lat1), (lon2, lat2)):
                if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                    errors.append(f'out of WGS84 bounds: [{lon}, {lat}]')
            if abs(lon1 - lon2) > 180:
                errors.append(f'antimeridian jump between longitude {lon1} and {lon2}')
    return errors


def main() -> int:
    paths: list[Path] = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(p.rglob('*.json')))
        else:
            paths.append(p)

    bad = 0
    total = 0
    for path in paths:
        data = json.loads(path.read_text())
        geom = data.get('geometry')
        if not geom:
            continue
        total += 1
        jump = max_lon_jump(geom)
        errors = sfeos_errors(geom)
        status = 'FAIL' if errors else 'ok'
        if errors:
            bad += 1
        print(f'{status:4} max_jump={jump:12.7f} {path.name}')
        for error in errors:
            print(f'     - {error}')

    print(f'\n{bad}/{total} items violate the sfeos topology rules')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
