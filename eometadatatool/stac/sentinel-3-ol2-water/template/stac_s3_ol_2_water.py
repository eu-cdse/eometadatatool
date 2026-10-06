from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
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

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    # Add reflectance data assets
    for i in [*range(1, 13), 16, 17, 18, 21]:
        band_id = f'Oa{i:02d}'
        assets[f'{band_id}_reflectanceData'] = NetCDFAsset(
            path=f'{item_path}/{attr[f"asset:{band_id}_reflectanceData"]}',
            title=f'Reflectance for OLCI acquisition band {band_id}',
            checksum=attr[f'asset:{band_id}_reflectanceData:checksum'],
            size=attr[f'asset:{band_id}_reflectanceData:size'],
            extra={'bands': generate_bands(OLCI_Bands, (band_id,))},
        )

    # Add derived products
    assets['trsp'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:trspData"]}',
        title='Transparency properties of water',
        checksum=attr['asset:trspData:checksum'],
        size=attr['asset:trspData:size'],
        extra={'processing:lineage': 'Input bands: Oa04, Oa06'},
    )

    assets['chl-Nn'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:chlNnData"]}',
        title='Neural net chlorophyll concentration',
        checksum=attr['asset:chlNnData:checksum'],
        size=attr['asset:chlNnData:size'],
        extra={
            'processing:lineage': 'Input bands: Oa01, Oa02, Oa03, Oa04, Oa05, Oa06, Oa07, Oa08, Oa09, Oa10, Oa11, Oa12, Oa16, Oa17, Oa18, Oa21'
        },
    )

    if (chl_oc4me_href := attr.get('asset:chlOc4meData')) is not None:
        assets['chl-Oc4me'] = NetCDFAsset(
            path=f'{item_path}/{chl_oc4me_href}',
            title='OC4Me algorithm chlorophyll concentration',
            checksum=attr['asset:chlOc4meData:checksum'],
            size=attr['asset:chlOc4meData:size'],
            extra={'processing:lineage': 'Input bands: Oa03, Oa04, Oa05, Oa06'},
        )

    if (chlor_a_href := attr.get('asset:chlor_aData')) is not None:
        assets['chlor-a'] = NetCDFAsset(
            path=f'{item_path}/{chlor_a_href}',
            title='Chlorophyll-a concentration (OWC algorithm)',
            checksum=attr['asset:chlor_aData:checksum'],
            size=attr['asset:chlor_aData:size'],
        )

    if (fluo_href := attr.get('asset:fluoData')) is not None:
        assets['fluo'] = NetCDFAsset(
            path=f'{item_path}/{fluo_href}',
            title='Fluorescence peak height',
            checksum=attr['asset:fluoData:checksum'],
            size=attr['asset:fluoData:size'],
            extra={'processing:lineage': 'Input bands: Oa08, Oa09, Oa10, Oa11, Oa12'},
        )

    assets['iop-Nn'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:iopNnData"]}',
        title='Inherent optical properties of water',
        checksum=attr['asset:iopNnData:checksum'],
        size=attr['asset:iopNnData:size'],
        extra={'processing:lineage': 'Input bands: Oa01, Oa12, Oa16, Oa17, Oa21'},
    )

    if (iop_lsd_href := attr.get('asset:iopLsdData')) is not None:
        assets['iop-Lsd'] = NetCDFAsset(
            path=f'{item_path}/{iop_lsd_href}',
            title='Inherent optical properties (3SAA algorithm)',
            checksum=attr['asset:iopLsdData:checksum'],
            size=attr['asset:iopLsdData:size'],
            extra={'processing:lineage': 'Input bands: Oa01, Oa02, Oa03, Oa04, Oa05, Oa06, Oa07, Oa08'},
        )

    assets['iwv'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:iwv"]}',
        title='Integrated water vapour column',
        checksum=attr['asset:iwv:checksum'],
        size=attr['asset:iwv:size'],
        extra={'processing:lineage': 'Input bands: Oa18, Oa19'},
    )

    assets['par'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:parData"]}',
        title='Photosynthetically active radiation',
        checksum=attr['asset:parData:checksum'],
        size=attr['asset:parData:size'],
    )

    assets['tsm-Nn'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:tsmNnData"]}',
        title='Total suspended matter concentration',
        checksum=attr['asset:tsmNnData:checksum'],
        size=attr['asset:tsmNnData:size'],
        extra={
            'processing:lineage': 'Input bands: Oa01, Oa02, Oa03, Oa04, Oa05, Oa06, Oa07, Oa08, Oa09, Oa10, Oa11, Oa12, Oa16, Oa17, Oa18, Oa21'
        },
    )

    assets['w-Aer'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:wAerData"]}',
        title='Aerosol over water',
        checksum=attr['asset:wAerData:checksum'],
        size=attr['asset:wAerData:size'],
        extra={'processing:lineage': 'Input bands: Oa05, Oa06, Oa17'},
    )

    assets['wqsf'] = NetCDFAsset(
        path=f'{item_path}/{attr["asset:wqsfData"]}',
        title='Water quality and science flags',
        checksum=attr['asset:wqsfData:checksum'],
        size=attr['asset:wqsfData:size'],
    )

    # Add remaining NetCDF assets without band information
    for asset_id, asset_title in (
        ('geo-coordinates', 'Geo Coordinates Annotations'),
        ('instrument-data', 'Instrument Annotation'),
        ('tie-geo-coordinates', 'Tie-Point Geo Coordinate Annotations'),
        ('tie-geometries', 'Tie-Point Geometries Annotations'),
        ('tie-meteo', 'Tie-Point Meteo Annotations'),
        ('time-coordinates', 'Time Coordinates Annotations'),
        ('wqsf', 'Water quality and science flags'),
    ):
        asset_key = asset_id.replace('-', '_')
        if attr.get(f'asset:{asset_key}') is not None:
            assets[asset_id] = NetCDFAsset(
                path=f'{item_path}/{attr[f"asset:{asset_key}"]}',
                title=attr.get(f'asset:{asset_key}:title', asset_title),
                checksum=attr[f'asset:{asset_key}:checksum'],
                size=attr[f'asset:{asset_key}:size'],
            )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
    ]

    collection = 'sentinel-3-olci-2-w'
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
