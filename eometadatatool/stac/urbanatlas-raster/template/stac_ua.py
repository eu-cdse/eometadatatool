from typing import Any
import re

from shapely import from_geojson
import orjson

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import CloudOptimizedGeoTIFFAsset, STACAsset, ProductManifestAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink
from eometadatatool.flags import is_no_private, is_hidden, is_extended_private_data

async def render(attr: dict[str, Any]) -> dict[str, Any]:
    item_path: str = attr['filepath']
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path, zipper=extended_private_data)

    match = re.search(r'_([A-Z]{2})\d{3}L\d_(.+?)_\d{5}_', attr['identifier'])

    props: dict[str, Any] = {
        'gsd': 10,
        'proj:code': attr['epsg'],
        'product:type': 'urban_atlas',
        'datetime': odata.content_isodate['Start'],
        'end_datetime': odata.content_isodate['End'],
        'region:country': 'UK' if match.group(1) == 'GB' else match.group(1),
        'region:name': match.group(2).replace('_', ' ').title(),
    }

    geom = from_geojson(orjson.dumps(odata.geo_footprint))
    coordinates = geom.wkt

    collection = 'clms_ua_building-height_europe_10m_3yearly_v1'

    identifier = attr.get('identifier', attr.get('filename', attr['name']))

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

        if odata.attributes:
            props['_private'].update(odata.attributes)

    assets: dict[str, STACAsset] = {
        'metadata': ProductManifestAsset(
            path=f'{item_path}/{attr['name']}.xml',
            title='Product Metadata',
            description='General product metadata in XML format.',
            size=attr.get(f'{attr['name']}.xml:size'),
            checksum=attr.get(f'{attr['name']}.xml:checksum'),
        ),
        'data': CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr['name']}.tif',
            title='Urban Atlas Building Height Raster (10m)',
            roles=['data'],
            size=attr.get(f'{attr['name']}.tif:size'),
            checksum=attr.get(f'{attr['name']}.tif:checksum'),
        ),
    }

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection=collection,
        identifier=identifier,
        coordinates=coordinates,
        links=[
            TraceabilityLink(
                href=f'{identifier}.zip',
            )
        ],
        assets=assets,
        extensions=(
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.EOPF,
            StacExtension.PROCESSING,
            StacExtension.REGION,
        ),
        extra=props,
    )
    return await item.generate()
