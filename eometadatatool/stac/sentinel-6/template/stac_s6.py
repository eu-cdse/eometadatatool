from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.stac.framework.stac_asset import (
    NetCDFAsset,
    ProductManifestAsset,
    STACAsset,
    XMLAsset,
)
from eometadatatool.stac.framework.stac_bands import (
    AMR_Bands,
    Poseidon_Bands,
    generate_bands,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink, TraceabilityLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    timeliness = attr.get('timeliness')
    timeliness_mapping = {
        'NR': 'PT3H',  # Near-Real Time (availability within 3 hours)
        'ST': 'PT36H',  # Short Time Critical (availability within 36 hours)
        'NT': 'P1M',  # Non Time Critical (availability within 60 days)
    }
    timeliness_collection_mapping = {'NR': 'nrt', 'ST': 'stc', 'NT': 'ntc'}

    if timeliness not in timeliness_mapping:
        raise ValueError(f'Unknown timeliness category: {timeliness}')
    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'platform': (
            attr['platformShortName'] + attr['platformSerialIdentifier']
        ).lower(),
        'constellation': attr['platformShortName'].lower(),
        'instruments': (attr['instrumentShortName'].lower(),),
        'processing:level': 'L' + attr['processingLevel'],
        'processing:datetime': attr['processingDate'],
        'proj:code': None,
        'sat:absolute_orbit': attr['orbitNumber'],
        'sat:relative_orbit': attr['relativeOrbitNumber'],
        'sat:orbit_cycle': attr['cycleNumber'],
        'sat:orbit_state': attr['orbitDirection'].lower(),
        'sat:platform_international_designator': attr['nssdcIdentifier'],
        'product:type': attr['productType'],
        'product:timeliness': timeliness_mapping.get(timeliness),
        'product:timeliness_category': timeliness,
    }
    if processor_version := attr.get('processorVersion'):
        props['processing:version'] = processor_version

    if attr['productType'].startswith('P4'):
        props['altm:instrument_type'] = 'sar'
        props['gsd'] = 20000
    elif attr['productType'].startswith('MW_2__AMR'):
        props['altm:instrument_type'] = 'microwave'
        props['gsd'] = 25000

    item_path: str = attr['filepath']
    odata = await get_odata_id(item_path)
    assets: dict[str, STACAsset] = {
        'xfdumanifest': ProductManifestAsset(
            path=f'{item_path}/xfdumanifest.xml',
            size=attr['xfdumanifest.xml:size'],
            checksum=attr['xfdumanifest.xml:checksum'],
        ),
    }
    if 'manifest.xml:size' in attr:
        assets['manifest'] = XMLAsset(
            path=f'{item_path}/manifest.safe',
            title='manifest.safe',
            # checksum is not available, see
            # https://gitlab.cloudferro.com/data-science/eometadatatool/-/merge_requests/68#note_283221
            # checksum=attr['manifest.xml:checksum'],
            size=attr['manifest.xml:size'],
            roles=['metadata'],
        )
    if 'asset:ALTData' in attr:
        assets['measurement'] = NetCDFAsset(
            path=f'{item_path}/{attr["asset:ALTData"]}',
            title='Measurement Data Set',
            checksum=attr['asset:ALTData:checksum'],
            size=attr['asset:ALTData:size'],
            extra={
                'bands': generate_bands(Poseidon_Bands, ['C', 'Ku']),
                'cube:dimensions': attr['dimensions'],
                'cube:variables': attr['variables'],
            },
        )
    if 'asset:ALTData0' in attr:
        assets['measurement'] = NetCDFAsset(
            path=f'{item_path}/{attr["asset:ALTData0"]}',
            roles=['data', 'standard'],
            title='Standard Measurement Data Set',
            description='The standard data file includes 1 Hz and 20 Hz measurements for the Ku-band as well as geophysical corrections at 1 Hz and some at 20 Hz.',
            checksum=attr['asset:ALTData0:checksum'],
            size=attr['asset:ALTData0:size'],
            extra={
                'bands': generate_bands(Poseidon_Bands, ['Ku']),
                'cube:dimensions': attr['dimensions_std'],
                'cube:variables': attr['variables_std'],
            },
        )
    if 'asset:ALTData1' in attr:
        assets['reduced_measurement'] = NetCDFAsset(
            path=f'{item_path}/{attr["asset:ALTData1"]}',
            roles=['data', 'reduced'],
            title='Reduced Measurement Data Set',
            description='The reduced data file contains only 1 Hz measurements for the Ku- and C-bands as well as geophysical corrections at 1 Hz.',
            checksum=attr['asset:ALTData1:checksum'],
            size=attr['asset:ALTData1:size'],
            extra={
                'bands': generate_bands(Poseidon_Bands, ['C', 'Ku']),
                'cube:dimensions': attr['dimensions_red'],
                'cube:variables': attr['variables_red'],
            },
        )
    if 'asset:AMRData' in attr:
        assets['measurement'] = NetCDFAsset(
            path=f'{item_path}/{attr["asset:AMRData"]}',
            title='AMR Measurement Data Set',
            checksum=attr['asset:AMRData:checksum'],
            size=attr['asset:AMRData:size'],
            extra={
                'bands': generate_bands(AMR_Bands, ['band1', 'band2', 'band3']),
                'cube:dimensions': attr['dimensions'],
                'cube:variables': attr['variables'],
            },
        )
    if 'EOPMetadata.xml:size' in attr:
        assets['eop_metadata'] = XMLAsset(
            path=f'{item_path}/EOPMetadata.xml',
            title='EOP Metadata',
            size=attr['EOPMetadata.xml:size'],
            roles=['metadata'],
        )

    links: list[STACLink] = [
        TraceabilityLink(
            href=f'{odata.name}.zip',
        )
    ]

    collection = 'sentinel-6-'
    match attr.get('productType'):
        case 'MW_2__AMR____':
            collection += 'amr-c'
        case 'P4_1B_LR_____':
            collection += 'p4-1b'
        case 'P4_2__LR_____':
            collection += 'p4-2'
        case _:
            raise ValueError(f'Unknown product type: {attr.get("productType")}')
    collection += '-' + timeliness_collection_mapping.get(timeliness)

    item = STACItem(
        path=item_path,
        odata=odata,
        collection=collection,
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=(
            StacExtension.ALTIMETRY,
            StacExtension.PROCESSING,
            StacExtension.PRODUCT,
            StacExtension.PROJECTION,
            StacExtension.SATELLITE,
            StacExtension.DATACUBE,
        ),
        extra=props,
    )
    return await item.generate()
