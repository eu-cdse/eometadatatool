import argparse
import logging
import pathlib
from typing import NamedTuple

import orjson

from eometadatatool.stac.framework.stac_extension import StacExtension


class Classes(NamedTuple):
    data: list[dict]


class Bitfields(NamedTuple):
    data: list[dict]


## dry-gross_dry_matter_productivity | net-gross_primary_production
"""
dmp_global_1km_10daily_v2, gdmp_global_1km_10daily_v2,
dmp_global_300m_10daily_v1, gdmp_global_300m_10daily_v1,
npp_global_300m_10daily_v1, gpp_global_300m_10daily_v1,
dmp_global_300m_10daily_v2, gdmp_global_300m_10daily_v2,
npp_global_300m_10daily_v2, gpp_global_300m_10daily_v2
For data asset
"""
classes__dmp_gdmp_npp_gpp_data = [
    {'value': -1, 'name': 'missing', 'description': 'Missing value'},
    {'value': -2, 'name': 'sea', 'description': 'Specific value for sea'},
]
bitfields__dmp_gdmp_npp_gpp_common = [
    {
        'name': 'fapar_availability',
        'description': 'fAPAR missing or invalid',
        'offset': 0,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'available', 'description': 'Available fAPAR value'},
            {'value': 1, 'name': 'missing', 'description': 'Missing fAPAR value'},
        ],
    },
    {
        'name': 'meteo_availability',
        'description': 'Meteorological input missing or invalid',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'available',
                'description': 'Available meteorological value',
            },
            {
                'value': 1,
                'name': 'missing',
                'description': 'Missing meteorological value',
            },
        ],
    },
    {
        'name': 'evergreen_broadleaf_forest',
        'description': 'Evergreen Broadleaf Forest (EBF)',
        'offset': 3,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'no_ebf',
                'description': 'Not Evergreen Broadleaf Forest',
            },
            {'value': 1, 'name': 'ebf', 'description': 'Evergreen Broadleaf Forest'},
        ],
    },
]
"""
dmp_global_1km_10daily_v2, gdmp_global_1km_10daily_v2
For 'qflag' asset
"""
bitfields__dmp_gdmp_global_1km_10daily_v2_qflag = [
    bitfields__dmp_gdmp_npp_gpp_common[0],
    bitfields__dmp_gdmp_npp_gpp_common[1],
    {
        'name': 'high_latitude_correction',
        'description': 'fAPAR correction for high latitude (lat > 55°N, SZA > 70°)',
        'offset': 2,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'no_high_latitude',
                'description': 'No high latitude correction',
            },
            {
                'value': 1,
                'name': 'high_latitude',
                'description': 'High latitude correction applied',
            },
        ],
    },
    bitfields__dmp_gdmp_npp_gpp_common[2],
    {
        'name': 'bare_soil',
        'description': 'Bare Soil',
        'offset': 4,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'no_bare_soil', 'description': 'Not bare soil'},
            {'value': 1, 'name': 'bare_soil', 'description': 'Bare soil'},
        ],
    },
    {'name': 'not_used_bit6', 'description': 'Not used', 'offset': 5, 'length': 1},
    {
        'name': 'fapar_climatology',
        'description': 'fAPAR filled with climatology',
        'offset': 6,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_filled',
                'description': 'fAPAR not filled with climatology',
            },
            {
                'value': 1,
                'name': 'climatology_filled',
                'description': 'fAPAR filled with climatology',
            },
        ],
    },
    {
        'name': 'fapar_gap_filling',
        'description': 'fAPAR gap filling by interpolation',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_interpolated',
                'description': 'fAPAR not interpolated',
            },
            {'value': 1, 'name': 'interpolated', 'description': 'fAPAR interpolated'},
        ],
    },
]
"""
dmp_global_300m_10daily_v1, gdmp_global_300m_10daily_v1,
npp_global_300m_10daily_v1, gpp_global_300m_10daily_v1,
dmp_global_300m_10daily_v2, gdmp_global_300m_10daily_v2,
npp_global_300m_10daily_v2, gpp_global_300m_10daily_v2
For 'qflag' asset
"""
bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag = [
    bitfields__dmp_gdmp_npp_gpp_common[0],
    bitfields__dmp_gdmp_npp_gpp_common[1],
    {'name': 'not_used_bit3', 'description': 'Not used', 'offset': 2, 'length': 1},
    bitfields__dmp_gdmp_npp_gpp_common[2],
    {'name': 'not_used_bit5', 'description': 'Not used', 'offset': 4, 'length': 1},
    {
        'name': 'low_fapar_correction',
        'description': 'Low fAPAR correction applied (Not used in v1.0 products)',
        'offset': 5,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'unchanged', 'description': 'fAPAR is unchanged'},
            {
                'value': 1,
                'name': 'rescaled',
                'description': 'fAPAR < 0.15 and rescaled',
            },
        ],
    },
    {
        'name': 'fapar_ebf_computation',
        'description': 'fAPAR computation method for EBF',
        'offset': 6,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'daily_observations',
                'description': 'fAPAR from daily observations',
            },
            {
                'value': 1,
                'name': 'previous_dekad',
                'description': 'fAPAR filled from previous dekad',
            },
        ],
    },
    {
        'name': 'fapar_gap_filling',
        'description': 'fAPAR gap filling by interpolation',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_interpolated',
                'description': 'fAPAR not interpolated',
            },
            {'value': 1, 'name': 'interpolated', 'description': 'fAPAR interpolated'},
        ],
    },
]

## dynamic_land_cover
"""
lc_global_100m_yearly_v3
For 'change_confidence' asset
"""
classes__lc_global_100m_yearly_v3_change_confidence = [
    {
        'value': 0,
        'name': 'no_change',
        'description': 'No change in discrete class between current year and previous year detected.',
    },
    {
        'value': 1,
        'name': 'potential_change',
        'description': 'BFASTmon detected break in second half of NRT year - potential change.',
    },
    {
        'value': 2,
        'name': 'medium_confidence',
        'description': "Imprint of urban, permanent water, snow or wetland; OR change detected by BFAST but HMM model didn't confirm in higher resolution; OR change detected by BFASTmon in first half of NRT year.",
    },
    {
        'value': 3,
        'name': 'high_confidence',
        'description': 'BFAST detected a change and HMM confirmed this change in higher resolution.',
    },
]
"""
lc_global_100m_yearly_v3
For 'discrete_classification' asset
"""
classes__lc_global_100m_yearly_v3_discrete_classification = [
    {
        'value': 0,
        'name': 'no_data',
        'description': 'No input data available',
        'color_hint': '282828',
    },
    {
        'value': 20,
        'name': 'shrubs',
        'description': 'Woody perennial plants with persistent and woody stems, without any defined main stem, less than 5 m tall. Foliage can be evergreen or deciduous.',
        'color_hint': 'FFBB22',
    },
    {
        'value': 30,
        'name': 'herbaceous_vegetation',
        'description': 'Plants without persistent stem or shoots above ground and lacking definite firm structure. Tree and shrub cover is less than 10%.',
        'color_hint': 'FFFF4C',
    },
    {
        'value': 40,
        'name': 'cropland',
        'description': 'Cultivated and managed vegetation/agriculture. Lands covered with temporary crops followed by harvest and a bare soil period.',
        'color_hint': 'F096FF',
    },
    {
        'value': 50,
        'name': 'urban_built_up',
        'description': 'Land covered by buildings and other man-made structures.',
        'color_hint': 'FA0000',
    },
    {
        'value': 60,
        'name': 'bare_sparse_vegetation',
        'description': 'Lands with exposed soil, sand, or rocks and never has more than 10% vegetated cover during any time of the year.',
        'color_hint': 'B4B4B4',
    },
    {
        'value': 70,
        'name': 'snow_ice',
        'description': 'Lands under snow or ice cover throughout the year.',
        'color_hint': 'F0F0F0',
    },
    {
        'value': 80,
        'name': 'permanent_water_bodies',
        'description': 'Lakes, reservoirs, and rivers. Can be either fresh or salt-water bodies.',
        'color_hint': '0032C8',
    },
    {
        'value': 90,
        'name': 'herbaceous_wetland',
        'description': 'Lands with a permanent mixture of water and herbaceous or woody vegetation in salt, brackish, or fresh water.',
        'color_hint': '0096A0',
    },
    {
        'value': 100,
        'name': 'moss_lichen',
        'description': 'Moss and lichen.',
        'color_hint': 'FAE6A0',
    },
    {
        'value': 111,
        'name': 'closed_forest_evergreen_needle_leaf',
        'description': 'Closed forest (tree canopy >70%), almost all needle leaf trees remain green all year.',
        'color_hint': '58481F',
    },
    {
        'value': 112,
        'name': 'closed_forest_evergreen_broad_leaf',
        'description': 'Closed forest (tree canopy >70%), almost all broadleaf trees remain green year round.',
        'color_hint': '009900',
    },
    {
        'value': 113,
        'name': 'closed_forest_deciduous_needle_leaf',
        'description': 'Closed forest (tree canopy >70%), seasonal needle leaf tree communities with annual leaf-on and leaf-off periods.',
        'color_hint': '70663E',
    },
    {
        'value': 114,
        'name': 'closed_forest_deciduous_broad_leaf',
        'description': 'Closed forest (tree canopy >70%), seasonal broadleaf tree communities with annual leaf-on and leaf-off periods.',
        'color_hint': '00CC00',
    },
    {
        'value': 115,
        'name': 'closed_forest_mixed',
        'description': 'Closed forest, mix of forest types.',
        'color_hint': '4E751F',
    },
    {
        'value': 116,
        'name': 'closed_forest_unknown',
        'description': 'Closed forest, not matching any of the other definitions.',
        'color_hint': '007800',
    },
    {
        'value': 121,
        'name': 'open_forest_evergreen_needle_leaf',
        'description': 'Open forest (trees 15-70%, second layer mixed shrubs and grassland), almost all needle leaf trees remain green all year.',
        'color_hint': '666000',
    },
    {
        'value': 122,
        'name': 'open_forest_evergreen_broad_leaf',
        'description': 'Open forest (trees 15-70%, second layer mixed shrubs and grassland), almost all broadleaf trees remain green year round.',
        'color_hint': '8DB400',
    },
    {
        'value': 123,
        'name': 'open_forest_deciduous_needle_leaf',
        'description': 'Open forest (trees 15-70%, second layer mixed shrubs and grassland), seasonal needle leaf tree communities with annual leaf-on and leaf-off periods.',
        'color_hint': '8D7400',
    },
    {
        'value': 124,
        'name': 'open_forest_deciduous_broad_leaf',
        'description': 'Open forest (trees 15-70%, second layer mixed shrubs and grassland), seasonal broadleaf tree communities with annual leaf-on and leaf-off periods.',
        'color_hint': 'A0DC00',
    },
    {
        'value': 125,
        'name': 'open_forest_mixed',
        'description': 'Open forest, mix of forest types.',
        'color_hint': '929900',
    },
    {
        'value': 126,
        'name': 'open_forest_unknown',
        'description': 'Open forest, not matching any of the other definitions.',
        'color_hint': '648C00',
    },
    {
        'value': 200,
        'name': 'open_sea',
        'description': 'Oceans, seas. Can be either fresh or salt-water bodies.',
        'color_hint': '000080',
    },
]
"""
lc_global_100m_yearly_v3
For 'forest_type' asset
"""
classes__lc_global_100m_yearly_v3_forest_type = [
    {
        'value': 0,
        'name': 'unknown',
        'description': "Doesn't match any of the other forest types.",
    },
    {
        'value': 1,
        'name': 'evergreen_needle_leaf',
        'description': 'Evergreen needle leaf forest.',
    },
    {
        'value': 2,
        'name': 'evergreen_broad_leaf',
        'description': 'Evergreen broad leaf forest.',
    },
    {
        'value': 3,
        'name': 'deciduous_needle_leaf',
        'description': 'Deciduous needle leaf forest.',
    },
    {
        'value': 4,
        'name': 'deciduous_broad_leaf',
        'description': 'Deciduous broad leaf forest.',
    },
    {'value': 5, 'name': 'mixed', 'description': 'Mix of forest types.'},
]
"""
tcd_pantropical_10m_yearly_v1
For 'map' asset
"""
classes__tcd_pantropical_10m_yearly_v1_map = [
    {
        'value': 10,
        'name': 'tcd_0_10',
        'description': 'Tree Cover Density 0% – 10%',
        'color_hint': 'EDF8E9',
    },
    {
        'value': 20,
        'name': 'tcd_10_20',
        'description': 'Tree Cover Density 10% – 20%',
        'color_hint': 'C7E9C0',
    },
    {
        'value': 30,
        'name': 'tcd_20_30',
        'description': 'Tree Cover Density 20% – 30%',
        'color_hint': 'A1D99B',
    },
    {
        'value': 40,
        'name': 'tcd_30_40',
        'description': 'Tree Cover Density 30% – 40%',
        'color_hint': '74C476',
    },
    {
        'value': 50,
        'name': 'tcd_40_50',
        'description': 'Tree Cover Density 40% – 50%',
        'color_hint': '41AB5D',
    },
    {
        'value': 60,
        'name': 'tcd_50_60',
        'description': 'Tree Cover Density 50% – 60%',
        'color_hint': '238B45',
    },
    {
        'value': 70,
        'name': 'tcd_60_70',
        'description': 'Tree Cover Density 60% – 70%',
        'color_hint': '006D2C',
    },
    {
        'value': 80,
        'name': 'tcd_70_80',
        'description': 'Tree Cover Density 70% – 80%',
        'color_hint': '00561F',
    },
    {
        'value': 90,
        'name': 'tcd_80_90',
        'description': 'Tree Cover Density 80% – 90%',
        'color_hint': '003D15',
    },
    {
        'value': 100,
        'name': 'tcd_90_100',
        'description': 'Tree Cover Density 90% – 100%',
        'color_hint': '00250C',
    },
    {
        'value': 254,
        'name': 'unclassifiable',
        'description': 'Unclassifiable due to data gaps (e.g. persistent cloud cover)',
        'color_hint': 'AAAAAA',
    },
    {
        'value': 255,
        'name': 'no_data',
        'description': 'No Data – outside area of interest',
        'color_hint': '000000',
        'nodata': True,
    },
]
"""
lcm_global_10m_yearly_v1
For 'map' asset
"""
classes__lcm_global_10m_yearly_v1_map = [
    {
        'value': 10,
        'name': 'tree_cover',
        'description': 'Tree cover',
        'color_hint': '006400',
    },
    {
        'value': 20,
        'name': 'shrubland',
        'description': 'Shrubland',
        'color_hint': 'FFBB22',
    },
    {
        'value': 30,
        'name': 'grassland',
        'description': 'Grassland',
        'color_hint': 'FFFF4C',
    },
    {
        'value': 40,
        'name': 'cropland',
        'description': 'Cropland',
        'color_hint': 'F096FF',
    },
    {
        'value': 50,
        'name': 'herbaceous_wetland',
        'description': 'Herbaceous wetland',
        'color_hint': '009696',
    },
    {
        'value': 60,
        'name': 'mangroves',
        'description': 'Mangroves',
        'color_hint': '00CF75',
    },
    {
        'value': 70,
        'name': 'moss_lichen',
        'description': 'Moss and lichen',
        'color_hint': 'FAE6A0',
    },
    {
        'value': 80,
        'name': 'bare_sparse_vegetation',
        'description': 'Bare / sparse vegetation',
        'color_hint': 'B4B4B4',
    },
    {
        'value': 90,
        'name': 'built_up',
        'description': 'Built-up',
        'color_hint': 'FA0000',
    },
    {
        'value': 100,
        'name': 'permanent_water_bodies',
        'description': 'Permanent water bodies',
        'color_hint': '0064C8',
    },
    {
        'value': 110,
        'name': 'snow_ice',
        'description': 'Snow and ice',
        'color_hint': 'F0F0F0',
    },
    {
        'value': 254,
        'name': 'unclassifiable',
        'description': 'Unclassifiable due to data gaps (e.g. persistent cloud cover)',
        'color_hint': '0A0A0A',
    },
    {
        'value': 255,
        'name': 'no_data',
        'description': 'No Data – outside area of interest',
        'color_hint': '000000',
        'nodata': True,
    },
]

