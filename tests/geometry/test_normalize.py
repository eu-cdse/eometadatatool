import numpy as np
from shapely import MultiPolygon, Polygon, get_coordinates, is_valid

from eometadatatool.geometry.constants import HALF_EARTH_THRESHOLD, LAT_MAX, LON_MAX
from eometadatatool.geometry.normalize import (
    NormalizeConfig,
    _clamp_coordinates,
    _ensure_ccw_orientation,
    normalize_geometry,
)


def test_clamp_coordinates_exact_180() -> None:
    geom = Polygon([(180, 45), (180, 46), (179, 46), (179, 45), (180, 45)])
    result = _clamp_coordinates(geom)
    coords = get_coordinates(result)
    assert coords[:, 0].max() == LON_MAX


def test_clamp_coordinates_exact_90() -> None:
    geom = Polygon([(0, 90), (1, 90), (1, 89), (0, 89), (0, 90)])
    result = _clamp_coordinates(geom)
    coords = get_coordinates(result)
    assert coords[:, 1].max() == LAT_MAX


def test_ensure_ccw_orientation_for_multipolygon() -> None:
    geom = MultiPolygon([
        Polygon([(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]),
        Polygon([(2, 0), (2, 1), (3, 1), (3, 0), (2, 0)]),
    ])
    result = _ensure_ccw_orientation(geom)
    assert isinstance(result, MultiPolygon)
    for poly in result.geoms:
        assert poly.exterior.is_ccw


def test_normalize_geometry_boundary_clamping() -> None:
    geom = Polygon([(180, 90), (180, 89), (179, 89), (179, 90), (180, 90)])
    result = normalize_geometry(geom)

    assert is_valid(result)
    coords = get_coordinates(result)
    assert coords[:, 0].max() < 180
    assert coords[:, 0].min() > -180
    assert coords[:, 1].max() < 90
    assert coords[:, 1].min() > -90


def test_normalize_geometry_invalid_bowtie_fixed() -> None:
    geom = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    result = normalize_geometry(geom)
    assert is_valid(result)


def test_normalize_geometry_out_of_bounds_lon() -> None:
    geom = Polygon([(190, 50), (200, 50), (200, 60), (190, 60), (190, 50)])
    result = normalize_geometry(geom)
    coords = get_coordinates(result)
    assert coords[:, 0].min() >= -180
    assert coords[:, 0].max() <= 180


def test_normalize_geometry_polar_footprint() -> None:
    geom = Polygon([(-110, 89), (15, 88), (140, 89), (-143, 89.5), (-110, 89)])
    result = normalize_geometry(geom)
    assert is_valid(result)
    assert get_coordinates(result)[:, 1].max() < 90


def test_normalize_geometry_inverted_polygon_fixed() -> None:
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

    result = normalize_geometry(geom)
    assert is_valid(result)
    assert result.area < HALF_EARTH_THRESHOLD


def test_normalize_geometry_antimeridian_strip() -> None:
    geom = Polygon([(179, 30), (179, 50), (-179, 50), (-179, 30), (179, 30)])
    result = normalize_geometry(geom)
    assert is_valid(result)
    assert isinstance(result, Polygon | MultiPolygon)


def test_normalize_geometry_accepts_custom_config() -> None:
    geom = Polygon([(180, 90), (180, 89), (179, 89), (179, 90), (180, 90)])
    config = NormalizeConfig(lon_limit=179.5, lat_limit=89.5)

    result = normalize_geometry(geom, config=config)
    coords = get_coordinates(result)

    assert coords[:, 0].max() <= 179.5
    assert coords[:, 1].max() <= 89.5


def test_clamp_coordinates_no_change_inside_bounds() -> None:
    geom = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    result = _clamp_coordinates(geom)
    assert np.array_equal(get_coordinates(result), get_coordinates(geom))


def test_normalize_geometry_output_rings_are_counterclockwise() -> None:
    # RFC 7946 wants exterior rings counterclockwise. Orienting mid-pipeline is
    # not enough: the east/west clip and make_valid both discard winding, so the
    # guarantee has to hold on the final output.
    antimeridian_tile = Polygon([
        (179.928473473918, 9.99897831672069),
        (-169.920147289013, 9.9909309627606),
        (-169.99173290556, 5.67994760615426e-06),
        (-179.999951582871, -0.0068357003079556),
        (179.928473473918, 9.99897831672069),
    ])
    # Full-globe extent, with the midpoints bbox_to_wkt inserts on wide boxes.
    globe = Polygon([
        (-180, 90),
        (0, 90),
        (180, 90),
        (180, -90),
        (0, -90),
        (-180, -90),
        (-180, 90),
    ])

    for geom in (antimeridian_tile, globe):
        result = normalize_geometry(geom)
        parts = result.geoms if isinstance(result, MultiPolygon) else (result,)
        assert all(part.exterior.is_ccw for part in parts), (
            f'clockwise exterior ring in {result.wkt[:80]}'
        )
