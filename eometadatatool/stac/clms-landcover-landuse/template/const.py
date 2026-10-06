from typing import TypedDict

CLMSConfig = TypedDict('CLMSConfig', {
    'collection': str,
    'gsd': int,
    'contains': str | None,
    'classification:classes': list[dict] | None,
    'bands': list[dict],
})

PRODUCT_CONFIGS: dict[str, dict[str, CLMSConfig]] = {
    'dominant_leaf_type': {
        'CLMS_HRLVLCC_BCD_': CLMSConfig(**{
            'collection': 'clms_vlcc_broadleaved-cover-density_europe_100m_yearly_v1',
            'gsd': 100,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'all_non_broadleaved_covered_areas', 'title': 'all non-broadleaved covered areas'},
                {'value': 1,   'name': 'broadleaved_cover_density', 'title': 'broadleaved cover density in %', 'description': 'Values 1-100 represent broadleaved cover density in percent'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Broadleaved Cover Density",
                  "name": "bcd"
                }
            ],
        }),
        'CLMS_HRLVLCC_CCD_': CLMSConfig(**{
            'collection': 'clms_vlcc_coniferous-cover-density_europe_100m_yearly_v1',
            'gsd': 100,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'all_non_coniferous_covered_areas', 'title': 'all non-coniferous covered areas'},
                {'value': 1,   'name': 'coniferous_cover_density', 'title': 'coniferous cover density in %', 'description': 'Values 1-100 represent coniferous cover density in percent'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Coniferous Cover Density",
                  "name": "ccd"
                }
            ],
        }),
        'CLMS_HRLVLCC_DLTC_': CLMSConfig(**{
            'collection': 'clms_vlcc_dominant-leaf-type-change_europe_20m_3yearly_v1',
            'gsd': 20,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'unchanged_areas_with_no_tree_cover', 'title': 'unchanged areas with no tree cover'},
                {'value': 1,   'name': 'new_broadleaved_cover', 'title': 'new broadleaved cover'},
                {'value': 2,   'name': 'new_coniferous_cover', 'title': 'new coniferous cover'},
                {'value': 3,   'name': 'loss_of_broadleaved_cover', 'title': 'loss of broadleaved cover'},
                {'value': 4,   'name': 'loss_of_coniferous_cover', 'title': 'loss of coniferous cover'},
                {'value': 10,  'name': 'unchanged_areas_with_tree_cover', 'title': 'unchanged areas with tree cover'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Dominant Leaf Type Change",
                  "name": "dltc"
                }
            ],
        }),
        'CLMS_HRLVLCC_DLTCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_dominant-leaf-type-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 1,   'name': 'classification_confidence', 'title': 'classification confidence', 'description': 'Values 0-100 represent classification confidence (probability margin between highest and second highest ranked leaf type class)'},
                {'value': 253, 'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Dominant Leaf Type Confidence Layer",
                  "name": "dltccl"
                }
            ],
        }),
        'CLMS_HRLVLCC_DLT_': CLMSConfig(**{
            'collection': 'clms_vlcc_dominant-leaf-type_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 1,   'name': 'broadleaved_trees', 'title': 'broadleaved trees'},
                {'value': 2,   'name': 'coniferous_trees', 'title': 'coniferous trees'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Dominant Leaf Type",
                  "name": "dlt"
                }
            ],
        }),
    },
    'forest_type': {
        'CLMS_HRLVLCC_FTY_10m': CLMSConfig(**{
            'collection': 'clms_vlcc_forest-type_europe_10m_3yearly_v1',
            'gsd': 10,
            'contains': '_R10m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_forest_areas', 'title': 'all non-forest areas'},
                {'value': 1,   'name': 'broadleaved_forest', 'title': 'broadleaved forest'},
                {'value': 2,   'name': 'coniferous_forest', 'title': 'coniferous forest'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Forest Type",
                  "name": "fty"
                }
            ],
        }),
        'CLMS_HRLVLCC_FTY_100m': CLMSConfig(**{
            'collection': 'clms_vlcc_forest-type_europe_100m_3yearly_v1',
            'gsd': 100,
            'contains': '_R100m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_forest_areas', 'title': 'all non-forest areas'},
                {'value': 1,   'name': 'broadleaved_forest', 'title': 'broadleaved forest'},
                {'value': 2,   'name': 'coniferous_forest', 'title': 'coniferous forest'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Forest Type",
                  "name": "fty"
                }
            ],
        }),
        'CLMS_HRLVLCC_FADSL_': CLMSConfig(**{
            'collection': 'clms_vlcc_forest-additional-support-layer_europe_10m_3yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'all_non_tree_covered_areas_and_tree_cover_without_urban_or_agricultural_use', 'title': 'all non-tree covered areas, and tree cover without urban context or agricultural use'},
                {'value': 3,   'name': 'trees_predominantly_used_for_agricultural_practices_broadleaved', 'title': 'trees predominantly used for agricultural practices broadleaved (from CLC2018)'},
                {'value': 4,   'name': 'trees_in_urban_context_broadleaved_and_coniferous_imd', 'title': 'trees in urban context broadleaved and coniferous (from IMD2018)'},
                {'value': 5,   'name': 'trees_in_urban_context_broadleaved_and_coniferous_clc', 'title': 'trees in urban context broadleaved and coniferous (from CLC2018)'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Forest Additional Support Layer",
                  "name": "fadsl"
                }
            ],
        }),
    },
    'tree_cover_density': {
        'CLMS_HRLVLCC_TCDCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_tree-cover-density-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'standard_deviation_of_tcd_estimate', 'title': 'standard deviation of tcd estimate', 'description': 'Values 0-100 represent standard deviation of TCD estimate in percent'},
                {'value': 253, 'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Tree Cover Density Confidence Layer",
                  "name": "tcdcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_TCD_100m': CLMSConfig(**{
            'collection': 'clms_vlcc_tree-cover-density_europe_100m_yearly_v1',
            'gsd': 100,
            'contains': '_R100m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Tree Cover Density",
                  "name": "tcd"
                }
            ],
        }),
        'CLMS_HRLVLCC_TCD_10m': CLMSConfig(**{
            'collection': 'clms_vlcc_tree-cover-density_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': '_R10m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Tree Cover Density",
                  "name": "tcd"
                }
            ],
        }),
        'CLMS_HRLVLCC_TCPCCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_tree-cover-presence-change-confidence-layer_europe_20m_3yearly_v1',
            'gsd': 20,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'change_confidence', 'title': 'change confidence', 'description': 'Values 1-100 represent change confidence'},
                {'value': 253, 'name': 'all_non_tree_covered_areas', 'title': 'all non-tree covered areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Tree Cover Presence Change Confidence Layer",
                  "name": "tcpccl"
                }
            ],
        }),
        'CLMS_HRLVLCC_TCPC_': CLMSConfig(**{
            'collection': 'clms_vlcc_tree-cover-presence-change_europe_20m_3yearly_v1',
            'gsd': 20,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'unchanged_areas_with_no_tree_cover', 'title': 'unchanged areas with no tree cover'},
                {'value': 1,   'name': 'new_tree_cover', 'title': 'new tree cover'},
                {'value': 2,   'name': 'loss_of_tree_cover', 'title': 'loss of tree cover'},
                {'value': 10,  'name': 'unchanged_areas_with_tree_cover', 'title': 'unchanged areas with tree cover'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Tree Cover Presence Change",
                  "name": "tcpc"
                }
            ],
        }),
    },
    'grassland_and_herbaceous': {
        'CLMS_HRLVLCC_GRACCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-change-confidence-layer_europe_20m_3yearly_v1',
            'gsd': 20,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'change_confidence', 'title': 'change confidence', 'description': 'Values 0-100 represents change confidence'},
                {'value': 253, 'name': 'all_non_change_areas', 'title': 'all non-change areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Change Confidence Layer",
                  "name": "graccl"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRAC_': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-change_europe_20m_3yearly_v1',
            'gsd': 20,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'unchanged_non_grassland_in_both_years', 'title': 'unchanged non-grassland in both years'},
                {'value': 1,   'name': 'grassland_gain', 'title': 'grassland gain'},
                {'value': 2,   'name': 'grassland_loss', 'title': 'grassland loss'},
                {'value': 10,  'name': 'unchanged_grassland_in_both_years', 'title': 'unchanged grassland in both years'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Change",
                  "name": "grac"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRACL_': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'classification_confidence', 'title': 'classification confidence', 'description': 'Values 0-100 represent classification confidence'},
                {'value': 253, 'name': 'all_non_grassland_areas', 'title': 'all non-grassland areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Confidence Layer",
                  "name": "gracl"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRA_100m': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland_europe_100m_yearly_v1',
            'gsd': 100,
            'contains': '_R100m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_grassland_areas', 'title': 'all non-grassland areas'},
                {'value': 1,   'name': 'grassland', 'title': 'grassland'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland",
                  "name": "gra"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRA_10m': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': '_R10m_',
            'classification:classes': [
                {'value': 0,   'name': 'all_non_grassland_areas', 'title': 'all non-grassland areas'},
                {'value': 1,   'name': 'grassland', 'title': 'grassland'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland",
                  "name": "gra"
                }
            ],
        }),
        'CLMS_HRLVLCC_HER_': CLMSConfig(**{
            'collection': 'clms_vlcc_herbaceous-cover_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'non_grassland_in_reference_year', 'title': 'non-grassland in reference year'},
                {'value': 1,   'name': 'temporary_grassland_in_reference_year', 'title': 'temporary grassland in reference year'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Herbaceous Cover",
                  "name": "her"
                }
            ],
        }),
        'CLMS_HRLVLCC_PLOUGH_': CLMSConfig(**{
            'collection': 'clms_vlcc_ploughing-indicator_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'indication_of_ploughing_in_current_year', 'title': 'Indication of ploughing in current year'},
                {'value': 1,   'name': 'years_since_last_ploughing_1', 'title': 'Number of years since last indication of ploughing'},
                {'value': 2,   'name': 'years_since_last_ploughing_2', 'title': 'Number of years since last indication of ploughing'},
                {'value': 3,   'name': 'years_since_last_ploughing_3', 'title': 'Number of years since last indication of ploughing'},
                {'value': 4,   'name': 'years_since_last_ploughing_4', 'title': 'Number of years since last indication of ploughing'},
                {'value': 5,   'name': 'years_since_last_ploughing_5', 'title': 'Number of years since last indication of ploughing'},
                {'value': 6,   'name': 'years_since_last_ploughing_6', 'title': 'Number of years since last indication of ploughing'},
                {'value': 100, 'name': 'change_in_herbaceous_cover', 'title': 'Change in herbaceous cover'},
                {'value': 253, 'name': 'no_ploughing_information', 'title': 'no ploughing information'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Ploughing Indicator",
                  "name": "plough"
                }
            ],
        }),
    },
    'grassland_mowing_events': {
        'CLMS_HRLVLCC_GRAMD': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-mowing-dates_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_mowing_detected', 'title': 'no mowing detected'},
                {'value': 1,     'name': 'start_doy_of_mowing_event', 'title': 'start doy of mowing event', 'description': 'Values 1-366 represent start (DOY) of each mowing event'},
                {'value': 65533, 'name': 'all_non_herbaceous_areas', 'title': 'all non-herbaceous areas'},
                {'value': 65535, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Mowing Dates",
                  "name": "gramd"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRAMECL_': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-mowing-events-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'mowing_detection_confidence', 'title': 'mowing detection confidence', 'description': 'Values 0-100 represent mowing detection confidence'},
                {'value': 253, 'name': 'all_non_mowing_areas', 'title': 'all non-mowing areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Mowing Events Confidence Layer",
                  "name": "gramecl"
                }
            ],
        }),
        'CLMS_HRLVLCC_GRAME_': CLMSConfig(**{
            'collection': 'clms_vlcc_grassland-mowing-events_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'no_mowing_detected', 'title': 'no mowing detected'},
                {'value': 1,   'name': 'number_of_mowing_events_1', 'title': 'Number of mowing events detected'},
                {'value': 2,   'name': 'number_of_mowing_events_2', 'title': 'Number of mowing events detected'},
                {'value': 3,   'name': 'number_of_mowing_events_3', 'title': 'Number of mowing events detected'},
                {'value': 4,   'name': 'number_of_mowing_events_4', 'title': 'Number of mowing events detected'},
                {'value': 253, 'name': 'all_non_herbaceous_areas', 'title': 'all non-herbaceous areas'},
                {'value': 255, 'name': 'outside_area', 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Grassland Mowing Events",
                  "name": "grame"
                }
            ],
        }),
    },
    'crop_types': {
        'CLMS_HRLVLCC_CTY_': CLMSConfig(**{
            'collection': 'clms_vlcc_crop-types_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_cropland',                 'title': 'no cropland'},
                {'value': 1110,  'name': 'wheat',                       'title': 'wheat'},
                {'value': 1120,  'name': 'barley',                      'title': 'barley'},
                {'value': 1130,  'name': 'maize',                       'title': 'maize'},
                {'value': 1140,  'name': 'rice',                        'title': 'rice'},
                {'value': 1150,  'name': 'other_cereals',               'title': 'other cereals'},
                {'value': 1210,  'name': 'fresh_vegetables',            'title': 'fresh vegetables'},
                {'value': 1220,  'name': 'dry_pulses',                  'title': 'dry pulses'},
                {'value': 1310,  'name': 'potatoes',                    'title': 'potatoes'},
                {'value': 1320,  'name': 'sugar_beet',                  'title': 'sugar beet'},
                {'value': 1410,  'name': 'sunflower',                   'title': 'sunflower'},
                {'value': 1420,  'name': 'soybeans',                    'title': 'soybeans'},
                {'value': 1430,  'name': 'rapeseed',                    'title': 'rapeseed'},
                {'value': 1440,  'name': 'flax_cotton_and_hemp',        'title': 'flax cotton and hemp'},
                {'value': 2100,  'name': 'grapes',                      'title': 'grapes'},
                {'value': 2200,  'name': 'olives',                      'title': 'olives'},
                {'value': 2310,  'name': 'fruits',                      'title': 'fruits'},
                {'value': 2320,  'name': 'nuts',                        'title': 'nuts'},
                {'value': 3100,  'name': 'unclassified_annual_crop',    'title': 'unclassified annual crop'},
                {'value': 3200,  'name': 'unclassified_permanent_crop', 'title': 'unclassified permanent crop'},
                {'value': 65535, 'name': 'outside_area',                'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Crop Types",
                  "name": "cty"
                }
            ],
        }),
        'CLMS_HRLVLCC_CTYCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_crop-types-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,   'name': 'crop_type_confidence', 'title': 'crop type confidence', 'description': 'Values 0-100 represent probability expressed as a percentage'},
                {'value': 253, 'name': 'no_cropland',          'title': 'no cropland'},
                {'value': 255, 'name': 'outside_area',         'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Crop Types Confidence Layer",
                  "name": "ctycl"
                }
            ],
        }),
    },
    'cropping_patterns': {
        'CLMS_HRLVLCC_CPBSA_': CLMSConfig(**{
            'collection': 'clms_vlcc_bare-soil-after_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',                        'title': 'no annual cropland'},
                {'value': 1,     'name': 'bare_soil_after_days',                      'title': 'bare soil period after harvest in days', 'description': 'Values 1-275 represent days'},
                {'value': 65526, 'name': 'fallow_land',                               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',                         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65529, 'name': 'bare_soil_period_not_within_calendar_year', 'title': 'bare soil period does not occur within calendar year boundaries'},
                {'value': 65531, 'name': 'insufficient_observations',                 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',                     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_defined_timeframe',          'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',                              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Bare Soil After",
                  "name": "cpbsa"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPBSACL_': CLMSConfig(**{
            'collection': 'clms_vlcc_bare-soil-after-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',                   'title': 'uncertainty in days', 'description': 'Values 1-80 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',                        'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',                  'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65529, 'name': 'bare_soil_not_within_calendar_year', 'title': 'bare soil period does not occur within calendar year boundaries'},
                {'value': 65531, 'name': 'insufficient_observations',          'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',              'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_defined_timeframe',   'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',           'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',                       'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Bare Soil After Confidence Layer",
                  "name": "cpbsacl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPBSB_': CLMSConfig(**{
            'collection': 'clms_vlcc_bare-soil-before_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',                        'title': 'no annual cropland'},
                {'value': 1,     'name': 'bare_soil_before_days',                     'title': 'bare soil period before emergence in days', 'description': 'Values 1-295 represent days'},
                {'value': 65526, 'name': 'fallow_land',                               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',                         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65529, 'name': 'bare_soil_period_not_within_calendar_year', 'title': 'bare soil period does not occur within calendar year boundaries'},
                {'value': 65531, 'name': 'insufficient_observations',                 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',                     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_defined_timeframe',          'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',                              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Bare Soil Before",
                  "name": "cpbsb"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPBSBCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_bare-soil-before-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',                   'title': 'uncertainty in days', 'description': 'Values 1-80 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',                        'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',                  'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65529, 'name': 'bare_soil_not_within_calendar_year', 'title': 'bare soil period does not occur within calendar year boundaries'},
                {'value': 65531, 'name': 'insufficient_observations',          'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',              'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_defined_timeframe',   'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',           'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',                       'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Bare Soil Before Confidence Layer",
                  "name": "cpbsbcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPCST_': CLMSConfig(**{
            'collection': 'clms_vlcc_cropping-seasons-types_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'not_consistently_annual_crop', 'title': 'location not consistently classified as annual crop over 3 years'},
                {'value': 1,     'name': 'one_crop_type',                'title': '1 unique crop type over 3-year period'},
                {'value': 2,     'name': 'two_crop_types',               'title': '2 unique crop types over 3-year period'},
                {'value': 3,     'name': 'three_crop_types',             'title': '3 unique crop types over 3-year period'},
                {'value': 65528, 'name': 'no_cpcst_possible',            'title': 'no CPCST possible - permanent/grassland/fodder in reference year'},
                {'value': 65535, 'name': 'outside_area',                 'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Cropping Seasons Types",
                  "name": "cpcst"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPCSY_': CLMSConfig(**{
            'collection': 'clms_vlcc_cropping-seasons_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'one_growing_season',        'title': '1 growing season'},
                {'value': 2,     'name': 'two_growing_seasons',       'title': '2 growing seasons'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Cropping Seasons Yearly",
                  "name": "cpcsy"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPFLD_': CLMSConfig(**{
            'collection': 'clms_vlcc_fallow-land-duration_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_fallow_land',        'title': 'no fallow land'},
                {'value': 1,     'name': 'fallow_duration_days',  'title': 'fallow land duration in days', 'description': 'Values 1-1826 represent total fallow days over 2017-2021'},
                {'value': 65535, 'name': 'outside_area',          'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Fallow Land Duration",
                  "name": "cpfld"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPFLDCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_fallow-land-duration-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',         'title': 'uncertainty in days', 'description': 'Values 1-200 represent uncertainty in days'},
                {'value': 65534, 'name': 'no_confidence_calculable', 'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',             'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Fallow Land Duration Confidence Layer",
                  "name": "cpfldcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPFLP_': CLMSConfig(**{
            'collection': 'clms_vlcc_fallow-land-presence_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_fallow_land', 'title': 'no fallow land'},
                {'value': 1,     'name': 'fallow_land',    'title': 'fallow land'},
                {'value': 65535, 'name': 'outside_area',   'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Fallow Land Presence",
                  "name": "cpflp"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPFLPCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_fallow-land-presence-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'fallow_presence_confidence', 'title': 'fallow presence confidence', 'description': 'Values 0-100 represent probability expressed as percentage'},
                {'value': 253,   'name': 'no_fallow_land',             'title': 'no fallow land'},
                {'value': 65535, 'name': 'outside_area',               'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Fallow Land Presence Confidence Layer",
                  "name": "cpflpcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCD_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-duration_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'duration_days',             'title': 'main crop season duration in days', 'description': 'Values 40-366 represent days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Duration",
                  "name": "cpmcd"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCDCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-duration-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',          'title': 'uncertainty in days', 'description': 'Values 1-80 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',  'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Duration Confidence Layer",
                  "name": "cpmcdcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCE_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-emergence_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'emergence_doy',             'title': 'emergence date YYDOY', 'description': 'YYDOY where YY = last 2 digits of year, DOY = day of year 1-366'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Emergence",
                  "name": "cpmce"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCECL_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-emergence-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',          'title': 'uncertainty in days', 'description': 'Values 1-40 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',  'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Emergence Confidence Layer",
                  "name": "cpmcecl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCH_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-harvest_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'harvest_doy',               'title': 'harvest date YYDOY', 'description': 'YYDOY where YY = last 2 digits of year, DOY = day of year 1-366'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Harvest",
                  "name": "cpmch"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPMCHCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_main-crop-harvest-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',          'title': 'uncertainty in days', 'description': 'Values 1-40 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',  'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Main Crop Harvest Confidence Layer",
                  "name": "cpmchcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPSCD_': CLMSConfig(**{
            'collection': 'clms_vlcc_secondary-crop-duration_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'duration_days',             'title': 'secondary crop duration in days', 'description': 'Values 40-366 represent days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65530, 'name': 'no_secondary_season',       'title': 'no secondary crop growing season beyond main season'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Secondary Crops Duration",
                  "name": "cpscd"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPSCDCL_': CLMSConfig(**{
            'collection': 'clms_vlcc_secondary-crop-duration-confidence-layer_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'uncertainty_days',          'title': 'uncertainty in days', 'description': 'Values 1-80 represent uncertainty in days'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65530, 'name': 'no_secondary_season',       'title': 'no secondary crop growing season beyond main season'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65534, 'name': 'no_confidence_calculable',  'title': 'no confidence can be calculated'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Secondary Crops Duration Confidence Layer",
                  "name": "cpscdcl"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPSCE_': CLMSConfig(**{
            'collection': 'clms_vlcc_secondary-crop-emergence_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'emergence_doy',             'title': 'secondary crop emergence YYDOY', 'description': 'YYDOY where YY = last 2 digits of year, DOY = day of year 1-366'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65530, 'name': 'no_secondary_season',       'title': 'no secondary crop growing season beyond main season'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Secondary Crops Emergence",
                  "name": "cpsce"
                }
            ],
        }),
        'CLMS_HRLVLCC_CPSCT_': CLMSConfig(**{
            'collection': 'clms_vlcc_secondary-crop-types_europe_10m_yearly_v1',
            'gsd': 10,
            'contains': None,
            'classification:classes': [
                {'value': 0,     'name': 'no_annual_cropland',        'title': 'no annual cropland'},
                {'value': 1,     'name': 'short_summer',              'title': 'short summer secondary season'},
                {'value': 2,     'name': 'long_summer',               'title': 'long summer secondary season'},
                {'value': 3,     'name': 'short_winter',              'title': 'short winter secondary season'},
                {'value': 4,     'name': 'long_winter',               'title': 'long winter secondary season'},
                {'value': 65526, 'name': 'fallow_land',               'title': 'fallow land occurrence'},
                {'value': 65527, 'name': 'no_field_geometry',         'title': 'no delineated field geometry overlaps with annual cropland'},
                {'value': 65530, 'name': 'no_secondary_season',       'title': 'no secondary crop growing season beyond main season'},
                {'value': 65531, 'name': 'insufficient_observations', 'title': 'insufficient satellite observations'},
                {'value': 65532, 'name': 'no_season_delineation',     'title': 'no season delineation possible'},
                {'value': 65533, 'name': 'season_outside_timeframe',  'title': 'season outside defined timeframe'},
                {'value': 65535, 'name': 'outside_area',              'title': 'outside area'},
            ],
            'bands': [
                {
                  "description": "Secondary Crops Types",
                  "name": "cpsct"
                }
            ],
        }),
    },
    'clcplus_instance': {
        'CLMS_CLCPLUS_LULUCF-INSTANCE_': CLMSConfig(**{
            'collection': 'clms_clcplus_lulucf-instance_europe_100m_yearly_v1',
            'gsd': 100,
            'contains': None,
            'classification:classes': [
                {'value': 11,  'name': 's_burnt_areas',              'title': 'S Burnt areas'},
                {'value': 12,  'name': 's_settlements',              'title': 'S Settlements'},
                {'value': 13,  'name': 's_green_urban_areas',        'title': 'S Green urban areas'},
                {'value': 14,  'name': 's_other_settlements',        'title': 'S Other settlements'},
                {'value': 21,  'name': 'fl_burnt_areas',             'title': 'FL Burnt areas'},
                {'value': 22,  'name': 'fl_transitional_woodland',   'title': 'FL Transitional woodland'},
                {'value': 23,  'name': 'fl_deciduous',               'title': 'FL Deciduous'},
                {'value': 24,  'name': 'fl_coniferous_evergreen',    'title': 'FL Coniferous/Evergreen'},
                {'value': 25,  'name': 'fl_other_forestland',        'title': 'FL Other forestland'},
                {'value': 31,  'name': 'cl_burnt_areas',             'title': 'CL Burnt areas'},
                {'value': 32,  'name': 'cl_annual_crops',            'title': 'CL Annual crops'},
                {'value': 33,  'name': 'cl_perennial_crops',         'title': 'CL Perennial crops'},
                {'value': 34,  'name': 'cl_other_cropland',          'title': 'CL Other cropland'},
                {'value': 41,  'name': 'gl_burnt_areas',             'title': 'GL Burnt areas'},
                {'value': 42,  'name': 'gl_pastures',                'title': 'GL Pastures'},
                {'value': 43,  'name': 'gl_shrubs',                  'title': 'GL Shrubs'},
                {'value': 44,  'name': 'gl_natural_grassland',       'title': 'GL Natural grassland'},
                {'value': 45,  'name': 'gl_other_grassland',         'title': 'GL Other grassland'},
                {'value': 51,  'name': 'wl_wetland_managed',         'title': 'WL Wetland managed'},
                {'value': 52,  'name': 'wl_wetland_unmanaged',       'title': 'WL Wetland unmanaged'},
                {'value': 53,  'name': 'wl_water_managed',           'title': 'WL Water managed'},
                {'value': 54,  'name': 'wl_water_unmanaged',         'title': 'WL Water unmanaged'},
                {'value': 55,  'name': 'wl_burnt_areas',             'title': 'WL Burnt areas'},
                {'value': 61,  'name': 'ol_bare_soil_and_rocks',     'title': 'OL Bare soil and rocks'},
                {'value': 62,  'name': 'ol_permanent_snow_and_ice',  'title': 'OL Permanent snow and ice'},
                {'value': 63,  'name': 'ol_lichens_and_mosses',      'title': 'OL Lichens and mosses'},
                {'value': 64,  'name': 'ol_other_otherland',         'title': 'OL Other otherland'},
                {'value': 254, 'name': 'unclassified_clouds',        'title': 'Unclassified, clouds'},
                {'value': 255, 'name': 'outside_area',               'title': 'Outside area'},
            ],
            'bands': [
                {
                  "description": "CLCplus LULUCF Instance",
                  "name": "clcplus_lulucf_instance"
                }
            ],
        }),
    },
}


def get_config(identifier: str) -> tuple[str, CLMSConfig]:
    for product_type, prefixes in PRODUCT_CONFIGS.items():
        for prefix, cfg in prefixes.items():
            contains = cfg['contains']
            if contains is None:
                if identifier.startswith(prefix):
                    return product_type, cfg
            else:
                base_prefix = prefix.rsplit('_', 1)[0] + '_'
                if identifier.startswith(base_prefix) and contains in identifier:
                    return product_type, cfg
    raise KeyError(f'No CLMS config found for identifier {identifier!r}')


ASSET_TITLES: dict[str, str] = {
    'CLMS_HRLVLCC_BCD_': 'Broadleaved Cover Density Raster (100m)',
    'CLMS_HRLVLCC_CCD_': 'Coniferous Cover Density Raster (100m)',
    'CLMS_HRLVLCC_DLTC_': 'Dominant Leaf Type Change Raster (20m)',
    'CLMS_HRLVLCC_DLTCL_': 'Dominant Leaf Type Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_DLT_': 'Dominant Leaf Type Raster (10m)',
    'CLMS_HRLVLCC_FTY_10m': 'Forest Type Raster (10m)',
    'CLMS_HRLVLCC_FTY_100m': 'Forest Type Raster (100m)',
    'CLMS_HRLVLCC_FADSL_': 'Forest Additional Support Layer Raster (10m)',
    'CLMS_HRLVLCC_TCDCL_': 'Tree Cover Density Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_TCD_10m': 'Tree Cover Density Raster (10m)',
    'CLMS_HRLVLCC_TCD_100m': 'Tree Cover Density Raster (100m)',
    'CLMS_HRLVLCC_TCPCCL_': 'Tree Cover Presence Change Confidence Layer Raster (20m)',
    'CLMS_HRLVLCC_TCPC_': 'Tree Cover Presence Change Raster (20m)',
    'CLMS_HRLVLCC_GRACCL_': 'Grassland Change Confidence Layer Raster (20m)',
    'CLMS_HRLVLCC_GRAC_': 'Grassland Change Raster (20m)',
    'CLMS_HRLVLCC_GRACL_': 'Grassland Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_GRA_10m': 'Grassland Raster (10m)',
    'CLMS_HRLVLCC_GRA_100m': 'Grassland Raster (100m)',
    'CLMS_HRLVLCC_HER_': 'Herbaceous Cover Raster (10m)',
    'CLMS_HRLVLCC_PLOUGH_': 'Ploughing Indicator Raster (10m)',
    'CLMS_HRLVLCC_GRAMD': 'Grassland Mowing Dates Raster (10m)',
    'CLMS_HRLVLCC_GRAMECL_': 'Grassland Mowing Events Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_GRAME_': 'Grassland Mowing Events Raster (10m)',
    # Crop Types
    'CLMS_HRLVLCC_CTY_': 'Crop Types Raster (10m)',
    'CLMS_HRLVLCC_CTYCL_': 'Crop Types Confidence Layer Raster (10m)',
    # Cropping Patterns - Bare Soil
    'CLMS_HRLVLCC_CPBSA_': 'Bare Soil After Raster (10m)',
    'CLMS_HRLVLCC_CPBSACL_': 'Bare Soil After Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_CPBSB_': 'Bare Soil Before Raster (10m)',
    'CLMS_HRLVLCC_CPBSBCL_': 'Bare Soil Before Confidence Layer Raster (10m)',
    # Cropping Patterns - Cropping Seasons
    'CLMS_HRLVLCC_CPCST_': 'Cropping Seasons Types Raster (10m)',
    'CLMS_HRLVLCC_CPCSY_': 'Cropping Seasons Yearly Raster (10m)',
    # Cropping Patterns - Fallow Land
    'CLMS_HRLVLCC_CPFLD_': 'Fallow Land Duration Raster (10m)',
    'CLMS_HRLVLCC_CPFLDCL_': 'Fallow Land Duration Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_CPFLP_': 'Fallow Land Presence Raster (10m)',
    'CLMS_HRLVLCC_CPFLPCL_': 'Fallow Land Presence Confidence Layer Raster (10m)',
    # Cropping Patterns - Main Crop
    'CLMS_HRLVLCC_CPMCD_': 'Main Crop Duration Raster (10m)',
    'CLMS_HRLVLCC_CPMCDCL_': 'Main Crop Duration Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_CPMCE_': 'Main Crop Emergence Raster (10m)',
    'CLMS_HRLVLCC_CPMCECL_': 'Main Crop Emergence Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_CPMCH_': 'Main Crop Harvest Raster (10m)',
    'CLMS_HRLVLCC_CPMCHCL_': 'Main Crop Harvest Confidence Layer Raster (10m)',
    # Cropping Patterns - Secondary Crop
    'CLMS_HRLVLCC_CPSCD_': 'Secondary Crop Duration Raster (10m)',
    'CLMS_HRLVLCC_CPSCDCL_': 'Secondary Crop Duration Confidence Layer Raster (10m)',
    'CLMS_HRLVLCC_CPSCE_': 'Secondary Crop Emergence Raster (10m)',
    'CLMS_HRLVLCC_CPSCT_': 'Secondary Crop Types Raster (10m)',
    # CLCplus LULUCF Instance
    'CLMS_CLCPLUS_LULUCF-INSTANCE_': 'CLCplus LULUCF Instance Raster (100m)',
}


def get_asset_title(identifier: str) -> str:
    if identifier.startswith('CLMS_HRLVLCC_FTY_'):
        if '_R10m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_FTY_10m']
        if '_R100m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_FTY_100m']
    if identifier.startswith('CLMS_HRLVLCC_TCD_'):
        if '_R10m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_TCD_10m']
        if '_R100m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_TCD_100m']
    if identifier.startswith('CLMS_HRLVLCC_GRA_'):
        if '_R10m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_GRA_10m']
        if '_R100m_' in identifier:
            return ASSET_TITLES['CLMS_HRLVLCC_GRA_100m']
    for prefix, title in ASSET_TITLES.items():
        if identifier.startswith(prefix):
            return title
    raise KeyError(f'No asset title found for identifier {identifier!r}')


