import logging
from dataclasses import dataclass
from functools import partial
from itertools import product
from typing import overload

import numpy as np
import shapely
from shapely import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    box,
    buffer,
    is_valid,
    make_valid,
    prepare,
    remove_repeated_points,
    set_coordinates,
    simplify,
    transform,
    union_all,
)
from shapely.errors import GEOSException
from shapely.validation import explain_validity

from eometadatatool.flags import is_strict
from eometadatatool.geometry.antimeridian import (
    _fix_inverted_polygon,
    _rework_antimeridian_polygon,
    _split_pole_routed_polygon,
    densify_pole_bridges,
)
from eometadatatool.geometry.constants import LAT_MAX, LON_MAX


@dataclass(frozen=True, slots=True)
class NormalizeConfig:
    lon_limit: float = LON_MAX
    lat_limit: float = LAT_MAX
    remove_repeated_tolerance: float = 1e-10
    post_fix_simplify_tolerance: float = 1e-7


DEFAULT_NORMALIZE_CONFIG = NormalizeConfig()


def _transform_tile_flip(a, *, x_offset: float, y_offset: float):
    return (a - (x_offset, y_offset)) * -1


def _transform_tile_shift(a, *, x_offset: float, y_offset: float):
    return a - (x_offset, y_offset)


def _clamp_coordinates(
    geom: Polygon | MultiPolygon,
    *,
    config: NormalizeConfig = DEFAULT_NORMALIZE_CONFIG,
) -> Polygon | MultiPolygon:
    """
    Clamp coordinates to avoid exact boundary values that OpenSearch rejects.

    OpenSearch geo_shape has issues with exact +/-180 longitude and +/-90 latitude
    due to tessellation problems. This function clamps all coordinates to
    slightly within the valid bounds.

    Args:
        geom: Input geometry
        config: Normalization thresholds.

    Returns:
        Geometry with clamped coordinates
    """
    coords = shapely.get_coordinates(geom)
    clamped = coords.copy()

    clamped[:, 0] = np.clip(coords[:, 0], -config.lon_limit, config.lon_limit)
    clamped[:, 1] = np.clip(coords[:, 1], -config.lat_limit, config.lat_limit)

    if not np.array_equal(coords, clamped):
        num_clamped = np.sum(coords != clamped)
        logging.debug('Clamped %d boundary coordinates', num_clamped)
        return set_coordinates(geom, clamped)

    return geom


