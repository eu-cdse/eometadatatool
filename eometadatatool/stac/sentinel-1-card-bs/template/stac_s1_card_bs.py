import re
from typing import Any

from eometadatatool.flags import is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import STACAsset, XMLAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.utils import generate_product_uuid

_IPF_VERSION_RE = re.compile(r'IPF\s+([\d.]+)')
_BAND_NAME_RE = re.compile(r'Gamma0_(\w+)\.(img|hdr)$')
_CENTRAL_MERIDIAN_RE = re.compile(r'central_meridian",\s*(-?[\d.]+)')
_FALSE_NORTHING_RE = re.compile(r'false_northing",\s*(-?[\d.]+)')


def _ipf_version(identifier: str) -> str | None:
    match = _IPF_VERSION_RE.search(identifier)
    return match.group(1) if match else None


def _epsg_from_auto_utm_wkt(wkt: str) -> str:
    """Derive the UTM EPSG code from a SNAP "WGS 84 / Auto UTM" WKT.

    SNAP's Auto UTM projection is computed per-scene and has no fixed EPSG
    code of its own, and the "zone" field written into the companion ENVI
    .hdr is not a real UTM zone (observed values exceed 60) -- so the zone
    and hemisphere are derived here from the standard, unambiguous
    central_meridian/false_northing WKT parameters instead.
    """
    central_meridian = float(_CENTRAL_MERIDIAN_RE.search(wkt).group(1))
    false_northing = float(_FALSE_NORTHING_RE.search(wkt).group(1))
    zone = round((central_meridian + 183) / 6)
    base = 32700 if false_northing > 0 else 32600
    return f'EPSG:{base + zone}'


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    item_path: str = attr['filepath']
    data_dir = f'{item_path}/{attr["filename"]}.data'

    pols: list[str] = []
    pol_ch1 = attr.get('polarisationChannel:1')
    if pol_ch1 and pol_ch1 != '-':
        pols.append(pol_ch1.upper())
    pol_ch2 = attr.get('polarisationChannel:2')
    if pol_ch2 and pol_ch2 != '-':
        pols.append(pol_ch2.upper())

    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': f'sentinel-{attr["missionId"].rsplit("-", 1)[-1].lower()}',
        'constellation': 'sentinel-1',
        'instruments': ['sar'],
        'processing:level': 'L2',
        'processing:facility': 'CloudFerro',
        'processing:datetime': attr['processingDate'],
        'processing:software': {'SNAP GPT': attr['gptVersion']},
        'product:type': 'CARD-BS',
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:orbit_cycle': attr['orbitCycle'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:absolute_orbit': attr['orbitNumber'],
        'sar:frequency_band': 'C',
        'sar:center_frequency': round(attr['radarFrequency'] / 1000, 3),
        'sar:instrument_mode': attr['acquisitionMode'].upper(),
        'sar:polarizations': pols,
        'sar:observation_direction': attr['antennaPointing'].lower(),
        'view:incidence_angle': round(
            (attr['incidenceNear'] + attr['incidenceFar']) / 2, 3
        ),
        'eopf:datatake_id': str(attr['datatakeID']),
    }

    if ipf_version := _ipf_version(attr['sourceProcessingSystemIdentifier']):
        props['processing:software']['Sentinel-1 IPF'] = ipf_version

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        props['_private']['product_uuid'] = generate_product_uuid(attr['identifier'])
        props['_private']['product_name'] = attr['identifier']
        props['_private']['visible'] = not hidden_flag

    assets: dict[str, STACAsset] = {
        'product_metadata': XMLAsset(
            path=f'{item_path}/{attr["filename"]}.dim',
            title='BEAM-DIMAP product metadata',
            description='Full product metadata (BEAM-DIMAP format) produced by the ESA SNAP Graph Processing Tool, including the processing graph used to derive this product.',
            roles=('metadata',),
            checksum=attr.get(f'{attr["filename"]}.dim:checksum:MD5'),
            size=attr.get(f'{attr["filename"]}.dim:size'),
        ),
    }

    hdr_names: dict[str, str] = {}
    for hdr_name in attr.get('asset:gamma0:hdr:name') or ():
        if match := _BAND_NAME_RE.search(hdr_name):
            hdr_names[match.group(1)] = hdr_name

    for img_name in attr.get('asset:gamma0:name') or ():
        match = _BAND_NAME_RE.search(img_name)
        if not match:
            continue
        pol = match.group(1)
        pol_title = pol.upper()

        assets[f'gamma0-{pol.lower()}'] = STACAsset(
            path=f'{data_dir}/{img_name}',
            media_type='application/x-envi',
            title=f'Gamma0 {pol_title}: terrain-corrected radiometrically calibrated backscatter',
            description=f'Gamma nought backscatter, {pol_title} polarization, radiometrically calibrated, thermal-noise-removed and terrain-corrected to ground range using a DEM.',
            roles=('data',),
            checksum=attr.get(f'{img_name}:checksum:MD5'),
            size=attr.get(f'{img_name}:size'),
            extra={
                'data_type': 'float32',
                'nodata': 0.0,
                'gsd': attr['rangePixelSpacing'],
                'proj:code': _epsg_from_auto_utm_wkt(attr['crsWKT']),
                'proj:shape': [attr['rasterHeight'], attr['rasterWidth']],
                'sar:polarizations': [pol_title],
                'sar:looks_range': int(attr['rangeLooks']),
                'sar:looks_azimuth': int(attr['azimuthLooks']),
                'sar:pixel_spacing_range': attr['rangePixelSpacing'],
                'sar:pixel_spacing_azimuth': attr['azimuthPixelSpacing'],
            },
        )

        if hdr_name := hdr_names.get(pol):
            assets[f'gamma0-{pol.lower()}-hdr'] = STACAsset(
                path=f'{data_dir}/{hdr_name}',
                media_type='text/plain',
                title=f'Gamma0 {pol_title} ENVI header',
                description='ENVI header file describing the raster layout, map info and coordinate reference system of the paired .img data file.',
                roles=('metadata',),
                checksum=attr.get(f'{hdr_name}:checksum:MD5'),
                size=attr.get(f'{hdr_name}:size'),
            )

    item = STACItem(
        path=item_path,
        odata=None,
        collection='sentinel-1-card-bs',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        assets=assets,
        product_asset_name=None,
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
