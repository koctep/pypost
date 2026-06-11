"""Test configuration: set Qt offscreen platform before any Qt imports."""
import os

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    """Shared QApplication for Qt widget tests (module-scoped singleton)."""
    app = QApplication.instance() or QApplication([])
    yield app


def pytest_runtest_setup(item):
    if item.get_closest_marker("timeout") is None:
        pytest.fail(
            f"{item.nodeid}: missing pytest.mark.timeout marker "
            "(declare module/class/function timeout; see do-testing.md)",
            pytrace=False,
        )
