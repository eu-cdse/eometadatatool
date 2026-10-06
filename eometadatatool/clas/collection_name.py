import asyncio
import importlib
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from eometadatatool.clas.product_type import get_product_type
from eometadatatool.clas.template import detect_template_name
from eometadatatool.dlc import get_odata_id

_TIMELINESS_MAP = {'NR': 'nrt', 'NT': 'ntc', 'ST': 'stc'}

_S6_PRODUCT_TYPE_MAP = {
    'MW_2__AMR____': 'amr-c',
    'P4_1B_LR_____': 'p4-1b',
    'P4_2__LR_____': 'p4-2',
}


def _timeliness_code(scene: Path) -> str | None:
    """Extract the Sentinel-3/6 timeliness code (NR/NT/ST) from the filename.

    It is always the second-to-last underscore-delimited field, immediately
    before the baseline number, immediately before the .SEN3/.SEN6[.zip]
    suffix -- confirmed against real example filenames across every S3
    sub-mission.
    """
    stem = scene.name.removesuffix('.zip').removesuffix('.SEN3').removesuffix('.SEN6')
    parts = stem.rsplit('_', 2)
    return parts[-2] if len(parts) == 3 else None


def _s3_collection(
    detected_template: str, product_type: str, scene: Path
) -> str | None:
    timeliness = _timeliness_code(scene)
    if timeliness is None:
        return None

    match detected_template:
        case 'stac_s3_ol_1_earth':
            # sentinel-3-ol1-earth/template/stac_s3_ol_1_earth.py:139-141,146
            res = 'fr' if product_type.endswith('FR___') else 'rr'
            tl = 'nrt' if timeliness == 'NR' else 'ntc'
            return f'sentinel-3-olci-1-e{res}-{tl}'
        case 'stac_s3_ol_2_land':
            # sentinel-3-ol2-land/template/stac_s3_ol_2_land.py:179-181,186
            res = 'fr' if product_type.endswith('FR___') else 'rr'
            tl = 'nrt' if timeliness == 'NR' else 'ntc'
            return f'sentinel-3-olci-2-l{res}-{tl}'
        case 'stac_s3_ol_2_water':
            # sentinel-3-ol2-water/template/stac_s3_ol_2_water.py:226-228,233
            res = 'fr' if product_type.endswith('FR___') else 'rr'
            tl = 'nrt' if timeliness == 'NR' else 'ntc'
            return f'sentinel-3-olci-2-w{res}-{tl}'
        case 'stac_s3_sl_1_rbt':
            # sentinel-3-sl1-rbt/template/stac_s3_sl_1_rbt.py:702-706
            return (
                'sentinel-3-sl-1-rbt-nrt'
                if timeliness == 'NR'
                else 'sentinel-3-sl-1-rbt-ntc'
            )
        case 'stac_s3_sl_2_frp_lst_wst':
            # sentinel-3-sl2-frp-lst-wst/template/stac_s3_sl_2_frp_lst_wst.py:20-21,195
            subtype = product_type[5:8].lower()
            tl = 'nrt' if timeliness == 'NR' else 'ntc'
            return f'sentinel-3-sl-2-{subtype}-{tl}'
        case 'stac_s3_sr_1_sra':
            # sentinel-3-sr1-sra/template/stac_s3_sr_1_sra.py:108-117
            tl = _TIMELINESS_MAP.get(timeliness)
            if tl is None:
                return None
            suffix = '-a' if product_type == 'SR_1_SRA_A_' else ''
            return f'sentinel-3-sr-1-sra{suffix}-{tl}'
        case 'stac_s3_sr_2_lan_wat':
            # sentinel-3-sr2-lan-wat/template/stac_s3_sr_2_lan_wat.py:131-149
            tl = _TIMELINESS_MAP.get(timeliness)
            sub = {
                'SR_2_LAN___': '-lan',
                'SR_2_LAN_HY': '-lan-hy',
                'SR_2_LAN_LI': '-lan-li',
                'SR_2_LAN_SI': '-lan-si',
                'SR_2_WAT___': '-wat',
            }.get(product_type)
            if tl is None or sub is None:
                return None
            return f'sentinel-3-sr-2{sub}-{tl}'
        case 'stac_s3_sy_2_syn':
            # sentinel-3-sy2-syn/template/stac_s3_sy_2_syn.py:233-234,238
            tl = 'ntc' if timeliness == 'NT' else 'stc'
            return f'sentinel-3-syn-2-syn-{tl}'
        case 'stac_s3_sy_2_veg':
            # sentinel-3-sy2-veg/template/stac_s3_sy_2_veg.py:150-163,168
            sub = {
                'SY_2_V10___': '10-',
                'SY_2_VG1___': 'g1-',
                'SY_2_VGP___': 'gp-',
            }.get(product_type)
            tl = {'NT': 'ntc', 'ST': 'stc'}.get(timeliness)
            if sub is None or tl is None:
                return None
            return f'sentinel-3-syn-2-v{sub}{tl}'
        case _:
            return None


