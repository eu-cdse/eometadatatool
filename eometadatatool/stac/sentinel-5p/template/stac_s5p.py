import re
from typing import Any

from dateutil import parser

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import NetCDFAsset, STACAsset
from eometadatatool.stac.framework.stac_bands import S5P_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink, TraceabilityLink

from .const import ASSET_TITLE_MAP, GSD_MAP, PRODUCT_TYPE_MAP, get_timeliness


def ensure_iso_datetime(value: str) -> str:
    if value is None:
        return None
    return parser.isoparse(value).strftime('%Y-%m-%dT%H:%M:%SZ')


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

    odata = await get_odata_id(attr['filepath'])

    extra = {
        'data_type': 'float32',
        'nodata': -999 if subtype.startswith('np-') else 9.9692099683868690e36,
    }
    if level == 1:
        extensions.append(StacExtension.EO)
        extra['bands'] = generate_bands(S5P_Bands, [subtype.upper()])

    assets: dict[str, STACAsset] = {
        'netcdf': NetCDFAsset(
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
        collection=f'sentinel-5p-l{level}-{subtype}-{attr["timeliness"].lower()}',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=extensions,
        product_asset_name=None,
        extra=props,
    )
    return await item.generate()
