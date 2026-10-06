import math
from collections.abc import Collection, Mapping, MutableSet, Sequence
from dataclasses import dataclass, field
from typing import Any, override

from eometadatatool.dlc import ODataInfo
from eometadatatool.gdalinfo import get_gdal_version
from eometadatatool.stac.framework.stac_asset import (
    AlternateKey,
    STACAsset,
    sanitize_nodata,
)
from eometadatatool.stac.framework.stac_extension import StacExtension

_THUMBNAIL_WMS = (
    'https://thumbnails.dataspace.copernicus.eu/wms?SERVICE=WMS&VERSION=1.3.0'
    '&REQUEST=GetMap&LAYERS={layers}&CRS={crs}&BBOX={bbox}'
    '&WIDTH={width}&HEIGHT={height}&FORMAT=image/png&TRANSPARENT=false'
)
_SLD_BASE = (
    'https://raw.githubusercontent.com/copernicus-land/colourmaps-legends/'
    'main/colourmaps/'
)

_THUMBNAIL_DIMENSIONS: tuple[tuple[int, int], ...] = (
    (750, 750),
    (750, 488),
    (750, 455),
    (750, 375),
    (750, 333),
    (750, 292),
    (750, 123),
    (750, 104),
    (750, 675),
    (750, 600),
    (750, 525),
    (675, 750),
    (600, 750),
    (525, 750),
)
_GDAL_VERSION: tuple[int, ...] | None = None
_GDAL_VERSION_CHECKED = False


@dataclass(kw_only=True)
class WMSThumbnailAsset(STACAsset):
    media_type: str = field(default='image/png', init=False)
    title: str = field(default='Quicklook')
    roles: Collection[str] = field(default=('thumbnail', 'overview'))
    prefer_alternate: AlternateKey = field(default='https', init=False)
    include_other_alternates: bool = field(default=False, init=False)
    is_https_public: bool = field(default=True, init=False)

    def __post_init__(self):
        self.https_href = self.path
        super().__post_init__()

    @override
    async def generate(
        self,
        odata: ODataInfo | None,
        extensions: MutableSet[StacExtension],
        item_props: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.https_href = self.path
        return await super().generate(None, extensions, item_props or {})


def native_bbox(transform: Sequence[float], shape: Sequence[int]) -> list[float]:
    a, _b, c, _d, e, f = transform[:6]
    rows, cols = shape[0], shape[1]
    return [c, f + e * rows, c + a * cols, f]


def thumbnail_dimensions(aspect: float) -> tuple[int, int]:
    return min(
        _THUMBNAIL_DIMENSIONS,
        key=lambda wh: abs(math.log((wh[0] / wh[1]) / aspect)),
    )


def wms_thumbnail_asset(
    *,
    layers: str,
    crs: str,
    bbox: Sequence[float],
    aspect: float | None = None,
    size: tuple[int, int] | None = None,
    sld: str | None = None,
) -> WMSThumbnailAsset:
    if size is not None:
        width, height = size
    elif aspect is not None:
        width, height = thumbnail_dimensions(aspect)
    else:
        raise ValueError('Either aspect or size must be given')
    href = _THUMBNAIL_WMS.format(
        layers=layers,
        crs=crs,
        bbox=','.join(str(v) for v in bbox),
        width=width,
        height=height,
    )
    if sld:
        href = f'{href}&sld={_SLD_BASE}{sld}'

    return WMSThumbnailAsset(
        path=href,
        extra={
            'data_type': 'uint8',
            'proj:bbox': list(bbox),
            'proj:code': crs,
            'proj:shape': [height, width],
            'alternate:name': 'HTTPS',
        },
    )


async def stac_extra_from_gdalinfo(
    gdalinfo: Mapping[str, Any],
    *,
    fallback_proj_code: str | None = None,
) -> dict[str, Any]:
    stacinfo: Mapping[str, Any] = gdalinfo.get('stac', {})
    extra: dict[str, Any] = {}

    if proj_code := stacinfo.get('proj:code'):
        extra['proj:code'] = proj_code
    elif proj_epsg := stacinfo.get('proj:epsg'):
        extra['proj:code'] = f'EPSG:{proj_epsg}'
    elif fallback_proj_code:
        extra['proj:code'] = fallback_proj_code
    elif proj_projjson := stacinfo.get('proj:projjson'):
        extra['proj:projjson'] = proj_projjson
    elif proj_wkt2 := stacinfo.get('proj:wkt2'):
        extra['proj:wkt2'] = proj_wkt2

    if proj_shape := stacinfo.get('proj:shape'):
        extra['proj:shape'] = proj_shape

    if transform := stacinfo.get('proj:transform'):
        if await _uses_gdal_geotransform_stac_bug():
            extra['proj:transform'] = [
                transform[1],
                transform[2],
                transform[0],
                transform[4],
                transform[5],
                transform[3],
            ]
        else:
            extra['proj:transform'] = transform

    if proj_bbox := stacinfo.get('proj:bbox'):
        extra['proj:bbox'] = proj_bbox
    elif 'proj:transform' in extra and 'proj:shape' in extra:
        extra['proj:bbox'] = native_bbox(
            extra['proj:transform'],
            extra['proj:shape'],
        )

    band = next(iter(stacinfo.get('bands', stacinfo.get('raster:bands', ()))), {})
    gdal_band = next(iter(gdalinfo.get('bands', ())), {})

    if band_dt := band.get('data_type'):
        extra['data_type'] = band_dt
    elif band_dt_gdal := gdal_band.get('data_type'):
        extra['data_type'] = band_dt_gdal

    band_nodata = band.get('nodata', band.get('noDataValue'))
    if band_nodata is not None:
        extra['nodata'] = sanitize_nodata(band_nodata)
    else:
        band_nodata_gdal = gdal_band.get('nodata', gdal_band.get('noDataValue'))
        if band_nodata_gdal is not None:
            extra['nodata'] = sanitize_nodata(band_nodata_gdal)

    if band_scale := band.get('scale'):
        extra['raster:scale'] = band_scale
    elif band_scale_gdal := gdal_band.get('scale'):
        extra['raster:scale'] = band_scale_gdal

    if band_offset := band.get('offset'):
        extra['raster:offset'] = band_offset
    elif band_offset_gdal := gdal_band.get('offset'):
        extra['raster:offset'] = band_offset_gdal

    return extra


async def _uses_gdal_geotransform_stac_bug() -> bool:
    global _GDAL_VERSION, _GDAL_VERSION_CHECKED
    if not _GDAL_VERSION_CHECKED:
        _GDAL_VERSION = await get_gdal_version()
        _GDAL_VERSION_CHECKED = True
    if _GDAL_VERSION is None:
        # GDAL version undetectable -> assume a recent, fixed GDAL (no reorder).
        return False
    return _GDAL_VERSION <= (3, 12, 0)
