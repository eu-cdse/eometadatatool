import posixpath
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, TypeVar

from shapely.geometry import shape

T = TypeVar('T', str, int, float, datetime)


def _get_by_path(dct: dict[str, Any], path: str) -> Any:
    parts = path.split('.')
    val: Any = dct.get(parts[0])
    for p in parts[1:]:
        if not isinstance(val, dict):
            break
        val = val.get(p)
    return val


def _emit(
    props: dict[str, Any],
    attrs: list[dict[str, Any]],
    typ: type[T],
    name: str,
    keys: str | tuple[str, ...],
    transform: Callable[[T], T | None] | None = None,
) -> None:
    # Resolve value strictly from props via key or tuple of keys (fallback order)
    if isinstance(keys, str):
        value: Any = _get_by_path(props, keys)
    else:
        value = None
        for k in keys:
            value = _get_by_path(props, k)
            if value is not None:
                break

    # If value is a list, handle generically by coercing to a scalar
    if isinstance(value, list):
        if typ is str:
            value = '&'.join(str(x) for x in value) if value else None
        elif typ in (int, float, datetime):
            value = value[0] if value else None

    if value is None:
        return

    # Convert type and derive OData metadata; then optionally post-transform the typed value
    if typ is str:
        v_typed: T = str(value)  # type: ignore[assignment]
        if v_typed == '':
            return
        otype = '#OData.CSC.StringAttribute'
        vtype = 'String'
    elif typ is int:
        v_typed = int(value)  # type: ignore[assignment]
        otype = '#OData.CSC.IntegerAttribute'
        vtype = 'Integer'
    elif typ is float:
        v_typed = float(value)  # type: ignore[assignment]
        otype = '#OData.CSC.DoubleAttribute'
        vtype = 'Double'
    elif typ is datetime:
        dt: datetime
        if isinstance(value, datetime):
            dt = value
        else:
            s = str(value)
            s = s[:-1] + '+00:00' if s.endswith('Z') else s
            dt = datetime.fromisoformat(s)
        v_typed = dt  # type: ignore[assignment]
        otype = '#OData.CSC.DateTimeOffsetAttribute'
        vtype = 'DateTimeOffset'
    else:
        raise ValueError('Unsupported type')

    if transform is not None:
        transformed = transform(v_typed)
        if (typ is str and not transformed) or transformed is None:
            return
        v_typed = transformed

    # Final value encoding
    if typ is datetime:
        v_out: Any
        dt_out: datetime = v_typed  # type: ignore[assignment]
        if dt_out.tzinfo is not None and dt_out.utcoffset() == timedelta(0):
            v_out = dt_out.replace(tzinfo=UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            v_out = dt_out.isoformat()
    else:
        v_out = v_typed

    attrs.append({
        '@odata.type': otype,
        'Name': name,
        'Value': v_out,
        'ValueType': vtype,
    })


def _platform_serial_identifier(platform: str | None) -> str | None:
    if not platform:
        return None
    # Accept only sentinel-[1236][abc] → A/B/C
    suffix = platform.rsplit('-', 1)[-1]
    if (
        len(suffix) == 2
        and suffix[0] in {'1', '2', '3', '6'}
        and suffix[1] in {'a', 'b', 'c'}
    ):
        return suffix[1].upper()
    return None


def s3path_from_stac(stac: dict[str, Any]) -> Path | None:
    # 1) Prefer STAC link with rel=enclosure pointing to s3
    for link in stac.get('links', ()):  # prefer enclosure s3 path
        href: str = link.get('href', '')
        if link.get('rel') == 'enclosure' and href.startswith('s3://'):
            return Path(href[4:].rstrip('/'))  # convert to OData S3Path format

    # 2) Fallback: common base across asset S3 hrefs
    s3_paths = [
        a['href'][4:].rstrip('/')
        for a in (stac.get('assets') or {}).values()
        if a.get('href', '').startswith('s3://')
    ]
    if not s3_paths:
        return None

    return Path(posixpath.commonpath(s3_paths).rstrip('/'))


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    stac_data: dict[str, Any] = attr['stac_data']
    props: dict[str, Any] = stac_data['properties']
    assets: dict[str, dict] = stac_data['assets']
    geometry: dict[str, Any] = stac_data['geometry']
    attributes: list[dict[str, Any]] = []

    # -- Prepare
    s3path = p.as_posix() if (p := s3path_from_stac(stac_data)) is not None else None

    # Extract suffix from file:local_path (e.g., ".SAFE")
    stac_id = stac_data['id']
    for asset in assets.values():
        local_path: str = asset.get('file:local_path', '')
        if local_path.startswith(stac_id):
            i = local_path.find('/', len(stac_id))
            stac_id = local_path[:i] if i != -1 else local_path
            break

    emit = partial(_emit, props, attributes)

    # -- Mission flags
    constellation = (props.get('constellation') or '').lower()
    is_s1 = constellation == 'sentinel-1'
    is_s2 = constellation == 'sentinel-2'
    is_s3 = constellation == 'sentinel-3'

    # -- Identity and platform
    emit(str, 'instrumentShortName', 'instruments', transform=str.upper)
    emit(str, 'operationalMode', ('eopf:instrument_mode', 'sar:instrument_mode'))
    emit(
        str,
        'platformSerialIdentifier',
        'platform',
        transform=_platform_serial_identifier,
    )
    emit(str, 'platformShortName', 'constellation', transform=str.upper)

    # -- Orbit and acquisition
    emit(int, 'cycleNumber', 'sat:orbit_cycle')
    emit(str, 'orbitDirection', 'sat:orbit_state', transform=str.upper)
    emit(int, 'orbitNumber', 'sat:absolute_orbit')
    emit(int, 'relativeOrbitNumber', 'sat:relative_orbit')
    if is_s1:
        emit(int, 'datatakeID', 'eopf:datatake_id')
        emit(int, 'instrumentConfigurationID', 'eopf:instrument_configuration_id')

    # -- Product & collection
    emit(float, 'cloudCover', 'eo:cloud_cover')
    emit(str, 'polarisationChannels', 'sar:polarizations', transform=str.upper)
    emit(str, 'productType', 'product:type')
    emit(str, 'swathIdentifier', 'sar:instrument_mode')
    if is_s2:
        emit(str, 'datastripId', 'eopf:datastrip_id')
        emit(str, 'productGroupId', 'eopf:datatake_id')
        emit(
            str,
            'tileId',
            'grid:code',
            transform=lambda s: (s[5:] if s.upper().startswith('MGRS-') else s),
        )

    # -- Processing metadata
    field = 'processingCenter' if is_s3 else ('origin' if (is_s1 or is_s2) else None)
    if field:
        emit(str, field, 'processing:facility')
    emit(datetime, 'processingDate', 'processing:datetime')
    emit(
        str,
        'processingLevel',
        'product:type' if is_s2 else 'processing:level',
        transform=(
            (lambda s: 'LEVEL' + s.removeprefix('L') if s.startswith('L') else s)
            if is_s1
            else ((lambda s: s.removeprefix('L')) if is_s3 else None)
        ),
    )
    emit(str, 'processorVersion', 'processing:version')
    emit(str, 'timeliness', ('product:timeliness_category', 'product:timeliness'))

    # -- Coverage statistics
    emit(float, 'coastalCover', 'statistics.coastal')
    emit(float, 'brightCover', 'statistics.bright')
    emit(float, 'freshInlandWaterCover', 'statistics.fresh_inland_water')
    emit(float, 'landCover', 'statistics.land')
    emit(float, 'salineWaterCover', 'statistics.saline_water')
    emit(float, 'tidalRegionCover', 'statistics.tidal_region')

    # -- Content dates
    start_date = props.get('start_datetime', props['datetime'])
    end_date = props.get('end_datetime', props['datetime'])
    emit(datetime, 'beginningDateTime', ('start_datetime', 'datetime'))
    emit(datetime, 'endingDateTime', ('end_datetime', 'datetime'))

    product: dict[str, Any] = next(
        asset
        for asset in assets.values()
        if '/' not in asset.get('file:local_path', '/')
    )

    origin_date = props.get('created', start_date)
    publication_date = props.get('published') or props.get('updated', start_date)
    modification_date = props.get('updated') or props.get('created', start_date)

    odata_assets: list[dict] = []
    if thumb := assets.get('thumbnail'):
        thumb_asset = {
            'DownloadLink': thumb['href'],
            'Id': re.search(r'Assets\((.*?)\)', thumb['href']).group(1),  # type: ignore
            'Type': 'QUICKLOOK',
        }
        if s3path is not None:
            thumb_asset['S3Path'] = s3path
        odata_assets.append(thumb_asset)

    odata_item: dict[str, Any] = {
        '@odata.mediaContentType': 'application/octet-stream',
        'Name': stac_id,
        'ContentType': 'application/octet-stream',
        'ContentLength': product.get('file:size', -1),
        'OriginDate': origin_date,
        'PublicationDate': publication_date,
        'ModificationDate': modification_date,
        'Online': True,
        'EvictionDate': '9999-12-31T23:59:59.999999Z',
        'ContentDate': {'Start': start_date, 'End': end_date},
        'Footprint': f"geography'SRID=4326;{shape(geometry).wkt}'",
        'GeoFootprint': geometry,
        'Attributes': attributes,
        'Assets': odata_assets,
    }

    if s3path is not None:
        odata_item['S3Path'] = s3path

    checksums: list[dict[str, Any]] = []
    if mh := product.get('file:checksum'):
        algo, hexval = _parse_multihash(mh)
        checksums.append({
            'Value': hexval,
            'Algorithm': algo,
            'ChecksumDate': modification_date,
        })
    if checksums:
        odata_item['Checksum'] = checksums

    return {
        '@odata.context': '$metadata#Products(Attributes(),Assets())',
        'value': [odata_item],
    }


def _parse_multihash(mh: str) -> tuple[str, str]:
    b = bytes.fromhex(mh)
    i = 0

    def _uvarint(data: bytes, j: int) -> tuple[int, int]:
        val = 0
        shift = 0
        while True:
            byte = data[j]
            j += 1
            val |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
        return val, j

    code, i = _uvarint(b, i)
    length, i = _uvarint(b, i)
    digest = b[i : i + length]
    algo = _MULTIHASH_CODEC_MAP[code]
    assert len(digest) == length
    return algo, digest.hex()


_MULTIHASH_CODEC_MAP: dict[int, str] = {
    0x11: 'SHA1',
    0x12: 'SHA256',
    0x13: 'SHA512',
    0x1E: 'BLAKE3',
    0xD5: 'MD5',
    0xB220: 'BLAKE2B-256',
    0xB240: 'BLAKE2B-512',
    0xB250: 'BLAKE2S-128',
    0xB260: 'BLAKE2S-256',
}