## evapotranspiration
"""
eta_global_300m_10daily_v1
For 'flag' asset
"""
bitfields__eta_global_300m_10daily_v1_flag = [
    {
        'name': 'no_et',
        'description': 'ET not modelled due to cloud cover, snow, or model non-convergence',
        'offset': 0,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'valid', 'description': 'ET modelled normally'},
            {
                'value': 1,
                'name': 'not_modelled',
                'description': 'ET not modelled - cloud, snow, or model non-convergence',
            },
        ],
    },
    {
        'name': 'inland_water',
        'description': 'Inland open-water pixel where ET is not modelled',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_water',
                'description': 'Not an inland open-water pixel',
            },
            {
                'value': 1,
                'name': 'water',
                'description': 'ET not modelled - inland open-water pixel',
            },
        ],
    },
    {
        'name': 'urban',
        'description': 'Urban pixel where ET is modelled but with very high uncertainty',
        'offset': 2,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'not_urban', 'description': 'Not an urban pixel'},
            {
                'value': 1,
                'name': 'urban',
                'description': 'ET modelled but with very high uncertainty - urban pixel',
            },
        ],
    },
    {
        'name': 'unused_bit3',
        'description': 'Currently unused',
        'offset': 3,
        'length': 1,
        'classes': [{'value': 0, 'name': 'unused', 'description': 'Currently unused'}],
    },
    {
        'name': 'unused_bit4',
        'description': 'Currently unused',
        'offset': 4,
        'length': 1,
        'classes': [{'value': 0, 'name': 'unused', 'description': 'Currently unused'}],
    },
    {
        'name': 'unused_bit5',
        'description': 'Currently unused',
        'offset': 5,
        'length': 1,
        'classes': [{'value': 0, 'name': 'unused', 'description': 'Currently unused'}],
    },
    {
        'name': 'unused_bit6',
        'description': 'Currently unused',
        'offset': 6,
        'length': 1,
        'classes': [{'value': 0, 'name': 'unused', 'description': 'Currently unused'}],
    },
    {
        'name': 'unused_bit7',
        'description': 'Currently unused',
        'offset': 7,
        'length': 1,
        'classes': [{'value': 0, 'name': 'unused', 'description': 'Currently unused'}],
    },
]

## Lake surface water temperature
"""
lswt-nrt_global_1km_10daily_v1, lswt-offline_global_1km_10daily_v1
For 'quality_level' asset
"""
classes__lswt_nrt_offline_global_1km_10daily_v1_quality_level = [
    {'value': 0, 'name': 'no_data', 'description': 'No data (fill value)'},
    {'value': 2, 'name': 'low', 'description': 'Low quality - use with care'},
    {'value': 3, 'name': 'medium', 'description': 'Medium quality - use with care'},
    {'value': 4, 'name': 'high', 'description': 'High quality - recommended'},
    {'value': 5, 'name': 'best', 'description': 'Best quality - highest confidence'},
]
"""
lswt-nrt_global_1km_10daily_v1, lswt-offline_global_1km_10daily_v1
For 'time_obs' asset
"""
bitfields__lswt_nrt_offline_global_1km_10daily_v1_time_obs = [
    {
        'offset': 0,
        'length': 1,
        'name': 'day_1_observation',
        'description': 'Observation on day 1 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 1'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 1 was used',
            },
        ],
    },
    {
        'offset': 1,
        'length': 1,
        'name': 'day_2_observation',
        'description': 'Observation on day 2 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 2'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 2 was used',
            },
        ],
    },
    {
        'offset': 2,
        'length': 1,
        'name': 'day_3_observation',
        'description': 'Observation on day 3 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 3'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 3 was used',
            },
        ],
    },
    {
        'offset': 3,
        'length': 1,
        'name': 'day_4_observation',
        'description': 'Observation on day 4 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 4'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 4 was used',
            },
        ],
    },
    {
        'offset': 4,
        'length': 1,
        'name': 'day_5_observation',
        'description': 'Observation on day 5 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 5'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 5 was used',
            },
        ],
    },
    {
        'offset': 5,
        'length': 1,
        'name': 'day_6_observation',
        'description': 'Observation on day 6 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 6'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 6 was used',
            },
        ],
    },
    {
        'offset': 6,
        'length': 1,
        'name': 'day_7_observation',
        'description': 'Observation on day 7 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 7'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 7 was used',
            },
        ],
    },
    {
        'offset': 7,
        'length': 1,
        'name': 'day_8_observation',
        'description': 'Observation on day 8 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 8'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 8 was used',
            },
        ],
    },
    {
        'offset': 8,
        'length': 1,
        'name': 'day_9_observation',
        'description': 'Observation on day 9 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 9'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 9 was used',
            },
        ],
    },
    {
        'offset': 9,
        'length': 1,
        'name': 'day_10_observation',
        'description': 'Observation on day 10 of the dekad was used',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 10'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 10 was used',
            },
        ],
    },
    {
        'offset': 10,
        'length': 1,
        'name': 'day_11_observation',
        'description': 'Observation on day 11 of the dekad was used (last dekad of month only)',
        'classes': [
            {'value': 0, 'name': 'not_used', 'description': 'No observation on day 11'},
            {
                'value': 1,
                'name': 'used',
                'description': 'Observation on day 11 was used',
            },
        ],
    },
    {
        'offset': 11,
        'length': 5,
        'name': 'unused',
        'description': 'Reserved/unused bits',
    },
]

