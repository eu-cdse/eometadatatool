import logging
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from shapely import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    box,
    buffer,
    difference,
    get_coordinates,
    symmetric_difference,
    union_all,
)
from shapely.ops import transform as transform_ops

from eometadatatool.geometry.constants import (
    EPSILON,
    HALF_EARTH_THRESHOLD,
    LAT_MAX,
    LON_MAX,
    WORLD_EQUIV_TOLERANCE,
)
from eometadatatool.geometry.projections import (
    _north_pole_projected,
    _south_pole_projected,
    _wgs84_to_polar_north,
    _wgs84_to_polar_south,
)

# Crossings within this distance of the equator belong to neither hemisphere.
# _split_polygon_at_equator inserts vertices at exactly lat=0, so counting them
# as northern would make a purely southern sub-polygon look mixed forever.
_EQUATOR_EPS = EPSILON * 100

# Safety bound for the equator-split recursion in _rework_antimeridian_polygon.
# Real footprints need a single level.
_MAX_EQUATOR_SPLIT_DEPTH = 4


def _normalize_lon_to_360(lon: float) -> float:
    """Normalize longitude from [-180, 180] to [0, 360) range.

    Args:
        lon: Longitude in degrees, typically in [-180, 180] range.

    Returns:
        Longitude normalized to [0, 360) range.
    """
    if lon < 0:
        return 180 + (lon + 180)
    return lon


def check_contains_pole(
    geom: Polygon | MultiPolygon,
) -> Literal['north', 'south', None]:
    """
    Check if geometry contains North or South pole using stereographic projection.

    This is more accurate than simple coordinate-based heuristics, especially
    for complex polar footprints (e.g., Sentinel-3 SLSTR/OLCI).

    Args:
        geom: Polygon or MultiPolygon geometry in WGS84 (EPSG:4326)

    Returns:
        'north' if contains North Pole
        'south' if contains South Pole
        None if contains neither
    """
    try:
        # Check North Pole - clip to northern hemisphere first
        north_half = box(-180, 0, 180, 90).intersection(geom)
        if not north_half.is_empty:
            north_geom = transform_ops(_wgs84_to_polar_north, north_half)
            # Buffer by 1m to handle float precision issues
            if north_geom.buffer(1).contains(_north_pole_projected):
                return 'north'
    except Exception as e:
        logging.debug('North pole containment check failed: %s', e)

    try:
        # Check South Pole - clip to southern hemisphere first
        south_half = box(-180, -90, 180, 0).intersection(geom)
        if not south_half.is_empty:
            south_geom = transform_ops(_wgs84_to_polar_south, south_half)
            if south_geom.buffer(1).contains(_south_pole_projected):
                return 'south'
    except Exception as e:
        logging.debug('South pole containment check failed: %s', e)

    return None


def lat_cross_antimeridian(p1: NDArray, p2: NDArray) -> float:
    """Calculate latitude where line between p1 and p2 crosses the antimeridian.

    Uses linear interpolation between two points that cross the antimeridian (+/-180 deg).

    Args:
        p1: First point as [lon, lat] array.
        p2: Second point as [lon, lat] array.

    Returns:
        Latitude in degrees at the antimeridian crossing.
    """
    lon1, lat1 = float(p1[0]), float(p1[1])
    lon2, lat2 = float(p2[0]), float(p2[1])

    # Normalize longitudes to [0, 360) for consistent calculation
    lon1 = _normalize_lon_to_360(lon1)
    lon2 = _normalize_lon_to_360(lon2)

    # Avoid division by zero
    if lon2 == lon1:
        return (lat1 + lat2) / 2

    # Linear interpolation: find latitude at lon=180
    m = (lat2 - lat1) / (lon2 - lon1)
    b = lat1 - m * lon1
    return 180.0 * m + b


