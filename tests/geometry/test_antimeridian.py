from pathlib import Path

import numpy as np
import pytest
from shapely import MultiPolygon, Polygon, from_wkt, get_coordinates, is_valid

from eometadatatool.geometry.antimeridian import (
    _count_antimeridian_crossings,
    _detect_antimeridian_crossings,
    _fix_inverted_polygon,
    _has_dual_pole_routing,
    _insert_pole_points_at_crossings,
    _is_simple_rectangle,
    _rework_antimeridian_polygon,
    _split_at_antimeridian,
    _split_pole_routed_polygon,
    _split_polygon_at_equator,
    check_contains_pole,
    densify_pole_bridges,
    lat_cross_antimeridian,
    lon_cross_equator,
)
from eometadatatool.geometry.constants import (
    EPSILON,
    HALF_EARTH_THRESHOLD,
    LAT_MAX,
    LON_MAX,
)
from eometadatatool.geometry.normalize import normalize_geometry
from eometadatatool.stac.clms.template.const import bbox_to_wkt

FIXTURE_DIR = Path(__file__).resolve().parents[1] / 'fixtures' / 'geometry'

# Full-orbit swath (326 vertices, pole to pole, 4 antimeridian crossings in both
# hemispheres) that made _rework_antimeridian_polygon recurse forever: its
# equator split returns the input unchanged.
_FULL_ORBIT_WKT = (FIXTURE_DIR / 'full_orbit_equator_split.wkt').read_text().strip()


def test_check_contains_pole_north() -> None:
    geom = Polygon([
        (-180, 80),
        (-90, 80),
        (0, 80),
        (90, 80),
        (180, 80),
        (0, 90),
        (-180, 80),
    ])
    assert check_contains_pole(geom) == 'north'


def test_check_contains_pole_south() -> None:
    geom = Polygon([
        (-180, -80),
        (-90, -80),
        (0, -80),
        (90, -80),
        (180, -80),
        (0, -90),
        (-180, -80),
    ])
    assert check_contains_pole(geom) == 'south'


def test_check_contains_pole_none() -> None:
    geom = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    assert check_contains_pole(geom) is None


def test_lat_cross_antimeridian_interpolates() -> None:
    p1 = np.array([170, 50])
    p2 = np.array([-170, 70])
    lat = lat_cross_antimeridian(p1, p2)
    assert lat == pytest.approx(60, abs=0.01)


def test_lon_cross_equator_interpolates() -> None:
    p1 = np.array([100, 30])
    p2 = np.array([110, -30])
    lon = lon_cross_equator(p1, p2)
    assert lon == pytest.approx(105, abs=0.01)


def test_count_antimeridian_crossings_mixed_hemispheres() -> None:
    coords = np.array([
        [170, 50],
        [-170, 30],
        [-170, -30],
        [170, -50],
        [170, 50],
    ])
    count, mixed, latitudes = _count_antimeridian_crossings(coords)
    assert count >= 2
    assert mixed is True
    assert any(lat > 0 for lat in latitudes)
    assert any(lat < 0 for lat in latitudes)


def test_detect_antimeridian_crossings_s5p_like_polygon() -> None:
    coords = np.array([
        [170, 60],
        [175, 61],
        [-175, 62],
        [-170, 63],
        [-165, 64],
        [-170, 63],
        [-175, 62],
        [175, 61],
        [170, 60],
    ])
    crossings = _detect_antimeridian_crossings(coords)
    assert len(crossings) == 2


def test_insert_pole_points_uses_limits() -> None:
    coords = np.array(
        [
            [170.0, 60.0],
            [-170.0, 60.0],
            [-170.0, 70.0],
            [170.0, 70.0],
            [170.0, 60.0],
        ],
        dtype=np.float64,
    )
    crossings = _detect_antimeridian_crossings(coords)
    result = _insert_pole_points_at_crossings(coords, crossings)

    assert len(result) == len(coords) + len(crossings) * 4
    assert np.any(np.isclose(np.abs(result[:, 0]), LON_MAX))
    assert np.any(np.isclose(np.abs(result[:, 1]), LAT_MAX))


def test_split_at_antimeridian_removes_pole_points() -> None:
    coords = [
        (170, 50),
        (LON_MAX, 55),
        (LON_MAX, LAT_MAX),
        (-LON_MAX, LAT_MAX),
        (-LON_MAX, 55),
        (-170, 60),
        (-170, 50),
        (-LON_MAX, 45),
        (-LON_MAX, LAT_MAX),
        (LON_MAX, LAT_MAX),
        (LON_MAX, 45),
        (170, 50),
    ]
    result = _split_at_antimeridian(Polygon(coords))

    if isinstance(result, MultiPolygon):
        all_coords = np.vstack([get_coordinates(p) for p in result.geoms])
    else:
        all_coords = get_coordinates(result)

    for coord in all_coords:
        is_pole_point = (
            abs(abs(coord[1]) - LAT_MAX) < EPSILON
            and abs(abs(coord[0]) - LON_MAX) < EPSILON
        )
        assert not is_pole_point


