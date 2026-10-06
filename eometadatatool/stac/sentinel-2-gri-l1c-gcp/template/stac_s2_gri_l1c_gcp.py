import re
from datetime import UTC, datetime
from typing import Any

from eometadatatool.stac.framework.stac_asset import STACAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink
from eometadatatool.stac.framework.utils import generate_product_uuid
from eometadatatool.flags import is_no_private, is_hidden


def calculate_bbox_wkt(coord_string: str) -> str:
    """
    Calculate bbox from coordinate pairs
    :param coord_string: string with coordinate pairs
    :return: bbox as wkt string
    """
    coord_pairs = coord_string.split(',')

    x_coords: list[float] = []
    y_coords: list[float] = []

    for pair in coord_pairs:
        x, y = map(float, pair.strip().split())
        x_coords.append(x)
        y_coords.append(y)

    min_x = min(x_coords)
    max_x = max(x_coords)
    min_y = min(y_coords)
    max_y = max(y_coords)

    wkt = f'POLYGON(({min_x} {min_y}, {max_x} {min_y}, {max_x} {max_y}, {min_x} {max_y}, {min_x} {min_y}))'

    return wkt

def convert_coordinate_string(filename: str) -> str | None:
    """
    Determine grid:code based on file name.
    :param filename: product file name
    :return: grid:code string
    """
    match = re.search(r'([NS]\d{2}[EW]\d{3})', filename)
    if not match:
        return None
    coord = match.group(1)

    return f'CDEM-{coord}'


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    start_datetime = datetime(2015, 6, 23, 1, 52, 0, tzinfo=UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_datetime = datetime(2262, 1, 1, 0, 0, 0, tzinfo=UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    props = {
        'datetime': start_datetime,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'constellation': 'sentinel-2',
        'instruments': ['msi'],
        'gsd': 10,
        'processing:level': 'L1',
        'product:type': 'S2GRIL1CGCP'
    }

    grid_code = convert_coordinate_string(attr['identifier'])
    if grid_code:
        props['grid:code'] = grid_code

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
        if re.match(r'^[NS]\d{2}[EW]\d{3}_L1C\.tar\.gz$', value.path.name):
            assets['gcp'] = STACAsset(
                path=str(value.path).replace('s3:/', 's3://'),
                media_type='application/x-gtar',
                title='Tarball compressed product',
                roles=['data'],
                include_other_alternates=False
            )
        if re.match(r'^[NS]\d{2}[EW]\d{3}.json$', value.path.name):
            assets['gcp_metadata'] = STACAsset(
                path=str(value.path).replace('s3:/', 's3://'),
                media_type='application/json',
                title='JSON metadata',
                roles=['metadata'],
                include_other_alternates=False,
            )

    item = STACItem(
        path=item_path,
        odata=None,
        collection='sentinel-2-gri-l1c-gcp',
        identifier=attr['identifier'],
        coordinates=calculate_bbox_wkt(attr['extent']),
        assets=assets,
        extensions=(StacExtension.GRID,),
        extra=props,
    )

    return await item.generate()
