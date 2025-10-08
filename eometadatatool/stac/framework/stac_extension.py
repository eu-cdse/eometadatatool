from enum import Enum


class StacExtension(str, Enum):
    ALTERNATE = 'https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json'
    ALTIMETRY = 'https://stac-extensions.github.io/altimetry/v0.1.0/schema.json'
    AUTHENTICATION = (
        'https://stac-extensions.github.io/authentication/v1.1.0/schema.json'
    )
    CLASSIFICATION = (
        'https://stac-extensions.github.io/classification/v2.0.0/schema.json'
    )
    DATACUBE = 'https://stac-extensions.github.io/datacube/v2.3.0/schema.json'
    EO = 'https://stac-extensions.github.io/eo/v2.0.0/schema.json'
    EOPF = 'https://cs-si.github.io/eopf-stac-extension/v1.2.0/schema.json'
    FILE = 'https://stac-extensions.github.io/file/v2.1.0/schema.json'
    GRID = 'https://stac-extensions.github.io/grid/v1.1.0/schema.json'
    PROCESSING = 'https://stac-extensions.github.io/processing/v1.2.0/schema.json'
    PRODUCT = 'https://stac-extensions.github.io/product/v1.0.0/schema.json'
    PROJECTION = 'https://stac-extensions.github.io/projection/v2.0.0/schema.json'
    RASTER = 'https://stac-extensions.github.io/raster/v2.0.0/schema.json'
    SAR = 'https://stac-extensions.github.io/sar/v1.3.0/schema.json'
    SATELLITE = 'https://stac-extensions.github.io/sat/v1.1.0/schema.json'
    SCIENTIFIC = 'https://stac-extensions.github.io/scientific/v1.0.0/schema.json'
    STORAGE = 'https://stac-extensions.github.io/storage/v2.0.0/schema.json'
    TIMESTAMP = 'https://stac-extensions.github.io/timestamps/v1.1.0/schema.json'
    VIEW = 'https://stac-extensions.github.io/view/v1.1.0/schema.json'