## Lake water quality
"""
lwq-nrt_global_100m_10daily_v2
For 'qflag' asset
"""
bitfields__lwq_nrt_global_100m_10daily_v2_qflag = [
    {
        'name': 'L1_invalid',
        'offset': 0,
        'length': 1,
        'description': 'L1 input data missing or invalid',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'cloud',
        'offset': 1,
        'length': 1,
        'description': 'One or more observations removed due to cloud detection by IdePix',
        'classes': [{'value': 0, 'name': 'no_cloud'}, {'value': 1, 'name': 'cloud'}],
    },
    {
        'name': 'land',
        'offset': 2,
        'length': 1,
        'description': 'One or more observations removed as pixel contains land',
        'classes': [{'value': 0, 'name': 'no_land'}, {'value': 1, 'name': 'land'}],
    },
    {
        'name': 'snow_ice',
        'offset': 3,
        'length': 1,
        'description': 'One or more observations removed as flagged by IdePix as snow or ice',
        'classes': [
            {'value': 0, 'name': 'no_snow_ice'},
            {'value': 1, 'name': 'snow_ice'},
        ],
    },
    {
        'name': 'bright_pixels',
        'offset': 4,
        'length': 1,
        'description': 'One or more observations removed as anomalously bright (Rw412 > 0.4 or Rw865 > 0.4)',
        'classes': [{'value': 0, 'name': 'normal'}, {'value': 1, 'name': 'bright'}],
    },
    {
        'name': 'atmospheric_correction_failure',
        'offset': 5,
        'length': 1,
        'description': 'One or more observations removed as Polymer bio-optical model reached concentration limits',
        'classes': [
            {'value': 0, 'name': 'no_failure'},
            {'value': 1, 'name': 'failure'},
        ],
    },
    {
        'name': 'chla_invalid',
        'offset': 6,
        'length': 1,
        'description': 'One or more observations removed as chlorophyll-a value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'tsm_invalid',
        'offset': 7,
        'length': 1,
        'description': 'One or more observations removed as TSM value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'turbidity_invalid',
        'offset': 8,
        'length': 1,
        'description': 'One or more observations removed as turbidity value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'floating_cyanobacteria',
        'offset': 9,
        'length': 1,
        'description': 'Floating cyanobacteria likely in one or more observations',
        'classes': [
            {'value': 0, 'name': 'not_detected'},
            {'value': 1, 'name': 'detected'},
        ],
    },
    {
        'name': 'floating_macrophytes_or_mixed_pixel',
        'offset': 10,
        'length': 1,
        'description': 'One or more observations likely contained floating macrophytes or was a mixed pixel',
        'classes': [
            {'value': 0, 'name': 'not_detected'},
            {'value': 1, 'name': 'detected'},
        ],
    },
    {
        'name': 'unused',
        'offset': 11,
        'length': 5,
        'description': 'Reserved / unused bits',
        'classes': [{'value': 0, 'name': 'unused'}],
    },
]
"""
lwq-nrt_global_300m_10daily_v2
For 'qflag' asset
"""
bitfields__lwq_nrt_global_300m_10daily_v2_qflag = [
    {
        'name': 'l1_invalid',
        'offset': 0,
        'length': 1,
        'description': 'L1 input data missing or invalid',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'atmospheric_correction_failure',
        'offset': 1,
        'length': 1,
        'description': 'One or more observations removed as Polymer bio-optical model reached concentration limits',
        'classes': [
            {'value': 0, 'name': 'no_failure'},
            {'value': 1, 'name': 'failure'},
        ],
    },
    {
        'name': 'cloud',
        'offset': 2,
        'length': 1,
        'description': 'One or more observations removed due to cloud detection by IdePix',
        'classes': [{'value': 0, 'name': 'no_cloud'}, {'value': 1, 'name': 'cloud'}],
    },
    {
        'name': 'land',
        'offset': 3,
        'length': 1,
        'description': 'One or more observations removed as pixel contains land',
        'classes': [{'value': 0, 'name': 'no_land'}, {'value': 1, 'name': 'land'}],
    },
    {
        'name': 'land_contaminated',
        'offset': 4,
        'length': 1,
        'description': 'One or more observations likely contaminated by land adjacency effect',
        'classes': [
            {'value': 0, 'name': 'not_contaminated'},
            {'value': 1, 'name': 'contaminated'},
        ],
    },
    {
        'name': 'snow_ice',
        'offset': 5,
        'length': 1,
        'description': 'One or more observations removed as flagged by IdePix as snow or ice',
        'classes': [
            {'value': 0, 'name': 'no_snow_ice'},
            {'value': 1, 'name': 'snow_ice'},
        ],
    },
    {
        'name': 'bright_pixels',
        'offset': 6,
        'length': 1,
        'description': 'One or more observations removed as anomalously bright (Rw412 > 0.4 or Rw865 > 0.4)',
        'classes': [{'value': 0, 'name': 'normal'}, {'value': 1, 'name': 'bright'}],
    },
    {
        'name': 'turbidity_invalid',
        'offset': 7,
        'length': 1,
        'description': 'One or more observations removed as turbidity value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'chla_invalid',
        'offset': 8,
        'length': 1,
        'description': 'One or more observations removed as chlorophyll-a value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'tsm_invalid',
        'offset': 9,
        'length': 1,
        'description': 'One or more observations removed as TSM value unrealistic',
        'classes': [{'value': 0, 'name': 'valid'}, {'value': 1, 'name': 'invalid'}],
    },
    {
        'name': 'floating_cyanobacteria',
        'offset': 10,
        'length': 1,
        'description': 'Floating cyanobacteria likely in one or more observations',
        'classes': [
            {'value': 0, 'name': 'not_detected'},
            {'value': 1, 'name': 'detected'},
        ],
    },
    {
        'name': 'floating_macrophytes_or_mixed_pixel',
        'offset': 11,
        'length': 1,
        'description': 'One or more observations likely contained floating macrophytes or was a mixed pixel',
        'classes': [
            {'value': 0, 'name': 'not_detected'},
            {'value': 1, 'name': 'detected'},
        ],
    },
    {
        'name': 'unused',
        'offset': 12,
        'length': 4,
        'description': 'Reserved / unused bits',
        'classes': [{'value': 0, 'name': 'unused'}],
    },
]

## Land surface temperature
"""
lst_global_5km_hourly_v1
For 'qflag' asset
"""
bitfields__lst_global_5km_hourly_v1_qflag = [
    {
        'name': 'satellite_source',
        'offset': 0,
        'length': 2,
        'classes': [
            {'value': 0, 'name': 'goes', 'description': 'GOES'},
            {'value': 1, 'name': 'msg', 'description': 'MSG'},
            {
                'value': 2,
                'name': 'mtsat_or_himawari',
                'description': 'MTSAT or Himawari',
            },
            {
                'value': 3,
                'name': 'multi_mission',
                'description': 'Multi-mission (overlapping regions)',
            },
        ],
    },
    {
        'name': 'sea_cloud_mask',
        'offset': 2,
        'length': 3,
        'classes': [
            {'value': 0, 'name': 'sea', 'description': 'Sea pixel'},
            {
                'value': 1,
                'name': 'cloud_free',
                'description': 'Cloud free pixel (clear sky > 90%)',
            },
            {
                'value': 2,
                'name': 'cloud_contaminated',
                'description': 'Pixel contaminated by clouds (90% > clear sky > 10%)',
            },
            {
                'value': 3,
                'name': 'cloud_filled',
                'description': 'Pixel filled by clouds (clear sky < 10%)',
            },
            {'value': 4, 'name': 'unprocessed', 'description': 'Unprocessed pixel'},
            {'value': 5, 'name': 'reserved_5'},
            {'value': 6, 'name': 'reserved_6'},
            {'value': 7, 'name': 'reserved_7'},
        ],
    },
    {
        'name': 'missing_value',
        'offset': 5,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'valid', 'description': 'Valid pixel'},
            {'value': 1, 'name': 'out_of_disk', 'description': 'Pixel out of Disk'},
        ],
    },
]
"""
lst_global_5km_hourly_v2
For 'qflag' asset
"""
bitfields__lst_global_5km_hourly_v2_qflag = [
    {
        'name': 'satellite_source',
        'offset': 0,
        'length': 3,
        'classes': [
            {
                'value': 0,
                'name': 'multi_mission',
                'description': 'Multi-mission (overlapping regions)',
            },
            {'value': 1, 'name': 'goes', 'description': 'GOES'},
            {'value': 2, 'name': 'msg_0deg', 'description': 'MSG (0° service)'},
            {'value': 3, 'name': 'msg_iodc', 'description': 'MSG IODC service'},
            {
                'value': 4,
                'name': 'mtsat_or_himawari',
                'description': 'MTSAT or Himawari',
            },
            {'value': 5, 'name': 'reserved_5'},
            {'value': 6, 'name': 'reserved_6'},
            {'value': 7, 'name': 'reserved_7'},
        ],
    },
    {
        'name': 'sea_cloud_mask',
        'offset': 3,
        'length': 3,
        'classes': [
            {'value': 0, 'name': 'sea', 'description': 'Sea pixel'},
            {
                'value': 1,
                'name': 'cloud_free',
                'description': 'Cloud free pixel (clear sky > 90%)',
            },
            {
                'value': 2,
                'name': 'cloud_contaminated',
                'description': 'Pixel contaminated by clouds (90% > clear sky > 10%)',
            },
            {
                'value': 3,
                'name': 'cloud_filled',
                'description': 'Pixel filled by clouds (clear sky < 10%)',
            },
            {'value': 4, 'name': 'unprocessed', 'description': 'Unprocessed pixel'},
            {'value': 5, 'name': 'reserved_5'},
            {'value': 6, 'name': 'reserved_6'},
            {'value': 7, 'name': 'reserved_7'},
        ],
    },
    {
        'name': 'missing_value',
        'offset': 6,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'valid', 'description': 'Valid pixel'},
            {'value': 1, 'name': 'out_of_disk', 'description': 'Pixel out of Disk'},
        ],
    },
]
"""
lst_global_3km_hourly_v3
For 'qflag' asset
"""
classes__lst_global_3km_hourly_v3_qflag = [
    {
        'value': 0,
        'name': 'unprocessed',
        'description': 'No data or pixel out of disk',
        'nodata': True,
    },
    {
        'value': 5,
        'name': 'sea',
        'description': 'Sea pixel',
    },
    {
        'value': 10,
        'name': 'msg',
        'description': 'MSG (0° service) – processed pixel, clear sky',
    },
    {
        'value': 15,
        'name': 'msg_unprocessed',
        'description': 'MSG (0° service) – unprocessed pixel, cloud conditions',
    },
    {
        'value': 20,
        'name': 'iodc',
        'description': 'MSG IODC service – processed pixel, clear sky',
    },
    {
        'value': 25,
        'name': 'iodc_unprocessed',
        'description': 'MSG IODC service – unprocessed pixel, cloud conditions',
    },
    {
        'value': 30,
        'name': 'hmwr',
        'description': 'Himawari – processed pixel, clear sky',
    },
    {
        'value': 35,
        'name': 'hmwr_unprocessed',
        'description': 'Himawari – unprocessed pixel, cloud conditions',
    },
    {
        'value': 40,
        'name': 'goes',
        'description': 'GOES – processed pixel, clear sky',
    },
    {
        'value': 45,
        'name': 'goes_unprocessed',
        'description': 'GOES – unprocessed pixel, cloud conditions',
    },
    {
        'value': 50,
        'name': 'multi',
        'description': 'Multi-mission (overlapping regions) – processed pixel, clear sky',
    },
    {
        'value': 55,
        'name': 'multi_unprocessed',
        'description': 'Multi-mission (overlapping regions) – unprocessed pixel, cloud conditions',
    },
]

## river_and_lake_ice_extent
"""
lie_baltic_250m_daily_v1, lie_europe_250m_daily_v2
For 'lie' asset
"""
classes__lie_baltic_europe_250m_daily_v1_v2_lie = [
    {
        'value': 0,
        'name': 'missing',
        'description': 'No satellite image data available',
        'color_hint': '000000',
        'nodata': True,
    },
    {
        'value': 1,
        'name': 'snow_covered_ice',
        'description': 'Fully snow covered ice',
        'color_hint': 'FFFFFF',
    },
    {
        'value': 2,
        'name': 'partial_snow_ice',
        'description': 'Partially snow covered or snow free ice',
        'color_hint': 'ADD8E6',
    },
    {
        'value': 3,
        'name': 'open_water',
        'description': 'Open water',
        'color_hint': '0000FF',
    },
    {
        'value': 4,
        'name': 'sea',
        'description': 'Sea area (masked out)',
        'color_hint': '1A1A6E',
    },
    {
        'value': 5,
        'name': 'cloud',
        'description': 'Cloud covered area',
        'color_hint': 'C8C8C8',
    },
    {
        'value': 6,
        'name': 'land',
        'description': 'Land area (masked out)',
        'color_hint': '8B6914',
    },
]
"""
lie_global_500m_daily_v2
For 'lie' asset
"""
classes__lie_global_500m_daily_v2_lie = [
    {
        'value': 0,
        'name': 'missing',
        'description': 'No satellite image data available',
        'color_hint': '000000',
        'nodata': True,
    },
    {
        'value': 10,
        'name': 'snow_covered_ice',
        'description': 'Fully snow-covered ice',
        'color_hint': 'FFFFFF',
    },
    {
        'value': 20,
        'name': 'ice',
        'description': 'Partially snow-covered or snow-free ice',
        'color_hint': 'ADD8E6',
    },
    {
        'value': 30,
        'name': 'open_water',
        'description': 'Open water',
        'color_hint': '0000FF',
    },
    {
        'value': 40,
        'name': 'cloud',
        'description': 'Cloud-covered pixel',
        'color_hint': 'C8C8C8',
    },
    {
        'value': 50,
        'name': 'not_interpreted',
        'description': 'No satellite image data available (uninterpreted area)',
        'color_hint': '404040',
    },
    {
        'value': 60,
        'name': 'sea',
        'description': 'Sea area (masked out)',
        'color_hint': '1A1A6E',
    },
    {
        'value': 70,
        'name': 'land',
        'description': 'Land area (masked out)',
        'color_hint': '8B6914',
    },
]
"""
lie_northernhemisphere_500m_daily_v1
For 'lie' asset
"""
classes__lie_northernhemisphere_500m_daily_v1_lie = [
    {
        'value': 0,
        'name': 'missing',
        'description': 'No satellite image data available',
        'color_hint': '000000',
        'nodata': True,
    },
    {
        'value': 1,
        'name': 'ice',
        'description': 'Ice (all types, including snow-covered ice)',
        'color_hint': 'ADD8E6',
    },
    {
        'value': 2,
        'name': 'open_water',
        'description': 'Open water',
        'color_hint': '0000FF',
    },
    {
        'value': 3,
        'name': 'cloud',
        'description': 'Cloud-covered pixel',
        'color_hint': 'C8C8C8',
    },
    {
        'value': 4,
        'name': 'sea',
        'description': 'Sea area (masked out)',
        'color_hint': '1A1A6E',
    },
    {
        'value': 5,
        'name': 'land',
        'description': 'Land area (masked out)',
        'color_hint': '8B6914',
    },
]

