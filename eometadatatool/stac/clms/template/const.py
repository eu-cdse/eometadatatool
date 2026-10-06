from shapely.geometry import Polygon
from typing import NamedTuple


TYPES = {
    'ba': 'burnt_area',
    'dmp': 'dry-gross_dry_matter_productivity',
    'lswt': 'lake_surface_water_temperature',
    'lwq': 'lake_water_quality',
    'lst': 'land_surface_temperature',
    'gpp': 'net-gross_primary_production',
    'lie': 'river_and_lake_ice_extent',
    'sce': 'snow_cover_extent',
    'swe': 'snow_water_equivalent',
    'swi': 'soil_water_index',
    'ssm': 'surface_soil_moisture',
    'toc': 'top-of-canopy_reflectances',
    'vgt_ind': 'vegetation_indices',
    'vgt_prop': 'vegetation_properties',
    'wb': 'water_bodies',
    'lc': 'dynamic_land_cover',
    'eta': 'evapotranspiration',
    'vppp': 'vegetation_phenology_and_productivity_parameters',
    'wl': 'river_and_lake_water_level',
}


def bbox_to_wkt(west: float, south: float, east: float, north: float) -> str:
    # For bboxes wider than 180°, add a midpoint on horizontal edges so that no
    # consecutive vertex pair has Δlon > 180°.  Without this, normalize_geometry
    # misidentifies the east→west edge as an antimeridian crossing and applies
    # orbital-footprint pole-routing, producing a degenerate geometry.
    if east - west > 180:
        mid = (west + east) / 2
        return Polygon([
            (west, north), (mid, north), (east, north),
            (east, south), (mid, south), (west, south),
            (west, north),
        ]).wkt
    return Polygon([
        (east, north), (east, south), (west, south), (west, north), (east, north)
    ]).wkt


EXTENTS = {
    'globe': bbox_to_wkt(-180.0, -90.0, 180.0, 90.0),
    'globe_80s80n': bbox_to_wkt(-180.0, -79.9776824, 179.9776872, 80.0223214),
    'globe_70s70n': bbox_to_wkt(-180.0, -70.0125000, 179.9875000, 70.0125000),
    'globe_60s80n_300m': bbox_to_wkt(-180.0, -59.9985119, 179.9985119, 80.0014881),
    'globe_60s80n_300m_b': bbox_to_wkt(-180.0, -59.998513, 179.9985148, 80.0014881),
    'globe_60s80n_1km': bbox_to_wkt(-180.0, -59.9955357, 179.9955357, 80.0044643),
    'globe_60s80n': bbox_to_wkt(-180.0, -60.0, 180.0, 80.0),
    'globe_65s85n': bbox_to_wkt(-180.0, -65.0, 180.0, 85.0),
    'globe_60s80n_500m': bbox_to_wkt(-180.0, -59.9975, 179.9975, 80.0025),
    'nhemi_35n85n': bbox_to_wkt(-180.0, 35.0, 180.0, 85.0),
    'nhemi_25n84n_500m': bbox_to_wkt(-180.0, 25.0025, 179.9975, 84.0025),
    'nhemi_25n84n': bbox_to_wkt(-180.0, 25.0, 180.0, 84.0),
    'eu_50n72n': bbox_to_wkt(-11.0, 35.0, 50.0, 72.0),
    'eu_35n72n': bbox_to_wkt(-11.00125, 35.00125, 49.99875, 72.00125),
    'baltic': bbox_to_wkt(4.99625, 44.99875, 45.00125, 71.00375),
}


class ProductConfig(NamedTuple):
    extent: str | None
    gsd: int | None
    product_type: str
    timeliness: str | None
    timeliness_category: str | None


