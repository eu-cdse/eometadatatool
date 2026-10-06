import logging
import re
from collections.abc import Collection
from typing import Any

import orjson

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.gdalinfo import run_gdalinfo
from eometadatatool.s3_utils import S3Path
from eometadatatool.stac.framework.clms_thumbnail import (
    native_bbox,
    stac_extra_from_gdalinfo,
    wms_thumbnail_asset,
)
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    JsonAsset,
    NetCDFAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink, TraceabilityLink
from eometadatatool.stac.framework.utils import ensure_iso_datetime

from .const import (
    PLATFORM_CONSTELLATION_MAP,
    PROD_MAP,
    THUMBNAIL_MAP,
)


def _apply_layer_rule(identifier: str, rule: list) -> str:
    """Derive the rendered COG band filename from an item identifier.

    See ``THUMBNAIL_MAP`` in ``const.py`` for the rule encoding.
    """
    style, idx, tokens, ext = rule
    base = re.sub(r'_(cog|nc)$', '', identifier)
    if style == 'same':
        return f'{base}.{ext}'
    fields = base.split('_')
    if style == 'u':
        fields[idx:idx] = tokens
        return f'{"_".join(fields)}.{ext}'
    # 'd': insert dash-segment(s) inside underscore field ``idx[0]``
    field_idx, seg_idx = idx
    segs = fields[field_idx].split('-')
    segs[seg_idx:seg_idx] = tokens
    fields[field_idx] = '-'.join(segs)
    return f'{"_".join(fields)}.{ext}'


def _asset_filename(asset: STACAsset) -> str:
    return asset.path.rsplit('/', 1)[-1]


def _thumbnail_layers(
    assets: dict[str, STACAsset], identifier: str, file_type: str, rule: list
) -> str | None:
    """Resolve the WMS LAYERS path (an ``s3://eodata`` COG band file)."""
    if file_type == 'nc':
        product = assets.get('Product')
        if not product:
            return None
        folder, _name = product.path.rsplit('/', 1)
        if not folder.endswith('_nc'):
            return None
        # NetCDF items render their COG twin (same product folder, _nc -> _cog)
        return f'{folder[:-3]}_cog/{_apply_layer_rule(identifier, rule)}'
    if rule[0] == 'match':
        substr = rule[1]
        for asset in assets.values():
            if substr in _asset_filename(asset):
                return asset.path
        return None
    target = _apply_layer_rule(identifier, rule)
    for asset in assets.values():
        if _asset_filename(asset) == target:
            return asset.path
    return None


def create_thumbnail_asset(
    assets: dict[str, STACAsset],
    props: dict[str, Any],
    subtype: str,
    file_type: str,
    identifier: str,
) -> STACAsset | None:
    cfg = THUMBNAIL_MAP.get(subtype)
    if cfg is None or file_type not in ('cog', 'nc'):
        return None

    layers = _thumbnail_layers(assets, identifier, file_type, cfg['rule'])
    if layers is None:
        return None

    if cfg['tiled']:
        target = layers.rsplit('/', 1)[-1]
        asset = next(
            (a for a in assets.values() if _asset_filename(a) == target),
            None,
        )
        asset_extra = asset.extra if asset else {}
        transform = asset_extra.get('proj:transform') or props.get('proj:transform')
        shape = asset_extra.get('proj:shape') or props.get('proj:shape')
        if not transform or not shape or not shape[0] or not shape[1]:
            return None
        bbox = asset_extra.get('proj:bbox') or native_bbox(transform, shape)
        crs = cfg['crs'] or props.get('proj:code')
        aspect = shape[1] / shape[0]
    else:
        bbox = cfg['bbox']
        crs = cfg['crs']
        aspect = (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])
    if bbox is None or crs is None:
        return None

    return wms_thumbnail_asset(
        layers=layers,
        crs=crs,
        bbox=bbox,
        aspect=aspect,
        sld=cfg['sld'],
    )


