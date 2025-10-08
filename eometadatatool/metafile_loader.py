import logging
from contextlib import contextmanager
from fnmatch import fnmatch, fnmatchcase
from functools import lru_cache
from gzip import GzipFile
from os import getenv
from os.path import basename
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZipFile

import h5netcdf
import numpy as np
from s3fs import S3FileSystem

from eometadatatool.geom_utils import average_angles
from eometadatatool.performance import logtime, logtime_decorator
from eometadatatool.s3_utils import S3Path


def is_multi_metafile(metafile: str) -> tuple[bool, str]:
    """Check if metafile is a multi-file pattern (wrapped in [...])."""
    return (
        (True, metafile[1:-1])
        if (metafile[:1] == '[' and metafile[-1:] == ']')
        else (False, metafile)
    )


@logtime_decorator
def find_in_directory(scene: Path, metafile: str) -> list[Path]:
    """Find a metadata file in a directory.

    :param scene: Path to the directory.
    :param metafile: Name of the metadata file (with support for pattern matching).
    :raises FileNotFoundError: If the metadata file is not found in the directory.
    :raises FileExistsError: If multiple metadata files are found in the directory.
    :return: Path to the metadata file.
    """
    multi_metafile, metafile = is_multi_metafile(metafile)
    paths = list(scene.glob(metafile, case_sensitive=False))
    if not paths:
        raise FileNotFoundError(f'Metafile {metafile!r} not found in {scene!r} (DIR)')
    if not multi_metafile and len(paths) > 1:
        raise FileExistsError(
            f'Multiple metafiles {metafile!r} found in {scene!r} (DIR)'
        )

    logging.debug('find_in_directory(metafile=%r) = %r', metafile, paths)
    return paths


@logtime_decorator
def find_in_s3_directory(s3_scene: S3Path, metafile: str) -> list[S3Path]:
    """Find a metadata file in a S3 directory.

    :param s3_scene: S3Path to the directory.
    :param metafile: Name of the metadata file (with support for pattern matching).
    :raises NotADirectoryError: If the S3Path does not represent a directory.
    :raises FileNotFoundError: If the metadata file is not found in the directory.
    :raises FileExistsError: If multiple metadata files are found in the directory.
    :return: S3Path to the metadata file.
    """
    if not s3_scene.is_dir():
        raise NotADirectoryError(
            f'Metafile {metafile!r} not found in {s3_scene!s}, not a directory'
        )

    multi_metafile, metafile = is_multi_metafile(metafile)
    metafile_fnmatch = _prepare_metafile_fnmatch(metafile)
    subkeys = [sk for sk in s3_scene.subkeys if fnmatchcase(sk, metafile_fnmatch)]

    if not subkeys:
        raise FileNotFoundError(f'Metafile {metafile!r} not found in {s3_scene!s} (S3)')

    if not multi_metafile and len(subkeys) > 1:
        gsc_cr_esa_files = [
            sk for sk in subkeys if fnmatch(basename(sk), 'GSC*CR**.xml')
        ]
        if len(gsc_cr_esa_files) > 1:
            subkeys = [gsc_cr_esa_files[0]]  # pick first
        else:
            raise FileExistsError(
                f'Multiple metafiles {metafile!r} found in {s3_scene!s} (S3)'
            )

    logging.debug('find_in_s3_directory(metafile=%r) = %r', metafile, subkeys)
    return [s3_scene.get_subpath(sk) for sk in subkeys]


@contextmanager
def extract_from_zip(scene: Path, metafile: str):
    """Extract a metadata file from a ZIP archive.

    :param scene: Path to the archive.
    :param metafile: Name of the metadata file (with support for pattern matching).
    :raises FileNotFoundError: If the metadata file is not found in the archive.
    :raises FileExistsError: If multiple metadata files are found in the archive.
    :return: Path to the metadata file.
    """
    with ZipFile(scene, 'r') as archive:
        metafile_fnmatch = _prepare_metafile_fnmatch(metafile)
        match tuple(
            filename
            for filename in archive.namelist()
            if fnmatchcase(filename, metafile_fnmatch)
        ):
            case ():
                raise FileNotFoundError(
                    f'Metafile {metafile!r} not found in {scene!r} (ZIP)'
                )
            case (filename,):
                logging.debug('extract_from_zip(metafile=%r) = %r', metafile, filename)
                with TemporaryDirectory() as tmpdir:
                    with logtime('Extracting from ZIP archive'):
                        path = Path(archive.extract(filename, path=tmpdir))
                    yield path
            case _:
                raise FileExistsError(
                    f'Multiple metafiles {metafile!r} found in {scene!r} (ZIP)'
                )


@contextmanager
def extract_from_tar(scene: Path, metafile: str):
    """Extract a metadata file from an optionally compressed TAR archive.

    :param scene: Path to the archive.
    :param metafile: Name of the metadata file (with support for pattern matching).
    :raises FileNotFoundError: If the metadata file is not found in the archive.
    :raises FileExistsError: If multiple metadata files are found in the archive.
    :return: Path to the metadata file.
    """
    with TarFile(scene, 'r') as archive:
        metafile_fnmatch = _prepare_metafile_fnmatch(metafile)
        match tuple(
            filename
            for filename in archive.getnames()
            if fnmatchcase(filename, metafile_fnmatch)
        ):
            case ():
                raise FileNotFoundError(
                    f'Metafile {metafile!r} not found in {scene!r} (TAR)'
                )
            case (filename,):
                logging.debug('extract_from_tar(metafile=%r) = %r', metafile, filename)
                with TemporaryDirectory() as tmpdir:
                    with logtime('Extracting from TAR archive'):
                        archive.extract(filename, path=tmpdir, filter='data')
                    yield next(iter(Path(tmpdir).iterdir()))
            case _:
                raise FileExistsError(
                    f'Multiple metafiles {metafile!r} found in {scene!r} (TAR)'
                )


