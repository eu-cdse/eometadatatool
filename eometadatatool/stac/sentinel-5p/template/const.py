# defaults to 3500 if not present in GSD_MAP
# gsd is the best resolution along either axis
GSD_MAP = {
    "ra-bd1": 5500,
    "ra-bd7": 5500,
    "ra-bd8": 5500,
    "ch4": 7000,
    "co": 7000,
    "o3-pr": 21000,
}


PRODUCT_TYPE_MAP = {
    "L1B_RA_BD1": "ra-bd1",
    "L1B_RA_BD2": "ra-bd2",
    "L1B_RA_BD3": "ra-bd3",
    "L1B_RA_BD4": "ra-bd4",
    "L1B_RA_BD5": "ra-bd5",
    "L1B_RA_BD6": "ra-bd6",
    "L1B_RA_BD7": "ra-bd7",
    "L1B_RA_BD8": "ra-bd8",
    "L2__AER_AI": "aer-ai",
    "L2__AER_LH": "aer-lh",
    "L2__CH4___": "ch4",
    "L2__CLOUD_": "cloud",
    "L2__CO____": "co",
    "L2__HCHO__": "hcho",
    "L2__NO2___": "no2",
    "L2__NP_BD3": "np-bd3",
    "L2__NP_BD6": "np-bd6",
    "L2__NP_BD7": "np-bd7",
    "L2__O3____": "o3",
    "L2__O3__PR": "o3-pr",
    "L2__O3_TCL": "o3-tcl",
    "L2__SO2___": "so2",
}


def get_timeliness(category: str | None, subtype: str) -> str | None:
    if category is None:
        return None

    category = category.upper()
    
    if category == "NRTI":
        return "PT3H"
    if category == "OFFL":
        return "P5D" if subtype == "o3-tcl" else "PT12H"

    return None


# defaults to ['nrti', 'offl', 'rpro'] if not present in TIMELINESS_CATEGORIES_MAP
TIMELINESS_CATEGORIES_MAP = {
    "ch4": ["offl", "rpro"],
    "np-bd3": ["offl", "rpro"],
    "np-bd6": ["offl", "rpro"],
    "np-bd7": ["offl", "rpro"],
    "o3": ["nrti", "offl"],
}


ASSET_TITLE_MAP = {
    "ra-bd1": "Radiance Product, Band 1",
    "ra-bd2": "Radiance Product, Band 2",
    "ra-bd3": "Radiance Product, Band 3",
    "ra-bd4": "Radiance Product, Band 4",
    "ra-bd5": "Radiance Product, Band 5",
    "ra-bd6": "Radiance Product, Band 6",
    "ra-bd7": "Radiance Product, Band 7",
    "ra-bd8": "Radiance Product, Band 8",
    "aer-ai": "UV Aerosol Index",
    "aer-lh": "UV Aerosol Layer Height",
    "ch4": "Methane Concentration",
    "cloud": "Cloud Parameters",
    "co": "Carbon Monoxide Concentration",
    "hcho": "Atmospheric Formaldehyde Concentration",
    "no2": "Nitrogen Dioxide Concentration",
    "np-bd3": "Cloud from the Suomi NPP mission, band 3",
    "np-bd6": "Cloud from the Suomi NPP mission, band 6",
    "np-bd7": "Cloud from the Suomi NPP mission, band 7",
    "o3": "Total Column Ozone Concentration",
    "o3-pr": "Atmospheric Ozone Concentration",
    "o3-tcl": "Tropospheric Ozone Concentration",
    "so2": "Atmospheric Sulfur Dioxide Concentrations",
}


PROCESSING_VERSIONS_MAP = {
    "ra-bd1": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd2": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd3": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd4": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd5": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd6": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd7": ["1.0.0", "2.0.0", "2.1.0"],
    "ra-bd8": ["1.0.0", "2.0.0", "2.1.0"],
    "aer-ai": [
        "1.0.2",
        "1.1.0",
        "1.2.0",
        "1.2.2",
        "1.3.0",
        "1.3.1",
        "1.3.2",
        "1.4.0",
        "2.2.0",
        "2.3.1",
        "2.4.0",
        "2.5.0",
        "2.6.0",
        "2.7.1"
    ],
    "aer-lh": ["1.3.0", "1.3.1", "1.3.2", "1.4.0", "2.2.0", "2.3.1", "2.4.0", "2.5.0", "2.6.0", "2.7.1"],
    "ch4": [
        "1.2.2",
        "1.3.0",
        "1.3.1",
        "1.3.2",
        "1.4.0",
        "2.2.0",
        "2.3.1",
        "2.4.0",
        "2.5.0",
        "2.6.0",
        "2.7.1"
    ],
    "cloud": [
        "1.0.0",
        "1.1.1",
        "1.1.2",
        "1.1.5",
        "1.1.6",
        "1.1.7",
        "1.1.8",
        "2.1.3",
        "2.1.4",
        "2.2.1",
        "2.3.0",
        "2.4.1",
        "2.5.0",
        "2.6.1"
    ],
    "co": [
        "1.0.2",
        "1.1.0",
        "1.2.0",
        "1.2.2",
        "1.3.0",
        "1.3.1",
        "1.3.2",
        "1.4.0",
        "2.2.0",
        "2.3.1",
        "2.4.0",
        "2.5.0",
        "2.6.0",
        "2.7.1"
    ],
    "hcho": ["1.1.2", "1.1.5", "1.1.6", "1.1.7", "1.1.8", "2.1.3", "2.1.4", "2.2.1", "2.3.0", "2.4.1", "2.5.0", "2.6.1"],
    "no2": [
        "1.0.2",
        "1.1.0",
        "1.2.0",
        "1.2.2",
        "1.3.0",
        "1.3.1",
        "1.3.2",
        "1.4.0",
        "2.2.0",
        "2.3.1",
        "2.4.0",
        "2.5.0",
        "2.6.0",
        "2.7.1"
    ],
    "np-bd3": ["1.0.0", "1.0.2", "1.1.0", "1.3.0", "2.0.1", "2.0.3"],
    "np-bd6": ["1.0.0", "1.0.2", "1.1.0", "1.3.0", "2.0.1", "2.0.3"],
    "np-bd7": ["1.0.0", "1.0.2", "1.1.0", "1.3.0", "2.0.1", "2.0.3"],
    "o3": [
        "1.1.2",
        "1.1.5",
        "1.1.6",
        "1.1.7",
        "1.1.8",
        "2.1.3",
        "2.1.4",
        "2.2.1",
        "2.3.0",
        "2.4.1",
        "2.5.0",
        "2.6.1"
    ],
    "o3-pr": ["2.3.1", "2.4.0", "2.5.0", "2.6.0", "2.7.1"],
    "o3-tcl": [
        "1.1.5",
        "1.1.6",
        "1.1.7",
        "1.1.8",
        "2.1.3",
        "2.1.4",
        "2.2.1",
        "2.3.0",
        "2.4.1",
        "2.5.0",
        "2.6.1"
    ],
    "so2": [
        "1.1.2",
        "1.1.5",
        "1.1.6",
        "1.1.7",
        "1.1.8",
        "2.1.3",
        "2.1.4",
        "2.2.1",
        "2.3.0",
        "2.4.1",
        "2.5.0",
        "2.6.1"
    ],
}
