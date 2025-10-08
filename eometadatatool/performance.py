import logging
from contextlib import contextmanager
from functools import wraps
from time import perf_counter

from pyinstrument import Profiler


@contextmanager
def logtime(name: str):
    """Log the time taken by the given block of code.

    :param name: Identifying name to be printed in the log.
    """
    ts = perf_counter()
    yield
    te = perf_counter()
    logging.debug('%s took %.3f seconds', name, te - ts)


def logtime_decorator(func):
    """Decorator to log the time taken by the given function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with logtime(func.__name__):
            return func(*args, **kwargs)

    return wrapper


@contextmanager
def profile(filename: str):
    """Profile the application and write the report to the given HTML file.

    :param filename: Path to the HTML file.
    """
    prof = Profiler()
    prof.start()
    logging.debug('Started profiling application')
    yield
    prof.stop()
    prof.write_html(filename)
    logging.info('Saved profiling report to %r', filename)
