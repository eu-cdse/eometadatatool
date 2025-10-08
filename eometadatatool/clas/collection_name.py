from collections.abc import Mapping
from pathlib import Path
from typing import Final

from eometadatatool.clas.product_type import get_product_type


def get_collection_name(scene: Path, *, gdalinfo: bool = False) -> str:
    product_type = get_product_type(scene, gdalinfo=gdalinfo)
    match sensor := scene.name[:2]:
        case 'S1':
            level = _LEVELS.get(product_type[8:9])
            return (
                'S1.AUX'
                if level is None or (product_type[:2] in {'GP', 'HK'})
                else f'S1.SAR.{level}'
            )
        case 'S2':
            level = (
                _LEVELS.get(product_type[4:6])  #
                if product_type[:3] == 'MSI'
                else None
            )
            return 'S2.AUX' if level is None else f'S2.MSI.{level}'
        case 'S3':
            level = (
                _LEVELS.get(product_type[3:4])  #
                if product_type[9:11] != 'AX'
                else None
            )
            s3_type = _S3_TYPES.get(product_type[:2])
            return (
                'S3.AUX'
                if level is None or s3_type is None
                else f'{sensor}.{s3_type}.{level}'
            )
        case _:
            return 'UNK'


_LEVELS: Final[Mapping[str, str]] = {
    '0': 'L0',
    'L0': 'L0',
    '1': 'L1',
    'L1': 'L1',
    '2': 'L2',
    'L2': 'L2',
    '1A': 'L1A',
    '1B': 'L1B',
    '1C': 'L1C',
    '2A': 'L2A',
    '3A': 'L3A',
}

_S3_TYPES: Final[Mapping[str, str]] = {
    'OL': 'OLCI',
    'SR': 'SRAL',
    'SL': 'SLSTR',
    'SY': 'Synergy',
    'DO': 'DORIS',
    'MW': 'MWR',
    'AX': 'AUX',
    'GN': 'GNSS',
    'TM': 'TM',
}
