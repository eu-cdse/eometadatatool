from collections.abc import Collection, Mapping, Sequence
from typing import NotRequired, TypedDict

EOBand = TypedDict(
    'EOBand',
    {
        'name': str,
        'description': str,
        'eo:center_wavelength': float,
        'eo:full_width_half_max': float,
        'eo:common_name': NotRequired[str],
    },
)

SARBand = TypedDict(
    'SARBand',
    {
        'description': str,
        'sar:frequency_band': str,
        'sar:center_frequency': float,
        'sar:bandwidth': float,
    },
)

CCMBand = TypedDict(
    'CCMBand',
    {
        'name': str,
        'nodata': int,
        'unit': str,
        'eo:common_name': str,
        'eo:center_wavelength': float,
        'eo:full_width_half_max': float,
        'raster:bits_per_sample': int,
        'raster:spatial_resolution': float,
    },
)


class SARPol(TypedDict):
    title: str
    description: str


class SARAsset(TypedDict):
    name: str
    short_name: str
    title: str
    description: str


type STACBand = EOBand | SARBand | CCMBand | SARPol | SARAsset


def generate_bands[T: STACBand](
    band_mapping: Mapping[str, T],
    band_names: Collection[str] | None,
) -> Sequence[T]:
    """Filter bands by name. If band_names is None, return all bands."""
    if band_names is None:
        return list(band_mapping.values())
    return [band_mapping[name] for name in band_names]


OLCI_Bands: Mapping[str, EOBand] = {
    'Oa01': {
        'name': 'Oa01',
        'description': 'Aerosol correction, improved water constituent retrieval',
        'eo:center_wavelength': 0.4,
        'eo:full_width_half_max': 0.015,
    },
    'Oa02': {
        'name': 'Oa02',
        'description': 'Yellow substance and detrital pigments (turbidity)',
        'eo:center_wavelength': 0.4125,
        'eo:full_width_half_max': 0.01,
    },
    'Oa03': {
        'name': 'Oa03',
        'description': 'Chlorophyll absorption maximum, biogeochemistry, vegetation',
        'eo:center_wavelength': 0.4425,
        'eo:full_width_half_max': 0.01,
    },
    'Oa04': {
        'name': 'Oa04',
        'description': 'Chlorophyll',
        'eo:center_wavelength': 0.49,
        'eo:full_width_half_max': 0.01,
    },
    'Oa05': {
        'name': 'Oa05',
        'description': 'Chlorophyll, sediment, turbidity, red tide',
        'eo:center_wavelength': 0.51,
        'eo:full_width_half_max': 0.01,
    },
    'Oa06': {
        'name': 'Oa06',
        'description': 'Chlorophyll reference (minimum)',
        'eo:center_wavelength': 0.56,
        'eo:full_width_half_max': 0.01,
    },
    'Oa07': {
        'name': 'Oa07',
        'description': 'Sediment loading',
        'eo:center_wavelength': 0.62,
        'eo:full_width_half_max': 0.01,
    },
    'Oa08': {
        'name': 'Oa08',
        'description': '2nd Chlorophyll absorption maximum, sediment, yellow substance / vegetation',
        'eo:center_wavelength': 0.665,
        'eo:full_width_half_max': 0.01,
    },
    'Oa09': {
        'name': 'Oa09',
        'description': 'Improved fluorescence retrieval',
        'eo:center_wavelength': 0.67375,
        'eo:full_width_half_max': 0.0075,
    },
    'Oa10': {
        'name': 'Oa10',
        'description': 'Chlorophyll fluorescence peak, red edge',
        'eo:center_wavelength': 0.68125,
        'eo:full_width_half_max': 0.0075,
    },
    'Oa11': {
        'name': 'Oa11',
        'description': 'Chlorophyll fluorescence baseline, red edge transition',
        'eo:center_wavelength': 0.70875,
        'eo:full_width_half_max': 0.01,
    },
    'Oa12': {
        'name': 'Oa12',
        'description': 'O2 absorption / clouds, vegetation',
        'eo:center_wavelength': 0.75375,
        'eo:full_width_half_max': 0.0075,
    },
    'Oa13': {
        'name': 'Oa13',
        'description': 'O2 absorption / aerosol correction',
        'eo:center_wavelength': 0.76125,
        'eo:full_width_half_max': 0.0025,
    },
    'Oa14': {
        'name': 'Oa14',
        'description': 'Atmospheric correction',
        'eo:center_wavelength': 0.764375,
        'eo:full_width_half_max': 0.00375,
    },
    'Oa15': {
        'name': 'Oa15',
        'description': 'O2 absorption used for cloud top pressure, fluorescence over land',
        'eo:center_wavelength': 0.7675,
        'eo:full_width_half_max': 0.0025,
    },
    'Oa16': {
        'name': 'Oa16',
        'description': 'Atmospheric / aerosol correction',
        'eo:center_wavelength': 0.77875,
        'eo:full_width_half_max': 0.015,
    },
    'Oa17': {
        'name': 'Oa17',
        'description': 'Atmospheric / aerosol correction, clouds, pixel co-registration',
        'eo:center_wavelength': 0.865,
        'eo:full_width_half_max': 0.02,
    },
    'Oa18': {
        'name': 'Oa18',
        'description': 'Water vapour absorption reference. Common reference band with SLSTR. Vegetation monitoring',
        'eo:center_wavelength': 0.885,
        'eo:full_width_half_max': 0.01,
    },
    'Oa19': {
        'name': 'Oa19',
        'description': 'Water vapour absorption, vegetation monitoring (maximum REFLECTANCE)',
        'eo:center_wavelength': 0.9,
        'eo:full_width_half_max': 0.01,
    },
    'Oa20': {
        'name': 'Oa20',
        'description': 'Water vapour absorption, atmospheric / aerosol correction',
        'eo:center_wavelength': 0.94,
        'eo:full_width_half_max': 0.02,
    },
    'Oa21': {
        'name': 'Oa21',
        'description': 'Water vapour absorption, atmospheric / aerosol correction',
        'eo:center_wavelength': 1.02,
        'eo:full_width_half_max': 0.04,
    },
}