@contextmanager
def extract_from_gzip(scene: Path):
    """Extract content of a GZIP-compressed file."""
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir, scene.stem)
        with (
            logtime('Decompressing GZIP file'),
            path.open('xb') as f,
            GzipFile(scene, 'rb') as gz,
        ):
            while chunk := gz.read(16 * 1024 * 1024):  # 16MB
                f.write(chunk)
        yield path


def extract_from_netcdf(scene: Path) -> dict[str, dict | Any]:
    """Read metadata from a netCDF file stored locally or on S3."""
    path = scene.as_posix()
    if path[:4] == 's3:/':
        kwargs: dict[str, Any] = {'default_block_size': 512 * 1024}  # 512 KiB
        endpoint = (
            getenv('AWS_ENDPOINT_URL_S3')
            or getenv('AWS_S3_ENDPOINT')
            or getenv('AWS_ENDPOINT_URL')
        )
        if endpoint:
            kwargs['endpoint_url'] = endpoint
        with (
            S3FileSystem(**kwargs).open('s3://' + path[4:]) as f,
            h5netcdf.File(f) as ds,
        ):
            return _extract_from_netcdf(ds, '/', {}, {}, {})

    with h5netcdf.File(scene) as ds:
        return _extract_from_netcdf(ds, '/', {}, {}, {})


def _extract_from_netcdf(
    group: h5netcdf.Group,
    path: str,
    attrs: dict[str, Any],
    vars: dict[str, Any],
    dims: dict[str, Any],
    _time_first: Any | None = None,
) -> dict[str, dict | Any]:
    """Extract a minimal, serializable view of a netCDF group.

    Single-pass, depth-first traversal with predictable access patterns.
    Only the first value of the ``time`` variable is read (on first
    encounter) and reused for both the ``time`` variable and dimension.
    This avoids global scans and full-array reads.
    """
    # _time_first is threaded through recursion (computed lazily on first use)

    # Group-level attributes: normalize to JSON-friendly primitives.
    # Build key prefix once to avoid repeated replace() work per attribute.
    prefix = path[1:].replace('/', '_')  # path always starts with '/'
    for attr_name, attr_value in group.attrs.items():
        v = attr_value
        if isinstance(v, np.generic):
            v = v.item()
        if v is None:
            continue
        if isinstance(v, bytes):
            v = v.decode()
        attrs[prefix + attr_name] = v

    # Dimensions: only attach values for 'time' to keep output compact.
    for dim_name, dim_obj in group.dimensions.items():
        entry = {
            'name': dim_name,
            'size': int(dim_obj.size),
            'defined_in': path,
            'values': None,
        }

        if dim_name == 'time' and _time_first is not None:
            entry['values'] = [_time_first]

        dims[dim_name] = entry

    # Variables in this group
    for var_name, variable in group.variables.items():
        # Extract minimal metadata for each variable
        var_info = {
            'shape': variable.shape,
            'dimensions': list(variable.dimensions),
            'values': None,
            'dtype': variable.dtype,
        }

        # Pull only attributes needed downstream (normalize to JSON-friendly)
        for k in ('long_name', 'standard_name', 'comment', 'units'):
            v = variable.attrs.get(k)
            if isinstance(v, np.generic):
                v = v.item()
            if v is None:
                continue
            if isinstance(v, bytes):
                v = v.decode()
            var_info[k] = v

        # Only get the first value for 'time' to avoid full reads
        if var_name == 'time':
            if _time_first is None:
                try:
                    _time_first = variable[0].item()
                except Exception as e:
                    logging.warning('Error extracting first time value: %r', e)

            if _time_first is not None:
                var_info['values'] = [_time_first]
                # Backfill dimension value if it was created earlier
                dim_time = dims.get('time')
                if dim_time is not None and dim_time.get('values') is None:
                    dim_time['values'] = [_time_first]

        # For lat/lon derive extent from attributes when available
        if var_name in {
            'latitude',
            'longitude',
            'latitude_csa',
            'latitude_ccd',
            'longitude_csa',
            'longitude_ccd',
        }:
            var_info['extent'] = [
                variable.attrs.get('min_val') or variable.attrs.get('valid_min'),
                variable.attrs.get('max_val') or variable.attrs.get('valid_max'),
            ]

        # nodata:
        fill = variable.attrs.get('_FillValue')
        if fill is not None:
            var_info['nodata'] = fill

        vars[var_name] = var_info

    # Recursively process subgroups
    for subgroup_name, subgroup in group.groups.items():
        _extract_from_netcdf(
            subgroup,
            path + subgroup_name + '/',
            attrs,
            vars,
            dims,
            _time_first,
        )

    return {'attributes': attrs, 'variables': vars, 'dimensions': dims}


def read_from_oat(scene: Path) -> dict[str, float]:
    """Read averaged angles from an OAT file.

    :param scene: Path to the file.
    :return: Mapping of column names to averaged angles.
    """
    with logtime('Calculating average angles from OAT file'):
        angles = np.loadtxt(scene).T
        angles = average_angles(angles)
    return {f'Column {i}': angle for i, angle in enumerate(angles.tolist(), start=1)}  # type: ignore


@lru_cache(maxsize=256)
def _prepare_metafile_fnmatch(metafile: str) -> str:
    """Prepare a metafile for fnmatch matching."""
    return f'**{metafile}' if metafile[0] == '/' else f'**/{metafile}'
