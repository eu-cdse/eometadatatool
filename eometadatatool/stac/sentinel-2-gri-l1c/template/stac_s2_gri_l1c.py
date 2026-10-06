from typing import Any

from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform

from eometadatatool.stac.framework.stac_asset import JPEG2000Asset, XMLAsset
from eometadatatool.stac.framework.stac_bands import S2_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink
from eometadatatool.stac.framework.utils import generate_product_uuid
from eometadatatool.flags import is_no_private, is_hidden


def raster_extent_wkt(ulx: int, uly: int, ncols: int, nrows: int, xres: int, yres: int, epsg: int) -> str:
    """
    Calculate bbox from available metadata
    :param ulx: upper left x coordinate
    :param uly: upper left y coordinate
    :param ncols: number of columns
    :param nrows: number of rows
    :param xres: x dimension
    :param yres: y dimension
    :param epsg: epsg code
    :return: wkt string
    """
    lrx = ulx + ncols * xres
    lry = uly + nrows * yres

    poly = Polygon([
        (ulx, uly),  # upper-left
        (lrx, uly),  # upper-right
        (lrx, lry),  # lower-right
        (ulx, lry),  # lower-left
        (ulx, uly),  # close polygon
    ])

    transformer = Transformer.from_crs(epsg, 4326, always_xy=True)
    poly_4326 = transform(transformer.transform, poly)

    return poly_4326.wkt

async def render(attr: dict[str, Any]) -> dict[str, Any]:
    props = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': attr['platformSerialIdentifier'].lower(),
        'constellation': 'sentinel-2',
        'instruments': ['msi'],
        'gsd': 10,
        'processing:level': 'L1',
        'processing:datetime': attr['processingDate'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'product:type': 'S2GRIL1C',
        'grid:code': attr['grid:code'],
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        props['_private']['product_uuid'] = generate_product_uuid(attr['identifier'])
        props['_private']['product_name'] = attr['identifier']
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

    item_path: str = attr['filepath']
    assets: dict = {}
    for value in attr['s3_scene'].subkeys.values():
        if '_MTD_L1C_DS_' in value.path.name:
            assets['datastrip_metadata'] = XMLAsset(
                path=str(value.path).replace('s3:/', 's3://'),
                title='Datastrip metadata',
                roles=('metadata',),
                size=value.size,
                include_other_alternates=False
            )
        if '_MTD_L1C_TL_' in value.path.name:
            assets['tile_metadata'] = XMLAsset(
                path=str(value.path).replace('s3:/', 's3://'),
                title='Tile metadata',
                roles=('metadata',),
                size=value.size,
                include_other_alternates=False
            )
        if 'B04' in value.path.name and 'IMG_DATA' in value.path.parent.name:
            assets['B04'] = JPEG2000Asset(
                path=str(value.path).replace('s3:/', 's3://'),
                title='Red (band 4) - 10m',
                roles=('data',),
                size=value.size,
                include_other_alternates=False,
                extra={
                    'bands': generate_bands(S2_Bands, ['B04']),
                    'data_type': 'uint16',
                    'gsd': 10,
                    'proj:code': f'EPSG:{attr['csCode']}',
                    'proj:shape': [
                        attr['colsNum'],
                        attr['rowsNum'],
                    ],
                },
            )

    item = STACItem(
        path=item_path,
        odata=None,
        collection='sentinel-2-gri-l1c',
        identifier=attr['identifier'],
        coordinates=raster_extent_wkt(attr['upperLeftX'],attr['upperLeftY'],attr['colsNum'],attr['rowsNum'],attr['xDim'],attr['yDim'],attr['csCode']),
        assets=assets,
        extensions=(
            StacExtension.SATELLITE,
            StacExtension.PRODUCT,
            StacExtension.GRID
        ),
        extra=props,
    )

    return await item.generate()
