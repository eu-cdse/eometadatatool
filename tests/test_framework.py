"""Unit tests for stac framework helpers.

Covers pure utilities and edge-case branches not exercised by the
template integration tests in test_template_output.py.
"""
import pytest

from eometadatatool.stac.framework.stac_asset import (
    has_meaningful_scale_or_offset,
    sanitize_nodata,
)
from eometadatatool.stac.framework.stac_bands import OLCI_Bands, generate_bands
from eometadatatool.stac.framework.stac_extension import StacExtension
from eometadatatool.stac.framework.stac_item import STACItem
from eometadatatool.stac.framework.utils import generate_product_uuid


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('nan', 'nan'),
        ('NaN', 'nan'),
        ('NAN', 'nan'),
        ('foo', 'foo'),
        ('', ''),
        (42, 42),
        (3.14, 3.14),
        (None, None),
    ],
)
def test_sanitize_nodata(value, expected):
    assert sanitize_nodata(value) == expected


@pytest.mark.parametrize(
    ('data', 'expected'),
    [
        ({}, False),
        ({'raster:scale': 1, 'raster:offset': 0}, False),
        ({'raster:scale': 2}, True),
        ({'raster:offset': 0.5}, True),
        ({'raster:scale': None, 'raster:offset': None}, False),
        ({'bands': [{'raster:scale': 1}, {'raster:scale': 1.5}]}, True),
        ({'outer': {'inner': {'raster:offset': -0.1}}}, True),
        ({'unrelated': 'value', 'nested': {'other': 999}}, False),
    ],
)
def test_has_meaningful_scale_or_offset(data, expected):
    assert has_meaningful_scale_or_offset(data) is expected


@pytest.mark.parametrize(
    ('mgrs', 'expected_epsg'),
    [
        ('31UDQ', 'EPSG:32631'),
        ('33MXP', 'EPSG:32733'),
        ('01CAA', 'EPSG:32701'),
        ('60XWN', 'EPSG:32660'),
        ('1NAA', 'EPSG:32601'),
    ],
)
def test_from_mgrs_valid(mgrs, expected_epsg):
    extensions: set[StacExtension] = set()
    result = STACItem.from_mgrs(mgrs, extensions)
    assert result == {
        'grid:code': f'MGRS-{mgrs}',
        'proj:code': expected_epsg,
    }


def test_from_mgrs_adds_extensions():
    extensions: set[StacExtension] = set()
    STACItem.from_mgrs('31UDQ', extensions)
    assert StacExtension.GRID in extensions
    assert StacExtension.PROJECTION in extensions


@pytest.mark.parametrize(
    'mgrs',
    [
        'invalid',
        '',
        'ABC',
        '999UDQ',
        '31BDQ',
    ],
)
def test_from_mgrs_invalid(mgrs):
    with pytest.raises(ValueError, match='Invalid MGRS format'):
        STACItem.from_mgrs(mgrs, set())


def test_generate_bands_all():
    result = generate_bands(OLCI_Bands, None)
    assert result == list(OLCI_Bands.values())


def test_generate_bands_subset():
    result = generate_bands(OLCI_Bands, ['Oa02', 'Oa01'])
    assert result == [OLCI_Bands['Oa02'], OLCI_Bands['Oa01']]


def test_generate_bands_empty():
    assert generate_bands(OLCI_Bands, []) == []


def test_generate_bands_unknown_raises():
    with pytest.raises(KeyError):
        generate_bands(OLCI_Bands, ['NotABand'])


@pytest.mark.parametrize(
    ('identifier', 'expected'),
    [
        (
            'Copernicus_DSM_COG_10_N00_00_E006_00_DEM',
            '3be180b6-07a6-51c1-8947-5e80afdc5cf2',
        ),
        ('S2_GRI_L1C_GCP_N00E006', '3585cc02-7cca-5fa0-bc22-8e5ec188e15d'),
    ],
)
def test_generate_product_uuid_is_stable(identifier, expected):
    # Pinned values: a failure means every published product_uuid would change.
    assert generate_product_uuid(identifier) == expected
