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
from eometadatatool.flags import is_no_footprint_facility, is_strict
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


def _quote(_, a):
    # honestly, no idea what it does
    return [str(a[0] if len(a) == 1 else a)]


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
):
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
    """Convert "lat,lon" coordinate list into a WKT representation."""

    if not a:
        raise ValueError(f'WKT: empty input (type={type(a).__qualname__!r})')
    if input_mode not in {'latlon', 'lonlat'}:
        raise ValueError(f'WKT: invalid input_mode {input_mode!r}')

    rings: list[NDArray[np.float64]] = []  # [[[lon, lat], ...], ...]
    no_footprint_facility = is_no_footprint_facility()

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

        if no_footprint_facility:
            # auto-close polygon
            if len(ring) > 2 and not np.array_equal(ring[0], ring[-1]):
                ring = np.vstack([ring, ring[0]])

            # auto-invert polygons
            # e.g., 63.09362308322442 -180.0 63.06862740448049 -178.84616 62.085586546155874 -178.98132 62.10745979106369 -180.0 62.130700338376066 178.91764514309176 62.3844112082036 178.93430277680787 62.52698174860236 179.03267835253862 62.66976551481473 179.1335104818659 62.81243245753552 179.23507271498553 62.95543203235052 179.33535796969508 63.09806561340324 179.4377446446368 63.10568485291513 179.4432101199678 63.09362308322442 -180.0
            ring[:, 0] = np.unwrap(ring[:, 0], period=360)

            # check if the ring spans the whole world after unwrapping
            ends_diff: float = abs((ring[0, 0] - ring[-1, 0]).tolist())
            spans_whole_world = ends_diff > 1 > abs(((ends_diff + 180) % 360) - 180)
            if spans_whole_world:
                # cover the nearest hemisphere
                pole_lat = 90 if ring[0, 1] >= 0 else -90
                pole_points = np.array(
                    [
                        [ring[-1, 0], pole_lat],
                        [ring[0, 0], pole_lat],
                    ],
                    np.float64,
                )
                ring = np.vstack([ring, pole_points])

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
                f'geo_pnt2wkt: expected non-empty list from XPath {xpath!r} (type={type(obj).__qualname__!r})'
            )
        first = obj[0]
        if not isinstance(first, etree._Element):
            raise TypeError(
                f'geo_pnt2wkt: expected etree._Element from XPath {xpath!r} (type={type(first).__qualname__!r})'
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
    """
    map lookup translation.

    >>> _map('yes', '{"true":"True","yes":"True","1":"True","default":"False"}')
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
    """
    Simple date math with reformatting (e.g., for clipping and rounding)
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
    """
    Calculate datetime attribute for S-3 and S-5p products
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
    """
    Parse a timedelta string, e.g. '2h13m', into a timedelta object.
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
