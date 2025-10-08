import logging
import re
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from functools import cache, lru_cache
from itertools import batched
from math import isnan
from os import PathLike, environ
from pathlib import Path
from typing import Any, NamedTuple, TypedDict, TypeGuard

import numpy as np
import orjson
import stamina
from httpx import AsyncClient, HTTPError, Timeout
from pyproj import Transformer
from shapely import (
    from_geojson,
    from_wkt,
)

from eometadatatool.custom_types import MappedMetadataValue
from eometadatatool.flags import get_odata_endpoint
from eometadatatool.geom_utils import normalize_geometry
from eometadatatool.odata_response import get_odata_response
from eometadatatool.s3_utils import S3Path
from eometadatatool.stac.framework.stac_bands import S2_Bands

_HTTP = AsyncClient(
    headers={'User-Agent': 'eometadatatool'},
    timeout=Timeout(
        float(environ.get('HTTP_TIMEOUT', '60')),
        connect=float(environ.get('HTTP_CONNECT_TIMEOUT', '20')),
        read=float(environ.get('HTTP_READ_TIMEOUT', '60')),
    ),
    follow_redirects=True,
)


class _ODataChecksum(TypedDict):
    Value: str
    Algorithm: str


class ODataInfo(NamedTuple):
    id: str
    thumbnail_link: str | None
    checksum: str
    checksum_algorithm: str | None
    file_size: int
    created_isodate: str
    updated_isodate: str
    published_isodate: str
    origin: str | None
    name: str


@stamina.retry(on=HTTPError)
async def get_odata_id(input: str | dict[str, Any], /) -> ODataInfo:
    """
    Get additional information from OData.
    Datahub HTTP request is made if no response is provided via configure_odata_response().

    :param name: Product S3Path from OData.
    :return: OData product information.
    """
    data: dict[str, Any] | None = get_odata_response(None)
    if data is None and isinstance(input, dict):
        ## CCM method
        name: str = input.get('s2msi:productUri') or input['filename']
        logging.debug('No exact OData match for %r, trying prefix match', name)
        r = await _HTTP.get(
            f'{get_odata_endpoint()}/Products',
            params=(
                ('$filter', f"startswith(Name,'{name}')"),
                ('$expand', 'Assets'),
                ('$expand', 'Attributes'),
            ),
        )
        r.raise_for_status()
        data = next(iter(r.json().get('value', ())), None)
        if data is None:
            logging.info('No OData matches for %r', name)
            s3_scene: S3Path | None = input.get('s3_scene')
            if s3_scene is not None:
                updated_isodate = s3_scene.last_modified.isoformat()
                return ODataInfo(
                    id='',
                    thumbnail_link=None,
                    checksum='0' * 32,
                    checksum_algorithm=None,
                    file_size=0,
                    created_isodate=updated_isodate,
                    updated_isodate=updated_isodate,
                    published_isodate=updated_isodate,
                    origin=None,
                    name=name,
                )

    elif data is None and isinstance(input, str):
        ## Standard approach
        query_filter = _odata_filter_parameters_from_s3path(Path(input))
        r = await _HTTP.get(
            f'{get_odata_endpoint()}/Products',
            params=(
                ('$filter', query_filter),
                ('$expand', 'Assets'),
                ('$expand', 'Attributes'),
            ),
        )
        r.raise_for_status()
        data = next(iter(r.json().get('value', ())), None)
        if data is None:
            raise ValueError(f'Product {input!r} not found in datahub.creodias.eu')

    assets: Sequence[dict[str, Any]] = data.get('Assets', ())
    attributes: Sequence[dict[str, Any]] = data['Attributes']
    checksums: Sequence[_ODataChecksum] = data.get('Checksum', ())

    thumbnail_link: str | None = next(
        iter(a['DownloadLink'] for a in assets if a['Type'] == 'QUICKLOOK'), None
    )
    checksum_data = next(iter(checksums), None)
    if _is_valid_odata_checksum(checksum_data):
        checksum = checksum_data['Value']
        checksum_algorithm = checksum_data['Algorithm']
    else:
        checksum = '0' * 32
        checksum_algorithm = None
    origin: str | None = next(
        iter(a['Value'] for a in attributes if a['Name'] == 'origin'), None
    )

    return ODataInfo(
        id=data['Id'],
        thumbnail_link=thumbnail_link,
        checksum=checksum,
        checksum_algorithm=checksum_algorithm,
        file_size=data['ContentLength'],
        created_isodate=data['OriginDate'],
        updated_isodate=data['ModificationDate'],
        published_isodate=data['PublicationDate'],
        origin=origin,
        name=data['Name'],
    )