SLSTR_Bands: Mapping[str, EOBand] = {
    'S1': {
        'name': 'S1',
        'description': 'Cloud screening, vegetation monitoring, aerosol',
        'eo:center_wavelength': 0.55427,
        'eo:full_width_half_max': 0.01926,
    },
    'S2': {
        'name': 'S2',
        'description': 'NDVI, vegetation monitoring, aerosol',
        'eo:center_wavelength': 0.65947,
        'eo:full_width_half_max': 0.01925,
    },
    'S3': {
        'name': 'S3',
        'description': 'NDVI, cloud flagging, pixel co-registration',
        'eo:center_wavelength': 0.868,
        'eo:full_width_half_max': 0.0206,
    },
    'S4': {
        'name': 'S4',
        'description': 'Cirrus detection over land',
        'eo:center_wavelength': 1.3748,
        'eo:full_width_half_max': 0.0208,
    },
    'S5': {
        'name': 'S5',
        'description': 'Cloud clearing, ice, snow, vegetation monitoring',
        'eo:center_wavelength': 1.6134,
        'eo:full_width_half_max': 0.06068,
    },
    'S6': {
        'name': 'S6',
        'description': 'Vegetation state and cloud clearing',
        'eo:center_wavelength': 2.2557,
        'eo:full_width_half_max': 0.05015,
    },
    'S7': {
        'name': 'S7',
        'description': 'SST, LST, Active fire',
        'eo:center_wavelength': 3.742,
        'eo:full_width_half_max': 0.398,
    },
    'S8': {
        'name': 'S8',
        'description': 'SST, LST, Active fire',
        'eo:center_wavelength': 10.854,
        'eo:full_width_half_max': 0.776,
    },
    'S9': {
        'name': 'S9',
        'description': 'SST, LST',
        'eo:center_wavelength': 12.0225,
        'eo:full_width_half_max': 0.905,
    },
    'F1': {
        'name': 'F1',
        'description': 'Active fire',
        'eo:center_wavelength': 3.742,
        'eo:full_width_half_max': 0.398,
    },
    'F2': {
        'name': 'F2',
        'description': 'Active fire',
        'eo:center_wavelength': 10.854,
        'eo:full_width_half_max': 0.776,
    },
}

