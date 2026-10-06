import asyncio
import csv
import datetime
import os
import tempfile
import uuid
from collections.abc import Iterator, Mapping
from typing import Any, Final

from dateutil import parser

# Fixed namespace for deterministically generating product_uuid values for
# collections without an OData record. Do not change this value: doing so
# would change the UUID generated for every existing product identifier.
PRODUCT_UUID_NAMESPACE: Final[uuid.UUID] = uuid.UUID('a9f5b1c4-6e2a-4b7d-9c3e-1d8f2a6b5c4d')


def generate_product_uuid(identifier: str) -> str:
    """
    Deterministically derive a product_uuid for collections that have no
    OData record to source one from. The same identifier always yields the
    same UUID, so regenerating a STAC item does not change its product_uuid.
    :param identifier: the product's unique identifier (e.g. attr['identifier'])
    :return: UUID string
    """
    return str(uuid.uuid5(PRODUCT_UUID_NAMESPACE, identifier))


class _EmptyDict[K, V](Mapping[K, V]):
    def __getitem__(self, key: K) -> V:
        raise KeyError(key)

    def __iter__(self) -> Iterator[K]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __hash__(self) -> int:
        return 0


EMPTY_MAPPING: Final[Mapping[str, Any]] = _EmptyDict()


def ensure_iso_datetime(value: str | datetime.datetime) -> str | None:
    if isinstance(value, str):
        return parser.isoparse(value).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return None


async def gdal_footprint_to_wkt(tif_path: str) -> str | None | Any:
    """
    Run gdal_footprint to calculate TIFF footprint.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)  # noqa: SIM115
    tmp_path = tmp.name
    tmp.close()

    try:
        process = await asyncio.create_subprocess_exec(
            'gdal_footprint',
            '-f',
            'CSV',
            '-lco',
            'GEOMETRY=AS_WKT',
            '-overwrite',
            '-t_srs',
            'EPSG:4326',
            '-convex_hull',
            tif_path,
            tmp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                f"gdal_footprint failed ({process.returncode}):\n{stderr.decode()}"
            )

        with open(tmp_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row is None:
                return None
            return row.get('WKT')

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
