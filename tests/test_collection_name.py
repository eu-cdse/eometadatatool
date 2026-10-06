"""Tests for get_collection_name().

Uses the real example item JSONs under eometadatatool/stac/{mission}/example*/
as ground truth: each one already carries the real "collection" id, and its
filename stem is the real scene filename the collection id was derived from.
"""

import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from constants import _STAC_DIR

from eometadatatool.clas import collection_name
from eometadatatool.clas.collection_name import _timeliness_code, get_collection_name
from eometadatatool.odata_response import configure_odata_response

_EXAMPLES = sorted(_STAC_DIR.glob('**/example*/*.json'))

# Plain CLMS (non-landcover) resolves its collection id via an OData lookup
# (see _clms_collection) instead of a fixed storage-path depth -- mock that
# lookup so the test runs offline, deterministic, and without needing the
# full s3://eodata/CLMS/... path.
_CLMS_DIR = _STAC_DIR / 'clms'
_stac_clms = importlib.import_module('eometadatatool.stac.clms.template.stac_clms')


def _scene_for(example_path: Path) -> Path:
    return Path(example_path.stem)


def _expected_collection(example_path: Path) -> str | None:
    return json.loads(example_path.read_bytes()).get('collection')


def _fake_clms_odata_response(scene: Path, expected_collection: str) -> dict[str, Any]:
    file_type = _stac_clms.identify_type(scene.name)
    dataset_id = expected_collection.removeprefix('clms_').removesuffix(f'_{file_type}')
    return {
        'Id': 'test-id',
        'Name': scene.name,
        'ContentLength': 0,
        'OriginDate': '2024-01-01T00:00:00.000Z',
        'ModificationDate': '2024-01-01T00:00:00.000Z',
        'PublicationDate': '2024-01-01T00:00:00.000Z',
        'Attributes': [{'Name': 'datasetIdentifier', 'Value': dataset_id}],
    }


@pytest.mark.parametrize(
    'example_path',
    _EXAMPLES,
    ids=[p.stem for p in _EXAMPLES],
)
async def test_get_collection_name_matches_example(example_path: Path):
    scene = _scene_for(example_path)
    expected = _expected_collection(example_path)

    if _CLMS_DIR in example_path.parents:
        with configure_odata_response(_fake_clms_odata_response(scene, expected)):
            result = await get_collection_name(scene)
    else:
        result = await get_collection_name(scene)

    assert result == expected


@pytest.mark.parametrize(
    'scene',
    [
        Path('S1__AUX_SCS_V20140406T133000_G20240612T132402.SAFE'),
        Path(
            'S2C_OPER_GIP_VIEDIR_MPC__20251010T000004_V20150622T000000_20251022T000000_B8A.TGZ'
        ),
        Path(
            'S2A_OPER_AUX_ECMWFD_PDMC_20150620T000000_V20150621T000000_G20150621T000000'
        ),
        Path(
            'S3A_SR___ROE_AX_20250112T172502_20250112T190642_20250112T192517___________________POD_O_NR____.SEN3.zip'
        ),
    ],
)
async def test_get_collection_name_returns_none_for_unmapped(scene: Path):
    assert await get_collection_name(scene) is None


async def test_get_collection_name_returns_none_for_gdalinfo():
    assert (
        await get_collection_name(Path('gdalinfo_only_input.tif'), gdalinfo=True)
        is None
    )


async def test_get_collection_name_returns_none_for_clms_not_found_in_odata(
    monkeypatch,
):
    async def _raise_not_found(*args, **kwargs):
        raise ValueError('Product not found in datahub.creodias.eu')

    monkeypatch.setattr(collection_name, 'get_odata_id', _raise_not_found)
    scene = Path('c_gls_UNKNOWN-PRODUCT_202101100000_GLOBE_OLCI_V1.1.1_nc')
    assert await get_collection_name(scene) is None


@pytest.mark.parametrize(
    ('name', 'expected'),
    [
        (
            'S3A_OL_1_EFR____20160406T012156_20160406T012355_20241003T093342_0119_002_345_1440_MAR_R_NT_004',
            'NT',
        ),
        (
            'S3B_OL_1_EFR____20230311T214926_20230311T214926_20230312T085631_0000_077_100_4320_PS2_O_NT_003.SEN3.zip',
            'NT',
        ),
        (
            'S3B_OL_1_EFR____20230311T214926_20230311T214926_20230312T085631_0000_077_100_4320_PS2_O_NT_003.SEN3',
            'NT',
        ),
        ('one_underscore', None),
        ('nounderscoresatall', None),
    ],
)
def test_timeliness_code(name: str, expected: str | None):
    assert _timeliness_code(Path(name)) == expected
