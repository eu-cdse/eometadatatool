"""Compatibility facade for geometry utilities.

Public API remains available at this module path:
- ``normalize_geometry`` -> ``eometadatatool.geometry.normalize``
- ``simplify_geometry`` -> ``eometadatatool.geometry.simplify``
- ``average_angles`` stays implemented in this facade

Legacy internals were moved to dedicated modules:
- constants -> ``eometadatatool.geometry.constants``
- CRS/projections -> ``eometadatatool.geometry.projections``
- antimeridian/pole routing -> ``eometadatatool.geometry.antimeridian``
"""

import numpy as np
from numpy.typing import NDArray

from eometadatatool.geometry.antimeridian import densify_pole_bridges
from eometadatatool.geometry.constants import (
    EPSILON,
    HALF_EARTH_THRESHOLD,
    LAT_MAX,
    LON_MAX,
)
from eometadatatool.geometry.normalize import normalize_geometry
from eometadatatool.geometry.simplify import simplify_geometry


def average_angles[T: NDArray[np.floating]](angles: T) -> T:
    """Average angles in collections using circular mean.

    Computes the circular mean of angles, which correctly handles the wraparound
    at 0/360 degrees. Uses the atan2 method for numerical stability.

    Args:
        angles: Array of shape (N, K), where N is the number of collections
            and K is the number of observations. Values in degrees.

    Returns:
        Array of shape (N,) with averaged angles in degrees, range [0, 360).
    """
    if not angles.size:
        return angles
    radians = np.radians(angles)
    x = np.sum(np.cos(radians), axis=1)
    y = np.sum(np.sin(radians), axis=1)
    return np.degrees(np.atan2(y, x)) % 360


__all__ = [
    'EPSILON',
    'HALF_EARTH_THRESHOLD',
    'LAT_MAX',
    'LON_MAX',
    'average_angles',
    'densify_pole_bridges',
    'normalize_geometry',
    'simplify_geometry',
]
