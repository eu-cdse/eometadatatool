from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
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
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'product:type': attr['productType'],
        'product:timeliness': 'PT3H' if attr['timeliness'] == 'NR' else 'P1M',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'saline_water': attr['salineWaterCover'],
            'coastal': attr['coastalCover'],
            'fresh_inland_water': attr['freshInlandWaterCover'],
            'tidal_region': attr['tidalRegionCover'],
            'land': attr['landCover'],
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
        'geo-coordinates': NetCDFAsset(
            path=f'{item_path}/{attr["asset:geo_coordinates"]}',
            title='Geo Coordinates Annotations',
            checksum=attr['asset:geo_coordinates:checksum'],
            size=attr['asset:geo_coordinates:size'],
        ),
        'time-coordinates': NetCDFAsset(
            path=f'{item_path}/{attr["asset:time_coordinates"]}',
            title='Time Coordinates Annotations',
            checksum=attr['asset:time_coordinates:checksum'],
            size=attr['asset:time_coordinates:size'],
        ),
        'tie-geo-coordinates': NetCDFAsset(
            path=f'{item_path}/{attr["asset:tie_geo_coordinates"]}',
            title='Tie-Point Geo Coordinate Annotations',
            checksum=attr['asset:tie_geo_coordinates:checksum'],
            size=attr['asset:tie_geo_coordinates:size'],
        ),
        'tie-geometries': NetCDFAsset(
            path=f'{item_path}/{attr["asset:tie_geometries"]}',
            title='Tie-Point Geometries Annotations',
            checksum=attr['asset:tie_geometries:checksum'],
            size=attr['asset:tie_geometries:size'],
        ),
        'tie-meteo': NetCDFAsset(
            path=f'{item_path}/{attr["asset:tie_meteo"]}',
            title='Tie-Point Meteo Annotations',
            checksum=attr['asset:tie_meteo:checksum'],
            size=attr['asset:tie_meteo:size'],
        ),
        'instrument-data': NetCDFAsset(
            path=f'{item_path}/{attr["asset:instrument_data"]}',
            title='Instrument Annotation',
            checksum=attr['asset:instrument_data:checksum'],
            size=attr['asset:instrument_data:size'],
        ),
        'lqsf': NetCDFAsset(
            path=f'{item_path}/{attr["asset:lqsf"]}',
            title='Land Quality and Science Flags',
            checksum=attr['asset:lqsf:checksum'],
            size=attr['asset:lqsf:size'],
        ),
    }

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    gifapar_key = (
        'asset:gifapar'
        if 'asset:gifapar' in attr
        else ('asset:ogvi' if 'asset:ogvi' in attr else None)
    )
    if gifapar_key is not None:
        assets['gifapar'] = NetCDFAsset(
            path=f'{item_path}/{attr[gifapar_key]}',
            title='Green Instantaneous FAPAR (GIFAPAR, formerly: OGVI)',
            checksum=attr[f'{gifapar_key}:checksum'],
            size=attr[f'{gifapar_key}:size'],
            extra={'processing:lineage': 'Input bands: Oa03, Oa10, Oa17'},
        )

    rc_gifapar_key = (
        'asset:rc_gifapar'
        if 'asset:rc_gifapar' in attr
        else ('asset:rc_ogvi' if 'asset:rc_ogvi' in attr else None)
    )
    if rc_gifapar_key is not None:
        assets['rc-gifapar'] = NetCDFAsset(
            path=f'{item_path}/{attr[rc_gifapar_key]}',
            title='Green Instantaneous FAPAR (GIFAPAR, formerly: OGVI) - Rectified Reflectance',
            checksum=attr[f'{rc_gifapar_key}:checksum'],
            size=attr[f'{rc_gifapar_key}:size'],
        )

    if iwv_path := attr.get('asset:iwv'):
        assets['iwv'] = NetCDFAsset(
            path=f'{item_path}/{iwv_path}',
            title='Integrated water vapour column',
            checksum=attr['asset:iwv:checksum'],
            size=attr['asset:iwv:size'],
            extra={'processing:lineage': 'Input bands: Oa18, Oa19'},
        )

    if otci_path := attr.get('asset:otci'):
        assets['otci'] = NetCDFAsset(
            path=f'{item_path}/{otci_path}',
            title='OLCI Terrestrial Chlorophyll Index',
            checksum=attr['asset:otci:checksum'],
            size=attr['asset:otci:size'],
            extra={'processing:lineage': 'Input bands: Oa10, Oa11, Oa12'},
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    collection = 'sentinel-3-olci-2-l'
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
            StacExtension.EO,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )
    return await item.generate()
