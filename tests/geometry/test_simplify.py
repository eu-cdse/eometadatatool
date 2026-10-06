import numpy as np
from shapely import MultiPolygon, Point, Polygon, count_coordinates, get_coordinates

from eometadatatool.geometry.antimeridian import densify_pole_bridges
from eometadatatool.geometry.normalize import normalize_geometry
from eometadatatool.geometry.simplify import (
    DEFAULT_SIMPLIFY_CONFIG,
    SimplifyConfig,
    simplify_geometry,
)


def test_simplify_config_defaults() -> None:
    config = SimplifyConfig()
    assert config.max_area_change == 0.05
    assert config.max_area_change_tol == 0.01
    assert config.min_tolerance_range == 50
    assert config.max_tolerance_range == 100000
    assert config.max_iter == 8
    assert config == DEFAULT_SIMPLIFY_CONFIG


def test_small_geometry_is_not_simplified() -> None:
    geom = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    result = simplify_geometry(geom)
    assert result.equals(geom)


def test_dense_polygon_can_be_simplified() -> None:
    geom = Point(0, 0).buffer(1.0, quad_segs=32)
    original_coords = count_coordinates(geom)

    result = simplify_geometry(
        geom,
        max_area_change=0.25,
        max_area_change_tol=0.02,
        min_tolerance_range=100,
        max_tolerance_range=10000,
    )

    assert count_coordinates(result) <= original_coords
    assert result.geom_type == 'Polygon'


def test_multipolygon_is_simplified_per_part() -> None:
    poly_a = Point(0, 0).buffer(1.0, quad_segs=24)
    poly_b = Point(3, 0).buffer(1.0, quad_segs=24)
    geom = MultiPolygon([poly_a, poly_b])

    result = simplify_geometry(
        geom,
        max_area_change=0.2,
        max_area_change_tol=0.02,
        min_tolerance_range=100,
        max_tolerance_range=10000,
    )

    assert result.geom_type == 'MultiPolygon'
    assert len(result.geoms) == 2


def test_simplify_geometry_accepts_config() -> None:
    geom = Point(0, 0).buffer(1.0, quad_segs=32)
    config = SimplifyConfig(
        max_area_change=0.2,
        max_area_change_tol=0.02,
        min_tolerance_range=100,
        max_tolerance_range=10000,
        max_iter=6,
    )

    result = simplify_geometry(geom, config=config)
    assert result.geom_type == 'Polygon'
    assert count_coordinates(result) <= count_coordinates(geom)


def test_simplify_geometry_config_can_be_overridden() -> None:
    geom = Point(0, 0).buffer(1.0, quad_segs=24)
    config = SimplifyConfig(max_area_change=0.01, max_tolerance_range=1000)

    result = simplify_geometry(geom, max_area_change=0.2, config=config)
    assert result.geom_type == 'Polygon'


def test_simplify_then_densify_keeps_lon_jumps_compliant() -> None:
    # simplify drops the collinear vertices densify_pole_bridges inserted along
    # the pole bridge, so STACItem re-densifies afterwards; check that pairing.
    normalized = normalize_geometry(
        Polygon([(-110, 89), (15, 88), (140, 89), (-143, 89.5), (-110, 89)])
    )

    def max_lon_jump(geom) -> float:
        parts = geom.geoms if isinstance(geom, MultiPolygon) else (geom,)
        return max(
            float(np.abs(np.diff(get_coordinates(ring)[:, 0])).max())
            for part in parts
            for ring in (part.exterior, *part.interiors)
        )

    assert max_lon_jump(normalized) <= 180
    assert max_lon_jump(densify_pole_bridges(simplify_geometry(normalized))) <= 180
