import pytest

from eometadatatool.dlc import _is_valid_odata_checksum, asset_to_zipper


@pytest.mark.parametrize(
    ('checksum', 'expected'),
    [
        (None, False),
        ({'Value': '', 'Algorithm': ''}, False),
        ({'Value': '0', 'Algorithm': 'MD5'}, False),
        ({'Value': 'N/A', 'Algorithm': 'MD5'}, False),
        ({'Value': '0' * 32, 'Algorithm': 'MD5'}, False),
        ({'Value': '1' * 32, 'Algorithm': 'MD5'}, True),
    ],
)
def test_is_valid_odata_checksum(checksum, expected):
    assert _is_valid_odata_checksum(checksum) == expected


@pytest.mark.parametrize(
    ('pid', 'scene_name', 'asset_path', 'expected'),
    [
        (
            'PID',
            'SCENE',
            'FOO/BAR',
            'https://zipper.dataspace.copernicus.eu/odata/v1/Products(PID)/Nodes(SCENE)/Nodes(FOO)/Nodes(BAR)/$value',
        ),
        (
            'PID',
            'SCENE',
            '/FOO/BAR',
            'https://zipper.dataspace.copernicus.eu/odata/v1/Products(PID)/Nodes(SCENE)/Nodes(FOO)/Nodes(BAR)/$value',
        ),
        (
            'PID',
            '/ABS/PATH/SCENE',
            'FOO/BAR',
            'https://zipper.dataspace.copernicus.eu/odata/v1/Products(PID)/Nodes(SCENE)/Nodes(FOO)/Nodes(BAR)/$value',
        ),
        (
            'PID',
            '/ABS/PATH/SCENE',
            '/ABS/PATH/SCENE/FOO/BAR',
            'https://zipper.dataspace.copernicus.eu/odata/v1/Products(PID)/Nodes(SCENE)/Nodes(FOO)/Nodes(BAR)/$value',
        ),
        (
            'PID',
            's3://ABS/PATH/SCENE',
            's3://ABS/PATH/SCENE/FOO/BAR',
            'https://zipper.dataspace.copernicus.eu/odata/v1/Products(PID)/Nodes(SCENE)/Nodes(FOO)/Nodes(BAR)/$value',
        ),
    ],
)
def test_asset_to_zipper(pid, scene_name, asset_path, expected):
    assert asset_to_zipper(pid, scene_name, asset_path) == expected


def test_asset_to_zipper_with_dot():
    with pytest.raises(AssertionError):
        asset_to_zipper('PID', 'S2A_MSIL1C_20230216T044851_N0509_R076_T46UEU', './FOO')