def lon_cross_equator(p1: NDArray, p2: NDArray) -> float:
    """Calculate longitude where line between p1 and p2 crosses the equator.

    Uses linear interpolation between two points that cross the equator (lat=0).

    Args:
        p1: First point as [lon, lat] array.
        p2: Second point as [lon, lat] array.

    Returns:
        Longitude in degrees at the equator crossing, in [-180, 180] range.
    """
    lon1, lat1 = float(p1[0]), float(p1[1])
    lon2, lat2 = float(p2[0]), float(p2[1])

    # Handle vertical line (same longitude) - return that longitude
    if lon1 == lon2:
        return lon1

    # Normalize longitudes to [0, 360) for consistent calculation
    lon1 = _normalize_lon_to_360(lon1)
    lon2 = _normalize_lon_to_360(lon2)

    # Avoid division by zero (horizontal line)
    if lat2 == lat1:
        return (lon1 + lon2) / 2

    # Linear interpolation: find longitude at lat=0
    # y = mx + b => x = (y - b) / m => x = -b / m (when y=0)
    m = (lat2 - lat1) / (lon2 - lon1)
    b = lat1 - m * lon1
    result = -b / m

    # Convert back to [-180, 180]
    if result > 180:
        result = result - 360
    return result


def _count_antimeridian_crossings(
    coords: NDArray,
) -> tuple[int, bool, list[float]]:
    """
    Count antimeridian crossings and check if they occur in both hemispheres.

    This is essential for detecting complex orbital footprints that require
    equator-split processing (e.g., S5P TROPOMI pole-to-pole orbits).

    Args:
        coords: Array of shape (N, 2) with [lon, lat] coordinates

    Returns:
        Tuple of:
        - count: Number of antimeridian crossings
        - mixed: True if crossings occur in both hemispheres (N and S)
        - latitudes: List of latitudes at each crossing point
    """
    count = 0
    latitudes: list[float] = []
    has_north = False
    has_south = False

    for i in range(len(coords) - 1):
        lon1, lon2 = coords[i, 0], coords[i + 1, 0]

        # Check for crossing: |delta lon| > 180 OR exact +/-180 deg
        is_crossing = abs(lon2 - lon1) > 180 or lon1 in {180, -180}

        if is_crossing and abs(lon2 - lon1) > 180:
            count += 1
            lat = lat_cross_antimeridian(coords[i], coords[i + 1])
            latitudes.append(lat)

            if lat > _EQUATOR_EPS:
                has_north = True
            elif lat < -_EQUATOR_EPS:
                has_south = True
            # else: crossing on the equator - belongs to neither hemisphere

    mixed = has_north and has_south
    return count, mixed, latitudes


def _detect_antimeridian_crossings(coords: NDArray) -> list[int]:
    """
    Detect indices where consecutive points cross the antimeridian (+/-180 deg).

    A crossing is detected when:
    1. Longitude difference > 180 deg between consecutive points, OR
    2. A point lies exactly on the antimeridian (lon == +/-180 deg)

    Args:
        coords: Array of shape (N, 2) with [lon, lat] coordinates

    Returns:
        List of indices where crossing occurs (at index i, points i and i+1 cross)
    """
    crossings = []
    for i in range(len(coords) - 1):
        lon1, lon2 = coords[i, 0], coords[i + 1, 0]
        lon_diff = abs(lon2 - lon1)

        # TRUE crossing: large longitude jump (> 180 deg)
        # This catches both normal crossings AND cases where one point is at +/-180
        if lon_diff > 180:
            crossings.append(i)

    return crossings


def _insert_pole_points_at_crossings(
    coords: NDArray,
    crossings: list[int],
    *,
    pole_sign: int | None = None,
) -> NDArray:
    """
    Insert pole routing points at each antimeridian crossing.

    At each crossing, inserts 4 points to route through the nearest pole:
    1. Point on antimeridian (exit side)
    2. Point at pole (exit side)
    3. Point at pole (entry side)
    4. Point on antimeridian (entry side)

    Args:
        coords: Array of shape (N, 2) with [lon, lat] coordinates
        crossings: List of crossing indices from _detect_antimeridian_crossings
        pole_sign: Override for the pole direction, applied to *every*
            crossing. +1 = route through North Pole, -1 = South Pole.
            When ``None`` (the default), each crossing routes through the
            pole of its own hemisphere.

    Returns:
        New coordinate array with pole points inserted
    """
    if not crossings:
        return coords

    # Ensure float64 to preserve precision of LON_MAX/LAT_MAX values
    result = coords.astype(np.float64)

    # Process crossings in reverse order to maintain correct indices
    for i in sorted(crossings, reverse=True):
        p1 = result[i]
        p2 = result[i + 1]

        # Determine horizontal direction based on exit longitude
        hsign = -1 if p1[0] < 0 else 1

        # Calculate latitude at antimeridian crossing
        lat_cross = lat_cross_antimeridian(p1, p2)

        # Determine vertical direction (pole) for THIS crossing. A single
        # ring-wide sign breaks footprints crossing in both hemispheres: a
        # crossing at lat -87 routed over the North Pole draws a bridge across
        # the whole map, and the polygon balloons to most of the lon/lat plane.
        vsign = pole_sign if pole_sign is not None else (-1 if lat_cross < 0 else 1)

        # Insert 4 pole routing points
        pole_points = np.array([
            [hsign * LON_MAX, lat_cross],  # On antimeridian (exit)
            [hsign * LON_MAX, vsign * LAT_MAX],  # To pole
            [-hsign * LON_MAX, vsign * LAT_MAX],  # Pole (opposite side)
            [-hsign * LON_MAX, lat_cross],  # Back from pole
        ])

        result = np.insert(result, i + 1, pole_points, axis=0)

    return result