## snow_cover_extent
"""
sce_europe_500m_daily_v1
For 'sce500' asset
"""
classes__sce_europe_500m_daily_v1_sce500 = [
    {
        'value': 0,
        'name': 'outside_area_of_interest',
        'description': 'Outside Continental Europe',
    },
    {'value': 20, 'name': 'sea', 'description': 'Sea mask'},
    {'value': 21, 'name': 'lake', 'description': 'Lake mask'},
    {'value': 22, 'name': 'river', 'description': 'River mask'},
    {
        'value': 30,
        'name': 'cloud',
        'description': 'Cloud mask (MODIS cloud product / Single Cloud Detection Approach 2.0)',
    },
    {
        'value': 251,
        'name': 'polar_night',
        'description': 'Polar night — solar zenith angle > 80°',
    },
    {'value': 254, 'name': 'input_data_error', 'description': 'Input data error'},
    {
        'value': 255,
        'name': 'no_data',
        'description': 'No data within Continental Europe extent',
    },
]
"""
sce_global_1km_daily_v1
For 'sce' asset
"""
classes__sce_global_1km_daily_v1_sce = [
    {
        'value': 0,
        'name': 'outside_area_of_interest',
        'description': 'Outside Area of Interest',
    },
    {
        'value': 20,
        'name': 'water',
        'description': 'Water mask (ESA CCI Land Cover 2000)',
    },
    {'value': 23, 'name': 'salt_lake', 'description': 'Salt lake mask'},
    {
        'value': 30,
        'name': 'cloud',
        'description': 'Cloud (Simple Cloud Detection Algorithm v2.3)',
    },
    {
        'value': 70,
        'name': 'antarctica',
        'description': 'Antarctica mask (ESA CCI Land Cover 2000)',
    },
    {
        'value': 251,
        'name': 'polar_night',
        'description': 'Polar night — solar zenith angle > 83°',
    },
    {'value': 254, 'name': 'input_data_error', 'description': 'Input data error'},
    {'value': 255, 'name': 'no_data', 'description': 'No data / fill value'},
]
"""
sce_global_1km_daily_v1
For 'sce_unc' asset
"""
classes__sce_global_1km_daily_v2_unc = [
    {
        'value': 0,
        'name': 'outside_area_of_interest',
        'description': 'Outside Area of Interest',
    },
    {'value': 20, 'name': 'water', 'description': 'Water mask'},
    {'value': 23, 'name': 'salt_lake', 'description': 'Salt lake mask'},
    {'value': 30, 'name': 'cloud', 'description': 'Cloud mask'},
    {'value': 70, 'name': 'antarctica', 'description': 'Antarctica mask'},
    {
        'value': 251,
        'name': 'polar_night',
        'description': 'Polar night — solar zenith angle > 83°',
    },
    {'value': 254, 'name': 'input_data_error', 'description': 'Input data error'},
    {'value': 255, 'name': 'no_data', 'description': 'No data / fill value'},
]
"""
sce_northernhemisphere_1km_daily_v1
For 'sce' asset
"""
classes__sce_northernhemisphere_1km_daily_v1_sce = [
    {
        'value': 0,
        'name': 'outside_area_of_interest',
        'description': 'Outside Northern Hemisphere extent',
    },
    {
        'value': 20,
        'name': 'water',
        'description': 'Water mask (ESA CCI Land Cover 2015, all water types)',
    },
    {
        'value': 30,
        'name': 'cloud',
        'description': 'Cloud mask (Single Cloud Detection Approach 2.0)',
    },
    {
        'value': 251,
        'name': 'polar_night',
        'description': 'Polar night — solar zenith angle > 80°',
    },
    {'value': 254, 'name': 'input_data_error', 'description': 'Input data error'},
    {
        'value': 255,
        'name': 'no_data',
        'description': 'No data within Northern Hemisphere extent',
    },
]

## soil_water_index
"""
swi_europe_1km_daily_v1, swi_europe_1km_daily_v2
For 'swi' and 'qflag' assets
"""
classes__swi_europe_1km_daily_v1_swi_qflag = [
    {
        'value': 241,
        'name': 'exceeding_min',
        'description': "Exceeding local pixel's dry extreme",
    },
    {
        'value': 242,
        'name': 'exceeding_max',
        'description': "Exceeding local pixel's wet extreme",
    },
    {'value': 251, 'name': 'water_mask', 'description': 'Masked water surface'},
    {
        'value': 252,
        'name': 'sensitivity_mask',
        'description': 'Masked for low sensitivity (S40)',
    },
    {
        'value': 253,
        'name': 'slope_mask',
        'description': 'Masked for extreme slope (topography)',
    },
    {
        'value': 254,
        'name': 'low_qflag',
        'description': 'QFLAG value is low, indicating SWI value is less reliable',
    },
]
"""
swi_europe_1km_daily_v1, swi_europe_1km_daily_v2
For 'ssf' asset
"""
bitfields__swi_europe_1km_daily_v1_ssf = [
    {'value': 0, 'name': 'nominal', 'description': 'Unfrozen soil, nominal conditions'},
    {'value': 1, 'name': 'frozen', 'description': 'Frozen soil'},
    {'value': 2, 'name': 'thawing', 'description': 'Thawing soil'},
    {'value': 3, 'name': 'frozen_snow', 'description': 'Frozen soil with snow cover'},
    {'value': 4, 'name': 'wet_snow', 'description': 'Wet snow'},
]
"""
swi_global_12.5km_10daily_v3, swi_global_12.5km_10daily_v4,
swi_global_12.5km_daily_v3, swi_global_12.5km_daily_v4,
swi-timeseries_global_12.5km_daily_v3, swi-timeseries_global_12.5km_daily_v4
For 'ssf' asset
"""
bitfields__swi_global_12_5km_daily_10daily_timeseries_v3_v4_ssf = [
    {
        'value': 0,
        'name': 'unknown',
        'description': 'No meteorological forecast available for that day; surface state could not be determined',
    },
    {
        'value': 1,
        'name': 'unfrozen',
        'description': 'Surface is unfrozen based on ECMWF skin temperature and snow depth forecasts',
    },
    {
        'value': 2,
        'name': 'frozen',
        'description': 'Majority of 12 two-hourly ECMWF forecast masks indicate skin temperature < 0°C or snow depth > 0 m',
    },
    {
        'value': 3,
        'name': 'temporary_water',
        'description': 'Temporary water on the surface (deprecated in V4; retained for format backwards compatibility only)',
    },
]

## surface_soil_moisture
"""
ssm_europe_1km_daily_v1
For 'ssm' asset
"""
classes__ssm_europe_1km_daily_v1 = [
    {
        'value': 241,
        'name': 'exceeding_min',
        'description': "Exceeding local pixel's dry extreme",
    },
    {
        'value': 242,
        'name': 'exceeding_max',
        'description': "Exceeding local pixel's wet extreme",
    },
    {'value': 251, 'name': 'water_mask', 'description': 'Masked water surface'},
    {
        'value': 252,
        'name': 'sensitivity_mask',
        'description': 'Masked for low sensitivity S40',
    },
    {
        'value': 253,
        'name': 'slope_mask',
        'description': 'Masked for extreme slope (topography)',
    },
    {'value': 255, 'name': 'nodata', 'description': 'No data (SSM not retrieved)'},
]