PROD_MAP = {
    # Burnt Area
    'ba_global_300m_daily_v3': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['ba'], 'PT24H', 'NRT'),
    'ba_global_300m_daily_v4': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['ba'], 'PT24H', 'NRT'),
    'ba_global_300m_monthly_v3': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['ba'], 'P2M', 'OFFL'),
    'ba_global_300m_monthly_v4': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['ba'], 'P2M', 'OFFL'),

    # Dry Matter Productivity
    'dmp_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['dmp'], None, None),
    'dmp_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['dmp'], 'P5D', 'NRT'),
    'dmp_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['dmp'], 'P2D', 'NRT'),

    # Gross Dry Matter Productivity
    'gdmp_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['dmp'], None, None),
    'gdmp_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['dmp'], 'P5D', 'NRT'),
    'gdmp_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['dmp'], 'P2D', 'NRT'),

    # Lake Surface Water Temperature
    'lswt-nrt_global_1km_10daily_v1': ProductConfig(EXTENTS['globe'], 1000, TYPES['lswt'], 'P3D', 'NRT'),
    'lswt-offline_global_1km_10daily_v1': ProductConfig(EXTENTS['globe'], 1000, TYPES['lswt'], None, None),

    # Lake Water Quality
    'lwq-nrt_global_1km_10daily_v1': ProductConfig(EXTENTS['globe'], 1000, TYPES['lwq'], None, None),
    'lwq-reproc_global_1km_10daily_v1': ProductConfig(EXTENTS['globe'], 1000, TYPES['lwq'], None, None),
    'lwq-nrt_global_100m_10daily_v1': ProductConfig(EXTENTS['globe'], 100, TYPES['lwq'], 'P4D', 'NRT'),
    'lwq-nrt_global_100m_10daily_v2': ProductConfig(EXTENTS['globe'], 100, TYPES['lwq'], 'P4D', 'NRT'),
    'lwq-nrt_global_300m_10daily_v1': ProductConfig(EXTENTS['globe'], 300, TYPES['lwq'], 'P3D', 'NRT'),
    'lwq-nrt_global_300m_10daily_v2': ProductConfig(EXTENTS['globe'], 300, TYPES['lwq'], 'P3D', 'NRT'),
    'lwq-reproc_global_300m_10daily_v1': ProductConfig(EXTENTS['globe'], 300, TYPES['lwq'], None, None),

    # Land Surface Temperature
    'lst-daily-cycle_global_5km_10daily_v1': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst-daily-cycle_global_5km_10daily_v2': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst-daily-cycle_global_3km_10daily_v3': ProductConfig(EXTENTS['globe_70s70n'], 3000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst-tci_global_5km_10daily_v1': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst-tci_global_5km_10daily_v2': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst-tci_global_3km_10daily_v3': ProductConfig(EXTENTS['globe_80s80n'], 3000, TYPES['lst'], 'P2D', 'OFFL'),
    'lst_global_5km_hourly_v1': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'PT4H', 'NRT'),
    'lst_global_5km_hourly_v2': ProductConfig(EXTENTS['globe_80s80n'], 5000, TYPES['lst'], 'PT4H', 'NRT'),
    'lst_global_3km_hourly_v3': ProductConfig(EXTENTS['globe_80s80n'], 3000, TYPES['lst'], 'PT4H', 'NRT'),

    # Gross/Net Primary Production
    'gpp_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['gpp'], 'P5D', 'NRT'),
    'gpp_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['gpp'], 'P2D', 'NRT'),
    'npp_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['gpp'], 'P5D', 'NRT'),
    'npp_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['gpp'], 'P2D', 'NRT'),

    # Lake and River Ice Extent
    'lie_baltic_250m_daily_v1': ProductConfig(EXTENTS['baltic'], 250, TYPES['lie'], 'P2D', 'NRT'),
    'lie_europe_250m_daily_v2': ProductConfig(EXTENTS['eu_35n72n'], 250, TYPES['lie'], 'P2D', 'NRT'),
    'lie_global_500m_daily_v2': ProductConfig(EXTENTS['globe_60s80n_500m'], 500, TYPES['lie'], 'P1D', 'NRT'),
    'lie_northernhemisphere_500m_daily_v1': ProductConfig(EXTENTS['nhemi_25n84n_500m'], 500, TYPES['lie'], 'P1D', 'NRT'),

    # Snow Cover Extent
    'sce_global_1km_daily_v1': ProductConfig(EXTENTS['globe'], 1000, TYPES['sce'], 'P1D', 'NRT'),
    'sce_europe_500m_daily_v1': ProductConfig(EXTENTS['eu_50n72n'], 500, TYPES['sce'], 'P1D', 'NRT'),
    'sce_northernhemisphere_1km_daily_v1': ProductConfig(EXTENTS['nhemi_25n84n'], 1000, TYPES['sce'], 'P1D', 'NRT'),

    # Snow Water Equivalent
    'swe_northernhemisphere_5km_daily_v1': ProductConfig(EXTENTS['nhemi_35n85n'], 5000, TYPES['swe'], 'PT12H', 'NRT'),
    'swe_northernhemisphere_5km_daily_v2': ProductConfig(EXTENTS['nhemi_35n85n'], 5000, TYPES['swe'], 'PT12H', 'NRT'),

    # Soil Water Index
    'swi_europe_1km_daily_v1': ProductConfig(EXTENTS['eu_50n72n'], 1000, TYPES['swi'], 'P2D', 'OFFL'),
    'swi_europe_1km_daily_v2': ProductConfig(EXTENTS['eu_50n72n'], 1000, TYPES['swi'], 'P2D', 'OFFL'),
    'swi_global_12.5km_10daily_v3': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P3D', 'OFFL'),
    'swi_global_12.5km_10daily_v4': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P3D', 'OFFL'),
    'swi_global_12.5km_daily_v3': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P1D', 'OFFL'),
    'swi_global_12.5km_daily_v4': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P1D', 'OFFL'),
    'swi-timeseries_global_12.5km_daily_v3': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P6M', 'OFFL'),
    'swi-timeseries_global_12.5km_daily_v4': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], 'P6M', 'OFFL'),
    'swi-static_global_12.5km_daily_v3': ProductConfig(EXTENTS['globe'], 12500, TYPES['swi'], None, None),

    # Surface Soil Moisture
    'ssm_europe_1km_daily_v1': ProductConfig(EXTENTS['eu_50n72n'], 1000, TYPES['ssm'], 'P1D', 'OFFL'),

    # Top-of-Canopy Reflectances
    'toc_global_300m_daily_v2': ProductConfig(EXTENTS['globe_65s85n'], 300, TYPES['toc'], 'P1D', 'OFFL'),

    # Vegetation Indices (NDVI)
    'ndvi_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_ind'], None, None),
    'ndvi_global_1km_10daily_v3': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_ind'], None, None),
    'ndvi_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_ind'], 'P3D', 'NRT'),
    'ndvi_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_ind'], 'P3D', 'NRT'),
    'ndvi_global_300m_10daily_v3': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_ind'], 'P3D', 'NRT'),
    'ndvi-lts_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_ind'], None, None),
    'ndvi-lts_global_1km_10daily_v3': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_ind'], None, None),
    'ndvi-sts_global_1km_10daily_v3': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_ind'], None, None),

    # Vegetation Properties (FAPAR / FCOVER / LAI)
    'fapar_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_prop'], None, None),
    'fapar_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P5D', 'NRT'),
    'fapar_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P2D', 'NRT'),
    'fcover_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_prop'], None, None),
    'fcover_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P5D', 'NRT'),
    'fcover_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P2D', 'NRT'),
    'lai_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['vgt_prop'], None, None),
    'lai_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P5D', 'NRT'),
    'lai_global_300m_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['vgt_prop'], 'P2D', 'NRT'),

    # Water Bodies
    'wb_global_1km_10daily_v2': ProductConfig(EXTENTS['globe_60s80n_1km'], 1000, TYPES['wb'], None, None),
    'wb_global_100m_monthly_v1': ProductConfig(EXTENTS['globe_60s80n'], 100, TYPES['wb'], 'P1M', 'OFFL'),
    'wb_global_300m_monthly_v2': ProductConfig(EXTENTS['globe_60s80n'], 300, TYPES['wb'], 'P1M', 'OFFL'),
    'wb_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_60s80n_300m'], 300, TYPES['wb'], 'P3D', 'OFFL'),

    # Land Cover
    'lc_global_100m_yearly_v3': ProductConfig(EXTENTS['globe_60s80n'], 100, TYPES['lc'], None, None),
    'lcm_global_10m_yearly_v1': ProductConfig(None, 10, TYPES['lc'], None, None),
    'tcd_pantropical_10m_yearly_v1': ProductConfig(None, 10, TYPES['lc'], None, None),

    # Evapotranspiration
    'eta_global_300m_10daily_v1': ProductConfig(EXTENTS['globe_65s85n'], 300, TYPES['eta'], 'P2D', 'OFFL'),
    'hf_global_300m_daily_v1': ProductConfig(EXTENTS['globe_65s85n'], 300, TYPES['eta'], 'P1D', 'OFFL'),

    # Vegetation phenology and productivity parameters
    'lsp_global_300m_yearly_v1': ProductConfig(EXTENTS['globe_60s80n_300m_b'], 300, TYPES['vppp'], 'P1M', 'OFFL'),
    'lsp_global_300m_yearly_v2': ProductConfig(EXTENTS['globe_60s80n_300m_b'], 300, TYPES['vppp'], 'P1M', 'OFFL'),

    # River and lake water level
    'wl-lakes_global_vector_daily_v2': ProductConfig(None, None, TYPES['wl'], 'P4D', 'NRT'),
    'wl-rivers_global_vector_daily_v2': ProductConfig(None, None, TYPES['wl'], 'P3D', 'NRT'),
}