SRAL_Bands: Mapping[str, SARBand] = {
    'C': {
        'description': 'Ionospheric correction',
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.409999872,
        'sar:bandwidth': 0.29,
    },
    'Ku': {
        'description': 'Range measurements',
        'sar:frequency_band': 'Ku',
        'sar:center_frequency': 13.575000064,
        'sar:bandwidth': 0.32,
    },
}

SYN_AOD_Bands: Mapping[str, EOBand] = {
    'SYN_440': {
        'name': 'SYN_440',
        'description': 'OLCI channel Oa03',
        'eo:center_wavelength': 0.4425,
        'eo:full_width_half_max': 0.01,
    },
    'SYN_550': {
        'name': 'SYN_550',
        'description': 'SLSTR nadir and oblique channel S1',
        'eo:center_wavelength': 0.55,
        'eo:full_width_half_max': 0.02,
    },
    'SYN_670': {
        'name': 'SYN_670',
        'description': 'SLSTR nadir and oblique channel S2',
        'eo:center_wavelength': 0.659,
        'eo:full_width_half_max': 0.02,
    },
    'SYN_865': {
        'name': 'SYN_865',
        'description': 'OLCI channel Oa17, SLSTR nadir and oblique channel S2',
        'eo:center_wavelength': 0.865,
        'eo:full_width_half_max': 0.02,
    },
    'SYN_1600': {
        'name': 'SYN_1600',
        'description': 'SLSTR nadir and oblique channel S5',
        'eo:center_wavelength': 1.61,
        'eo:full_width_half_max': 0.06,
    },
    'SYN_2250': {
        'name': 'SYN_2250',
        'description': 'SLSTR nadir and oblique channel S6',
        'eo:center_wavelength': 2.25,
        'eo:full_width_half_max': 0.05,
    },
}

SYN_VGT_Bands: Mapping[str, EOBand] = {
    'B0': {
        'name': 'B0',
        'description': 'OLCI channels Oa02, Oa03',
        'eo:center_wavelength': 0.45,
        'eo:full_width_half_max': 0.02,
    },
    'B2': {
        'name': 'B2',
        'description': 'OLCI channels Oa06, Oa07, Oa08, Oa09, Oa10',
        'eo:center_wavelength': 0.645,
        'eo:full_width_half_max': 0.035,
    },
    'B3': {
        'name': 'B3',
        'description': 'OLCI channels Oa16, Oa17, Oa18, Oa21',
        'eo:center_wavelength': 0.835,
        'eo:full_width_half_max': 0.055,
    },
    'MIR': {
        'name': 'MIR',
        'description': 'SLSTR nadir and oblique channels S5, S6',
        'eo:center_wavelength': 1.665,
        'eo:full_width_half_max': 0.085,
    },
}

