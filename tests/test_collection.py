"""Validation of collection JSONs.

Walks every ``eometadatatool/stac/{mission}/template``,
gathers collection JSONs and validates using stac_validator.
"""
import json
from pathlib import Path

import pytest
from stac_validator import stac_validator
from constants import _STAC_DIR

collections_list: list[Path] = list(_STAC_DIR.glob('**/template*/*collection*.json'))

@pytest.mark.parametrize('col', collections_list, ids=[path.stem for path in collections_list])
def test_collection(col: Path):
    collection: dict = json.loads(col.read_bytes())

    validator = stac_validator.StacValidate()
    validator.validate_dict(collection)

    if validator.message[0]['valid_stac'] is not True:
        with Path('test_collection_output.json').open('a') as f:
            json.dump({col.stem: validator.message[0]['error_message']}, f, indent=2)

    assert validator.message[0]['valid_stac'] is True, (
        f'{col.stem} is not valid, error message: {validator.message[0]["error_message"]}'
    )
