# Run this script to update the collection JSON files in this folder.
# Simply run: python collections.py
import json
from typing import Any

import const

# defaults to 2018-04-30T00:18:51Z for L2 if product type is not set in START_DATE_MAP
START_DATE_MAP = {
    "aer-ai": "2018-04-30T00:18:50Z",
    "aer-lh": "2018-04-01T00:00:11Z",
    "ch4": "2018-04-01T01:01:34Z",
    "cloud": "2018-04-30T00:18:50Z",
    "co": "2018-04-01T00:00:11Z",
    "o3-pr": "2018-04-01T00:00:11Z",
    "o3-tcl": "2018-04-30T10:50:26Z",
    "so2": "2018-04-30T00:18:50Z",
}


COLLECTION_TITLE_MAP = {
    "aer-ai": "Ultraviolet Aerosol Index",
    "aer-lh": "Aerosol Layer Height",
    "ch4": "Methane",
    "cloud": "Cloud",
    "co": "Carbon Monoxide",
    "hcho": "Formaldehyde",
    "no2": "Nitrogen Dioxide",
    "np-bd3": "NPP Cloud (band 3)",
    "np-bd6": "NPP Cloud (band 6)",
    "np-bd7": "NPP Cloud (band 7)",
    "o3": "Ozone",
    "o3-pr": "Ozone Profile",
    "o3-tcl": "Tropospheric Ozone",
    "so2": "Sulphur Dioxide",
}


COLLECTION_DESCRIPTION_MAP = {
    "aer-ai": "This Collection provides Sentinel-5P Level-2 AER AI products, which contains high-resolution imagery of the UV Aerosol Index (UVAI), also called the Absorbing Aerosol Index (AAI).",
    "aer-lh": "This Collection provides Sentinel-5P Level-2 AER LH products, which contains high-resolution imagery of the UV Aerosol Index (UVAI), also called the Absorbing Layer Height (ALH).",
    "ch4": "This Collection provides Sentinel-5P Level-2 CH4 products, which contains high-resolution imagery of methane concentrations.",
    "cloud": "This Collection provides Sentinel-5P Level-2 Cloud products, which contains high-resolution imagery of cloud parameters.",
    "co": "This Collection provides Sentinel-5P Level-2 CO products, which contains high-resolution imagery of carbon monoxide concentrations.",
    "hcho": "This Collection provides Sentinel-5P Level-2 HCHO products, which contains high-resolution imagery of atmospheric formaldehyde concentrations.",
    "no2": "This Collection provides Sentinel-5P Level-2 NO2 products, which contains high-resolution imagery of nitrogen dioxide concentrations.",
    "np-bd3": "This Collection provides Sentinel-5P Level-2 NP BD3 products, which contains information on cloud and scene homogeneity.",
    "np-bd6": "This Collection provides Sentinel-5P Level-2 NP BD6 products, which contains information on cloud and scene homogeneity.",
    "np-bd7": "This Collection provides Sentinel-5P Level-2 NP BD7 products, which contains information on cloud and scene homogeneity.",
    "o3": "This Collection provides Sentinel-5P Level-2 O3 products, which contains high-resolution imagery of total column ozone concentrations.",
    "o3-pr": "This Collection provides Sentinel-5P Level-2 O3 PR products, which contains ozone concentration for 33 levels in the atmosphere.",
    "o3-tcl": "This Collection provides Sentinel-5P Level-2 O3 TCL products, which contains high-resolution imagery of tropospheric ozone concentrations.",
    "so2": "This Collection provides Sentinel-5P Level-2 SO2 products, which contains high-resolution imagery of atmospheric sulfur dioxide concentrations.",
}


def get_collection_description(level: int, subtype: str) -> str:
    if level == 1:
        band = subtype[5:]
        return f"This Collection provides Sentinel-5P Level-1 RA BD{band} products, which contains Earth radiance spectra for spectral band {band}."
    else:
        return COLLECTION_DESCRIPTION_MAP[subtype]


def get_collection_title(level: int, subtype: str) -> str:
    if level == 1:
        band = subtype[5:]
        return f"Radiance Band {band}"
    else:
        return COLLECTION_TITLE_MAP[subtype]


def get_start_date(level: int, subtype: str) -> str:
    if level == 1:
        return "2018-04-30T00:19:50Z"
    else:
        return START_DATE_MAP.get(subtype, "2018-04-30T00:18:51Z")


