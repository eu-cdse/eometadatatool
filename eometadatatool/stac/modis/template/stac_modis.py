from typing import Any, Final

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_hidden, is_no_private, is_extended_private_data
from eometadatatool.stac.framework.stac_asset import HDFAsset, ThumbnailAsset, XMLAsset
from eometadatatool.stac.framework.stac_bands import MODIS_BANDS
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink, TraceabilityLink, ZipperLink


GSD_TO_PROJ_SHAPE: Final[dict[int, list[int]]] = {
    250: [4800, 4800],
    500: [2400, 2400],
    1000: [1200, 1200],
}

PT_BASE_TO_GSD: Final[dict[str, int]] = {
    # 250m
    "MOD09Q1": 250, "MYD09Q1": 250, "MOD13Q1": 250, "MYD13Q1": 250,
    # 1000m
    "MOD11A1": 1000, "MOD11A2": 1000, "MYD11A1": 1000, "MYD11A2": 1000,
    "MOD14A1": 1000, "MOD14A2": 1000, "MYD14A1": 1000, "MYD14A2": 1000,
    "MOD21A2": 1000, "MYD21A2": 1000, "MOD13A2": 1000, "MYD13A2": 1000,
    # 500m
    "MOD09A1": 500, "MYD09A1": 500,
    "MOD10A1": 500, "MOD10A2": 500, "MYD10A1": 500, "MYD10A2": 500,
    "MOD13A1": 500,  "MYD13A1": 500,
    "MOD15A2H": 500, "MYD15A2H": 500, "MCD15A2H": 500, "MCD15A3H": 500,
    "MOD16A2GF": 500, "MOD16A3GF": 500, "MYD16A3GF": 500,
    "MOD17A2H": 500, "MOD17A2HGF": 500, "MOD17A3HGF": 500,
    "MYD17A2H": 500, "MYD17A2HGF": 500, "MYD17A3HGF": 500,
    "MCD12Q1": 500, "MCD43A4": 500, "MCD64A1": 500,
}

L4: Final[set[str]] = {
    "MOD15A2H", "MYD15A2H", "MCD15A2H", "MCD15A3H",
    "MOD16A2GF", "MOD16A3GF", "MYD16A3GF",
    "MOD17A2H", "MOD17A2HGF", "MOD17A3HGF",
    "MYD17A2H", "MYD17A2HGF", "MYD17A3HGF",
}
L3: Final[set[str]] = {
    "MOD09A1", "MOD09Q1", "MYD09A1", "MYD09Q1",
    "MOD10A1", "MOD10A2", "MYD10A1", "MYD10A2",
    "MOD11A1", "MOD11A2", "MYD11A1", "MYD11A2",
    "MOD13A1", "MOD13A2", "MOD13Q1", "MYD13A1", "MYD13A2", "MYD13Q1",
    "MOD14A1", "MOD14A2", "MYD14A1", "MYD14A2",
    "MOD21A2", "MYD21A2",
    "MCD12Q1", "MCD43A4", "MCD64A1",
}

SAT_INTL_DESIGNATORS = {
    "terra": "1999-068A",
    "aqua": "2002-022A",
}

PRODUCT_PREFIX_TO_PLATFORM: Final[dict[str, str]] = {
    "MOD": "terra",
    "MYD": "aqua",
    "MCD": ["terra", "aqua"]
}


def get_list(attr, prefix) -> set[str]:
    result = set()
    for i in range(1, 3):
        value = attr.get(f"{prefix}{i}", "").strip().lower()
        if len(value) > 0:
            result.add(value)
    return result


