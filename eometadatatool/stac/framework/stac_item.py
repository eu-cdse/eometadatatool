import datetime

import re
from collections.abc import Collection, Mapping, MutableSet
from dataclasses import dataclass
from typing import Any

from shapely import MultiPolygon, Polygon, from_wkt

from eometadatatool._version import __version__
from eometadatatool.dlc import (
    ODataInfo,
)
from eometadatatool.geom_utils import normalize_geometry, simplify_geometry
from eometadatatool.stac.framework.stac_asset import (
    ProductAsset,
    STACAsset,
)
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_link import STACLink


@dataclass(kw_only=True, slots=True)
class STACItem:
    path: str
    """Path to the product/scene in the filesystem or S3."""

    odata: ODataInfo | None
    """OData information about the item."""

    collection: str
    """Collection name."""

    identifier: str
    """Item identifier."""

    coordinates: str
    """Geometry coordinates in WKT format."""

    links: Collection[STACLink]
    """Links belonging to the item."""

    assets: Mapping[str, STACAsset]
    """Assets belonging to the item."""

    product_asset_name: str | None = 'product'
    """Name of the automatically generated product asset. None to disable."""

    extensions: Collection[StacExtension] = ()
    """Additional STAC extensions implemented by this item."""

    extra: Mapping[str, Any]
    """Additional properties."""

    async def generate(self) -> dict[str, Any]:
        geom: Polygon | MultiPolygon = normalize_geometry(from_wkt(self.coordinates))  # type: ignore

        extensions = {
            StacExtension.AUTHENTICATION,
            StacExtension.STORAGE,
            StacExtension.TIMESTAMP,
            StacExtension.PROCESSING,
            *self.extensions,
        }

        props: dict[str, Any] = {}

        if self.odata:
            props.update(
                (k, v)
                for k, v in (
                    ('created', self.odata.created_isodate),
                    ('updated', self.odata.updated_isodate),
                    ('published', self.odata.published_isodate),
                    ('eopf:origin_datetime', self.odata.created_isodate),
                )
                if not v.startswith('1970-01-01T00:00:00')
            )

        props.update({
            'auth:schemes': {
                's3': {
                    'type': 's3',
                },
            },
            'storage:schemes': {
                'cdse-s3': {
                    'title': 'Copernicus Data Space Ecosystem S3',
                    'description': 'This endpoint provides access to EO data which is stored on the object storage of both CloudFerro Cloud and OpenTelekom Cloud (OTC). See the [documentation](https://documentation.dataspace.copernicus.eu/APIs/S3.html) for more information, including how to get credentials.',
                    'platform': 'https://eodata.dataspace.copernicus.eu',
                    'requester_pays': False,
                    'type': 'custom-s3',
                },
                'creodias-s3': {
                    'title': 'CREODIAS S3',
                    'description': 'Comprehensive Earth Observation Data (EODATA) archive offered by CREODIAS as a commercial part of CDSE, designed to provide users with access to a vast repository of satellite data without predefined quota limits.',
                    'platform': 'https://eodata.cloudferro.com',
                    'requester_pays': True,
                    'type': 'custom-s3',
                },
            },
            **self.extra,
        })

        if self.odata:
            props['auth:schemes']['oidc'] = {
                'type': 'openIdConnect',
                'openIdConnectUrl': 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/.well-known/openid-configuration',
            }

        if self.odata:
            props['eopf:origin_datetime'] = self.odata.created_isodate
            extensions.add(StacExtension.EOPF)

        props.update(self.extra)

        if 'processing:software' not in props:
            props['processing:software'] = {'eometadatatool': __version__}
        else:
            props['processing:software']['eometadatatool'] = __version__

        if 'processing:facility' not in props and self.odata and self.odata.origin:
            props['processing:facility'] = self.odata.origin

        # Remove invalid values for relative orbit numbers, especially 0
        if 'sat:relative_orbit' in props and not (props['sat:relative_orbit'] >= 1):
            del props['sat:relative_orbit']

        assets: dict[str, dict] = {
            k: await asset.generate(self.odata, extensions, props)
            for k, asset in self.assets.items()
        }
        if self.product_asset_name is not None and self.odata:
            assert self.product_asset_name not in assets, (
                'product asset is managed automatically'
            )
            assets[self.product_asset_name] = await ProductAsset(
                path=self.path
            ).generate(self.odata, extensions)

        if 'start_datetime' not in props and props['datetime']:
            props['start_datetime'] = props['datetime']

        if 'end_datetime' not in props and props['datetime']:
            props['end_datetime'] = props['datetime']

        props['expires'] = datetime.datetime(9999,1,1,0,0,0, tzinfo=datetime.UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        return {
            'type': 'Feature',
            'stac_version': '1.1.0',
            'collection': self.collection,
            'id': self.identifier,
            'properties': props,
            'bbox': geom.bounds,
            'geometry': simplify_geometry(geom).__geo_interface__,
            'links': [link.generate() for link in self.links],
            'assets': assets,
            'stac_extensions': sorted(extensions),
        }

    @staticmethod
    def from_mgrs(mgrs: str, extensions: MutableSet[StacExtension]) -> dict[str, str]:
        # Extract UTM zone number and latitude band
        match = re.match(r'^(\d{1,2})([C-X])', mgrs)
        if not match:
            raise ValueError('Invalid MGRS format')

        utm_zone = int(match.group(1))  # Extract UTM zone number
        lat_band = match.group(2)  # Extract latitude band

        # Determine the hemisphere
        if lat_band >= 'N':
            epsg_code = 32600 + utm_zone  # Northern Hemisphere
        else:
            epsg_code = 32700 + utm_zone  # Southern Hemisphere

        extensions.add(StacExtension.GRID)
        extensions.add(StacExtension.PROJECTION)
        return {
            'grid:code': f'MGRS-{mgrs}',
            'proj:code': f'EPSG:{epsg_code}',
        }
