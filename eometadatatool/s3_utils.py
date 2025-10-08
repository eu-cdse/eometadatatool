import logging
from asyncio import TaskGroup
from collections.abc import AsyncIterator, Collection, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from os import PathLike, environ, getenv, scandir
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import TYPE_CHECKING, NamedTuple

import aioboto3
import aiohttp
import botocore.exceptions
import stamina
from aiobotocore.config import AioConfig
from asyncache import cached
from lrucache_rs import LRUCache
from sizestr import sizestr

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client
    from types_aiobotocore_s3.type_defs import HeadObjectOutputTypeDef

S3_CLIENT: 'S3Client' = None  # type: ignore

_TEMPFILE_CACHE: dict[Path, Path] = {}


@asynccontextmanager
async def setup_s3_client():
    global S3_CLIENT
    logging.debug('Setting up S3 client')
    async with aioboto3.Session().client(
        service_name='s3',
        endpoint_url=(
            getenv('AWS_ENDPOINT_URL_S3')
            or getenv('AWS_S3_ENDPOINT')
            or getenv('AWS_ENDPOINT_URL')
        ),
        config=AioConfig(
            connect_timeout=float(environ.get('AWS_S3_CONNECT_TIMEOUT', '20')),
            read_timeout=float(environ.get('AWS_S3_READ_TIMEOUT', '60')),
            tcp_keepalive=True,
        ),
    ) as S3_CLIENT:
        yield
    logging.debug('Tearing down S3 client')


class S3Path(NamedTuple):
    path: Path
    bucket: str
    key: str
    key_relative: str
    last_modified: datetime
    etag: str
    size: int
    subkeys: Mapping[str, 'S3Path']

    @classmethod
    async def from_path(cls, path: Path) -> 'S3Path | None':
        """Parse a Path into an S3Path, containing bucket and key information.

        :param path: Path to the file, e.g. `s3://bucket/key` or `/eodata/key`.
        :return: S3Path instance, or None if the path is not a valid S3 path.
        """
        match path.parents:
            case (*_, bucket, schema, _) if schema == Path('s3:'):
                key = path.relative_to(bucket).as_posix()
                bucket = bucket.name
                logging.debug(
                    '%r [dark_green]is a valid S3 path[/] [white](reason: URI)[/]',
                    str(path),
                )
            case (*_, schema, _) if (
                schema == Path('/eodata') and 'AWS_S3_EODATA_BUCKET' in environ
            ):
                key = path.relative_to(schema).as_posix()
                bucket = environ['AWS_S3_EODATA_BUCKET']
                logging.debug(
                    '%r [dark_green]is a valid S3 path[/] [white](reason: EODATA)[/]',
                    str(path),
                )
            case _:
                logging.debug('%r [red]is not a valid S3 path[/]', str(path))
                return None
        key = key.rstrip('/')
        async with TaskGroup() as tg:
            subkeys_t = tg.create_task(_get_subkeys(path, bucket, key))
            head_t = tg.create_task(_head_object(bucket, key))

        head = head_t.result() or {}
        last_modified = head.get('LastModified') or datetime.fromtimestamp(0, UTC)
        etag = head.get('ETag', '-')
        size = head.get('ContentLength', 0)

        return cls(
            path=path,
            bucket=bucket,
            key=key,
            key_relative='',
            last_modified=last_modified,
            etag=etag,
            size=size,
            subkeys=subkeys_t.result(),
        )

    def __str__(self) -> str:
        """Return a URI representation of the S3Path."""
        return f's3://{self.bucket}/{self.key}'

    def is_dir(self) -> bool:
        """Check if the S3Path represents a directory."""
        return bool(self.subkeys)

    def get_subpath(self, subkey: str) -> 'S3Path':
        """From a subkey, return a new S3Path instance.

        :param subkey: Subkey of this directory.
        :raises FileNotFoundError: If the subkey is not found in this directory.
        :return: S3Path instance, containing bucket and key information.
        """
        subpath = self.subkeys.get(subkey)
        if subpath is None:
            raise FileNotFoundError(f'Subkey {subkey!r} not found in {self!s}')
        return subpath

    @asynccontextmanager
    @stamina.retry(on=(botocore.exceptions.ClientError, aiohttp.ClientError))
    async def tempfile(self):
        """Download a S3 file to a temporary file.

        :raises IsADirectoryError: If the S3Path represents a directory.
        :yield: Path to the temporary file.
        """
        if self.is_dir():
            raise IsADirectoryError(
                f'Cannot create temporary file from directory {self!s}'
            )

        if self.path.suffix == '.nc':
            yield self.path
            return

        if cached := _TEMPFILE_CACHE.get(self.path):
            yield cached
            return

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir, self.path.name)
            with path.open('xb') as f:
                ts = perf_counter()
                async for chunk in await self._iter_body():
                    f.write(chunk)
                tt = perf_counter() - ts
            logging.debug(
                'Downloaded %r file in %.3f seconds (%s)',
                str(self),
                tt,
                sizestr(path.stat().st_size),
            )
            _TEMPFILE_CACHE[self.path] = path
            try:
                yield path
            finally:
                del _TEMPFILE_CACHE[self.path]

    async def _iter_body(self) -> AsyncIterator[bytes]:
        """Get an iterator over the body of the S3 file."""
        r = await S3_CLIENT.get_object(Bucket=self.bucket, Key=self.key)
        return r['Body'].iter_chunks(chunk_size=16 * 1024 * 1024)  # 16MB


