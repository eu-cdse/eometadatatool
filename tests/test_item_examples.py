import json
from pathlib import Path

import pytest
from stac_validator import stac_validator

_MAIN_DIR = Path(__file__).parent.parent

examples_list: list[Path] = list(_MAIN_DIR.glob('**/example*/*.json'))


@pytest.mark.parametrize('item_example', examples_list)
def test_item_examples(item_example: Path):
    item: dict = json.loads(item_example.read_bytes())

    item['links'].append({
        'rel': 'collection',
        'href': 'https://www.google.com',
        'type': 'application/json',
        'title': 'Placeholder collection link',
    })

    validator = stac_validator.StacValidate()
    validator.validate_dict(item)
    
    if validator.message[0]['valid_stac'] is not True:
        with Path('test_item_examples_output.json').open('a') as f:
            json.dump({item_example.stem: validator.message[0]['error_message']}, f, indent=2)

    assert validator.message[0]['valid_stac'] is True, (
        f'Item {item_example.stem} is not valid, error message: {validator.message[0]["error_message"]}'
    )
