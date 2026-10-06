from datetime import datetime
from typing import Any
from decimal import Decimal

import re

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import (
    GeoTIFFAsset,
    STACAsset,
    ThumbnailAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    LANDSAT_5_Bands,
    LANDSAT_7_Bands_VCID,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import TraceabilityLink

# Parses software strings by finding the last separator (e.g. '_' or ' ')
# and splitting the string into a name and version based on that separator.
def parse_software(entries: list[str|None]) -> dict[str, str]:
    software = {}
    for entry in entries:
        if entry is None:
            continue
        # Find the last separator in the string
        match = re.search(r'[_\s](?=[^_\s]+$)', entry)
        if match:
            sep_index = match.start()
            name = entry[:sep_index]
            version = entry[sep_index + 1:]
            software[name] = version
    return software

def get_collection_name(scene_name: str, processing_level: str | None) -> str | None:
    if scene_name.startswith('LS05'): # Equivalent to L1G
        if 'TM__GEO_1P' in scene_name:
            return 'landsat-5-l1g'
        elif 'TM__GTC_1P' in scene_name: # Equivalent to L1T
            return 'landsat-5-l1t'
    elif scene_name.startswith('LS07'):
        if 'ETM_GTC_1P' in scene_name:
            return 'landsat-7-l1t'
    elif scene_name.startswith('LE7') and processing_level:
        # for USGS products
        if processing_level == 'l1g' or processing_level == 'l1t' or processing_level == 'l1gt':
            return f'landsat-7-{processing_level}-usgs'
        else:
            raise ValueError(f'Unrecognized product type')

    return None

def cdse_to_usgs_name(cdse_id: str, suffix: str, station: str = "ESA", version: str = "00") -> str:
    """
    Convert a CDSE Landsat product identifier into a legacy USGS-style file name.

    cdse_id: e.g. 'LS05_RFUI_TM__GTC_1P_19840406T092240_19840406T092308_000523_0191_0037_E25D'
    suffix:  whatever comes after the scene ID, e.g. 'B1.TIF', 'MTL.txt', 'GCP.txt'
    station: ground station code (not encoded in CDSE id, must be supplied)
    version: archive version (not encoded in CDSE id, must be supplied)
    """
    pattern = (
        r"^LS(?P<sat>\d{2})_"
        r"(?P<category>[A-Z]{4})_"
        r"(?P<sensor>[A-Z_]{3})_"   # fixed-width 3-char sensor field, right-padded with '_' (e.g. 'TM_' or 'ETM')
        r"(?P<proc>[A-Z]{3})_"
        r"(?P<ptype>\d[A-Z])_"
        r"(?P<start>\d{8}T\d{6})_"
        r"(?P<stop>\d{8}T\d{6})_"
        r"(?P<orbit>\d{6})_"
        r"(?P<path>\d{4})_"
        r"(?P<row>\d{4})_"
        r"(?P<crc>[A-Z0-9]{4})$"
    )
    m = re.match(pattern, cdse_id)
    if not m:
        raise ValueError(f"Doesn't match expected CDSE pattern: {cdse_id}")

    sat_digit = str(int(m.group("sat")))
    sensor_raw = m.group("sensor").rstrip("_")
    sensor_map = {"TM": "T", "MSS": "M", "ETM": "E"}
    sensor_letter = sensor_map.get(sensor_raw, sensor_raw[0])

    path = f"{int(m.group('path')):03d}"
    row = f"{int(m.group('row')):03d}"

    start_dt = datetime.strptime(m.group("start")[:8], "%Y%m%d")
    year = start_dt.strftime("%Y")
    doy = start_dt.strftime("%j")

    usgs_scene_id = f"L{sensor_letter}{sat_digit}{path}{row}{year}{doy}{station}{version}"
    return f"{usgs_scene_id}_{suffix}"


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    is_esa = attr['origin'] == 'ESA'

    constellation, platform_number = attr['platform'].lower().split('_')
    if platform_number != '5' and platform_number != '7':
        raise ValueError(f'Unsupported landsat platform number: {platform_number}')

    productType = attr.get('productType') # only available in ESA products
    collection_name = get_collection_name(attr['filename'], attr['processingLevel'].lower())

    # common extensions
    extensions: set[StacExtension] = {
        StacExtension.SATELLITE,
        StacExtension.PROCESSING,
        StacExtension.PROJECTION,
        StacExtension.VIEW,
        StacExtension.PRODUCT,
        StacExtension.RASTER,
        StacExtension.EO,
        StacExtension.GRID,
        StacExtension.INSTRUMENTS,
    }

    gsdPan = 15 if platform_number == '7' else None
    gsdThermal = 60 if platform_number == '7' else 120
    gsdReflective = 30
    all_gsd = [gsdPan, gsdThermal, gsdReflective]
    gsd = min([x for x in all_gsd if x is not None])

    # common properties
    props = {
        'datetime': f'{attr["date"]}T{attr["time"]}',
        'platform': f'{constellation}-{platform_number}',
        'constellation': constellation,
        'instruments': [
            attr['instrument'].lower()
        ],
        'instrument_modes': [
            attr['instrumentMode'].lower()
        ],
        'gsd': gsd,
        'processing:level': attr['processingLevel'][:2],
        'processing:datetime': attr['processingDate'],
        'processing:software': parse_software([
            attr.get('processingSoftware1'),
            attr.get('processingSoftware2')
        ]),
        'product:acquisition_type': attr['acquisitionType'].lower(),
        'grid:code': f'WRS2-{attr["wrsPath"]:03d}{attr["wrsRow"]:03d}',
        'sat:platform_international_designator': '1984-021A' if platform_number == '5' else '1999-020A',
        'view:sun_elevation': attr['sunElevation'],
        'view:sun_azimuth': float((Decimal(attr['sunAzimuth']) + Decimal(360)) % Decimal(360)), # avoid floating point issues
    }

    if productType:
        props['product:type'] = productType

    if start_datetime := attr.get('beginningDateTime'):
        props['start_datetime'] = start_datetime

    if end_datetime := attr.get('endingDateTime'):
        props['end_datetime'] = end_datetime

    cloud_cover = attr.get('cloudCover', -1)
    if cloud_cover >= 0:
        extensions.add(StacExtension.EO)
        props['eo:cloud_cover'] = cloud_cover

    if orbit := attr.get('orbitNumber'):
         props['sat:absolute_orbit'] = orbit

    if orbit_direction := attr.get('orbitDirection'):
        props['sat:orbit_state'] = orbit_direction.lower()

    # common assets
    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(attr['filename'], omit_date=True, omit_collection=True, zipper=extended_private_data)
    item_path: str = attr['filepath']
    subfolder_path: str = f'{item_path}/{attr["productID"]}.TIFF'

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

    proj_bbox = [
        min(attr['cornerULX'], attr['cornerURX'], attr['cornerLLX'], attr['cornerLRX']),
        min(attr['cornerULY'], attr['cornerURY'], attr['cornerLLY'], attr['cornerLRY']),
        max(attr['cornerULX'], attr['cornerURX'], attr['cornerLLX'], attr['cornerLRX']),
        max(attr['cornerULY'], attr['cornerURY'], attr['cornerLLY'], attr['cornerLRY']),
    ]

    projection = attr.get('projection')
    if projection == 'UTM':
        # Landsat uses only the northern UTM zones, even for data in the southern hemisphere
        utm = abs(attr['utmZone'])
        proj_code = f'EPSG:326{utm:02d}'
    elif projection == 'PS':
        proj_code = "EPSG:3031"  # Antarctic Polar Stereographic
    else:
        raise ValueError(f'Unsupported projection type: {attr.get("projection")}')
    proj_shape_reflective = (attr['reflectiveLines'], attr['reflectiveSamples'])
    proj_shape_thermal = (attr['thermalLines'], attr['thermalSamples'])
    proj_shape_pan = (attr.get('panLines'), attr.get('panSamples'))

    assets: dict[str, STACAsset] = {
        'product_metadata': STACAsset(
            path=f'{item_path}/{attr["productID"]}_MTL.txt' if is_esa == False else f'{subfolder_path}/{cdse_to_usgs_name(attr["productID"], 'MTL.txt')}',
            title=f'{attr["productID"]}_MTL.txt',
            roles=('metadata',),
            media_type='text/plain',
        ),
    }

    if is_esa:
        assets['product_metadata_esa'] = XMLAsset(
            path=f'{item_path}/{attr["productID"]}.MTR.XML',
            title=f'{attr["productID"]}.MTR.XML',
            roles=('metadata',),
        )
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/{attr["thumbnailFilename"]}',
            roles=('thumbnail', 'overview'),
            extra={
                'proj:code': attr['thumbnailProjection'],
            }
        )
    else:
        assets['thumbnail'] = ThumbnailAsset(
            path=f'{item_path}/{attr["productID"]}.jpg',
            roles=('thumbnail', 'overview'),
            extra={
                'proj:code': None,
            }
        )
        assets['visual'] = ThumbnailAsset(
            path=f'{item_path}/{attr["productID"]}.tif',
            roles=('overview','visual'),
            extra={
                'proj:code': proj_code,
            }
        )
        assets['thumbnail_tir'] = ThumbnailAsset(
            path=f'{item_path}/{attr["productID"]}_TIR.jpg',
            roles=('thumbnail', 'overview'),
            extra={
                'proj:code': None,
            }
        )
        assets['visual_tir'] = ThumbnailAsset(
            path=f'{item_path}/{attr["productID"]}_TIR.tif',
            roles=('overview','visual'),
            extra={
                'proj:code': proj_code,
            }
        )

    bands = LANDSAT_5_Bands if platform_number == '5' else LANDSAT_7_Bands_VCID
    for band_id in bands:
        band = bands[band_id]
        is_thermal = band.get('eo:common_name') == 'lwir'
        is_pan = band.get('eo:common_name') == 'pan'
        roles = ['data']

        if is_thermal:
            roles.append('temperature')
            gsd = gsdThermal
            resolution = attr['cellSizeThermal']
            proj_shape = proj_shape_thermal
        elif is_pan:
            roles.append('panchromatic')
            gsd = gsdPan
            resolution = attr['cellSizePan']
            proj_shape = proj_shape_pan
        else:
            gsd = gsdReflective
            resolution = attr['cellSizeReflective']
            proj_shape = proj_shape_reflective

        scale = attr.get(f'{band_id}_reflectance_scale')
        offset = attr.get(f'{band_id}_reflectance_offset')
        measurement_type = 'reflectance'
        if scale is None and offset is None:
            scale = attr.get(f'{band_id}_radiance_scale')
            offset = attr.get(f'{band_id}_radiance_offset')
            measurement_type = 'radiance'
            if scale is None and offset is None:
                measurement_type = None

        if measurement_type is not None:
            roles.append(measurement_type)

        extra = {
            'bands': [band],
            'gsd': gsd,
            'data_type': 'uint8',
            'nodata:': 0,
            'proj:code': proj_code,
            'proj:bbox': proj_bbox,
            'proj:shape': proj_shape,
            'raster:spatial_resolution': resolution,
        }
        if scale is not None:
            extra['raster:scale'] = scale
        if offset is not None:
            extra['raster:offset'] = offset

        if measurement_type and measurement_type not in roles:
            roles.append(measurement_type)

        assets[band_id] = GeoTIFFAsset(
            path=f'{item_path}/{attr["productID"]}_{band_id}.TIF' if is_esa == False else f'{subfolder_path}/{cdse_to_usgs_name(attr["productID"], 'MTL.txt')}',
            title=f'{band["description"]} - {gsd}m',
            description=f'Applying scale and offset will convert the pixel values to {measurement_type}.' if measurement_type else None,
            roles=roles,
            extra=extra,
        )

    coordinates = attr.get('coordinates')
    if not coordinates:
        # Build geographic WKT (lon/lat) from corner points if not provided.
        coordinates = "POLYGON(({ullon} {ullat}, {urlon} {urlat}, {lrlon} {lrlat}, {lllon} {lllat}, {ullon} {ullat}))".format(
            ullon=attr['cornerULLon'],
            ullat=attr['cornerULLat'],
            urlon=attr['cornerURLon'],
            urlat=attr['cornerURLat'],
            lrlon=attr['cornerLRLon'],
            lrlat=attr['cornerLRLat'],
            lllon=attr['cornerLLLon'],
            lllat=attr['cornerLLLat'],
        )

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection_name,
        identifier=attr['productID'],
        coordinates=coordinates,
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