def generate_collection(
    product_type: str, level: int, subtype: str, timeliness_category: str
) -> dict[str, Any]:
    collection_id = f"sentinel-5p-l{level}-{subtype}-{timeliness_category}"
    title = get_collection_title(level, subtype)
    thumbnail_filename = "RA_BD" if level == 1 else subtype.replace("-", "_").upper()
    extensions = [
        "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json",
        "https://stac-extensions.github.io/authentication/v1.1.0/schema.json",
        "https://stac-extensions.github.io/processing/v1.2.0/schema.json",
        "https://stac-extensions.github.io/product/v0.1.0/schema.json",
        "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
        "https://stac-extensions.github.io/sat/v1.1.0/schema.json",
        "https://stac-extensions.github.io/scientific/v1.0.0/schema.json",
        "https://stac-extensions.github.io/storage/v2.0.0/schema.json",
    ]
    if level == 1:
        extensions.append("https://stac-extensions.github.io/eo/v2.0.0/schema.json")
    collection = {
        "stac_version": "1.1.0",
        "stac_extensions": extensions,
        "id": collection_id,
        "type": "Collection",
        "title": f"Sentinel-5P Level {level} {title} ({timeliness_category.upper()})",
        "description": get_collection_description(level, subtype),
        "sci:citation": "Copernicus Sentinel data [Year]",
        "extent": {
            "spatial": {"bbox": [[-180, -90, 180, 90]]},
            "temporal": {"interval": [[get_start_date(level, subtype), None]]},
        },
        "license": "other",
        "keywords": [
            "Sentinel",
            "Copernicus",
            "ESA",
            "Satellite",
            "Global",
            "Atmosphere",
            f"L{level}",
            subtype.upper(),
            timeliness_category.upper(),
            "EU",
            "EC",
        ],
        "providers": [
            {
                "url": "https://sentinel.esa.int/web/sentinel/missions/sentinel-5p",
                "name": "ESA",
                "roles": ["producer"],
            },
            {
                "url": "https://commission.europa.eu/",
                "name": "European Commission",
                "roles": ["licensor"],
            },
            {
                "url": "https://cloudferro.com/",
                "name": "CloudFerro",
                "roles": ["host", "processor"],
            },
        ],
        "assets": {
            "thumbnail": {
                "href": f"https://s3.waw3-2.cloudferro.com/swift/v1/stac-png/S5P_L{level}_{thumbnail_filename}.jpg",
                "type": "image/jpeg",
                "roles": ["thumbnail"],
                "title": f"Sentinel-5P L{level} {title} Thumbnail",
                "proj:code": None,
                "proj:shape": [360, 640],
            }
        },
        "summaries": {
            "gsd": [const.GSD_MAP.get(subtype, 3500)],
            "platform": ["sentinel-5p"],
            "constellation": ["sentinel-5"],
            "instruments": ["tropomi"],
            "product:type": [product_type],
            "processing:level": [f"L{level}"],
            "processing:version": const.PROCESSING_VERSIONS_MAP[subtype],
            "proj:code": [None],
            "sat:platform_international_designator": ["2017-064A"],
        },
        "auth:schemes": {
            "oidc": {
                "type": "openIdConnect",
                "openIdConnectUrl": "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/.well-known/openid-configuration",
            },
            "s3": {"type": "s3"},
        },
        "storage:schemes": {
            "cdse-s3": {
                "title": "Copernicus Data Space Ecosystem S3",
                "description": "This endpoint provides access to EO data which is stored on the object storage of both CloudFerro Cloud and OpenTelekom Cloud (OTC). See the [documentation](https://documentation.dataspace.copernicus.eu/APIs/S3.html) for more information, including how to get credentials.",
                "platform": "https://eodata.dataspace.copernicus.eu",
                "requester_pays": False,
                "type": "custom-s3",
            },
            "creodias-s3": {
                "title": "CREODIAS S3",
                "description": "Comprehensive Earth Observation Data (EODATA) archive offered by CREODIAS as a commercial part of CDSE, designed to provide users with access to a vast repository of satellite data without predefined quota limits",
                "platform": "https://eodata.cloudferro.com",
                "requester_pays": True,
                "type": "custom-s3",
            },
        },
        "item_assets": {
            "netcdf": {
                "type": "application/netcdf",
                "title": const.ASSET_TITLE_MAP[subtype],
                "roles": ["data"],
                "data_type": "float32",
                "nodata": -999 if subtype.startswith("np-") else 9.9692099683868690e36,
                "alternate:name": "S3",
                "auth:refs": ["s3"],
                "storage:refs": ["cdse-s3", "creodias-s3"],
                "alternate": {
                    "https": {
                        "alternate:name": "HTTPS",
                        "auth:refs": ["oidc"],
                        "storage:refs": [],
                    }
                },
            }
        },
        "links": [
            {
                "rel": "license",
                "href": "https://sentinel.esa.int/documents/247904/690755/Sentinel_Data_Legal_Notice",
                "type": "application/pdf",
                "title": "Legal notice on the use of Copernicus Sentinel Data and Service Information",
            },
        ],
    }

    if level == 1:
        collection["item_assets"]["netcdf"]["bands"] = [const.get_band(subtype)]
        collection["bands"] = const.L1_RA_BANDS

    if timeliness := const.get_timeliness(timeliness_category, subtype):
        collection["summaries"].update(
            {
                "product:timeliness": [timeliness],
                "product:timeliness_category": [timeliness_category.upper()],
            }
        )

    return collection


for product_type, subtype in const.PRODUCT_TYPE_MAP.items():
    for timeliness in const.TIMELINESS_CATEGORIES_MAP.get(
        subtype, ["nrti", "offl", "rpro"]
    ):
        level = 2 if product_type.startswith("L2") else 1
        collection = generate_collection(product_type, level, subtype, timeliness)
        filepath = (
            f"./collection_s5p_l{level}_{subtype.replace('-', '_')}_{timeliness}.json"
        )
        with open(filepath, "w") as f:
            f.write(json.dumps(collection, indent=2))
