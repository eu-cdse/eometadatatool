import logging
from functools import partial
from itertools import product
from typing import TYPE_CHECKING, overload

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer
from shapely import (
    GeometryCollection,
    MultiPolygon,
    Polygon,
    box,
    count_coordinates,
    make_valid,
    multipolygons,
    prepare,
    simplify,
    symmetric_difference,
    transform,
    union_all,
)
from shapely.ops import transform as transform_ops

from eometadatatool.flags import is_no_footprint_facility, is_strict

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry


def average_angles[T: NDArray[np.floating]](angles: T) -> T:
    """Average angles in collections.

    :param angles: Array of shape (N, K), where N is the number of collections and K is the number of observations.
    :return: Array of shape (N,).
    """
    if not angles.size:
        return angles
    radians = np.radians(angles)
    x = np.sum(np.cos(radians), axis=1)
    y = np.sum(np.sin(radians), axis=1)
    return np.degrees(np.atan2(y, x)) % 360


@overload
def normalize_geometry(geom: Polygon) -> Polygon | MultiPolygon: ...
@overload
def normalize_geometry(geom: MultiPolygon) -> MultiPolygon: ...
def normalize_geometry(geom: Polygon | MultiPolygon) -> Polygon | MultiPolygon:
    """Normalize and simplify a geometry, so coordinates are within the [-180, 180] and [-90, 90] bounds."""
    if not is_no_footprint_facility():
        from eometadatatool.footprint_facility import (
            AlreadyReworkedPolygonError,
            rework_to_polygon_geometry,
        )

        try:
            return rework_to_polygon_geometry(geom)  # type: ignore
        except AlreadyReworkedPolygonError:
            return geom

    if not geom.is_valid:
        if is_strict():
            raise ValueError(f'normalize_geometry: invalid geometry {geom.wkt!r})')
        geom = make_valid(geom, method='structure', keep_collapsed=False)  # type: ignore

    min_x, min_y, max_x, max_y = geom.bounds
    if not (
        -180 <= min_x <= 180
        and -90 <= min_y <= 90
        and -180 <= max_x <= 180
        and -90 <= max_y <= 90
    ):
        # Prepare geometry for faster intersection checks
        prepare(geom)

        min_x_step = int((min_x + 180) // 360)
        max_x_step = int((max_x + 180) // 360)
        min_y_step = int((min_y + 90) // 180)
        max_y_step = int((max_y + 90) // 180)
        geoms: list[Polygon | MultiPolygon] = []

        for x_step, y_step in product(
            range(min_x_step, max_x_step + 1), range(min_y_step, max_y_step + 1)
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
                if flip_y:
                    t = lambda a, offset=(x_offset, y_offset): (a - offset) * -1
                else:
                    t = lambda a, offset=(x_offset, y_offset): a - offset
                part = transform(part, t)

            geoms.extend(
                g
                for g in (
                    part.geoms if isinstance(part, GeometryCollection) else (part,)
                )
                if isinstance(g, Polygon | MultiPolygon)
            )

        geom = union_all(geoms)  # type: ignore

    return geom


_cart2ease = partial(
    transform_ops, Transformer.from_crs(4087, 'ESRI:54009', always_xy=True).transform
)
"""Convert metric coordinates to equal-area (Mollweide)"""

_cart2geod = partial(
    transform_ops, Transformer.from_crs(4087, 4326, always_xy=True).transform
)
"""Convert metric coordinates to geographic (lon/lat)"""

_geod2cart = partial(
    transform_ops, Transformer.from_crs(4326, 4087, always_xy=True).transform
)
"""Convert geographic (lon/lat) to metric coordinates"""


def simplify_geometry[T: BaseGeometry](
    geometry: T,
    max_area_change: float = 0.05,
    max_area_change_tol: float = 0.01,
    min_tolerance_range: float = 50,
    max_tolerance_range: float = 100000,
    max_iter: int = 8,
) -> T:
    # don't simplify small geometries
    num_coords = count_coordinates(geometry)
    if num_coords <= 10:
        return geometry

    # in case of multipolygon, simplify each polygon separately
    if isinstance(geometry, MultiPolygon):
        return multipolygons([
            simplify_geometry(
                poly,
                max_area_change,
                max_area_change_tol,
                min_tolerance_range,
                max_tolerance_range,
                max_iter,
            )
            for poly in geometry.geoms
        ])  # type: ignore

    footprint = _geod2cart(geometry)
    ref_area = _cart2ease(footprint).area

    # don't simplify geometries without area
    if not ref_area:
        return geometry

    def area_diff(tol: float) -> tuple[float, int]:
        """Get the area_change deviation from the max_area_change, and the number of coordinates in the simplified geometry."""
        simplified = simplify(footprint, tol)
        delta = symmetric_difference(footprint, simplified)
        diff = (_cart2ease(delta).area / ref_area) - max_area_change
        return diff, count_coordinates(simplified)

    # early exit for trivial cases
    b = max_tolerance_range
    fb, b_num = area_diff(b)
    if fb <= 0:
        logging.debug(
            'simplify_adaptive: max_tolerance_range %g is too low (trivial acceptable)',
            b,
        )
        return _cart2geod(simplify(footprint, b)) if b_num < num_coords else geometry

    a = min_tolerance_range
    fa, a_num = area_diff(a)
    if fa >= 0:
        logging.debug(
            'simplify_adaptive: min_tolerance_range %g is too high (trivial not acceptable)',
            a,
        )
        return geometry

    a_weight = b_weight = 1
    prev_adjusted_is_a: bool | None = None

    i = 0
    for i in range(1, max_iter + 1):
        # Compute the candidate tolerance using the Illinois update formula
        # https://en.wikipedia.org/wiki/Regula_falsi#The_Illinois_algorithm
        fa_weighted = fa * a_weight
        fb_weighted = fb * b_weight
        c = (a * fb_weighted - b * fa_weighted) / (fb_weighted - fa_weighted)
        fc, c_num = area_diff(c)
        logging.debug(
            'simplify_adaptive: step=%d, c=%g, f(c)=%g, c_num=%d', i, c, fc, c_num
        )

        # early exit if we hit acceptable precision
        if abs(fc) < max_area_change_tol:
            optimal_tol = c
            break

        if fc < 0:
            a, fa, a_num, a_weight = c, fc, c_num, 1
            if prev_adjusted_is_a is True:
                b_weight = 0.5
            prev_adjusted_is_a = True
        else:
            b, fb, b_num, b_weight = c, fc, c_num, 1
            if prev_adjusted_is_a is False:
                a_weight = 0.5
            prev_adjusted_is_a = False

        # early exit if no further improvement is possible
        if a_num - b_num <= 1:
            optimal_tol = a if (abs(fa) < abs(fb)) else b
            break
    else:
        # if we run out of iterations, perform a final linear approximation
        optimal_tol = a - (fa / (fb - fa)) * (b - a)

    logging.debug('simplify_adaptive: optimal_tol=%g after %d steps', optimal_tol, i)
    return _cart2geod(simplify(footprint, optimal_tol))
