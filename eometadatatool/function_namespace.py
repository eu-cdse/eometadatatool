import logging
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal, cast

import dateutil.parser
import numpy as np
import orjson
from lxml import etree
from shapely import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
    linestrings,
    multilinestrings,
    multipoints,
    multipolygons,
    points,
    polygons,
)

from eometadatatool.etree_utils import single_xpathobject_tostr
from eometadatatool.flags import is_strict
from eometadatatool.geom_utils import normalize_geometry

if TYPE_CHECKING:
    from numpy.typing import NDArray

_registered: bool = False


def register_function_namespace() -> None:
    """Register default extension functions for lxml.etree."""
    global _registered
    if _registered:
        return
    _registered = True
    ns = etree.FunctionNamespace(None)
    ns['uppercase'] = _uppercase
    ns['lowercase'] = _lowercase
    ns['quote'] = _quote
    ns['regex-match'] = _regex_match
    ns['join'] = _join
    ns['WKT'] = _wkt
    ns['geo_pnt2wkt'] = _geo_pnt2wkt
    ns['map'] = _map
    ns['from_json'] = _from_json
    ns['date_format'] = _date_format
    ns['date_diff'] = _date_diff
    ns['find_in_list'] = _find_in_list


def _uppercase(_, a: 'etree._XPathObject') -> str:
    value = single_xpathobject_tostr(a)
    if not value and is_strict():
        raise ValueError(f'uppercase: empty input (type={type(a).__qualname__!r})')
    result = value.upper()
    logging.debug('uppercase(%r)  %r', value, result)
    return result


def _lowercase(_, a: 'etree._XPathObject') -> str:
    value = single_xpathobject_tostr(a)
    if not value and is_strict():
        raise ValueError(f'lowercase: empty input (type={type(a).__qualname__!r})')
    result = value.lower()
    logging.debug('lowercase(%r) = %r', value, result)
    return result


def _quote(_, a: Any) -> list[str]:
    """Quote XPath object as string list.

    Args:
        a: XPath object to quote.

    Returns:
        Single-element list with stringified value.
    """
    if isinstance(a, list) and len(a) == 1:
        return [str(a[0])]
    return [str(a)]


def _regex_match(_, a: 'etree._XPathObject', regex: str, group: int = 1) -> str:
    value = single_xpathobject_tostr(a)
    if not value:
        raise ValueError(f'regex-match: empty input (type={type(a).__qualname__!r})')
    match = re.search(regex, value)
    if not match:
        raise ValueError(f'regex-match: no match for {regex!r} in {value!r}')
    result = match.group(group)
    logging.debug(
        'regex-match(%r, regex=%r, group=%d) = %r', value, regex, group, result
    )
    return result


def _join(
    _, a: list[etree._Element | str] | etree._Element | str, separator: str = ', '
) -> str:
    """Join XPath elements with separator.

    Args:
        a: XPath element(s) to join.
        separator: String to use between elements.

    Returns:
        Joined string.
    """
    join_strs: list[str] = []
    for element in a if isinstance(a, list) else (a,):
        value = single_xpathobject_tostr(element)
        if value:
            join_strs.append(value)
        elif is_strict():
            raise ValueError(
                f'join: empty element in {a!r} (type={type(element).__qualname__!r})'
            )
    return separator.join(join_strs)


