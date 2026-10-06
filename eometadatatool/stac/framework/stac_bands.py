from collections.abc import Collection, Mapping, Sequence
from typing import NotRequired, TypedDict, Final

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

class S2Asset(TypedDict):
    name: str
    description: str

class MODISBand(TypedDict):
    name: str
    description: str
    common_name: NotRequired[str]


type STACBand = EOBand | SARBand | CCMBand | SARPol | SARAsset | S2Asset | MODISBand


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

S2_NS_Bands: Mapping[str, S2Asset] = {
    'AOT': {
        'name': 'AOT',
        'description': 'Aerosol optical thickness',
    },
    'WVP': {
        'name': 'WVP',
        'description': 'Water vapour',
    },
    'CLD': {
        'name': 'CLD',
        'description': 'Cloud probability',
    },
    'SNW': {
        'name': 'SNW',
        'description': 'Snow probability',
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

S1_OCN: Mapping[str, SARPol] = {
    'VV': {
        'title': 'OCN Measurement Data (VV)',
        'description': 'Level-2 Ocean Product measurement file containing Ocean Wind Field Component (OWI) and Radial Surface Velocity Component (RVL).',
    },
    'VH': {
        'title': 'OCN Measurement Data (VH)',
        'description': 'Level-2 Ocean Product measurement file containing Ocean Wind Field Component (OWI) and Radial Surface Velocity Component (RVL).',
    },
    'HH': {
        'title': 'OCN Measurement Data (HH)',
        'description': 'Level-2 Ocean Product measurement file containing Ocean Wind Field Component (OWI) and Radial Surface Velocity Component (RVL).',
    },
    'HV': {
        'title': 'OCN Measurement Data (HV)',
        'description': 'Level-2 Ocean Product measurement file containing Ocean Wind Field Component (OWI) and Radial Surface Velocity Component (RVL).',
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

LANDSAT_5_7_B1: EOBand = {
    'name': 'B1',
    'description': 'Blue (band 1)',
    'eo:center_wavelength': 0.485,
    'eo:full_width_half_max': 0.07,
    'eo:common_name': 'blue',
}
LANDSAT_5_7_B2: EOBand = {
    'name': 'B2',
    'description': 'Green (band 2)',
    'eo:center_wavelength': 0.56,
    'eo:full_width_half_max': 0.08,
    'eo:common_name': 'green',
}
LANDSAT_5_7_B3: EOBand = {
    'name': 'B3',
    'description': 'Red (band 3)',
    'eo:center_wavelength': 0.66,
    'eo:full_width_half_max': 0.06,
    'eo:common_name': 'red',
}
LANDSAT_5_7_B5: EOBand = {
    'name': 'B5',
    'description': 'Short-wave Infrared 1.6 (band 5)',
    'eo:center_wavelength': 1.65,
    'eo:full_width_half_max': 0.2,
    'eo:common_name': 'swir16',
}
LANDSAT_5_7_B6: EOBand = {
    'name': 'B6',
    'description': 'Long-wave Infrared (band 6)',
    'eo:center_wavelength': 11.45,
    'eo:full_width_half_max': 2.1,
    'eo:common_name': 'lwir',
}
LANDSAT_5_7_B7: EOBand = {
    'name': 'B7',
    'description': 'Short-wave Infrared 2.2 (band 7)',
    'eo:center_wavelength': 2.215,
    'eo:full_width_half_max': 0.27,
    'eo:common_name': 'swir22',
}

LANDSAT_5_Bands: Mapping[str, EOBand] = {
    'B1': LANDSAT_5_7_B1,
    'B2': LANDSAT_5_7_B2,
    'B3': LANDSAT_5_7_B3,
    'B4': {
        'name': 'B4',
        'description': 'Near Infrared (band 4)',
        'eo:center_wavelength': 0.83,
        'eo:full_width_half_max': 0.14,
        'eo:common_name': 'nir',
    },
    'B5': LANDSAT_5_7_B5,
    'B6': LANDSAT_5_7_B6,
    'B7': LANDSAT_5_7_B7,
}

LANDSAT_7_B4: EOBand = {
    'name': 'B4',
    'description': 'Near Infrared (band 4)',
    'eo:center_wavelength': 0.835,
    'eo:full_width_half_max': 0.13,
    'eo:common_name': 'nir',
}
LANDSAT_7_B8: EOBand = {
    'name': 'B8',
    'description': 'Panchromatic (band 8)',
    'eo:center_wavelength': 0.71,
    'eo:full_width_half_max': 0.38,
    'eo:common_name': 'pan',
}

LANDSAT_7_Bands: Mapping[str, EOBand] = {
    'B1': LANDSAT_5_7_B1,
    'B2': LANDSAT_5_7_B2,
    'B3': LANDSAT_5_7_B3,
    'B4': LANDSAT_7_B4,
    'B5': LANDSAT_5_7_B5,
    'B6': LANDSAT_5_7_B6,
    'B7': LANDSAT_5_7_B7,
    'B8': LANDSAT_7_B8,
}

LANDSAT_7_B6_VCID_1: EOBand = LANDSAT_5_7_B6.copy()
LANDSAT_7_B6_VCID_1.update({
    'description': 'Long-wave Infrared (band 6) - VCD 1: Low Gain',
})
LANDSAT_7_B6_VCID_2: EOBand = LANDSAT_5_7_B6.copy()
LANDSAT_7_B6_VCID_2.update({
    'description': 'Long-wave Infrared (band 6) - VCD 2: High Gain',
})

LANDSAT_7_Bands_VCID: Mapping[str, EOBand] = {
    'B1': LANDSAT_5_7_B1,
    'B2': LANDSAT_5_7_B2,
    'B3': LANDSAT_5_7_B3,
    'B4': LANDSAT_7_B4,
    'B5': LANDSAT_5_7_B5,
    'B6_VCID_1': LANDSAT_7_B6_VCID_1,
    'B6_VCID_2': LANDSAT_7_B6_VCID_2,
    'B7': LANDSAT_5_7_B7,
    'B8': LANDSAT_7_B8,
}

# 1-9 L1 OLI
# 10-11 L1 TIRS
# 1-11 L1 OLI TIRS
# 1-7 L2 OLI TIRS

LANDSAT_C2_OLI_TIRS_Bands: Mapping[str, EOBand] = {
    'B1': {
        'name': 'B1',
        'description': 'Coastal aerosol (band 1)',
        'eo:center_wavelength': 0.443,
        'eo:full_width_half_max': 0.016,
        'eo:common_name': 'coastal',
    },
    'B2': {
        'name': 'B2',
        'description': 'Blue (band 2)',
        'eo:center_wavelength': 0.482,
        'eo:full_width_half_max': 0.060,
        'eo:common_name': 'blue',
    },
    'B3': {
        'name': 'B3',
        'description': 'Green (band 3)',
        'eo:center_wavelength': 0.561,
        'eo:full_width_half_max': 0.057,
        'eo:common_name': 'green',
    },
    'B4': {
        'name': 'B4',
        'description': 'Red (band 4)',
        'eo:center_wavelength': 0.655,
        'eo:full_width_half_max': 0.037,
        'eo:common_name': 'red',
    },
    'B5': {
        'name': 'B5',
        'description': 'Near Infrared (band 5)',
        'eo:center_wavelength': 0.865,
        'eo:full_width_half_max': 0.028,
        'eo:common_name': 'nir08',
    },
    'B6': {
        'name': 'B6',
        'description': 'Short-wave Infrared 1.6 (band 6)',
        'eo:center_wavelength': 1.609,
        'eo:full_width_half_max': 0.085,
        'eo:common_name': 'swir16',
    },
    'B7': {
        'name': 'B7',
        'description': 'Short-wave Infrared 2.2 (band 7)',
        'eo:center_wavelength': 2.201,
        'eo:full_width_half_max': 0.187,
        'eo:common_name': 'swir22',
    },
    'B8': {
        'name': 'B8',
        'description': 'Panchromatic (band 8)',
        'eo:center_wavelength': 0.590,
        'eo:full_width_half_max': 0.172,
        'eo:common_name': 'pan',
    },
    'B9': {
        'name': 'B9',
        'description': 'Cirrus (band 9)',
        'eo:center_wavelength': 1.373,
        'eo:full_width_half_max': 0.020,
        'eo:common_name': 'cirrus',
    },
    'B10': {
        'name': 'B10',
        'description': 'Thermal Infrared 10.9 (band 10)',
        'eo:center_wavelength': 10.895,
        'eo:full_width_half_max': 0.590,
        'eo:common_name': 'lwir11',
    },
    'B11': {
        'name': 'B11',
        'description': 'Thermal Infrared 12.0 (band 11)',
        'eo:center_wavelength': 12.005,
        'eo:full_width_half_max': 1.010,
        'eo:common_name': 'lwir12',
    }
}

MCD12Q1_Bands: Mapping[str, MODISBand] = {
    "LC_Type1": {"name": "LC_Type1", "description": "Land_Cover_Type_1"},
    "LC_Type2": {"name": "LC_Type2", "description": "Land_Cover_Type_2"},
    "LC_Type3": {"name": "LC_Type3", "description": "Land_Cover_Type_3"},
    "LC_Type4": {"name": "LC_Type4", "description": "Land_Cover_Type_4"},
    "LC_Type5": {"name": "LC_Type5", "description": "Land_Cover_Type_5"},
    "LC_Prop1_Assessment": {"name": "LC_Prop1_Assessment", "description": "Land_Cover_Property_1_Assessment"},
    "LC_Prop2_Assessment": {"name": "LC_Prop2_Assessment", "description": "Land_Cover_Property_2_Assessment"},
    "LC_Prop3_Assessment": {"name": "LC_Prop3_Assessment", "description": "Land_Cover_Property_3_Assessment"},
    "LC_Prop1": {"name": "LC_Prop1", "description": "Land_Cover_Property_1"},
    "LC_Prop2": {"name": "LC_Prop2", "description": "Land_Cover_Property_2"},
    "LC_Prop3": {"name": "LC_Prop3", "description": "Land_Cover_Property_3"},
    "QC": {"name": "QC", "description": "Quality_Flags"},
    "LW": {"name": "LW", "description": "Land_Water_Mask"},
}

MCD15A2H_Bands: Mapping[str, MODISBand] = {
    "Fpar_500m": {"name": "Fpar_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M FPAR (8-day composite)"},
    "Lai_500m": {"name": "Lai_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Leaf Area Index LAI (8-day composite)"},
    "FparLai_QC": {"name": "FparLai_QC", "description": "MOD15A2H MODIS/Terra+Aqua QC for FPAR and LAI (8-day composite)"},
    "FparExtra_QC": {"name": "FparExtra_QC", "description": "MOD15A2H MODIS/Terra+Aqua pass-through QC for FPAR and LAI (8-day composite)"},
    "FparStdDev_500m": {"name": "FparStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation FPAR (8-day composite)"},
    "LaiStdDev_500m": {"name": "LaiStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation Leaf Area Index (8-day composite)"},
}

MCD15A3H_Bands: Mapping[str, MODISBand] = {
    "Fpar_500m": {"name": "Fpar_500m", "description": "MCD15A3H MODIS/Terra Gridded 500M FPAR (4-day composite)"},
    "Lai_500m": {"name": "Lai_500m", "description": "MCD15A3H MODIS/Terra Gridded 500M Leaf Area Index LAI (4-day composite)"},
    "FparLai_QC": {"name": "FparLai_QC", "description": "MCD15A3H MODIS/Terra+Aqua QC for FPAR and LAI (4-day composite)"},
    "FparExtra_QC": {"name": "FparExtra_QC", "description": "MCD15A3H MODIS/Terra+Aqua pass-through QC for FPAR and LAI (4-day composite)"},
    "FparStdDev_500m": {"name": "FparStdDev_500m", "description": "MCD15A3H MODIS/Terra Gridded 500M Standard Deviation FPAR (4-day composite)"},
    "LaiStdDev_500m": {"name": "LaiStdDev_500m", "description": "MCD15A3H MODIS/Terra Gridded 500M Standard Deviation Leaf Area Index (4-day composite)"},
}

MCD43A4_Bands: Mapping[str, MODISBand] = {
    "BRDF_Albedo_Band_Mandatory_Quality_Band1": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band1", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band1"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band2": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band2", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band2"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band3": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band3", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band3"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band4": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band4", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band4"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band5": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band5", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band5"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band6": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band6", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band6"},
    "BRDF_Albedo_Band_Mandatory_Quality_Band7": {"name": "BRDF_Albedo_Band_Mandatory_Quality_Band7", "description": "BRDF_Albedo_Band_Mandatory_Quality_Band7"},
    "Nadir_Reflectance_Band1": {"name": "Nadir_Reflectance_Band1", "description": "Nadir_Reflectance_Band1"},
    "Nadir_Reflectance_Band2": {"name": "Nadir_Reflectance_Band2", "description": "Nadir_Reflectance_Band2"},
    "Nadir_Reflectance_Band3": {"name": "Nadir_Reflectance_Band3", "description": "Nadir_Reflectance_Band3"},
    "Nadir_Reflectance_Band4": {"name": "Nadir_Reflectance_Band4", "description": "Nadir_Reflectance_Band4"},
    "Nadir_Reflectance_Band5": {"name": "Nadir_Reflectance_Band5", "description": "Nadir_Reflectance_Band5"},
    "Nadir_Reflectance_Band6": {"name": "Nadir_Reflectance_Band6", "description": "Nadir_Reflectance_Band6"},
    "Nadir_Reflectance_Band7": {"name": "Nadir_Reflectance_Band7", "description": "Nadir_Reflectance_Band7"},
}

MCD64A1_Bands: Mapping[str, MODISBand] = {
    "Burn Date": {"name": "Burn Date", "description": "ordinal day of burn"},
    "Burn Date Uncertainty": {"name": "Burn Date Uncertainty", "description": "uncertainty in day of burn"},
    "QA": {"name": "QA", "description": "QA"},
    "First Day": {"name": "First Day", "description": "first day of reliable change detection"},
    "Last Day": {"name": "Last Day", "description": "last day of reliable change detection"},
}

MOD09A1_Bands: Mapping[str, MODISBand] = {
    "sur_refl_b01": {"name": "sur_refl_b01", "description": "Surface_reflectance_for_band_1", "common_name": "red"},
    "sur_refl_b02": {"name": "sur_refl_b02", "description": "Surface_reflectance_for_band_2", "common_name": "nir"},
    "sur_refl_b03": {"name": "sur_refl_b03", "description": "Surface_reflectance_for_band_3", "common_name": "blue"},
    "sur_refl_b04": {"name": "sur_refl_b04", "description": "Surface_reflectance_for_band_4", "common_name": "green"},
    "sur_refl_b05": {"name": "sur_refl_b05", "description": "Surface_reflectance_for_band_5"},
    "sur_refl_b06": {"name": "sur_refl_b06", "description": "Surface_reflectance_for_band_6", "common_name": "swir16"},
    "sur_refl_b07": {"name": "sur_refl_b07", "description": "Surface_reflectance_for_band_7", "common_name": "swir22"},
    "sur_refl_qc_500m": {"name": "sur_refl_qc_500m", "description": "Surface_reflectance_500m_quality_control_flags"},
    "sur_refl_szen": {"name": "sur_refl_szen", "description": "Solar_zenith"},
    "sur_refl_vzen": {"name": "sur_refl_vzen", "description": "View_zenith"},
    "sur_refl_raz": {"name": "sur_refl_raz", "description": "Relative_azimuth"},
    "sur_refl_state_500m": {"name": "sur_refl_state_500m", "description": "Surface_reflectance_500m_state_flags"},
    "sur_refl_day_of_year": {"name": "sur_refl_day_of_year", "description": "Surface_reflectance_day_of_year"},
}

MOD09Q1_Bands: Mapping[str, MODISBand] = {
    "sur_refl_b01": {"name": "sur_refl_b01", "description": "Surface_reflectance_for_band_1", "common_name": "red"},
    "sur_refl_b02": {"name": "sur_refl_b02", "description": "Surface_reflectance_for_band_2", "common_name": "nir"},
    "sur_refl_state_250m": {"name": "sur_refl_state_250m", "description": "Surface_reflectance_250m_state_flags"},
    "sur_refl_qc_250m": {"name": "sur_refl_qc_250m", "description": "Surface_reflectance_250m_quality_control_flags"},
}

MOD10A1_Bands: Mapping[str, MODISBand] = {
    "NDSI_Snow_Cover": {"name": "NDSI_Snow_Cover", "description": "NDSI snow cover from best observation of the day"},
    "NDSI_Snow_Cover_Basic_QA": {"name": "NDSI_Snow_Cover_Basic_QA", "description": "NDSI snow cover general quality value"},
    "NDSI_Snow_Cover_Algorithm_Flags_QA": {"name": "NDSI_Snow_Cover_Algorithm_Flags_QA", "description": "NDSI snow cover algorithm bit flags"},
    "NDSI": {"name": "NDSI", "description": "Raw NDSI"},
    "Snow_Albedo_Daily_Tile": {"name": "Snow_Albedo_Daily_Tile", "description": "Snow albedo of the corresponding snow cover observation"},
    "orbit_pnt": {"name": "orbit_pnt", "description": "Orbit pointer for observation"},
    "granule_pnt": {"name": "granule_pnt", "description": "Granule pointer for observation"},
}

MOD10A2_Bands: Mapping[str, MODISBand] = {
    "Maximum_Snow_Extent": {"name": "Maximum_Snow_Extent", "description": "Maximum snow extent over the 8-day period"},
    "Eight_Day_Snow_Cover": {"name": "Eight_Day_Snow_Cover", "description": "Eight day snow cover chronobyte"},
}

MOD11A1_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1km": {"name": "LST_Day_1km", "description": "Daily daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "Day_view_time": {"name": "Day_view_time", "description": "Time of daytime Land-surface Temperature observation"},
    "Day_view_angl": {"name": "Day_view_angl", "description": "View zenith angle of daytime Land-surface Temperature"},
    "LST_Night_1km": {"name": "LST_Night_1km", "description": "Daily nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "Night_view_time": {"name": "Night_view_time", "description": "Time of nighttime Land-surface Temperature observation"},
    "Night_view_angl": {"name": "Night_view_angl", "description": "View zenith angle of nighttime Land-surface Temperature"},
    "Emis_31": {"name": "Emis_31", "description": "Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Band 32 emissivity"},
    "Clear_day_cov": {"name": "Clear_day_cov", "description": "day clear-sky coverage"},
    "Clear_night_cov": {"name": "Clear_night_cov", "description": "night clear-sky coverage"},
}

MOD11A2_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1km": {"name": "LST_Day_1km", "description": "8-day daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "Day_view_time": {"name": "Day_view_time", "description": "Average time of daytime Land-surface Temperature observation"},
    "Day_view_angl": {"name": "Day_view_angl", "description": "Average view zenith angle of daytime Land-surface Temperature"},
    "LST_Night_1km": {"name": "LST_Night_1km", "description": "8-day nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "Night_view_time": {"name": "Night_view_time", "description": "Average time of nighttime Land-surface Temperature observation"},
    "Night_view_angl": {"name": "Night_view_angl", "description": "Average view zenith angle of nighttime Land-surface Temperature"},
    "Emis_31": {"name": "Emis_31", "description": "Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Band 32 emissivity"},
    "Clear_sky_days": {"name": "Clear_sky_days", "description": "the days in clear-sky conditions and with validate LSTs"},
    "Clear_sky_nights": {"name": "Clear_sky_nights", "description": "the nights in clear-sky conditions and with validate LSTs"},
}

MOD13A1_Bands: Mapping[str, MODISBand] = {
    "500m 16 days NDVI": {"name": "500m 16 days NDVI", "description": "500m 16 days NDVI"},
    "500m 16 days EVI": {"name": "500m 16 days EVI", "description": "500m 16 days EVI"},
    "500m 16 days VI Quality": {"name": "500m 16 days VI Quality", "description": "500m 16 days VI Quality"},
    "500m 16 days red reflectance": {"name": "500m 16 days red reflectance", "description": "500m 16 days red reflectance"},
    "500m 16 days NIR reflectance": {"name": "500m 16 days NIR reflectance", "description": "500m 16 days NIR reflectance"},
    "500m 16 days blue reflectance": {"name": "500m 16 days blue reflectance", "description": "500m 16 days blue reflectance"},
    "500m 16 days MIR reflectance": {"name": "500m 16 days MIR reflectance", "description": "500m 16 days MIR reflectance"},
    "500m 16 days view zenith angle": {"name": "500m 16 days view zenith angle", "description": "500m 16 days view zenith angle"},
    "500m 16 days sun zenith angle": {"name": "500m 16 days sun zenith angle", "description": "500m 16 days sun zenith angle"},
    "500m 16 days relative azimuth angle": {"name": "500m 16 days relative azimuth angle", "description": "500m 16 days relative azimuth angle"},
    "500m 16 days composite day of the year": {"name": "500m 16 days composite day of the year", "description": "500m 16 days composite day of the year"},
    "500m 16 days pixel reliability": {"name": "500m 16 days pixel reliability", "description": "500m 16 days pixel reliability"},
}

MOD13A2_Bands: Mapping[str, MODISBand] = {
    "1 km 16 days NDVI": {"name": "1 km 16 days NDVI", "description": "1 km 16 days NDVI"},
    "1 km 16 days EVI": {"name": "1 km 16 days EVI", "description": "1 km 16 days EVI"},
    "1 km 16 days VI Quality": {"name": "1 km 16 days VI Quality", "description": "1 km 16 days VI Quality"},
    "1 km 16 days red reflectance": {"name": "1 km 16 days red reflectance", "description": "1 km 16 days red reflectance"},
    "1 km 16 days NIR reflectance": {"name": "1 km 16 days NIR reflectance", "description": "1 km 16 days NIR reflectance"},
    "1 km 16 days blue reflectance": {"name": "1 km 16 days blue reflectance", "description": "1 km 16 days blue reflectance"},
    "1 km 16 days MIR reflectance": {"name": "1 km 16 days MIR reflectance", "description": "1 km 16 days MIR reflectance"},
    "1 km 16 days view zenith angle": {"name": "1 km 16 days view zenith angle", "description": "1 km 16 days view zenith angle"},
    "1 km 16 days sun zenith angle": {"name": "1 km 16 days sun zenith angle", "description": "1 km 16 days sun zenith angle"},
    "1 km 16 days relative azimuth angle": {"name": "1 km 16 days relative azimuth angle", "description": "1 km 16 days relative azimuth angle"},
    "1 km 16 days composite day of the year": {"name": "1 km 16 days composite day of the year", "description": "1 km 16 days composite day of the year"},
    "1 km 16 days pixel reliability": {"name": "1 km 16 days pixel reliability", "description": "1 km 16 days pixel reliability"},
}

MOD13Q1_Bands: Mapping[str, MODISBand] = {
    "250m 16 days NDVI": {"name": "250m 16 days NDVI", "description": "250m 16 days NDVI"},
    "250m 16 days EVI": {"name": "250m 16 days EVI", "description": "250m 16 days EVI"},
    "250m 16 days VI Quality": {"name": "250m 16 days VI Quality", "description": "250m 16 days VI Quality"},
    "250m 16 days red reflectance": {"name": "250m 16 days red reflectance", "description": "250m 16 days red reflectance"},
    "250m 16 days NIR reflectance": {"name": "250m 16 days NIR reflectance", "description": "250m 16 days NIR reflectance"},
    "250m 16 days blue reflectance": {"name": "250m 16 days blue reflectance", "description": "250m 16 days blue reflectance"},
    "250m 16 days MIR reflectance": {"name": "250m 16 days MIR reflectance", "description": "250m 16 days MIR reflectance"},
    "250m 16 days view zenith angle": {"name": "250m 16 days view zenith angle", "description": "250m 16 days view zenith angle"},
    "250m 16 days sun zenith angle": {"name": "250m 16 days sun zenith angle", "description": "250m 16 days sun zenith angle"},
    "250m 16 days relative azimuth angle": {"name": "250m 16 days relative azimuth angle", "description": "250m 16 days relative azimuth angle"},
    "250m 16 days composite day of the year": {"name": "250m 16 days composite day of the year", "description": "250m 16 days composite day of the year"},
    "250m 16 days pixel reliability": {"name": "250m 16 days pixel reliability", "description": "250m 16 days pixel reliability"},
}

MOD14A1_Bands: Mapping[str, MODISBand] = {
    "FireMask": {"name": "FireMask", "description": "FireMask"},
    "QA": {"name": "QA", "description": "QA"},
    "MaxFRP": {"name": "MaxFRP", "description": "MaxFRP"},
    "sample": {"name": "sample", "description": "sample"},
}

MOD14A2_Bands: Mapping[str, MODISBand] = {
    "FireMask": {"name": "FireMask", "description": "FireMask"},
    "QA": {"name": "QA", "description": "QA"},
}

MOD15A2H_Bands: Mapping[str, MODISBand] = {
    "Fpar_500m": {"name": "Fpar_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M FPAR (8-day composite)"},
    "Lai_500m": {"name": "Lai_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Leaf Area Index LAI (8-day composite)"},
    "FparLai_QC": {"name": "FparLai_QC", "description": "MOD15A2H MODIS/Terra+Aqua QC for FPAR and LAI (8-day composite)"},
    "FparExtra_QC": {"name": "FparExtra_QC", "description": "MOD15A2H MODIS/Terra+Aqua pass-through QC for FPAR and LAI (8-day composite)"},
    "FparStdDev_500m": {"name": "FparStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation FPAR (8-day composite)"},
    "LaiStdDev_500m": {"name": "LaiStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation Leaf Area Index (8-day composite)"},
}

MOD16A2GF_Bands: Mapping[str, MODISBand] = {
    "ET_500m": {"name": "ET_500m", "description": "MODIS Gridded 500m 8-day Composite Evapotranspiration (ET)"},
    "LE_500m": {"name": "LE_500m", "description": "MODIS Gridded 500m 8-day Composite latent heat flux (LE)"},
    "PET_500m": {"name": "PET_500m", "description": "MODIS Gridded 500m 8-day Composite potential Evapotranspiration (ET)"},
    "PLE_500m": {"name": "PLE_500m", "description": "MODIS Gridded 500m 8-day Composite potential latent heat flux (LE)"},
    "ET_QC_500m": {"name": "ET_QC_500m", "description": "ET_QC_500m"},
}

MOD16A3GF_Bands: Mapping[str, MODISBand] = {
    "ET_500m": {"name": "ET_500m", "description": "MODIS Gridded 500m Annual Evapotranspiration (ET)"},
    "LE_500m": {"name": "LE_500m", "description": "MODIS Gridded 500m Annual latent heat flux (LE)"},
    "PET_500m": {"name": "PET_500m", "description": "MODIS Gridded 500m Annual potential Evapotranspiration (ET)"},
    "PLE_500m": {"name": "PLE_500m", "description": "MODIS Gridded 500m Annual potential latent heat flux (LE)"},
    "ET_QC_500m": {"name": "ET_QC_500m", "description": "ET_Qc_500m, (bad_Qc days / total days) in growing season"},
}

MOD17A2H_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MODIS/Terra Gross Primary Production (GPP) 8-Day L4 Global 500m SIN Grid"},
    "PsnNet_500m": {"name": "PsnNet_500m", "description": "MODIS/Terra Net Photosynthesis (GPP - maint resp) 8-Day L4 Global 500m SIN Grid"},
    "Psn_QC_500m": {"name": "Psn_QC_500m", "description": "MODIS/Terra QC for 8-day GPP/PSN"},
}

MOD17A2HGF_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MODIS/Terra Gross Primary Production (GPP) 8-Day L4 Global 500m SIN Grid"},
    "PsnNet_500m": {"name": "PsnNet_500m", "description": "MODIS/Terra Net Photosynthesis (GPP - maint resp) 8-Day L4 Global 500m SIN Grid"},
    "Psn_QC_500m": {"name": "Psn_QC_500m", "description": "MODIS/Terra QC for 8-day GPP/PSN"},
}

MOD17A3HGF_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MOD17A3H -- MODIS Gridded 500M Gross Primary Productivity (GPP)"},
    "Npp_500m": {"name": "Npp_500m", "description": "MOD17A3H -- MODIS Gridded 500M Net Primary Productivity (NPP)"},
    "Npp_QC_500m": {"name": "Npp_QC_500m", "description": "NPP_QC_500M, (bad_Qc days / total days) in growing season"},
}

MOD21A2_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1KM": {"name": "LST_Day_1KM", "description": " 8-day daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "View_Angle_Day": {"name": "View_Angle_Day", "description": "Average view zenith angle of daytime Land-surface Temperature"},
    "View_Time_Day": {"name": "View_Time_Day", "description": "Average time of daytime Land-surface Temperature observation"},
    "LST_Night_1KM": {"name": "LST_Night_1KM", "description": " 8-day nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "View_Angle_Night": {"name": "View_Angle_Night", "description": "Average view zenith angle of nighttime Land-surface Temperature"},
    "View_Time_Night": {"name": "View_Time_Night", "description": "Average time of nighttime Land-surface Temperature observation"},
    "Emis_29": {"name": "Emis_29", "description": "Average Band 29 emissivity"},
    "Emis_31": {"name": "Emis_31", "description": "Average Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Average Band 32 emissivity"},
}

MYD09A1_Bands: Mapping[str, MODISBand] = {
    "sur_refl_b01": {"name": "sur_refl_b01", "description": "Surface_reflectance_for_band_1", "common_name": "red"},
    "sur_refl_b02": {"name": "sur_refl_b02", "description": "Surface_reflectance_for_band_2", "common_name": "nir"},
    "sur_refl_b03": {"name": "sur_refl_b03", "description": "Surface_reflectance_for_band_3", "common_name": "blue"},
    "sur_refl_b04": {"name": "sur_refl_b04", "description": "Surface_reflectance_for_band_4", "common_name": "green"},
    "sur_refl_b05": {"name": "sur_refl_b05", "description": "Surface_reflectance_for_band_5"},
    "sur_refl_b06": {"name": "sur_refl_b06", "description": "Surface_reflectance_for_band_6", "common_name": "swir16"},
    "sur_refl_b07": {"name": "sur_refl_b07", "description": "Surface_reflectance_for_band_7", "common_name": "swir22"},
    "sur_refl_qc_500m": {"name": "sur_refl_qc_500m", "description": "Surface_reflectance_500m_quality_control_flags"},
    "sur_refl_szen": {"name": "sur_refl_szen", "description": "Solar_zenith"},
    "sur_refl_vzen": {"name": "sur_refl_vzen", "description": "View_zenith"},
    "sur_refl_raz": {"name": "sur_refl_raz", "description": "Relative_azimuth"},
    "sur_refl_state_500m": {"name": "sur_refl_state_500m", "description": "Surface_reflectance_500m_state_flags"},
    "sur_refl_day_of_year": {"name": "sur_refl_day_of_year", "description": "Surface_reflectance_day_of_year"},
}

MYD09Q1_Bands: Mapping[str, MODISBand] = {
    "sur_refl_b01": {"name": "sur_refl_b01", "description": "Surface_reflectance_for_band_1", "common_name": "red"},
    "sur_refl_b02": {"name": "sur_refl_b02", "description": "Surface_reflectance_for_band_2", "common_name": "nir"},
    "sur_refl_state_250m": {"name": "sur_refl_state_250m", "description": "Surface_reflectance_250m_state_flags"},
    "sur_refl_qc_250m": {"name": "sur_refl_qc_250m", "description": "Surface_reflectance_250m_quality_control_flags"},
}

MYD10A1_Bands: Mapping[str, MODISBand] = {
    "NDSI_Snow_Cover": {"name": "NDSI_Snow_Cover", "description": "NDSI snow cover from best observation of the day"},
    "NDSI_Snow_Cover_Basic_QA": {"name": "NDSI_Snow_Cover_Basic_QA", "description": "NDSI snow cover general quality value"},
    "NDSI_Snow_Cover_Algorithm_Flags_QA": {"name": "NDSI_Snow_Cover_Algorithm_Flags_QA", "description": "NDSI snow cover algorithm bit flags"},
    "NDSI": {"name": "NDSI", "description": "Raw NDSI"},
    "Snow_Albedo_Daily_Tile": {"name": "Snow_Albedo_Daily_Tile", "description": "Snow albedo of the corresponding snow cover observation"},
    "orbit_pnt": {"name": "orbit_pnt", "description": "Orbit pointer for observation"},
    "granule_pnt": {"name": "granule_pnt", "description": "Granule pointer for observation"},
}

MYD10A2_Bands: Mapping[str, MODISBand] = {
    "Maximum_Snow_Extent": {"name": "Maximum_Snow_Extent", "description": "Maximum snow extent over the 8-day period"},
    "Eight_Day_Snow_Cover": {"name": "Eight_Day_Snow_Cover", "description": "Eight day snow cover chronobyte"},
}

MYD11A1_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1km": {"name": "LST_Day_1km", "description": "Daily daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "Day_view_time": {"name": "Day_view_time", "description": "Time of daytime Land-surface Temperature observation"},
    "Day_view_angl": {"name": "Day_view_angl", "description": "View zenith angle of daytime Land-surface Temperature"},
    "LST_Night_1km": {"name": "LST_Night_1km", "description": "Daily nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "Night_view_time": {"name": "Night_view_time", "description": "Time of nighttime Land-surface Temperature observation"},
    "Night_view_angl": {"name": "Night_view_angl", "description": "View zenith angle of nighttime Land-surface Temperature"},
    "Emis_31": {"name": "Emis_31", "description": "Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Band 32 emissivity"},
    "Clear_day_cov": {"name": "Clear_day_cov", "description": "day clear-sky coverage"},
    "Clear_night_cov": {"name": "Clear_night_cov", "description": "night clear-sky coverage"},
}

MYD11A2_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1km": {"name": "LST_Day_1km", "description": "8-day daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "Day_view_time": {"name": "Day_view_time", "description": "Average time of daytime Land-surface Temperature observation"},
    "Day_view_angl": {"name": "Day_view_angl", "description": "Average view zenith angle of daytime Land-surface Temperature"},
    "LST_Night_1km": {"name": "LST_Night_1km", "description": "8-day nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "Night_view_time": {"name": "Night_view_time", "description": "Average time of nighttime Land-surface Temperature observation"},
    "Night_view_angl": {"name": "Night_view_angl", "description": "Average view zenith angle of nighttime Land-surface Temperature"},
    "Emis_31": {"name": "Emis_31", "description": "Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Band 32 emissivity"},
    "Clear_sky_days": {"name": "Clear_sky_days", "description": "the days in clear-sky conditions and with validate LSTs"},
    "Clear_sky_nights": {"name": "Clear_sky_nights", "description": "the nights in clear-sky conditions and with validate LSTs"},
}

MYD13A1_Bands: Mapping[str, MODISBand] = {
    "500m 16 days NDVI": {"name": "500m 16 days NDVI", "description": "500m 16 days NDVI"},
    "500m 16 days EVI": {"name": "500m 16 days EVI", "description": "500m 16 days EVI"},
    "500m 16 days VI Quality": {"name": "500m 16 days VI Quality", "description": "500m 16 days VI Quality"},
    "500m 16 days red reflectance": {"name": "500m 16 days red reflectance", "description": "500m 16 days red reflectance"},
    "500m 16 days NIR reflectance": {"name": "500m 16 days NIR reflectance", "description": "500m 16 days NIR reflectance"},
    "500m 16 days blue reflectance": {"name": "500m 16 days blue reflectance", "description": "500m 16 days blue reflectance"},
    "500m 16 days MIR reflectance": {"name": "500m 16 days MIR reflectance", "description": "500m 16 days MIR reflectance"},
    "500m 16 days view zenith angle": {"name": "500m 16 days view zenith angle", "description": "500m 16 days view zenith angle"},
    "500m 16 days sun zenith angle": {"name": "500m 16 days sun zenith angle", "description": "500m 16 days sun zenith angle"},
    "500m 16 days relative azimuth angle": {"name": "500m 16 days relative azimuth angle", "description": "500m 16 days relative azimuth angle"},
    "500m 16 days composite day of the year": {"name": "500m 16 days composite day of the year", "description": "500m 16 days composite day of the year"},
    "500m 16 days pixel reliability": {"name": "500m 16 days pixel reliability", "description": "500m 16 days pixel reliability"},
}

MYD13A2_Bands: Mapping[str, MODISBand] = {
    "1 km 16 days NDVI": {"name": "1 km 16 days NDVI", "description": "1 km 16 days NDVI"},
    "1 km 16 days EVI": {"name": "1 km 16 days EVI", "description": "1 km 16 days EVI"},
    "1 km 16 days VI Quality": {"name": "1 km 16 days VI Quality", "description": "1 km 16 days VI Quality"},
    "1 km 16 days red reflectance": {"name": "1 km 16 days red reflectance", "description": "1 km 16 days red reflectance"},
    "1 km 16 days NIR reflectance": {"name": "1 km 16 days NIR reflectance", "description": "1 km 16 days NIR reflectance"},
    "1 km 16 days blue reflectance": {"name": "1 km 16 days blue reflectance", "description": "1 km 16 days blue reflectance"},
    "1 km 16 days MIR reflectance": {"name": "1 km 16 days MIR reflectance", "description": "1 km 16 days MIR reflectance"},
    "1 km 16 days view zenith angle": {"name": "1 km 16 days view zenith angle", "description": "1 km 16 days view zenith angle"},
    "1 km 16 days sun zenith angle": {"name": "1 km 16 days sun zenith angle", "description": "1 km 16 days sun zenith angle"},
    "1 km 16 days relative azimuth angle": {"name": "1 km 16 days relative azimuth angle", "description": "1 km 16 days relative azimuth angle"},
    "1 km 16 days composite day of the year": {"name": "1 km 16 days composite day of the year", "description": "1 km 16 days composite day of the year"},
    "1 km 16 days pixel reliability": {"name": "1 km 16 days pixel reliability", "description": "1 km 16 days pixel reliability"},
}

MYD13Q1_Bands: Mapping[str, MODISBand] = {
    "250m 16 days NDVI": {"name": "250m 16 days NDVI", "description": "250m 16 days NDVI"},
    "250m 16 days EVI": {"name": "250m 16 days EVI", "description": "250m 16 days EVI"},
    "250m 16 days VI Quality": {"name": "250m 16 days VI Quality", "description": "250m 16 days VI Quality"},
    "250m 16 days red reflectance": {"name": "250m 16 days red reflectance", "description": "250m 16 days red reflectance"},
    "250m 16 days NIR reflectance": {"name": "250m 16 days NIR reflectance", "description": "250m 16 days NIR reflectance"},
    "250m 16 days blue reflectance": {"name": "250m 16 days blue reflectance", "description": "250m 16 days blue reflectance"},
    "250m 16 days MIR reflectance": {"name": "250m 16 days MIR reflectance", "description": "250m 16 days MIR reflectance"},
    "250m 16 days view zenith angle": {"name": "250m 16 days view zenith angle", "description": "250m 16 days view zenith angle"},
    "250m 16 days sun zenith angle": {"name": "250m 16 days sun zenith angle", "description": "250m 16 days sun zenith angle"},
    "250m 16 days relative azimuth angle": {"name": "250m 16 days relative azimuth angle", "description": "250m 16 days relative azimuth angle"},
    "250m 16 days composite day of the year": {"name": "250m 16 days composite day of the year", "description": "250m 16 days composite day of the year"},
    "250m 16 days pixel reliability": {"name": "250m 16 days pixel reliability", "description": "250m 16 days pixel reliability"},
}

MYD14A1_Bands: Mapping[str, MODISBand] = {
    "FireMask": {"name": "FireMask", "description": "FireMask"},
    "QA": {"name": "QA", "description": "QA"},
    "MaxFRP": {"name": "MaxFRP", "description": "MaxFRP"},
    "sample": {"name": "sample", "description": "sample"},
}

MYD14A2_Bands: Mapping[str, MODISBand] = {
    "FireMask": {"name": "FireMask", "description": "FireMask"},
    "QA": {"name": "QA", "description": "QA"},
}

MYD15A2H_Bands: Mapping[str, MODISBand] = {
    "Fpar_500m": {"name": "Fpar_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M FPAR (8-day composite)"},
    "Lai_500m": {"name": "Lai_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Leaf Area Index LAI (8-day composite)"},
    "FparLai_QC": {"name": "FparLai_QC", "description": "MOD15A2H MODIS/Terra+Aqua QC for FPAR and LAI (8-day composite)"},
    "FparExtra_QC": {"name": "FparExtra_QC", "description": "MOD15A2H MODIS/Terra+Aqua pass-through QC for FPAR and LAI (8-day composite)"},
    "FparStdDev_500m": {"name": "FparStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation FPAR (8-day composite)"},
    "LaiStdDev_500m": {"name": "LaiStdDev_500m", "description": "MOD15A2H MODIS/Terra Gridded 500M Standard Deviation Leaf Area Index (8-day composite)"},
}

MYD16A3GF_Bands: Mapping[str, MODISBand] = {
    "ET_500m": {"name": "ET_500m", "description": "MODIS Gridded 500m Annual Evapotranspiration (ET)"},
    "LE_500m": {"name": "LE_500m", "description": "MODIS Gridded 500m Annual latent heat flux (LE)"},
    "PET_500m": {"name": "PET_500m", "description": "MODIS Gridded 500m Annual potential Evapotranspiration (ET)"},
    "PLE_500m": {"name": "PLE_500m", "description": "MODIS Gridded 500m Annual potential latent heat flux (LE)"},
    "ET_QC_500m": {"name": "ET_QC_500m", "description": "ET_Qc_500m, (bad_Qc days / total days) in growing season"},
}

MYD17A2H_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MODIS/Terra Gross Primary Production (GPP) 8-Day L4 Global 500m SIN Grid"},
    "PsnNet_500m": {"name": "PsnNet_500m", "description": "MODIS/Terra Net Photosynthesis (GPP - maint resp) 8-Day L4 Global 500m SIN Grid"},
    "Psn_QC_500m": {"name": "Psn_QC_500m", "description": "MODIS/Terra QC for 8-day GPP/PSN"},
}