def _is_pole_point(lon: float, lat: float) -> bool:
    """Check if point is a pole routing point (should be skipped)."""
    return abs(abs(lon) - 180) < EPSILON * 100 and abs(abs(lat) - 90) < EPSILON * 100


def _add_to_side(
    coord: NDArray,
    *,
    to_east: bool,
    east_coords: list[NDArray],
    west_coords: list[NDArray],
) -> None:
    """Add coordinate to appropriate side list."""
    if to_east:
        east_coords.append(coord)
    else:
        west_coords.append(coord)


def _split_at_antimeridian(geom: Polygon) -> Polygon | MultiPolygon:
    """
    Split a polygon at the antimeridian into western and eastern parts.

    Algorithm:
    1. Track which side (east/west) we're on based on longitude sign
    2. When crossing antimeridian, add transition point to BOTH sides
    3. Skip pole routing points (lon ~ +/-180 AND lat ~ +/-90)
    4. Build separate polygons for each side

    Args:
        geom: Polygon with pole routing points already inserted.

    Returns:
        MultiPolygon with separate western and eastern parts,
        or Polygon if only one part.
    """
    coords = get_coordinates(geom)
    n = len(coords)

    # east_coords = positive lon (Asia side, lon >= 0)
    # west_coords = negative lon (Americas side, lon < 0)
    east_coords: list[NDArray] = []
    west_coords: list[NDArray] = []

    for i in range(n):
        lon, lat = coords[i, 0], coords[i, 1]

        # Skip pole routing points
        if _is_pole_point(lon, lat):
            continue

        # Determine which side this point belongs to
        is_east = lon >= 0

        # Check for crossing to next point
        if i < n - 1:
            next_lon = coords[i + 1, 0]

            # Skip if next point is a pole point (find the real next point)
            next_idx = i + 1
            while next_idx < n - 1 and _is_pole_point(
                coords[next_idx, 0], coords[next_idx, 1]
            ):
                next_idx += 1
            if next_idx < n:
                next_lon = coords[next_idx, 0]

            # Detect crossing (large longitude jump, not pole points)
            if abs(next_lon - lon) > 180:
                # Calculate latitude at antimeridian
                next_lat = coords[next_idx, 1] if next_idx < n else lat
                lat_at_am = lat_cross_antimeridian(
                    np.array([lon, lat]),
                    np.array([next_lon, next_lat]),
                )

                # Add current point to its side
                _add_to_side(
                    coords[i],
                    to_east=is_east,
                    east_coords=east_coords,
                    west_coords=west_coords,
                )

                # Add transition point to BOTH sides (key fix!)
                # East side gets +LON_MAX, west side gets -LON_MAX
                east_coords.append(np.array([LON_MAX, lat_at_am]))
                west_coords.append(np.array([-LON_MAX, lat_at_am]))
                continue

        # Normal point - add to appropriate side
        _add_to_side(
            coords[i],
            to_east=is_east,
            east_coords=east_coords,
            west_coords=west_coords,
        )

    # Build result polygons
    if not east_coords and not west_coords:
        return geom if geom.is_valid else buffer(geom, 0.0)

    parts = []
    for coords_list, name in [(east_coords, 'east'), (west_coords, 'west')]:
        if len(coords_list) < 3:
            continue

        arr = np.array(coords_list)
        # Close ring if needed
        if not np.allclose(arr[0], arr[-1]):
            arr = np.vstack([arr, arr[0]])

        try:
            poly = Polygon(arr)
            if not poly.is_valid:
                poly = buffer(poly, 0.0)  # type: ignore[assignment]
            if poly.is_empty:
                continue
            if isinstance(poly, Polygon):
                parts.append(poly)
            elif isinstance(poly, MultiPolygon):
                parts.extend(p for p in poly.geoms if not p.is_empty)  # type: ignore[union-attr]
        except Exception as e:
            logging.debug('Failed to create %s polygon: %s', name, e)

    if len(parts) == 0:
        return geom if geom.is_valid else buffer(geom, 0.0)
    if len(parts) == 1:
        return parts[0]
    return MultiPolygon(parts)