class PlatformPattern(NamedTuple):
    pattern: str
    platform: str | None
    constellation: str


PLATFORM_CONSTELLATION_MAP = [
    PlatformPattern(r'\b(?:sentinel[-\s]?3|s3)(?!\s*[ab]\b)', None, 'sentinel-3'),
    PlatformPattern(r'\b(?:sentinel[-\s]?3|s3)\s*a\b', 'sentinel-3a', 'sentinel-3'),
    PlatformPattern(r'\b(?:sentinel[-\s]?3|s3)\s*b\b', 'sentinel-3b', 'sentinel-3'),
    PlatformPattern(r'proba-v','proba-v', 'proba-1'),
    PlatformPattern(r'\b(?:sentinel[-\s]?2|s2)(?!\s*[ab]\b)', None, 'sentinel-2'),
    PlatformPattern(r'\b(?:sentinel[-\s]?2|s2)\s*a\b', 'sentinel-2a', 'sentinel-2'),
    PlatformPattern(r'\b(?:sentinel[-\s]?2|s2)\s*b\b', 'sentinel-2b', 'sentinel-2'),
    PlatformPattern(r'envisat','envisat', 'envisat'),
    PlatformPattern(r'terra','terra', 'a-train'),
    PlatformPattern(r'noaa-20','noaa-20', 'jpss'),
    PlatformPattern(r'suomi_npp','suomi npp', 'jpss'),
    PlatformPattern(r'\bMETOP (?:[ABC](?:\+[ABC])?)\b','metop', 'metop'),
    PlatformPattern(r'\b(?:sentinel[-\s]?1|s1)(?!\s*[ab]\b)|\bsentinel[-\s]?1\s*a\+b\b', None, 'sentinel-1'),
    PlatformPattern(r'\b(?:sentinel[-\s]?1|s1)\s*a(?![\w+])','sentinel-1a', 'sentinel-1'),
    PlatformPattern(r'\b(?:sentinel[-\s]?1|s1)\s*b(?![\w+])','sentinel-1b', 'sentinel-1'),
    PlatformPattern(r'spot[- ]?4','spot 4', 'spot'),
    PlatformPattern(r'spot[- ]?5','spot 5', 'spot')
]


