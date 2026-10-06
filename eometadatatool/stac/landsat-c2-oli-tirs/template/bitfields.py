qa_bitfields = [
    {
        'name': 'fill',
        'description': 'Corresponding pixels in L1 image bands are fill',
        'offset': 0,
        'length': 1,
        'classes': [
            {
                'name': 'not_fill',
                'description': 'L1 image band pixels are not fill',
                'value': 0
            },
            {
                'name': 'fill',
                'description': 'L1 image band pixels are fill',
                'value': 1
            }
        ]
    },
    {
        'name': 'dilated',
        'description': 'Dilated cloud',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'name': 'not_dilated',
                'description': 'Cloud is not dilated or no cloud',
                'value': 0
            },
            {
                'name': 'dilated',
                'description': 'Cloud dilation',
                'value': 1
            }
        ]
    },
    {
        'name': 'cirrus',
        'description': 'Cirrus mask',
        'offset': 2,
        'length': 1,
        'classes': [
            {
                'name': 'not_cirrus',
                'description': 'No confidence level set or low confidence cirrus',
                'value': 0
            },
            {
                'name': 'cirrus',
                'description': 'High confidence cirrus',
                'value': 1
            }
        ]
    },
    {
        'name': 'cloud',
        'description': 'Cloud mask',
        'offset': 3,
        'length': 1,
        'classes': [
            {
                'name': 'not_cloud',
                'description': 'Cloud confidence is not high',
                'value': 0
            },
            {
                'name': 'cloud',
                'description': 'High confidence cloud',
                'value': 1
            }
        ]
    },
    {
        'name': 'shadow',
        'description': 'Cloud shadow mask',
        'offset': 4,
        'length': 1,
        'classes': [
            {
                'name': 'not_shadow',
                'description': 'Cloud shadow confidence is not high',
                'value': 0
            },
            {
                'name': 'shadow',
                'description': 'High confidence cloud shadow',
                'value': 1
            }
        ]
    },
    {
        'name': 'snow',
        'description': 'Snow/Ice mask',
        'offset': 5,
        'length': 1,
        'classes': [
            {
                'name': 'not_snow',
                'description': 'Snow/Ice confidence is not high',
                'value': 0
            },
            {
                'name': 'snow',
                'description': 'High confidence snow cover',
                'value': 1
            }
        ]
    },
    {
        'name': 'clear',
        'description': 'Cloud or dilated cloud bits set',
        'offset': 6,
        'length': 1,
        'classes': [
            {
                'name': 'not_clear',
                'description': 'Cloud or dilated cloud bits are set',
                'value': 0
            },
            {
                'name': 'clear',
                'description': 'Cloud and dilated cloud bits are not set',
                'value': 1
            }
        ]
    },
    {
        'name': 'water',
        'description': 'Water mask',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'name': 'not_water',
                'description': 'Land or cloud',
                'value': 0
            },
            {
                'name': 'water',
                'description': 'Water',
                'value': 1
            }
        ]
    },
    {
        'name': 'cloud_confidence',
        'description': 'Cloud confidence levels',
        'offset': 8,
        'length': 2,
        'classes': [
            {
                'name': 'not_set',
                'description': 'No confidence level set',
                'value': 0
            },
            {
                'name': 'low',
                'description': 'Low confidence cloud',
                'value': 1
            },
            {
                'name': 'medium',
                'description': 'Medium confidence cloud',
                'value': 2
            },
            {
                'name': 'high',
                'description': 'High confidence cloud',
                'value': 3
            }
        ]
    },
    {
        'name': 'shadow_confidence',
        'description': 'Cloud shadow confidence levels',
        'offset': 10,
        'length': 2,
        'classes': [
            {
                'name': 'not_set',
                'description': 'No confidence level set',
                'value': 0
            },
            {
                'name': 'low',
                'description': 'Low confidence cloud shadow',
                'value': 1
            },
            {
                'name': 'reserved',
                'description': 'Reserved - value not used',
                'value': 2
            },
            {
                'name': 'high',
                'description': 'High confidence cloud shadow',
                'value': 3
            }
        ]
    },
    {
        'name': 'snow_confidence',
        'description': 'Snow/Ice confidence levels',
        'offset': 12,
        'length': 2,
        'classes': [
            {
                'name': 'not_set',
                'description': 'No confidence level set',
                'value': 0
            },
            {
                'name': 'low',
                'description': 'Low confidence snow/ice',
                'value': 1
            },
            {
                'name': 'reserved',
                'description': 'Reserved - value not used',
                'value': 2
            },
            {
                'name': 'high',
                'description': 'High confidence snow/ice',
                'value': 3
            }
        ]
    },
    {
        'name': 'cirrus_confidence',
        'description': 'Cirrus confidence levels',
        'offset': 14,
        'length': 2,
        'classes': [
            {
                'name': 'not_set',
                'description': 'No confidence level set',
                'value': 0
            },
            {
                'name': 'low',
                'description': 'Low confidence cirrus',
                'value': 1
            },
            {
                'name': 'reserved',
                'description': 'Reserved - value not used',
                'value': 2
            },
            {
                'name': 'high',
                'description': 'High confidence cirrus',
                'value': 3
            }
        ]
    }
]

radsat_bitfields = [
    {
        'name': 'band1',
        'description': 'Band 1 radiometric saturation',
        'offset': 0,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 1 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 1 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band2',
        'description': 'Band 2 radiometric saturation',
        'offset': 1,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 2 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 2 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band3',
        'description': 'Band 3 radiometric saturation',
        'offset': 2,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 3 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 3 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band4',
        'description': 'Band 4 radiometric saturation',
        'offset': 3,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 4 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 4 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band5',
        'description': 'Band 5 radiometric saturation',
        'offset': 4,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 5 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 5 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band6',
        'description': 'Band 6 radiometric saturation',
        'offset': 5,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 6 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 6 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'band7',
        'description': 'Band 7 radiometric saturation',
        'offset': 6,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 7 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 7 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 7,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'band9',
        'description': 'Band 9 radiometric saturation',
        'offset': 8,
        'length': 1,
        'classes': [
            {
                'name': 'not_saturated',
                'description': 'Band 9 is not saturated',
                'value': 0
            },
            {
                'name': 'saturated',
                'description': 'Band 9 is saturated',
                'value': 1
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 9,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 10,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'occlusion',
        'description': 'Terrain not visible from sensor due to intervening terrain',
        'offset': 11,
        'length': 1,
        'classes': [
            {
                'name': 'not_occluded',
                'description': 'Terrain is not occluded',
                'value': 0
            },
            {
                'name': 'occluded',
                'description': 'Terrain is occluded',
                'value': 1
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 12,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 13,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 14,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    },
    {
        'name': 'unused',
        'description': 'Unused bit',
        'offset': 15,
        'length': 1,
        'classes': [
            {
                'name': 'unused',
                'description': 'Unused bit',
                'value': 0
            }
        ]
    }
]