MYD17A2HGF_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MODIS/Terra Gross Primary Production (GPP) 8-Day L4 Global 500m SIN Grid"},
    "PsnNet_500m": {"name": "PsnNet_500m", "description": "MODIS/Terra Net Photosynthesis (GPP - maint resp) 8-Day L4 Global 500m SIN Grid"},
    "Psn_QC_500m": {"name": "Psn_QC_500m", "description": "MODIS/Terra QC for 8-day GPP/PSN"},
}

MYD17A3HGF_Bands: Mapping[str, MODISBand] = {
    "Gpp_500m": {"name": "Gpp_500m", "description": "MOD17A3H -- MODIS Gridded 500M Gross Primary Productivity (GPP)"},
    "Npp_500m": {"name": "Npp_500m", "description": "MOD17A3H -- MODIS Gridded 500M Net Primary Productivity (NPP)"},
    "Npp_QC_500m": {"name": "Npp_QC_500m", "description": "NPP_QC_500M, (bad_Qc days / total days) in growing season"},
}

MYD21A2_Bands: Mapping[str, MODISBand] = {
    "LST_Day_1KM": {"name": "LST_Day_1KM", "description": " 8-day daytime 1km grid Land-surface Temperature"},
    "QC_Day": {"name": "QC_Day", "description": "Quality control for daytime LST and emissivity"},
    "View_Angle_Day": {"name": "View_Angle_Day", "description": "Average view zenith angle of daytime Land-surface Temperature"},
    "View_Time_Day": {"name": "View_Time_Day", "description": "Average time of daytime Land-surface Temperature observation"},
    "LST_Night_1KM": {"name": "LST_Night_1KM", "description": " 8-day nighttime 1km grid Land-surface Temperature"},
    "QC_Night": {"name": "QC_Night", "description": "Quality control for nighttime LST and emissivity"},
    "View_Angle_Night": {"name": "View_Angle_Night", "description": "Average view zenith angle of nighttime Land-surface Temperature"},
    "View_Time_Night": {"name": "View_Time_Night", "description": "Average time of nighttime Land-surface Temperature observation"},
    "Emis_29": {"name": "Emis_29", "description": "Average Band 29 emissivity"},
    "Emis_31": {"name": "Emis_31", "description": "Average Band 31 emissivity"},
    "Emis_32": {"name": "Emis_32", "description": "Average Band 32 emissivity"},
}