def test_split_polygon_at_equator_for_crossing() -> None:
    geom = Polygon([(10, 30), (20, 30), (20, -30), (10, -30), (10, 30)])
    result = _split_polygon_at_equator(geom)
    assert len(result) >= 2


def test_rework_antimeridian_polygon_crossing_is_valid() -> None:
    geom = Polygon([(170, 50), (-170, 50), (-170, 60), (170, 60), (170, 50)])
    result = _rework_antimeridian_polygon(geom)
    assert isinstance(result, Polygon | MultiPolygon)
    assert is_valid(result) or is_valid(result.buffer(0))


def test_fix_inverted_polygon_takes_complement() -> None:
    inverted_coords = [
        (-179.99, 89.99),
        (-179.99, -70),
        (-150, -70),
        (-120, -60),
        (-90, -50),
        (-60, -60),
        (-30, -70),
        (0, -80),
        (30, -70),
        (60, -60),
        (90, -50),
        (120, -60),
        (150, -70),
        (179.99, -70),
        (179.99, 89.99),
        (-179.99, 89.99),
    ]
    geom = Polygon(inverted_coords)
    assert geom.area > HALF_EARTH_THRESHOLD

    fixed = _fix_inverted_polygon(geom)
    assert fixed.area < HALF_EARTH_THRESHOLD


def test_fix_inverted_polygon_keeps_world_box() -> None:
    geom = from_wkt(bbox_to_wkt(-180.0, -90.0, 180.0, 90.0))
    assert isinstance(geom, Polygon)
    assert geom.area > HALF_EARTH_THRESHOLD

    fixed = _fix_inverted_polygon(geom)
    assert not fixed.is_empty
    assert fixed.area == pytest.approx(360 * 180, abs=1.0)


def test_normalize_geometry_global_bbox_is_non_empty() -> None:
    geom = from_wkt(bbox_to_wkt(-180.0, -90.0, 180.0, 90.0))
    assert isinstance(geom, Polygon)

    result = normalize_geometry(geom)
    assert not result.is_empty
    assert is_valid(result)
    minx, miny, maxx, maxy = result.bounds
    assert minx == pytest.approx(-LON_MAX, abs=1e-3)
    assert maxx == pytest.approx(LON_MAX, abs=1e-3)
    assert miny == pytest.approx(-LAT_MAX, abs=1e-3)
    assert maxy == pytest.approx(LAT_MAX, abs=1e-3)


# Large CLMS extents (e.g. globe_80s80n) cover ~89% of the globe and so exceed
# HALF_EARTH_THRESHOLD, but they are plain rectangles — not inverted footprints.
# bbox_to_wkt adds edge midpoints, producing a 6-unique-vertex ring that must
# still be recognised as a simple rectangle.
_LARGE_CLMS_EXTENTS = (
    (-180.0, -79.9776824, 179.9776872, 80.0223214),  # globe_80s80n (the bug)
    (-180.0, -70.0125000, 179.9875000, 70.0125000),  # globe_70s70n
    (-180.0, -60.0, 180.0, 80.0),  # globe_60s80n
)


@pytest.mark.parametrize(('west', 'south', 'east', 'north'), _LARGE_CLMS_EXTENTS)
def test_is_simple_rectangle_matches_large_clms_extents(
    west: float, south: float, east: float, north: float
) -> None:
    geom = from_wkt(bbox_to_wkt(west, south, east, north))
    assert isinstance(geom, Polygon)
    assert geom.area > HALF_EARTH_THRESHOLD
    assert _is_simple_rectangle(geom)


def test_is_simple_rectangle_rejects_orbital_footprint() -> None:
    # 15-vertex scalloped swath (S5P-style) that genuinely needs inverting.
    footprint = Polygon([
        (-179.99, 89.99), (-179.99, -70), (-150, -70), (-120, -60), (-90, -50),
        (-60, -60), (-30, -70), (0, -80), (30, -70), (60, -60), (90, -50),
        (120, -60), (150, -70), (179.99, -70), (179.99, 89.99), (-179.99, 89.99),
    ])
    assert footprint.area > HALF_EARTH_THRESHOLD
    assert not _is_simple_rectangle(footprint)


