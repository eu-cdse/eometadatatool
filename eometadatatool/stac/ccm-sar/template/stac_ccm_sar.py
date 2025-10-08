import re
from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import STACAsset, XMLAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    extensions = [
        StacExtension.PRODUCT,
        StacExtension.PROJECTION,
        StacExtension.SAR,
    ]

    platform_name_map = {
        # There's also CS00, which seems to refer to the entire COSMO-SkyMed constellation
        # but that's not a specific platform, so we only list the constellation
        "CS01": "cosmo-skymed-1",
        "CS02": "cosmo-skymed-2",
        "CS03": "cosmo-skymed-3",
        "CS04": "cosmo-skymed-4",
        "IE00": "iceye",
        "PAZ1": "paz",
        "RS02": "radarsat-2",
        "TX01": "terrasar-x"
    }

    constellation_map = {
        "CS": "cosmo-skymed",
        "IE": "iceye",
        "PAZ": "paz",
        "RS": "radarsat",
        "TX": "terrasar-x"
    }

    props: dict[str, Any] = {
        'datetime': attr['dateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'instruments': (attr['instrumentShortName'].lower(),),
        'product:type': attr['productType'],
        'sar:polarizations': (
            attr['polarisations']
            if isinstance(attr['polarisations'], list)
            else [p.strip() for p in str(attr['polarisations']).split(',')]
        )
    }
    
    if 'swathIdentifier' in attr and attr['swathIdentifier'] is not None:
        if isinstance(attr['swathIdentifier'], list):
            props['sar:beam_ids'] = attr['swathIdentifier']
        else:
            props['sar:beam_ids'] = [
                s.strip() for s in str(attr['swathIdentifier']).split(',')
            ]

    if attr.get('operationalMode'):
        props['sar:instrument_mode'] = attr.get('operationalMode')

    constellation_code = re.sub(r'\d+$', '', attr['platformShortName'])
    if constellation_code in constellation_map:
        props['constellation'] = constellation_map[constellation_code]

    if attr['platformShortName'] in platform_name_map:
        props['platform'] = platform_name_map[attr['platformShortName']]

    acq_type = attr.get('acquisitionType')
    if acq_type is not None:
        acq_type = acq_type.lower()
        props['product:acquisition_type'] = acq_type if acq_type in ('nominal', 'calibration') else 'other'

    abs_orbit = attr.get('orbitNumber')
    if abs_orbit is not None and abs_orbit > 0:
       extensions.append(StacExtension.SATELLITE)
       props['sat:absolute_orbit'] = abs_orbit

    odata = await get_odata_id(attr)
    item_path: str = attr['filepath']
    assets: dict[str, STACAsset] = {
        'circulation_report': XMLAsset(
            path=f'{item_path}/{attr["GSC:original_filename"]}',
            title='Circulation report',
            checksum=attr['GSC:checksum'],
            size=attr['GSC:size'],
            roles=['metadata']
        )
    }

    local_path = f'{odata.name}.zip'
    links: list[STACLink] = [
        STACLink(
            title='Product history record from the CDSE traceability service',
            rel='version-history',
            href=f'https://trace.dataspace.copernicus.eu/api/v1/traces/name/{local_path}',
            media_type='application/json',
        )
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection = 'ccm-sar',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=tuple(extensions),
        extra=props,
    )
    return await item.generate()

