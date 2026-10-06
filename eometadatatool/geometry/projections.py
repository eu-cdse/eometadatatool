from functools import partial

from pyproj import Transformer
from shapely import Point
from shapely.ops import transform as transform_ops

_wgs84_to_polar_north = Transformer.from_crs(
    'EPSG:4326',
    '+proj=stere +lat_0=90 +lat_ts=75',
    always_xy=True,
).transform

_wgs84_to_polar_south = Transformer.from_crs(
    'EPSG:4326',
    '+proj=stere +lat_0=-90 +lat_ts=-75',
    always_xy=True,
).transform

_north_pole_projected = transform_ops(_wgs84_to_polar_north, Point(0, 90))
_south_pole_projected = transform_ops(_wgs84_to_polar_south, Point(0, -90))

_cart2ease = partial(
    transform_ops,
    Transformer.from_crs(4087, 'ESRI:54009', always_xy=True).transform,
)

_cart2geod = partial(
    transform_ops,
    Transformer.from_crs(4087, 4326, always_xy=True).transform,
)

_geod2cart = partial(
    transform_ops,
    Transformer.from_crs(4326, 4087, always_xy=True).transform,
)

__all__ = [
    '_cart2ease',
    '_cart2geod',
    '_geod2cart',
    '_north_pole_projected',
    '_south_pole_projected',
    '_wgs84_to_polar_north',
    '_wgs84_to_polar_south',
]
