from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    SYN_VGT_Bands,
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
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('olci', 'slstr'),
        'gsd': 1000,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'eo:snow_cover': attr['snowOrIceCover'],
        'product:type': attr['productType'],
        'product:timeliness': 'P1M' if attr['timeliness'] == 'NT' else 'PT48H',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'land': attr['landCover'],
        },
    }

    ## VGP specific attributes
    if attr['productType'] == 'SY_2_VGP___':
        props['statistics']['saline_water'] = attr['salineWaterCover']
        props['statistics']['coastal'] = attr['coastalCover']
        props['statistics']['fresh_inland_water'] = attr['freshInlandWaterCover']
        props['statistics']['tidal_region'] = attr['tidalRegionCover']

    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'xfdumanifest': ProductManifestAsset(
            path=f'{item_path}/xfdumanifest.xml',
        ),
    }

    ql_path = attr.get('ql:path')
    if attr['productType'] != 'SY_2_VGP___' and ql_path is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    def add_netcdf(key: str, title: str, **kwargs) -> None:
        local_path = attr[f'asset:{key}']
        assets[key] = NetCDFAsset(
            path=f'{item_path}/{local_path}',
            title=title,
            checksum=attr[f'asset:{key}:checksum'],
            size=attr[f'asset:{key}:size'],
            **kwargs,
        )

    ## Common assets
    for band_id in ['B0', 'B2', 'B3', 'MIR']:
        if attr['productType'] == 'SY_2_VGP___':
            reflectance_asset_title = (
                f'TOA reflectance associated with VGT-{band_id} channel'
            )
        else:
            reflectance_asset_title = (
                f'Surface Reflectance Data Set associated with VGT-{band_id} channel'
            )
        add_netcdf(
            band_id,
            reflectance_asset_title,
            extra={'bands': generate_bands(SYN_VGT_Bands, [band_id])},
        )

    add_netcdf('og', 'Total Ozone column data')
    add_netcdf('saa', 'Solar azimuth angle data')
    add_netcdf('sm', 'Status Map data')
    add_netcdf('sza', 'Solar zenith angle data')
    add_netcdf('vaa', 'View azimuth angle data')
    add_netcdf('vza', 'View zenith angle data')
    add_netcdf('wvg', 'Total column water vapour data')

    ## V10 and VG1 specific assets
    if attr['productType'] in {'SY_2_V10___', 'SY_2_VG1___'}:
        add_netcdf('ag', 'Aerosol optical thickness data')
        add_netcdf(
            'NDVI',
            'Normalised difference vegetation index',
            extra={'processing:lineage': 'Input bands: B2, B3'},
        )
        add_netcdf('tg', 'Synthesis time data')

    if attr['productType'] == 'SY_2_VG1___' and attr.get('asset:toa_ndvi'):
        add_netcdf(
            'toa_ndvi',
            'Normalised difference vegetation index, computed using TOA reflectance',
            extra={'processing:lineage': 'Input bands: B2, B3'},
        )

    if attr['productType'] == 'SY_2_VGP___':
        add_netcdf('ag', 'Aerosol optical thickness at 550 nm')

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    collection = 'sentinel-3-syn-2-v'
    match attr['productType']:
        case 'SY_2_V10___':
            collection += '10-'
        case 'SY_2_VG1___':
            collection += 'g1-'
        case 'SY_2_VGP___':
            collection += 'gp-'

    match attr['timeliness']:
        case 'NT':
            collection += 'ntc'
        case 'ST':
            collection += 'stc'

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
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