## vegetation_indices
"""
ndvi_global_1km_10daily_v2, ndvi_global_1km_10daily_v3
For 'ndvi' asset
"""
classes__ndvi_global_1km_10daily_v3_ndvi = [
    {'value': 251, 'name': 'missing', 'description': 'Missing / bad radiometry'},
    {'value': 252, 'name': 'cloud', 'description': 'Cloud or shadow'},
    {'value': 253, 'name': 'snow', 'description': 'Snow or ice'},
    {'value': 254, 'name': 'sea', 'description': 'Sea pixel'},
    {
        'value': 255,
        'name': 'background',
        'description': 'Background / missing input data',
    },
]
"""
ndvi_global_1km_10daily_v2, ndvi_global_1km_10daily_v3
For 'qflag' asset
"""
classes__ndvi_global_1km_10daily_v3_qflag = [
    {
        'value': 0,
        'name': 'no_clear_obs',
        'description': 'BRDF inversion not executed, no clear observations available during 16-day accumulation period (NOBS=0)',
    },
    {
        'value': 1,
        'name': 'inversion_failed',
        'description': 'BRDF inversion failed in one or both spectral bands',
    },
    {
        'value': 3,
        'name': 'brdf_ok',
        'description': 'BRDF OK, successful inversion in both bands (best quality)',
    },
    {
        'value': 8,
        'name': 'brdf_ok_warning',
        'description': 'BRDF OK with warning: inversion successful but with suspiciously low normalized RED reflectance',
    },
    {
        'value': 16,
        'name': 'sea',
        'description': 'BRDF inversion not executed, sea pixel',
    },
]
"""
ndvi_global_300m_10daily_v3
For 'ndvi' asset
"""
classes__ndvi_global_300m_10daily_v3_ndvi = [
    {
        'value': 252,
        'name': 'unknown',
        'description': 'NOBS=0 and BRDF priors are interpolated (pixels >55°N)',
    },
    {'value': 253, 'name': 'snow', 'description': 'NOBS>0 and NOBS_SNOW >= 1/2 NOBS'},
    {'value': 254, 'name': 'water'},
    {
        'value': 255,
        'name': 'missing',
        'description': 'TOC-r out of range or no TOC-r available for at least one red/NIR band',
    },
]
"""
ndvi_global_300m_10daily_v3
For 'qflag' asset
"""
bitfields__ndvi_global_300m_10daily_v3_qflag = [
    {
        'name': 'no_observations',
        'offset': 0,
        'length': 1,
        'description': 'No observations found in the compositing window in at least one of the red or NIR bands',
        'classes': [
            {'value': 0, 'name': 'observations_available'},
            {'value': 1, 'name': 'no_observations'},
        ],
    },
    {
        'name': 'snow_observation',
        'offset': 1,
        'length': 1,
        'description': 'At least one observation in the compositing window is flagged as snow',
        'classes': [
            {'value': 0, 'name': 'no_snow'},
            {'value': 1, 'name': 'snow_detected'},
        ],
    },
    {
        'name': 'red_quality_warning',
        'offset': 2,
        'length': 1,
        'description': 'At least one TOC-r input band for red has quality warning',
        'classes': [
            {'value': 0, 'name': 'no_warning'},
            {'value': 1, 'name': 'warning'},
        ],
    },
    {
        'name': 'red_quality_extreme_warning',
        'offset': 3,
        'length': 1,
        'description': 'At least one TOC-r input band for red has quality extreme warning',
        'classes': [
            {'value': 0, 'name': 'no_extreme_warning'},
            {'value': 1, 'name': 'extreme_warning'},
        ],
    },
    {
        'name': 'nir_quality_warning',
        'offset': 4,
        'length': 1,
        'description': 'At least one TOC-r input band for NIR has quality warning',
        'classes': [
            {'value': 0, 'name': 'no_warning'},
            {'value': 1, 'name': 'warning'},
        ],
    },
    {
        'name': 'nir_quality_extreme_warning',
        'offset': 5,
        'length': 1,
        'description': 'At least one TOC-r input band for NIR has quality extreme warning',
        'classes': [
            {'value': 0, 'name': 'no_extreme_warning'},
            {'value': 1, 'name': 'extreme_warning'},
        ],
    },
    {
        'name': 'toc_r_out_of_range',
        'offset': 6,
        'length': 1,
        'description': 'TOC-r out of range (TOC-r < 0 or TOC-r > 1) for at least one band',
        'classes': [
            {'value': 0, 'name': 'in_range'},
            {'value': 1, 'name': 'out_of_range'},
        ],
    },
    {
        'name': 'brdf_priors_gap_filled',
        'offset': 7,
        'length': 1,
        'description': 'The BRDF MCD43P priors are gap filled by linear interpolation',
        'classes': [
            {'value': 0, 'name': 'not_gap_filled'},
            {'value': 1, 'name': 'gap_filled'},
        ],
    },
]
"""
ndvi_global_300m_10daily_v2
For 'ndvi' asset
"""
classes__ndvi_global_300m_10daily_v2_ndvi = [
    {'value': 254, 'name': 'sea', 'description': 'Water (QFLAG = 128)'},
    {
        'value': 255,
        'name': 'missing',
        'description': 'No TOC-r available (QFLAG = 2) or TOC-r out of range (QFLAG = 64)',
    },
]
"""
ndvi_global_300m_10daily_v2
For 'qflag' asset
"""
bitfields__ndvi_global_300m_10daily_v2_qflag = [
    {
        'name': 'no_observations',
        'offset': 0,
        'length': 1,
        'description': 'No observations found in the compositing window in at least one of the RED or NIR bands',
        'classes': [
            {'value': 0, 'name': 'observations_available'},
            {'value': 1, 'name': 'no_observations'},
        ],
    },
    {
        'name': 'no_toc_r',
        'offset': 1,
        'length': 1,
        'description': 'No TOC-r in at least one of the RED or NIR bands',
        'classes': [
            {'value': 0, 'name': 'toc_r_available'},
            {'value': 1, 'name': 'toc_r_missing'},
        ],
    },
    {
        'name': 'red_quality_warning',
        'offset': 2,
        'length': 1,
        'description': 'At least one TOC-r input band for RED has quality warning',
        'classes': [
            {'value': 0, 'name': 'no_warning'},
            {'value': 1, 'name': 'warning'},
        ],
    },
    {
        'name': 'red_quality_extreme_warning',
        'offset': 3,
        'length': 1,
        'description': 'At least one TOC-r input band for RED has quality extreme warning',
        'classes': [
            {'value': 0, 'name': 'no_extreme_warning'},
            {'value': 1, 'name': 'extreme_warning'},
        ],
    },
    {
        'name': 'nir_quality_warning',
        'offset': 4,
        'length': 1,
        'description': 'At least one TOC-r input band for NIR has quality warning',
        'classes': [
            {'value': 0, 'name': 'no_warning'},
            {'value': 1, 'name': 'warning'},
        ],
    },
    {
        'name': 'nir_quality_extreme_warning',
        'offset': 5,
        'length': 1,
        'description': 'At least one TOC-r input band for NIR has quality extreme warning',
        'classes': [
            {'value': 0, 'name': 'no_extreme_warning'},
            {'value': 1, 'name': 'extreme_warning'},
        ],
    },
    {
        'name': 'toc_r_out_of_range',
        'offset': 6,
        'length': 1,
        'description': 'TOC-r out of range (TOC-r < 0 or TOC-r > 1) for at least one band',
        'classes': [
            {'value': 0, 'name': 'in_range'},
            {'value': 1, 'name': 'out_of_range'},
        ],
    },
    {
        'name': 'sea',
        'offset': 7,
        'length': 1,
        'description': 'Pixel is sea according to OLCI land-sea mask',
        'classes': [{'value': 0, 'name': 'land'}, {'value': 1, 'name': 'sea'}],
    },
]
"""
ndvi_global_300m_10daily_v1
For 'ndvi' asset
"""
classes__ndvi_global_300m_10daily_v1_ndvi = [
    {'value': 251, 'name': 'missing', 'description': 'Bad radiometric quality'},
    {'value': 252, 'name': 'cloud', 'description': 'Cloud or shadow'},
    {'value': 253, 'name': 'snow', 'description': 'Snow or ice'},
    {'value': 254, 'name': 'sea', 'description': 'Water (land mask = 0)'},
    {
        'value': 255,
        'name': 'background',
        'description': 'No data available (Status Map = 0)',
    },
]
"""
ndvi-lts_global_1km_10daily_v2, ndvi-lts_global_1km_10daily_v3,
ndvi-sts_global_1km_10daily_v3
For 'min', 'median', 'max', 'mean' and 'stdev' assets
"""
classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev = [
    {'value': 254, 'name': 'sea', 'description': 'Pixel masked as sea'},
    {
        'value': 255,
        'name': 'no_data',
        'description': 'Too few observations to compute statistics',
    },
]

## vegetation_phenology_and_productivity_parameters
"""
lsp_global_300m_yearly_v1, lsp_global_300m_yearly_v2
For 'QA' item
"""
bitfields__lsp_global_300m_yearly_v1_v2_qflag = [
    {
        'name': 'sos_quality',
        'description': 'Start of season (green-up) phenology quality',
        'offset': 0,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'best',
                'description': 'More than 2 valid observations and average best PPI quality',
            },
            {
                'value': 1,
                'name': 'good',
                'description': 'More than 2 valid observations and average good PPI quality',
            },
            {
                'value': 2,
                'name': 'fair',
                'description': 'More than 2 valid observations and average fair PPI quality',
            },
            {
                'value': 3,
                'name': 'poor',
                'description': 'Average poor PPI data quality, or fewer than 3 observations, or more than 24 observations',
            },
        ],
    },
    {
        'name': 'peak_quality',
        'description': 'Peak (green peak) phenology quality',
        'offset': 2,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'best',
                'description': 'More than 2 valid observations and average best PPI quality',
            },
            {
                'value': 1,
                'name': 'good',
                'description': 'More than 2 valid observations and average good PPI quality',
            },
            {
                'value': 2,
                'name': 'fair',
                'description': 'More than 2 valid observations and average fair PPI quality',
            },
            {
                'value': 3,
                'name': 'poor',
                'description': 'Average poor PPI data quality, or fewer than 3 observations, or more than 24 observations',
            },
        ],
    },
    {
        'name': 'eos_quality',
        'description': 'End of season (green-down) phenology quality',
        'offset': 4,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'best',
                'description': 'More than 2 valid observations and average best PPI quality',
            },
            {
                'value': 1,
                'name': 'good',
                'description': 'More than 2 valid observations and average good PPI quality',
            },
            {
                'value': 2,
                'name': 'fair',
                'description': 'More than 2 valid observations and average fair PPI quality',
            },
            {
                'value': 3,
                'name': 'poor',
                'description': 'Average poor PPI data quality, or fewer than 3 observations, or more than 24 observations',
            },
        ],
    },
    {
        'name': 'overall_quality',
        'description': 'Overall quality across all three phenological phases',
        'offset': 6,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'best',
                'description': 'No poor quality in three phenology phases',
            },
            {
                'value': 1,
                'name': 'good',
                'description': 'Maximum one phase with poor quality',
            },
            {
                'value': 2,
                'name': 'fair',
                'description': 'Maximum two phases with poor quality',
            },
            {
                'value': 3,
                'name': 'poor',
                'description': 'All three phases with poor quality',
            },
        ],
    },
]

## vegetation_properties
"""
fapar_global_300m_10daily_v2, fcover_global_300m_10daily_v2,
lai_global_300m_10daily_v2
For 'qflag' asset
"""
bitfields__fapar_fcover_lai_global_300m_10daily_v2_qflag = [
    {
        'name': 'land_water',
        'description': 'Land/water flag',
        'offset': 0,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'land', 'description': 'Land pixel'},
            {'value': 1, 'name': 'water', 'description': 'Water pixel (not processed)'},
        ],
    },
    {
        'name': 'vegetation_class',
        'description': 'Vegetation class identified',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'nonEBF',
                'description': 'Non-Evergreen Broadleaf Forest',
            },
            {'value': 1, 'name': 'EBF', 'description': 'Evergreen Broadleaf Forest'},
        ],
    },
    {
        'name': 'unused_bit2',
        'description': 'Reserved, not used',
        'offset': 2,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'unused_bit3',
        'description': 'Reserved, not used',
        'offset': 3,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'method_EBF',
        'description': 'Method used for EBF case (applicable when vegetation_class=1)',
        'offset': 4,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'based_on_observations',
                'description': 'Product based on instantaneous observations',
            },
            {
                'value': 1,
                'name': 'based_on_previous_or_missing',
                'description': 'Product based on previous dekadal value, or set to missing',
            },
        ],
    },
    {
        'name': 'method_nonEBF',
        'description': 'Method used for nonEBF case (applicable when vegetation_class=0)',
        'offset': 5,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'second_degree_polynomial',
                'description': 'Second degree polynomial fit',
            },
            {'value': 1, 'name': 'linear_fit', 'description': 'Linear fit'},
            {
                'value': 2,
                'name': 'interpolation',
                'description': 'Interpolation between two nearest dates within 15-day window',
            },
            {
                'value': 3,
                'name': 'nearest_or_missing',
                'description': 'Nearest data within 5-day window, or set to missing',
            },
        ],
    },
    {
        'name': 'instantaneous_EBF_class',
        'description': 'Instantaneous EBF classification flag',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'nonEBF_instantaneous',
                'description': 'nonEBF instantaneous value',
            },
            {
                'value': 1,
                'name': 'EBF_instantaneous',
                'description': 'EBF instantaneous value',
            },
        ],
    },
]
"""
fapar_global_300m_10daily_v1, fcover_global_300m_10daily_v1,
lai_global_300m_10daily_v1
For 'qflag' asset
"""
bitfields__fapar_fcover_lai_global_300m_10daily_v1_qflag = [
    {
        'name': 'land_water',
        'description': 'Land/water flag',
        'offset': 0,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'water', 'description': 'Water pixel (not processed)'},
            {'value': 1, 'name': 'land', 'description': 'Land pixel'},
        ],
    },
    {
        'name': 'vegetation_class',
        'description': 'Vegetation class identified',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'nonEBF',
                'description': 'Non-Evergreen Broadleaf Forest',
            },
            {'value': 1, 'name': 'EBF', 'description': 'Evergreen Broadleaf Forest'},
        ],
    },
    {
        'name': 'missing_dekad_interpolated',
        'description': 'Whether a missing dekad was filled by gap interpolation (HIST mode only)',
        'offset': 2,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'not_interpolated', 'description': 'Not interpolated'},
            {
                'value': 1,
                'name': 'interpolated',
                'description': 'Interpolated from neighbouring dekads',
            },
        ],
    },
    {
        'name': 'unused_bit3',
        'description': 'Reserved, not used',
        'offset': 3,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'method_EBF',
        'description': 'Method used for EBF case (applicable when vegetation_class=1)',
        'offset': 4,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'based_on_observations',
                'description': 'Product based on instantaneous observations',
            },
            {
                'value': 1,
                'name': 'based_on_previous_or_missing',
                'description': 'Product based on previous dekadal value, or set to missing',
            },
        ],
    },
    {
        'name': 'method_nonEBF',
        'description': 'Method used for nonEBF case (applicable when vegetation_class=0)',
        'offset': 5,
        'length': 2,
        'classes': [
            {
                'value': 0,
                'name': 'second_degree_polynomial',
                'description': 'Second degree polynomial fit',
            },
            {'value': 1, 'name': 'linear_fit', 'description': 'Linear fit'},
            {
                'value': 2,
                'name': 'interpolation',
                'description': 'Interpolation between two nearest dates within 15-day window',
            },
            {
                'value': 3,
                'name': 'nearest_or_missing',
                'description': 'Nearest data within 5-day window, or set to missing',
            },
        ],
    },
    {
        'name': 'instantaneous_EBF_class',
        'description': 'Instantaneous EBF classification flag',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'nonEBF_instantaneous',
                'description': 'nonEBF instantaneous value',
            },
            {
                'value': 1,
                'name': 'EBF_instantaneous',
                'description': 'EBF instantaneous value',
            },
        ],
    },
]
"""
fapar_global_1km_10daily_v2, fcover_global_1km_10daily_v2,
lai_global_1km_10daily_v2
For 'qflag' asset
"""
bitfields__fapar_fcover_lai_global_1km_10daily_v2_qflag = [
    {
        'name': 'land_sea',
        'description': 'Land/sea mask based on GLC-2000',
        'offset': 0,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'land', 'description': 'Land pixel'},
            {'value': 1, 'name': 'sea', 'description': 'Sea pixel'},
        ],
    },
    {
        'name': 'unused_bit1',
        'description': 'Reserved, not used',
        'offset': 1,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'filled',
        'description': 'Gap-filling applied (fewer than 6 valid obs in the ±60-day compositing window)',
        'offset': 2,
        'length': 1,
        'classes': [
            {'value': 0, 'name': 'not_filled', 'description': 'No gap-filling applied'},
            {'value': 1, 'name': 'filled', 'description': 'Gap-filling applied'},
        ],
    },
    {
        'name': 'unused_bit3',
        'description': 'Reserved, not used',
        'offset': 3,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'unused_bit4',
        'description': 'Reserved, not used',
        'offset': 4,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'input_status',
        'description': 'Input reflectance data status',
        'offset': 5,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'ok',
                'description': 'Valid reflectance data available',
            },
            {
                'value': 1,
                'name': 'invalid',
                'description': 'All reflectances within ±60 days are out of range or invalid',
            },
        ],
    },
    {
        'name': 'lai_status',
        'description': 'LAI value status',
        'offset': 6,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'ok',
                'description': 'LAI in expected range including tolerance',
            },
            {
                'value': 1,
                'name': 'invalid',
                'description': 'LAI out of range or invalid',
            },
        ],
    },
    {
        'name': 'fapar_status',
        'description': 'FAPAR value status',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'ok',
                'description': 'FAPAR in expected range including tolerance',
            },
            {
                'value': 1,
                'name': 'invalid',
                'description': 'FAPAR out of range or invalid',
            },
        ],
    },
    {
        'name': 'fcover_status',
        'description': 'FCover value status',
        'offset': 8,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'ok',
                'description': 'FCover in expected range including tolerance',
            },
            {
                'value': 1,
                'name': 'invalid',
                'description': 'FCover out of range or invalid',
            },
        ],
    },
    {
        'name': 'hlat_status',
        'description': 'High-latitude correction status',
        'offset': 9,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'no_correction',
                'description': 'No high-latitude correction applied',
            },
            {
                'value': 1,
                'name': 'corrected',
                'description': 'High-latitude correction applied (lat > 55° and SZA > 70°)',
            },
        ],
    },
    {
        'name': 'ebf_status',
        'description': 'Evergreen Broadleaf Forest classification (from GEOCLIM climatology)',
        'offset': 10,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_ebf',
                'description': 'Pixel not recognized as Evergreen Broadleaf Forest',
            },
            {
                'value': 1,
                'name': 'ebf',
                'description': 'Pixel recognized as Evergreen Broadleaf Forest',
            },
        ],
    },
    {
        'name': 'bs_status',
        'description': 'Bare Soil classification (from GEOCLIM climatology; may include inland water)',
        'offset': 11,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_bare_soil',
                'description': 'Pixel not recognized as Bare Soil',
            },
            {
                'value': 1,
                'name': 'bare_soil',
                'description': 'Pixel recognized as Bare Soil',
            },
        ],
    },
    {
        'name': 'climatology_fill',
        'description': 'Climatology-based gap-filling status',
        'offset': 12,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_filled',
                'description': 'Not filled with climatology',
            },
            {
                'value': 1,
                'name': 'filled_climatology',
                'description': 'Gap filled using CACAO climatology',
            },
        ],
    },
    {
        'name': 'interpolation_fill',
        'description': 'Interpolation-based gap-filling status',
        'offset': 13,
        'length': 1,
        'classes': [
            {
                'value': 0,
                'name': 'not_filled',
                'description': 'Not filled with interpolation',
            },
            {
                'value': 1,
                'name': 'filled_interpolation',
                'description': 'Gap filled using linear interpolation',
            },
        ],
    },
    {
        'name': 'unused_bit14',
        'description': 'Reserved, not used',
        'offset': 14,
        'length': 1,
        'classes': [],
    },
    {
        'name': 'unused_bit15',
        'description': 'Reserved, not used',
        'offset': 15,
        'length': 1,
        'classes': [],
    },
]

