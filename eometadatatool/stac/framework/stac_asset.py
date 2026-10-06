import json
import logging
import mimetypes
import re
from collections import ChainMap
from collections.abc import Collection, Mapping, MutableSet
from dataclasses import dataclass, field
from typing import Any, Literal, override
from urllib.parse import urlsplit, urlunsplit

import orjson

from eometadatatool.dlc import ODataInfo, asset_to_zipper, hex_to_multihash
from eometadatatool.gdalinfo import get_gdal_version, run_gdalinfo
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.utils import EMPTY_MAPPING

type AlternateKey = Literal['s3', 'https']

DEFAULT_ODATA_ASSET_URL = 'https://datahub.creodias.eu/odata/v1/Assets'


def _normalize_thumbnail_href(href: str) -> str:
    """Normalize OData asset links so thumbnails always point to the public host."""
    default = urlsplit(DEFAULT_ODATA_ASSET_URL)
    parsed = urlsplit(href)
    if not parsed.path.startswith(f'{default.path}('):
        return href
    return urlunsplit(parsed._replace(scheme=default.scheme, netloc=default.netloc))


# NOTE: add slots=True when super() fixed in 3.14
# see https://github.com/python/cpython/issues/90562


@dataclass(kw_only=True)
class STACAsset:
    path: str
    """Path to the asset in the filesystem or S3."""

    media_type: str
    """Media type (mime type) of the asset."""

    title: str
    """Name of the asset."""

    roles: Collection[str]
    """Roles of the asset."""

    https_href: str | None = 'zipper'
    """Public HTTPS URL of the asset."""

    description: str | None = None
    """Asset description."""

    checksum: str | None = None
    """Asset checksum as hex-encoded hash string."""

    checksum_fn_code: int = 0xD5
    """Checksum multihash function code."""

    size: int | None = None
    """Asset size in bytes."""

    prefer_alternate: AlternateKey = 's3'
    """Which alternate to prefer."""

    include_other_alternates: bool = True
    """Whether to include other alternates under 'alternate' key."""

    is_https_public: bool = False
    """Whether the HTTPS asset is public or not (i.e. requires auth)."""

    extra: Mapping[str, Any] = EMPTY_MAPPING
    """Additional properties."""

    def __post_init__(self):
        if self.path[-1] == '/':
            self.path = self.path.rstrip('/')

    async def generate(
        self,
        odata: ODataInfo | None,
        extensions: MutableSet[StacExtension],
        item_props: dict[str, Any] = {},
    ) -> dict[str, Any]:
        props: dict[str, Any] = {
            'type': self.media_type,
            'title': self.title,
            'roles': self.roles,
            **self.extra,
        }

        if self.description is not None:
            props['description'] = self.description
        if self.checksum is not None:
            checksum = hex_to_multihash(self.checksum, self.checksum_fn_code)
            if checksum is not None:
                props['file:checksum'] = checksum
        if self.size is not None and self.size > 0:
            props['file:size'] = self.size

        if odata is not None:
            try:
                local_path = self.path[self.path.index(f'/{odata.name}') + 1 :]
            except ValueError:
                pass
            else:
                props['file:local_path'] = (
                    f'{odata.name}.zip'
                    if self.media_type == 'application/zip' and local_path == odata.name
                    else local_path
                )

            if self.https_href == 'zipper':
                self.https_href = asset_to_zipper(odata.id, odata.name, self.path)

        available_alternates: dict[AlternateKey, str] = {}
        if self.path[:5] == 's3://':
            available_alternates['s3'] = self.path
        if self.https_href is not None:
            available_alternates['https'] = self.https_href

        if available_alternates:
            if self.prefer_alternate not in available_alternates:
                logging.warning(
                    'Preferred alternate %r not available for %s',
                    self.prefer_alternate,
                    self.path,
                )
                self.prefer_alternate = next(iter(available_alternates))

            props.update(
                self._generate_alternate_properties(
                    self.prefer_alternate,
                    available_alternates,
                    extensions,
                )
            )

        if self.include_other_alternates and len(available_alternates) > 1:
            extensions.add(StacExtension.ALTERNATE)
            props['alternate'] = {}
            for key in available_alternates:
                if key == self.prefer_alternate:
                    continue
                props['alternate'][key] = self._generate_alternate_properties(
                    key,
                    available_alternates,
                    extensions,
                    is_alternate=True,
                )

        if 'bands' in self.extra:
            match any(key.startswith('eo:') for key in self.extra['bands'][0]):
                case True:
                    extensions.add(StacExtension.EO)
            match any(key.startswith('sar:') for key in self.extra['bands'][0]):
                case True:
                    extensions.add(StacExtension.SAR)

        if any(key[:5] == 'file:' for key in props):
            extensions.add(StacExtension.FILE)

        return props

    def _generate_alternate_properties(
        self,
        kind: AlternateKey,
        alternates: Mapping[AlternateKey, str],
        extensions: MutableSet[StacExtension],
        is_alternate: bool = False,
    ) -> dict[str, Any]:
        asset: dict[str, Any] = {
            'href': alternates[kind],
        }
        match kind:
            case 'https':
                if self.include_other_alternates and len(alternates) > 1:
                    asset['alternate:name'] = 'HTTPS'
                if not self.is_https_public:
                    extensions.add(StacExtension.AUTHENTICATION)
                    asset['auth:refs'] = ('oidc',)
                if is_alternate:
                    extensions.add(StacExtension.STORAGE)
                    asset['storage:refs'] = ()
                return asset
            case 's3':
                if self.include_other_alternates and len(alternates) > 1:
                    asset['alternate:name'] = 'S3'
                extensions.add(StacExtension.AUTHENTICATION)
                asset['auth:refs'] = ('s3',)
                extensions.add(StacExtension.STORAGE)
                asset['storage:refs'] = (
                    'cdse-s3',
                    'creodias-s3',
                )
                return asset

        raise ValueError(f'Unsupported alternate kind {kind!r}')


