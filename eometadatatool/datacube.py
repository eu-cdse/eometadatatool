from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Any

import numpy as np
import orjson


def _get_dimension_type_axis(name: str) -> tuple[str, str | None]:
    """Return dimension type and axis."""
    if name in {'scanline', 'latitude_ccd', 'latitude_csa'}:
        return 'spatial', 'y'
    if name in {'ground_pixel', 'longitude_ccd', 'longitude_csa'}:
        return 'spatial', 'x'
    if name == 'time':
        return 'temporal', None
    return 'other', None


def _get_variable_type(name: str) -> str:
    """Return variable type."""
    return (
        'auxiliary'
        if name
        in {
            'corner',
            'delta_time',
            'ground_pixel',
            'latitude',
            'longitude',
            'scanline',
            'time_utc',
            'time',
        }
        else 'data'
    )


def _get_description(meta: dict | None) -> Any | None:
    """Pick a human-friendly description from common CF attributes."""
    if not meta:
        return None
    for key in ('long_name', 'standard_name', 'comment'):
        if (value := meta.get(key)) is not None:
            return value
    return None


def _get_unit(meta: dict) -> Any | None:
    units = meta.get('units')
    return units if units and units != '1' else None


def _get_nodata(meta: dict) -> Any | None:
    nodata = meta.get('nodata')
    if nodata is None:
        return None
    value = _serialize(nodata)
    return value or None


def _get_datatype(meta: dict) -> str | None:
    dtype = meta.get('dtype')
    if isinstance(dtype, np.dtype):
        dtype = dtype.name
    if not isinstance(dtype, str):
        return None
    if dtype.startswith(('int', 'uint')):
        return dtype
    if dtype.startswith('complex'):
        # Map numpy complex<N> to cfloat<N>
        return 'cfloat' + dtype[7:]
    return 'other'


def _serialize(o: Any) -> Any:
    if isinstance(o, bytes):
        return o.decode()
    if isinstance(o, np.floating):
        o = o.tolist()
    elif isinstance(o, np.generic):
        return o.tolist()
    if isinstance(o, float) and not isfinite(o):
        return str(o)
    return o


def _to_iso8601_from_seconds(seconds: float) -> str:
    base = datetime(2010, 1, 1, tzinfo=UTC)
    return (base + timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def _build_dimension(name: str, dim: dict, vars_dict: dict) -> tuple[str, dict]:
    dim_type, axis = _get_dimension_type_axis(name)
    result: dict[str, Any] = {'type': dim_type}

    if axis:
        result['axis'] = axis
    if description := _get_description(vars_dict.get(name)):
        result['description'] = description

    if dim_type == 'spatial':
        if name in {'latitude_ccd', 'latitude_csa'}:
            result['extent'] = [-20.0, 20.0]
            result['reference_system'] = 4326
        elif name in {'longitude_ccd', 'longitude_csa'}:
            result['extent'] = [-180.0, 180.0]
            result['reference_system'] = 4326
        else:
            # default 0..size extent for grid-like axes
            result['extent'] = [0, dim['size']]
    elif dim_type == 'temporal':
        # Keep extent consistent with other dimensions and attach first value if present
        result['extent'] = [0, dim['size']]
        if values := dim.get('values'):
            result['values'] = [_to_iso8601_from_seconds(values[0])]
    else:
        result['extent'] = [0, dim['size']]

    return name, result


def _build_variable(name: str, var: dict) -> tuple[str, dict] | None:
    dims = var.get('dimensions')
    if not dims:
        return None

    result: dict[str, Any] = {'dimensions': dims, 'type': _get_variable_type(name)}

    # Special-cases
    if name in {
        'latitude',
        'latitude_ccd',
        'latitude_csa',
        'longitude',
        'longitude_ccd',
        'longitude_csa',
    }:
        if extent := var.get('extent'):
            extent_min, extent_max = extent[0], extent[-1]
            if extent_min is None and extent_max is None:
                return None
            result['extent'] = [extent_min, extent_max]
    elif name == 'time' and (values := var.get('values')):
        result['values'] = [values[0]]

    # Common optionals
    if (desc := _get_description(var)) is not None and not isinstance(desc, tuple):
        result['description'] = desc
    if (unit := _get_unit(var)) is not None and not isinstance(unit, tuple):
        result['unit'] = unit
    if (nodata := _get_nodata(var)) is not None and not isinstance(nodata, tuple):
        result['nodata'] = nodata
    if (dtype := _get_datatype(var)) is not None:
        result['data_type'] = dtype

    return name, result


def extract_dims_vars(dims_dict: dict, vars_dict: dict) -> tuple[str, str]:
    """Build minimal DataCube-compliant dimensions and variables.

    Returns JSON strings for both objects (to be embedded into XML as text
    and later parsed with Dict datatype in mappings).
    """
    # Dimensions
    dimensions: dict[str, Any] = {}
    for dim_name, dim in dims_dict.items():
        key, value = _build_dimension(dim_name, dim, vars_dict)
        dimensions[key] = value

    # Variables
    variables: dict[str, Any] = {}
    for var_name, var in vars_dict.items():
        built = _build_variable(var_name, var)
        if built is None:
            continue
        key, value = built
        variables[key] = value

    return (
        orjson.dumps(dimensions, default=_serialize).decode(),
        orjson.dumps(variables, default=_serialize).decode(),
    )
