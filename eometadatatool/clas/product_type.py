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
        'PN04',
        'QB02',
        'RE00',
        'S20A',
        'SP04',
        'SP05',
        'SP06',
        'SP07',
        'SW00',
        'TR00',
        'UK02',
        'VS01',
    )):
        return 'CCM_OPTICAL'
    if name.startswith(('CS00', 'IE00', 'PAZ1', 'RS02', 'TX01')):
        return 'CCM_SAR'
    if name.startswith('DEM1'):
        return 'COPDEM_INSP'
    if name.startswith('Sentinel-1'):
        if 'DH' in name:
            return 'S1SAR_L3_DH_MCM'
        elif 'IW' in name:
            return 'S1SAR_L3_IW_MCM'
    if name.startswith('S1'):
        if '_CARD_BS' in name:
            return 'CARD_BS'
        if name.startswith('S1B') and ('GRDH' in name or 'GRDM' in name):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_B'
        elif name.startswith('S1C') and ('GRDH' in name or 'GRDM' in name):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_C'
        elif name.startswith('S1D') and ('GRDH' in name or 'GRDM' in name):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_D'
        elif (name.startswith('S1') and '_ETA' in name) or (
            name.startswith('S1') and '_OCN_' in name
            ):
            return f'S1_{name[4:10]}'
        elif (name.startswith('S1') and ('CAL' in name or 'PP1' in name or 'PP2' in name or 'ML2' in name or 'INS' in name)):
            return f'{name[4:11]}'
        elif name.startswith('S1B'):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_B'
        elif name.startswith('S1C'):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_C'
        elif name.startswith('S1D'):
            return name.replace('_OPER', '')[4:14].replace('_V2', '') + '_D'
        else:
            return name.replace('_OPER', '')[4:14].replace('_V2', '')
    if name.startswith('S2') and 'HR_IMAGE_2015' not in str(scene):
        if '_MSIL1C_' in name and 'GRI' not in name:
            return 'MSI_L1C'
        if '_MSIL2A_' in name:
            return 'MSI_L2A'
        if '_GRI_L1C_GCP_' in name:
            return 'GRI_L1C_GCP'
        if '_GRIL1C_' in name:
            return 'GRI_MSIL1C'
        return name[9:19]
    if name.startswith('S3'):
        return name[4:15]
    if name.startswith('S5P'):
        return f'S5P{name[8:20]}'
    if name.startswith(('S6A_P4', 'S6B_P4')):
        return f'S6_{name[4:6]}'
    if name.startswith(('S6A_MW_2__AMR', 'S6B_MW_2__AMR')):
        return f'S6_{name[10:13]}'
    if name.startswith('S6'):
        if '_OPER_AUX_' in name:
            return f'S6_{name[9:19]}'
        if name[4:6] == 'AX':
            return f'S6_{name[4:17]}'
        if name[3:7] == 'COMB':
            return 'S6_AUX_COMB'
    if name.startswith('LS05'):
        if 'TM__GEO_1P' in name:
            return 'TM__GEO_1P'
        elif 'TM__GTC_1P' in name:
            return 'TM__GTC_1P'
    if name.startswith('LS07') and 'ETM_GTC_1P' in name:
        return 'ETM_GTC_1P'
    if name.startswith('LE7'):
        return 'L7_USGS'
    if name.startswith(('LO08', 'LO09')) and '_L1' in name:
        return 'LOL1'  # oli
    if name.startswith(('LC08', 'LC09')) and '_L1' in name:
        return 'LCL1'  # oli/tirs
    if name.startswith(('LT08', 'LT09')) and '_L1' in name:
        return 'LTL1'  # tirs
    if name.startswith(('LC08', 'LC09')) and '_L2' in name:
        return 'LCL2'  # oli/tirs
    if 'Sentinel-1-RTC' in parent_names:
        return 'RTC'
    if name.startswith('Sentinel-2_mosaic'):
        return 'S2MSI_L3__MCQ'
    if name.startswith('Copernicus_DSM') and 'COG' in name:
        return 'COPDEM_COG'
    if name.startswith('Landsat_mosaic'):
        return 'LS_MOSAIC'
    if (name.startswith('c_gls') or name.startswith('cgl')) and '_nc' in name:
        return 'CLMS_netcdf'
    if (
        name.startswith('c_gls')
        or name.startswith('cgl')
        or name.startswith('PROBAV_LC100')
        or name.startswith('clms')
        or name.startswith('LCFM_LCM-10')
        or name.startswith('LCFM_TCD-10')
    ) and '_cog' in name:
        return 'CLMS_cog'
    if name.startswith('c_gls') and '_geojson' in name:
        return 'CLMS_geojson'
    if name.startswith('MOD'):
        return 'MODIS_TERRA'
    if name.startswith('MYD'):
        return 'MODIS_AQUA'
    if name.startswith('MCD'):
        return 'MODIS_TERRA_AQUA'
    if name.startswith('CLMS_UA_BBH'):
        return 'UA'
    if name.startswith((
        'CLMS_HRLVLCC_BCD_',
        'CLMS_HRLVLCC_CCD_',
        'CLMS_HRLVLCC_DLTC_',
        'CLMS_HRLVLCC_DLTCL_',
        'CLMS_HRLVLCC_DLT_',
        'CLMS_HRLVLCC_FTY_',
        'CLMS_HRLVLCC_FADSL_',
        'CLMS_HRLVLCC_TCD_',
        'CLMS_HRLVLCC_TCDCL_',
        'CLMS_HRLVLCC_TCPC_',
        'CLMS_HRLVLCC_TCPCCL_',
        'CLMS_HRLVLCC_GRACCL_',
        'CLMS_HRLVLCC_GRAC_',
        'CLMS_HRLVLCC_GRACL_',
        'CLMS_HRLVLCC_GRA_',
        'CLMS_HRLVLCC_HER_',
        'CLMS_HRLVLCC_PLOUGH_',
        'CLMS_HRLVLCC_GRAMD',
        'CLMS_HRLVLCC_GRAMECL_',
        'CLMS_HRLVLCC_GRAME_',
        'CLMS_HRLVLCC_CTY_',
        'CLMS_HRLVLCC_CTYCL_',
        'CLMS_HRLVLCC_CPFLPCL_',
        'CLMS_HRLVLCC_CPBSA_',
        'CLMS_HRLVLCC_CPBSACL_',
        'CLMS_HRLVLCC_CPBSB_',
        'CLMS_HRLVLCC_CPBSBCL_',
        'CLMS_HRLVLCC_CPCST_',
        'CLMS_HRLVLCC_CPCSY_',
        'CLMS_HRLVLCC_CPFLD_',
        'CLMS_HRLVLCC_CPFLDCL_',
        'CLMS_HRLVLCC_CPFLP_',
        'CLMS_HRLVLCC_CPFLPCL_',
        'CLMS_HRLVLCC_CPMCD_',
        'CLMS_HRLVLCC_CPMCDCL_',
        'CLMS_HRLVLCC_CPMCE_',
        'CLMS_HRLVLCC_CPMCECL_',
        'CLMS_HRLVLCC_CPMCH_',
        'CLMS_HRLVLCC_CPMCHCL_',
        'CLMS_HRLVLCC_CPSCD_',
        'CLMS_HRLVLCC_CPSCDCL_',
        'CLMS_HRLVLCC_CPSCE_',
        'CLMS_HRLVLCC_CPSCT_',
        'CLMS_CLCPLUS_LULUCF-INSTANCE_',
    )):
        return 'CLMS_LL'

    if (
        scene.suffix.lower() == '.json'
        and scene.is_file()
        and 'stac_version' in orjson.loads(scene.read_bytes())
    ):
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
