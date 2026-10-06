from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
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
