from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    OLCI_Bands,
    generate_bands,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
    ZipperLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    full_res = attr['productType'].endswith('FR___')
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': (attr['instrumentShortName'].lower(),),
        'gsd': 300 if full_res else 1200,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'product:type': attr['productType'],
        'product:timeliness': 'PT3H' if attr['timeliness'] == 'NR' else 'P1M',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'saline_water': attr['salineWaterCover'],
            'coastal': attr['coastalCover'],
            'fresh_inland_water': attr['freshInlandWaterCover'],
            'tidal_region': attr['tidalRegionCover'],
            'bright': attr['brightPixels'],
            'invalid': attr['invalidPixels'],
            'cosmetic': attr['cosmeticPixels'],
            'duplicated': attr['duplicatedPixels'],
            'saturated': attr['saturatedPixels'],
            'dubious_samples': attr['dubiousSamples'],
        },
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'xfdumanifest': ProductManifestAsset(
            path=f'{item_path}/xfdumanifest.xml',
        ),
    }

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    # Add standard NetCDF assets
    for asset_id in (
        'geo-coordinates',
        'instrument-data',
        'quality-flags',
        'tie-geo-coordinates',
        'tie-geometries',
        'tie-meteo',
        'time-coordinates',
    ):
        asset_key = asset_id.replace('-', '_')
        assets[asset_id] = NetCDFAsset(
            path=f'{item_path}/{attr[f"asset:{asset_key}"]}',
            title=f'{" ".join(word.title() for word in asset_id.split("-"))} Annotations',
            checksum=attr[f'asset:{asset_key}:checksum'],
            size=attr[f'asset:{asset_key}:size'],
        )

    if 'asset:removed_pixels' in attr:
        assets['removed-pixels'] = NetCDFAsset(
            path=f'{item_path}/{attr["asset:removed_pixels"]}',
            title='Removed Pixels information used for SYN L1c reconstruction',
            checksum=attr['asset:removed_pixels:checksum'],
            size=attr['asset:removed_pixels:size'],
        )

    # Add radiance data and uncertainty assets for each band
    for band_id, band in zip(OLCI_Bands, generate_bands(OLCI_Bands, None), strict=True):
        assets[f'{band_id}_radianceData'] = NetCDFAsset(
            path=f'{item_path}/{attr[f"asset:{band_id}_radianceData"]}',
            title=f'TOA radiance for OLCI acquisition band {band_id}',
            checksum=attr[f'asset:{band_id}_radianceData:checksum'],
            size=attr[f'asset:{band_id}_radianceData:size'],
            extra={'bands': (band,)},
        )
        if f'asset:{band_id}_radiance_uncData' in attr:
            assets[f'{band_id}_radiance_uncData'] = NetCDFAsset(
                path=f'{item_path}/{attr[f"asset:{band_id}_radiance_uncData"]}',
                title=f'Log10 scaled Radiometric Uncertainty Estimate for OLCI acquisition band {band_id}',
                checksum=attr[f'asset:{band_id}_radiance_uncData:checksum'],
                size=attr[f'asset:{band_id}_radiance_uncData:size'],
                extra={'bands': (band,)},
            )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    collection = 'sentinel-3-olci-1-e'
    collection += 'fr-' if full_res else 'rr-'
    collection += 'nrt' if attr['timeliness'] == 'NR' else 'ntc'

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )
    return await item.generate()