def _s5p_collection(scene: Path) -> str | None:
    name = scene.name
    subtype_key = name[9:19]  # e.g. 'L2__NO2___', 'L1B_RA_BD1'
    try:
        module = importlib.import_module(
            'eometadatatool.stac.sentinel-5p.template.stac_s5p'
        )
    except ImportError:
        return None
    subtype = module.PRODUCT_TYPE_MAP.get(subtype_key)
    if subtype is None:
        return None
    level = 1 if subtype_key.startswith('L1B') else 2
    timeliness = name[4:8].lower()  # 'offl' / 'nrti' / 'rpro'
    # Reuse the template's rule so CLAS and the rendered item cannot disagree:
    # NRTI keeps its own collection, OFFL/RPRO share one, L1 RA bands merge.
    return module.gen_collection_id(level, subtype, timeliness)


def _s6_collection(scene: Path) -> str | None:
    sub = _S6_PRODUCT_TYPE_MAP.get(scene.name[4:17])
    tl = _TIMELINESS_MAP.get(_timeliness_code(scene))
    if sub is None or tl is None:
        return None
    return f'sentinel-6-{sub}-{tl}'

def _s6_aux_collection(scene: Path) -> str | None:
    module = importlib.import_module(
        'eometadatatool.stac.sentinel-6-aux.template.stac_s6_aux'
    )
    return module._recognize_collection(scene.name)

def _landsat_collection(scene: Path) -> str | None:
    module = importlib.import_module(
        'eometadatatool.stac.landsat-c2-oli-tirs.template.stac_lc2_oli_tirs'
    )
    return module._recognize_collection(scene.name)

async def _landsat_legacy_collection(scene: Path) -> str | None:
    module = importlib.import_module(
        'eometadatatool.stac.landsat-legacy.template.stac_l5_l7'
    )
    if scene.name.startswith('LE7'):
        """For those products, collection name cannot be recognized from file name alone."""
        try:
            odata_content = await get_odata_id(
                str(scene), omit_date=True, omit_collection=True
            )
        except ValueError:
            return None

        product_type = (odata_content.attributes or {}).get('processingLevel')

        if product_type is None:
            return None

        return module.get_collection_name(scene.name, product_type.lower().replace('level', 'l'))
    else:
        return module.get_collection_name(scene.name, None)


def _clms_landcover_landuse_collection(scene: Path) -> str | None:
    module = importlib.import_module(
        'eometadatatool.stac.clms-landcover-landuse.template.const'
    )
    try:
        _product_type, cfg = module.get_config(scene.name)
    except KeyError:
        return None
    return cfg['collection']


