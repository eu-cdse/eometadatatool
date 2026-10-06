from typing import Any

from eometadatatool.dlc import format_baseline, get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    def mode_beams(mode: str) -> list[str]:
        match mode:
            case 'IW':
                return ['iw1', 'iw2', 'iw3']
            case 'SM':
                return ['s' + attr['filename'][5]]
            case 'EW':
                return ['ew1', 'ew2', 'ew3', 'ew4', 'ew5']
        raise ValueError(f'Unsupported mode beams {mode!r}')

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
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
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:platform_international_designator': attr['platformIdentifier'],
        'sat:anx_datetime': attr['anxTime'],
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.405,
        'sar:instrument_mode': attr['operationalMode'].upper(),
        'sar:beam_ids': mode_beams(attr['operationalMode'].upper()),
        'sar:polarizations': list(dict.fromkeys(p.upper() for p in pols)),
        'eopf:datatake_id': str(attr['datatakeID']),
        'eopf:instrument_configuration_id': attr['instrumentConfigurationID'],
        'view:incidence_angle': (
            attr['view_incidence_angle_min'] + attr['view_incidence_angle_max']
        )
        / 2,
    }

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
        'safe_manifest': ProductManifestAsset(
            path=f'{item_path}/manifest.safe',
            title='manifest.safe',
            description='General product metadata in XML format.',
            checksum=attr['manifest.safe:checksum'],
            size=attr['manifest.safe:size'],
        ),
        'annotation_schema': XMLAsset(
            path=f'{item_path}/{attr["etadAnnotation:file"]}',
            title='Schema annotation',
            description='Annotation schema file defining the metadata structure.',
            roles=['metadata'],
            checksum=attr['etadAnnotation:checksum'],
            size=attr['etadAnnotation:size'],
        ),
        'annotation_orbit': XMLAsset(
            path=f'{item_path}/{attr["etadOrbit:file"]}',
            title='Orbit annotation',
            description='Precise Orbit Ephemerides (POE) Orbit File',
            roles=['metadata'],
            checksum=attr['etadOrbit:checksum'],
            size=attr['etadOrbit:size'],
        ),
    }

    thumb_size = attr.get('asset:quicklook:size', 0)
    if thumb_size > 0:
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/{attr["asset:quicklook:file"]}',
            checksum=attr['asset:quicklook:checksum'],
            size=attr['asset:quicklook:size'],
        )

    assets['measurement'] = NetCDFAsset(
        path=f'{item_path}/{attr["etadNetCDF:file"]}',
        title='AUX ETA Measurement',
        description='NetCDF measurement file from a Sentinel-1 auxiliary product, containing timing and along track deviation related calibration data.',
        roles=['data'],
        checksum=attr['etadNetCDF:checksum'],
        size=attr['etadNetCDF:size'],
        extra={
            'data_type': 'float64',
            'proj:code': None,
            'proj:shape': [
                attr['shape1'],
                attr['shape2'],
            ],
        },
    )

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection='sentinel-1-etad',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=[
            TraceabilityLink(href=f'{attr["filename"]}.zip'),
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