def _odata_filter_parameters_from_s3path(s3path: Path) -> str:
    parts = s3path.parts
    collection = parts[2].upper()
    content_start_date = parts[5] + parts[6] + parts[7]
    name = parts[-1]

    one_day = timedelta(days=1)
    start_date = (datetime.strptime(content_start_date, '%Y%m%d') - one_day).strftime(
        '%Y-%m-%dT00:00:00.000Z'
    )
    end_date = (datetime.strptime(content_start_date, '%Y%m%d') + one_day).strftime(
        '%Y-%m-%dT23:59:59.999Z'
    )
    return (
        f"(Name eq '{name}') "
        f'and (ContentDate/Start ge {start_date} and ContentDate/Start le {end_date}) '
        f"and (Collection/Name eq '{collection}')"
    )


def _is_valid_odata_checksum(
    checksum_data: _ODataChecksum | None,
) -> TypeGuard[_ODataChecksum]:
    return bool(
        checksum_data
        and checksum_data['Algorithm']
        and (checksum := set(checksum_data['Value']))
        and '/' not in checksum  # "N/A" is invalid
        and (len(checksum) >= 2 or '0' not in checksum)  # "0000..." is invalid
    )


class UserDataInfo(NamedTuple):
    name: str
    created_isodate: str
    updated_isodate: str
    published_isodate: str
    grid_code: str
    coords: list[float] | list[list[float]] | list[list[list[float]]]
    bbox: tuple[float, float, float, float]
    start_isodate: str
    end_isodate: str
    crs: str


async def get_metadata_from_userdata(dir_: PathLike) -> UserDataInfo:
    """Get additional information from a userdata.json file.

    :param dir_: Path to the directory containing the userdata.json file (with support for S3).
    :raises ValueError: If the dir_ is empty.
    """
    path = Path(dir_)
    if s3_path := await S3Path.from_path(path):
        if not s3_path.is_dir():
            raise NotADirectoryError(
                f'userdata.json not found in {s3_path!s}, not a directory'
            )
        data_path = s3_path.get_subpath(f'{s3_path.key}/userdata.json')
        async with data_path.tempfile() as f:
            content = f.read_bytes()
    else:
        if not path.is_dir():
            raise NotADirectoryError(
                f'userdata.json not found in {path!r}, not a directory'
            )
        data_path = path.joinpath('userdata.json')
        content = data_path.read_bytes()

    data: dict[str, Any] = orjson.loads(content)
    name: str = data['Name']
    grid_code = name.split('_')[-3]
    crs = ('EPSG:327' if grid_code[2] < 'N' else 'EPSG:326') + grid_code[:2]
    geom = from_geojson(orjson.dumps(data['GeoFootprint']))
    return UserDataInfo(
        name=name,
        created_isodate=data['OriginDate'],
        updated_isodate=data['ModificationDate'],
        published_isodate=data['PublicationDate'],
        grid_code=grid_code,
        coords=data['GeoFootprint']['coordinates'],
        bbox=geom.bounds,
        start_isodate=data['ContentDate']['Start'],
        end_isodate=data['ContentDate']['End'],
        crs=crs,
    )