S2_Bands: Mapping[str, EOBand] = {
    'B01': {
        'name': 'B01',
        'description': 'Coastal aerosol (band 1)',
        'eo:center_wavelength': 0.443,
        'eo:full_width_half_max': 0.228,
        'eo:common_name': 'coastal',
    },
    'B02': {
        'name': 'B02',
        'description': 'Blue (band 2)',
        'eo:center_wavelength': 0.493,
        'eo:full_width_half_max': 0.267,
        'eo:common_name': 'blue',
    },
    'B03': {
        'name': 'B03',
        'description': 'Green (band 3)',
        'eo:center_wavelength': 0.560,
        'eo:full_width_half_max': 0.291,
        'eo:common_name': 'green',
    },
    'B04': {
        'name': 'B04',
        'description': 'Red (band 4)',
        'eo:center_wavelength': 0.665,
        'eo:full_width_half_max': 0.342,
        'eo:common_name': 'red',
    },
    'B05': {
        'name': 'B05',
        'description': 'Red edge 1 (band 5)',
        'eo:center_wavelength': 0.704,
        'eo:full_width_half_max': 0.357,
        'eo:common_name': 'rededge071',
    },
    'B06': {
        'name': 'B06',
        'description': 'Red edge 2 (band 6)',
        'eo:center_wavelength': 0.741,
        'eo:full_width_half_max': 0.374,
        'eo:common_name': 'rededge075',
    },
    'B07': {
        'name': 'B07',
        'description': 'Red edge 3 (band 7)',
        'eo:center_wavelength': 0.783,
        'eo:full_width_half_max': 0.399,
        'eo:common_name': 'rededge078',
    },
    'B08': {
        'name': 'B08',
        'description': 'NIR 1 (band 8)',
        'eo:center_wavelength': 0.833,
        'eo:full_width_half_max': 0.454,
        'eo:common_name': 'nir',
    },
    'B8A': {
        'name': 'B8A',
        'description': 'NIR 2 (band 8A)',
        'eo:center_wavelength': 0.865,
        'eo:full_width_half_max': 0.441,
        'eo:common_name': 'nir08',
    },
    'B09': {
        'name': 'B09',
        'description': 'NIR 3 (band 9)',
        'eo:center_wavelength': 0.945,
        'eo:full_width_half_max': 0.479,
        'eo:common_name': 'nir09',
    },
    'B10': {
        'name': 'B10',
        'description': 'Cirrus (band 10)',
        'eo:center_wavelength': 1.377,
        'eo:full_width_half_max': 0.706,
        'eo:common_name': 'cirrus',
    },
    'B11': {
        'name': 'B11',
        'description': 'SWIR 1 (band 11)',
        'eo:center_wavelength': 1.614,
        'eo:full_width_half_max': 0.841,
        'eo:common_name': 'swir16',
    },
    'B12': {
        'name': 'B12',
        'description': 'SWIR 2 (band 12)',
        'eo:center_wavelength': 2.202,
        'eo:full_width_half_max': 1.160,
        'eo:common_name': 'swir22',
    },
}

S1_Pols: Mapping[str, SARPol] = {
    'VV': {
        'title': 'VV: Vertical transmit, vertical receive',
        'description': 'Amplitude of vertically polarized signal received vertically.',
    },
    'VH': {
        'title': 'VH: Vertical transmit, horizontal receive',
        'description': 'Amplitude of vertically polarized signal received horizontally.',
    },
    'HH': {
        'title': 'HH: Horizontal transmit, horizontal receive',
        'description': 'Amplitude of horizontally polarized signal received horizontally.',
    },
    'HV': {
        'title': 'HV: Horizontal transmit, horizontal receive',
        'description': 'Amplitude of horizontally polarized signal received vertically.',
    },
}

S1_Assets: Mapping[str, SARAsset] = {
    'schema-product': {
        'name': 'schema-product',
        'short_name': 'product',
        'title': 'product Schema',
        'description': "Main source of band's metadata, including: state of the platform during acquisition, image properties, Doppler information, geographic location, etc.",
    },
    'schema-calibration': {
        'name': 'schema-calibration',
        'short_name': 'calibration',
        'title': 'calibration Schema',
        'description': 'Calibration metadata including calibration details and lookup tables for beta nought, sigma nought, gamma, and digital numbers used in absolute product calibration.',
    },
    'schema-noise': {
        'name': 'schema-noise',
        'short_name': 'noises',
        'title': 'noise Schema',
        'description': 'Estimated thermal noise look-up tables.',
    },
}

