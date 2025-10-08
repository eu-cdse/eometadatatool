import datetime
from collections.abc import Iterator, Mapping
from typing import Any, Final

from dateutil import parser


class _EmptyDict[K, V](Mapping[K, V]):
    def __getitem__(self, key: K) -> V:
        raise KeyError(key)

    def __iter__(self) -> Iterator[K]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __hash__(self) -> int:
        return 0


EMPTY_MAPPING: Final[Mapping[str, Any]] = _EmptyDict()


def ensure_iso_datetime(value: str | datetime.datetime) -> str | None:
    if isinstance(value, str):
        return parser.isoparse(value).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return None