# ---------------------------------------------------------------------------
# Thumbnail (WMS GetMap) configuration, keyed by product subtype.
#
# Reproduces the per-item "thumbnail" asset already published on the CDSE STAC
# (https://stac.dataspace.copernicus.eu/v1/collections/<collection>/items).
# Each thumbnail is a WMS GetMap request against the thumbnails.dataspace
# rendering service, pointing at one specific COG band rendered with the
# collection's SLD style from the copernicus-land/colourmaps-legends repo.
#
# Per subtype:
#   rule  - how to derive the rendered COG band filename from the item id:
#             ['d', [field, seg], [token], ext] insert dash-segment into field
#             ['u', idx, [tokens], ext]         insert underscore field(s)
#             ['same', None, [], ext]           band file == item id base
#             ['match', substr]                 pick the band asset whose
#                                               filename contains substr
#   sld   - colourmaps-legends path (under colourmaps/) or None (no SLD param)
#   tiled - True  -> proj:bbox computed per-item from proj:transform/proj:shape
#           False -> proj:bbox is the fixed grid extent below
#   bbox  - fixed EPSG:4326 raster extent for gridded products (None if tiled)
#   crs   - EPSG code for gridded/lcm/tcd (None for tiled native -> item proj:code)
#
# NetCDF items reuse their COG twin's band file (the _nc product folder is
# swapped for _cog). Subtypes with no COG twin (ndvi-sts, swi-timeseries, toc)
# are intentionally absent and therefore get no thumbnail, matching production.
# ---------------------------------------------------------------------------
THUMBNAIL_MAP: dict[str, dict] = {
    'ba_global_300m_daily_v3': {
        'rule': ['d', [2, 1], ['DOB'], 'tiff'],
        'sld': 'ba_global_300m_daily_v4/clms_global_ba-dob_300m_v4_daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'ba_global_300m_daily_v4': {
        'rule': ['d', [2, 1], ['BF'], 'tiff'],
        'sld': 'ba_global_300m_daily_v4/clms_global_ba-bf_300m_v4_daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'ba_global_300m_monthly_v3': {
        'rule': ['d', [2, 1], ['DOB'], 'tiff'],
        'sld': 'ba_global_300m_monthly_v4/clms_global_ba-dob_300m_v4_monthly.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'ba_global_300m_monthly_v4': {
        'rule': ['d', [2, 1], ['BF'], 'tiff'],
        'sld': 'ba_global_300m_monthly_v4/clms_global_ba-bf_300m_v4_monthly.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'dmp_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['DMP'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'dmp_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['DMP'], 'tiff'],
        'sld': 'dmp_global_300m_10daily_v2/clms_global_dmp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'dmp_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['DMP'], 'tiff'],
        'sld': 'dmp_global_300m_10daily_v2/clms_global_dmp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'eta_global_300m_10daily_v1': {
        'rule': ['u', 2, ['GFD'], 'tif'],
        'sld': 'eta_global_300m_10daily_v1/clms_global_eta-gfd_300m_v1_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473481,
            179.99851190505504,
            80.0014880952381,
        ],
        'crs': 'EPSG:4326',
    },
    'fapar_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': 'fapar_global_1km_10daily_v2/clms_global_fapar_1km_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'fapar_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': 'fapar_global_300m_10daily_v2/clms_global_fapar-nobs_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'fapar_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': 'fapar_global_300m_10daily_v2/clms_global_fapar-nobs_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'fcover_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'fcover_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': 'fcover_global_300m_10daily_v2/clms_global_fcover-nobs_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'fcover_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['NOBS'], 'tiff'],
        'sld': 'fcover_global_300m_10daily_v2/clms_global_fcover-nobs_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'gdmp_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['GDMP'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'gdmp_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['GDMP'], 'tiff'],
        'sld': 'gdmp_global_300m_10daily_v2/clms_global_gdmp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'gdmp_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['GDMP'], 'tiff'],
        'sld': 'gdmp_global_300m_10daily_v2/clms_global_gdmp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'gpp_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['GPP'], 'tiff'],
        'sld': 'gpp_global_300m_10daily_v2/clms_global_gpp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'gpp_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['GPP'], 'tiff'],
        'sld': 'gpp_global_300m_10daily_v2/clms_global_gpp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'hf_global_300m_daily_v1': {
        'rule': ['u', 2, ['H-TSEBPT'], 'tif'],
        'sld': 'hf_global_300m_daily_v1/clms_global_hf-h_300m_v1_daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.9985119047395,
            179.99851190501883,
            80.0014880952381,
        ],
        'crs': 'EPSG:4326',
    },
    'lai_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['LAI'], 'tiff'],
        'sld': 'lai_global_1km_10daily_v2/clms_global_lai_1km_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'lai_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['LAI'], 'tiff'],
        'sld': 'lai_global_300m_10daily_v1/clms_global_lai_300m_v1_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'lai_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['LAI'], 'tiff'],
        'sld': 'lai_global_300m_10daily_v2/clms_global_lai-lafter_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'lc_global_100m_yearly_v3': {
        'rule': ['match', 'Forest-Type-layer'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, -60.00000000000114, 180.0000000000029, 80.0],
        'crs': 'EPSG:4326',
    },
    'lcm_global_10m_yearly_v1': {
        'rule': ['u', 5, ['MAP'], 'tif'],
        'sld': None,
        'tiled': True,
        'bbox': None,
        'crs': None,
    },
    'lie_baltic_250m_daily_v1': {
        'rule': ['d', [2, 1], ['LIE'], 'tiff'],
        'sld': 'lie_baltic_250m_daily_v1/clms_baltic_lie_250m_v1_daily.sld',
        'tiled': False,
        'bbox': [4.99625, 44.99875, 45.00125, 71.00375],
        'crs': 'EPSG:4326',
    },
    'lie_europe_250m_daily_v2': {
        'rule': ['d', [2, 1], ['LIE'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-11.00125, 35.00125, 49.99875, 72.00125],
        'crs': 'EPSG:4326',
    },
    'lie_global_500m_daily_v2': {
        'rule': ['d', [2, 1], ['LIE'], 'tiff'],
        'sld': 'lie_global_500m_daily_v2/clms_global_lie_500m_lie_v2_daily.sld',
        'tiled': False,
        'bbox': [-180.0025, -59.9975, 179.9975, 80.0025],
        'crs': 'EPSG:4326',
    },
    'lie_northernhemisphere_500m_daily_v1': {
        'rule': ['d', [2, 2], ['P'], 'tiff'],
        'sld': 'lie_northernhemisphere_500m_daily_v1/clms_nhemi_lie_500m_lie_v1_daily.sld',
        'tiled': False,
        'bbox': [-180.0025, 25.002499999999998, 179.9975, 84.0025],
        'crs': 'EPSG:4326',
    },
    'lsp_global_300m_yearly_v1': {
        'rule': ['same', None, [], 'tiff'],
        'sld': 'lsp_global_300m_yearly_v2/clms_global_lsp-tprod-season1_300m_v2_yearly.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851302476188,
            179.99851478476185,
            80.0014880952381,
        ],
        'crs': 'EPSG:4326',
    },
    'lsp_global_300m_yearly_v2': {
        'rule': ['same', None, [], 'tiff'],
        'sld': 'lsp_global_300m_yearly_v2/clms_global_lsp-tprod-season1_300m_v2_yearly.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851302476188,
            179.99851478476185,
            80.0014880952381,
        ],
        'crs': 'EPSG:4326',
    },
    'lst-daily-cycle_global_5km_10daily_v1': {
        'rule': ['d', [2, 2], ['MAX'], 'tiff'],
        'sld': 'lst-daily-cycle_global_5km_10daily_v1/clms_global_lst_5km_v1_max_10daily-daily-cycle.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lst-daily-cycle_global_5km_10daily_v2': {
        'rule': ['d', [2, 2], ['MAX'], 'tiff'],
        'sld': 'lst-daily-cycle_global_5km_10daily_v2/clms_global_lst_5km_v2_max_10daily-daily-cycle.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lst-tci_global_5km_10daily_v1': {
        'rule': ['d', [2, 2], ['MAX'], 'tiff'],
        'sld': 'lst-tci_global_5km_10daily_v1/clms_global_lst_5km_v1_10daily-tci.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lst-tci_global_5km_10daily_v2': {
        'rule': ['d', [2, 2], ['MAX'], 'tiff'],
        'sld': 'lst-tci_global_5km_10daily_v2/clms_global_lst_5km_v2_10daily-tci.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lst_global_5km_hourly_v1': {
        'rule': ['d', [2, 1], ['LST'], 'tiff'],
        'sld': 'lst_global_5km_hourly_v1/clms_global_lst_5km_v1_hourly.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lst_global_5km_hourly_v2': {
        'rule': ['d', [2, 1], ['LST'], 'tiff'],
        'sld': 'lst_global_5km_hourly_v2/clms_global_lst_5km_v2_hourly.sld',
        'tiled': False,
        'bbox': [
            -180.0223214291036,
            -79.97768238559365,
            179.97768715396523,
            80.02232142910361,
        ],
        'crs': 'EPSG:4326',
    },
    'lswt-nrt_global_1km_10daily_v1': {
        'rule': ['d', [2, 1], ['UNC'], 'tiff'],
        'sld': 'lswt-nrt_global_1km_10daily_v1/clms_global_lswt_1km_v1_10daily-nrt-lake_surface_water_temperature.sld',
        'tiled': False,
        'bbox': [
            -180.00000101727616,
            -90.00000101729864,
            180.00000101727827,
            90.0000010172997,
        ],
        'crs': 'EPSG:4326',
    },
    'lswt-offline_global_1km_10daily_v1': {
        'rule': ['d', [2, 1], ['UNC'], 'tiff'],
        'sld': 'lswt-offline_global_1km_10daily_v1/clms_global_lswt_1km_v1_10daily-reproc-lake_surface_water_temperature.sld',
        'tiled': False,
        'bbox': [
            -180.00000101727616,
            -90.00000101729864,
            180.00000101727827,
            90.0000010172997,
        ],
        'crs': 'EPSG:4326',
    },
    'lwq-nrt_global_100m_10daily_v1': {
        'rule': ['d', [2, 1], ['TSI'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, -89.99999999999662, 179.99999999999324, 90.0],
        'crs': 'EPSG:4326',
    },
    'lwq-nrt_global_100m_10daily_v2': {
        'rule': ['d', [2, 1], ['TSI'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, -89.99999999999662, 179.99999999999324, 90.0],
        'crs': 'EPSG:4326',
    },
    'lwq-nrt_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['TSI'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.00000000000003, -90.00000000000344, 180.00000000000685, 90.0],
        'crs': 'EPSG:4326',
    },
    'lwq-nrt_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['TSI'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.00000000000003, -90.00000000000344, 180.00000000000685, 90.0],
        'crs': 'EPSG:4326',
    },
    'lwq-reproc_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['TSI'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.00000000000003, -90.00000000000344, 180.00000000000685, 90.0],
        'crs': 'EPSG:4326',
    },
    'ndvi-lts_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['MAX'], 'tiff'],
        'sld': 'ndvi-lts_global_1km_10daily_v3/clms_global_ndvi-lts-max_1km_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi-lts_global_1km_10daily_v3': {
        'rule': ['d', [2, 1], ['MAX'], 'tiff'],
        'sld': 'ndvi-lts_global_1km_10daily_v3/clms_global_ndvi-lts-max_1km_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['NDVI'], 'tiff'],
        'sld': 'ndvi_global_1km_10daily_v3/clms_global_ndvi-ndvi_1km_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi_global_1km_10daily_v3': {
        'rule': ['d', [2, 1], ['UNC'], 'tiff'],
        'sld': 'ndvi_global_1km_10daily_v3/clms_global_ndvi-unc_1km_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['NDVI'], 'tiff'],
        'sld': 'ndvi_global_300m_10daily_v3/clms_global_ndvi-ndvi_300m_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['UNC'], 'tiff'],
        'sld': 'ndvi_global_300m_10daily_v2/clms_global_ndvi-unc_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'ndvi_global_300m_10daily_v3': {
        'rule': ['d', [2, 1], ['UNC'], 'tiff'],
        'sld': 'ndvi_global_300m_10daily_v3/clms_global_ndvi-unc_300m_v3_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'npp_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['NPP'], 'tiff'],
        'sld': 'npp_global_300m_10daily_v2/clms_global_npp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'npp_global_300m_10daily_v2': {
        'rule': ['d', [2, 1], ['NPP'], 'tiff'],
        'sld': 'npp_global_300m_10daily_v2/clms_global_npp_300m_v2_10daily.sld',
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'sce_europe_500m_daily_v1': {
        'rule': ['same', None, [], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-11.0, 35.0, 50.0, 72.0],
        'crs': 'EPSG:4326',
    },
    'sce_global_1km_daily_v1': {
        'rule': ['d', [2, 1], ['SCE'], 'tiff'],
        'sld': 'sce_global_1km_daily_v1/clms_global_sce_1km_v1_daily.sld',
        'tiled': False,
        'bbox': [-180.0, -90.0, 180.0, 90.0],
        'crs': 'EPSG:4326',
    },
    'sce_northernhemisphere_1km_daily_v1': {
        'rule': ['same', None, [], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, 25.0, 180.0, 84.0],
        'crs': 'EPSG:4326',
    },
    'ssm_europe_1km_daily_v1': {
        'rule': ['d', [2, 1], ['SSM'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-11.0, 35.00000000000001, 49.999999999998444, 71.9999999999916],
        'crs': 'EPSG:4326',
    },
    'swe_northernhemisphere_5km_daily_v1': {
        'rule': ['d', [2, 1], ['SWE'], 'tiff'],
        'sld': 'swe_northernhemisphere_5km_daily_v2/clms_nhemi_swe_5km_daily_v2_1.sld',
        'tiled': False,
        'bbox': [-180.0, 35.0, 180.0, 85.0],
        'crs': 'EPSG:4326',
    },
    'swe_northernhemisphere_5km_daily_v2': {
        'rule': ['d', [2, 1], ['SWE'], 'tiff'],
        'sld': 'swe_northernhemisphere_5km_daily_v2/clms_nhemi_swe_5km_daily_v2_1.sld',
        'tiled': False,
        'bbox': [-180.0, 35.0, 180.0, 85.0],
        'crs': 'EPSG:4326',
    },
    'swi-static_global_12.5km_daily_v3': {
        'rule': ['same', None, [], 'tiff'],
        'sld': 'swi-static_global_12.5km_daily_v3/clms_global_swi_12.5km_static_ci_v3.sld',
        'tiled': False,
        'bbox': [
            -179.99999999999997,
            -90.00000000001023,
            180.00000000000003,
            89.99999999998977,
        ],
        'crs': 'EPSG:4326',
    },
    'swi_europe_1km_daily_v1': {
        'rule': ['d', [2, 1], ['SSF'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-11.0, 35.00000000000001, 49.999999999998444, 71.9999999999916],
        'crs': 'EPSG:4326',
    },
    'swi_europe_1km_daily_v2': {
        'rule': ['d', [2, 1], ['SSF'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-11.0, 35.00000000000839, 49.999999999998444, 71.99999999999999],
        'crs': 'EPSG:4326',
    },
    'swi_global_12.5km_10daily_v3': {
        'rule': ['d', [2, 1], ['SWI001'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -179.99999999999997,
            -90.00000000001023,
            180.00000000000003,
            89.99999999998977,
        ],
        'crs': 'EPSG:4326',
    },
    'swi_global_12.5km_10daily_v4': {
        'rule': ['d', [2, 1], ['SWI001'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -179.99999999999997,
            -90.00000000001023,
            180.00000000000003,
            89.99999999998977,
        ],
        'crs': 'EPSG:4326',
    },
    'swi_global_12.5km_daily_v3': {
        'rule': ['d', [2, 1], ['SSF'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -179.99999999999997,
            -90.00000000001023,
            180.00000000000003,
            89.99999999998977,
        ],
        'crs': 'EPSG:4326',
    },
    'swi_global_12.5km_daily_v4': {
        'rule': ['d', [2, 1], ['SSF'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-179.99999999999997, -90.0, 180.00000000000003, 90.0],
        'crs': 'EPSG:4326',
    },
    'tcd_pantropical_10m_yearly_v1': {
        'rule': ['u', 5, ['MAP'], 'tif'],
        'sld': None,
        'tiled': True,
        'bbox': None,
        'crs': None,
    },
    'wb_global_100m_monthly_v1': {
        'rule': ['d', [2, 1], ['WB'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, -59.9999999999944, 179.99999999998562, 80.0],
        'crs': 'EPSG:4326',
    },
    'wb_global_1km_10daily_v2': {
        'rule': ['d', [2, 1], ['WB'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -180.00446428571428,
            -59.995535714253904,
            179.9955357147765,
            80.00446428571429,
        ],
        'crs': 'EPSG:4326',
    },
    'wb_global_300m_10daily_v1': {
        'rule': ['d', [2, 1], ['WB'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [
            -180.0014880952381,
            -59.99851190473011,
            179.99851190639774,
            80.00148809523809,
        ],
        'crs': 'EPSG:4326',
    },
    'wb_global_300m_monthly_v2': {
        'rule': ['d', [2, 1], ['WB'], 'tiff'],
        'sld': None,
        'tiled': False,
        'bbox': [-180.0, -60.0, 180.0, 80.0],
        'crs': 'EPSG:4326',
    },
}