S5P_Bands: Mapping[str, EOBand] = {
    'RA-BD1': {
        'name': 'BD1',
        'description': 'Band 1 (UV)',
        'eo:center_wavelength': 0.285,
        'eo:full_width_half_max': 0.030,
    },
    'RA-BD2': {
        'name': 'BD2',
        'description': 'Band 2 (UV)',
        'eo:center_wavelength': 0.310,
        'eo:full_width_half_max': 0.020,
    },
    'RA-BD3': {
        'name': 'BD3',
        'description': 'Band 3 (UVIS)',
        'eo:center_wavelength': 0.3625,
        'eo:full_width_half_max': 0.085,
    },
    'RA-BD4': {
        'name': 'BD4',
        'description': 'Band 4 (UVIS)',
        'eo:center_wavelength': 0.4525,
        'eo:full_width_half_max': 0.095,
    },
    'RA-BD5': {
        'name': 'BD5',
        'description': 'Band 5 (NIR)',
        'eo:center_wavelength': 0.700,
        'eo:full_width_half_max': 0.050,
    },
    'RA-BD6': {
        'name': 'BD6',
        'description': 'Band 6 (NIR)',
        'eo:center_wavelength': 0.750,
        'eo:full_width_half_max': 0.050,
    },
    'RA-BD7': {
        'name': 'BD7',
        'description': 'Band 7 (SWIR)',
        'eo:center_wavelength': 2.325,
        'eo:full_width_half_max': 0.040,
    },
    'RA-BD8': {
        'name': 'BD8',
        'description': 'Band 8 (SWIR)',
        'eo:center_wavelength': 2.365,
        'eo:full_width_half_max': 0.040,
    },
}

CCM_AIS_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.489,
        'eo:full_width_half_max': 0.086,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.559,
        'eo:full_width_half_max': 0.094,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.668,
        'eo:full_width_half_max': 0.070,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.844,
        'eo:full_width_half_max': 0.176,
    },
}
CCM_DOV_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.487,
        'eo:full_width_half_max': 0.073,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.541,
        'eo:full_width_half_max': 0.104,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.631,
        'eo:full_width_half_max': 0.094,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.813,
        'eo:full_width_half_max': 0.098,
    },
}
CCM_GIS_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.480,
        'eo:full_width_half_max': 0.060,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.545,
        'eo:full_width_half_max': 0.070,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.672,
        'eo:full_width_half_max': 0.035,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.850,
        'eo:full_width_half_max': 0.140,
    },
}
CCM_HRS_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.496,
        'eo:full_width_half_max': 0.059,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.566,
        'eo:full_width_half_max': 0.067,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.668,
        'eo:full_width_half_max': 0.057,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.831,
        'eo:full_width_half_max': 0.122,
    },
}
CCM_NAO_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'B0',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.487,
        'eo:full_width_half_max': 0.071,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'B1',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.557,
        'eo:full_width_half_max': 0.067,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'B2',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.659,
        'eo:full_width_half_max': 0.077,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'B3',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.819,
        'eo:full_width_half_max': 0.133,
    },
}
CCM_OPT_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.485,
        'eo:full_width_half_max': 0.070,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.555,
        'eo:full_width_half_max': 0.070,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.660,
        'eo:full_width_half_max': 0.060,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.830,
        'eo:full_width_half_max': 0.120,
    },
}

CCM_PHR_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'B0',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.490,
        'eo:full_width_half_max': 0.120,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'B1',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.555,
        'eo:full_width_half_max': 0.130,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'B2',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.660,
        'eo:full_width_half_max': 0.140,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'B3',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.845,
        'eo:full_width_half_max': 0.210,
    },
}

CCM_S14_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.475,
        'eo:full_width_half_max': 0.070,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.550,
        'eo:full_width_half_max': 0.080,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.635,
        'eo:full_width_half_max': 0.070,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.835,
        'eo:full_width_half_max': 0.150,
    },
}


