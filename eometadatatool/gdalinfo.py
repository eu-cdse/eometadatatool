import asyncio
import logging
import os
import re

import stamina


class GdalInfoError(Exception):
    pass


def _gdal_s3_env() -> dict[str, str]:
    env = os.environ.copy()
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL', '')
    env['GDAL_SKIP'] = 'netCDF'
    if endpoint_url:
        hostname = endpoint_url.replace('https://', '').replace('http://', '').rstrip('/')
        env['AWS_S3_ENDPOINT'] = hostname
        env['AWS_HTTPS'] = 'YES'
        env['AWS_VIRTUAL_HOSTING'] = 'FALSE'
    return env


async def get_gdal_version() -> tuple[int, ...] | None:
    try:
        process = await asyncio.create_subprocess_exec(
            *(
                'gdalinfo',
                '--version',
            ),
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            # e.g. "GDAL 3.8.4, released 2024/02/08" -> (3, 8, 4)
            match = re.search(r'(\d+)\.(\d+)\.(\d+)', stdout.decode())
            if match:
                return tuple(int(part) for part in match.groups())
    except Exception as e:
        logging.error("Error getting GDAL version: %s", e)

    return None


async def run_gdalinfo(path: str, /, *, deep: bool = False) -> bytes | None:
    """Run gdalinfo subprocess and return raw JSON data.

    :param path: Local or S3 path to the scene
    :param deep: Whether to deeply analyze files to extract even more metadata (slow)
    :return: Raw gdalinfo JSON data
    """
    try:
        return await _run_gdalinfo(path, deep=deep)
    except GdalInfoError:
        return None


@stamina.retry(on=GdalInfoError, attempts=2)
async def _run_gdalinfo(path: str, /, *, deep: bool = False) -> bytes:
    gdal_path = path.replace('s3://', '/vsis3/', 1)
    logging.debug('Running gdalinfo on path %r', gdal_path)

    process = await asyncio.create_subprocess_exec(
        *(
            'gdalinfo',
            '-json',
            *(
                (
                    '-checksum',
                    '-stats',
                )
                if deep
                else ()
            ),
            gdal_path,
        ),
        stdout=asyncio.subprocess.PIPE,
        env=_gdal_s3_env(),
    )

    stdout, _ = await process.communicate()
    if process.returncode:
        raise GdalInfoError(f'gdalinfo exited with code {process.returncode}')
    return stdout
