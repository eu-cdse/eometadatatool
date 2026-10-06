from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    STACAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink
from eometadatatool.stac.framework.utils import ensure_iso_datetime


async def render(attr: dict[str, Any]) -> dict[str, Any]:

    props: dict[str, Any] = {
        'datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'start_datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'end_datetime': ensure_iso_datetime(attr['endingDateTime']),
        'platform': f'sentinel-1{attr["platformSerialIdentifier"].lower()}',
        'constellation': attr['platformShortName'].lower(),
        'instruments': [attr['instrumentShortName'].lower()],
        'processing:level': 'L1',
        'processing:facility': attr['processingCenter'],
        'processing:datetime': attr['processingDate'],
        'product:type': attr['productType'],
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'eopf:instrument_configuration_id': attr['instrumentConfigurationID'],
    }

    item_path: str = attr['filepath']

    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path[:-4], zipper=extended_private_data)

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
    }

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection=f'sentinel-1-aux-{attr["productType"][4:7].lower()}',
        identifier=attr['identifier'][:-9],
        coordinates=attr.get('coordinates', {}),
        links=[
            TraceabilityLink(href=f'{attr["filename"]}'),
        ],
        assets=assets,
        extensions=(
            StacExtension.SATELLITE,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SAR,
            StacExtension.EOPF,
        ),
        extra=props,
    )

    return await item.generate()
