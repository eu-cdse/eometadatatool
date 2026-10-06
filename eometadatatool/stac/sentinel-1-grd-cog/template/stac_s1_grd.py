from typing import Any

from eometadatatool.dlc import format_baseline, get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    ThumbnailAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import S1_Assets, S1_Pols, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    polarizations = []
    if attr.get('polarisationChannel:1') is not None:
        polarizations.append(attr['polarisationChannel:1'])
    if attr.get('polarisationChannel:2') is not None:
        polarizations.append(attr['polarisationChannel:2'])
    props = {
        'platform': f'sentinel-1{attr["platformSerialIdentifier"].lower()}',
        'constellation': attr['platformShortName'].lower(),
        'instruments': [attr['instrumentShortName'].lower()],
        'processing:level': 'L1',
        'processing:facility': attr['processingCenter'],
        'processing:datetime': attr['processingDate'],
        'processing:version': format_baseline(attr['processorVersion']),
        'product:type': attr['identifier'][4:14],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:platform_international_designator': attr['platformIdentifier'],
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.405,
        'sar:observation_direction': 'right',
        'sar:instrument_mode': attr['operationalMode'],
        'sar:polarizations': polarizations,
        'sar:pixel_spacing_range': attr['rangePixelSpacing'],
        'sar:pixel_spacing_azimuth': attr['azimuthPixelSpacing'],
        'view:incidence_angle': attr['incidenceAngleMid'],
        'view:azimuth': attr['azimuthAngle'] % 360,
        'datetime': attr['beginningDateTime'],
        'eopf:datatake_id': attr['datatakeID'],
        'eopf:instrument_configuration_id': attr['instrumentConfigurationID'],
    }
    if attr['timeliness'] == 'Fast-24h':
        props['product:timeliness'] = 'PT24H'
        props['product:timeliness_category'] = 'Fast-24h'
    elif attr['timeliness'] == 'NRT-10m':
        props['product:timeliness'] = 'PT10M'
        props['product:timeliness_category'] = 'NRT-10m'
    elif attr['timeliness'] == 'NRT-3h':
        props['product:timeliness'] = 'PT3H'
        props['product:timeliness_category'] = 'NRT-3h'
    if attr['operationalMode'] == 'iw':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 20
    elif attr['operationalMode'] == 'ew':
        props['sar:resolution_range'] = 20
        props['sar:resolution_azimuth'] = 40
    elif attr['operationalMode'] == 'sm':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 5

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

    assets = {
        'safe_manifest': ProductManifestAsset(
            path=f'{item_path}/manifest.safe',
            title='manifest.safe',
            checksum=attr['manifest.safe:checksum:MD5'],
            size=attr['manifest.safe:size'],
        ),
        'thumbnail': ThumbnailAsset(
            path=f'{item_path}/preview/thumbnail.png',
            title='Thumbnail',
            roles=['thumbnail'],
            checksum=attr['thumbnail.png:checksum'],
            size=attr['thumbnail.png:size'],
            extra={
                'proj:shape': (343, 343),
            },
        ),
    }

    for pol in polarizations:
        pol = pol.lower()
        pol_uc = pol.upper()
        mode = attr['swathIdentifier'].lower()
        for asset_id in generate_bands(S1_Assets, None):
            asset_key = f'asset:{mode}:{pol}:{asset_id["short_name"]}'
            assets[f'{asset_id["name"]}-{pol}'] = XMLAsset(
                path=f'{item_path}{attr[asset_key]}',
                title=f'{pol_uc} {asset_id["title"]}',
                description=asset_id['description'],
                roles=['metadata'],
                size=attr[f'{asset_key}:size'],
                checksum=attr[f'{asset_key}:checksum'],
                checksum_fn_code=0x16,
                extra={
                    'sar:polarizations': [pol_uc],
                },
            )

        asset_key = f'asset:{mode}:{pol}:measurement'
        assets[pol] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}{attr[asset_key]}',
            title=S1_Pols[pol_uc]['title'],
            description=S1_Pols[pol_uc]['description'],
            size=attr[f'{asset_key}:size'],
            checksum=attr[f'{asset_key}:checksum'],
            checksum_fn_code=0x16,
            extra={
                'data_type': 'uint16',
                'nodata': 0,
                'proj:code': None,
                'proj:shape': [attr['shape1'], attr['shape2']],
                'sar:polarizations': [pol_uc],
            },
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='sentinel-1-grd',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        product_asset_name='Product',
        assets=assets,
        extensions=(
            StacExtension.FILE,
            StacExtension.PROCESSING,
            StacExtension.PROJECTION,
            StacExtension.ALTERNATE,
            StacExtension.TIMESTAMP,
            StacExtension.AUTHENTICATION,
            StacExtension.SAR,
            StacExtension.EOPF,
            StacExtension.STORAGE,
            StacExtension.SATELLITE,
            StacExtension.VIEW,
            StacExtension.PRODUCT,
        ),
        extra=props,
    )

    return await item.generate()
