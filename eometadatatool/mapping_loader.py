import csv
from pathlib import Path
from typing import TYPE_CHECKING, Final, NamedTuple, TypedDict, cast

from eometadatatool.clas.mapping import read_mapping_file
from eometadatatool.custom_types import VALID_DATA_TYPES, DataType

if TYPE_CHECKING:
    from collections.abc import Iterable


class _MappingFileRow(TypedDict):
    metadata: str
    file: str
    mappings: str
    datatype: DataType | str


class MappingTarget(NamedTuple):
    xpath: str
    data_type: DataType


STATIC_METAFILE: Final[str] = 'static'


def load_mappings(
    scene: Path, *, local_override: bool
) -> dict[str, dict[str, MappingTarget]]:
    """Load mappings for the given scene.

    :param scene: Path to the scene.
    :param local_override: Whether to support "mappings.csv" local override.
    :return: Metadata mapping queries.
    """
    reader = csv.DictReader(
        read_mapping_file(scene, local_override=local_override).splitlines(),
        delimiter=';',
    )
    result: dict[str, dict[str, MappingTarget]] = {}
    for row in cast('Iterable[_MappingFileRow]', reader):
        xpath = row.get('mappings')
        if not xpath:
            continue
        data_type = row['datatype']
        if data_type not in VALID_DATA_TYPES:
            raise ValueError(f'Invalid datatype: {data_type!r}')

        if xpath[:1] == '=':
            xpath = xpath[1:]
            file = STATIC_METAFILE
        else:
            file = row['file']

        result.setdefault(file, {})[row['metadata']] = MappingTarget(
            xpath,
            data_type,
        )
    return result
