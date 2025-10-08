from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_bands import S1_Pols, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
    ZipperLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    parts = attr['filename'].split('_')
    mode = parts[1]
    mgrs = parts[5]
    polarizations = {'IW': ['VH', 'VV'], 'DH': ['HH', 'HV']}

    extensions = {
        StacExtension.SAR,
        StacExtension.TIMESTAMP,
        StacExtension.PRODUCT,
        StacExtension.PROCESSING,
    }

    props = {
        'datetime': attr['contentDate:Start'],
        'start_datetime': attr['contentDate:Start'],
        'end_datetime': attr['contentDate:End'],
        'created': attr['originDate'],
        'published': attr['publicationDate'],
        'updated': attr['modificationDate'],
        'constellation': 'sentinel-1',
        'instruments': ['sar'],
        'processing:level': 'L3',
        'processing:facility': attr['processingCenter'],
        'product:type': attr['productType'],
        'product:timeliness': 'P1M',
        'sar:instrument_mode': mode,
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.405,
        'sar:polarizations': polarizations[mode],
        'gsd': 20 if mode == 'IW' else 40,
    }

    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    if mgrs:
        grid_epsg = STACItem.from_mgrs(mgrs, extensions)
        props.update({'grid:code': grid_epsg['grid:code']})

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'userdata': ProductManifestAsset(
            path=f'{item_path}/userdata.json',
            title='userdata.json',
            checksum=attr['userdata.json:checksum'],
            size=attr['userdata.json:size'],
        )
    }

    for band_id, band in zip(S1_Pols, generate_bands(S1_Pols, None), strict=True):
        if band_id in polarizations[mode]:
            extra = {
                'data_type': 'float32',
                'nodata': -32768,
                'sar:polarizations': [band_id],
            }

            if mgrs:
                extra.update({'proj:code': grid_epsg['proj:code']})

            assets[band_id] = CloudOptimizedGeoTIFFAsset(
                path=f'{item_path}/{band_id}.tif',
                title=f'{band["title"]}',
                description=f'{band["description"]}',
                size=attr[f'{band_id}.tif:size'],
                extra=extra,
            )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='sentinel-1-global-mosaics',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        product_asset_name='Product',
        assets=assets,
        extensions=extensions,
        extra=props,
    )

    return await item.generate()
