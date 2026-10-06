import io
import re

import logging
import orjson
import subprocess
from contextlib import contextmanager
from enum import Enum
from fnmatch import fnmatchcase
from functools import lru_cache
from gzip import GzipFile
from os import getenv
from pathlib import Path
from pyhdf.SD import SD, SDC
from tarfile import TarFile
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZipFile

import h5netcdf
import netCDF4
import numpy as np
from s3fs import S3FileSystem

from eometadatatool.geom_utils import average_angles
from eometadatatool.performance import logtime, logtime_decorator
from eometadatatool.s3_utils import S3Path

# HDF5 magic bytes: used to distinguish netCDF-4/HDF5 from netCDF-3 classic.
_HDF5_MAGIC = b'\x89HDF\r\n\x1a\n'


# Map GDAL type names to numpy-compatible dtype strings
_GDAL_TO_NUMPY_DTYPE: dict[str, str] = {
    'Byte': 'uint8',
    'Int8': 'int8',
    'UInt16': 'uint16',
    'Int16': 'int16',
    'UInt32': 'uint32',
    'Int32': 'int32',
    'Float32': 'float32',
    'Float64': 'float64',
    'CFloat32': 'complex64',
    'CFloat64': 'complex128',
}


class MetafileMode(Enum):
    SINGLE = 'single'  # default: exactly one match required
    MULTI = 'multi'  # [...]: multiple matches, return all
    FIRST = 'first'  # (...): allow duplicates, return first


def parse_metafile(metafile: str) -> tuple[MetafileMode, str]:
    """Parse metafile string for mode markers.

    - ``[pattern]`` -> MULTI (return all matches)
    - ``(pattern)`` -> FIRST (allow duplicates, return first)
    - ``pattern``   -> SINGLE (exactly one match)
    """
    if metafile[:1] == '[' and metafile[-1:] == ']':
        return MetafileMode.MULTI, metafile[1:-1]
    if metafile[:1] == '(' and metafile[-1:] == ')':
        return MetafileMode.FIRST, metafile[1:-1]
    return MetafileMode.SINGLE, metafile


def is_multi_metafile(metafile: str) -> tuple[bool, str]:
    """Check if metafile is a multi-file pattern (wrapped in [...])."""
    mode, name = parse_metafile(metafile)
    return mode == MetafileMode.MULTI, name


def _is_hdf5_bytes(data: bytes) -> bool:
    """Return True if the byte buffer starts with the HDF5 magic signature."""
    return data[:8] == _HDF5_MAGIC


def _is_hdf5_file(path: Path) -> bool:
    """Return True if the file at *path* starts with the HDF5 magic signature."""
    with path.open('rb') as f:
        return f.read(8) == _HDF5_MAGIC


