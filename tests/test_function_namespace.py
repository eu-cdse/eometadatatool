from datetime import timedelta

import pytest

from eometadatatool.function_namespace import _parse_timedelta


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('2h13m', timedelta(hours=2, minutes=13)),
        ('8h', timedelta(hours=8)),
        ('2d8h5m20s', timedelta(days=2, hours=8, minutes=5, seconds=20)),
        ('2m4s', timedelta(minutes=2, seconds=4)),
    ],
)
def test_parse_timedelta(value: str, expected: timedelta):
    assert _parse_timedelta(value) == expected
