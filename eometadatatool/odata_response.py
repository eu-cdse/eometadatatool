import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_ODATA_CTX: ContextVar[dict[str, Any] | None] = ContextVar('odata_response')


@contextmanager
def configure_odata_response(odata: dict[str, Any] | None):
    logging.debug('Configured explicit oData response to %s', odata)
    token = _ODATA_CTX.set(odata)
    try:
        yield
    finally:
        _ODATA_CTX.reset(token)


get_odata_response = _ODATA_CTX.get