@dataclass(kw_only=True)
class XMLAsset(STACAsset):
    media_type: str = field(default='application/xml', init=False)


@dataclass(kw_only=True)
class ProductAsset(STACAsset):
    https_href: str | None = field(default=None, init=False)
    media_type: str = field(default='application/zip', init=False)
    title: str = field(default='Zipped product', init=False)
    roles: Collection[str] = field(default=('data', 'metadata', 'archive'), init=False)
    checksum: str | None = field(default=None, init=False)
    size: int | None = field(default=None, init=False)
    prefer_alternate: AlternateKey = field(default='https', init=False)
    include_other_alternates: bool = field(default=False, init=False)

    @override
    async def generate(
        self,
        odata: ODataInfo | None,
        extensions: MutableSet[StacExtension],
        item_props: dict[str, Any] = {},
    ) -> dict[str, Any]:
        if odata:
            self.https_href = f'https://download.dataspace.copernicus.eu/odata/v1/Products({odata.id})/$value'
            if odata.checksum and odata.checksum != '0' * len(odata.checksum):
                self.checksum = odata.checksum
            if odata.file_size > 0:
                self.size = odata.file_size
        return await super().generate(odata, extensions, item_props)


@dataclass(kw_only=True)
class TarProductAsset(ProductAsset):
    media_type: str = field(default='application/x-tar', init=False)
    title: str = field(default='TAR archive', init=False)


@dataclass(kw_only=True)
class TgzProductAsset(ProductAsset):
    media_type: str = field(default='application/gzip', init=False)
    title: str = field(default='Gzipped TAR archive', init=False)


@dataclass(kw_only=True)
class GzipProductAsset(ProductAsset):
    media_type: str = field(default='application/gzip', init=False)
    title: str = field(default='Gzipped product', init=False)


@dataclass(kw_only=True)
class ProductManifestAsset(STACAsset):
    media_type: str = field(default='application/xml', init=False)
    title: str = field(default='Product manifest')
    roles: Collection[str] = field(default=('metadata',), init=False)


