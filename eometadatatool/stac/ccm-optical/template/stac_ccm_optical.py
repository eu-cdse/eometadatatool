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
        StacExtension.PROJECTION
    ]

    platform_name_map = {
        "AL01": "alos-1",
        "BJ01": "beijing-1",
        "DE01": "geosat-1",
        "DM01": "geosat-1",
        "DM02": "geosat-2",
        "EW02": "worldview-2",
        "EW03": "worldview-3",
        "FO02": "formosat2",
        "GY01": "geoeye-1",
        "IR06": "resourcesat-1",
        "IR07": "resourcesat-2",
        "KS03": "kompsat-3",
        "KS04": "kompsat-3a",
        "NG01": "nigeriasat-1",
        "PH1A": "pleiades-1a",
        "PH1B": "pleiades-1b",
        "PL00": "planetscope",
        "PN03": "pleiades-neo-3",
        "PN04": "pleiades-neo-4",
        "QB02": "quickbird-2",
        "RE00": "rapideye",
        "S20A": "sentinel-2a",
        "SP04": "spot-4",
        "SP05": "spot-5",
        "SP06": "spot-6",
        "SP07": "spot-7",
        "UK01": "uk-dmc1",
        "UK02": "uk-dmc2",
        "VS01": "vision-1"
    }

    constellation_map = {
        "AL": "alos",
        "AR3D": "alos",
        "BJ": "beijing",
        "DC": "dmc",
        "DE": "geosat",
        "DM": "geosat",
        "EW": "worldview",
        "FO": "formosat",
        "GY": "geoeye",
        "IR": "resourcesat",
        "KS": "kompsat",
        "NG": "nigeriasat",
        "PH": "pleiades",
        "PL": "planetscope",
        "PN": "pleiades-neo",
        "QB": "quickbird",
        "RE": "rapideye",
        "S2": "sentinel-2",
        "SP": "spot",
        "SW": "superview",
        "TR": "triplesat",
        "UK": "uk-dmc",
        "VS": "vision"
    }

    level_map = {
        "Level 1": "L1",
        "Ortho-rectified Level": "L2",
        "Orthorectified": "L2"
    }

    props: dict[str, Any] = {
        'datetime': attr.get('datetime'),
        'start_datetime': attr.get('beginningDateTime'),
        'end_datetime': attr.get('endingDateTime'),
        'instruments': (attr['instrumentShortName'].lower(),),
        'proj:code': attr.get('epsg'),
        'product:type': attr.get('productType'),
    }

    constellation_code = re.sub(r'\d+$', '', attr['platformShortName'])
    if constellation_code in constellation_map:
        props['constellation'] = constellation_map[constellation_code]

    if attr['platformShortName'] in platform_name_map:
        props['platform'] = platform_name_map[attr['platformShortName']]

    level = attr.get('processingLevel')
    if level in level_map:
        extensions.append(StacExtension.PROCESSING)
        props['processing:level'] = level_map[level]

    acq_type = attr.get('acquisitionType')
    if acq_type is not None:
        acq_type = acq_type.lower()
        props['product:acquisition_type'] = acq_type if acq_type in ('nominal', 'calibration') else 'other'

    potential_fields = {
        'cloudCoverPercentage': 'eo:cloud_cover',
        'acrossTrackIncidenceAngle': 'view:incidence_angle',
        'illuminationAzimuthAngle': 'view:sun_azimuth',
        'illuminationElevationAngle': 'view:sun_elevation',
        'orbitState': 'sat:orbit_state',
    }
    for source, target in potential_fields.items():
        value = attr.get(source)
        if value is not None:
            props[target] = abs(value)


    potential_fields_gt_0 = {
        'resolution': 'gsd',
        'orbitNumber': 'sat:absolute_orbit',
    }
    for source, target in potential_fields_gt_0.items():
        value = attr.get(source)
        if value is not None and value > 0:
            props[target] = value

    if 'eo:cloud_cover' in props:
       extensions.append(StacExtension.EO)
    if 'sat:absolute_orbit' in props or 'sat:orbit_state' in props:
       extensions.append(StacExtension.SATELLITE)
    if 'view:incidence_angle' in props or 'view:sun_azimuth' in props or 'view:sun_elevation' in props:
       extensions.append(StacExtension.VIEW)

    odata = await get_odata_id(attr)
    item_path: str = attr['filepath']
    assets: dict[str, STACAsset] = {}

    if 'GSC:original_filename' in attr:
        assets['circulation_report'] = XMLAsset(
            path=f'{item_path}/{attr["GSC:original_filename"]}',
            title='Circulation report',
            checksum=attr.get('GSC:checksum'),
            size=attr.get('GSC:size'),
            roles=['metadata']
        )

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
        collection = 'ccm-optical',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=tuple(extensions),
        extra=props,
    )

    return await item.generate()