def _wkt(
    _,
    a: list[etree._Element | str] | etree._Element | str,
    input_mode: Literal['latlon', 'lonlat'] = 'latlon',
) -> str:
    """Convert coordinate list into a WKT representation.

    This function only extracts and converts coordinates.
    All antimeridian/pole handling is done in normalize_geometry().

    Args:
        a: XPath element(s) containing coordinates as "lat,lon" or "lon lat" strings.
        input_mode: Order of coordinates - 'latlon' (default) or 'lonlat'.

    Returns:
        WKT string (Point, Polygon, MultiPolygon, etc.).

    Raises:
        ValueError: If input is empty or invalid.
    """

    if not a:
        raise ValueError(f'WKT: empty input (type={type(a).__qualname__!r})')
    if input_mode not in {'latlon', 'lonlat'}:
        raise ValueError(f'WKT: invalid input_mode {input_mode!r}')

    rings: list[NDArray[np.float64]] = []  # [[[lon, lat], ...], ...]

    for element in a if isinstance(a, list) else (a,):
        value = single_xpathobject_tostr(element)
        if not value:
            raise ValueError(
                f'WKT: empty element in {a!r} (type={type(element).__qualname__!r})'
            )

        if ',' in value[:24]:
            value = value.replace(',', ' ')

        # [lat1, lon1, lat2, lon2, ...]:
        ring = np.fromstring(value, np.float64, sep=' ')
        # [[lat1, lon1], [lat2, lon2], ...]:
        ring = ring.reshape(-1, 2)

        # [[lon1, lat1], [lon2, lat2], ...]:
        if input_mode == 'latlon':
            ring = ring[:, [1, 0]]

        # auto-close polygon
        if len(ring) > 2 and not np.array_equal(ring[0], ring[-1]):
            ring = np.vstack([ring, ring[0]])

        rings.append(ring)

    if not rings:
        raise ValueError('WKT: empty input coordinates')

    single = len(rings) == 1
    first_ring_size = len(rings[0])
    if first_ring_size == 1:
        result = (
            cast('Point', points(rings[0]))
            if single
            else cast('MultiPoint', multipoints(np.vstack(rings)))
        ).wkt
    elif first_ring_size == 2:
        result = (
            cast('LineString', linestrings(rings[0]))
            if single
            else cast('MultiLineString', multilinestrings(rings))
        ).wkt
    else:
        result = normalize_geometry(
            cast('Polygon', polygons(rings[0]))
            if single
            else cast('MultiPolygon', multipolygons(rings))
        ).wkt

    logging.debug('WKT(...) = %r', result)
    return result


def _geo_pnt2wkt(context, a: list[etree._Element] | etree._Element) -> str:
    def get_text(e: etree._Element, xpath: str) -> str:
        obj = e.xpath(xpath)
        if not obj or not isinstance(obj, list):
            raise TypeError(
                f'geo_pnt2wkt: expected non-empty list from XPath {xpath!r} '
                f'(type={type(obj).__qualname__!r})'
            )
        first = obj[0]
        if not isinstance(first, etree._Element):
            raise TypeError(
                f'geo_pnt2wkt: expected etree._Element from XPath {xpath!r} '
                f'(type={type(first).__qualname__!r})'
            )
        text = first.text
        if not text:
            raise ValueError(
                f'geo_pnt2wkt: empty etree._Element.text from XPath {xpath!r}'
            )
        return text

    coordinates: list[str] = []
    for pnt in a if isinstance(a, list) else (a,):
        lat = get_text(pnt, "*[local-name()='LATITUDE']")
        lng = get_text(pnt, "*[local-name()='LONGITUDE']")
        coordinates.append(f'{lat},{lng}')
    logging.debug('geo_pnt2wkt calling WKT with %d coordinates', len(coordinates))
    return _wkt(context, ' '.join(coordinates))


def _map(_, a: 'etree._XPathObject', json_string: str) -> Any:
    """Lookup value in JSON mapping dictionary.

    Args:
        a: XPath object containing value to look up.
        json_string: JSON string with mapping dict, must have 'default' key.

    Returns:
        Mapped value or default if not found.

    Examples:
        >>> _map('yes', '{"true":"True","yes":"True","default":"False"}')
        'True'
        >>> _map('95.0', '{"100.0":"NOMINAL","default":"DEGRADED"}')
        'DEGRADED'
    """
    value = single_xpathobject_tostr(a)
    lookup = orjson.loads(json_string)
    result = lookup.get(value)
    is_default = result is None
    if is_default:
        result = lookup['default']
    logging.debug(
        'map(%r, json_string=%r) = %r (is_default=%r)',
        a,
        json_string,
        result,
        is_default,
    )
    return result


def _from_json(_, a: 'etree._XPathObject') -> Any:
    value = single_xpathobject_tostr(a)
    if not value:
        raise ValueError(f'from_json: empty input (type={type(a).__qualname__!r})')
    result = orjson.loads(value)
    logging.debug('from_json(...) = %r', result)
    return result