def calculate_bbox_from_wkt(wkt_: str, /) -> tuple[float, float, float, float]:
    """Calculate bounding box from a WKT representation.

    :param wkt_: Well-Known Text representation of the geometry.
    :return: Tuple of (min_lon, min_lat, max_lon, max_lat).
    """
    return normalize_geometry(from_wkt(wkt_)).bounds  # type: ignore


def asset_to_zipper(pid: str, scene_name: str, asset_path: str) -> str:
    """Get a Copernicus zipper URL for the given asset.

    :param pid: Product identifier.
    :param scene_name: Scene name or scene path.
    :param asset_path: Path to the asset, relative within the scene, or absolute.
    :raises ValueError: If the scene name contains slashes.
    :return: Zipper URL.
    """
    scene_name = scene_name.rsplit('/', 1)[-1]
    if asset_path.startswith(('/', 's3://')):  # convert absolute paths to relative
        index = asset_path.find(f'/{scene_name}/')
        if index >= 0:
            asset_path = asset_path[index + len(scene_name) + 2 :]
        elif asset_path[:1] == '/':
            asset_path = asset_path.lstrip('/')
        elif asset_path[:5] == 's3://':
            asset_path = asset_path[5:]

    if 'S5P' in scene_name:
        selector_path = f'{scene_name}'
    else:
        selector_path = f'{scene_name}/{asset_path}'

    selectors: list[str] = []
    for part in selector_path.split('/'):
        if not part:
            continue
        if part == '.':
            raise AssertionError(
                f'Suspicious "." in the selector path: {selector_path!r}. This zipper URL would be broken - please fix the asset path.'
            )
        selectors.append(f'/Nodes({part})')

    return f'https://zipper.dataspace.copernicus.eu/odata/v1/Products({pid}){"".join(selectors)}/$value'


@lru_cache(maxsize=256)
def _encode_varint(value: int) -> bytes:
    """Encode an integer as a varint in bytes."""
    encoded = bytearray()
    while value > 0x7F:
        encoded.append((value & 0x7F) | 0x80)
        value >>= 7
    encoded.append(value)
    return bytes(encoded)


