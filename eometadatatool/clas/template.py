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

    # Landsat 8+
    if (name.startswith(('LO', 'LC', 'LT')) and '_L1' in name) or (
        name.startswith('LC') and '_L2' in name
    ):
        return 'stac_lc2_oli_tirs'

    # Landsat 5 + 7
    if name.startswith('LS05') or name.startswith('LS07') or name.startswith('LE7'):
        return 'stac_l5_l7'

    # Sentinel-1
    if name.startswith('S1'):
        if '_CARD_BS' in name:
            return 'stac_s1_card_bs'
        if '_GRD' in name:
            return 'stac_s1_grd'
        if '_SLC_' in name:
            if '_WV_' in name:
                return 'stac_s1_slc_wv'
            else:
                return 'stac_s1_slc'
        if '_ETA' in name:
            return 'stac_s1_etad'
        if '_OCN_' in name:
            return 'stac_s1_ocn'
        if 'CAL' in name or 'PP1' in name or 'PP2' in name or 'ML2' in name or 'INS' in name:
            return 'stac_s1_aux_ipf'

    # Sentinel-2
    if name.startswith('S2'):
        if '_MSIL1C_' in name:
            return 'stac_s2l1c'
        elif '_MSIL2A_' in name:
            return 'stac_s2l2a'
        elif 'L1C_GCP' in name:
            return 'stac_s2_gri_l1c_gcp'
        elif 'GRIL1C' in name:
            return 'stac_s2_gri_l1c'
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
        if '_OPER_AUX_' in name or name[4:6] == 'AX' or name[3:7] == 'COMB':
            return 'stac_s6_aux'
        return 'stac_s6'

    # CCM SAR
    if name.startswith(('CS00', 'IE00', 'PAZ1', 'RS02', 'TX01')):
        return 'stac_ccm_sar'

    # CCM OPTICAL
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
        return 'stac_ccm_optical'

    # COP DEM
    if name.startswith('DEM1'):
        return 'stac_copdem_insp'

    # GLOBAL-MOSAICS
    if 'mosaic' in name:
        if 'Sentinel-1' in name:
            return 'stac_s1_mosaic'
        if 'Sentinel-2' in name:
            return 'stac_s2_mosaic'

    # COPDEM COG
    if name.startswith('Copernicus_DSM') and 'COG' in name:
        return 'stac_copdem_cog'

    # MODIS
    if name.startswith(('MOD', 'MYD', 'MCD')):
        return 'stac_modis'

    # Urban Atlas
    if name.startswith('CLMS_UA_BBH'):
        return 'stac_ua'

    # CLMS Land Cover Land Use

    if name.startswith(('CLMS_HRLVLCC', 'CLMS_CLCPLUS_')):
        return 'stac_clms_landcover_landuse'

    if name.startswith('Landsat_mosaic'):
        return 'stac_landsat_mosaic'

    # CLMS
    if (
        'c_gls' in name
        or 'cgl' in name
        or 'PROBAV_LC100' in name
        or 'clms' in name
        or 'LCFM_LCM-10' in name
        or 'LCFM_TCD-10' in name
    ):
        return 'stac_clms'

    return None
