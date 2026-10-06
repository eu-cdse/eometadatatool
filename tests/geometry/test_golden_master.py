import math
from pathlib import Path
from typing import Any

import orjson
import pytest
from shapely import MultiPolygon, Polygon, from_wkt, is_valid

from eometadatatool.geom_utils import normalize_geometry

BBOX_ABS_TOL = 1e-6
AREA_ABS_TOL = 1e-6
AREA_REL_TOL = 1e-6

FIXTURE_DIR = Path(__file__).resolve().parents[1] / 'fixtures' / 'geometry'
INPUTS_FILE = FIXTURE_DIR / 'golden_inputs.json'
EXPECTED_FILE = FIXTURE_DIR / 'golden_expected.json'


def _load_json(path: Path) -> Any:
    return orjson.loads(path.read_bytes())


def _iter_input_cases(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    return inputs['cases']


INPUT_CASES = _iter_input_cases(_load_json(INPUTS_FILE))
EXPECTED_CASES = _load_json(EXPECTED_FILE)


def _expected_by_case_id() -> dict[str, dict[str, Any]]:
    return {case['case_id']: case for case in EXPECTED_CASES}


EXPECTED_BY_CASE_ID = _expected_by_case_id()


def test_golden_fixture_consistency() -> None:
    expected_ids = {case['case_id'] for case in EXPECTED_CASES}
    input_ids = {case['case_id'] for case in INPUT_CASES}
    assert expected_ids == input_ids

    for input_case in INPUT_CASES:
        expected_case = EXPECTED_BY_CASE_ID[input_case['case_id']]
        assert expected_case['input_wkt'] == input_case['input_wkt']


def test_full_orbit_fixture_matches_golden_case() -> None:
    # tests/geometry/test_antimeridian.py and test_polar_coverage.py drive the
    # same ring from a standalone .wkt so they stay independent of this corpus;
    # keep the two copies in step.
    case = EXPECTED_BY_CASE_ID['full_orbit_dual_pole_antimeridian']
    fixture = (FIXTURE_DIR / 'full_orbit_equator_split.wkt').read_text().strip()
    assert case['input_wkt'] == fixture


@pytest.mark.parametrize('case', INPUT_CASES, ids=[case['case_id'] for case in INPUT_CASES])
def test_normalize_geometry_golden_master(case: dict[str, str]) -> None:
    expected = EXPECTED_BY_CASE_ID[case['case_id']]
    geom = from_wkt(case['input_wkt'])
    assert isinstance(geom, Polygon | MultiPolygon)
    normalized = normalize_geometry(geom)

    assert normalized.geom_type == expected['expected_type']
    assert bool(is_valid(normalized)) is expected['expected_is_valid']

    for got, want in zip(normalized.bounds, expected['expected_bbox'], strict=True):
        assert abs(got - want) <= BBOX_ABS_TOL

    assert math.isclose(
        normalized.area,
        expected['expected_area'],
        rel_tol=AREA_REL_TOL,
        abs_tol=AREA_ABS_TOL,
    )
