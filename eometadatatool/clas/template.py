import logging
from functools import lru_cache
from pathlib import Path

from eometadatatool.custom_types import ProductType, TemplateName


@lru_cache(maxsize=256)
def detect_template_name(
    scene: Path, *, product_type: ProductType
) -> TemplateName | None:
    """Detect the corresponding template basename based from the scene."""
    if product_type == 'GDALINFO':
        template_name = 'stac_gdalinfo'
    elif product_type == 'STAC':
        template_name = 'stac_odata'
    else:
        template_name = _from_scene(scene)

    if template_name is not None:
        logging.debug('Detected template name %r from scene %r', template_name, scene)
        return TemplateName(template_name)
    else:
        logging.debug('Could not detect template name from scene %r', scene)
        return None


def _from_scene(scene: Path) -> str | None:
    name = scene.name

    # Landsat
    if name.startswith('LO') and '_L1GT_' in name:
        return 'stac_landsat_l1_oli'
    if name.startswith('LC') and '_L1GT_' in name:
        return 'stac_landsat_l1_oli_tirs'
    if name.startswith('LT') and '_L1GT_' in name:
        return 'stac_landsat_l1_tirs'

    # Sentinel-1
    if name.startswith('S1'):
        if '_GRD' in name:
            return 'stac_s1_grd'
        if '_SLC_' in name:
            if '_WV_' in name:
                return 'stac_s1_slc_wv'
            else:
                return 'stac_s1_slc'

    # Sentinel-2
    if name.startswith('S2') and '_MSIL1C_' in name:
        return 'stac_s2l1c'
    if name.startswith('S2') and '_MSIL2A_' in name:
        return 'stac_s2l2a'
    if name.startswith('Sentinel-2_mosaic_'):
        return 'stac_s2_mosaic'

    # Sentinel-3 OL
    if name.startswith('S3') and 'OL_1_E' in name:
        return 'stac_s3_ol_1_earth'
    if name.startswith('S3') and 'OL_2_L' in name:
        return 'stac_s3_ol_2_land'
    if name.startswith('S3') and 'OL_2_W' in name:
        return 'stac_s3_ol_2_water'

    # Sentinel-3 SL
    if name.startswith('S3') and 'SL_1_RBT____' in name:
        return 'stac_s3_sl_1_rbt'
    if name.startswith('S3') and 'SL_2_AOD____' in name:
        return 'stac_s3_sl_2_aod'
    if name.startswith('S3') and (
        'SL_2_FRP____' in name  #
        or 'SL_2_LST____' in name
        or 'SL_2_WST____' in name
    ):
        return 'stac_s3_sl_2_frp_lst_wst'

    # Sentinel-3 SR
    if name.startswith('S3') and (
        'SR_1_SRA____' in name  #
        or 'SR_1_SRA_A__' in name
        or 'SR_1_SRA_BS_' in name
    ):
        return 'stac_s3_sr_1_sra'

    if name.startswith('S3') and (
        'SR_2_LAN____' in name
        or 'SR_2_LAN_HY_' in name
        or 'SR_2_LAN_LI_' in name
        or 'SR_2_LAN_SI_' in name
        or 'SR_2_WAT____' in name
    ):
        return 'stac_s3_sr_2_lan_wat'

    # Sentinel-3 SY
    if name.startswith('S3') and 'SY_2_AOD____' in name:
        return 'stac_s3_sy_2_aod'
    if name.startswith('S3') and 'SY_2_SYN____' in name:
        return 'stac_s3_sy_2_syn'
    if name.startswith('S3') and (
        'SY_2_V10____' in name  #
        or 'SY_2_VG1____' in name
        or 'SY_2_VGP____' in name
    ):
        return 'stac_s3_sy_2_veg'

    # Sentinel-5P
    if name.startswith('S5P_') and (
        '_L1B_RA_BD' in name
        or '_L2__AER_AI_' in name
        or '_L2__AER_LH_' in name
        or '_L2__CH4____' in name
        or '_L2__CLOUD__' in name
        or '_L2__CO_____' in name
        or '_L2__HCHO___' in name
        or '_L2__NO2____' in name
        or '_L2__NP_BD3_' in name
        or '_L2__NP_BD6_' in name
        or '_L2__NP_BD7_' in name
        or '_L2__O3_____' in name
        or '_L2__O3__PR_' in name
        or '_L2__O3_TCL_' in name
        or '_L2__SO2____' in name
    ):
        return 'stac_s5p'

    # Sentinel-6
    if name.startswith('S6'):
        return 'stac_s6'

    # CCM SAR
    if 'SAR_SEA_ICE' in str(scene) or 'DWH_MG1_CORE_11' in str(scene):
        return 'stac_ccm_sar'

    # CCM OPTICAL
    elif any(
        key in str(scene)
        for key in [
            'VHR_IMAGE_2024',
            'VHR_IMAGE_2021',
            'VHR_IMAGE_2018',
            'VHR_IMAGE_2015',
            'Urban_Atlas_2012',
            'DAP_MG2b_01',
            'DAP_MG2b_02',
            'DWH_MG2b_CORE_03',
            'HR_IMAGE_2015',
            'Image2012',
            'DWH_MG2_CORE_01',
            'Image2006',
            'Image2009',
            'DWH_MG2_CORE_02',
            'DAP_MG2-3_01',
            'DWH_MG2_CORE_09',
            'EUR_HR2_MULTITEMP',
            'DWH_MG2-3_CORE_08',
            'MR_IMAGE_2015',
            'DEM_VHR_2018',
        ]
    ):
        return 'stac_ccm_optical'

    # CCM DEM
    elif 'COP-DEM' in str(scene):
        return 'stac_ccm_dem'

    # GLOBAL-MOSAICS
    if 'mosaic' in name:
        if 'Sentinel-1' in name:
            return 'stac_s1_mosaic'
        if 'Sentinel-2' in name:
            return 'stac_s2_mosaic'

    # COPDEM COG
    if name.startswith('Copernicus_DSM') and 'COG' in name:
        return 'stac_copdem_cog'

    if name.startswith('Landsat_mosaic'):
        return 'stac_landsat_mosaic'

    return None