@pytest.mark.parametrize(('west', 'south', 'east', 'north'), _LARGE_CLMS_EXTENTS)
def test_fix_inverted_polygon_keeps_large_clms_extents(
    west: float, south: float, east: float, north: float
) -> None:
    geom = from_wkt(bbox_to_wkt(west, south, east, north))
    assert isinstance(geom, Polygon)

    fixed = _fix_inverted_polygon(geom)
    # Must be kept as-is, not replaced by its (tiny) complement frame.
    assert fixed.area == pytest.approx(geom.area, rel=1e-6)


def test_normalize_geometry_globe_80s80n_is_single_band() -> None:
    # Regression: this bbox used to normalize into a degenerate ~4 deg² frame
    # because _fix_inverted_polygon took the complement.
    geom = from_wkt(bbox_to_wkt(-180.0, -79.9776824, 179.9776872, 80.0223214))
    assert isinstance(geom, Polygon)

    result = normalize_geometry(geom)
    assert isinstance(result, Polygon)
    assert is_valid(result)
    # Solid band preserved (clamping shaves a sliver), not erased to its frame.
    assert result.area == pytest.approx(geom.area, rel=1e-3)
    minx, miny, maxx, maxy = result.bounds
    assert miny == pytest.approx(-79.9776824, abs=1e-2)
    assert maxy == pytest.approx(80.0223214, abs=1e-2)


def test_split_pole_routed_polygon_noop_for_regular_polygon() -> None:
    geom = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    assert _split_pole_routed_polygon(geom).equals(geom)


def _full_orbit_polygon() -> Polygon:
    geom = from_wkt(_FULL_ORBIT_WKT)
    assert isinstance(geom, Polygon)
    return geom


def test_count_antimeridian_crossings_ignores_equator_crossing() -> None:
    # Southern polygon whose boundary touches lat=0 exactly at the antimeridian,
    # as produced by _split_polygon_at_equator. The equatorial crossing must not
    # count as northern, otherwise the part looks mixed and is split forever.
    coords = np.array([
        [170, 0],
        [-170, 0],
        [-170, -40],
        [170, -40],
        [170, 0],
    ])
    _count, mixed, latitudes = _count_antimeridian_crossings(coords)
    assert 0 in latitudes
    assert mixed is False


def test_split_polygon_at_equator_can_return_input_unchanged() -> None:
    # Documents the no-progress case guarded against in
    # _rework_via_equator_split: _merge_paths builds no polygon, so the split
    # falls back to returning its input.
    geom = _full_orbit_polygon()
    count, mixed, _latitudes = _count_antimeridian_crossings(get_coordinates(geom))
    assert count == 4
    assert mixed is True

    parts = _split_polygon_at_equator(geom)
    assert len(parts) == 1
    assert parts[0].equals(geom)


def test_rework_antimeridian_polygon_full_orbit_terminates() -> None:
    result = _rework_antimeridian_polygon(_full_orbit_polygon())
    assert isinstance(result, Polygon | MultiPolygon)
    assert is_valid(result)


def test_normalize_geometry_full_orbit_keeps_polar_extent() -> None:
    normalized = normalize_geometry(_full_orbit_polygon())
    assert isinstance(normalized, MultiPolygon)
    assert is_valid(normalized)

    # The swath passes over both poles, so both caps must survive. Clipping
    # them away used to drop ~6% of the footprint area.
    min_lat, max_lat = normalized.bounds[1], normalized.bounds[3]
    assert min_lat == pytest.approx(-LAT_MAX)
    assert max_lat == pytest.approx(LAT_MAX)

    assert all(part.area > 0 for part in normalized.geoms)


def test_normalize_geometry_full_orbit_rings_are_counterclockwise() -> None:
    normalized = normalize_geometry(_full_orbit_polygon())
    assert all(part.exterior.is_ccw for part in normalized.geoms)


def test_normalize_geometry_full_orbit_parts_stay_on_one_side() -> None:
    # OpenSearch cannot tessellate a part that straddles the antimeridian /
    # prime-meridian seam, so every part must live in a single hemisphere.
    normalized = normalize_geometry(_full_orbit_polygon())
    for part in normalized.geoms:
        lons = get_coordinates(part)[:, 0]
        assert lons.min() >= -EPSILON or lons.max() <= EPSILON


def test_insert_pole_points_routes_each_crossing_to_its_own_pole() -> None:
    # One crossing far north, one far south: routing both over the same pole
    # draws a bridge across the whole map.
    coords = np.array(
        [
            [170.0, 80.0],
            [-170.0, 80.0],
            [-170.0, -80.0],
            [170.0, -80.0],
            [170.0, 80.0],
        ],
        dtype=np.float64,
    )
    crossings = _detect_antimeridian_crossings(coords)
    assert len(crossings) == 2

    result = _insert_pole_points_at_crossings(coords, crossings)
    pole_lats = result[np.isclose(np.abs(result[:, 1]), LAT_MAX), 1]
    assert (pole_lats > 0).any(), 'northern crossing must route over the North Pole'
    assert (pole_lats < 0).any(), 'southern crossing must route over the South Pole'


