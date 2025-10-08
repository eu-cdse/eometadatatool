from itertools import product
from typing import Any

from eometadatatool.dlc import format_baseline, get_odata_id, normalize_angle
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import S1_Pols
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    def mode_beams(mode: str) -> list[str]:
        match mode:
            case 'iw':
                return ['iw1', 'iw2', 'iw3']
            case 'sm':
                return ['s' + attr['filename'][5]]
            case 'ew':
                return ['ew1', 'ew2', 'ew3', 'ew4', 'ew5']
        raise ValueError(f'Unsupported mode beams {mode!r}')

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
        'sar:beam_ids': mode_beams(mode),
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

    # Check if product has thumbnail
    thumb_size = attr.get('thumbnail.png:size', 0)
    if thumb_size > 0:
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/preview/thumbnail.png',
            checksum=attr.get('thumbnail.png:checksum'),
            size=attr.get('thumbnail.png:size'),
        )

    # Process measurement data for each mode/polarization
    for beam, pol in product(mode_beams(mode), pols):
        # Product
        assets[f'schema-product-{beam}-{pol}'] = XMLAsset(
            path=f'{item_path}/{attr[f"asset:{beam}:{pol}:product"]}',
            title=f'{pol.upper()} Product Schema',
            description="Main source of band's metadata, including: state of the platform during acquisition, image properties, Doppler information, geographic location, etc.",
            roles=('metadata', beam),
            checksum=attr[f'asset:{beam}:{pol}:product:checksum'],
            size=attr[f'asset:{beam}:{pol}:product:size'],
        )

        # Calibration
        assets[f'schema-calibration-{beam}-{pol}'] = XMLAsset(
            path=f'{item_path}/{attr[f"asset:{beam}:{pol}:calibration"]}',
            title=f'{pol.upper()} calibration Schema',
            description='Calibration metadata including calibration details and lookup tables for beta nought, sigma nought, gamma, and digital numbers used in absolute product calibration.',
            roles=('metadata', beam),
            checksum=attr[f'asset:{beam}:{pol}:calibration:checksum'],
            size=attr[f'asset:{beam}:{pol}:calibration:size'],
        )

        # Noise
        assets[f'schema-noise-{beam}-{pol}'] = XMLAsset(
            path=f'{item_path}/{attr[f"asset:{beam}:{pol}:noises"]}',
            title=f'{pol.upper()} noise Schema',
            description='Estimated thermal noise look-up tables',
            roles=('metadata', beam),
            checksum=attr[f'asset:{beam}:{pol}:noises:checksum'],
            size=attr[f'asset:{beam}:{pol}:noises:size'],
        )

        # Measurement
        assets[f'{beam}-{pol}'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr[f"asset:{beam}:{pol}:measurement"]}',
            title=S1_Pols[pol.upper()]['title'],
            description=S1_Pols[pol.upper()]['description'],
            roles=('data', beam),
            checksum=attr[f'asset:{beam}:{pol}:measurement:checksum'],
            size=attr[f'asset:{beam}:{pol}:measurement:size'],
            extra={
                'data_type': 'cint16',
                'proj:code': None,
                'proj:shape': [
                    attr[f'shape1:{beam}:{pol}'],
                    attr[f'shape2:{beam}:{pol}'],
                ],
                'sar:polarizations': [pol.upper()],
                'sar:looks_range': attr[f'looksRange:{beam}:{pol}'],
                'sar:looks_azimuth': attr[f'looksAzimuth:{beam}:{pol}'],
                'sar:pixel_spacing_range': attr[f'rangePixelSpacing:{beam}:{pol}'],
                'sar:pixel_spacing_azimuth': attr[f'azimuthPixelSpacing:{beam}:{pol}'],
                'view:incidence_angle': attr[f'incidenceAngleMid:{beam}:{pol}'],
                'view:azimuth': normalize_angle(attr[f'azimuthAngle:{beam}:{pol}']),
            },
        )

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection='sentinel-1-slc',
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