def hex_to_multihash(hex_str: str, fn_code: int) -> str | None:
    """Convert a hex-encoded hash string to a hex-encoded multihash.

    :param hex_str: Input hex-encoded hash string.
    :param fn_code: Multihash function code. `See definition table<https://github.com/multiformats/multicodec/blob/master/table.csv>`_.
    :return: Hex-encoded multihash string.
    """
    if not hex_str or hex_str == '0' * len(hex_str):
        return None
    byte_fn_code = _encode_varint(fn_code)
    byte_hash_length = _encode_varint(len(hex_str) // 2)
    return (byte_fn_code + byte_hash_length).hex() + hex_str.lower()


def s2_compute_average(
    metadata: dict[str, MappedMetadataValue | float], field: str
) -> float:
    """Compute the average value of a given field for all Sentinel-2 bands.

    :param metadata: Mapping of metadata values.
    :param field: Field to compute the average for.
    :return: Average value.
    """
    bands_values: list[float] = []
    for band in S2_Bands:
        value = metadata[f'asset:{band}:{field}']
        value_float = value['Value'] if isinstance(value, dict) else value
        if not isnan(value_float):
            bands_values.append(value_float)
    return np.mean(bands_values).tolist()


def format_baseline(x: str | float) -> str:
    """Format a value into XX.XX format.

    :param x: Input value.
    :raises ValueError: If the input value is not a number.
    :return: Value in XX.XX format.

    >>> format_baseline('1.2')
    '01.20'
    """
    return f'{float(x):05.2f}'


def normalize_angle(angle: float) -> float:
    """Normalize an angle to the range [0, 360)."""
    return angle % 360


@cache
def _get_projection_transformer(to_crs: str | int) -> Transformer:
    """Get a transformer, from EPSG:4326 to the given CRS.

    :param to_crs: Target CRS. If int, it is assumed to be EPSG code.
    :return: Transformer instance.
    """
    return Transformer.from_crs(
        crs_from='EPSG:4326',
        crs_to=f'EPSG:{to_crs}' if isinstance(to_crs, int) else to_crs,
        always_xy=True,
    )


def _get_bbox_from_corners(
    coords: str | Iterable[Iterable[float]],
) -> tuple[float, float, float, float]:
    """Get bounding box from the given coordinates.

    :param coords: Coordinates, in the form of "a1 b1,a2 b2,a3 b3,a4 b4" or [(a1, b1), (a2, b2), ...].
    :return: Bounding box, in the form of (min_a, min_b, max_a, max_b).
    """
    arr = (
        np.loadtxt(coords.split(','))  #
        if isinstance(coords, str)
        else np.asarray(coords)
    )
    min_a, min_b = arr.min(axis=0).tolist()
    max_a, max_b = arr.max(axis=0).tolist()
    return min_a, min_b, max_a, max_b


def reproject_bbox(
    coords: str | Iterable[Iterable[float]],
    to_crs: str | int,
) -> tuple[float, float, float, float]:
    """Get bounding box of the given coordinates in the target CRS.

    :param coords: Coordinates to transform, in the form of "lat1 lon1,lat2 lon2,..." or [(lat1, lon1), (lat2, lon2), ...].
    :param to_crs: Target CRS. If int, it is assumed to be EPSG code.
    :return: Bounding box of the transformed coordinates, in the form of (min_lon, min_lat, max_lon, max_lat).
    """
    min_lat, min_lon, max_lat, max_lon = _get_bbox_from_corners(coords)
    return _get_projection_transformer(to_crs).transform_bounds(
        left=min_lon,
        bottom=min_lat,
        right=max_lon,
        top=max_lat,
    )


def regex_match(text: str, pattern: str, group: int = 1) -> str:
    """Extract a value from a string using a regular expression.

    :param text: Input text.
    :param pattern: Regular expression pattern.
    :param group: Match group to extract, defaults to 1.
    :raises ValueError: If no match is found.
    :return: Match group.
    """
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f'No match for {pattern!r} in {text!r}')
    return match.group(group)


def coordinates_to_wkt(rings: Iterable[str]) -> str:
    """Convert a list of coordinate rings into a WKT representation.

    :param rings: List of coordinate rings, in the form of ["lat1,lon1 lat2,lon2 ..."].
    :raises ValueError: If the input is empty.
    :return: Well-Known Text representation of the geometry.
    """
    rings_coords: list[list[Sequence[str]]] = []
    for ring in rings:
        coords: list[Sequence[str]]
        if ',' in ring:
            # convert "lat,lon" into [lat, lon]
            coords = [coord.split(',') for coord in ring.split()]
        else:
            # split string at every second space if no comma is contained
            coords = list(batched(ring.split(), 2, strict=True))
        if coords:
            rings_coords.append(coords)
    if not rings_coords:
        raise ValueError('Empty coordinate list')
    rings_str = [
        # reverse [lat, lon] into [lon, lat]
        ', '.join(f'{coord[1]} {coord[0]}' for coord in coords)
        for coords in rings_coords
    ]
    match len(rings_coords[0]):
        case 1:
            match rings_str:
                case (ring_str,):
                    return f'POINT({ring_str})'
                case _:
                    return f'MULTIPOINT(({"), (".join(rings_str)}))'
        case 2:
            match rings_str:
                case (ring_str,):
                    return f'LINESTRING({ring_str})'
                case _:
                    return f'MULTILINESTRING(({"), (".join(rings_str)}))'
        case _:
            # auto-close polygons
            for i, coords in enumerate(rings_coords):
                if coords[0] != coords[-1]:
                    coord = coords[0]
                    rings_str[i] += f', {coord[1]} {coord[0]}'
            match rings_str:
                case (ring_str,):
                    return f'POLYGON(({ring_str}))'
                case _:
                    return f'MULTIPOLYGON((({")), ((".join(rings_str)})))'