def _ensure_ccw_orientation(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    """
    Ensure counterclockwise orientation per GeoJSON RFC 7946.

    GeoJSON standard requires exterior rings to be counterclockwise
    and interior rings (holes) to be clockwise.

    Args:
        geom: Input geometry

    Returns:
        Geometry with correct orientation
    """
    # shapely.orient_polygons enforces CCW for exterior rings by default
    return shapely.orient_polygons(geom)


def _is_within_wgs84_bounds(geom: Polygon | MultiPolygon) -> bool:
    min_x, min_y, max_x, max_y = geom.bounds
    return (
        -180 <= min_x <= 180
        and -90 <= min_y <= 90
        and -180 <= max_x <= 180
        and -90 <= max_y <= 90
    )


def _normalize_out_of_bounds_tiles(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    min_x, min_y, max_x, max_y = geom.bounds

    # Prepare geometry for faster intersection checks
    prepare(geom)

    min_x_step = int((min_x + 180) // 360)
    max_x_step = int((max_x + 180) // 360)
    min_y_step = int((min_y + 90) // 180)
    max_y_step = int((max_y + 90) // 180)
    geoms: list[Polygon | MultiPolygon] = []

    for x_step, y_step in product(
        range(min_x_step, max_x_step + 1),
        range(min_y_step, max_y_step + 1),
    ):
        x_offset = x_step * 360
        y_offset = y_step * 180
        part = box(
            xmin=x_offset - 180,
            ymin=y_offset - 90,
            xmax=x_offset + 180,
            ymax=y_offset + 90,
        ).intersection(geom)
        if part.is_empty:
            continue

        if x_offset or y_offset:
            flip_y = y_step % 2 == 1
            transform_fn = partial(
                _transform_tile_flip if flip_y else _transform_tile_shift,
                x_offset=x_offset,
                y_offset=y_offset,
            )
            part = transform(part, transform_fn)

        geoms.extend(
            g
            for g in (
                part.geoms if isinstance(part, GeometryCollection) else (part,)
            )
            if isinstance(g, Polygon | MultiPolygon)
        )

    return union_all(geoms)  # type: ignore[return-value]


@overload
def normalize_geometry(
    geom: Polygon,
    *,
    config: NormalizeConfig = DEFAULT_NORMALIZE_CONFIG,
) -> Polygon | MultiPolygon: ...


@overload
def normalize_geometry(
    geom: MultiPolygon,
    *,
    config: NormalizeConfig = DEFAULT_NORMALIZE_CONFIG,
) -> MultiPolygon: ...


def normalize_geometry(
    geom: Polygon | MultiPolygon,
    *,
    config: NormalizeConfig = DEFAULT_NORMALIZE_CONFIG,
) -> Polygon | MultiPolygon:
    """Normalize geometry for OpenSearch geo_shape compatibility.

    Ensures:
    - Coordinates within [-180+eps, 180-eps] x [-90+eps, 90-eps] (no exact boundaries)
    - Counterclockwise orientation (GeoJSON RFC 7946 standard)
    - Valid topology (no self-intersection)

    Args:
        geom: Input Polygon or MultiPolygon.

    Returns:
        Normalized geometry compatible with OpenSearch geo_shape.
    """
    # 1. Rework antimeridian crossings FIRST (polar-inclusive algorithm)
    # This MUST happen before make_valid, because the algorithm handles
    # self-intersections by routing through poles. If make_valid runs first,
    # it fragments the geometry into multiple parts.
    if isinstance(geom, Polygon):
        geom = _rework_antimeridian_polygon(geom)
    elif isinstance(geom, MultiPolygon):
        reworked_parts: list[Polygon] = []
        for poly in geom.geoms:
            reworked = _rework_antimeridian_polygon(poly)
            if isinstance(reworked, MultiPolygon):
                reworked_parts.extend(reworked.geoms)
            else:
                reworked_parts.append(reworked)
        geom = (
            MultiPolygon(reworked_parts)
            if len(reworked_parts) > 1
            else reworked_parts[0]
        )

    # 2. Initial validation (after antimeridian rework)
    if not geom.is_valid:
        if is_strict():
            raise ValueError(f'normalize_geometry: invalid geometry {geom.wkt!r})')
        geom = make_valid(geom, method='structure', keep_collapsed=False)  # type: ignore

    # 3. Tile-based normalization for coordinates outside [-180, 180] x [-90, 90]
    if not _is_within_wgs84_bounds(geom):
        geom = _normalize_out_of_bounds_tiles(geom)

    # 4. Fix inverted polygon (interior/exterior swap for large footprints)
    geom = _fix_inverted_polygon(geom)

    # 5. Clamp boundary coordinates (avoid exact +/-180, +/-90)
    geom = _clamp_coordinates(geom, config=config)

    # 6. Remove duplicate consecutive coordinates (OpenSearch rejects these)
    # Duplicates arise when clamping snaps distinct coords to the same LON_MAX/LAT_MAX
    # or when antimeridian transition points coincide with existing vertices.
    # Clamping can collapse a ring to <3 points, causing GEOSException in
    # remove_repeated_points. In that case, repair with make_valid instead.
    try:
        geom = remove_repeated_points(geom, tolerance=config.remove_repeated_tolerance)
    except GEOSException:
        geom = make_valid(geom, method='structure', keep_collapsed=False)  # type: ignore[assignment]

    # 7. Ensure counterclockwise orientation (GeoJSON RFC 7946)
    geom = _ensure_ccw_orientation(geom)

    # 8. Split dual-pole routed polygons (S5P full-orbit products)
    # Must be done AFTER orientation but BEFORE final validation
    geom = _split_pole_routed_polygon(geom)

    # 9. Final validation (ensure result is valid for OpenSearch)
    if not is_valid(geom):
        reason = explain_validity(geom)
        logging.warning('Invalid geometry after normalization: %s', reason)
        geom = make_valid(geom, method='structure', keep_collapsed=False)  # type: ignore[assignment]
        # Apply buffer(0) to fix remaining self-intersections
        # Important for complex polar geometries with antimeridian crossings
        geom = buffer(geom, 0.0)  # type: ignore[assignment]
        # After buffer, simplify slightly to clean up any micro-segments
        geom = simplify(geom, tolerance=config.post_fix_simplify_tolerance)  # type: ignore[assignment]

    # 10. Subdivide pole-bridge segments so no ring keeps a |dlon| > 180 jump
    # between consecutive vertices (rejected by sfeos); shape is unchanged.
    geom = densify_pole_bridges(geom)

    # 11. Re-assert counterclockwise orientation, and do it last.
    # Neither the east/west clip in step 8 nor make_valid/buffer in step 9
    # preserves ring winding, so step 7 alone leaves clockwise exterior rings
    # in the output (GeoJSON RFC 7946 wants them counterclockwise).
    return _ensure_ccw_orientation(geom)
