from collections.abc import Collection

import pytest
import pytest_asyncio


def pytest_collection_modifyitems(
    config: pytest.Config, items: Collection[pytest.Item]
):
    # run all tests in the session in the same event loop
    # https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
    session_scope_marker = pytest.mark.asyncio(loop_scope='session')
    for item in items:
        if pytest_asyncio.is_async_test(item):
            item.add_marker(session_scope_marker, append=False)
