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

    props: dict[str, Any] = {
        'datetime': attr['datetime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'proj:code': attr['epsg'],
        'sar:polarizations': [
            attr['polarisations']
        ],
        'product:type': attr['productType'],
    }

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
        collection = 'ccm-dem',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=tuple(extensions),
        extra=props,
    )
    return await item.generate()

