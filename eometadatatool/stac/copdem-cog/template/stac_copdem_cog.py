import re
from typing import Any

from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.utils import ensure_iso_datetime, generate_product_uuid

from eometadatatool.flags import is_no_private, is_hidden


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

    extensions: list[StacExtension] = [
        StacExtension.PROJECTION,
        StacExtension.ALTERNATE,
        StacExtension.TIMESTAMP,
        StacExtension.AUTHENTICATION,
        StacExtension.STORAGE,
        StacExtension.GRID,
    ]

    props = {
        'start_datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'end_datetime': ensure_iso_datetime(attr['endingDateTime']),
        'datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'created': ensure_iso_datetime(attr[f'{xml_name}:last_modified']),
        'gsd': gsd,
        'proj:code': 'EPSG:' + attr['projCode'],
        'product:type': prod_type,
        'processing:version': attr['processingVersion'],
        'grid:code': grid_code,
    }

    polarisation = attr.get('polarisation', 'UNDEFINED')
    if polarisation and polarisation != 'UNDEFINED':
        props['sar:polarizations'] = [polarisation]
        extensions.append(StacExtension.SAR)

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        props['_private']['product_uuid'] = generate_product_uuid(attr['identifier'])
        props['_private']['product_name'] = attr['identifier']
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

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
        assets=assets,
        extensions=extensions,
        extra=props,
    )

    return await item.generate()