CCM_VHI_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.475,
        'eo:full_width_half_max': 0.070,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.550,
        'eo:full_width_half_max': 0.080,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.635,
        'eo:full_width_half_max': 0.070,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 4.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.835,
        'eo:full_width_half_max': 0.150,
    },
}
CCM_WV2_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.480,
        'eo:full_width_half_max': 0.060,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.545,
        'eo:full_width_half_max': 0.070,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.660,
        'eo:full_width_half_max': 0.060,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.833,
        'eo:full_width_half_max': 0.125,
    },
}
CCM_WV3_Bands: Mapping[str, CCMBand] = {
    'BLUE': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'BLUE',
        'eo:common_name': 'blue',
        'eo:center_wavelength': 0.481,
        'eo:full_width_half_max': 0.072,
    },
    'GREEN': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'GREEN',
        'eo:common_name': 'green',
        'eo:center_wavelength': 0.546,
        'eo:full_width_half_max': 0.079,
    },
    'RED': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'RED',
        'eo:common_name': 'red',
        'eo:center_wavelength': 0.661,
        'eo:full_width_half_max': 0.070,
    },
    'NIR': {
        'nodata': 0,
        'unit': 'µm',
        'raster:bits_per_sample': 16,
        'raster:spatial_resolution': 2.0,
        'name': 'NIR',
        'eo:common_name': 'nir',
        'eo:center_wavelength': 0.797,
        'eo:full_width_half_max': 0.203,
    },
}

Poseidon_Bands: Mapping[str, SARBand] = {
    'C': {
        'description': 'Ionospheric correction and surface roughness estimation',
        'sar:frequency_band': 'C',
        'sar:center_frequency': 5.41,
        'sar:bandwidth': 0.32,
    },
    'Ku': {
        'description': 'Primary altimetric measurements',
        'sar:frequency_band': 'Ku',
        'sar:center_frequency': 13.575,
        'sar:bandwidth': 0.32,
    },
}

AMR_Bands: Mapping[str, EOBand] = {
    'band1': {
        'name': 'band1',
        'description': 'AMR-C Band 1 at 18.7 GHz with 200 MHz bandwidth',
        'eo:center_wavelength': 16031.682,
        'eo:full_width_half_max': 171.462,
    },
    'band2': {
        'name': 'band2',
        'description': 'AMR-C Band 2 at 23.8 GHz with 400 MHz bandwidth',
        'eo:center_wavelength': 12596.322,
        'eo:full_width_half_max': 211.703,
    },
    'band3': {
        'name': 'band3',
        'description': 'AMR-C Band 3 at 34.0 GHz with 700 MHz bandwidth',
        'eo:center_wavelength': 8817.425,
        'eo:full_width_half_max': 181.535,
    },
}

LANDSAT_MOSAIC_Bands: Mapping[str, EOBand] = {
    'B01': {
        'name': 'B01',
        'description': 'Blue',
        'eo:center_wavelength': 0.482,
        'eo:full_width_half_max': 0.060,
        'eo:common_name': 'blue',
    },
    'B02': {
        'name': 'B02',
        'description': 'Green',
        'eo:center_wavelength': 0.561,
        'eo:full_width_half_max': 0.057,
        'eo:common_name': 'green',
    },
    'B03': {
        'name': 'B03',
        'description': 'Red',
        'eo:center_wavelength': 0.655,
        'eo:full_width_half_max': 0.037,
        'eo:common_name': 'red',
    },
    'B04': {
        'name': 'B04',
        'description': 'Near Infrared',
        'eo:center_wavelength': 0.865,
        'eo:full_width_half_max': 0.028,
        'eo:common_name': 'nir08',
    },
    'B05': {
        'name': 'B05',
        'description': 'Short-wave Infrared 1.6',
        'eo:center_wavelength': 1.609,
        'eo:full_width_half_max': 0.085,
        'eo:common_name': 'swir16',
    },
    'B06': {
        'name': 'B06',
        'description': 'Short-wave Infrared 2.2',
        'eo:center_wavelength': 2.201,
        'eo:full_width_half_max': 0.187,
        'eo:common_name': 'swir22',
    },
    'B07': {
        'name': 'B07',
        'description': 'Thermal',
        'eo:center_wavelength': 12.005,
        'eo:full_width_half_max': 1.010,
        'eo:common_name': 'lwir12',
    }
}
