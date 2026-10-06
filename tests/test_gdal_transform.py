import json
from pathlib import Path

import pytest

_MAIN_DIR = Path(__file__).parent.parent

examples_list: list[Path] = list(_MAIN_DIR.glob('**/example*/*.json'))

GDAL_IDENTITY = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0)

# Source: https://github.com/rasterio/rasterio/blob/a66f87/rasterio/transform.py#L128
def tastes_like_gdal(seq):
    """Return True if `seq` matches the GDAL geotransform pattern."""
    return tuple(seq) == GDAL_IDENTITY or (seq[2] == seq[4] == 0.0 and seq[1] > 0 and seq[5] < 0)

@pytest.mark.parametrize('item_example', examples_list)
def test_gdal_transform(item_example: Path):
    item: dict = json.loads(item_example.read_bytes())

    # Check that proj:transform is a affine transform, not GDAL GeoTransform
    transforms = []
    if 'proj:transform' in item.get('properties', {}):
        transforms.append(item['properties']['proj:transform'])
    else:
        for asset in item.get('assets', {}).values():
            if "proj:transform" in asset:
                transforms.append(asset['proj:transform'])

    for transform in transforms:
        assert not tastes_like_gdal(transform), (
            f'Item {item_example.stem} likely contains a GDAL-like GeoTransform in proj:transform: {transform}'
        )
