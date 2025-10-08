import re
from typing import Any

from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.utils import ensure_iso_datetime


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    xml_name: str = f'{attr['filename'].replace('COG_', '').replace('_DEM', '')}.xml'
    gsd = None
    match attr['resolution']:
        case 10:
            gsd = 30
        case 30:
            gsd = 90

    coor_code = re.search(r'([NS]\d{2})_00_([EW]\d{3})_00', attr['filename'])
    grid_code = f'CDEM-{coor_code.group(1)}{coor_code.group(2)}'

    prod_type = f'DGE_{gsd}-COG'

    props = {
        'start_datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'end_datetime': ensure_iso_datetime(attr['endingDateTime']),
        'sar:polarizations': [attr['polarisation']],
        'datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'created': ensure_iso_datetime(attr[f'{xml_name}:last_modified']),
        'gsd': gsd,
        'proj:code': 'EPSG:' + attr['projCode'],
        'product:type': prod_type,
        'processing:version': attr['processingVersion'],
        'grid:code': grid_code,
    }

    assets = {
        'data': CloudOptimizedGeoTIFFAsset(
            path=f'{attr['filepath']}/{attr['filename']}.tif',
            title=f'{attr['filename']}.tif',
            include_other_alternates=False
        ),
        'manifest': XMLAsset(
            path=f'{attr['filepath']}/{xml_name}',
            title='manifest',
            roles=['metadata'],
            include_other_alternates=False
        )
    }

    item = STACItem(
        path=attr['filepath'],
        odata=None,
        collection=f'cop-dem-glo-{gsd}-dged-cog',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=[],
        assets=assets,
        extensions=(
            StacExtension.PROJECTION,
            StacExtension.ALTERNATE,
            StacExtension.TIMESTAMP,
            StacExtension.AUTHENTICATION,
            StacExtension.SAR,
            StacExtension.STORAGE,
            StacExtension.GRID,
        ),
        extra=props,
    )

    return await item.generate()
