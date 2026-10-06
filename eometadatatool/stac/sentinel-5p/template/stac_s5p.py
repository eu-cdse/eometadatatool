import re
from typing import Any

from dateutil import parser

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import NetCDFAsset, STACAsset
from eometadatatool.stac.framework.stac_bands import S5P_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink, TraceabilityLink
from eometadatatool.stac.framework.utils import ensure_iso_datetime

from .const import ASSET_TITLE_MAP, GSD_MAP, PRODUCT_TYPE_MAP, get_timeliness


def gen_collection_id(level: int, subtype: str, timeliness: str) -> str:
    if 'ra-bd' in subtype:
        subtype = 'ra'

    match timeliness:
        case 'nrti':
            return f'sentinel-5p-l{level}-{subtype}-nrti'
        case _:
            return f'sentinel-5p-l{level}-{subtype}'

async def render(attr: dict[str, Any]) -> dict[str, Any]:
    subtype = PRODUCT_TYPE_MAP.get(attr['productType'])
    if not subtype:
        raise ValueError(f'Unknown product type: {attr["productType"]}')
    level: int = attr['level']

    if subtype == 'o3-tcl':
        # O3 TCL is a bit special
        orbit = int(re.search(r'O3_TCL_[\dT]+_[\dT]+_(\d+)_', attr['filename'])[1])
        shape = [40, 360]
        attr['timeliness'] = re.search(r'^[^_]*_([^_]*)', attr['identifier'])[1]
    else:
        orbit = attr['orbitNumber']
        shape = [
            attr['dimensions']['scanline']['extent'][-1],
            attr['dimensions']['ground_pixel']['extent'][-1],
        ]

    extensions = [
        StacExtension.PROCESSING,
        StacExtension.PRODUCT,
        StacExtension.PROJECTION,
        StacExtension.SATELLITE,
        StacExtension.DATACUBE,
    ]

    props: dict[str, Any] = {
        'datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'start_datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'end_datetime': ensure_iso_datetime(attr['endingDateTime']),
        'platform': 'sentinel-5p',
        'constellation': 'sentinel-5p',
        'instruments': ['tropomi'],
        'gsd': GSD_MAP.get(subtype, 3500),
        'proj:code': 'EPSG:4326' if level >= 2 else None,
        'proj:shape': shape,
        'sat:absolute_orbit': orbit,
        'sat:platform_international_designator': '2017-064A',
        'cube:dimensions': attr['dimensions'],
        'cube:variables': attr['variables'],
        'product:type': attr['productType'],
        'processing:level': f'L{level}',
    }

    if processing_center := attr.get('processingCenter'):
        props['processing:facility'] = processing_center

    if processing_date := attr.get('processingDate'):
        props['processing:datetime'] = ensure_iso_datetime(processing_date)

    timeliness_category = attr.get('timeliness')
    if timeliness := get_timeliness(timeliness_category, subtype):
        props['product:timeliness'] = timeliness
        props['product:timeliness_category'] = timeliness_category

    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(attr['filepath'], zipper=extended_private_data)

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

    extra = {
        'data_type': 'float32',
        'nodata': -999 if subtype.startswith('np-') else 9.9692099683868690e36,
    }
    if level == 1:
        extensions.append(StacExtension.EO)
        extra['bands'] = generate_bands(S5P_Bands, [subtype.upper()])

    assets: dict[str, STACAsset] = {
        'Product': NetCDFAsset(
            path=attr['filepath'],
            title=ASSET_TITLE_MAP[subtype],
            checksum=odata.checksum,
            size=odata.file_size,
            extra=extra,
        )
    }

    links: list[STACLink] = [TraceabilityLink(href=odata.name)]

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection=gen_collection_id(level, subtype, attr['timeliness'].lower()),
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=extensions,
        product_asset_name=None,
        extra=props,
    )
    return await item.generate()
