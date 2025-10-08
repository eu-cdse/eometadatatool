from collections.abc import Collection
from typing import Any, TypedDict, Unpack

from eometadatatool.dlc import (
    get_odata_id,
)
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    ThumbnailAsset,
)
from eometadatatool.stac.framework.stac_bands import (
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
        'instruments': ('slstr',),
        'gsd': 1000,
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
        'product:timeliness': 'PT3H' if attr['timeliness'] == 'NR' else 'P1M',
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
        'xfdumanifest': ProductManifestAsset(path=f'{item_path}/xfdumanifest.xml'),
    }

    if (ql_path := attr.get('ql:path')) is not None:
        assets['thumbnail'] = ThumbnailAsset(path=ql_path)

    s1_bands = generate_bands(SLSTR_Bands, ('S1',))
    s2_bands = generate_bands(SLSTR_Bands, ('S2',))
    s3_bands = generate_bands(SLSTR_Bands, ('S3',))
    s4_bands = generate_bands(SLSTR_Bands, ('S4',))
    s5_bands = generate_bands(SLSTR_Bands, ('S5',))
    s6_bands = generate_bands(SLSTR_Bands, ('S6',))
    s7_bands = generate_bands(SLSTR_Bands, ('S7',))
    s8_bands = generate_bands(SLSTR_Bands, ('S8',))
    s9_bands = generate_bands(SLSTR_Bands, ('S9',))
    f1_bands = generate_bands(SLSTR_Bands, ('F1',))
    f2_bands = generate_bands(SLSTR_Bands, ('F2',))

    def add_netcdf(
        key: str,
        title: str,
        *,
        optional: bool = False,
        **extra: Unpack[_NetCDFExtra],
    ) -> None:
        attr_key = f'asset:{key}Data'
        local_path = attr.get(attr_key)
        if local_path is None:
            if optional:
                return
            raise AssertionError(f'{attr_key=!r} must be present in the metadata')
        assets[key] = NetCDFAsset(
            path=f'{item_path}/{local_path}',
            title=title,
            checksum=attr[f'{attr_key}:checksum'],
            size=attr[f'{attr_key}:size'],
            extra=extra,
        )

    add_netcdf(
        'cartesian_an',
        'Full resolution cartesian coordinates for the A stripe grid, nadir view',
    )
    add_netcdf(
        'cartesian_ao',
        'Full resolution cartesian coordinates for the A stripe grid, oblique view',
    )
    add_netcdf(
        'cartesian_bn',
        'Full resolution cartesian coordinates for the B stripe grid, nadir view',
    )
    add_netcdf(
        'cartesian_bo',
        'Full resolution cartesian coordinates for the B stripe grid, oblique view',
    )
    add_netcdf(
        'cartesian_cn',
        'Full resolution cartesian coordinates for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'cartesian_co',
        'Full resolution cartesian coordinates for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'cartesian_fn',
        'Full resolution cartesian coordinates for the 1km F1 grid, nadir view',
        optional=True,
    )
    add_netcdf(
        'cartesian_fo',
        'Full resolution cartesian coordinates for the 1km F1 grid, oblique view',
        optional=True,
    )
    add_netcdf(
        'cartesian_in',
        'Full resolution cartesian coordinates for the 1km TIR grid, nadir view',
    )
    add_netcdf(
        'cartesian_io',
        'Full resolution cartesian coordinates for the 1km TIR grid, oblique view',
    )
    add_netcdf(
        'cartesian_tx',
        '16km cartesian coordinates',
    )
    add_netcdf(
        'F1_BT_fn',
        'Gridded pixel brightness temperature for channel F1 (1km F1 grid, nadir view)',
        bands=f1_bands,
        optional=True,
    )
    add_netcdf(
        'F1_BT_fo',
        'Gridded pixel brightness temperature for channel F1 (1km F1 grid, oblique view)',
        bands=f1_bands,
        optional=True,
    )
    add_netcdf(
        'F1_quality_fn',
        'Thermal Infrared quality annotations for channel F1 (1km F1 grid, nadir view)',
        optional=True,
    )
    add_netcdf(
        'F1_quality_fo',
        'Thermal Infrared quality annotations for channel F1 (1km F1 grid, oblique view)',
        optional=True,
    )
    add_netcdf(
        'F1_BT_in',
        'Gridded pixel brightness temperature for channel F1 (1km TIR grid, nadir view)',
        bands=f1_bands,
        optional=True,
    )
    add_netcdf(
        'F1_BT_io',
        'Gridded pixel brightness temperature for channel F1 (1km TIR grid, oblique view)',
        bands=f1_bands,
        optional=True,
    )
    add_netcdf(
        'F1_quality_in',
        'Thermal Infrared quality annotations for channel F1 (1km TIR grid, nadir view)',
        optional=True,
    )
    add_netcdf(
        'F1_quality_io',
        'Thermal Infrared quality annotations for channel F1 (1km TIR grid, oblique view)',
        optional=True,
    )
    add_netcdf(
        'F2_BT_in',
        'Gridded pixel brightness temperature for channel F2 (1km TIR grid, nadir view)',
        bands=f2_bands,
    )
    add_netcdf(
        'F2_BT_io',
        'Gridded pixel brightness temperature for channel F2 (1km TIR grid, oblique view)',
        bands=f2_bands,
    )
    add_netcdf(
        'F2_quality_in',
        'Thermal Infrared quality annotations for channel F2 (1km TIR grid, nadir view)',
    )
    add_netcdf(
        'F2_quality_io',
        'Thermal Infrared quality annotations for channel F2 (1km TIR grid, oblique view)',
    )
    add_netcdf(
        'flags_an',
        'Global flags for the A stripe grid, nadir view',
    )
    add_netcdf(
        'flags_ao',
        'Global flags for the A stripe grid, oblique view',
    )
    add_netcdf(
        'flags_bn',
        'Global flags for the B stripe grid, nadir view',
    )
    add_netcdf(
        'flags_bo',
        'Global flags for the B stripe grid, oblique view',
    )
    add_netcdf(
        'flags_cn',
        'Global flags for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'flags_co',
        'Global flags for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'flags_fn',
        'Global flags for the 1km F1 grid, nadir view',
        optional=True,
    )
    add_netcdf(
        'flags_fo',
        'Global flags for the 1km F1 grid, oblique view',
        optional=True,
    )
    add_netcdf(
        'flags_in',
        'Global flags for the 1km TIR grid, nadir view',
    )
    add_netcdf(
        'flags_io',
        'Global flags for the 1km TIR grid, oblique view',
    )
    add_netcdf(
        'geodetic_an',
        'Full resolution geodetic coordinates for the A stripe grid, nadir view',
    )
    add_netcdf(
        'geodetic_ao',
        'Full resolution geodetic coordinates for the A stripe grid, oblique view',
    )
    add_netcdf(
        'geodetic_bn',
        'Full resolution geodetic coordinates for the B stripe grid, nadir view',
    )
    add_netcdf(
        'geodetic_bo',
        'Full resolution geodetic coordinates for the B stripe grid, oblique view',
    )
    add_netcdf(
        'geodetic_cn',
        'Full resolution geodetic coordinates for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'geodetic_co',
        'Full resolution geodetic coordinates for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'geodetic_fn',
        'Full resolution geodetic coordinates for the 1km F1 grid, nadir view',
        optional=True,
    )
    add_netcdf(
        'geodetic_fo',
        'Full resolution geodetic coordinates for the 1km F1 grid, oblique view',
        optional=True,
    )
    add_netcdf(
        'geodetic_in',
        'Full resolution geodetic coordinates for the 1km TIR grid, nadir view',
    )
    add_netcdf(
        'geodetic_io',
        'Full resolution geodetic coordinates for the 1km TIR grid, oblique view',
    )
    add_netcdf(
        'geodetic_tx',
        '16km geodetic coordinates',
    )
    add_netcdf(
        'geometry_tn',
        '16km solar and satellite geometry annotations, nadir view',
    )
    add_netcdf(
        'geometry_to',
        '16km solar and satellite geometry annotations, oblique view',
    )
    add_netcdf(
        'indices_an',
        'Scan, pixel and detector annotations for the A stripe grid, nadir view',
    )
    add_netcdf(
        'indices_ao',
        'Scan, pixel and detector annotations for the A stripe grid, oblique view',
    )
    add_netcdf(
        'indices_bn',
        'Scan, pixel and detector annotations for the B stripe grid, nadir view',
    )
    add_netcdf(
        'indices_cn',
        'Scan, pixel and detector annotations for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'indices_co',
        'Scan, pixel and detector annotations for the A, B or TDI stripe grid, nadir or oblique view',
        optional=True,
    )
    add_netcdf(
        'indices_fn',
        'Scan, pixel and detector annotations for the 1km F1 grid, nadir view',
        optional=True,
    )
    add_netcdf(
        'indices_fo',
        'Scan, pixel and detector annotations for the 1km F1 grid, oblique view',
        optional=True,
    )
    add_netcdf(
        'indices_bo',
        'Scan, pixel and detector annotations for the B stripe grid, oblique view',
    )
    add_netcdf(
        'indices_in',
        'Scan, pixel and detector annotations for the 1km TIR grid, nadir view',
    )
    add_netcdf(
        'indices_io',
        'Scan, pixel and detector annotations for the 1km TIR grid, oblique view',
    )
    add_netcdf(
        'met_tx',
        'Meteorological parameters regridded onto the 16km tie points',
    )
    add_netcdf(
        'S1_quality_an',
        'Visible and Shortwave IR quality annotations for channel S1 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S1_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S1 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S1_radiance_an',
        'TOA radiance for channel S1 (A stripe grid, nadir view)',
        bands=s1_bands,
    )
    add_netcdf(
        'S1_radiance_ao',
        'TOA radiance for channel S1 (A stripe grid, oblique view)',
        bands=s1_bands,
    )
    add_netcdf(
        'S2_quality_an',
        'Visible and Shortwave IR quality annotations for channel S2 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S2_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S2 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S2_radiance_an',
        'TOA radiance for channel S2 (A stripe grid, nadir view)',
        bands=s2_bands,
    )
    add_netcdf(
        'S2_radiance_ao',
        'TOA radiance for channel S2 (A stripe grid, oblique view)',
        bands=s2_bands,
    )
    add_netcdf(
        'S3_quality_an',
        'Visible and Shortwave IR quality annotations for channel S3 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S3_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S3 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S3_radiance_an',
        'TOA radiance for channel S3 (A stripe grid, nadir view)',
        bands=s3_bands,
    )
    add_netcdf(
        'S3_radiance_ao',
        'TOA radiance for channel S3 (A stripe grid, oblique view)',
        bands=s3_bands,
    )
    add_netcdf(
        'S4_quality_an',
        'Visible and Shortwave IR quality annotations for channel S4 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S4_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S4 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S4_quality_bn',
        'Visible and Shortwave IR quality annotations for channel S4 (B stripe grid, nadir view)',
    )
    add_netcdf(
        'S4_quality_bo',
        'Visible and Shortwave IR quality annotations for channel S4 (B stripe grid, oblique view)',
    )
    add_netcdf(
        'S4_quality_cn',
        'Visible and Shortwave IR quality annotations for channel S4 (TDI stripe grid, nadir view)',
        optional=True,
    )
    add_netcdf(
        'S4_quality_co',
        'Visible and Shortwave IR quality annotations for channel S4 (TDI stripe grid, oblique view)',
        optional=True,
    )
    add_netcdf(
        'S4_radiance_an',
        'TOA radiance for channel S4 (A stripe grid, nadir view)',
        bands=s4_bands,
    )
    add_netcdf(
        'S4_radiance_ao',
        'TOA radiance for channel S4 (A stripe grid, oblique view)',
        bands=s4_bands,
    )
    add_netcdf(
        'S4_radiance_bn',
        'TOA radiance for channel S4 (B stripe grid, nadir view)',
        bands=s4_bands,
    )
    add_netcdf(
        'S4_radiance_bo',
        'TOA radiance for channel S4 (B stripe grid, oblique view)',
        bands=s4_bands,
    )
    add_netcdf(
        'S4_radiance_bo',
        'TOA radiance for channel S4 (B stripe grid, oblique view)',
        bands=s4_bands,
    )
    add_netcdf(
        'S4_radiance_cn',
        'TOA radiance for channel S4 (TDI stripe grid, nadir view)',
        bands=s4_bands,
        optional=True,
    )
    add_netcdf(
        'S4_radiance_co',
        'TOA radiance for channel S4 (TDI stripe grid, oblique view)',
        bands=s4_bands,
        optional=True,
    )
    add_netcdf(
        'S5_quality_an',
        'Visible and Shortwave IR quality annotations for channel S5 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S5_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S5 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S5_quality_bn',
        'Visible and Shortwave IR quality annotations for channel S5 (B stripe grid, nadir view)',
    )
    add_netcdf(
        'S5_quality_bo',
        'Visible and Shortwave IR quality annotations for channel S5 (B stripe grid, oblique view)',
    )
    add_netcdf(
        'S5_quality_cn',
        'Visible and Shortwave IR quality annotations for channel S5 (TDI stripe grid, nadir view)',
        optional=True,
    )
    add_netcdf(
        'S5_quality_co',
        'Visible and Shortwave IR quality annotations for channel S5 (TDI stripe grid, oblique view)',
        optional=True,
    )
    add_netcdf(
        'S5_radiance_an',
        'TOA radiance for channel S5 (A stripe grid, nadir view)',
        bands=s5_bands,
    )
    add_netcdf(
        'S5_radiance_ao',
        'TOA radiance for channel S5 (A stripe grid, oblique view)',
        bands=s5_bands,
    )
    add_netcdf(
        'S5_radiance_bn',
        'TOA radiance for channel S5 (B stripe grid, nadir view)',
        bands=s5_bands,
    )
    add_netcdf(
        'S5_radiance_bo',
        'TOA radiance for channel S5 (B stripe grid, oblique view)',
        bands=s5_bands,
    )
    add_netcdf(
        'S5_radiance_cn',
        'TOA radiance for channel S5 (TDI stripe grid, nadir view)',
        bands=s5_bands,
        optional=True,
    )
    add_netcdf(
        'S5_radiance_co',
        'TOA radiance for channel S5 (TDI stripe grid, oblique view)',
        bands=s5_bands,
        optional=True,
    )
    add_netcdf(
        'S6_quality_an',
        'Visible and Shortwave IR quality annotations for channel S6 (A stripe grid, nadir view)',
    )
    add_netcdf(
        'S6_quality_ao',
        'Visible and Shortwave IR quality annotations for channel S6 (A stripe grid, oblique view)',
    )
    add_netcdf(
        'S6_quality_bn',
        'Visible and Shortwave IR quality annotations for channel S6 (B stripe grid, nadir view)',
    )
    add_netcdf(
        'S6_quality_bo',
        'Visible and Shortwave IR quality annotations for channel S6 (B stripe grid, oblique view)',
    )
    add_netcdf(
        'S6_quality_cn',
        'Visible and Shortwave IR quality annotations for channel S6 (TDI stripe grid, nadir view)',
        optional=True,
    )
    add_netcdf(
        'S6_quality_co',
        'Visible and Shortwave IR quality annotations for channel S6 (TDI stripe grid, oblique view)',
        optional=True,
    )
    add_netcdf(
        'S6_radiance_an',
        'TOA radiance for channel S6 (A stripe grid, nadir view)',
        bands=s6_bands,
    )
    add_netcdf(
        'S6_radiance_ao',
        'TOA radiance for channel S6 (A stripe grid, oblique view)',
        bands=s6_bands,
    )
    add_netcdf(
        'S6_radiance_bn',
        'TOA radiance for channel S6 (B stripe grid, nadir view)',
        bands=s6_bands,
    )
    add_netcdf(
        'S6_radiance_bo',
        'TOA radiance for channel S6 (B stripe grid, oblique view)',
        bands=s6_bands,
    )
    add_netcdf(
        'S6_radiance_cn',
        'TOA radiance for channel S6 (TDI stripe grid, nadir view)',
        bands=s6_bands,
        optional=True,
    )
    add_netcdf(
        'S6_radiance_co',
        'TOA radiance for channel S6 (TDI stripe grid, oblique view)',
        bands=s6_bands,
        optional=True,
    )
    add_netcdf(
        'S7_BT_in',
        'Gridded pixel brightness temperature for channel S7 (1km TIR grid, nadir view)',
        bands=s7_bands,
    )
    add_netcdf(
        'S7_BT_io',
        'Gridded pixel brightness temperature for channel S7 (1km TIR grid, oblique view)',
        bands=s7_bands,
    )
    add_netcdf(
        'S7_quality_in',
        'Thermal Infrared quality annotations for channel S7 (1km TIR grid, nadir view)',
    )
    add_netcdf(
        'S7_quality_io',
        'Thermal Infrared quality annotations for channel S7 (1km TIR grid, oblique view)',
    )
    add_netcdf(
        'S8_BT_in',
        'Gridded pixel brightness temperature for channel S8 (1km TIR grid, nadir view)',
        bands=s8_bands,
    )
    add_netcdf(
        'S8_BT_io',
        'Gridded pixel brightness temperature for channel S8 (1km TIR grid, oblique view)',
        bands=s8_bands,
    )
    add_netcdf(
        'S8_quality_in',
        'Thermal Infrared quality annotations for channel S8 (1km TIR grid, nadir view)',
    )
    add_netcdf(
        'S8_quality_io',
        'Thermal Infrared quality annotations for channel S8 (1km TIR grid, oblique view)',
    )
    add_netcdf(
        'S9_BT_in',
        'Gridded pixel brightness temperature for channel S9 (1km TIR grid, nadir view)',
        bands=s9_bands,
    )
    add_netcdf(
        'S9_BT_io',
        'Gridded pixel brightness temperature for channel S9 (1km TIR grid, oblique view)',
        bands=s9_bands,
    )
    add_netcdf(
        'S9_quality_in',
        'Thermal Infrared quality annotations for channel S9 (1km TIR grid, nadir view)',
    )
    add_netcdf(
        'S9_quality_io',
        'Thermal Infrared quality annotations for channel S9 (1km TIR grid, oblique view)',
    )
    add_netcdf(
        'time_an',
        'Time annotations for the A stripe grid',
        optional=True,
    )
    add_netcdf(
        'time_bn',
        'Time annotations for the B stripe grid',
        optional=True,
    )
    add_netcdf(
        'time_cn',
        'Time annotations for the A, B or TDI stripe grid, nadir and oblique view',
        optional=True,
    )
    add_netcdf(
        'time_in',
        'Time annotations for the 1 KM grid',
        optional=True,
    )
    add_netcdf(
        'viscal',
        'VISCAL data obtained from input VISCAL ADF',
    )

    links: list[STACLink] = [
        TraceabilityLink(href=f'{odata.name}.zip'),
        ZipperLink(href=attr['filepath']),
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=(
            'sentinel-3-sl-1-rbt-nrt'
            if attr['timeliness'] == 'NR'
            else 'sentinel-3-sl-1-rbt-ntc'
        ),
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
        ),
        extra=props,
    )

    return await item.generate()