## water_bodies
"""
wb_global_100m_monthly_v1, wb_global_300m_monthly_v2
For 'qual' asset
"""
classes__wb_global_100m_monthly_v1_qual = [
    {'value': 0, 'name': 'sea', 'description': 'Sea'},
    {'value': 71, 'name': 'very_low', 'description': 'Water body occurrence: Very Low'},
    {'value': 72, 'name': 'low', 'description': 'Water body occurrence: Low'},
    {'value': 73, 'name': 'medium', 'description': 'Water body occurrence: Medium'},
    {'value': 74, 'name': 'high', 'description': 'Water body occurrence: High'},
    {
        'value': 75,
        'name': 'very_high',
        'description': 'Water body occurrence: Very High',
    },
    {
        'value': 76,
        'name': 'permanent',
        'description': 'Water body occurrence: Permanent (WBf ≥ 95%)',
    },
    {'value': 251, 'name': 'no_data', 'description': 'No data'},
    {'value': 252, 'name': 'cloud', 'description': 'Masked by cloud'},
    {'value': 255, 'name': 'not_water', 'description': 'Not water'},
]
"""
wb_global_100m_monthly_v1, wb_global_300m_monthly_v2
For 'wb' asset
"""
classes__wb_global_100m_monthly_v1_wb = [
    {'value': 0, 'name': 'sea', 'description': 'Sea'},
    {'value': 70, 'name': 'water', 'description': 'Water body detected'},
    {'value': 251, 'name': 'no_data', 'description': 'No data'},
    {'value': 255, 'name': 'no_water', 'description': 'No water'},
]
"""
wb_global_300m_10daily_v1, wb_global_1km_10daily_v2
For 'qual' asset
"""
classes__wb_global_300m_1km_10daily_v1_qual = [
    {'value': 0, 'name': 'sea', 'description': 'Sea'},
    {'value': 71, 'name': 'very_low', 'description': 'Water body occurrence: Very Low'},
    {'value': 72, 'name': 'low', 'description': 'Water body occurrence: Low'},
    {'value': 73, 'name': 'medium', 'description': 'Water body occurrence: Medium'},
    {'value': 74, 'name': 'high', 'description': 'Water body occurrence: High'},
    {
        'value': 75,
        'name': 'very_high',
        'description': 'Water body occurrence: Very High',
    },
    {
        'value': 76,
        'name': 'permanent',
        'description': 'Water body occurrence: Permanent (WBf ≥ 95%)',
    },
    {
        'value': 151,
        'name': 'lowland_vegetation',
        'description': 'Masked: lowland vegetation (NDVI mask)',
    },
    {
        'value': 152,
        'name': 'mountain_vegetation',
        'description': 'Masked: mountain vegetation',
    },
    {'value': 241, 'name': 'glacier', 'description': 'Masked: permanent glacier'},
    {'value': 242, 'name': 'volcanic', 'description': 'Masked: volcanic soils'},
    {
        'value': 243,
        'name': 'mountain_no_vegetation',
        'description': 'Masked: mountain without vegetation',
    },
    {
        'value': 244,
        'name': 'lowland_no_vegetation',
        'description': 'Masked: lowland without vegetation',
    },
    {'value': 252, 'name': 'cloud', 'description': 'Masked: cloud'},
    {'value': 253, 'name': 'snow', 'description': 'Masked: snow/ice'},
    {
        'value': 254,
        'name': 'sza_gt_65',
        'description': 'Masked: solar zenith angle > 65°',
    },
    {'value': 255, 'name': 'not_water', 'description': 'Not water'},
]
"""
wb_global_300m_10daily_v1
For 'wb' asset
"""
classes__wb_global_300m_10daily_v1_wb = [
    {'value': 0, 'name': 'sea', 'description': 'Sea'},
    {'value': 70, 'name': 'water', 'description': 'Water body detected'},
    {'value': 255, 'name': 'no_water', 'description': 'No water'},
]
"""
wb_global_1km_10daily_v2
For 'wb' asset
"""
classes__wb_global_1km_10daily_v2_wb = [
    {'value': 0, 'name': 'sea', 'description': 'Sea'},
    {'value': 70, 'name': 'water', 'description': 'Water body detected'},
    {'value': 251, 'name': 'no_data', 'description': 'No data'},
    {'value': 255, 'name': 'no_water', 'description': 'No water'},
]

