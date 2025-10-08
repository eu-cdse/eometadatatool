from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
    ZipperLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('olci', 'slstr'),
        'gsd': 4500,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'product:type': attr['productType'],
        'product:timeliness': 'P1M',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'saline_water': attr['salineWaterCover'],
            'land': attr['landCover'],
        },
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'ntc_aod_data': NetCDFAsset(
            path=f'{item_path}/{attr["asset:ntc_aod_data"]}',
            title='Global aerosol parameters',
            checksum=attr['asset:ntc_aod_data:checksum'],
            size=attr['asset:ntc_aod_data:size'],
        ),
        'xfdumanifest': ProductManifestAsset(
            path=f'{item_path}/xfdumanifest.xml',
        ),
    }

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='sentinel-3-syn-2-aod-ntc',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.EO,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )
    return await item.generate()
