from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path

import orjson

from eometadatatool.custom_types import ProductType


@lru_cache(maxsize=256)
def get_product_type(scene: Path, *, gdalinfo: bool = False) -> ProductType:
    return ProductType(_from_scene(scene) if not gdalinfo else 'GDALINFO')


def _from_scene(scene: Path) -> str:
    parent_names = {p.name for p in scene.parents}
    name = scene.name
    if name.startswith((
        'AL01',
        'AR3D',
        'DM01',
        'DM02',
        'EW02',
        'EW03',
        'FO02',
        'GY01',
        'IR06',
        'IR07',
        'KS03',
        'KS04',
        'PH1A',
        'PH1B',
        'PL00',
        'PN03',
        'QB02',
        'RE00',
        'S20A',
        'SP04',
        'SP05',
        'SP06',
        'SW00',
        'TR00',
        'UK02',
        'VS01',
    )):
        return 'CCM_OPTICAL'
    if name.startswith(('CS00', 'IE00', 'PAZ1', 'RS02', 'TX01')):
        return 'CCM_SAR'
    if name.startswith('DEM1'):
        return 'CCM_DEM'
    if name.startswith('Sentinel-1'):
        if 'DH' in name:
            return 'S1SAR_L3_DH_MCM'
        elif 'IW' in name:
            return 'S1SAR_L3_IW_MCM'
    if name.startswith('S1'):
        if name.startswith('S1B') and ('GRDH' in name or 'GRDM' in name):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_B'
        elif name.startswith('S1C') and ('GRDH' in name or 'GRDM' in name):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_C'
        elif name.startswith('S1B'):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_B'
        elif name.startswith('S1C'):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_C'
        else:
            return name.replace('_OPER', '')[4:14].replace('_V2', '')
    if name.startswith('S2') and 'HR_IMAGE_2015' not in str(scene):
        if '_MSIL1C_' in name:
            return 'MSI_L1C'
        if '_MSIL2A_' in name:
            return 'MSI_L2A'
        return name[9:19]
    if name.startswith('S3'):
        return name[4:15]
    if name.startswith('S5P'):
        return f'S5P{name[8:20]}'
    if name.startswith(('S6A_P4', 'S6B_P4')):
        return f'S6_{name[4:6]}'
    if name.startswith(('S6A_MW_2__AMR', 'S6B_MW_2__AMR')):
        return f'S6_{name[10:13]}'
    if name.startswith(('LO09_L1', 'LC09_L1', 'LT09_L1')):
        return 'L09L1'
    if name.startswith('LC09_L2SP'):
        return 'LC09_L2SR'
    if 'Sentinel-1-RTC' in parent_names:
        return 'RTC'
    if name.startswith('Sentinel-2_mosaic'):
        return 'S2MSI_L3__MCQ'
    if name.startswith('Copernicus_DSM') and 'COG' in name:
        return 'COPDEM_COG'
    if name.startswith('Landsat_mosaic'):
        return 'LS_MOSAIC'

    if scene.suffix.lower() == '.json' and scene.is_file() and 'stac_version' in orjson.loads(scene.read_bytes()):
        return 'STAC'

    raise ValueError(f'Could not identify product type for {name!r}')


if __name__ == '__main__':
    parser = ArgumentParser(description='Sentinel metadata parser')
    parser.add_argument(
        'scene',
        type=Path,
        help='Path to Sentinel scene (zipped file or folder)',
    )
    args = parser.parse_args()
    print(get_product_type(args.scene))
