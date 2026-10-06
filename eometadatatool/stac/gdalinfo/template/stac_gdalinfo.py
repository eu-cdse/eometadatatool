import mimetypes
from collections import Counter
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shapely import union_all
from shapely.geometry import shape

from eometadatatool.dlc import ODataInfo
from eometadatatool.stac.framework.stac_asset import STACAsset, ThumbnailAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    extents: list[BaseGeometry] = []
    assets: dict[str, STACAsset] = {}

    ql_path = attr.get('ql:path')
    ql_name = attr.get('ql:name')
    all_metapaths: list[Path] = []
    thumbnail_stacinfo: dict[str, Any] = {}

    # First pass: collect all metapaths and check for thumbnail
    metapath: Path
    for metapath in attr['gdalinfo']:
        metapath = metapath.with_suffix('')  # strip .json suffix
        all_metapaths.append(metapath)

    # Generate simplified names for all non-thumbnail assets
    simplified_names = _simplify_names(all_metapaths)

    # Second pass: create assets with simplified names
    gdalinfo: dict[str, Any]
    for metapath, gdalinfo in attr['gdalinfo'].items():
        metapath = metapath.with_suffix('')  # strip .json suffix
        stacinfo: dict[str, Any] = gdalinfo.get('stac', {})

        # Transform proj:epsg into proj:code
        proj_epsg = stacinfo.pop('proj:epsg', None)
        if proj_epsg and 'proj:code' not in stacinfo:
            stacinfo['proj:code'] = f'EPSG:{proj_epsg}'

        # Transform cornerCoordinates into proj:bbox
        corner = gdalinfo.get('cornerCoordinates')
        if corner is not None:
            stacinfo['proj:bbox'] = [*corner['lowerLeft'], *corner['upperRight']]

        # Store thumbnail stacinfo for later
        if ql_name == metapath.name:
            thumbnail_stacinfo = stacinfo
            continue

        extent = gdalinfo.get('wgs84Extent')
        if extent is not None:
            extents.append(shape(extent))

        asset_name = simplified_names[metapath]
        asset_path = str(metapath)
        assets[asset_name] = STACAsset(
            path=asset_path,
            media_type=_get_media_type(gdalinfo['driverShortName'], asset_path),
            title=f'{gdalinfo["driverLongName"]} data file',
            roles=['data'],
            https_href=None,
            extra=stacinfo,
        )

    if ql_path is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path, extra=thumbnail_stacinfo)

    assert extents, 'No extents found'

    odata = ODataInfo(
        id='',
        thumbnail_link=None,
        checksum='',
        checksum_algorithm=None,
        file_size=0,
        created_isodate=attr['publicationDate'],
        updated_isodate=attr['publicationDate'],
        published_isodate=attr['publicationDate'],
        origin=None,
        name=attr['filename'],
    )
    item = STACItem(
        path=attr['filepath'],
        odata=odata,
        collection='gdalinfo',
        identifier=attr['identifier'],
        coordinates=union_all(extents).normalize().wkt,
        links=[],
        assets=assets,
        product_asset_name=None,
        extensions=(
            StacExtension.PROJECTION,
            StacExtension.RASTER,
            StacExtension.EO,
        ),
        extra={
            'datetime': attr['publicationDate'],
        },
    )
    return await item.generate()


def _simplify_names(metapaths: list[Path]) -> dict[Path, str]:
    stages_map: dict[Path, list[str]] = {}
    for p in metapaths:
        name_parts = p.name.split('.')
        stages_map[p] = list(
            chain(
                ('.'.join(name_parts[: i + 1]) for i in range(len(name_parts))),
                ('/'.join(p.parts[-i:]) for i in range(2, len(p.parts) + 1)),
            )
        )

    indices = dict.fromkeys(metapaths, 0)

    while True:
        names = {
            p: stages_map[p][min(idx, len(stages_map[p]) - 1)]
            for p, idx in indices.items()
        }

        counts = Counter(names.values())
        conflicts = {n for n, c in counts.items() if c > 1}

        if not conflicts:
            return names

        for p, name in names.items():
            if name in conflicts and indices[p] < len(stages_map[p]) - 1:
                indices[p] += 1


def _get_media_type(driver: str, file: str) -> str:
    """Get media type using stdlib mimetypes with GDAL driver fallbacks."""
    # First try stdlib mimetypes based on filename
    if mime_type := mimetypes.guess_type(file)[0]:
        # Add geospatial-specific profiles for known formats
        if mime_type == 'image/tiff':
            if driver == 'COG':
                return 'image/tiff; application=geotiff; profile=cloud-optimized'
            if driver == 'GTiff':
                return 'image/tiff; application=geotiff'
        return mime_type

    # Fallback to driver-specific mappings
    driver_mapping = {
        'BAG': 'application/x-hdf5',
        'ECW': 'image/x-ecw',
        'ENVI': 'application/x-envi',
        'ERDAS': 'application/x-erdas-img',
        'GRIB': 'model/grib2',
        'HDF4': 'application/x-hdf',
        'HDF5': 'application/x-hdf5',
        'MrSID': 'image/x-mrsid',
        'netCDF': 'application/x-netcdf',
        'PCIDSK': 'application/x-pcidsk',
        'PDS': 'application/x-pds',
        'USGSDEM': 'application/x-usgsdem',
        'VRT': 'application/x-gdal-vrt',
        'ZARR': 'application/x-zarr',
    }
    return driver_mapping.get(driver, 'application/octet-stream')