@logtime_decorator
def find_in_directory(scene: Path, metafile: str) -> list[Path]:
    """Find a metadata file in a directory.

    :param scene: Path to the directory.
    :param metafile: Name of the metadata file (with support for pattern matching).
    :raises FileNotFoundError: If the metadata file is not found in the directory.
    :raises FileExistsError: If multiple metadata files are found in the directory.
    :return: Path to the metadata file.
    """
    mode, metafile = parse_metafile(metafile)
    paths = list(scene.glob(metafile, case_sensitive=False))
    if not paths:
        raise FileNotFoundError(f'Metafile {metafile!r} not found in {scene!r} (DIR)')
    if mode == MetafileMode.SINGLE and len(paths) > 1:
        raise FileExistsError(
            f'Multiple metafiles {metafile!r} found in {scene!r} (DIR)'
        )
    if mode == MetafileMode.FIRST and len(paths) > 1:
        logging.info(
            'Multiple metafiles %r found in %r (DIR), using first match',
            metafile,
            scene,
        )
        paths = paths[:1]

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

    mode, metafile = parse_metafile(metafile)
    metafile_fnmatch = _prepare_metafile_fnmatch(metafile)
    subkeys = [sk for sk in s3_scene.subkeys if fnmatchcase(sk, metafile_fnmatch)]

    if not subkeys:
        raise FileNotFoundError(f'Metafile {metafile!r} not found in {s3_scene!s} (S3)')

    if mode == MetafileMode.SINGLE and len(subkeys) > 1:
        raise FileExistsError(
            f'Multiple metafiles {metafile!r} found in {s3_scene!s} (S3)'
        )
    if mode == MetafileMode.FIRST and len(subkeys) > 1:
        logging.info(
            'Multiple metafiles %r found in %s (S3), using first match',
            metafile,
            s3_scene,
        )
        subkeys = subkeys[:1]

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
    with TarFile.open(scene, 'r') as archive:
        metafile_fnmatch = _prepare_metafile_fnmatch(metafile)
        match tuple(
            filename
            for filename in archive.getnames()
            if fnmatchcase(f'/{filename}', metafile_fnmatch)
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
                    yield Path(tmpdir, filename)
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


class _NC4AttrsView:
    """Emulates the h5netcdf attrs dict-like interface for a netCDF4 object."""

    __slots__ = ('_obj',)

    def __init__(self, obj: netCDF4.Dataset | netCDF4.Group | netCDF4.Variable) -> None:
        self._obj = obj

    def items(self):
        return ((k, self._obj.getncattr(k)) for k in self._obj.ncattrs())

    def get(self, key: str, default=None):
        try:
            return self._obj.getncattr(key)
        except AttributeError:
            return default


class _NC4GroupAdapter:
    """Wraps a netCDF4 Dataset/Group to expose the h5netcdf Group interface."""

    __slots__ = ('_grp',)

    def __init__(self, grp: netCDF4.Dataset | netCDF4.Group) -> None:
        self._grp = grp

    @property
    def attrs(self) -> _NC4AttrsView:
        return _NC4AttrsView(self._grp)

    @property
    def dimensions(self) -> dict:
        return {
            name: _NC4DimAdapter(dim)
            for name, dim in self._grp.dimensions.items()
        }

    @property
    def variables(self) -> dict:
        return {
            name: _NC4VariableAdapter(var)
            for name, var in self._grp.variables.items()
        }

    @property
    def groups(self) -> dict:
        return {
            name: _NC4GroupAdapter(grp)
            for name, grp in self._grp.groups.items()
        }


class _NC4DimAdapter:
    """Wraps netCDF4.Dimension to expose h5netcdf Dimension.size."""

    __slots__ = ('_dim',)

    def __init__(self, dim: netCDF4.Dimension) -> None:
        self._dim = dim

    @property
    def size(self) -> int:
        return len(self._dim)


class _NC4VariableAdapter:
    """Wraps netCDF4.Variable to expose the h5netcdf Variable interface."""

    __slots__ = ('_var',)

    def __init__(self, var: netCDF4.Variable) -> None:
        self._var = var

    @property
    def attrs(self) -> _NC4AttrsView:
        return _NC4AttrsView(self._var)

    @property
    def shape(self):
        return self._var.shape

    @property
    def dimensions(self):
        return self._var.dimensions

    @property
    def dtype(self):
        return self._var.dtype

    def __getitem__(self, item):
        return self._var[item]


def extract_from_netcdf(scene: Path) -> dict[str, dict | Any]:
    """Read metadata from a netCDF file (HDF5-based or classic) on disk or S3.

    Format is detected via the HDF5 magic bytes rather than by attempting
    to open and catching exceptions:
    - HDF5/netCDF-4 files (e.g. Sentinel-5P) are opened with h5netcdf.
    - Classic netCDF-3 files (e.g. Sentinel-1 OCN) are opened with netCDF4
      and wrapped in an adapter that exposes the same interface.

    For S3 paths the full file is read into memory first (required for both
    backends), and the magic-byte check is performed on the in-memory buffer.
    """
    path = scene.as_posix()

    if path[:4] == 's3:/':
        return _extract_from_netcdf_s3(path)

    return _extract_from_netcdf_local(scene)


def _extract_from_netcdf_local(scene: Path) -> dict[str, dict | Any]:
    """Open a local netCDF file using the appropriate backend."""
    if _is_hdf5_file(scene):
        logging.debug('extract_from_netcdf: HDF5 format detected for %r', scene)
        try:
            with h5netcdf.File(scene) as ds:
                return _extract_from_netcdf(ds, '/', {}, {}, {})
        except Exception as exc:
            raise RuntimeError(
                f'Failed to read HDF5/netCDF-4 file {scene!r} with h5netcdf'
            ) from exc
    else:
        logging.debug('extract_from_netcdf: classic netCDF-3 format detected for %r', scene)
        try:
            with netCDF4.Dataset(scene, mode='r') as ds:
                return _extract_from_netcdf(_NC4GroupAdapter(ds), '/', {}, {}, {})
        except Exception as exc:
            raise RuntimeError(
                f'Failed to read classic netCDF-3 file {scene!r} with netCDF4'
            ) from exc


def _get_s3_endpoint() -> str | None:
    """Resolve the configured S3 endpoint (if any) from the environment.

    Checks the same set of environment variables used elsewhere in the
    codebase (s3fs/boto3-style names), so that all S3 access paths
    (netCDF via s3fs, TIFF via gdalinfo/GDAL) agree on the same endpoint.
    """
    return (
        getenv('AWS_ENDPOINT_URL_S3')
        or getenv('AWS_S3_ENDPOINT')
        or getenv('AWS_ENDPOINT_URL')
    )


def _s3_endpoint_host(endpoint: str) -> tuple[str, bool]:
    """Split an endpoint URL into (host[:port], use_https) for GDAL's
    AWS_S3_ENDPOINT / AWS_HTTPS config options, which expect a bare host
    without the scheme.
    """
    use_https = True
    host = endpoint
    if host.startswith('https://'):
        host = host[len('https://'):]
    elif host.startswith('http://'):
        host = host[len('http://'):]
        use_https = False
    host = host.rstrip('/')
    return host, use_https


def _extract_from_netcdf_s3(path: str) -> dict[str, dict | Any]:
    kwargs: dict[str, Any] = {}
    endpoint = _get_s3_endpoint()
    if endpoint:
        kwargs['endpoint_url'] = endpoint

    fs = S3FileSystem(**kwargs)
    key = path[4:]  # strip 's3:/'

    # Peek at magic bytes with a minimal fetch to detect format.
    with fs.open(key, cache_type='blockcache', block_size=512 * 1024) as f:
        magic = f.read(8)
        f.seek(0)

        if magic == _HDF5_MAGIC:
            logging.debug('extract_from_netcdf: HDF5 format detected for S3 path %r', path)
            try:
                with h5netcdf.File(f, mode='r') as ds:
                    return _extract_from_netcdf(ds, '/', {}, {}, {})
            except Exception as exc:
                raise RuntimeError(
                    f'Failed to read HDF5/netCDF-4 file from S3 {path!r} with h5netcdf'
                ) from exc
        else:
            # NetCDF-3 classic: netCDF4 requires a seekable buffer or memory,
            # not a streaming file-like object — fall back to full download.
            logging.debug(
                'extract_from_netcdf: classic netCDF-3 format detected for S3 path %r, '
                'falling back to full download', path
            )
            data = f.read()  # f is already seeked to 0, reads the whole file

    try:
        with netCDF4.Dataset('inmemory', memory=data, mode='r') as ds:
            return _extract_from_netcdf(_NC4GroupAdapter(ds), '/', {}, {}, {})
    except Exception as exc:
        raise RuntimeError(
            f'Failed to read classic netCDF-3 file from S3 {path!r} with netCDF4'
        ) from exc


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

        if dim_name in ['lat', 'latitude', 'lon', 'longitude']:
            try:
                values = group.variables[dim_name][...]
                entry['values'] = (min(values), max(values))
            except KeyError:
                logging.warning('Failed to find min/max for dimension %r', dim_name)

        if dim_name == 'time' and _time_first is not None:
            entry['values'] = [_time_first]

        dims[dim_name] = entry

    # Variables in this group
    for var_name, variable in group.variables.items():
        # Skip scalar/dimensionless variables (e.g. CRS grid_mapping containers)
        # h5netcdf raises ValueError on .shape/.dimensions for these when no
        # HDF5 dimension scale is associated with their axes.
        try:
            dims_list = list(variable.dimensions)
            shape = variable.shape
        except ValueError:
            logging.debug(
                'Skipping variable %r: no dimension scale (likely scalar CRS)', var_name
            )
            continue

        # Extract minimal metadata for each variable
        var_info = {
            'shape': shape,
            'dimensions': dims_list,
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
            'lat',
            'lon',
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


def extract_from_hdf4(scene: Path) -> dict[str, Any]:
    def j(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, np.generic):
            v = v.item()
        if isinstance(v, (bytes, bytearray)):
            try:
                v = v.decode()
            except Exception:
                v = v.decode(errors="replace")
        if isinstance(v, str):
            v = v.replace("\x00", "")
        if isinstance(v, (list, tuple)):
            v = [j(x) for x in v]
        return v

    keep = {
        "long_name", "standard_name", "units", "scale_factor", "add_offset",
        "_FillValue", "fill_value", "valid_min", "valid_max", "min_val", "max_val",
    }

    sd = SD(scene.as_posix(), SDC.READ)
    datasets: dict[str, Any] = {}
    try:
        for name in sd.datasets().keys():
            try:
                sds = sd.select(name)
                _n, _r, dims, dtype, _na = sds.info()
                out = {"shape": tuple(int(x) for x in dims), "dtype": j(dtype)}

                try:
                    a = sds.attributes()
                except Exception:
                    a = {}

                for k in keep:
                    if k in a:
                        out[k] = j(a.get(k))

                fv = a.get("_FillValue") or a.get("fill_value")
                if fv is not None:
                    out["nodata"] = j(fv)

                datasets[name] = out
                try:
                    sds.endaccess()
                except Exception:
                    pass
            except Exception as e:
                datasets[name] = {"error": repr(e)}
        return {"datasets": datasets}
    finally:
        try:
            sd.end()
        except Exception:
            pass

def read_from_oat(scene: Path) -> dict[str, float]:
    """Read averaged angles from an OAT file.

    :param scene: Path to the file.
    :return: Mapping of column names to averaged angles.
    """
    with logtime('Calculating average angles from OAT file'):
        angles = np.loadtxt(scene).T
        angles = average_angles(angles)
    return {f'Column {i}': angle for i, angle in enumerate(angles.tolist(), start=1)}  # type: ignore


def read_from_tiff(scene: Path) -> dict:
    with logtime('Reading TIFF file'):
        cmd = ['gdalinfo', '-json']

        # When reading a TIFF from S3 (via /vsis3/...), gdalinfo/GDAL does
        # NOT pick up AWS_ENDPOINT_URL_S3 / AWS_ENDPOINT_URL (those are
        # s3fs/boto3-style names). GDAL only understands its own
        # AWS_S3_ENDPOINT config option, so without it GDAL falls back to
        # building a default AWS endpoint from the region, which produces
        # bogus hosts like s3.us-east-2.amazonaws.com and 403s. Pass the
        # same endpoint used elsewhere (s3fs) explicitly via --config so
        # both code paths agree.
        scene_str = str(scene)
        if scene_str.startswith('/vsis3/'):
            endpoint = _get_s3_endpoint()
            if endpoint:
                host, use_https = _s3_endpoint_host(endpoint)
                cmd += [
                    '--config', 'AWS_S3_ENDPOINT', host,
                    '--config', 'AWS_HTTPS', 'YES' if use_https else 'NO',
                    '--config', 'AWS_VIRTUAL_HOSTING', 'FALSE',
                ]

        cmd.append(scene_str)

        result = subprocess.run(  # noqa: S603
            cmd,  # noqa: S607
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f'gdalinfo failed for {scene}: {result.stderr.decode()}'
            )
        info = orjson.loads(result.stdout)

        width, height = info['size']
        bands = info['bands']
        count = len(bands)
        driver = info['driverShortName']

        # GDAL GeoTransform: (xoff, xscale, xskew, yoff, yskew, yscale)
        # Convert to affine format: [xscale, xskew, xoff, yskew, yscale, yoff]
        gt = info['geoTransform']
        transform = [gt[1], gt[2], gt[0], gt[4], gt[5], gt[3]]

        corners = info['cornerCoordinates']
        ul = corners['upperLeft']
        ur = corners['upperRight']
        lr = corners['lowerRight']
        ll = corners['lowerLeft']
        bounds = (
            f'POLYGON(('
            f'{ul[0]} {ul[1]}, '
            f'{ur[0]} {ur[1]}, '
            f'{lr[0]} {lr[1]}, '
            f'{ll[0]} {ll[1]}, '
            f'{ul[0]} {ul[1]}'
            f'))'
        )

        band0 = bands[0]
        nodata = band0.get('noDataValue')
        gdal_dtype = band0['type']
        dtype = _GDAL_TO_NUMPY_DTYPE.get(gdal_dtype, gdal_dtype.lower())

        # Main TIFF metadata tags live in the default (empty-string) domain
        main_meta = info.get('metadata', {}).get('', {})

        tiff_data: dict = {
            'width': width,
            'height': height,
            'count': count,
            'dtype': dtype,
            'driver': driver,
            'transform': transform,
            'bounds': bounds,
            'nodata': nodata,
            **main_meta,
            **{f'band_{i + 1}': band.get('metadata', {}) for i, band in enumerate(bands)},
        }

        wkt = info.get('coordinateSystem', {}).get('wkt', '')
        if wkt:
            tiff_data['crs_wkt'] = wkt
            if m := re.search(r'ID\["EPSG",(\d+)]', wkt):
                epsg = int(m.group(1))
                tiff_data['crs'] = f'EPSG:{epsg}'
                tiff_data['epsg'] = epsg

    return tiff_data


def read_from_mtl(path: Path) -> dict:
    """Parse a Landsat MTL text file into a nested dict.

    The MTL format uses ``GROUP = name`` / ``END_GROUP = name`` blocks with
    ``KEY = value`` entries inside.  String values are stored without their
    surrounding double-quotes.

    :param path: Path to the ``*_MTL.txt`` file.
    :return: Nested dict mirroring the GROUP hierarchy.
    """
    stack: list[dict] = [{}]
    with path.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line == 'END':
                continue
            key, _, value = line.partition(' = ')
            key = key.strip()
            value = value.strip()
            if key == 'GROUP':
                new_group: dict = {}
                stack[-1][value] = new_group
                stack.append(new_group)
            elif key == 'END_GROUP':
                stack.pop()
            else:
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                stack[-1][key] = value
    return stack[0]


def read_from_sp3(path: Path) -> dict[str, Any]:
    """Read an SP3 header. Timestamps are GPS scale, returned as UTC."""
    from astropy.time import Time

    with path.open('rb') as f:
        h0, h1 = f.read(512).decode('ascii', 'replace').splitlines()[:2]
    start = int(h1[3:7]) * 604800 + float(h1[8:23])
    end = start + float(h1[24:38]) * (int(h0[32:39]) - 1)
    return {
        'beginningDateTime': Time(start, format='gps', precision=6).utc.isot + 'Z',
        'endingDateTime': Time(end, format='gps', precision=6).utc.isot + 'Z',
        'processingCenter': h0[56:60].strip(),
    }


@lru_cache(maxsize=256)
def _prepare_metafile_fnmatch(metafile: str) -> str:
    """Prepare a metafile for fnmatch matching."""
    return f'**{metafile}' if metafile[0] == '/' else f'**/{metafile}'
