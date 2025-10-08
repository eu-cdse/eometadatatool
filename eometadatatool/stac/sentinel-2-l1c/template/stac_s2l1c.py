from math import isnan
from typing import Any

from eometadatatool.dlc import get_odata_id, s2_compute_average
from eometadatatool.stac.framework.stac_asset import (
    JPEG2000Asset,
    ProductManifestAsset,
    ThumbnailAsset,
    XMLAsset,
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
    proj = f'EPSG:{attr["epsg"]}'
    props = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': f'sentinel-{attr["platformSerialIdentifier"].lower()}',
        'constellation': attr['platformShortName'].lower(),
        'instruments': [attr['instrumentShortName'].lower()],
        'gsd': 10,
        'processing:level': 'L1',
        'processing:datetime': attr['processingDate'],
        'product:type': attr['productType'],
        'product:timeliness': 'PT24H',
        'product:timeliness_category': 'NRT',
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['sat:absolute_orbit'],
        'sat:platform_international_designator': {
            '2A': '2015-028A',
            '2B': '2017-013A',
            '2C': '2024-157A',
        }.get(attr['platformSerialIdentifier'], attr.get('nssdcIdentifier')),
        'grid:code': attr['grid:code'],
        'view:sun_azimuth': attr['illuminationZenithAngle'],
        'view:sun_elevation': 90 - attr['view:sun_elevation'],
        'eopf:datastrip_id': attr['datastripId'],
        'eopf:datatake_id': attr['productGroupId'],
        'eopf:instrument_mode': attr['s2msi:dataTakeType'],
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version
    average_azimuth = s2_compute_average(attr, 'view:azimuth')
    if not isnan(average_azimuth):
        props['view:azimuth'] = average_azimuth
    average_incidence_angle = s2_compute_average(attr, 'view:incidence_angle')
    if not isnan(average_incidence_angle):
        props['view:incidence_angle'] = average_incidence_angle

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets = {
        'safe_manifest': ProductManifestAsset(
            path=f'{item_path}/manifest.safe',
            title='manifest.safe',
            checksum=attr['manifest.safe:checksum:MD5'],
            size=attr['manifest.safe:size'],
        ),
        'product_metadata': XMLAsset(
            path=f'{item_path}/MTD_MSIL1C.xml',
            title='MTD_MSIL1C.xml',
            roles=('metadata',),
            checksum=attr['MTD_MSIL1C:checksum'],
            size=attr['MTD_MSIL1C:size'],
        ),
        'granule_metadata': XMLAsset(
            path=f'{item_path}{attr["MTD_TL"]}',
            title='MTD_TL.xml',
            roles=('metadata',),
            checksum=attr['MTD_TL:checksum'],
            size=attr['MTD_TL:size'],
        ),
        'inspire_metadata': XMLAsset(
            path=f'{item_path}/INSPIRE.xml',
            title='INSPIRE.xml',
            roles=('metadata',),
            checksum=attr['INSPIRE:checksum'],
            size=attr['INSPIRE:size'],
        ),
        'datastrip_metadata': XMLAsset(
            path=f'{item_path}{attr["MTD_DS"]}',
            title='MTD_DS.xml',
            roles=('metadata',),
            checksum=attr['MTD_DS:checksum'],
            size=attr['MTD_DS:size'],
        ),
        'thumbnail': ThumbnailAsset(
            path=attr['ql:path'],
            title='Quicklook',
            roles=('thumbnail', 'overview'),
            checksum=attr['ql:checksum'],
            size=attr['ql:size'],
            extra={
                'data_type': 'uint8',
                'proj:code': None,
                'proj:shape': (343, 343),
            },
        ),
    }

    for band_id, band in zip(S2_Bands, generate_bands(S2_Bands, None), strict=True):
        res = int(attr[f'asset:{band_id}:eo:gsd'])
        asset_key = f'asset:{band_id}'

        extra = {
            'bands': (band,),
            'data_type': 'uint16',
            'nodata': attr['raster:bands:nodata'],
            'raster:scale': 0.0001,
            'raster:offset': -0.1,
            'gsd': res,
            'proj:code': proj,
            'proj:shape': [
                attr[f'asset:proj:shape:{res}:NCOLS'],
                attr[f'asset:proj:shape:{res}:NROWS'],
            ],
            'proj:bbox': [
                attr[f'asset:proj:transform:{res}:ULX'],
                (
                    attr[f'asset:proj:transform:{res}:ULY']
                    - res * attr[f'asset:proj:shape:{res}:NCOLS']
                ),
                (
                    attr[f'asset:proj:transform:{res}:ULX']
                    + res * attr[f'asset:proj:shape:{res}:NROWS']
                ),
                attr[f'asset:proj:transform:{res}:ULY'],
            ],
            'proj:transform': (
                res,
                0,
                attr[f'asset:proj:transform:{res}:ULX'],
                0,
                -res,
                attr[f'asset:proj:transform:{res}:ULY'],
            ),
        }
        view_azimuth = attr[f'asset:{band_id}:view:azimuth']
        if not isnan(view_azimuth):
            extra['view:azimuth'] = view_azimuth
        view_incidence_angle = attr[f'asset:{band_id}:view:incidence_angle']
        if not isnan(view_incidence_angle):
            extra['view:incidence_angle'] = view_incidence_angle

        assets[band_id] = JPEG2000Asset(
            path=f'{item_path}/{attr[asset_key]}',
            title=f'{band["description"]} - {res}m',
            roles=('data', 'reflectance'),
            size=attr[f'{asset_key}:file:size'],
            checksum=attr[f'{asset_key}:file:checksum'],
            checksum_fn_code=0x16,
            extra=extra,
        )

    assets['TCI'] = JPEG2000Asset(
        path=f'{item_path}/{attr["asset:TCI"]}',
        title='True color image',
        roles=('visual',),
        size=attr['asset:TCI:file:size'],
        checksum=attr['asset:TCI:file:checksum'],
        checksum_fn_code=0x16,
        extra={
            'bands': generate_bands(S2_Bands, ('B04', 'B03', 'B02')),
            'data_type': 'uint8',
            'nodata': 0,
            'gsd': 10,
            'proj:code': proj,
            'proj:shape': [
                attr['asset:proj:shape:10:NCOLS'],
                attr['asset:proj:shape:10:NROWS'],
            ],
            'proj:bbox': [
                attr['asset:proj:transform:10:ULX'],
                (
                    attr['asset:proj:transform:10:ULY']
                    - 10 * attr['asset:proj:shape:10:NCOLS']
                ),
                (
                    attr['asset:proj:transform:10:ULX']
                    + 10 * attr['asset:proj:shape:10:NROWS']
                ),
                attr['asset:proj:transform:10:ULY'],
            ],
            'proj:transform': (
                10,
                0,
                attr['asset:proj:transform:10:ULX'],
                0,
                -10,
                attr['asset:proj:transform:10:ULY'],
            ),
        },
    )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='sentinel-2-l1c',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        product_asset_name='Product',
        assets=assets,
        extensions=(
            StacExtension.EO,
            StacExtension.RASTER,
            StacExtension.SATELLITE,
            StacExtension.GRID,
            StacExtension.VIEW,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
        ),
        extra=props,
    )

    return await item.generate()
