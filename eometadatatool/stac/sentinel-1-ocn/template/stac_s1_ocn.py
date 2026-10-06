from itertools import product
from typing import Any

from eometadatatool.dlc import format_baseline, get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_bands import S1_OCN
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink

from eometadatatool.flags import is_no_private, is_hidden, is_extended_private_data
from eometadatatool.metafile_loader import extract_from_netcdf
from eometadatatool.datacube import extract_dims_vars
from pathlib import Path
import json

async def render(attr: dict[str, Any]) -> dict[str, Any]:
    def mode_beams(mode: str) -> list[str]:
        match mode:
            case 'iw':
                return ['iw1', 'iw2', 'iw3']
            case 'ew':
                return ['ew1', 'ew2', 'ew3', 'ew4', 'ew5']
            case 'sm':
                return ['s' + attr['filename'][5]]
            case 'wv':
                return ['wv1', 'wv2']
        raise ValueError(f'Unsupported mode beams {mode!r}')

    item_path: str = attr['filepath']
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path, zipper=extended_private_data)
    mode: str = attr['operationalMode'].lower()
    pols: list[str] = []
    pol_ch1 = attr.get('polarisationChannel:1')
    if pol_ch1 is not None:
        pols.append(pol_ch1.lower())
    pol_ch2 = attr.get('polarisationChannel:2')
    if pol_ch2 is not None:
        pols.append(pol_ch2.lower())

    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': f'sentinel-1{attr["platformSerialIdentifier"].lower()}',
        'constellation': attr['platformShortName'].lower(),
        'instruments': [attr['instrumentShortName'].lower()],
        'processing:level': 'L2',
        'processing:facility': attr['processingCenter'],
        'processing:datetime': attr['processingDate'],
        'processing:version': format_baseline(attr['processorVersion']),
        'processing:software': {attr['processorName']: attr['processorVersion']},
        'product:type': attr['identifier'][4:14],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:platform_international_designator': attr['platformIdentifier'],
        'sat:anx_datetime': attr['anxTime'],
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.405,
        'sar:instrument_mode': mode.upper(),
        'sar:beam_ids': mode_beams(mode),
        'sar:polarizations': [p.upper() for p in pols],
        'eopf:datatake_id': str(attr['datatakeID']),
        'eopf:instrument_configuration_id': attr['instrumentConfigurationID'],
    }

    if timeliness := _get_timeliness(attr['timeliness']):
        props['product:timeliness'] = timeliness
        props['product:timeliness_category'] = attr['timeliness']

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

    if mode == 'iw':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 20
    elif mode == 'ew':
        props['sar:resolution_range'] = 20
        props['sar:resolution_azimuth'] = 40
    elif mode == 'sm':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 5
    elif mode == 'wv':
        props['sar:resolution_range'] = 20
        props['sar:resolution_azimuth'] = 40

    # Build assets dictionary
    assets: dict[str, STACAsset] = {
        'safe_manifest': ProductManifestAsset(
            path=f'{item_path}/manifest.safe',
            title='manifest.safe',
            description='General product metadata in XML format.',
            checksum=attr['manifest.safe:checksum:MD5'],
            size=attr['manifest.safe:size'],
        ),
    }

    thumb_size = attr.get('asset:quicklook:owi:size', 0)
    if thumb_size > 0:
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/preview/quick-look-l2-owi.png',
            checksum=attr.get('asset:quicklook:owi:checksum'),
            size=attr.get('asset:quicklook:owi:size'),
        )

    # Process measurement data for each mode/polarization
    for beam, pol in product(mode_beams(mode), pols):
        if mode in ['iw', 'ew'] and f'asset:product:{pol}' in attr:

            prod = attr[f'asset:product:{pol}']
            prod_checksum = attr[f'asset:product:{pol}:checksum']
            prod_size = attr[f'asset:product:{pol}:size']

            collection = 'sentinel-1-ocn'

            dims, vars = {}, {}

            for j in range(len(prod)):
                prod_nc_path = f"{item_path}/{prod[j].replace('./', '')}"
                prod_nc_data = extract_from_netcdf(Path(prod_nc_path))

                dims, vars = extract_dims_vars(
                    prod_nc_data.get('dimensions', {}),
                    prod_nc_data.get('variables', {})
                )

                assets[f'{mode}-ocn-{pol}'] = NetCDFAsset(
                    path=f'{item_path}/{prod[j]}',
                    title=S1_OCN[pol.upper()]['title'],
                    description=S1_OCN[pol.upper()]['description'],
                    roles=('data', mode),
                    checksum=prod_checksum[j],
                    size=prod_size[j],
                    extra={
                        'data_type': 'float32',
                        'sar:polarizations': [pol.upper()],
                        'cube:dimensions': dims if isinstance(dims,
                                                              dict) else json.loads(
                            dims),
                        'cube:variables': vars if isinstance(vars,
                                                             dict) else json.loads(
                            vars),
                    },
                )

            if f'asset:{beam}:{pol}:osw' in attr:
                suffix = 'osw'
                asset = attr[f'asset:{beam}:{pol}:{suffix}']
                asset_checksum = attr[f'asset:{beam}:{pol}:{suffix}:checksum']
                asset_size = attr[f'asset:{beam}:{pol}:{suffix}:size']

                if asset:
                    nc_path = f"{item_path}/{asset[0].replace('./', '')}"
                    nc_data = extract_from_netcdf(Path(nc_path))

                    dims, vars = extract_dims_vars(
                        nc_data.get('dimensions', {}),
                        nc_data.get('variables', {})
                    )

                for j in range(len(asset)):
                    swath_id = asset[j][-6:-3]

                    assets[f'{beam}-{suffix}-{pol}-{swath_id}'] = NetCDFAsset(
                        path=f'{item_path}/{asset[j]}',
                        title=f'OSW Component',
                        description=f'The Ocean Swell Wave Spectra component - {beam.upper()}, {pol.upper()}',
                        roles=('data', beam),
                        checksum=asset_checksum[j],
                        size=asset_size[j],
                        extra={
                            'data_type': 'float32',
                            'sar:polarizations': [pol.upper()],
                            'cube:dimensions': dims if isinstance(dims,
                                                                  dict) else json.loads(
                                dims),
                            'cube:variables': vars if isinstance(vars,
                                                                 dict) else json.loads(
                                vars),
                        },
                    )



        elif mode == 'sm' and f'asset:product:{pol}:{beam}' in attr:
            prod = attr[f'asset:product:{pol}:{beam}']
            prod_checksum = attr[f'asset:product:{pol}:checksum:{beam}']
            prod_size = attr[f'asset:product:{pol}:size:{beam}']

            collection = 'sentinel-1-ocn'

            for j in range(len(prod)):
                assets[f'{mode}-ocn-{pol}'] = NetCDFAsset(
                    path=f'{item_path}/{prod[j]}',
                    title=S1_OCN[pol.upper()]['title'],
                    description=S1_OCN[pol.upper()]['description'],
                    roles=('data', mode),
                    checksum=prod_checksum[j],
                    size=prod_size[j],
                    extra={
                        'data_type': 'float32',
                        'sar:polarizations': [pol.upper()],
                        'cube:dimensions': attr['dimensions'],
                        'cube:variables': attr['variables'],
                    },
                )

        elif mode == 'wv' and f'asset:{beam}:{pol}:ocn' in attr:
            suffix = 'ocn'
            asset = attr[f'asset:{beam}:{pol}:{suffix}']
            asset_checksum = attr[f'asset:{beam}:{pol}:{suffix}:checksum']
            asset_size = attr[f'asset:{beam}:{pol}:{suffix}:size']

            collection = 'sentinel-1-ocn-wv'

            for j in range(len(asset)):
                swath_id = asset[j][-6:-3]

                assets[f'{beam}-{suffix}-{pol}-{swath_id}'] = NetCDFAsset(
                    path=f'{item_path}/{asset[j]}',
                    title=f'Wave Mode Vignette - {beam.upper()} ({pol.upper()})',
                    description=f'Single OCN vignette measurement (20x20 km) from beam {beam.upper()}. Contains OSW, OWI, and RVL components.',
                    roles=('data', beam),
                    checksum=asset_checksum[j],
                    size=asset_size[j],
                    extra={
                        'data_type': 'float32',
                        'sar:polarizations': [pol.upper()],
                    },
                )

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection=collection,
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=[
            TraceabilityLink(
                href=f'{attr["filename"]}.zip',
            )
        ],
        assets=assets,
        extensions=(
            StacExtension.SATELLITE,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SAR,
            StacExtension.EOPF,
        ) + (() if mode == 'wv' else (StacExtension.DATACUBE,)),
        extra=props,
    )

    return await item.generate()


def _get_timeliness(timeliness: str) -> str | None:
    match timeliness:
        case 'Fast-24h':
            return 'PT24H'
        case 'NRT-10m':
            return 'PT10M'
        case 'NRT-3h':
            return 'PT3H'
        case 'Reprocessing':
            return None
    raise ValueError(f'Unsupported timeliness {timeliness!r}')
