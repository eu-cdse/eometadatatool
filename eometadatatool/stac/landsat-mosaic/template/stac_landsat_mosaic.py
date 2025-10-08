import datetime
import re
from calendar import monthrange
from typing import Any

from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
)
from eometadatatool.stac.framework.stac_bands import LANDSAT_MOSAIC_Bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem


def create_title(key_relative: str) -> str:
    if re.match(r"^B\d{2}", key_relative):
        return key_relative.replace('B0', 'Band ')
    else:
        return key_relative.replace('_', ' ').capitalize()

def extent_wkt_from_filename(filename):
    pattern = r'_(\d{2})([NS])(\d{3})([EW])_'
    match = re.search(pattern, filename)
    if not match:
        return None
    lat_val = int(match.group(1))
    lat_dir = match.group(2)
    lon_val = int(match.group(3))
    lon_dir = match.group(4)

    lat = float(lat_val) if lat_dir == 'N' else -float(lat_val)
    lon = float(lon_val) if lon_dir == 'E' else -float(lon_val)

    min_lon = lon
    min_lat = lat
    max_lon = lon + 1 if lon_dir == 'E' else lon - 1
    max_lat = lat + 1 if lat_dir == 'N' else lat - 1

    min_lon, max_lon = sorted([min_lon, max_lon])
    min_lat, max_lat = sorted([min_lat, max_lat])

    wkt = (
        f'POLYGON (({min_lon} {min_lat}, {min_lon} {max_lat}, {max_lon} {max_lat}, '
        f'{max_lon} {min_lat}, {min_lon} {min_lat}))'
    )
    return wkt

def convert_coordinate_string(filename: str) -> str | None:
    match = re.search(r'(\d{2}[NS]\d{3}[EW])', filename)
    if not match:
        return None
    coord = match.group(1)
    lat = coord[:3]
    lon = coord[3:]
    lat_new = lat[2] + lat[:2]
    lon_new = lon[3] + lon[:3]

    return f'CDEM-{lat_new}{lon_new}'


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    prod_id: str = attr['identifier']
    try:
        prod_year = int(prod_id.split('_')[2])
        start_month = int(prod_id.split('_')[3].split('-')[0])
    except Exception as ex:
        raise ValueError('Cannot parse date from identifier') from ex

    start_datetime = datetime.datetime(year=prod_year, month=start_month, day=1, tzinfo=datetime.UTC)
    end_datetime = datetime.datetime(year=prod_year, month=start_month+1, day=monthrange(prod_year, start_month+1)[1], hour=23, minute=59, second=59, tzinfo=datetime.UTC)

    props = {
        'start_datetime': start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'end_datetime': end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        'datetime': None,
        'gsd': 30,
        'constellation': 'Landsat',
        'instruments': ['TM', 'ETM+', 'OLI', 'TIRS'],
        'product:type': 'landsat_mosaic',
        'proj:code': 'EPSG:4326',
        'processing:version': re.search(r'V(\d+\.\d+\.\d+)', attr['identifier']).group(1),
        'processing:level': 'L2'
    }

    grid_code = convert_coordinate_string(attr['identifier'])
    if grid_code:
        props['grid:code'] = grid_code

    assets = {}
    for value in attr['s3_scene'].subkeys.values():
        asset = {
            value.key_relative[:-9]: CloudOptimizedGeoTIFFAsset(
                path=str(value.path).replace('s3:/', 's3://'),
                title=create_title(value.key_relative[:-9]),
                size=value.size,
                include_other_alternates=False,
            )
        }
        band = LANDSAT_MOSAIC_Bands.get(value.key_relative[:-9])
        if band:
            asset[value.key_relative[:-9]].extra = {
                'bands': [LANDSAT_MOSAIC_Bands[value.key_relative[:-9]]]
            }
        if value.key_relative[:-9] == 'clear_sky_mask':
            asset[value.key_relative[:-9]].roles = [*asset[value.key_relative[:-9]].roles, 'mask']
        assets.update(asset)
    item = STACItem(
        path=attr['filepath'],
        odata=None,
        collection='opengeohub-landsat-bimonthly-mosaic-v1.0.1',
        identifier=attr['identifier'],
        coordinates=extent_wkt_from_filename(attr['filename']),
        links=[],
        assets=assets,
        extensions=(
            StacExtension.PROJECTION,
            StacExtension.ALTERNATE,
            StacExtension.TIMESTAMP,
            StacExtension.AUTHENTICATION,
            StacExtension.STORAGE,
            StacExtension.GRID
        ),
        extra=props,
    )

    return await item.generate()
