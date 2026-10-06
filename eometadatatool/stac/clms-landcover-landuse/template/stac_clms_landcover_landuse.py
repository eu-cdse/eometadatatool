from typing import Any

import orjson
from shapely import from_geojson

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.gdalinfo import run_gdalinfo
from eometadatatool.stac.framework.clms_thumbnail import (
    native_bbox,
    stac_extra_from_gdalinfo,
    wms_thumbnail_asset,
)
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    ProductManifestAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink

from .const import VLCC_THUMBNAIL_SLD, get_asset_title, get_config


def create_thumbnail_asset(
    collection: str,
    data_path: str,
    data_extra: dict[str, Any],
    fallback_crs: str,
) -> STACAsset | None:
    if collection not in VLCC_THUMBNAIL_SLD:
        return None

    transform = data_extra.get('proj:transform')
    shape = data_extra.get('proj:shape')
    crs = data_extra.get('proj:code') or fallback_crs
    if not transform or not shape or not shape[0] or not shape[1] or not crs:
        return None

    bbox = data_extra.get('proj:bbox') or native_bbox(transform, shape)
    return wms_thumbnail_asset(
        layers=data_path,
        crs=crs,
        bbox=bbox,
        aspect=shape[1] / shape[0],
        sld=VLCC_THUMBNAIL_SLD[collection],
    )


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    item_path: str = attr['filepath']
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path, zipper=extended_private_data, omit_date=True)

    identifier = attr.get('identifier') or attr['filename']

    product_type, cfg = get_config(identifier)

    collection = cfg['collection']

    props: dict[str, Any] = {
        'gsd': cfg['gsd'],
        'proj:code': attr['epsg'],
        'product:type': product_type,
        'datetime': odata.content_isodate['Start'],
        'end_datetime': odata.content_isodate['End'],
    }
    if cfg['classification:classes']:
        props['classification:classes'] = cfg['classification:classes']

    geom = from_geojson(orjson.dumps(odata.geo_footprint))
    coordinates = geom.wkt

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

    data_path = f'{item_path}/{attr["filename"]}.tif'
    data_extra: dict[str, Any] = {}
    if gdalinfo_data := await run_gdalinfo(data_path):
        data_extra = await stac_extra_from_gdalinfo(
            orjson.loads(gdalinfo_data),
            fallback_proj_code=props['proj:code'],
        )
    data_extra['bands'] = cfg['bands']

    assets: dict[str, STACAsset] = {
        'metadata': ProductManifestAsset(
            path=f'{item_path}/{attr["filename"]}.xml',
            title='Product Metadata',
            description='General product metadata in XML format.',
            size=attr.get(f'{attr["filename"]}.xml:size'),
            checksum=attr.get(f'{attr["filename"]}.xml:checksum'),
        ),
        'data': CloudOptimizedGeoTIFFAsset(
            path=data_path,
            title=get_asset_title(identifier),
            roles=['data'],
            size=attr.get(f'{attr["filename"]}.tif:size'),
            checksum=attr.get(f'{attr["filename"]}.tif:checksum'),
            extra=data_extra,
        ),
    }
    if thumbnail := create_thumbnail_asset(
        collection,
        data_path,
        data_extra,
        props['proj:code'],
    ):
        assets['thumbnail'] = thumbnail

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
            StacExtension.CLASSIFICATION,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.EOPF,
            StacExtension.PROCESSING,
        ),
        extra=props,
    )
    return await item.generate()
