from collections.abc import Collection
from itertools import product
from typing import Any, TypedDict, Unpack, cast

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    EOBand,
    OLCI_Bands,
    SLSTR_Bands,
    STACBand,
    generate_bands,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import (
    STACLink,
    TraceabilityLink,
    ZipperLink,
)


class _NetCDFExtra(TypedDict, total=False):
    bands: Collection[STACBand]


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': ('olci', 'slstr'),
        'gsd': 300,
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'eo:cloud_cover': round(attr['cloudCover'], 2),
        'product:type': attr['productType'],
        'product:timeliness': 'P1M' if attr['timeliness'] == 'NT' else 'PT48H',
        'product:timeliness_category': attr['timeliness'],
        'statistics': {
            'saline_water': attr['salineWaterCover'],
            'coastal': attr['coastalCover'],
            'fresh_inland_water': attr['freshInlandWaterCover'],
            'tidal_region': attr['tidalRegionCover'],
            'land': attr['landCover'],
        },
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'xfdumanifest': ProductManifestAsset(
            path=f'{item_path}/xfdumanifest.xml',
        ),
    }

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    def add_netcdf(key: str, title: str, **extra: Unpack[_NetCDFExtra]) -> None:
        local_path = str(attr[f'asset:{key}'])
        assets[key] = NetCDFAsset(
            path=f'{item_path}/{local_path}',
            title=title,
            checksum=attr[f'asset:{key}:checksum'],
            size=attr[f'asset:{key}:size'],
            extra=extra,
        )

    olci_bands = cast(
        'list[EOBand]',
        generate_bands(
            OLCI_Bands,
            [
                'Oa01',
                'Oa02',
                'Oa03',
                'Oa04',
                'Oa05',
                'Oa06',
                'Oa07',
                'Oa08',
                'Oa09',
                'Oa10',
                'Oa11',
                'Oa12',
                'Oa16',
                'Oa17',
                'Oa18',
                'Oa21',
            ],
        ),
    )
    slstr_bands = cast(
        'list[EOBand]',
        generate_bands(
            SLSTR_Bands,
            [
                'S1',
                'S2',
                'S3',
                'S5',
                'S6',
            ],
        ),
    )

    sdr_bands = slstr_bands + olci_bands
    add_netcdf(
        'flags',
        'Classification and quality Flags associated with OLCI, SLSTR and SYNERGY products',
    )
    add_netcdf(
        'geolocation',
        'High resolution georeferencing data',
    )
    add_netcdf(
        'syn_amin',
        'L2 Aerosol model index number data',
    )
    add_netcdf(
        'syn_angstrom_exp550',
        'Aerosol Angstrom Exponent Data Set',
        bands=sdr_bands,
    )
    add_netcdf(
        'syn_annot_rem',
        'Annotations parameters associated with removed pixel',
    )
    add_netcdf(
        'syn_aot550',
        'Aerosol Optical Thickness Data Set',
        bands=sdr_bands,
    )
    add_netcdf(
        'syn_sdr_removed_pixel',
        'Surface directional reflectance and aerosol parameters associated with removed pixel',
        bands=sdr_bands,
    )
    add_netcdf(
        'tiepoints_meteo',
        'ECMWF meteorology data',
    )
    add_netcdf(
        'tiepoints_olci',
        'Low resolution georeferencing data and Sun and View angles associated with OLCI products',
    )
    add_netcdf(
        'tiepoints_slstr_n',
        'Low resolution georeferencing data and Sun and View angles associated with SLSTR nadir view products',
    )
    add_netcdf(
        'tiepoints_slstr_o',
        'Low resolution georeferencing data and Sun and View angles associated with SLSTR oblique view products',
    )
    add_netcdf(
        'time',
        'Time stamps annotation',
    )

    # add OLCI reflectance channels
    for band in olci_bands:
        channel = band['name'][2:]
        add_netcdf(
            f'syn_{band["name"]}_reflectance',
            f'Surface directional reflectance associated with OLCI channel {channel}',
            bands=[
                {
                    'name': f'SYN{channel}',
                    'description': band['description'],
                    'eo:center_wavelength': band['eo:center_wavelength'],
                    'eo:full_width_half_max': band['eo:full_width_half_max'],
                }
            ],
        )

    # add SLSTR reflectance channels
    for band, view in product(slstr_bands, 'NO'):
        channel = int(band['name'][1:])
        view_name = 'nadir' if view == 'N' else 'oblique'
        add_netcdf(
            f'syn_S{channel}{view}_reflectance',
            f'Surface directional reflectance associated with SLSTR channel {channel:02d} acquired in {view_name} view',
            bands=[
                {
                    'name': f'SYN{17 + channel if view == "N" else 22 + channel}',
                    'description': f'SLSTR {view_name} channel {band["name"]}',
                    'eo:center_wavelength': band['eo:center_wavelength'],
                    'eo:full_width_half_max': band['eo:full_width_half_max'],
                }
            ],
        )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    collection = 'sentinel-3-syn-2-syn-'
    collection += 'ntc' if attr['timeliness'] == 'NT' else 'stc'
    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.EO,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )
    return await item.generate()
