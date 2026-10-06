import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import NamedTuple


class _Flags(NamedTuple):
    odata_endpoint: str = 'https://datahub.creodias.eu/odata/v1'
    strict: bool = False
    no_private: bool = False
    hidden: bool = False
    extended_private_data: bool = False


_CTX: ContextVar[_Flags] = ContextVar(f'{__file__}.Flags', default=_Flags())  # noqa: B039


@contextmanager
def configure_flags(
    *,
    odata_endpoint: str = 'https://datahub.creodias.eu/odata/v1',
    strict: bool = False,
    no_private: bool = False,
    hidden: bool = False,
    extended_private_data: bool = False,
):
    flags = _Flags(
        odata_endpoint=odata_endpoint,
        strict=strict,
        no_private=no_private,
        hidden=hidden,
        extended_private_data=extended_private_data,
    )
    logging.debug('Configured runtime flags to %r', flags)
    token = _CTX.set(flags)
    try:
        yield
    finally:
        _CTX.reset(token)


def get_flags() -> _Flags:
    return _CTX.get()


def is_strict() -> bool:
    return _CTX.get().strict


def get_odata_endpoint() -> str:
    return _CTX.get().odata_endpoint


def is_no_private() -> bool:
    return _CTX.get().no_private


def is_hidden() -> bool:
    return _CTX.get().hidden


def is_extended_private_data() -> bool:
    return _CTX.get().extended_private_data
