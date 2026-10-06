import re
from typing import Any

from eometadatatool.dlc import get_odata_id
from eometadatatool.flags import is_extended_private_data, is_hidden, is_no_private
from eometadatatool.stac.framework.stac_asset import GeoTIFFAsset, STACAsset, XMLAsset
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.stac_link import STACLink


async def render(attr: dict[str, Any]) -> dict[str, Any]:
    extensions = [
        StacExtension.PROJECTION,
        StacExtension.ALTERNATE,
        StacExtension.TIMESTAMP,
        StacExtension.AUTHENTICATION,
        StacExtension.SAR,
        StacExtension.STORAGE,
        StacExtension.GRID,
    ]

    productIdentifier = attr['productIdentifier']

    match = re.search(r':([^:]+)$', productIdentifier)
    processing_version = match.group(1) if match else None

    match = re.search(r'([NS]\d{2})(?:_00)?(?:[^\d]*)([EW]\d{2,3})', productIdentifier)
    grid_code = f'CDEM-{match.group(1)}{match.group(2)}' if match else None

    match = re.search(
        r'(Copernicus_DSM_\d+m?(?:_[A-Za-z0-9]+)*?_?[NS]\d{2}(?:_00)?_?[EW]\d{2,3}(?:_00)?)',
        productIdentifier,
    )
    filename = match.group(1) if match else None

    props: dict[str, Any] = {
        'datetime': attr['beginningDateTime'],
        'start_datetime': attr['beginningDateTime'],
        'end_datetime': attr['endingDateTime'],
        'proj:code': attr['epsg'],
        'sar:polarizations': [attr['polarisations']],
        'product:type': attr['productType'],
        'gsd': 10,
        'grid:code': grid_code,
        'processing:version': processing_version,
        'instruments': [attr['instrumentShortName']],
    }

    acq_type = attr.get('acquisitionType')
    if acq_type is not None:
        acq_type = acq_type.lower()
        props['product:acquisition_type'] = (
            acq_type if acq_type in ('nominal', 'calibration') else 'other'
        )

    extended_private_data = is_extended_private_data()
    odata = await get_odata_id(
        attr['filepath'],
        zipper=extended_private_data,
        omit_date=True,
        omit_collection=True,
    )

    private_flag = is_no_private()
    hidden_flag = is_hidden()
    if private_flag is False:
        props['_private'] = {}
        props['_private']['product_size'] = attr['private:product_size']
        props['_private']['product_uuid'] = odata.id
        props['_private']['product_name'] = odata.name
        if hidden_flag:
            props['_private']['visible'] = False
        else:
            props['_private']['visible'] = True

        if extended_private_data:
            props['_private']['brands'] = odata.zipper_data

    item_path: str = attr['filepath']

    assets: dict[str, STACAsset] = {
        'data': GeoTIFFAsset(
            path=f'{attr["filepath"]}/{filename}/DEM/{filename}_DEM.tif',
            title=f'{filename}_DEM.tif',
            include_other_alternates=False,
        ),
        'circulation_report_metadata': XMLAsset(
            path=f'{item_path}/{attr["GSC:original_filename"]}',
            title='Circulation report',
            checksum=attr.get('GSC:checksum'),
            size=attr.get('GSC:size'),
            roles=['metadata'],
        ),
        'inspire_metadata': XMLAsset(
            path=f'{item_path}/INSPIRE.xml',
            title='Inspire',
            size=attr.get('INSPIRE.xml:size'),
            roles=['metadata'],
        ),
    }

    local_path = f'{odata.name}.zip'
    links: list[STACLink] = [
        STACLink(
            title='Product history record from the CDSE traceability service',
            rel='version-history',
            href=f'https://trace.dataspace.copernicus.eu/api/v1/traces/name/{local_path}',
            media_type='application/json',
        )
    ]

    item = STACItem(
        path=item_path,
        odata=odata,
        collection='cop-dem-eea-10-laea-tif',
        identifier=attr['identifier'],
        coordinates=attr['coordinates'],
        links=links,
        assets=assets,
        extensions=tuple(extensions),
        extra=props,
    )
    return await item.generate()
