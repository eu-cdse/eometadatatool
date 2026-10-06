"""Coverage checks against an independent spherical reference.

``normalize_geometry`` represents a footprint in plate-carree lon/lat, where the
antimeridian is a seam and the poles are lines rather than points. Golden-master
snapshots pin what the code currently produces; these tests instead pin what it
*should* produce, by rebuilding the footprint in a projection that has no seam
anywhere near the region under test:

1. densify the source ring along great circles, so each edge follows the real
   ground track instead of a straight lon/lat line;
2. project to south-polar stereographic, which is one-to-one on the sphere
   minus the North Pole - no antimeridian, and the South Pole is an ordinary
   interior point;
3. test grid membership there.

Any disagreement is then a property of our lon/lat handling, not of the source.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from pyproj import CRS, Transformer
from shapely import (
    Polygon,
    contains_xy,
    from_wkt,
    get_coordinates,
    make_valid,
    prepare,
)

from eometadatatool.geometry.normalize import normalize_geometry

if TYPE_CHECKING:
    from numpy.typing import NDArray

FIXTURE_DIR = Path(__file__).resolve().parents[1] / 'fixtures' / 'geometry'

# Probe points for deciding which side of the ring is the footprint. Stereographic
# projection from the South Pole sends the North Pole to infinity, so the projected
# polygon's interior is whichever side excludes the North Pole - which side that is
# depends on the footprint. Each probe below is justified directly by source
# vertices of full_orbit_equator_split.wkt:
#   (-80, -30) inside : the ring crosses lat -30 at lon -95.47 and lon -66.23
#   (-100, -30) outside: west of that western edge
#   (120, 0) outside  : at the equator the ring sits near lon -100.8 and -75.8
_FULL_ORBIT_INSIDE = ((-80.0, -30.0),)
_FULL_ORBIT_OUTSIDE = ((-100.0, -30.0), (120.0, 0.0))

_SOUTH_POLAR = CRS.from_proj4(
    '+proj=stere +lat_0=-90 +lon_0=0 +R=6371000 +units=m +no_defs'
)
_DENSIFY = 200


def _reference_footprint(ring: NDArray) -> tuple[Polygon, Transformer]:
    """Project the ring to south-polar stereographic, densified along great circles."""
    lon, lat = np.radians(ring[:, 0]), np.radians(ring[:, 1])
    xyz = np.column_stack([
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ])
    steps = np.linspace(0, 1, _DENSIFY, endpoint=False)[:, None]
    dense = np.vstack([
        a * (1 - steps) + b * steps
        for a, b in zip(xyz, np.roll(xyz, -1, axis=0), strict=True)
    ])
    dense /= np.linalg.norm(dense, axis=1, keepdims=True)

    transformer = Transformer.from_crs(
        CRS.from_epsg(4326), _SOUTH_POLAR, always_xy=True
    )
    x, y = transformer.transform(
        np.degrees(np.arctan2(dense[:, 1], dense[:, 0])),
        np.degrees(np.arcsin(dense[:, 2])),
    )
    # A swath outline may graze itself near a pole; repair rather than reject.
    reference = make_valid(
        Polygon(np.column_stack([x, y])), method='structure', keep_collapsed=False
    )
    prepare(reference)
    return reference, transformer  # type: ignore[return-value]


def _truth_mask(
    ring: NDArray,
    lons: NDArray,
    lats: NDArray,
    *,
    known_inside: tuple[tuple[float, float], ...],
    known_outside: tuple[tuple[float, float], ...],
) -> NDArray:
    reference, transformer = _reference_footprint(ring)

    def projected_inside(pts) -> NDArray:
        px, py = transformer.transform([p[0] for p in pts], [p[1] for p in pts])
        return contains_xy(reference, np.asarray(px), np.asarray(py))

    inside_hits = projected_inside(known_inside)
    outside_hits = projected_inside(known_outside)
    if inside_hits.all() and not outside_hits.any():
        invert = False
    elif not inside_hits.any() and outside_hits.all():
        invert = True
    else:
        pytest.fail(
            'reference polarity is ambiguous: the probe points disagree, so the '
            'fixture or the probes are wrong'
        )

    px, py = transformer.transform(lons, lats)
    mask = contains_xy(reference, px, py)
    return ~mask if invert else mask


def _coverage_error(
    wkt: str,
    *,
    known_inside: tuple[tuple[float, float], ...],
    known_outside: tuple[tuple[float, float], ...],
) -> tuple[float, float]:
    """Return (spurious, missing) as a share of the true footprint area."""
    source = from_wkt(wkt)
    assert isinstance(source, Polygon)

    # Denser sampling near the poles, where lon/lat handling is hardest.
    grid_lon = np.arange(-179.5, 180, 1.0)
    grid_lat = np.concatenate([
        np.arange(-89.9, -85, 0.1),
        np.arange(-85, 85, 1.0),
        np.arange(85, 89.95, 0.1),
    ])
    mesh_lon, mesh_lat = np.meshgrid(grid_lon, grid_lat)
    lons, lats = mesh_lon.ravel(), mesh_lat.ravel()

    truth = _truth_mask(
        get_coordinates(source)[:-1],
        lons,
        lats,
        known_inside=known_inside,
        known_outside=known_outside,
    )

    normalized = normalize_geometry(source)
    prepare(normalized)
    ours = contains_xy(normalized, lons, lats)

    weight = np.cos(np.radians(lats))  # cell area shrinks toward the poles
    total = weight[truth].sum()
    return (
        weight[ours & ~truth].sum() / total,
        weight[truth & ~ours].sum() / total,
    )


def test_full_orbit_footprint_matches_spherical_reference() -> None:
    wkt = (FIXTURE_DIR / 'full_orbit_equator_split.wkt').read_text().strip()
    spurious, missing = _coverage_error(
        wkt,
        known_inside=_FULL_ORBIT_INSIDE,
        known_outside=_FULL_ORBIT_OUTSIDE,
    )

    # Routing every crossing over one pole used to lose the whole North polar
    # cap (missing 6.18%) and over-fill the South cap.
    assert missing < 0.001, f'{missing:.2%} of the footprint is missing'
    # The remainder is the South cap wedge left by interpolating a near-pole
    # segment linearly in lon/lat instead of along its great circle.
    assert spurious < 0.01, f'{spurious:.2%} of the footprint is invented'
