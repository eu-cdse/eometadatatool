import logging
import mimetypes
from collections import ChainMap
from collections.abc import Collection, Mapping, MutableSet
from dataclasses import dataclass, field
from typing import Any, Literal, override

import orjson

from eometadatatool.dlc import ODataInfo, asset_to_zipper, hex_to_multihash
from eometadatatool.gdalinfo import run_gdalinfo
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.utils import EMPTY_MAPPING

type AlternateKey = Literal['s3', 'https']

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
        return props


@dataclass(kw_only=True)
class JPEG2000Asset(STACAsset):
    media_type: str = field(default='image/jp2', init=False)
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
        if odata:
            self.https_href = odata.thumbnail_link
        return await super().generate(odata, extensions, item_props)


async def _fill_from_file(
    path: str, props: dict[str, Any], item_props: dict[str, Any]
) -> None:
    """Fill missing asset properties from the file metadata."""
    all_props = ChainMap(item_props, props)

    has_datatype = "data_type" in all_props
    has_nodata = "nodata" in all_props
    has_projection = "proj:code" in all_props or "proj:wkt2" in all_props or "proj:projjson" in all_props

    # ensure we have at least two of the following: bbox, shape, transform
    has_bbox = "proj:bbox" in all_props
    has_shape = "proj:shape" in all_props
    has_transform = "proj:transform" in all_props
    has_proj_related = sum((has_bbox, has_shape, has_transform)) >= 2

    # all required properties are already present
    if has_datatype and has_nodata and has_projection and has_proj_related:
        return

    gdalinfo_data = await run_gdalinfo(path)
    if not gdalinfo_data:
        logging.warning('Failed to read additional metadata for %r with GDAL', path)
        return

    gdalinfo = orjson.loads(gdalinfo_data)
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
    if not has_transform and (proj_transform := stacinfo.get('proj:transform')):
        props['proj:transform'] = proj_transform

    # handle nodata and data_type
    # these are in the bands dict
    band: dict[str, Any]
    band = next(iter(stacinfo.get('bands', stacinfo.get('raster:bands', ()))), {})

    if not has_datatype and (band_dt := band.get('data_type')):
        props['data_type'] = band_dt
    if not has_nodata and (band_nodata := band.get('nodata')):
        props['nodata'] = band_nodata
    # todo: do we need to handle multiple bands?
    #       Usually, the data type and nodata are the same for all bands.