collection_asset_matches: dict[str, dict] = {
    'dmp_global_1km_10daily_v2': {
        'dmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_global_1km_10daily_v2_qflag),
    },
    'gdmp_global_1km_10daily_v2': {
        'gdmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_global_1km_10daily_v2_qflag),
    },
    'dmp_global_300m_10daily_v1': {
        'dmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'gdmp_global_300m_10daily_v1': {
        'gdmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'npp_global_300m_10daily_v1': {
        'npp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'gpp_global_300m_10daily_v1': {
        'gpp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'dmp_global_300m_10daily_v2': {
        'dmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'gdmp_global_300m_10daily_v2': {
        'gdmp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'npp_global_300m_10daily_v2': {
        'npp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    'gpp_global_300m_10daily_v2': {
        'gpp': Classes(classes__dmp_gdmp_npp_gpp_data),
        'qflag': Bitfields(bitfields__dmp_gdmp_npp_gpp_global_300m_10daily_v1_v2_qflag),
    },
    # dynamic_land_cover
    'lc_global_100m_yearly_v3': {
        'change_confidence_layer': Classes(
            classes__lc_global_100m_yearly_v3_change_confidence
        ),
        'discrete_classification_map': Classes(
            classes__lc_global_100m_yearly_v3_discrete_classification
        ),
        'forest_type_layer': Classes(classes__lc_global_100m_yearly_v3_forest_type),
    },
    'lcm_global_10m_yearly_v1': {'map': Classes(classes__lcm_global_10m_yearly_v1_map)},
    'tcd_pantropical_10m_yearly_v1': {
        'map': Classes(classes__tcd_pantropical_10m_yearly_v1_map)
    },
    # evapotranspiration
    'eta_global_300m_10daily_v1': {
        'flag': Bitfields(bitfields__eta_global_300m_10daily_v1_flag),
    },
    # lake_surface_water_temperature
    'lswt-nrt_global_1km_10daily_v1': {
        'qlevel': Classes(
            classes__lswt_nrt_offline_global_1km_10daily_v1_quality_level
        ),
        'tobs': Bitfields(bitfields__lswt_nrt_offline_global_1km_10daily_v1_time_obs),
    },
    'lswt-offline_global_1km_10daily_v1': {
        'qlevel': Classes(
            classes__lswt_nrt_offline_global_1km_10daily_v1_quality_level
        ),
        'tobs': Bitfields(bitfields__lswt_nrt_offline_global_1km_10daily_v1_time_obs),
    },
    # lake_water_quality (v2 only; v1 has no qflag)
    'lwq-nrt_global_100m_10daily_v2': {
        'qflag': Bitfields(bitfields__lwq_nrt_global_100m_10daily_v2_qflag),
    },
    'lwq-nrt_global_300m_10daily_v2': {
        'qflag': Bitfields(bitfields__lwq_nrt_global_300m_10daily_v2_qflag),
    },
    # land_surface_temperature (hourly only; daily-cycle and tci have no qflag classes)
    'lst_global_5km_hourly_v1': {
        'qflag': Bitfields(bitfields__lst_global_5km_hourly_v1_qflag),
    },
    'lst_global_5km_hourly_v2': {
        'qflag': Bitfields(bitfields__lst_global_5km_hourly_v2_qflag),
    },
    'lst_global_3km_hourly_v3': {
        'qflag': Classes(classes__lst_global_3km_hourly_v3_qflag),
    },
    # river_and_lake_ice_extent
    'lie_baltic_250m_daily_v1': {
        'lie': Classes(classes__lie_baltic_europe_250m_daily_v1_v2_lie),
    },
    'lie_europe_250m_daily_v2': {
        'lie': Classes(classes__lie_baltic_europe_250m_daily_v1_v2_lie),
    },
    'lie_global_500m_daily_v2': {
        'lie': Classes(classes__lie_global_500m_daily_v2_lie),
    },
    'lie_northernhemisphere_500m_daily_v1': {
        'nh_lie': Classes(classes__lie_northernhemisphere_500m_daily_v1_lie),
    },
    # snow_cover_extent
    'sce_europe_500m_daily_v1': {
        'sce500': Classes(classes__sce_europe_500m_daily_v1_sce500),
    },
    'sce_global_1km_daily_v1': {
        'sce': Classes(classes__sce_global_1km_daily_v1_sce),
        'unc': Classes(classes__sce_global_1km_daily_v2_unc),
    },
    'sce_northernhemisphere_1km_daily_v1': {
        'sce': Classes(classes__sce_northernhemisphere_1km_daily_v1_sce),
    },
    # soil_water_index — Europe 1km (T-values: 002, 005, 010, 015, 020, 040, 060, 100)
    'swi_europe_1km_daily_v1': {
        'swi002': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi005': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi010': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi015': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi020': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi040': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi060': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi100': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag002': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag005': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag010': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag015': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag020': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag040': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag060': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag100': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'ssf': Bitfields(bitfields__swi_europe_1km_daily_v1_ssf),
    },
    'swi_europe_1km_daily_v2': {
        'swi002': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi005': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi010': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi015': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi020': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi040': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi060': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'swi100': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag002': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag005': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag010': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag015': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag020': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag040': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag060': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'qflag100': Classes(classes__swi_europe_1km_daily_v1_swi_qflag),
        'ssf': Bitfields(bitfields__swi_europe_1km_daily_v1_ssf),
    },
    # soil_water_index — global daily (ssf only; 10-daily omitted — no ssf in COG example)
    'swi_global_12.5km_daily_v3': {
        'ssf': Bitfields(
            bitfields__swi_global_12_5km_daily_10daily_timeseries_v3_v4_ssf
        ),
    },
    'swi_global_12.5km_daily_v4': {
        'ssf': Bitfields(
            bitfields__swi_global_12_5km_daily_10daily_timeseries_v3_v4_ssf
        ),
    },
    # surface_soil_moisture
    'ssm_europe_1km_daily_v1': {
        'ssm': Classes(classes__ssm_europe_1km_daily_v1),
    },
    # vegetation_indices — NDVI 1km
    'ndvi_global_1km_10daily_v2': {
        'ndvi': Classes(classes__ndvi_global_1km_10daily_v3_ndvi),
    },
    'ndvi_global_1km_10daily_v3': {
        'ndvi': Classes(classes__ndvi_global_1km_10daily_v3_ndvi),
        'qflag': Classes(classes__ndvi_global_1km_10daily_v3_qflag),
    },
    # vegetation_indices — NDVI 300m
    'ndvi_global_300m_10daily_v1': {
        'ndvi': Classes(classes__ndvi_global_300m_10daily_v1_ndvi),
    },
    'ndvi_global_300m_10daily_v2': {
        'ndvi': Classes(classes__ndvi_global_300m_10daily_v2_ndvi),
        'qflag': Bitfields(bitfields__ndvi_global_300m_10daily_v2_qflag),
    },
    'ndvi_global_300m_10daily_v3': {
        'ndvi': Classes(classes__ndvi_global_300m_10daily_v3_ndvi),
        'qflag': Bitfields(bitfields__ndvi_global_300m_10daily_v3_qflag),
    },
    # vegetation_indices — NDVI LTS
    'ndvi-lts_global_1km_10daily_v2': {
        'min_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'median_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'max_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'mean_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'stdev_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
    },
    'ndvi-lts_global_1km_10daily_v3': {
        'min_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'median_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'max_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'mean_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
        'stdev_lts': Classes(
            classes__ndvi_lts_global_1km_10daily_v2_min_median_max_mean_stdev
        ),
    },
    # vegetation_phenology_and_productivity_parameters
    'lsp_global_300m_yearly_v1': {
        'qa_s1': Bitfields(bitfields__lsp_global_300m_yearly_v1_v2_qflag),
        'qa_s2': Bitfields(bitfields__lsp_global_300m_yearly_v1_v2_qflag),
    },
    'lsp_global_300m_yearly_v2': {
        'qa_s1': Bitfields(bitfields__lsp_global_300m_yearly_v1_v2_qflag),
        'qa_s2': Bitfields(bitfields__lsp_global_300m_yearly_v1_v2_qflag),
    },
    # vegetation_properties — FAPAR / FCOVER / LAI 1km v2
    'fapar_global_1km_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_1km_10daily_v2_qflag),
    },
    'fcover_global_1km_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_1km_10daily_v2_qflag),
    },
    'lai_global_1km_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_1km_10daily_v2_qflag),
    },
    # vegetation_properties — FAPAR / FCOVER / LAI 300m v1
    'fapar_global_300m_10daily_v1': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v1_qflag),
    },
    'fcover_global_300m_10daily_v1': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v1_qflag),
    },
    'lai_global_300m_10daily_v1': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v1_qflag),
    },
    # vegetation_properties — FAPAR / FCOVER / LAI 300m v2
    'fapar_global_300m_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v2_qflag),
    },
    'fcover_global_300m_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v2_qflag),
    },
    'lai_global_300m_10daily_v2': {
        'qflag': Bitfields(bitfields__fapar_fcover_lai_global_300m_10daily_v2_qflag),
    },
    # water_bodies
    'wb_global_100m_monthly_v1': {
        'qual': Classes(classes__wb_global_100m_monthly_v1_qual),
        'wb': Classes(classes__wb_global_100m_monthly_v1_wb),
    },
    'wb_global_300m_monthly_v2': {
        'qual': Classes(classes__wb_global_100m_monthly_v1_qual),
        'wb': Classes(classes__wb_global_100m_monthly_v1_wb),
    },
    'wb_global_300m_10daily_v1': {
        'qual': Classes(classes__wb_global_300m_1km_10daily_v1_qual),
        'wb': Classes(classes__wb_global_300m_10daily_v1_wb),
    },
    'wb_global_1km_10daily_v2': {
        'qual': Classes(classes__wb_global_300m_1km_10daily_v1_qual),
        'wb': Classes(classes__wb_global_1km_10daily_v2_wb),
    },
}

collection_product_pages: dict[str, str | None] = {
    # burnt_area
    'ba_global_300m_daily_v3': 'https://land.copernicus.eu/en/products/vegetation/burnt-area-v3-1-daily-300m',
    'ba_global_300m_daily_v4': 'https://land.copernicus.eu/en/products/vegetation/burnt-area-v4-daily-300m',
    'ba_global_300m_monthly_v3': 'https://land.copernicus.eu/en/products/vegetation/burnt-area-v3-1-monthly-300m',
    'ba_global_300m_monthly_v4': 'https://land.copernicus.eu/en/products/vegetation/burnt-area-v4-monthly-300m',
    # vegetation_productivity
    'dmp_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/dry-matter-productivity-v2-0-1km',
    'dmp_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/dry-matter-productivity-v1-0-300m',
    'dmp_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/dry-matter-productivity-v2-0-300m',
    'gdmp_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/gross-dry-matter-productivity-v2-0-1km',
    'gdmp_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/gross-dry-matter-productivity-v1-0-300m',
    'gdmp_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/gross-dry-matter-productivity-v2-0-300m',
    # dynamic_land_cover
    'lc_global_100m_yearly_v3': 'https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-2019-globe',
    'lcm_global_10m_yearly_v1': 'https://land.copernicus.eu/en/products/global-dynamic-land-cover/land-cover-2020-raster-10-m-global-annual',
    'tcd_pantropical_10m_yearly_v1': 'https://land.copernicus.eu/en/products/global-dynamic-land-cover/tree-cover-density-2020-raster-10-m-pantropical-annual',
    # evapotranspiration
    'eta_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/evapotranspiration/evapotranspiration-2025-present-raster-300m-global-10-daily-version-1',
    'hf_global_300m_daily_v1': 'https://land.copernicus.eu/en/products/evapotranspiration/heat-flux-2025-present-raster-300-m-global-daily-version-1',
    # lake_surface_water_temperature
    'lswt-nrt_global_1km_10daily_v1': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/lake-surface-water-temperature-near-real-time-v1-0-1km',
    'lswt-offline_global_1km_10daily_v1': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/lake-surface-water-temperature-offline-1km',
    # lake_water_quality
    'lwq-nrt_global_100m_10daily_v1': 'https://land.copernicus.eu/en/products/water-bodies/lake-water-quality-v1-0-100m',
    'lwq-nrt_global_100m_10daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/lake-water-quality-v2-0-100m',
    'lwq-nrt_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/water-bodies/lake-water-quality-near-real-time-v1-0-300m',
    'lwq-nrt_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/lake-water-quality-near-real-time-v2-0-300m',
    'lwq-reproc_global_300m_10daily_v1': None,
    # land_surface_temperature
    'lst-daily-cycle_global_5km_10daily_v1': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-daily-cycle-global-v1-0-5km',
    'lst-daily-cycle_global_5km_10daily_v2': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-daily-cycle-global-v2-0-5km',
    'lst-daily-cycle_global_3km_10daily_v3': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/daily-land-surface-temperature-global-v3-0-3km',
    'lst_global_5km_hourly_v1': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/hourly-land-surface-temperature-global-v1-0-5km',
    'lst_global_5km_hourly_v2': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/hourly-land-surface-temperature-global-v2-0-5km',
    'lst_global_3km_hourly_v3': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/hourly-land-surface-temperature-global-v3-0-3km',
    'lst-tci_global_5km_10daily_v1': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-thermal-condition-index-global-v1-0-5km',
    'lst-tci_global_5km_10daily_v2': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/10-daily-land-surface-temperature-thermal-condition-index-global-v2-0-5km',
    'lst-tci_global_3km_10daily_v3': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/10daily-land-surface-temperature-synthesis-global-v3-0-3km',
    # net-gross_primary_production
    'gpp_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/gross-primary-production-v1-0-300m',
    'gpp_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/gross-primary-production-v2-0-300m',
    'npp_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/net-primary-production-v1-0-300m',
    'npp_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/net-primary-production-v2-0-300m',
    # river_and_lake_ice_extent
    'lie_baltic_250m_daily_v1': 'https://land.copernicus.eu/en/products/water-bodies/lake-ice-extent-baltic-v1-250m',
    'lie_europe_250m_daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/lake-ice-extent-europe-v2-250m',
    'lie_global_500m_daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/lake-ice-extent-global-500m_v2',
    'lie_northernhemisphere_500m_daily_v1': 'https://land.copernicus.eu/en/products/water-bodies/lake-ice-extent-northern-hemisphere-500m',
    # river_and_lake_water_level
    'wl-lakes_global_vector_daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/water-level-lakes-near-real-time-v2.0',
    'wl-rivers_global_vector_daily_v2': 'https://land.copernicus.eu/en/products/water-bodies/water-level-rivers-near-real-time-v2.0',
    # snow_cover_extent
    'sce_europe_500m_daily_v1': 'https://land.copernicus.eu/en/products/snow/snow-cover-extent-europe-v1-0-500m',
    'sce_global_1km_daily_v1': 'https://land.copernicus.eu/en/products/snow/snow-cover-global-v1-0-1km',
    'sce_northernhemisphere_1km_daily_v1': 'https://land.copernicus.eu/en/products/snow/snow-cover-extent-northern-hemisphere-v1-0-1km',
    # snow_water_equivalent
    'swe_northernhemisphere_5km_daily_v1': 'https://land.copernicus.eu/en/products/snow/snow-water-equivalent-v1-0-5km',
    'swe_northernhemisphere_5km_daily_v2': 'https://land.copernicus.eu/en/products/snow/snow-water-equivalent-v2-0-5km',
    # soil_water_index
    'swi_europe_1km_daily_v1': 'https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-europe-v1-0-1km',
    'swi_europe_1km_daily_v2': 'https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-europe-1km-v2',
    'swi_global_12.5km_10daily_v3': 'https://land.copernicus.eu/en/products/soil-moisture/10-daily-soil-water-index-global-12-5-km-v3',
    'swi_global_12.5km_10daily_v4': 'https://land.copernicus.eu/en/products/soil-moisture/10-daily-soil-water-index-global-12-5-km-v4',
    'swi_global_12.5km_daily_v3': 'https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-global-v3-0-12-5km',
    'swi_global_12.5km_daily_v4': 'https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-global-12-5km-v4',
    'swi-static_global_12.5km_daily_v3': 'https://land.copernicus.eu/en/products/soil-moisture/soil-water-index-static-layers-12-5-km',
    'swi-timeseries_global_12.5km_daily_v3': 'https://land.copernicus.eu/en/products/soil-moisture/daily-soil-water-index-temporal-series-global-12-5km',
    'swi-timeseries_global_12.5km_daily_v4': 'https://land.copernicus.eu/en/products/soil-moisture/soil-water-index-time-series-global-12-5km-v4',
    # surface_soil_moisture
    'ssm_europe_1km_daily_v1': 'https://land.copernicus.eu/en/products/soil-moisture/daily-surface-soil-moisture-v1.0',
    # top-of-canopy_reflectances
    'toc_global_300m_daily_v2': 'https://land.copernicus.eu/en/products/temperature-and-reflectance/surface-reflectance-2018-present-raster-300m-global-daily-version-2.3',
    # vegetation_indices
    'ndvi_global_1km_10daily_v2': None,
    'ndvi_global_1km_10daily_v3': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-index-v3-0-1km',
    'ndvi_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/normalized-difference-vegetation-index-300m-v1.0',
    'ndvi_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-index-v2-0-300m',
    'ndvi_global_300m_10daily_v3': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-index-v3-0-300m',
    'ndvi-lts_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-index-long-term-statistics-v2-0-1km',
    'ndvi-lts_global_1km_10daily_v3': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-long-term-statistics-v3-0-1km',
    'ndvi-sts_global_1km_10daily_v3': 'https://land.copernicus.eu/en/products/vegetation/normalised-difference-vegetation-short-term-statistics-v3-0-1km',
    # vegetation_phenology_and_productivity_parameters
    'lsp_global_300m_yearly_v1': 'https://land.copernicus.eu/en/products/vegetation/land-surface-phenology-2023-present-raster-300m-global-yearly-version-1',
    'lsp_global_300m_yearly_v2': 'https://land.copernicus.eu/en/products/vegetation/land-surface-phenology-2014-present-raster-300m-global-yearly-version-2',
    # vegetation_properties
    'fapar_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-absorbed-photosynthetically-active-radiation-v2-0-1km',
    'fapar_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-absorbed-photosynthetically-active-radiation-v1-0-300m',
    'fapar_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-absorbed-photosynthetically-active-radiation-v2-0-300m',
    'fcover_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-green-vegetation-cover-v2-0-1km',
    'fcover_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-green-vegetation-cover-v1-0-300m',
    'fcover_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/fraction-of-green-vegetation-cover-v2-0-300m',
    'lai_global_1km_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/leaf-area-index-v2-0-1km',
    'lai_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/vegetation/leaf-area-index-300m-v1.0',
    'lai_global_300m_10daily_v2': 'https://land.copernicus.eu/en/products/vegetation/leaf-area-index-v2-0-300m',
    # water_bodies
    'wb_global_100m_monthly_v1': 'https://land.copernicus.eu/en/products/water-bodies/water-bodies-global-v1-0-100m',
    'wb_global_300m_monthly_v2': 'https://land.copernicus.eu/en/products/water-bodies/water-bodies-global-v2-0-300m',
    'wb_global_300m_10daily_v1': 'https://land.copernicus.eu/en/products/water-bodies/water-bodies-global-v1-0-300m',
    'wb_global_1km_10daily_v2': None,
}

