from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
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
)


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    subtype = attr['productType'][5:8].lower()
    timeliness = 'nrt' if attr['timeliness'] == 'NR' else 'ntc'
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('slstr',),
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
        'product:type': attr['productType'],
        'product:timeliness': 'PT3H' if attr['timeliness'] == 'NR' else 'P1M',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'saline_water': attr['salineWaterCover'],
            'coastal': attr['coastalCover'],
            'fresh_inland_water': attr['freshInlandWaterCover'],
            'tidal_region': attr['tidalRegionCover'],
            'land': attr['landCover'],
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

    titles = {
        'cartesian_fn': 'Full resolution cartesian coordinates for the 1km F1 grid, nadir view',
        'cartesian_in': 'Full resolution cartesian coordinates for the 1km TIR grid, nadir view',
        'cartesian_tx': '16km cartesian coordinates',
        'flags_fn': 'Global flags for the 1km F1 grid, nadir view',
        'flags_in': 'Global flags for the 1km TIR grid, nadir view',
        'FRP_an': 'FRP_an measurements',
        'FRP_bn': 'FRP_bn measurements',
        'FRP_in': 'FRP_in measurements',
        'geodetic_fn': 'Full resolution geodetic coordinates for the 1km F1 grid, nadir view',
        'geodetic_in': 'Full resolution geodetic coordinates for the 1km TIR grid, nadir view',
        'geodetic_tx': '16km geodetic coordinates',
        'geometry_tn': '16km solar and satellite geometry annotations, nadir view',
        'indices_fn': 'Scan, pixel and detector annotations for the 1km F1 grid, nadir view',
        'indices_in': 'Scan, pixel and detector annotations for the 1km TIR grid, nadir view',
        'met_tx': 'Meteorological parameters regridded onto the 16km tie points',
        'time_an': 'Time annotations for the A stripe grid',
        'time_bn': 'Time annotations for the B stripe grid',
        'time_in': 'Time annotations for the 1 KM grid',
        'LST_ancillary_ds': 'LST ancillary measurements',
        'LST_in': 'LST_in measurements',
        'L2P': 'L2P measurements',
        'L2P_dual': 'L2P dual-view measurements',
        'L2P_nadir': 'L2P nadir-view measurements',
        'FRP_MWIR1km_STANDARD': 'Fire Radiative Power measurements',
        'FRP_MWIR1km_ALTERNATIVE': 'Fire Radiative Power measurements',
        'FRP_Merged_MWIR1kmStandard_SWIR1km': 'Fire Radiative Power measurements',
        'FRP_SWIR500m': 'Fire Radiative Power measurements',
        'FRP_MWIR1km_ALTERNATIVE_CSV': 'Fire Radiative Power measurements',
        'FRP_MWIR1km_STANDARD_CSV': 'Fire Radiative Power measurements',
        'FRP_SWIR500m_CSV': 'Fire Radiative Power measurements',
    }

    optional_assets: dict[str, dict[str, Any]] = {}
    required_assets: dict[str, dict[str, Any]] = {}
    if subtype == 'frp':
        extras = {'processing:lineage': 'Input bands: S5, S6, S7, F1'}
        optional_assets = {
            'geodetic_in': {},
            'FRP_in': extras,
            'flags_in': {},
        }
        if timeliness == 'nrt':
            optional_assets.update({
                'FRP_MWIR1km_STANDARD': {},
                'FRP_MWIR1km_ALTERNATIVE': {},
                'FRP_Merged_MWIR1kmStandard_SWIR1km': {},
                'FRP_SWIR500m': {},
                'FRP_MWIR1km_ALTERNATIVE_CSV': {},
                'FRP_MWIR1km_STANDARD_CSV': {},
                'FRP_SWIR500m_CSV': {},
            })
        elif timeliness == 'ntc':
            optional_assets.update({
                'FRP_an': extras,
                'FRP_bn': extras,
                'cartesian_fn': {},
                'cartesian_in': {},
                'cartesian_tx': {},
                'flags_fn': {},
                'geodetic_fn': {},
                'geodetic_tx': {},
                'geometry_tn': {},
                'indices_fn': {},
                'indices_in': {},
                'met_tx': {},
                'time_an': {},
                'time_bn': {},
                'time_in': {},
            })
    elif subtype == 'lst':
        required_assets = {
            'cartesian_in': {},
            'cartesian_tx': {},
            'flags_in': {},
            'geodetic_in': {},
            'geodetic_tx': {},
            'geometry_tn': {},
            'indices_in': {},
            'LST_ancillary_ds': {},
            'LST_in': {'processing:lineage': 'Input bands: S8, S9'},
            'met_tx': {},
            'time_in': {},
        }
    elif subtype == 'wst':
        l2p_extra = {'processing:lineage': 'Input bands: S7, S8, S9'}
        if attr.get('asset:L2PData') is not None:
            # Baseline 003 and earlier contain one L2P NetCDF asset.
            required_assets = {'L2P': l2p_extra}
        else:
            # Baseline 004 splits L2P into nadir and dual-view NetCDF assets.
            required_assets = {
                'L2P_dual': l2p_extra,
                'L2P_nadir': l2p_extra,
            }

    asset_keys = list(required_assets.keys()) + list(optional_assets.keys())
    asset_keys.sort()
    for key in asset_keys:
        optional = key in optional_assets
        attr_key = f'asset:{key}Data'
        local_path = attr.get(attr_key)
        if local_path is None:
            if optional:
                continue
            else:
                raise AssertionError(f'{attr_key=!r} must be present in the metadata')
        assets[key] = NetCDFAsset(
            path=f'{item_path}/{local_path}',
            title=titles[key],
            checksum=attr[f'{attr_key}:checksum'],
            size=attr[f'{attr_key}:size'],
            extra=optional_assets[key] if optional else required_assets[key],
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=f'sentinel-3-sl-2-{subtype}-{timeliness}',
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
