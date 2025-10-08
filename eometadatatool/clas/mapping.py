import csv
import importlib.resources
import logging
from argparse import ArgumentParser
from collections.abc import Mapping
from functools import cache
from importlib.resources.abc import Traversable
from pathlib import Path

from eometadatatool.clas.product_type import get_product_type
from eometadatatool.custom_types import ProductType


@cache
def _get_mapping_config() -> Mapping[ProductType, str]:
    with importlib.resources.open_text(
        'eometadatatool.mappings', 'ProductTypes2RuleMapping.csv'
    ) as f:
        reader = csv.DictReader(f, delimiter=';')
        return {ProductType(row['ESAProductType']): row['RuleName'] for row in reader}


def get_mapping_name(scene: Path) -> str:
    product_type = get_product_type(scene)
    result = f'{_get_mapping_config()[product_type]}.csv'
    logging.debug('get_mapping_name: %r → %r', product_type, result)
    return result


@cache
def _get_mapping_resources() -> Mapping[str, Traversable]:
    result: dict[str, Traversable] = {}
    search_dirs: list[Traversable] = [
        importlib.resources.files('eometadatatool.mappings'),
        importlib.resources.files('eometadatatool.stac'),
    ]
    while search_dirs:
        for p in search_dirs.pop().iterdir():
            if p.name[:1] == '.':  # skip hidden files
                continue
            if p.is_dir():
                search_dirs.append(p)
                continue
            if p.name[-4:] == '.csv':
                result[p.name] = p
    logging.debug('Found %d mapping files', len(result))
    return result


def read_mapping_file(scene: Path, *, local_override: bool) -> str:
    # support an overriding mapping file
    if local_override:
        mapping = scene.with_name('mappings.csv')
        if mapping.is_file():
            return mapping.read_text()
    return _get_mapping_resources()[get_mapping_name(scene)].read_text()


if __name__ == '__main__':
    parser = ArgumentParser(description='Sentinel metadata parser')
    parser.add_argument(
        'scene',
        type=Path,
        help='Path to Sentinel scene (zipped file or folder)',
    )
    args = parser.parse_args()
    print(get_mapping_name(args.scene))
