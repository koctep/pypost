"""Test configuration: set Qt offscreen platform before any Qt imports."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_runtest_setup(item):
    if item.get_closest_marker("timeout") is None:
        pytest.fail(
            f"{item.nodeid}: missing pytest.mark.timeout marker "
            "(declare module/class/function timeout; see do-testing.md)",
            pytrace=False,
        )