async def _clms_collection(scene: Path) -> str | None:
    """Query OData for the dataset identifier instead of relying on a fixed
    storage-path depth (see clms/template/stac_clms.py:142-149's
    `identify_product`, which needs `scene` to be the full s3 path).
    """
    try:
        odata_content = await get_odata_id(
            str(scene), omit_date=True, omit_collection=True
        )
    except ValueError:
        return None

    dataset_id = (odata_content.attributes or {}).get('datasetIdentifier')
    if dataset_id is None:
        return None

    module = importlib.import_module('eometadatatool.stac.clms.template.stac_clms')
    file_type = module.identify_type(scene.name)
    if file_type is None:
        return None

    return f'clms_{dataset_id}_{file_type}'


def _modis_collection(scene: Path) -> str | None:
    """modis/template/stac_modis.py:88,107,197-206.

    `attr['productType']` is XML-derived (`ShortName.VersionId`), but its
    first ('.'-split) component always equals the filename's own prefix up
    to the first dot (confirmed against every example in
    eometadatatool/stac/modis/example/) -- so no XML parsing is needed here.
    """
    module = importlib.import_module('eometadatatool.stac.modis.template.stac_modis')
    product = scene.name.split('.')[0]
    platform = module.PRODUCT_PREFIX_TO_PLATFORM.get(product[:3].upper())
    if platform is None:
        return None
    return f'modis-{"".join(platform)}-{product.lower()}'


def _copdem_cog_collection(scene: Path) -> str | None:
    # copdem-cog/template/stac_copdem_cog.py:18-22,70
    name = scene.name
    if '_COG_10_' in name:
        return 'cop-dem-glo-30-dged-cog'
    if '_COG_30_' in name:
        return 'cop-dem-glo-90-dged-cog'
    return None