def _merge_paths(paths: list[list[NDArray]]) -> list[Polygon]:
    if not paths:
        return []

    # If start and end paths can connect, merge them
    if len(paths) >= 2:
        first = paths[0]
        last = paths[-1]
        if first and last and np.allclose(first[0], last[-1], atol=1e-6):
            paths = [last + first[1:], *paths[1:-1]]

    result = []
    for path in paths:
        if len(path) < 3:
            continue
        arr = np.array(path)
        # Close ring if needed
        if not np.allclose(arr[0], arr[-1], atol=1e-6):
            arr = np.vstack([arr, arr[0]])
        try:
            poly = Polygon(arr)
            if not poly.is_valid:
                poly = buffer(poly, 0.0)
            # MultiPolygon results from buffer(0) are dropped on purpose:
            # keeping their parts makes the equator split "succeed" but loses
            # whole polar lobes of orbital swaths. The caller detects the
            # resulting no-progress split and falls back to pole routing.
            if not poly.is_empty and isinstance(poly, Polygon):
                result.append(poly)
        except Exception as e:
            logging.debug('Failed to create polygon from path: %s', e)
    return result


def _split_polygon_at_equator(geom: Polygon) -> list[Polygon]:
    """
    Split a polygon at the equator into northern and southern parts.

    This is needed for complex orbital footprints that cross the antimeridian
    multiple times in both hemispheres (e.g., S5P TROPOMI pole-to-pole orbits).

    The algorithm traces the polygon boundary, splitting at equator crossings
    to create separate north/south polygons that can be processed independently.

    Args:
        geom: Input Polygon

    Returns:
        List of Polygons (north and south parts)
    """
    coords = get_coordinates(geom)
    n = len(coords)

    north_paths: list[list[NDArray]] = []
    south_paths: list[list[NDArray]] = []
    current_north: list[NDArray] = []
    current_south: list[NDArray] = []

    for i in range(n):
        point = coords[i]
        lat = point[1]

        # Add to appropriate hemisphere
        if lat >= 0:
            current_north.append(point)
        if lat <= 0:
            current_south.append(point)

        # Check for equator crossing to next point
        if i < n - 1:
            next_lat = coords[i + 1, 1]

            # Crossing from north to south
            if lat > 0 and next_lat < 0:
                equator_lon = lon_cross_equator(point, coords[i + 1])
                equator_point = np.array([equator_lon, 0.0])
                current_north.append(equator_point)
                if current_north:
                    north_paths.append(current_north)
                    current_north = []
                current_south.append(equator_point)

            # Crossing from south to north
            elif lat < 0 and next_lat > 0:
                equator_lon = lon_cross_equator(point, coords[i + 1])
                equator_point = np.array([equator_lon, 0.0])
                current_south.append(equator_point)
                if current_south:
                    south_paths.append(current_south)
                    current_south = []
                current_north.append(equator_point)

    # Finalize remaining paths
    if current_north:
        north_paths.append(current_north)
    if current_south:
        south_paths.append(current_south)

    polygons = _merge_paths(north_paths) + _merge_paths(south_paths)
    return polygons if polygons else [geom]