# ---------------------------------------------------------------------------
# Thumbnail (WMS GetMap) SLD per collection, mirroring the CDSE STAC.
#
# Each VLCC item gets a "thumbnail" asset: a WMS GetMap request against the
# thumbnails.dataspace rendering service with LAYERS pointing at the item's
# own data COG, styled by the collection's SLD from the
# copernicus-land/colourmaps-legends repo (path under colourmaps/, or None
# when production renders with the service default style).
#
# Only collections present here get a thumbnail.
# 'dominant-leaf-type-change' is currently an empty collection; its SLD is
# included to match its sibling layers once data is published.
# ---------------------------------------------------------------------------
VLCC_THUMBNAIL_SLD: dict[str, str | None] = {
    'clms_clcplus_lulucf-instance_europe_100m_yearly_v1': 'clms_clcplus_lulucf-instance/clms_clcplus_lulucf-instance_europe_100m_yearly_v1.sld',
    'clms_vlcc_bare-soil-after-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_bare-soil-after-confidence-layer/clms_vlcc_bare-soil-after-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_bare-soil-after_europe_10m_yearly_v1': 'clms_vlcc_bare-soil-after/clms_vlcc_bare-soil-after_europe_10m_yearly_v1.sld',
    'clms_vlcc_bare-soil-before-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_bare-soil-before-confidence-layer/clms_vlcc_bare-soil-before-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_bare-soil-before_europe_10m_yearly_v1': 'clms_vlcc_bare-soil-before/clms_vlcc_bare-soil-before_europe_10m_yearly_v1.sld',
    'clms_vlcc_broadleaved-cover-density_europe_100m_yearly_v1': 'clms_vlcc_broadleaved-cover-density/clms_vlcc_broadleaved-cover-density_europe_100m_yearly_v1.sld',
    'clms_vlcc_coniferous-cover-density_europe_100m_yearly_v1': None,
    'clms_vlcc_crop-types-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_crop-types-confidence-layer/clms_vlcc_crop-types-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_crop-types_europe_10m_yearly_v1': 'clms_vlcc_crop-types/clms_vlcc_crop-types_europe_10m_yearly_v1.sld',
    'clms_vlcc_cropping-seasons-types_europe_10m_yearly_v1': 'clms_vlcc_cropping-seasons-types/clms_vlcc_cropping-seasons-types_europe_10m_yearly_v1.sld',
    'clms_vlcc_cropping-seasons_europe_10m_yearly_v1': 'clms_vlcc_cropping-seasons/clms_vlcc_cropping-seasons_europe_10m_yearly_v1.sld',
    'clms_vlcc_dominant-leaf-type-change_europe_20m_3yearly_v1': 'clms_vlcc_dominant-leaf-type-change/clms_vlcc_dominant-leaf-type-change_europe_20m_3yearly_v1.sld',  # extrapolated (empty collection)
    'clms_vlcc_dominant-leaf-type-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_dominant-leaf-type-confidence-layer/clms_vlcc_dominant-leaf-type-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_dominant-leaf-type_europe_10m_yearly_v1': 'clms_vlcc_dominant-leaf-type/clms_vlcc_dominant-leaf-type_europe_10m_yearly_v1.sld',
    'clms_vlcc_fallow-land-duration-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_fallow-land-duration-confidence-layer/clms_vlcc_fallow-land-duration-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_fallow-land-duration_europe_10m_yearly_v1': 'clms_vlcc_fallow-land-duration/clms_vlcc_fallow-land-duration_europe_10m_yearly_v1.sld',
    'clms_vlcc_fallow-land-presence-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_fallow-land-presence-confidence-layer/clms_vlcc_fallow-land-presence-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_fallow-land-presence_europe_10m_yearly_v1': 'clms_vlcc_fallow-land-presence/clms_vlcc_fallow-land-presence_europe_10m_yearly_v1.sld',
    'clms_vlcc_forest-additional-support-layer_europe_10m_3yearly_v1': 'clms_vlcc_forest-additional-support-layer/clms_vlcc_forest-additional-support-layer_europe_10m_3yearly_v1.sld',
    'clms_vlcc_forest-type_europe_100m_3yearly_v1': 'clms_vlcc_forest-type/clms_vlcc_forest-type_europe_100m_3yearly_v1.sld',
    'clms_vlcc_forest-type_europe_10m_3yearly_v1': 'clms_vlcc_forest-type/clms_vlcc_forest-type_europe_10m_3yearly_v1.sld',
    'clms_vlcc_grassland-change-confidence-layer_europe_20m_3yearly_v1': 'clms_vlcc_grassland-change-confidence-layer/clms_vlcc_grassland-change-confidence-layer_europe_20m_3yearly_v1.sld',
    'clms_vlcc_grassland-change_europe_20m_3yearly_v1': 'clms_vlcc_grassland-change/clms_vlcc_grassland-change_europe_20m_3yearly_v1.sld',
    'clms_vlcc_grassland-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_grassland-confidence-layer/clms_vlcc_grassland-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_grassland-mowing-dates_europe_10m_yearly_v1': 'clms_vlcc_grassland-mowing-dates/clms_vlcc_grassland-mowing-dates_europe_10m_yearly_v1.sld',
    'clms_vlcc_grassland-mowing-events-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_grassland-mowing-events-confidence-layer/clms_vlcc_grassland-mowing-events-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_grassland-mowing-events_europe_10m_yearly_v1': 'clms_vlcc_grassland-mowing-events/clms_vlcc_grassland-mowing-events_europe_10m_yearly_v1.sld',
    'clms_vlcc_grassland_europe_100m_yearly_v1': 'clms_vlcc_grassland/clms_vlcc_grassland_europe_100m_yearly_v1.sld',
    'clms_vlcc_grassland_europe_10m_yearly_v1': 'clms_vlcc_grassland/clms_vlcc_grassland_europe_10m_yearly_v1.sld',
    'clms_vlcc_herbaceous-cover_europe_10m_yearly_v1': 'clms_vlcc_herbaceous-cover/clms_vlcc_herbaceous-cover_europe_10m_yearly_v1.sld',
    'clms_vlcc_main-crop-duration-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_main-crop-duration-confidence-layer/clms_vlcc_main-crop-duration-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_main-crop-duration_europe_10m_yearly_v1': 'clms_vlcc_main-crop-duration/clms_vlcc_main-crop-duration_europe_10m_yearly_v1.sld',
    'clms_vlcc_main-crop-emergence-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_main-crop-emergence-confidence-layer/clms_vlcc_main-crop-emergence-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_main-crop-emergence_europe_10m_yearly_v1': None,
    'clms_vlcc_main-crop-harvest-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_main-crop-harvest-confidence-layer/clms_vlcc_main-crop-harvest-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_main-crop-harvest_europe_10m_yearly_v1': None,
    'clms_vlcc_ploughing-indicator_europe_10m_yearly_v1': 'clms_vlcc_ploughing-indicator/clms_vlcc_ploughing-indicator_europe_10m_yearly_v1.sld',
    'clms_vlcc_secondary-crop-duration-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_secondary-crop-duration-confidence-layer/clms_vlcc_secondary-crop-duration-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_secondary-crop-duration_europe_10m_yearly_v1': 'clms_vlcc_secondary-crop-duration/clms_vlcc_secondary-crop-duration_europe_10m_yearly_v1.sld',
    'clms_vlcc_secondary-crop-emergence_europe_10m_yearly_v1': None,
    'clms_vlcc_secondary-crop-types_europe_10m_yearly_v1': 'clms_vlcc_secondary-crop-types/clms_vlcc_secondary-crop-types_europe_10m_yearly_v1.sld',
    'clms_vlcc_tree-cover-density-confidence-layer_europe_10m_yearly_v1': 'clms_vlcc_tree-cover-density-confidence-layer/clms_vlcc_tree-cover-density-confidence-layer_europe_10m_yearly_v1.sld',
    'clms_vlcc_tree-cover-density_europe_100m_yearly_v1': 'clms_vlcc_tree-cover-density/clms_vlcc_tree-cover-density_europe_100m_yearly_v1.sld',
    'clms_vlcc_tree-cover-density_europe_10m_yearly_v1': 'clms_vlcc_tree-cover-density/clms_vlcc_tree-cover-density_europe_10m_yearly_v1.sld',
    'clms_vlcc_tree-cover-presence-change-confidence-layer_europe_20m_3yearly_v1': 'clms_vlcc_tree-cover-presence-change-confidence-layer/clms_vlcc_tree-cover-presence-change-confidence-layer_europe_20m_3yearly_v1.sld',
    'clms_vlcc_tree-cover-presence-change_europe_20m_3yearly_v1': 'clms_vlcc_tree-cover-presence-change/clms_vlcc_tree-cover-presence-change_europe_20m_3yearly_v1.sld',
}