def _date_format(
    _,
    a: 'etree._XPathObject',
    fmt: str | None = None,
    date_add_delta: str | None = None,
) -> str:
    """Format date with optional delta adjustment.

    Parses ISO date, optionally adds time delta, and formats output.

    Args:
        a: XPath object containing ISO date string.
        fmt: Output format string (strftime). If None, uses isoformat().
        date_add_delta: Time delta to add, e.g. '2h13m', '1d'. Optional.

    Returns:
        Formatted date string.

    Raises:
        ValueError: If input is empty.
    """
    value = single_xpathobject_tostr(a)
    if not value:
        raise ValueError(f'date_format: empty input (type={type(a).__qualname__!r})')
    delta = _parse_timedelta(date_add_delta) if date_add_delta else timedelta()
    adjusted = datetime.fromisoformat(value) + delta
    if adjusted.tzinfo is None:
        adjusted = adjusted.replace(tzinfo=UTC)
    result = datetime.strftime(adjusted, fmt) if fmt else adjusted.isoformat()
    logging.debug(
        'date_format(%r, format=%r, date_add_delta=%r) = %r',
        value,
        fmt,
        date_add_delta,
        result,
    )
    return result


def _date_diff(
    _,
    start_dates: list[etree._Element | str] | etree._Element | str,
    end_dates: list[etree._Element | str] | etree._Element | str,
    timespec: str = 'auto',
) -> str:
    """Calculate midpoint datetime between start and end dates.

    Used for S-3 and S-5P products to compute representative datetime.

    Args:
        start_dates: XPath element(s) containing start date.
        end_dates: XPath element(s) containing end date.
        timespec: Precision for isoformat output ('auto', 'seconds', 'milliseconds').

    Returns:
        ISO format string of the midpoint datetime.
    """
    start_date = start_dates[0] if isinstance(start_dates, list) else start_dates
    if not isinstance(start_date, str):
        start_date = etree.tostring(start_date, encoding='unicode', method='text')
    end_date = end_dates[0] if isinstance(end_dates, list) else end_dates
    if not isinstance(end_date, str):
        end_date = etree.tostring(end_date, encoding='unicode', method='text')

    start_datetime = dateutil.parser.parse(start_date)
    end_datetime = dateutil.parser.parse(end_date)
    midpoint = start_datetime + (end_datetime - start_datetime) / 2
    if midpoint.tzinfo is None:
        midpoint = midpoint.replace(tzinfo=UTC)
    result = midpoint.isoformat(timespec=timespec)
    logging.debug(
        'date_diff(%r, %r, timespec=%r) = %r',
        start_dates,
        end_dates,
        timespec,
        result,
    )
    return result


_TIMEDELTA_RE = re.compile(
    r'^(?:(?P<days>[\d.]+?)d)?(?:(?P<hours>[\d.]+?)h)?(?:(?P<minutes>[\d.]+?)m)?(?:(?P<seconds>[\d.]+?)s)?$',
    re.IGNORECASE,
)


def _parse_timedelta(time_str: str) -> timedelta:
    """Parse a timedelta string into a timedelta object.

    Args:
        time_str: String like '2h13m', '1d', '30s', '2d8h5m20s'.

    Returns:
        Parsed timedelta object.

    Raises:
        ValueError: If string format is invalid.
    """
    parts = _TIMEDELTA_RE.match(time_str)
    if parts is None:
        raise ValueError(
            f'Could not parse time information from {time_str!r}. '
            "Examples of valid strings: '8h', '2d8h5m20s', '2m4s'."
        )
    time_params = {
        name: float(param) for name, param in parts.groupdict().items() if param
    }
    result = timedelta(**time_params)
    logging.debug('parse_timedelta(%r) = %r', time_str, result)
    return result


def _find_in_list(_, objects_list: etree._Element, prefix: str, key: str) -> str:
    results = ''

    for item in objects_list[0]:
        for obj in item.iter(prefix):
            for name in obj.itertext(key):
                results += f'{name},'

    return results
