from collections.abc import Collection
from typing import Any, TypedDict, Unpack

from eometadatatool.dlc import (
    get_odata_id,
)
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    SRAL_Bands,
    STACBand,
    generate_bands,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
)


class _NetCDFExtra(TypedDict, total=False):
    bands: Collection[STACBand]


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('sral',),
        'gsd': 1640,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'product:type': attr['productType'],
        'product:timeliness': _get_timeliness(attr['timeliness']),
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
        'xfdumanifest': ProductManifestAsset(path=f'{item_path}/xfdumanifest.xml'),
    }

    def add_measurement(
        key: str, name: str, title: str, **extra: Unpack[_NetCDFExtra]
    ) -> None:
        attr_key = f'asset:{key}Data'
        local_path = attr.get(attr_key)
        if local_path is None:
            raise AssertionError(f'{attr_key=!r} must be present in the metadata')

        assets[name] = NetCDFAsset(
            path=f'{item_path}/{local_path}',
            title=title,
            checksum=attr[f'{attr_key}:checksum'],
            size=attr[f'{attr_key}:size'],
            extra=extra,
        )

    # Add measurement assets
    add_measurement(
        'enhancedMeasurement',
        'enhanced_measurement',
        'Enhanced Measurement Data Object File',
        bands=generate_bands(SRAL_Bands, ['C', 'Ku']),
    )

    add_measurement(
        'standardMeasurement',
        'standard_measurement',
        'Standard Measurement Data Object File',
        bands=generate_bands(SRAL_Bands, ['C', 'Ku']),
    )

    if attr['productType'] == 'SR_2_LAN___' or attr['productType'] == 'SR_2_WAT___':
        add_measurement(
            'reducedMeasurement',
            'reduced_measurement',
            'Reduced Measurement Data Object File',
            bands=generate_bands(SRAL_Bands, ['Ku']),
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
    ]

    collection = 'sentinel-3-sr-2'
    match attr['productType']:
        case 'SR_2_LAN___':
            collection += '-lan'
        case 'SR_2_LAN_HY':
            collection += '-lan-hy'
        case 'SR_2_LAN_LI':
            collection += '-lan-li'
        case 'SR_2_LAN_SI':
            collection += '-lan-si'
        case 'SR_2_WAT___':
            collection += '-wat'
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
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
            StacExtension.ALTIMETRY,
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
