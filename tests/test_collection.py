import json
from pathlib import Path

import pytest
from stac_validator import stac_validator

_MAIN_DIR = Path(__file__).parent.parent

collections_list: list[Path] = list(_MAIN_DIR.glob('**/template*/*collection*.json'))


@pytest.mark.parametrize('col', collections_list)
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