def get_stat(attr: dict[str, Any], prop: str) -> float | None:
    value = attr.get(prop)
    if value is not None and len(value) > 0:
        return round(float(value), 1)
    return None


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    extensions = {
        StacExtension.GRID,
        StacExtension.PROCESSING,
        StacExtension.PRODUCT,
        StacExtension.PROJECTION,
    }

    product = attr["productType"].split(".")[0]

    gsd = PT_BASE_TO_GSD[product]
    shape = GSD_TO_PROJ_SHAPE[gsd]

    props = {
        "datetime": attr["beginningDateTime"],
        "start_datetime": attr["beginningDateTime"],
        "end_datetime": attr["endingDateTime"],
        "constellation": "modis",
        "processing:datetime": attr["processingDate"],
        "processing:version": attr["processorVersion"],
        "product:type": product,
        "grid:code": f"MSIN-{attr['hTile']}{attr['vTile']}",
        "gsd": gsd,
        "instruments": ["modis"]
    }

    product_prefix = product[:3].upper()
    platform_from_product = PRODUCT_PREFIX_TO_PLATFORM.get(product_prefix)

    if isinstance(platform_from_product, str):
        props["platform"] = platform_from_product
        props["sat:platform_international_designator"] = (
            SAT_INTL_DESIGNATORS[platform_from_product]
        )
        extensions.add(StacExtension.SATELLITE)

    if orbit := attr.get("orbitNumber"):
        props["sat:absolute_orbit"] = orbit
        extensions.add(StacExtension.SATELLITE)

    processing_level = "L4" if product in L4 else ("L3" if product in L3 else None)
    if processing_level:
        props["processing:level"] = processing_level

    cloud_cover = get_stat(attr, "cloudCover")
    if cloud_cover is not None:
        props["eo:cloud_cover"] = cloud_cover
        extensions.add(StacExtension.EO)

    stats_keys = ["missing_data", "out_of_bounds_data", "interpolated_data"]
    stats = {
        key: value
        for key in stats_keys
        if (value := get_stat(attr, key)) is not None
    }
    if len(stats) > 0:
        props["statistics"] = stats

    bands = list(MODIS_BANDS[product].values())

    item_path: str = attr["filepath"]
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(item_path, zipper=extended_private_data)

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props["_private"] = {}
        props["_private"]["product_size"] = attr["private:product_size"]
        props["_private"]["product_uuid"] = odata.id
        props['_private']['product_name'] = odata.name
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

        if extended_private_data:
            props['_private']['brands'] = odata.zipper_data

    xml_key = next((k for k in attr if k.endswith(".xml:checksum")), None).split(':')[0]
    hdf_key = next((k for k in attr if k.endswith(".hdf:checksum")), None).split(':')[0]

    assets: dict[str, Any] = {
        "metadata": XMLAsset(
            path=f"{item_path}/{xml_key}",
            title=f"{xml_key}",
            roles=("metadata",),
            checksum=attr[next(k for k in attr if k.endswith("xml:checksum"))],
            size=attr[next(k for k in attr if k.endswith("xml:size"))],
        ),
        "data": HDFAsset(
            path=f"{item_path}/{hdf_key}",
            title=f"{hdf_key}",
            roles=("data",),
            checksum=attr[next(k for k in attr if k.endswith(".hdf:checksum"))],
            size=attr[next(k for k in attr if k.endswith(".hdf:size"))],
            extra={
                "bands": bands,
                "proj:shape": shape,
            },
        ),
    }

    jpg_checksum_key = next((k for k in attr if k.endswith(".jpg:checksum")), None)
    jpg_size_key = next((k for k in attr if k.endswith(".jpg:size")), None)
    if jpg_checksum_key and jpg_size_key:
        assets["thumbnail"] = ThumbnailAsset(
            path=f"{item_path}/{jpg_checksum_key.split(':')[0]}",
            title=f"{jpg_checksum_key.split(':')[0]}",
            roles=("thumbnail", "graphic"),
            checksum=attr[jpg_checksum_key],
            size=attr[jpg_size_key],
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f"{odata.name}.zip"),
    ]

    collection_id = [
        "modis",
        "".join(platform_from_product),
        product.lower(),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection="-".join(collection_id),
        identifier=attr["identifier"],
        coordinates=attr["coordinates"],
        links=links,
        product_asset_name="Product",
        assets=assets,
        extensions=tuple(extensions),
        extra=props,
    )

    return await item.generate()
