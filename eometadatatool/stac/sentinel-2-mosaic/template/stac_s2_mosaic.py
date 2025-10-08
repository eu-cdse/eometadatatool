from io import StringIO
from typing import Any

import numpy as np

from eometadatatool.dlc import (
    coordinates_to_wkt,
    get_metadata_from_userdata,
    get_odata_id,
    reproject_bbox,
)
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
    ZipperLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    json_data = await get_metadata_from_userdata(attr['filepath'])

    coords_arr = np.asarray(json_data.coords, np.float64)
    coords_arr = coords_arr.reshape(-1, 2)  # flatten rings
    coords_arr = coords_arr[:, [1, 0]]  # change (lon,lat) into (lat,lon)

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
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'userdata': ProductManifestAsset(
            path=f'{item_path}/userdata.json',
            title='Product Odata Response File (JSON)',
            size=attr['userdata.json:size'],
        )
    }

    s2_mosaic_bands = ['B02', 'B03', 'B04', 'B08']
    proj_bbox = reproject_bbox(coords_arr, json_data.crs)
    for band_id, band in zip(
        s2_mosaic_bands, generate_bands(S2_Bands, s2_mosaic_bands), strict=True
    ):
        extra = {
            'bands': (band,),
            'data_type': 'int16',
            'nodata': -32768,
            'gsd': 10,
            'proj:shape': [10008, 10008],
            'proj:bbox': proj_bbox,
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
            'proj:bbox': proj_bbox,
        },
    )

    with StringIO() as buf:
        np.savetxt(buf, coords_arr, fmt='%s', delimiter=' ', newline=' ')
        coordinates = coordinates_to_wkt((buf.getvalue(),))

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
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
            StacExtension.PRODUCT,
            StacExtension.PROCESSING,
        ),
        extra=props,
    )

    return await item.generate()