def _rework_via_equator_split(
    geom: Polygon,
    *,
    count: int,
    depth: int,
) -> Polygon | MultiPolygon | None:
    """
    Split at the equator and rework each part recursively.

    ``_split_polygon_at_equator`` is not guaranteed to make progress: when
    ``_merge_paths`` cannot build a polygon from any traced path, it falls back
    to returning its input unchanged. Recursing on an unchanged part never
    terminates - S5P-style pole-to-pole footprints hit a ~1000 frame
    RecursionError - so parts equal to the input are dropped and the depth is
    bounded.

    Args:
        geom: Input Polygon
        count: Antimeridian crossing count of geom (for logging)
        depth: Current equator-split recursion depth

    Returns:
        Reworked geometry, or None if the split made no progress. None tells
        the caller to use the standard pole-routing path instead.
    """
    if depth >= _MAX_EQUATOR_SPLIT_DEPTH:
        logging.warning(
            'Equator split depth limit %d reached (count=%d), using pole routing',
            _MAX_EQUATOR_SPLIT_DEPTH,
            count,
        )
        return None

    parts = [part for part in _split_polygon_at_equator(geom) if not part.equals(geom)]
    if not parts:
        logging.warning(
            'Equator split made no progress (count=%d, depth=%d), using pole routing',
            count,
            depth,
        )
        return None

    reworked_parts: list[Polygon] = []
    for part in parts:
        reworked = _rework_antimeridian_polygon(part, _depth=depth + 1)  # Recursive
        if isinstance(reworked, MultiPolygon):
            reworked_parts.extend(reworked.geoms)
        elif isinstance(reworked, Polygon):
            reworked_parts.append(reworked)

    if not reworked_parts:
        return None
    merged = union_all(reworked_parts)
    return merged if isinstance(merged, Polygon | MultiPolygon) else None


def _rework_antimeridian_polygon(
    geom: Polygon,
    *,
    _depth: int = 0,
) -> Polygon | MultiPolygon:
    """
    Rework a polygon to handle antimeridian crossings.

    Implements the Polar Inclusive algorithm:
    1. For multi-cross with mixed hemispheres: split at equator first
    2. Insert pole routing points at every crossing
    3. If contains pole: return the reworked polygon (routes through pole)
    4. If NOT contains pole: split at antimeridian

    Args:
        geom: Input Polygon
        _depth: Internal equator-split recursion depth (see
            _rework_via_equator_split).

    Returns:
        Reworked geometry (Polygon if contains pole, MultiPolygon otherwise)
    """
    coords = get_coordinates(geom)

    # Step 1: Analyze crossings
    count, mixed, latitudes = _count_antimeridian_crossings(coords)

    if count == 0:
        return geom

    logging.debug(
        'Antimeridian analysis: count=%d, mixed=%s, latitudes=%s',
        count,
        mixed,
        latitudes,
    )

    # Step 2: Handle multi-cross with mixed hemispheres
    if count > 2 and mixed:
        if count % 2 == 1:
            # Odd crossings -> polygon contains a pole. Route all crossings
            # through the correct pole and let make_valid resolve the
            # self-intersections. The equator-split approach cannot be used
            # here because it creates gaps between the sub-polygons.
            logging.debug(
                'Multi-cross with mixed hemispheres and odd count=%d, '
                'processing directly (no equator split)',
                count,
            )
        else:
            # Even crossings -> no pole. Split at equator first, then
            # process each part recursively.
            logging.debug('Multi-cross with mixed hemispheres, splitting at equator')
            merged = _rework_via_equator_split(geom, count=count, depth=_depth)
            if merged is not None:
                return merged
            # Split made no progress - fall through to pole routing below

    # Step 3: Standard processing - detect crossings and insert pole points
    crossings = _detect_antimeridian_crossings(coords)
    if not crossings:
        return geom

    logging.debug('Detected %d crossing(s) at indices %s', len(crossings), crossings)

    # Step 4: Insert pole routing points at every crossing.
    # For odd crossings with mixed hemispheres, determine the correct pole
    # from the majority of crossing latitudes. The default heuristic (first
    # crossing latitude) fails when the first crossing is in the opposite
    # hemisphere from the pole the polygon actually contains.
    pole_sign: int | None = None
    if len(crossings) % 2 == 1 and mixed:
        n_positive = sum(
            1
            for ci in crossings
            if lat_cross_antimeridian(coords[ci], coords[ci + 1]) >= 0
        )
        pole_sign = 1 if n_positive > len(crossings) // 2 else -1
        logging.debug(
            'Odd crossings with mixed hemispheres: pole_sign=%d (positive_lats=%d/%d)',
            pole_sign,
            n_positive,
            len(crossings),
        )

    new_coords = _insert_pole_points_at_crossings(
        coords,
        crossings,
        pole_sign=pole_sign,
    )
    reworked = Polygon(new_coords)

    # Step 5: Determine pole containment.
    #
    # We use check_contains_pole on the *reworked* polygon. Although the
    # reworked polygon already has pole routing points inserted, the
    # stereographic-projection test is still reliable in practice - the only
    # known false-positive case was the S5P south sub-polygon produced by
    # the equator split (2 even crossings, both southern-hemisphere, routed
    # through the south pole). That case is now eliminated by the Step 2
    # bypass: odd mixed-hemisphere crossings skip the equator split entirely,
    # so the problematic sub-polygon is never created.
    #
    # Pure crossing-parity (odd = pole) is NOT reliable because some orbits
    # have vertices at exactly +/-180 longitude, which masks a real crossing
    # and produces a false odd count (e.g. Sentinel-6).
    pole = check_contains_pole(reworked)

    if pole:
        logging.debug('Footprint contains %s pole, keeping polar routing', pole)
        if not reworked.is_valid:
            reworked = buffer(reworked, 0.0)
        return reworked

    logging.debug('Footprint does not contain pole, splitting at antimeridian')
    return _split_at_antimeridian(reworked)