MODIS_BANDS: Final[Mapping[str, Mapping[str, MODISBand]]] = {
    "MOD09A1": MOD09A1_Bands,
    "MOD09Q1": MOD09Q1_Bands,
    "MOD10A1": MOD10A1_Bands,
    "MOD10A2": MOD10A2_Bands,
    "MOD11A1": MOD11A1_Bands,
    "MOD11A2": MOD11A2_Bands,
    "MOD13A1": MOD13A1_Bands,
    "MOD13A2": MOD13A2_Bands,
    "MOD13Q1": MOD13Q1_Bands,
    "MOD14A1": MOD14A1_Bands,
    "MOD14A2": MOD14A2_Bands,
    "MOD15A2H": MOD15A2H_Bands,
    "MOD16A2GF": MOD16A2GF_Bands,
    "MOD16A3GF": MOD16A3GF_Bands,
    "MOD17A2H": MOD17A2H_Bands,
    "MOD17A2HGF": MOD17A2HGF_Bands,
    "MOD17A3HGF": MOD17A3HGF_Bands,
    "MOD21A2": MOD21A2_Bands,
    "MYD09A1": MYD09A1_Bands,
    "MYD09Q1": MYD09Q1_Bands,
    "MYD10A1": MYD10A1_Bands,
    "MYD10A2": MYD10A2_Bands,
    "MYD11A1": MYD11A1_Bands,
    "MYD11A2": MYD11A2_Bands,
    "MYD13A1": MYD13A1_Bands,
    "MYD13A2": MYD13A2_Bands,
    "MYD13Q1": MYD13Q1_Bands,
    "MYD14A1": MYD14A1_Bands,
    "MYD14A2": MYD14A2_Bands,
    "MYD15A2H": MYD15A2H_Bands,
    "MYD16A3GF": MYD16A3GF_Bands,
    "MYD17A2H": MYD17A2H_Bands,
    "MYD17A2HGF": MYD17A2HGF_Bands,
    "MYD17A3HGF": MYD17A3HGF_Bands,
    "MYD21A2": MYD21A2_Bands,
    "MCD12Q1": MCD12Q1_Bands,
    "MCD15A2H": MCD15A2H_Bands,
    "MCD15A3H": MCD15A3H_Bands,
    "MCD43A4": MCD43A4_Bands,
    "MCD64A1": MCD64A1_Bands,
}