def identify_type(identifier: str) -> str | None:
    """Identify product type by its identifier."""
    if re.search(r'_nc', identifier):
        return 'nc'
    if re.search(r'_cog', identifier):
        return 'cog'
    if re.search(r'_geojson', identifier):
        return 'geojson'

    return None


def identify_product(
    file_path: str, prod_map: dict
) -> tuple[str, Any] | tuple[None, None]:
    """Get metadata for product by its type (odata's datasetIdentifier)."""
    try:
        prod_type = file_path.split('/')[6]
        return prod_type, prod_map[prod_type]
    except KeyError:
        return None, None


def identify_platform_constellation(
    platform: str | None,
) -> tuple[str, str] | tuple[None, None]:
    """Get constellation for product based on its platform. If data comes from more than one satellite, we omit both."""
    if platform is None or len(platform.split(',')) > 1:
        return None, None

    for pattern, sat_platform, constellation in PLATFORM_CONSTELLATION_MAP:
        if re.search(pattern, platform, re.IGNORECASE):
            return sat_platform, constellation

    return None, None


def create_bands_netcdf(vars_dict: dict[str, Any]) -> dict[str, Any] | None:
    """Create netcdf_bands dict from variables for netCDF products."""
    netcdf_bands: list[dict] = []
    for key, value in vars_dict.items():
        if key not in ['lat', 'lat_bounds', 'lon', 'lon_bounds', 'time']:
            try:
                netcdf_bands.append({
                    'name': key,
                    'description': value.get('description')
                    if value.get('description') and value.get('description') != ''
                    else key.replace('_', ' '),
                })
            except KeyError:
                continue
    return netcdf_bands if len(netcdf_bands) > 0 else None


def _strip_product_prefix(asset_name: str, scene_name: str) -> str:
    """Drop the leading token of ``asset_name`` when it repeats the product code.

    ``c_gls_*`` band files carry the product code inside the variable field
    (``NDVI300-NDVI`` → ``ndvi``, ``LIE-NH-LIE`` → ``nh_lie``), while ``clms_*``
    band files keep the product code in its own field, so their variable field is
    already prefix-free and must be left alone (``ETA300_E-ENSEMBLE`` →
    ``e_ensemble``, not ``ensemble``).
    """
    if '_' not in asset_name:
        return asset_name
    head, tail = asset_name.split('_', 1)
    tokens = {t.lower() for field in scene_name.split('_') for t in field.split('-')}
    return tail if head in tokens else asset_name


def create_bands_cog(gdalinfo_bands: list[dict], asset_name: str) -> list[dict] | None:
    """Create band dict from gdalinfo_bands for COG products.

    Band names match the asset name they belong to.

    For hourly multi-band products (e.g. LST Daily Cycle), where the asset name ends
    with a ``_HH_HH`` hour-range suffix and the COG contains more than one band, the
    range suffix is replaced with the zero-padded hour parsed from each band's
    description (e.g. ``dc_fobs_00_11`` → ``dc_fobs_00``, ``dc_fobs_01``, …).
    """
    # Hourly multi-band case: name ends with _HH_HH and there are multiple bands
    is_hourly = len(gdalinfo_bands) > 1 and bool(
        re.search(r'_\d{2}_\d{2}$', asset_name)
    )
    base_without_range = re.sub(r'_\d{2}_\d{2}$', '', asset_name) if is_hourly else None

    cog_bands: list[dict] = []
    for band in gdalinfo_bands:
        if is_hourly:
            hour_match = re.search(r'at (\d+) hr', band['description'])
            hour = int(hour_match.group(1)) if hour_match else band['band'] - 1
            name = f'{base_without_range}_{hour:02d}'
        else:
            name = asset_name
        cog_bands.append({'name': name, 'description': band['description']})

    return cog_bands if len(cog_bands) > 0 else None