@dataclass(kw_only=True)
class NetCDFAsset(STACAsset):
    media_type: str = field(default='application/netcdf', init=False)
    roles: Collection[str] = field(default=('data',))


@dataclass(kw_only=True)
class CloudOptimizedGeoTIFFAsset(STACAsset):
    media_type: str = field(
        default='image/tiff; application=geotiff; profile=cloud-optimized', init=False
    )
    roles: Collection[str] = field(default=('data',))

    @override
    async def generate(
        self,
        odata: ODataInfo | None,
        extensions: MutableSet[StacExtension],
        item_props: dict[str, Any] = {},
    ) -> dict[str, Any]:
        props = await super().generate(odata, extensions, item_props)
        await _fill_from_file(self.path, props, item_props)
        if has_meaningful_scale_or_offset(props):
            extensions.add(StacExtension.RASTER)
        return props


@dataclass(kw_only=True)
class GeoTIFFAsset(STACAsset):
    media_type: str = field(default='image/tiff; application=geotiff', init=False)
    roles: Collection[str] = field(default=('data',))


@dataclass(kw_only=True)
class JPEG2000Asset(STACAsset):
    media_type: str = field(default='image/jp2', init=False)
    roles: Collection[str] = field(default=('data',))


@dataclass(kw_only=True)
class HDFAsset(STACAsset):
    media_type: str = field(default='application/x-hdf', init=False)
    roles: Collection[str] = field(default=('data',))


@dataclass(kw_only=True)
class ThumbnailAsset(STACAsset):
    https_href: str | None = field(default=None, init=False)
    media_type: str = field(default='', init=False)
    title: str = field(default='Thumbnail')
    roles: Collection[str] = field(default=('thumbnail',))
    prefer_alternate: AlternateKey = field(default='https', init=False)
    is_https_public: bool = field(default=True, init=False)

    def __post_init__(self):
        media_type = mimetypes.guess_file_type(self.path)[0]
        if media_type is None:
            raise ValueError(f'Could not guess file type for {self.path}')
        self.media_type = media_type

    @override
    async def generate(
        self,
        odata: ODataInfo | None,
        extensions: MutableSet[StacExtension],
        item_props: dict[str, Any] = {},
    ) -> dict[str, Any]:
        if odata and odata.thumbnail_link is not None:
            self.https_href = _normalize_thumbnail_href(odata.thumbnail_link)
        return await super().generate(odata, extensions, item_props)


@dataclass(kw_only=True)
class JsonAsset(STACAsset):
    media_type: str = field(default='application/json', init=False)
    roles: Collection[str] = field(default=('data',))


GDAL_VERSION: tuple[int, ...] | None = None


def sanitize_nodata(value):
    if isinstance(value, str) and value.lower() == 'nan':
        return 'nan'
    return value