providers: list[dict] = [
    {
        'url': 'https://land.copernicus.eu/',
        'name': 'European Environment Agency',
        'roles': ['producer'],
    },
    {
        'url': 'https://commission.europa.eu/',
        'name': 'European Commission',
        'roles': ['licensor'],
    },
    {'url': 'https://vito.be/', 'name': 'VITO', 'roles': ['processor']},
]
# Collections coordinated by the EU Joint Research Centre instead of the EEA:
# the Copernicus Global Land component (global bio-geophysical variables and
# global land cover). Verified against the responsible-party metadata exposed
# by https://land.copernicus.eu/++api++/en/products/...
providers_jrc: list[dict] = [
    {
        'url': 'https://joint-research-centre.ec.europa.eu/',
        'name': "European Commission's Joint Research Centre",
        'roles': ['producer'],
    },
    {
        'url': 'https://commission.europa.eu/',
        'name': 'European Commission',
        'roles': ['licensor'],
    },
    {'url': 'https://vito.be/', 'name': 'VITO', 'roles': ['processor']},
]
jrc_collections: frozenset[str] = frozenset({
    'ba_global_300m_daily_v3',
    'ba_global_300m_daily_v4',
    'ba_global_300m_monthly_v3',
    'ba_global_300m_monthly_v4',
    'dmp_global_1km_10daily_v2',
    'dmp_global_300m_10daily_v1',
    'dmp_global_300m_10daily_v2',
    'fapar_global_1km_10daily_v2',
    'fapar_global_300m_10daily_v1',
    'fapar_global_300m_10daily_v2',
    'fcover_global_1km_10daily_v2',
    'fcover_global_300m_10daily_v1',
    'fcover_global_300m_10daily_v2',
    'gdmp_global_1km_10daily_v2',
    'gdmp_global_300m_10daily_v1',
    'gdmp_global_300m_10daily_v2',
    'gpp_global_300m_10daily_v1',
    'gpp_global_300m_10daily_v2',
    'lai_global_1km_10daily_v2',
    'lai_global_300m_10daily_v1',
    'lai_global_300m_10daily_v2',
    'lc_global_100m_yearly_v3',
    'lcm_global_10m_yearly_v1',
    'lie_baltic_250m_daily_v1',
    'lie_europe_250m_daily_v2',
    'lie_global_500m_daily_v2',
    'lie_northernhemisphere_500m_daily_v1',
    'lsp_global_300m_yearly_v1',
    'lst-daily-cycle_global_3km_10daily_v3',
    'lst-daily-cycle_global_5km_10daily_v1',
    'lst-daily-cycle_global_5km_10daily_v2',
    'lst-tci_global_3km_10daily_v3',
    'lst-tci_global_5km_10daily_v1',
    'lst-tci_global_5km_10daily_v2',
    'lst_global_3km_hourly_v3',
    'lst_global_5km_hourly_v1',
    'lst_global_5km_hourly_v2',
    'lswt-nrt_global_1km_10daily_v1',
    'lswt-offline_global_1km_10daily_v1',
    'lwq-nrt_global_100m_10daily_v1',
    'lwq-nrt_global_100m_10daily_v2',
    'lwq-nrt_global_300m_10daily_v1',
    'lwq-nrt_global_300m_10daily_v2',
    'lwq-reproc_global_300m_10daily_v1',
    'ndvi-lts_global_1km_10daily_v2',
    'ndvi-lts_global_1km_10daily_v3',
    'ndvi-sts_global_1km_10daily_v3',
    'ndvi_global_1km_10daily_v2',
    'ndvi_global_1km_10daily_v3',
    'ndvi_global_300m_10daily_v1',
    'ndvi_global_300m_10daily_v2',
    'ndvi_global_300m_10daily_v3',
    'npp_global_300m_10daily_v1',
    'npp_global_300m_10daily_v2',
    'sce_europe_500m_daily_v1',
    'sce_global_1km_daily_v1',
    'sce_northernhemisphere_1km_daily_v1',
    'ssm_europe_1km_daily_v1',
    'swe_northernhemisphere_5km_daily_v1',
    'swe_northernhemisphere_5km_daily_v2',
    'swi-static_global_12.5km_daily_v3',
    'swi-timeseries_global_12.5km_daily_v3',
    'swi-timeseries_global_12.5km_daily_v4',
    'swi_europe_1km_daily_v1',
    'swi_europe_1km_daily_v2',
    'swi_global_12.5km_10daily_v3',
    'swi_global_12.5km_10daily_v4',
    'swi_global_12.5km_daily_v3',
    'swi_global_12.5km_daily_v4',
    'tcd_pantropical_10m_yearly_v1',
    'wb_global_1km_10daily_v2',
    'wb_global_300m_10daily_v1',
    'wb_global_300m_monthly_v2',
    'wl-lakes_global_vector_daily_v2',
    'wl-rivers_global_vector_daily_v2',
})
contacts: list[dict] = [
    {
        'name': 'Copernicus Land Monitoring Service',
        'organization': 'European Environment Agency',
        'roles': ['producer'],
        'emails': [{'value': 'copernicus@eea.europa.eu', 'roles': ['contact point']}],
        'phones': [{'value': '+4533367100', 'roles': ['contact point']}],
        'links': [
            {
                'href': 'https://land.copernicus.eu/',
                'rel': 'about',
                'type': 'text/html',
                'title': 'Homepage of the Copernicus Land Monitoring Service',
            }
        ],
    }
]
data_policy: dict[str, str] = {
    'href': 'https://land.copernicus.eu/en/data-policy',
    'rel': 'license',
    'type': 'text/html',
    'title': 'Data policy for Copernicus Land Monitoring Service products and services',
}


def add_extras(jsons_folder: pathlib.Path):
    collection_jsons = jsons_folder.glob('collection*.json')
    for collection_json in collection_jsons:
        with open(collection_json, 'r+') as f:
            added: bool = False
            content: dict = orjson.loads(f.read())
            collection_name: str = (
                content['id']
                .replace('clms_', '')
                .replace('_cog', '')
                .replace('_nc', '')
                .replace('_geojson', '')
            )
            is_cog: bool = False if '_nc' in content['id'] else True

            collection_providers = (
                providers_jrc if collection_name in jrc_collections else providers
            )
            # Swap a producer left over from the other coordinating body in
            # place, so moving a collection between the two lists replaces the
            # producer instead of leaving both of them behind.
            superseded_producer = (
                providers[0]
                if collection_providers is providers_jrc
                else providers_jrc[0]
            )
            if superseded_producer in content['providers']:
                content['providers'][
                    content['providers'].index(superseded_producer)
                ] = collection_providers[0]

            for provider in collection_providers:
                if provider not in content['providers']:
                    content['providers'].append(provider)

            if not content.get('contacts'):
                content['contacts'] = contacts
                content['stac_extensions'].append(
                    'https://stac-extensions.github.io/contacts/v1.0.0/schema.json'
                )

            if not content.get('links') or len(content['links']) == 0:
                content['links'] = [data_policy]
                if collection_product_pages[collection_name]:
                    content['links'].append({
                        'rel': 'about',
                        'href': collection_product_pages[collection_name],
                        'type': 'text/html',
                        'title': 'Product page',
                    })

            if is_cog:
                try:
                    for key, match in collection_asset_matches[collection_name].items():
                        if isinstance(match, Classes):
                            content['item_assets'][key]['bands'][0][
                                'classification:classes'
                            ] = match.data
                            added = True
                        if isinstance(match, Bitfields):
                            content['item_assets'][key]['bands'][0][
                                'classification:bitfields'
                            ] = match.data
                            added = True

                    if added:
                        found = False
                        for ext in content['stac_extensions']:
                            if 'classification' in ext:
                                found = True
                        if not found:
                            content['stac_extensions'].append(
                                StacExtension.CLASSIFICATION
                            )
                except KeyError:
                    logging.warning(
                        'No classes/bitfields found for collection %s', collection_name
                    )

            f.seek(0)
            f.write(orjson.dumps(content, option=orjson.OPT_INDENT_2).decode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extend CLMS collections with additional data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-f',
        '--folder',
        default=pathlib.Path(__file__).parent,
        help='Path to folder with CLMS collections (default: current folder)',
        type=pathlib.Path,
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='Increase verbosity',
        action='count',
        default=0,
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    add_extras(args.folder)