def create_cog_asset_name_title(
    gdalinfo_content: dict[str, Any],
    prod_subtype: str,
    s3_subkey: S3Path,
    scene_name: str,
) -> tuple[str, str] | tuple[None, None]:
    """Create asset name and title for COG product."""
    asset_name: str
    asset_title: str
    try:
        if prod_subtype in (
            'lst-daily-cycle_global_5km_10daily_v1',
            'lst-daily-cycle_global_5km_10daily_v2',
            'lst-daily-cycle_global_3km_10daily_v3',
        ):
            asset_date = str(s3_subkey.key_relative).split('_')[3]
            if asset_date.endswith('0000'):
                asset_suffix = '00_11'
                asset_title_hours = '00-11'
            elif asset_date.endswith('1200'):
                asset_suffix = '12_23'
                asset_title_hours = '12-23'
            else:
                logging.warning(
                    f'Unrecognized date {asset_date} for asset {s3_subkey.key_relative!s}'
                )
                return None, None

            asset_name = (
                f'{str(s3_subkey.key_relative).split("_")[2]}-{asset_suffix}'.replace(
                    '-', '_'
                ).lower()
            )
            asset_title = (
                gdalinfo_content['bands'][0]['description']
                .replace('0', asset_title_hours, 1)
                .replace('12', asset_title_hours)
            )

        elif prod_subtype == 'lc_global_100m_yearly_v3':
            asset_name = (
                str(s3_subkey.key_relative).split('_')[5].replace('-', '_').lower()
            )
            asset_title = gdalinfo_content['bands'][0]['description']

        elif prod_subtype in [
            'lcm_global_10m_yearly_v1',
            'tcd_pantropical_10m_yearly_v1',
        ]:
            asset_name = 'map'
            asset_title = f'{str(s3_subkey.key_relative).split("_")[1]} Map'

        else:
            asset_name = re.sub(
                r'_rt\d+',
                '',
                str(s3_subkey.key_relative).split('_')[2].replace('-', '_').lower(),
            )
            asset_title = gdalinfo_content['bands'][0]['description']

        return _strip_product_prefix(asset_name, scene_name), asset_title

    except KeyError:
        logging.warning(f'Failed to create asset name and title for {s3_subkey!s}')
        return None, None


