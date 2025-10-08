from itertools import product
from typing import Any

from eometadatatool.dlc import format_baseline, get_odata_id, normalize_angle
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    STACAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import S1_Pols
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
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
        'processing:level': 'L1',
        'processing:facility': attr['processingCenter'],
        'processing:datetime': attr['processingDate'],
        'processing:version': format_baseline(attr['processorVersion']),
        'processing:software': {attr['processorName']: attr['processorVersion']},
        'product:type': attr['identifier'][4:14],
        'product:timeliness': _get_timeliness(attr['timeliness']),
        'product:timeliness_category': attr['timeliness'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:platform_international_designator': attr['platformIdentifier'],
        'sat:anx_datetime': attr['anxTime'],
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.405,
        'sar:instrument_mode': mode.upper(),
        'sar:beam_ids': ['wv1', 'wv2'],
        'sar:polarizations': [p.upper() for p in pols],
        'eopf:datatake_id': str(attr['datatakeID']),
        'eopf:instrument_configuration_id': attr['instrumentConfigurationID'],
    }

    if mode == 'iw':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 20
    elif mode == 'sm':
        props['sar:resolution_range'] = 5
        props['sar:resolution_azimuth'] = 5
    elif mode == 'ew':
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

    # Add core product assets
    # Process measurement data for each mode/polarization
    for beam, pol in product(['wv1', 'wv2'], pols):
        prod = attr[f'asset:{beam}:{pol}:product']
        prod_checksum = attr[f'asset:{beam}:{pol}:product:checksum']
        prod_size = attr[f'asset:{beam}:{pol}:product:size']
        calib = attr[f'asset:{beam}:{pol}:calibration']
        calib_checksum = attr[f'asset:{beam}:{pol}:calibration:checksum']
        calib_size = attr[f'asset:{beam}:{pol}:calibration:size']
        noise = attr[f'asset:{beam}:{pol}:noises']
        noise_checksum = attr[f'asset:{beam}:{pol}:noises:checksum']
        noise_size = attr[f'asset:{beam}:{pol}:noises:size']
        measure = attr[f'asset:{beam}:{pol}:measurement']
        measure_checksum = attr[f'asset:{beam}:{pol}:measurement:checksum']
        measure_size = attr[f'asset:{beam}:{pol}:measurement:size']

        for j in range(len(prod)):
            swath_id = prod[j][-7:-4]  # sequence number before the extension

            # Product
            assets[f'schema-product-{beam}-{pol}-{swath_id}'] = XMLAsset(
                path=f'{item_path}/{prod[j]}',
                title=f'{pol.upper()} Product Schema',
                description="Main source of band's metadata, including: state of the platform during acquisition, image properties, Doppler information, geographic location, etc.",
                roles=('metadata', beam),
                checksum=prod_checksum[j],
                size=prod_size[j],
            )

            # Calibration
            assets[f'schema-calibration-{beam}-{pol}-{swath_id}'] = XMLAsset(
                path=f'{item_path}/{calib[j]}',
                title=f'{pol.upper()} calibration Schema',
                description='Calibration metadata including calibration details and lookup tables for beta nought, sigma nought, gamma, and digital numbers used in absolute product calibration.',
                roles=('metadata', beam),
                checksum=calib_checksum[j],
                size=calib_size[j],
            )

            # Noise
            assets[f'schema-noise-{beam}-{pol}-{swath_id}'] = XMLAsset(
                path=f'{item_path}/{noise[j]}',
                title=f'{pol.upper()} noise Schema',
                description='Estimated thermal noise look-up tables',
                roles=('metadata', beam),
                checksum=noise_checksum[j],
                size=noise_size[j],
            )

            # Measurement
            assets[f'{beam}-{pol}-{swath_id}'] = CloudOptimizedGeoTIFFAsset(
                path=f'{item_path}/{measure[j]}',
                title=S1_Pols[pol.upper()]['title'],
                description=S1_Pols[pol.upper()]['description'],
                roles=('data', beam),
                checksum=measure_checksum[j],
                size=measure_size[j],
                extra={
                    'data_type': 'cint16',
                    'proj:code': None,
                    'proj:shape': [
                        attr[f'shape1:{beam}:{pol}'][j],
                        attr[f'shape2:{beam}:{pol}'][j],
                    ],
                    'sar:polarizations': [pol.upper()],
                    'sar:looks_range': attr[f'looksRange:{beam}:{pol}'][j],
                    'sar:looks_azimuth': attr[f'looksAzimuth:{beam}:{pol}'][j],
                    'sar:pixel_spacing_range': attr[f'rangePixelSpacing:{beam}:{pol}'][
                        j
                    ],
                    'sar:pixel_spacing_azimuth': attr[
                        f'azimuthPixelSpacing:{beam}:{pol}'
                    ][j],
                    'view:incidence_angle': attr[f'incidenceAngleMid:{beam}:{pol}'][j],
                    'view:azimuth': normalize_angle(
                        attr[f'azimuthAngle:{beam}:{pol}'][j]
                    ),
                },
            )

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection='sentinel-1-slc-wv',
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
            StacExtension.VIEW,
            StacExtension.EOPF,
        ),
        extra=props,
    )

    return await item.generate()


def _get_timeliness(timeliness: str) -> str:
    match timeliness:
        case 'Fast-24h':
            return 'PT24H'
        case 'NRT-10m':
            return 'PT10M'
        case 'NRT-3h':
            return 'PT3H'
    raise ValueError(f'Unsupported timeliness {timeliness!r}')