@stamina.retry(on=(botocore.exceptions.ClientError, aiohttp.ClientError))
async def _head_object(bucket: str, key: str) -> 'HeadObjectOutputTypeDef | None':
    """Get the metadata of an S3 file.

    :param bucket: Name of the S3 bucket.
    :param key: Key of the file.
    :return: Metadata of the file. None if the file does not exist or is a directory.
    """
    try:
        return await S3_CLIENT.head_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        match e.response:
            case {'Error': {'Code': '404'}}:
                return None
        raise


@cached(LRUCache(maxsize=256))
@stamina.retry(on=(botocore.exceptions.ClientError, aiohttp.ClientError))
async def _get_subkeys(path: Path, bucket: str, key: str) -> dict[str, S3Path]:
    """Get all subkeys of a directory in S3. If key points to a file, return an empty dict.

    :param path: Path to the directory.
    :param bucket: Name of the S3 bucket.
    :param key: Key of the directory or file.
    :return: Mapping of subkeys to their S3Path instances.
    """
    subkey_relative_start_i = len(key) + 1
    empty_dict = {}
    result: list[tuple[str, S3Path]] = []
    paginator = S3_CLIENT.get_paginator('list_objects_v2')
    async for page in paginator.paginate(
        Bucket=bucket,
        Prefix=f'{key}/',
    ):
        for o in page.get('Contents', ()):
            subkey: str = o['Key']  # type: ignore
            subkey_relative = subkey[subkey_relative_start_i:]
            subpath = path.joinpath(subkey_relative)

            last_modified = o.get('LastModified') or datetime.fromtimestamp(0, UTC)
            etag = o.get('ETag', '0' * 32)
            size = o.get('Size', 0)

            if etag[-1] == '"':
                etag = etag.split('"')[-2].lower()
            if '-' in etag:
                etag = '0' * 32  # drop multipart checksums

            result.append((
                subkey,
                S3Path(
                    path=subpath,
                    bucket=bucket,
                    key=subkey,
                    key_relative=subkey_relative,
                    last_modified=last_modified,
                    etag=etag,
                    size=size,
                    subkeys=empty_dict,
                ),
            ))
    logging.debug('_get_subkeys(%r, %r) = %d subkeys', bucket, key, len(result))
    return dict(result)


def get_all_files(
    scene: Path, s3_scene: S3Path | None
) -> tuple[Collection[Path], Collection[S3Path]]:
    if s3_scene:
        if not s3_scene.is_dir():
            return (), (s3_scene,)
        else:
            return (), s3_scene.subkeys.values()
    elif not scene.is_dir():
        return (scene,), ()
    else:
        search_dirs: list[PathLike] = [scene]
        result: list[Path] = []
        while search_dirs:
            for p in scandir(search_dirs.pop()):
                if p.name[:1] == '.':  # skip hidden files
                    continue
                if p.is_dir():
                    search_dirs.append(p.path)
                    continue
                result.append(Path(p.path))
        return result, ()