def get_processing_level(level: str | None, identifier: str) -> str:
    if (
        'STATIC-FM' in identifier
        or 'STATIC-TC' in identifier
        or 'STATIC-WF' in identifier
        or 'LCFM_LCM-10' in identifier
        or 'LCFM_TCD-10' in identifier
    ):
        return 'L3'
    elif level:
        return re.search(r'L\d', level)[0]
    else:
        return None


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    file_type = identify_type(attr['identifier'])
    subtype, product_config = identify_product(attr['filepath'], PROD_MAP)
    if file_type is None:
        raise ValueError(f'Not a NetCDF or COG: {attr["identifier"]}')
    if subtype is None:
        raise ValueError(f'Could not identify the product: {attr["identifier"]}')

    if product_config is None:
        raise ValueError(f'Unknown product type: {attr["identifier"]}')
    coords, gsd, prod_type, timeliness, timeliness_cat = product_config

    platform_attr = attr.get('platform')
    platform, constellation = identify_platform_constellation(platform_attr)

    extensions: Collection[StacExtension] = [
        StacExtension.PROCESSING,
        StacExtension.PRODUCT,
        StacExtension.PROJECTION,
    ]

    odata = await get_odata_id(attr['filepath'], omit_date=True)
    if not odata:
        raise ValueError(f'Could not get Odata response for {attr["identifier"]}')

    """
    For some products, attributes time_coverage_start / time_coverage_end
    describe the INPUT DATA LOOKBACK/LOOKFORWARD WINDOW used to compute the
    value at D -- they are processing metadata, not the temporal validity
    of the product itself.

    Using these verbatim as STAC start_datetime/end_datetime would make a
    single-dekad product (which represents ONE date, D) appear to "cover" a
    multi-week-to-7-month span, breaking date-range search.
    Hence why, as temporary fix, dates are now taken from OData response.
    """
    start_dt = odata.content_isodate['Start']
    end_dt = odata.content_isodate['End']

    props: dict[str, Any] = {
        'datetime': start_dt,
        'start_datetime': start_dt,
        'end_datetime': end_dt,
        **(
            {
                'instruments': list(
                    dict.fromkeys(
                        instrument.lower().strip()
                        for instrument in attr['sensor'].split(',')
                        if instrument.strip()
                    )
                )
            }
            if attr.get('sensor')
            else {}
        ),
        **({'gsd': gsd} if gsd else {}),
        'proj:code': 'EPSG:4326',
        'product:type': prod_type,
        **(
            {'processing:level': v}
            if (v := get_processing_level(attr.get('level'), attr['identifier']))
            else {}
        ),
        **({'cube:dimensions': attr['dimensions']} if file_type == 'nc' else {}),
        **({'cube:variables': attr['variables']} if file_type == 'nc' else {}),
        **({'platform': platform} if platform else {}),
        **({'constellation': constellation} if constellation else {}),
        **({'product:timeliness': timeliness} if timeliness else {}),
        **({'product:timeliness_category': timeliness_cat} if timeliness_cat else {}),
        **({'processing:version': v} if (v := attr.get('productVersion')) else {}),
    }

    extended_private_data = is_extended_private_data()
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

    if file_type == 'nc':
        extensions.append(StacExtension.DATACUBE)
        s3path_obj = list(attr['s3_scene'].subkeys.values())[0]
        asset_bands = create_bands_netcdf(attr['variables'])

        assets['Product'] = NetCDFAsset(
            path=str(s3path_obj),
            title=attr['title'],
            checksum=attr[f'{s3path_obj.key_relative}:checksum'],
            size=attr[f'{s3path_obj.key_relative}:size'],
            extra={'bands': asset_bands} if asset_bands else {},
            include_other_alternates=False
            if subtype == 'lwq-nrt_global_1km_10daily_v1'
            or subtype == 'lwq-reproc_global_1km_10daily_v1'
            else True,
        )
    elif file_type == 'cog':
        for value in attr['s3_scene'].subkeys.values():
            gdal_content = await run_gdalinfo(str(value))

            if gdal_content:
                gdal_content = orjson.loads(gdal_content.decode())
                asset_name, asset_title = create_cog_asset_name_title(
                    gdal_content, subtype, value, attr['identifier']
                )
                if asset_name in assets:
                    logging.warning(
                        'Duplicate asset name %r in %s: %s overwrites %s',
                        asset_name,
                        attr['identifier'],
                        value.key_relative,
                        assets[asset_name].path.rsplit('/', 1)[-1],
                    )
                asset_bands = create_bands_cog(gdal_content['bands'], asset_name)
                asset_extra = await stac_extra_from_gdalinfo(
                    gdal_content,
                    fallback_proj_code=props['proj:code'],
                )
                if asset_bands:
                    asset_extra['bands'] = asset_bands
                assets[asset_name] = CloudOptimizedGeoTIFFAsset(
                    path=str(value),
                    title=asset_title,
                    checksum=attr[f'{value.key_relative}:checksum'],
                    size=attr[f'{value.key_relative}:size'],
                    extra=asset_extra,
                )
    elif file_type == 'geojson':
        s3path_obj = list(attr['s3_scene'].subkeys.values())[0]

        assets['json'] = JsonAsset(
            path=str(s3path_obj),
            title=attr['title'],
            checksum=attr[f'{s3path_obj.key_relative}:checksum'],
            size=attr[f'{s3path_obj.key_relative}:size'],
        )

    if thumbnail := create_thumbnail_asset(
        assets,
        props,
        subtype,
        file_type,
        attr['identifier'],
    ):
        assets['thumbnail'] = thumbnail

    links: list[STACLink] = (
        [
            TraceabilityLink(
                href=odata.name,
            )
        ]
        if odata
        else []
    )

    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection=f'clms_{subtype}_{file_type}',
        identifier=attr['identifier'],
        coordinates=coords if coords else attr['geometry'],
        links=links,
        product_asset_name='Product' if file_type == 'cog' else None,
        assets=assets,
        extensions=extensions,
        extra=props,
    )
    return await item.generate()
