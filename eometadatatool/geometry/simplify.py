import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, overload

from shapely import (
    MultiPolygon,
    count_coordinates,
    multipolygons,
    simplify,
    symmetric_difference,
)

from eometadatatool.geometry.projections import _cart2ease, _cart2geod, _geod2cart

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True, slots=True)
class SimplifyConfig:
    max_area_change: float = 0.05
    max_area_change_tol: float = 0.01
    min_tolerance_range: float = 50
    max_tolerance_range: float = 100000
    max_iter: int = 8


DEFAULT_SIMPLIFY_CONFIG = SimplifyConfig()


def _resolve_simplify_config(
    *,
    config: SimplifyConfig | None,
    max_area_change: float | None,
    max_area_change_tol: float | None,
    min_tolerance_range: float | None,
    max_tolerance_range: float | None,
    max_iter: int | None,
) -> SimplifyConfig:
    resolved = config or DEFAULT_SIMPLIFY_CONFIG

    if max_area_change is not None:
        resolved = replace(resolved, max_area_change=max_area_change)
    if max_area_change_tol is not None:
        resolved = replace(resolved, max_area_change_tol=max_area_change_tol)
    if min_tolerance_range is not None:
        resolved = replace(resolved, min_tolerance_range=min_tolerance_range)
    if max_tolerance_range is not None:
        resolved = replace(resolved, max_tolerance_range=max_tolerance_range)
    if max_iter is not None:
        resolved = replace(resolved, max_iter=max_iter)

    return resolved


def _simplify_multipolygon(
    geometry: MultiPolygon,
    *,
    config: SimplifyConfig,
) -> MultiPolygon:
    return multipolygons([
        simplify_geometry(poly, config=config)
        for poly in geometry.geoms
    ])


def _area_diff(
    footprint,
    *,
    ref_area: float,
    max_area_change: float,
    tolerance: float,
) -> tuple[float, int]:
    """Get area_change deviation and coordinate count for tolerance."""
    simplified = simplify(footprint, tolerance)
    delta = symmetric_difference(footprint, simplified)
    diff = (_cart2ease(delta).area / ref_area) - max_area_change
    return diff, count_coordinates(simplified)


@overload
def simplify_geometry[T: BaseGeometry](
    geometry: T,
    max_area_change: float = 0.05,
    max_area_change_tol: float = 0.01,
    min_tolerance_range: float = 50,
    max_tolerance_range: float = 100000,
    max_iter: int = 8,
) -> T: ...


@overload
def simplify_geometry[T: BaseGeometry](
    geometry: T,
    max_area_change: float | None = None,
    max_area_change_tol: float | None = None,
    min_tolerance_range: float | None = None,
    max_tolerance_range: float | None = None,
    max_iter: int | None = None,
    *,
    config: SimplifyConfig,
) -> T: ...


def simplify_geometry[T: BaseGeometry](
    geometry: T,
    max_area_change: float | None = None,
    max_area_change_tol: float | None = None,
    min_tolerance_range: float | None = None,
    max_tolerance_range: float | None = None,
    max_iter: int | None = None,
    *,
    config: SimplifyConfig | None = None,
) -> T:
    config = _resolve_simplify_config(
        config=config,
        max_area_change=max_area_change,
        max_area_change_tol=max_area_change_tol,
        min_tolerance_range=min_tolerance_range,
        max_tolerance_range=max_tolerance_range,
        max_iter=max_iter,
    )

    # don't simplify small geometries
    num_coords = count_coordinates(geometry)
    if num_coords <= 10:
        return geometry

    # in case of multipolygon, simplify each polygon separately
    if isinstance(geometry, MultiPolygon):
        return _simplify_multipolygon(geometry, config=config)  # type: ignore[return-value]

    footprint = _geod2cart(geometry)
    ref_area = _cart2ease(footprint).area

    # don't simplify geometries without area
    if not ref_area:
        return geometry

    # early exit for trivial cases
    b = config.max_tolerance_range
    fb, b_num = _area_diff(
        footprint,
        ref_area=ref_area,
        max_area_change=config.max_area_change,
        tolerance=b,
    )
    if fb <= 0:
        logging.debug(
            'simplify_adaptive: max_tolerance_range %g too low (trivial ok)',
            b,
        )
        return _cart2geod(simplify(footprint, b)) if b_num < num_coords else geometry

    a = config.min_tolerance_range
    fa, a_num = _area_diff(
        footprint,
        ref_area=ref_area,
        max_area_change=config.max_area_change,
        tolerance=a,
    )
    if fa >= 0:
        logging.debug(
            'simplify_adaptive: min_tolerance_range %g too high (not ok)',
            a,
        )
        return geometry

    a_weight = b_weight = 1
    prev_adjusted_is_a: bool | None = None

    i = 0
    for i in range(1, config.max_iter + 1):
        # Compute the candidate tolerance using the Illinois update formula
        # https://en.wikipedia.org/wiki/Regula_falsi#The_Illinois_algorithm
        fa_weighted = fa * a_weight
        fb_weighted = fb * b_weight
        c = (a * fb_weighted - b * fa_weighted) / (fb_weighted - fa_weighted)
        fc, c_num = _area_diff(
            footprint,
            ref_area=ref_area,
            max_area_change=config.max_area_change,
            tolerance=c,
        )
        logging.debug(
            'simplify_adaptive: step=%d, c=%g, f(c)=%g, c_num=%d',
            i,
            c,
            fc,
            c_num,
        )

        # early exit if we hit acceptable precision
        if abs(fc) < config.max_area_change_tol:
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


__all__ = ['DEFAULT_SIMPLIFY_CONFIG', 'SimplifyConfig', 'simplify_geometry']