def _is_simple_rectangle(geom: Polygon | MultiPolygon) -> bool:
    """Check whether geom is a simple axis-aligned bounding box.

    CLMS extents (e.g. ``globe_80s80n``) are plain lon/lat rectangles that can
    legitimately cover most of the globe (>40000 deg²). They fill their own
    bounding box exactly (collinear edge midpoints included) and have at most 6
    unique vertices. Orbital footprints (S5P, etc.) are scalloped swaths with
    many vertices that never equal their bounding box, so they are not matched.

    Used to stop ``_fix_inverted_polygon`` from misclassifying a large-but-valid
    rectangle as an inverted footprint and erasing it into its complement.
    """
    if not isinstance(geom, Polygon) or geom.interiors:
        return False
    # <=6 unique vertices: 4-corner bbox, or 6 when bbox_to_wkt adds edge midpoints
    if len(get_coordinates(geom)) - 1 > 6:
        return False
    return symmetric_difference(geom, box(*geom.bounds)).area < WORLD_EQUIV_TOLERANCE


def _fix_inverted_polygon(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    """
    Fix inverted polygon where interior/exterior are swapped.

    When a polygon covers more than half of Earth's surface (area > 40000),
    it indicates that the interior/exterior identification is inverted.
    The fix is to take the complement: world_box - polygon.

    This typically happens with:
    - Sentinel-5P orbital footprints crossing antimeridian
    - Other wide-swath sensors with complex geometry

    Args:
        geom: Input geometry

    Returns:
        Fixed geometry (complement if inverted, original otherwise)
    """
    if geom.area > HALF_EARTH_THRESHOLD:
        # Large axis-aligned rectangles (CLMS extents) are valid, not inverted.
        if _is_simple_rectangle(geom):
            logging.debug(
                'Polygon is a simple rectangle (area=%.1f) — keeping as-is',
                geom.area,
            )
            return geom
        world_box = box(-180, -90, 180, 90)
        repaired = buffer(geom, 0.0)
        # Genuinely-global footprints: equal to the world box ⇒ complement is
        # empty, so keep the polygon as-is instead of erasing it.
        if symmetric_difference(world_box, repaired).area < WORLD_EQUIV_TOLERANCE:
            logging.debug(
                'Polygon equals world box (area=%.1f) — keeping as-is',
                geom.area,
            )
            return geom
        logging.info(
            'Detected inverted polygon (area=%.1f > %d), taking complement',
            geom.area,
            HALF_EARTH_THRESHOLD,
        )
        fixed = difference(world_box, repaired)
        if isinstance(fixed, Polygon | MultiPolygon):
            return fixed
        # Fallback: wrap in MultiPolygon if GeometryCollection
        return geom

    return geom


def _has_dual_pole_routing(coords: NDArray) -> bool:
    """Check whether a ring carries pole routing points at BOTH poles."""
    threshold = EPSILON * 100  # ~1e-6
    on_meridian = np.abs(np.abs(coords[:, 0]) - LON_MAX) < threshold
    at_north = on_meridian & (np.abs(coords[:, 1] - LAT_MAX) < threshold)
    at_south = on_meridian & (np.abs(coords[:, 1] + LAT_MAX) < threshold)
    return bool(at_north.any() and at_south.any())


def _split_pole_routed_polygon(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    """
    Split dual-pole routed polygons into a MultiPolygon.

    S5P full-orbit products route through BOTH poles via (+/-LON_MAX, +/-LAT_MAX).
    While valid in Shapely, OpenSearch cannot tessellate that topology, so every
    dual-pole part is cut into an eastern and a western half separated by a tiny
    gap. Single-pole products (S3, S6) pass through unchanged.

    The polar caps are kept. For a swath that genuinely passes over a pole they
    are real coverage, not routing artifacts - clipping them away dropped 6% of
    the footprint area on S5P full-orbit products.

    Args:
        geom: Input geometry

    Returns:
        Original geometry OR split MultiPolygon if dual-pole routing detected
    """
    gap = 1e-8
    halves = (
        box(-LON_MAX, -LAT_MAX, -gap, LAT_MAX),  # west
        box(gap, -LAT_MAX, LON_MAX, LAT_MAX),  # east
    )

    parts: list[Polygon] = []
    split_any = False

    for poly in geom.geoms if isinstance(geom, MultiPolygon) else (geom,):
        if not _has_dual_pole_routing(get_coordinates(poly)):
            parts.append(poly)
            continue

        split_any = True
        for half in halves:
            part = poly.intersection(half)
            if part.is_empty:
                continue
            if isinstance(part, Polygon):
                parts.append(part)
            elif isinstance(part, MultiPolygon):
                parts.extend(part.geoms)
            elif isinstance(part, GeometryCollection):
                parts.extend(g for g in part.geoms if isinstance(g, Polygon))

    if not split_any or not parts:
        return geom

    result = MultiPolygon(parts) if len(parts) > 1 else parts[0]
    logging.debug('Split into %d part(s), total area=%.1f', len(parts), result.area)

    return result


def _densify_lon_jump_ring(coords: NDArray, max_lon_step: float) -> NDArray | None:
    """Subdivide ring segments with |Δlon| > 180. Returns None when unchanged."""
    out: list[NDArray] = []
    changed = False
    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        out.append(p1)
        lon_delta = abs(float(p2[0]) - float(p1[0]))
        if lon_delta > 180:
            changed = True
            steps = int(np.ceil(lon_delta / max_lon_step))
            out.extend(
                p1 + (p2 - p1) * t for t in np.linspace(0.0, 1.0, steps + 1)[1:-1]
            )
    if not changed:
        return None
    out.append(coords[-1])
    return np.array(out)


def _densify_polygon_bridges(geom: Polygon, max_lon_step: float) -> Polygon:
    shell_coords = get_coordinates(geom.exterior)
    shell = _densify_lon_jump_ring(shell_coords, max_lon_step)

    holes: list[NDArray] = []
    holes_changed = False
    for interior in geom.interiors:
        ring = get_coordinates(interior)
        densified = _densify_lon_jump_ring(ring, max_lon_step)
        if densified is None:
            holes.append(ring)
        else:
            holes.append(densified)
            holes_changed = True

    if shell is None and not holes_changed:
        return geom
    return Polygon(shell if shell is not None else shell_coords, holes)


def densify_pole_bridges(
    geom: Polygon | MultiPolygon,
    *,
    max_lon_step: float = 90.0,
) -> Polygon | MultiPolygon:
    """Subdivide ring segments whose longitude jump exceeds 180 degrees.

    Pole routing leaves a horizontal bridge at +/-LAT_MAX spanning the full
    longitude range (LON_MAX -> -LON_MAX). The planar shape is unchanged by
    subdivision, but catalog validators (sfeos) and OpenSearch reject rings
    where consecutive vertices jump more than 180 degrees in longitude, as
    they read it as an improper antimeridian crossing (RFC 7946 3.1.9).

    Args:
        geom: Input geometry.
        max_lon_step: Maximum longitude span of any subdivided segment.

    Returns:
        Geometry with compliant rings (the input object when already compliant).
    """
    if isinstance(geom, MultiPolygon):
        parts = [_densify_polygon_bridges(p, max_lon_step) for p in geom.geoms]
        if all(new is old for new, old in zip(parts, geom.geoms, strict=True)):
            return geom
        return MultiPolygon(parts)
    if isinstance(geom, Polygon) and not geom.is_empty:
        return _densify_polygon_bridges(geom, max_lon_step)
    return geom


__all__ = [
    '_count_antimeridian_crossings',
    '_detect_antimeridian_crossings',
    '_fix_inverted_polygon',
    '_insert_pole_points_at_crossings',
    '_is_simple_rectangle',
    '_normalize_lon_to_360',
    '_rework_antimeridian_polygon',
    '_split_at_antimeridian',
    '_split_pole_routed_polygon',
    '_split_polygon_at_equator',
    'check_contains_pole',
    'densify_pole_bridges',
    'lat_cross_antimeridian',
    'lon_cross_equator',
]
