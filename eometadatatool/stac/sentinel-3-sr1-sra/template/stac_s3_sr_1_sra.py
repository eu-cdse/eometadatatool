from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_bands import SRAL_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
    ZipperLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    timeliness = _get_timeliness(attr['timeliness'])
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('sral',),
        'gsd': 300,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'processing:facility': attr['processingCenter'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'product:type': attr['productType'],
        'product:timeliness': timeliness,
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'land': attr['landCover'],
            'closed_sea': attr['closedSeaCover'],
            'continental_ice': attr['continentalIceCover'],
            'open_ocean': attr['openOceanCover'],
        },
        'altm:instrument_mode': 'lrm' if attr['lrmMode'] > 0 else 'sar',
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'xfdumanifest': ProductManifestAsset(path=f'{item_path}/xfdumanifest.xml'),
        'measurement_data': NetCDFAsset(
            path=f'{item_path}/{attr["asset:measurementData"]}',
            title='Measurement Data Object File',
            checksum=attr['asset:measurementData:checksum'],
            size=attr['asset:measurementData:size'],
            extra={'bands': generate_bands(SRAL_Bands, ['C', 'Ku'])},
        ),
    }

    if attr['productType'] == 'SR_1_SRA___' and (
        acq_data := (
            attr.get('asset:acquisitionDataOldProds')
            or attr.get('asset:acquisitionData')
        )
    ):
        assets['acquisition_data'] = NetCDFAsset(
            path=f'{item_path}/{acq_data}',
            title='Acquisition Data Object File',
            checksum=(
                attr.get('asset:acquisitionDataOldProds:checksum')
                or attr.get('asset:acquisitionData:checksum')
            ),
            size=(
                attr.get('asset:acquisitionDataOldProds:size')
                or attr.get('asset:acquisitionData:size')
            ),
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    collection = 'sentinel-3-sr-1-sra'
    if attr['productType'] == 'SR_1_SRA_A_':
        collection += '-a'
    match attr['timeliness']:
        case 'NR':
            collection += '-nrt'
        case 'NT':
            collection += '-ntc'
        case 'ST':
            collection += '-stc'

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.ALTIMETRY,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )

    return await item.generate()


def _get_timeliness(timeliness: str) -> str:
    match timeliness:
        case 'NR':
            return 'PT3H'
        case 'NT':
            return 'P1M'
        case _:
            return 'PT48H'