def test_insert_pole_points_pole_sign_overrides_every_crossing() -> None:
    coords = np.array(
        [
            [170.0, 80.0],
            [-170.0, 80.0],
            [-170.0, -80.0],
            [170.0, -80.0],
            [170.0, 80.0],
        ],
        dtype=np.float64,
    )
    crossings = _detect_antimeridian_crossings(coords)
    result = _insert_pole_points_at_crossings(coords, crossings, pole_sign=-1)
    pole_lats = result[np.isclose(np.abs(result[:, 1]), LAT_MAX), 1]
    assert len(pole_lats) == 2 * len(crossings)
    assert (pole_lats < 0).all()


def test_has_dual_pole_routing() -> None:
    both = np.array([[LON_MAX, LAT_MAX], [-LON_MAX, -LAT_MAX], [10.0, 0.0]])
    north_only = np.array([[LON_MAX, LAT_MAX], [-LON_MAX, 50.0], [10.0, 0.0]])
    assert _has_dual_pole_routing(both) is True
    assert _has_dual_pole_routing(north_only) is False


def test_split_pole_routed_polygon_keeps_polar_caps() -> None:
    # Ring routed over both poles: the split must cut east/west without
    # clipping the caps off the top and bottom.
    geom = Polygon([
        (170, 50),
        (LON_MAX, 55),
        (LON_MAX, LAT_MAX),
        (-LON_MAX, LAT_MAX),
        (-LON_MAX, 55),
        (-170, 50),
        (-170, -50),
        (-LON_MAX, -55),
        (-LON_MAX, -LAT_MAX),
        (LON_MAX, -LAT_MAX),
        (LON_MAX, -55),
        (170, -50),
        (170, 50),
    ])
    result = _split_pole_routed_polygon(geom)

    assert isinstance(result, MultiPolygon)
    assert result.bounds[1] == pytest.approx(-LAT_MAX)
    assert result.bounds[3] == pytest.approx(LAT_MAX)
    for part in result.geoms:
        lons = get_coordinates(part)[:, 0]
        assert lons.min() >= -EPSILON or lons.max() <= EPSILON


def _max_lon_jump(geom: Polygon | MultiPolygon) -> float:
    parts = geom.geoms if isinstance(geom, MultiPolygon) else (geom,)
    return max(
        float(np.abs(np.diff(get_coordinates(ring)[:, 0])).max())
        for part in parts
        for ring in (part.exterior, *part.interiors)
    )


def test_densify_pole_bridges_splits_the_full_width_bridge() -> None:
    # Pole routing leaves a single segment running +LON_MAX -> -LON_MAX at the
    # pole. sfeos reads a |dlon| > 180 step as an improper antimeridian
    # crossing (RFC 7946 3.1.9) and rejects the item.
    geom = Polygon([
        (170, 80),
        (LON_MAX, 80),
        (LON_MAX, LAT_MAX),
        (-LON_MAX, LAT_MAX),
        (-LON_MAX, 80),
        (-170, 80),
        (170, 80),
    ])
    assert _max_lon_jump(geom) > 180

    result = densify_pole_bridges(geom)
    assert _max_lon_jump(result) <= 180
    assert result.area == pytest.approx(geom.area)
    assert result.symmetric_difference(geom).area == pytest.approx(0, abs=1e-9)


def test_densify_pole_bridges_respects_max_lon_step() -> None:
    geom = Polygon([
        (LON_MAX, LAT_MAX),
        (-LON_MAX, LAT_MAX),
        (-LON_MAX, 80),
        (LON_MAX, 80),
        (LON_MAX, LAT_MAX),
    ])
    assert _max_lon_jump(densify_pole_bridges(geom, max_lon_step=45.0)) <= 45


def test_densify_pole_bridges_returns_compliant_geometry_unchanged() -> None:
    geom = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    assert densify_pole_bridges(geom) is geom


def test_normalize_geometry_emits_no_oversized_lon_jump() -> None:
    # Single-pole footprints keep their pole bridge (no east/west split), so
    # this is the case that used to ship a 360 deg step.
    polar = Polygon([(-110, 89), (15, 88), (140, 89), (-143, 89.5), (-110, 89)])
    for geom in (polar, _full_orbit_polygon()):
        assert _max_lon_jump(normalize_geometry(geom)) <= 180
