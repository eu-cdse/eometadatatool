from io import StringIO
from typing import Any

import numpy as np

from eometadatatool.dlc import (
    coordinates_to_wkt,
    get_metadata_from_userdata,
    get_odata_id,
)
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_bands import S2_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    json_data = await get_metadata_from_userdata(attr['filepath'])

    coords_arr = np.asarray(json_data.coords, np.float64)
    coords_arr = coords_arr.reshape(-1, 2)
    coords_arr = coords_arr[:, [1, 0]]

    props = {
        'datetime': json_data.start_isodate,
        'start_datetime': json_data.start_isodate,
        'end_datetime': json_data.end_isodate,
        'constellation': 'sentinel-2',
        'instruments': ['msi'],
        'processing:level': 'L3',
        'processing:facility': 'Copernicus Data Space Ecosystem',
        'product:type': 'S2MSI_L3__MCQ',
        'product:timeliness': 'P3M',
        'gsd': 10,
        'grid:code': 'MGRS-' + json_data.grid_code,
        'proj:code': json_data.crs,
    }

    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']

    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path, zipper=extended_private_data)

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        props['_private']['product_uuid'] = odata.id
        props['_private']['product_name'] = odata.name
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

        if extended_private_data:
            props['_private']['brands'] = odata.zipper_data

    assets: dict[str, STACAsset] = {
        'userdata': ProductManifestAsset(
            path=f'{item_path}/userdata.json',
            title='Product Odata Response File (JSON)',
            size=attr['userdata.json:size'],
        )
    }

    band_info = {}

    s2_mosaic_bands = ['B02', 'B03', 'B04', 'B08']

    for band_id, band in zip(
        s2_mosaic_bands, generate_bands(S2_Bands, s2_mosaic_bands), strict=True
    ):
        extra = {
            'bands': (band,),
            'data_type': 'int16',
            'nodata': -32768,
            'gsd': 10,
            'proj:shape': [10008, 10008],
            **band_info.get(band_id, {}),
        }

        assets[band_id] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{band_id}.tif',
            title=f'{band["description"]}',
            size=attr[f'{band_id}.tif:size'],
            extra=extra,
        )

    assets['observations'] = CloudOptimizedGeoTIFFAsset(
        path=f'{item_path}/observations.tif',
        title='Observations',
        description='Number of valid observations for each pixel',
        size=attr['observations.tif:size'],
        extra={
            'data_type': 'uint16',
            'nodata': 0,
            'gsd': 10,
            'proj:shape': [10008, 10008],
            **band_info.get('OBSERVATIONS', {}),
        },
    )

    with StringIO() as buf:
        np.savetxt(buf, coords_arr, fmt='%s', delimiter=' ', newline=' ')
        coordinates = coordinates_to_wkt((buf.getvalue(),))

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='sentinel-2-global-mosaics',
        identifier=json_data.name,
        coordinates=coordinates,
        links=links,
        product_asset_name='Product',
        assets=assets,
        extensions=(
            StacExtension.TIMESTAMP,
            StacExtension.PROJECTION,
            StacExtension.PRODUCT,
            StacExtension.PROCESSING,
            StacExtension.GRID,
        ),
        extra=props,
    )

    return await item.generate()