async def get_collection_name(scene: Path, *, gdalinfo: bool = False) -> str | None:
    product_type = get_product_type(scene, gdalinfo=gdalinfo)
    detected_template = detect_template_name(scene, product_type=product_type)

    match detected_template:
        ## Sentinel-1
        case 'stac_s1_card_bs':
            return 'sentinel-1-card-bs'  # sentinel-1-card-bs/template/stac_s1_card_bs.py
        case 'stac_s1_etad':
            return 'sentinel-1-etad'  # sentinel-1-etad/template/stac_s1_etad.py:144
        case 'stac_s1_grd':
            return 'sentinel-1-grd'  # sentinel-1-grd-cog/template/stac_s1_grd.py:156
        case 'stac_s1_mosaic':
            return 'sentinel-1-global-mosaics'  # sentinel-1-mosaic/templates/stac_s1_mosaic.py:114
        case 'stac_s1_ocn':
            # sentinel-1-ocn/template/stac_s1_ocn.py:133,209,233,254
            return (
                'sentinel-1-ocn-wv' if product_type == 'S1_WV_OCN' else 'sentinel-1-ocn'
            )
        case 'stac_s1_slc':
            return 'sentinel-1-slc'  # sentinel-1-slc/template/stac_s1_slc.py:180
        case 'stac_s1_slc_wv':
            return (
                'sentinel-1-slc-wv'  # sentinel-1-slc-wv/template/stac_s1_slc_wv.py:181
            )
        case 'stac_s1_aux_ipf':
            return f'sentinel-1-aux-{product_type[4:7].lower()}' # sentinel-1-aux-ipf/template/stac_s1_aux_ipf.py:57

        ## Sentinel-2
        case 'stac_s2_gri_l1c':
            return 'sentinel-2-gri-l1c'  # sentinel-2-gri-l1c/template/stac_s2_gri_l1c.py:114
        case 'stac_s2_gri_l1c_gcp':
            return 'sentinel-2-gri-l1c-gcp'  # sentinel-2-gri-l1c-gcp/template/stac_s2_gri_l1c_gcp.py:105
        case 'stac_s2l1c':
            return 'sentinel-2-l1c'  # sentinel-2-l1c/template/stac_s2l1c.py:231
        case 'stac_s2l2a':
            return 'sentinel-2-l2a'  # sentinel-2-l2a/template/stac_s2l2a.py:606
        case 'stac_s2_mosaic':
            return 'sentinel-2-global-mosaics'  # sentinel-2-mosaic/template/stac_s2_mosaic.py:127

        ## Sentinel-3
        case (
            'stac_s3_ol_1_earth'
            | 'stac_s3_ol_2_land'
            | 'stac_s3_ol_2_water'
            | 'stac_s3_sl_1_rbt'
            | 'stac_s3_sl_2_frp_lst_wst'
            | 'stac_s3_sr_1_sra'
            | 'stac_s3_sr_2_lan_wat'
            | 'stac_s3_sy_2_syn'
            | 'stac_s3_sy_2_veg'
        ):
            return _s3_collection(detected_template, product_type, scene)
        case 'stac_s3_sl_2_aod':
            return 'sentinel-3-sl-2-aod-nrt'  # sentinel-3-sl2-aod/template/stac_s3_sl_2_aod.py:95
        case 'stac_s3_sy_2_aod':
            return 'sentinel-3-syn-2-aod-ntc'  # sentinel-3-sy2-aod/template/stac_s3_sy_2_aod.py:88

        ## Sentinel-5P
        case 'stac_s5p':
            return _s5p_collection(scene)

        ## Sentinel-6
        case 'stac_s6':
            return _s6_collection(scene)
        case 'stac_s6_aux':
            return _s6_aux_collection(scene)

        ## Landsat
        case 'stac_lc2_oli_tirs':
            return _landsat_collection(scene)
        case 'stac_landsat_mosaic':
            # landsat-mosaic/template/stac_landsat_mosaic.py:135
            return 'opengeohub-landsat-bimonthly-mosaic-v1.0.1'
        case 'stac_l5_l7':
            return await _landsat_legacy_collection(scene)

        ## CLMS
        case 'stac_ua':
            return 'clms_ua_building-height_europe_10m_3yearly_v1'  # urbanatlas-raster/template/stac_ua.py:75
        case 'stac_clms_landcover_landuse':
            return _clms_landcover_landuse_collection(scene)
        case 'stac_clms':
            return await _clms_collection(scene)

        ## COP-DEM
        case 'stac_copdem_insp':
            return 'cop-dem-eea-10-laea-tif'  # copdem-insp/template/stac_copdem_insp.py:116
        case 'stac_copdem_cog':
            return _copdem_cog_collection(scene)

        ## CCM
        case 'stac_ccm_optical':
            return 'ccm-optical'  # ccm-optical/template/stac_ccm_optical.py:183
        case 'stac_ccm_sar':
            return 'ccm-sar'  # ccm-sar/template/stac_ccm_sar.py:130

        ## MODIS
        case 'stac_modis':
            return _modis_collection(scene)

        ## No fixed collection: generic/fallback templates (stac_gdalinfo,
        ## stac_odata), or missions needing deep-parsed metadata not
        ## available from the filename alone.
        case _:
            return None


if __name__ == '__main__':
    parser = ArgumentParser(
        description=(
            'Print STAC collection ID for a product, derived from its filename.\n\n'
            'Covers Sentinel-1/2/3/5P/6, Landsat, MODIS, CLMS, CCM, and\n'
            'Copernicus DEM products; prints None for unknown collections.'
        ),
        epilog=(
            'examples:\n'
            '  %(prog)s S2A_MSIL2A_20220217T183431_N0510_R027_T13VEK_20240516T022440.SAFE\n'
            '    -> sentinel-2-l2a\n\n'
            '  %(prog)s S3A_OL_1_EFR____20160406T012156_20160406T012355_20241003T093342_0119_002_345_1440_MAR_R_NT_004.SEN3\n'
            '    -> sentinel-3-olci-1-efr-ntc\n\n'
            '  %(prog)s MOD17A2H.A2021001.h00v08.061.2021069214628.hdf\n'
            '    -> modis-terra-mod17a2h'
        ),
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'scene',
        type=Path,
        help='path to the scene (local file/folder, or a bare filename)',
    )
    args = parser.parse_args()
    print(asyncio.run(get_collection_name(args.scene)))