async def _fill_from_file(
    path: str, props: dict[str, Any], item_props: dict[str, Any]
) -> None:
    """Fill missing asset properties from the file metadata."""
    all_props = ChainMap(item_props, props)

    has_datatype = 'data_type' in all_props
    # An explicit `nodata: None` is a template asserting that the file carries no
    # nodata value, so there is nothing for GDAL to look up. It counts as known,
    # but must not end up in the output.
    has_nodata = 'nodata' in all_props
    if 'nodata' in props and props['nodata'] is None:
        del props['nodata']
    has_projection = (
        'proj:code' in all_props
        or 'proj:wkt2' in all_props
        or 'proj:projjson' in all_props
    )

    # ensure we have at least two of the following: bbox, shape, transform
    has_bbox = 'proj:bbox' in all_props
    has_shape = 'proj:shape' in all_props
    has_transform = 'proj:transform' in all_props
    has_proj_related = sum((has_bbox, has_shape, has_transform)) >= 2

    has_scale = 'scale' in all_props
    has_offset = 'offset' in all_props

    # all required properties are already present
    if has_datatype and has_nodata and has_projection and has_proj_related:
        return

    global GDAL_VERSION
    if GDAL_VERSION is None:
        GDAL_VERSION = await get_gdal_version()
        logging.debug('Detected GDAL version: %s', GDAL_VERSION)

    gdalinfo_data = await run_gdalinfo(path)
    if not gdalinfo_data:
        logging.warning('Failed to read additional metadata for %r with GDAL', path)
        return

    try:
        gdalinfo = orjson.loads(gdalinfo_data)
    except orjson.JSONDecodeError:
        gdalinfo_data_valid_json = re.sub(
            rb'\bnan\b|\bNaN\b|-?[Ii]nfinity\b|-?[Ii]nf\b', b'null', gdalinfo_data
        )
        gdalinfo = json.loads(gdalinfo_data_valid_json)
    stacinfo: dict[str, Any] = gdalinfo.get('stac', {})

    # handle projection related properties
    # these are always in the top-level of the dict
    if not has_projection:
        if props.get('proj:code'):
            pass
        elif 'proj:code' not in props and (proj_code := stacinfo.get('proj:code')):
            props['proj:code'] = proj_code
        elif 'proj:projjson' not in props and (
            proj_projjson := stacinfo.get('proj:projjson')
        ):
            props['proj:projjson'] = proj_projjson
        elif 'proj:wkt2' not in props and (proj_wkt2 := stacinfo.get('proj:wkt2')):
            props['proj:wkt2'] = proj_wkt2

    if not has_shape and (proj_shape := stacinfo.get('proj:shape')):
        props['proj:shape'] = proj_shape
    if not has_transform and (transform := stacinfo.get('proj:transform')):
        if GDAL_VERSION is not None and GDAL_VERSION <= (3, 12, 0):
            # GDAL 3.12.0 and earlier have a bug where the transform is a GeoTransform
            # see https://github.com/OSGeo/gdal/pull/13363
            props['proj:transform'] = [
                transform[1],
                transform[2],
                transform[0],
                transform[4],
                transform[5],
                transform[3],
            ]
        else:
            props['proj:transform'] = transform

    # handle data_type, nodata, scale and offset
    # these are in the bands dict
    band: dict[str, Any]
    gdal_band: dict[str, Any]
    band = next(iter(stacinfo.get('bands', stacinfo.get('raster:bands', ()))), {})
    gdal_band = next(iter(gdalinfo.get('bands', ())), {})

    if not has_datatype:
        band_dt = band.get('data_type')
        if band_dt:
            props['data_type'] = band_dt
        elif band_dt_gdal := gdal_band.get('data_type'):
            props['data_type'] = band_dt_gdal
    if not has_nodata:
        band_nodata = band.get('nodata', band.get('noDataValue'))
        if band_nodata is not None:
            props['nodata'] = sanitize_nodata(band_nodata)
        elif band_nodata_gdal := gdal_band.get('nodata', gdal_band.get('noDataValue')):
            props['nodata'] = sanitize_nodata(band_nodata_gdal)
    if not has_scale:
        band_scale = band.get('scale')
        if band_scale:
            props['raster:scale'] = band_scale
        elif band_scale_gdal := gdal_band.get('scale'):
            props['raster:scale'] = band_scale_gdal
    if not has_offset:
        band_offset = band.get('offset')
        if band_offset:
            props['raster:offset'] = band_offset
        elif band_offset_gdal := gdal_band.get('offset'):
            props['raster:offset'] = band_offset_gdal
    # todo: do we need to handle multiple bands?
    #       Usually, the data type and nodata are the same for all bands.


def has_meaningful_scale_or_offset(d):
    """Return True if any scale != 1 or offset != 0 exists anywhere in a nested dict."""

    def search(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value is not None:
                    if key == 'raster:scale' and value != 1:
                        return True
                    if key == 'raster:offset' and value != 0:
                        return True
                if search(value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if search(item):
                    return True
        return False

    return search(d)
