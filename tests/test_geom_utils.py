"""Facade-level API tests for eometadatatool.geom_utils."""

import numpy as np
from shapely import (
    MultiPolygon,
    Point,
    Polygon,
    count_coordinates,
    get_coordinates,
    is_valid,
)

from eometadatatool.geom_utils import (
    EPSILON,
    HALF_EARTH_THRESHOLD,
    LAT_MAX,
    LON_MAX,
    average_angles,
    normalize_geometry,
    simplify_geometry,
)
from eometadatatool.geometry.normalize import NormalizeConfig
from eometadatatool.geometry.simplify import SimplifyConfig


def test_public_constants_available() -> None:
    assert EPSILON > 0
    assert LON_MAX < 180
    assert LAT_MAX < 90
    assert HALF_EARTH_THRESHOLD > 30000


def test_normalize_geometry_valid_geometry() -> None:
    geom = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    result = normalize_geometry(geom)
    assert is_valid(result)


def test_normalize_geometry_clamps_boundaries() -> None:
    geom = Polygon([(180, 90), (180, 89), (179, 89), (179, 90), (180, 90)])
    result = normalize_geometry(geom)

    coords = get_coordinates(result)
    assert coords[:, 0].max() < 180
    assert coords[:, 0].min() > -180
    assert coords[:, 1].max() < 90
    assert coords[:, 1].min() > -90


def test_normalize_geometry_fixes_invalid_polygon() -> None:
    geom = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    result = normalize_geometry(geom)
    assert is_valid(result)


def test_normalize_geometry_antimeridian_crossing() -> None:
    geom = Polygon([(170, 50), (-170, 50), (-170, 60), (170, 60), (170, 50)])
    result = normalize_geometry(geom)
    assert is_valid(result)
    assert isinstance(result, Polygon | MultiPolygon)


def test_normalize_geometry_multipolygon_input() -> None:
    poly_a = Polygon([(170, 50), (-170, 50), (-170, 55), (170, 55), (170, 50)])
    poly_b = Polygon([(10, 50), (20, 50), (20, 60), (10, 60), (10, 50)])
    result = normalize_geometry(MultiPolygon([poly_a, poly_b]))
    assert is_valid(result)


def test_simplify_geometry_small_geometry_unchanged() -> None:
    geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    result = simplify_geometry(geom)
    assert result.equals(geom)


def test_simplify_geometry_dense_polygon() -> None:
    geom = Point(0, 0).buffer(1.0, quad_segs=32)
    original = count_coordinates(geom)
    result = simplify_geometry(geom, max_area_change=0.25, max_area_change_tol=0.02)
    assert count_coordinates(result) <= original
    assert result.geom_type == 'Polygon'


def test_facade_normalize_geometry_accepts_config() -> None:
    geom = Polygon([(180, 90), (180, 89), (179, 89), (179, 90), (180, 90)])
    result = normalize_geometry(geom, config=NormalizeConfig(lon_limit=179.5))
    assert get_coordinates(result)[:, 0].max() <= 179.5


def test_facade_simplify_geometry_accepts_config() -> None:
    geom = Point(0, 0).buffer(1.0, quad_segs=24)
    result = simplify_geometry(geom, config=SimplifyConfig(max_area_change=0.2))
    assert result.geom_type == 'Polygon'


def test_average_angles_wraparound() -> None:
    angles = np.array([[359.0, 1.0], [90.0, 100.0]])
    result = average_angles(angles)
    assert np.isclose(result[0], 0.0) or np.isclose(result[0], 360.0)
    assert 90.0 <= result[1] <= 100.0


def test_average_angles_empty_input() -> None:
    angles = np.array([[]], dtype=float)
    result = average_angles(angles)
    assert result.size == 0
