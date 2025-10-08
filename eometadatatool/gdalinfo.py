import asyncio
import logging


async def run_gdalinfo(path: str, /, *, deep: bool = False) -> bytes | None:
    """Run gdalinfo subprocess and return raw JSON data.

    :param path: Local or S3 path to the scene
    :param deep: Whether to deeply analyze files to extract even more metadata (slow)
    :return: Raw gdalinfo JSON data
    """
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
    )

    stdout, _ = await process.communicate()
    return None if process.returncode else stdout
