import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import NamedTuple


class _Flags(NamedTuple):
    odata_endpoint: str = 'https://datahub.creodias.eu/odata/v1'
    strict: bool = False
    no_footprint_facility: bool = False


_CTX: ContextVar[_Flags] = ContextVar(f'{__file__}.Flags', default=_Flags())  # noqa: B039


@contextmanager
def configure_flags(
    *,
    odata_endpoint: str = 'https://datahub.creodias.eu/odata/v1',
    strict: bool = False,
    no_footprint_facility: bool = False,
):
    flags = _Flags(
        odata_endpoint=odata_endpoint,
        strict=strict,
        no_footprint_facility=no_footprint_facility,
    )
    logging.debug('Configured runtime flags to %r', flags)
    token = _CTX.set(flags)
    try:
        yield
    finally:
        _CTX.reset(token)


def is_strict() -> bool:
    return _CTX.get().strict


def is_no_footprint_facility() -> bool:
    return _CTX.get().no_footprint_facility


def get_odata_endpoint() -> str:
    return _CTX.get().odata_endpoint
