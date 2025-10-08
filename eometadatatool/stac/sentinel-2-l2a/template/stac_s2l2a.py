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
        'processing:level': 'L2',
        'processing:datetime': attr['processingDate'],
        'product:type': attr['productType'],
        'product:timeliness': 'PT24H',
        'product:timeliness_category': 'NRT',
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'eo:snow_cover': attr['s2:snow_ice_percentage'],
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
        'statistics': {
            'nodata': attr['s2:nodata_pixel_percentage'],
            'saturated_defective': attr['s2:saturated_defective_pixel_percentage'],
            'dark_area': attr.get(
                's2:dark_features_percentage',
                attr.get('s2:cast_shadow_percentage'),
            ),
            'cloud_shadow': attr['s2:cloud_shadow_percentage'],
            'vegetation': attr['s2:vegetation_percentage'],
            'not_vegetated': attr['s2:not_vegetated_percentage'],
            'water': attr['s2:water_percentage'],
            'unclassified': attr['s2:unclassified_percentage'],
            'medium_proba_clouds': attr['s2:medium_proba_clouds_percentage'],
            'high_proba_clouds': attr['s2:high_proba_clouds_percentage'],
            'thin_cirrus': attr['s2:thin_cirrus_percentage'],
        },
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
            path=f'{item_path}/MTD_MSIL2A.xml',
            title='MTD_MSIL2A.xml',
            roles=('metadata',),
            checksum=attr['MTD_MSIL2A:checksum'],
            size=attr['MTD_MSIL2A:size'],
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
    }

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(
            path=ql_path,
            title='Quicklook',
            roles=('thumbnail', 'overview'),
            checksum=attr['ql:checksum'],
            size=attr['ql:size'],
            extra={
                'data_type': 'uint8',
                'proj:code': None,
                'proj:shape': (343, 343),
            },
        )

    for band_id, band in zip(S2_Bands, generate_bands(S2_Bands, None), strict=True):
        original_res = int(attr[f'asset:{band_id}:eo:gsd'])
        for res in (10, 20, 60):
            asset_key = f'asset:{band_id}:{res}m'
            if asset_key not in attr:
                continue

            if original_res == res:
                sampling = 'sampling:original'
            elif original_res > res:
                sampling = 'sampling:upsampled'
            else:
                sampling = 'sampling:downsampled'

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

            assets[f'{band_id}_{res}m'] = JPEG2000Asset(
                path=f'{item_path}/{attr[asset_key]}',
                title=f'{band["description"]} - {res}m',
                roles=(
                    'data',
                    'reflectance',
                    sampling,
                    f'gsd:{res}m',
                ),
                size=attr[f'{asset_key}:file:size'],
                checksum=attr[f'{asset_key}:file:checksum'],
                checksum_fn_code=0x16,
                extra=extra,
            )

    # TCI assets
    tci_bands = generate_bands(S2_Bands, ('B04', 'B03', 'B02'))
    original_res = 10
    for res in (10, 20, 60):
        asset_key = f'asset:TCI:{res}m'

        if original_res == res:
            sampling = 'sampling:original'
        elif original_res > res:
            sampling = 'sampling:upsampled'
        else:
            sampling = 'sampling:downsampled'

        assets[f'TCI_{res}m'] = JPEG2000Asset(
            path=f'{item_path}/{attr[asset_key]}',
            title='True color image',
            roles=('visual', sampling, f'gsd:{res}m'),
            size=attr[f'{asset_key}:file:size'],
            checksum=attr[f'{asset_key}:file:checksum'],
            checksum_fn_code=0x16,
            extra={
                'bands': tci_bands,
                'data_type': 'uint8',
                'nodata': 0,
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
            },
        )

    # AOT assets
    for res in (10, 20, 60):
        asset_key = f'asset:AOT:{res}m'
        assets[f'AOT_{res}m'] = JPEG2000Asset(
            path=f'{item_path}/{attr[asset_key]}',
            title=f'Aerosol optical thickness (AOT) - {res}m',
            roles=('data', f'gsd:{res}m'),
            size=attr[f'{asset_key}:file:size'],
            checksum=attr[f'{asset_key}:file:checksum'],
            checksum_fn_code=0x16,
            extra={
                'data_type': 'uint16',
                'nodata': attr['raster:bands:nodata'],
                'raster:scale': 0.0001,
                'raster:offset': -0.1,
                'gsd': res,
                'proj:code': proj,
                'proj:shape': [
                    attr[f'asset:proj:shape:{res}:NROWS'],
                    attr[f'asset:proj:shape:{res}:NCOLS'],
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
            },
        )

    # SCL assets
    original_res = 20
    for res in (20, 60):
        asset_key = f'asset:SCL:{res}m'

        if original_res == res:
            sampling = 'sampling:original'
        elif original_res > res:
            sampling = 'sampling:upsampled'
        else:
            sampling = 'sampling:downsampled'

        assets[f'SCL_{res}m'] = JPEG2000Asset(
            path=f'{item_path}/{attr[asset_key]}',
            title=f'Scene classification map (SCL) - {res}m',
            roles=('data', sampling, f'gsd:{res}m'),
            size=attr[f'{asset_key}:file:size'],
            checksum=attr[f'{asset_key}:file:checksum'],
            checksum_fn_code=0x16,
            extra={
                'data_type': 'uint8',
                'nodata': attr['raster:bands:nodata'],
                'gsd': res,
                'proj:code': proj,
                'proj:shape': [
                    attr[f'asset:proj:shape:{res}:NROWS'],
                    attr[f'asset:proj:shape:{res}:NCOLS'],
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
                'classification:classes': (
                    {
                        'value': 0,
                        'name': 'no_data',
                        'nodata': True,
                        'percentage': attr['s2:nodata_pixel_percentage'],
                    },
                    {
                        'value': 1,
                        'name': 'saturated_or_defective',
                        'percentage': attr['s2:saturated_defective_pixel_percentage'],
                    },
                    {
                        'value': 2,
                        'name': 'dark_area_pixels',
                        'percentage': attr.get(
                            's2:dark_features_percentage',
                            attr.get('s2:cast_shadow_percentage'),
                        ),
                    },
                    {
                        'value': 3,
                        'name': 'cloud_shadows',
                        'percentage': attr['s2:cloud_shadow_percentage'],
                    },
                    {
                        'value': 4,
                        'name': 'vegetation',
                        'percentage': attr['s2:vegetation_percentage'],
                    },
                    {
                        'value': 5,
                        'name': 'not_vegetated',
                        'percentage': attr['s2:not_vegetated_percentage'],
                    },
                    {
                        'value': 6,
                        'name': 'water',
                        'percentage': attr['s2:water_percentage'],
                    },
                    {
                        'value': 7,
                        'name': 'unclassified',
                        'percentage': attr['s2:unclassified_percentage'],
                    },
                    {
                        'value': 8,
                        'name': 'cloud_medium_probability',
                        'percentage': attr['s2:medium_proba_clouds_percentage'],
                    },
                    {
                        'value': 9,
                        'name': 'cloud_high_probability',
                        'percentage': attr['s2:high_proba_clouds_percentage'],
                    },
                    {
                        'value': 10,
                        'name': 'thin_cirrus',
                        'percentage': attr['s2:thin_cirrus_percentage'],
                    },
                    {
                        'value': 11,
                        'name': 'snow',
                        'percentage': attr['s2:snow_ice_percentage'],
                    },
                )
                if sampling == 'sampling:original'
                else (
                    {'value': 0, 'name': 'no_data', 'nodata': True},
                    {'value': 1, 'name': 'saturated_or_defective'},
                    {'value': 2, 'name': 'dark_area_pixels'},
                    {'value': 3, 'name': 'cloud_shadows'},
                    {'value': 4, 'name': 'vegetation'},
                    {'value': 5, 'name': 'not_vegetated'},
                    {'value': 6, 'name': 'water'},
                    {'value': 7, 'name': 'unclassified'},
                    {'value': 8, 'name': 'cloud_medium_probability'},
                    {'value': 9, 'name': 'cloud_high_probability'},
                    {'value': 10, 'name': 'thin_cirrus'},
                    {'value': 11, 'name': 'snow'},
                ),
            },
        )

    # WVP assets
    for res in (10, 20, 60):
        asset_key = f'asset:WVP:{res}m'
        gsd = res
        assets[f'WVP_{res}m'] = JPEG2000Asset(
            path=f'{item_path}/{attr[asset_key]}',
            title=f'Water vapour (WVP) - {res}m',
            roles=('data', f'gsd:{res}m'),
            size=attr[f'{asset_key}:file:size'],
            checksum=attr[f'{asset_key}:file:checksum'],
            checksum_fn_code=0x16,
            extra={
                'data_type': 'uint16',
                'nodata': attr['raster:bands:nodata'],
                'raster:scale': 0.0001,
                'raster:offset': -0.1,
                'gsd': gsd,
                'proj:code': proj,
                'proj:shape': [
                    attr[f'asset:proj:shape:{res}:NROWS'],
                    attr[f'asset:proj:shape:{res}:NCOLS'],
                ],
                'proj:bbox': [
                    attr[f'asset:proj:transform:{res}:ULX'],
                    (
                        attr[f'asset:proj:transform:{res}:ULY']
                        - gsd * attr[f'asset:proj:shape:{res}:NCOLS']
                    ),
                    (
                        attr[f'asset:proj:transform:{res}:ULX']
                        + gsd * attr[f'asset:proj:shape:{res}:NROWS']
                    ),
                    attr[f'asset:proj:transform:{res}:ULY'],
                ],
                'proj:transform': (
                    gsd,
                    0,
                    attr[f'asset:proj:transform:{res}:ULX'],
                    0,
                    -gsd,
                    attr[f'asset:proj:transform:{res}:ULY'],
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
        collection='sentinel-2-l2a',
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
            StacExtension.CLASSIFICATION,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
        ),
        extra=props,
    )

    return await item.generate()
