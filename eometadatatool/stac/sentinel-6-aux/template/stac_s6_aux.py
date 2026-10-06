from typing import Any
from pathlib import PurePath

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import GzipProductAsset, STACAsset, TarProductAsset, TgzProductAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink
from eometadatatool.stac.framework.utils import ensure_iso_datetime


def _recognize_collection(scene_name: str) -> str:
    if '_OPER_AUX_' in scene_name:
        suffix = scene_name[13:19].strip('_').lower()
    elif scene_name[4:6] == 'AX':
        suffix = (
            scene_name[4:17].removeprefix('AX').removesuffix('_AX').strip('_').lower()
        )
    else:
        suffix = scene_name[3:7].lower()  # COMB
    return f'sentinel-6-aux-{suffix}'


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {
        'datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'start_datetime': ensure_iso_datetime(attr['beginningDateTime']),
        'end_datetime': ensure_iso_datetime(attr['endingDateTime']),
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': [attr['instrumentShortName'].lower()],
        'product:type': attr['productType'],
    }
    if facility := (
        attr.get('processingFacilityName') or attr.get('processingCenter')
    ):
        props['processing:facility'] = facility
    if processing_date := attr.get('processingDate'):
        props['processing:datetime'] = ensure_iso_datetime(processing_date)
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version
    if timeliness := attr.get('timeliness'):
        props['product:timeliness_category'] = timeliness

    item_path: str = attr['filepath']

    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(
        item_path.removesuffix('.tar').removesuffix('.tgz').removesuffix('.gz').removesuffix('.TGZ'),
        zipper=extended_private_data,
    )

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

    assets: dict[str, STACAsset] = {}

    scene_name = PurePath(attr['filepath']).name
    collection = _recognize_collection(scene_name)

    if scene_name.endswith(('.tgz', '.TGZ')):
        product_asset_cls = TgzProductAsset
    elif scene_name.endswith('.gz'):
        product_asset_cls = GzipProductAsset
    else:
        product_asset_cls = TarProductAsset

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
        identifier=attr['identifier'].split('.', 1)[0],
        coordinates=attr.get('coordinates', {}),
        links=[
            TraceabilityLink(href=f'{odata.name}.zip'),
        ],
        assets=assets,
        product_asset_cls=product_asset_cls,
        extensions=(
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
        ),
        extra=props,
    )
    return await item.generate()
