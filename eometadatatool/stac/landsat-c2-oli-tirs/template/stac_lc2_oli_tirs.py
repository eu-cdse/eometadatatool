from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    CloudOptimizedGeoTIFFAsset,
    STACAsset,
    ThumbnailAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    LANDSAT_C2_OLI_TIRS_Bands,
    generate_bands,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink
from eometadatatool.stac.framework.utils import gdal_footprint_to_wkt, generate_product_uuid

from .bitfields import qa_bitfields, radsat_bitfields

# Fixed raster properties of the L2 surface temperature (ST) bands, per the Landsat
# Collection 2 Level-2 Data Format Control Book. Only used by the 'landsat-c2-l2-oli-tirs'
# ST products. Supplying data_type and nodata lets the framework skip the per-asset
# gdalinfo lookup; ST_B10 has no fixed scale, its rescaling comes from the scene metadata.
_L2_ST_RASTER_PROPS: dict[str, dict[str, Any]] = {
    'ST_B10': {'data_type': 'uint16', 'nodata': 0},
    'ST_TRAD': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.001},
    'ST_URAD': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.001},
    'ST_DRAD': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.001},
    'ST_ATRAN': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.0001},
    'ST_EMIS': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.0001},
    'ST_EMSD': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.0001},
    'ST_CDIST': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.01},
    'ST_QA': {'data_type': 'int16', 'nodata': -9999, 'raster:scale': 0.01},
}


def _recognize_collection(filename: str) -> str | None:
    if filename.startswith('LO') and '_L1' in filename:
        return 'landsat-c2-l1-oli'
    if filename.startswith('LC') and '_L1' in filename:
        return 'landsat-c2-l1-oli-tirs'
    if filename.startswith('LT') and '_L1' in filename:
        return 'landsat-c2-l1-tirs'
    if filename.startswith('LC') and '_L2' in filename:
        return 'landsat-c2-l2-oli-tirs'

    return None


def _calculate_bbox(attr: dict[str, Any]) -> list[float]:
    lons = [
        attr['cornerULLon'],
        attr['cornerURLon'],
        attr['cornerLLLon'],
        attr['cornerLRLon'],
    ]
    lats = [
        attr['cornerULLat'],
        attr['cornerURLat'],
        attr['cornerLLLat'],
        attr['cornerLRLat'],
    ]
    return [min(lons), min(lats), max(lons), max(lats)]


def _get_grid_cell_size(attr: dict[str, Any], band_id: str) -> float:
    if band_id == 'B8':
        return attr['gridCellSizePanchromatic']
    elif band_id in ['B10', 'B11']:
        return attr['gridCellSizeThermal']
    return attr['gridCellSizeReflective']


def _get_proj_shape(attr: dict[str, Any], band_id: str) -> tuple[int, int]:
    if band_id in ['B10', 'B11']:
        return attr['thermalLines'], attr['thermalSamples']
    return attr['reflectiveLines'], attr['reflectiveSamples']


def _build_transform(attr: dict[str, Any], band_id: str) -> tuple:
    cell_size = _get_grid_cell_size(attr, band_id)
    half_cell = cell_size / 2
    ul_x = attr['cornerULX'] - half_cell
    ul_y = attr['cornerULY'] + half_cell
    return cell_size, 0, ul_x, 0, -cell_size, ul_y


def _get_raster_params(attr: dict[str, Any], band_id: str) -> tuple[float, float]:
    band_num = band_id[1:]
    if band_id in ['B10', 'B11']:
        return attr[f'radianceMultBand{band_num}'], attr[f'radianceAddBand{band_num}']
    return attr[f'reflectanceMultBand{band_num}'], attr[f'reflectanceAddBand{band_num}']


def _get_proj_code(attr: dict[str, Any]) -> str:
    utm_zone = attr.get('utm')
    if utm_zone:
        epsg = f'326{utm_zone:02d}'
    else:
        # Polar Stereographic: Based on Landsat 8-9 OLI/TIRS Collection 2 Level 1
        # Data Format Control Book, should only ever be 71 or -71
        lat_ts = int(attr.get('trueScaleLat', 0))
        if lat_ts == -71:
            epsg = '3031'  # Antarctic
        elif lat_ts == 71:
            epsg = '3995'  # Arctic
        else:
            raise Exception(
                f'Unexpeced value for PROJECTION_ATTRIBUTES/TRUE_SCALE_LAT: {lat_ts} '
            )
    return f'EPSG:{epsg}'


def _get_l2_product_type(scene_name: str) -> str | None:
    if '_SR' in scene_name:
        return 'sr'
    elif '_ST' in scene_name:
        return 'st'

    return None


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    collection_name = _recognize_collection(attr['filename'])
    if collection_name is None:
        raise ValueError(f'Unrecognized collection for filename: {attr["filename"]}')
    level = attr['processingLevel'][:2]
    l2_product_type = _get_l2_product_type(attr['filename'])

    # common extensions
    extensions: set[StacExtension] = {
        StacExtension.PROCESSING,
        StacExtension.PROJECTION,
        StacExtension.VIEW,
        StacExtension.PRODUCT,
        StacExtension.RASTER,
        StacExtension.CLASSIFICATION,
        StacExtension.GRID,
    }

    platform_identifiers = {
        'landsat-8': '2013-008A',
        'landsat-9': '2021-088A',
    }

    datetime = attr.get('datetime', attr.get('datetimeAlt'))
    if datetime is None:
        raise ValueError('No datetime found in "datetime" or "datetimeAlt" attributes')

    # common properties
    platform = attr['spacecraftID'].lower().replace('_', '-')
    props = {
        'datetime': datetime,
        'platform': platform,
        'constellation': 'landsat',
        'instruments': collection_name[14:].split('-'),
        'gsd': 30,
        'processing:level': level,
        'processing:datetime': attr['dateGenerated'],
        'processing:version': attr['processingVersion'],
        'product:type': attr['processingLevel'],
        'product:timeliness': 'PT6H' if level == 'L1' else 'PT24H',
        'product:timeliness_category': 'STC',
        'grid:code': f'WRS{attr["wrsType"]}-{attr["wrsPath"]:03d}{attr["wrsRow"]:03d}',
        'view:off_nadir': abs(attr['rollAngle'])
        if attr['nadirOffnadir'] == 'OFFNADIR'
        else 0,
        'view:sun_elevation': attr['sunElevation'],
        'view:sun_azimuth': attr['sunAzimuth']
        if attr['sunAzimuth'] >= 0
        else attr['sunAzimuth'] + 360,
    }

    cloud_cover = attr.get('cloudCover', -1)
    if cloud_cover >= 0:
        extensions.add(StacExtension.EO)
        props['eo:cloud_cover'] = cloud_cover

    cloud_cover_land = attr.get('cloudCoverLand', -1)
    if cloud_cover_land >= 0:
        props['statistics'] = {
            'cloud_cover_land': attr['cloudCoverLand'],
        }

    platform_id = platform_identifiers.get(platform)
    if platform_id:
        extensions.add(StacExtension.SATELLITE)
        props['sat:platform_international_designator'] = platform_id

    if reflectanceAlgoVer := attr.get('reflectanceAlgorithmVer'):
        props.setdefault('processing:software', {})['LaSRC'] = reflectanceAlgoVer

    if procSoftwareVer := attr.get('processingSoftwareVer'):
        props.setdefault('processing:software', {})['LPGS'] = procSoftwareVer

    if collection_name == 'landsat-c2-l2-oli-tirs':
        accuracy_props = {
            'accuracy:geometric_x_stddev': attr.get('geometricXStdDev'),
            'accuracy:geometric_y_stddev': attr.get('geometricYStdDev'),
            'accuracy:geometric_rmse': attr.get('geometricRMSE'),
        }

        if all(v is not None for v in accuracy_props.values()):
            extensions.add(StacExtension.ACCURACY)
            props.update(accuracy_props)

    proj_properties = {
        'proj:code': _get_proj_code(attr),
        'proj:shape': (
            (attr['thermalLines'], attr['thermalSamples'])
            if collection_name == 'landsat-c2-l1-tirs'
            else (attr['reflectiveLines'], attr['reflectiveSamples'])
        ),
        'proj:bbox': _calculate_bbox(attr),
        # default grid for assets that are not per-band (QA, angle and L2 ST bands);
        # per-band assets override this below
        'proj:transform': _build_transform(
            attr, 'B10' if collection_name == 'landsat-c2-l1-tirs' else 'B1'
        ),
    }

    # common assets
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(
        attr['filename'],
        zipper=extended_private_data,
        omit_date=True,
        omit_collection=True,
    )
    item_path: str = attr['filepath']

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        # product_uuid is intentionally None:
        # these products get generated via a different endpoint
        props['_private']['product_uuid'] = odata.id if odata is not None else None
        if odata is not None:
            props['_private']['product_name'] = odata.name
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

        if extended_private_data and odata is not None:
            props['_private']['brands'] = odata.zipper_data

    assets: dict[str, STACAsset] = {
        'product_metadata': XMLAsset(
            path=f'{item_path}/{attr["productID"]}_MTL.xml',
            title=f'{attr["productID"]}_MTL.xml',
            roles=('metadata',),
            include_other_alternates=False if level == 'L2' else True,
        ),
        'qa_pixel': CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_QA_PIXEL.TIF',
            title='Quality Assessment Band',
            roles=('cloud', 'cloud-shadow', 'snow-ice', 'water-mask'),
            extra={
                'classification:bitfields': qa_bitfields,
                'data_type': 'uint16',
                'nodata': None,  # QA bands carry no nodata value
                **proj_properties,
            },
            include_other_alternates=False if level == 'L2' else True,
        ),
        'qa_radsat': CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_QA_RADSAT.TIF',
            title='Radiometric Saturation Quality Assessment Band',
            roles=('data', 'saturation'),
            extra={
                'classification:bitfields': radsat_bitfields,
                'data_type': 'uint16',
                'nodata': None,  # QA bands carry no nodata value
                **proj_properties,
            },
            include_other_alternates=False if level == 'L2' else True,
        ),
        'ANG': STACAsset(
            path=f'{item_path}/{attr["productID"]}_ANG.txt',
            media_type='text/plain',
            title='Angle Coefficients File',
            roles=('metadata',),
            include_other_alternates=False if level == 'L2' else True,
        ),
    }

    if not (collection_name == 'landsat-c2-l2-oli-tirs' and l2_product_type == 'sr'):
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/{attr["productID"]}_thumb_large.jpeg',
            roles=('thumbnail', 'overview'),
            include_other_alternates=False if level == 'L2' else True,
        )

    # collection-specific assets
    if collection_name in ['landsat-c2-l1-oli', 'landsat-c2-l1-oli-tirs']:
        # angle bands are int16 and carry no nodata value
        angle_properties = {
            'data_type': 'int16',
            'nodata': None,
            **proj_properties,
        }
        assets['VAA'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_VAA.TIF',
            title='Sensor Azimuth Angle Band',
            roles=('data', 'azimuth'),
            extra=angle_properties,
        )
        assets['VZA'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_VZA.TIF',
            title='Sensor Zenith Angle Band',
            roles=('data', 'zenith'),
            extra=angle_properties,
        )
        assets['SAA'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_SAA.TIF',
            title='Solar Azimuth Angle Band',
            roles=('data', 'sun-azimuth'),
            extra=angle_properties,
        )
        assets['SZA'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_SZA.TIF',
            title='Solar Zenith Angle Band',
            roles=('data', 'sun-zenith'),
            extra=angle_properties,
        )

    # L2 ST-specific assets
    if collection_name == 'landsat-c2-l2-oli-tirs' and l2_product_type == 'st':
        if tempAlgoVer := attr.get('temperatureAlgorithmVer'):
            props.setdefault('processing:software', {})['Landsat Surface Temperature'] = tempAlgoVer

        assets['ST_ATRAN'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_ATRAN.TIF',
            title='Atmospheric Transmittance Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_ATRAN'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_B10'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_B10.TIF',
            title='Surface Temperature Band 10',
            roles=('data', 'temperature'),
            extra={
                **_L2_ST_RASTER_PROPS['ST_B10'],
                'raster:scale': attr['temperatureMultBandSTB10'],
                'raster:offset': attr['temperatureAddBandSTB10'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_CDIST'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_CDIST.TIF',
            title='Cloud Distance Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_CDIST'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_DRAD'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_DRAD.TIF',
            title='Downwelled Radiance Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_DRAD'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_EMIS'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_EMIS.TIF',
            title='Emissivity Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_EMIS'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_EMSD'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_EMSD.TIF',
            title='Emissivity Standard Deviation Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_EMSD'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_QA'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_QA.TIF',
            title='Surface Temperature Quality Assessment Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_QA'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_TRAD'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_TRAD.TIF',
            title='Thermal Radiance Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_TRAD'],
                'gsd': 30.0,
                **proj_properties,
            },
        )
        assets['ST_URAD'] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_URAD.TIF',
            title='Upwelled Radiance Band',
            roles=('data',),
            extra={
                **_L2_ST_RASTER_PROPS['ST_URAD'],
                'gsd': 30.0,
                **proj_properties,
            },
        )


    # collection-specific bands
    ranges = {
        'landsat-c2-l1-oli': range(1, 10),
        'landsat-c2-l1-tirs': range(10, 12),
        'landsat-c2-l1-oli-tirs': range(1, 12),
        'landsat-c2-l2-oli-tirs': range(1, 8),
    }

    for band in generate_bands(
        LANDSAT_C2_OLI_TIRS_Bands, [f'B{num}' for num in ranges[collection_name]]
    ):
        if l2_product_type == 'st':
            break

        band_id = band['name']
        scale, offset = _get_raster_params(attr, band_id)
        gsd = 15.0 if band_id == 'B8' else 30.0

        assets[band_id] = CloudOptimizedGeoTIFFAsset(
            path=f'{item_path}/{attr["filename"]}_{band_id}.TIF',
            title=f'{band["description"]} - {int(gsd)}m',
            roles=(
                'data',
                'temperature'
                if collection_name == 'landsat-c2-l1-tirs'
                else 'reflectance',
            ),
            extra={
                'bands': [band],
                'data_type': 'uint16',
                'nodata': 0,
                'raster:scale': scale,
                'raster:offset': offset,
                'gsd': gsd,
                **proj_properties,
                'proj:shape': _get_proj_shape(
                    attr, band_id
                ),  # overrides proj:shape in proj_properties
                'proj:transform': _build_transform(attr, band_id),
            },
            include_other_alternates=False if level == 'L2' else True,
        )

    """
    Geometry in L2SP SR MTL file covers corners of the full north-up raster
    (data + nodata fill triangles), which would be invalid for STAC geometry,
    hence the need to use gdal_footprint_to_wkt for those products.
    """

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection_name,
        identifier=attr['filename'],
        coordinates=attr['coordinates']
        if attr.get('coordinates') is not None
        else await gdal_footprint_to_wkt(
            assets.get('B1', assets.get('ST_B10')).path.replace('s3://', '/vsis3/', 1)
        ),
        links=[
            TraceabilityLink(href=f'{attr["filename"]}.zip'),
        ],
        product_asset_name='Product',
        assets=assets,
        extensions=extensions,
        extra=props,
        eopf=False,
    )

    return await item.generate()
