"""Test configuration: set Qt offscreen platform before any Qt imports."""
import logging
import os
import sys

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    """Shared QApplication for Qt widget tests (module-scoped singleton)."""
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(scope="session")
def mcp_collection_live_server():
    """Session-scoped MCP server for the committed test collection (PYPOST-593)."""
    from tests.helpers.mcp_live_server import LiveMCPServer
    from tests.helpers.mcp_test_collection import mcp_exposed_requests

    server = LiveMCPServer(mcp_exposed_requests())
    server.start()
    yield server
    server.stop()


def pytest_runtest_setup(item):
    if item.get_closest_marker("timeout") is None:
        pytest.fail(
            f"{item.nodeid}: missing pytest.mark.timeout marker "
            "(declare module/class/function timeout; see do-testing.md)",
            pytrace=False,
        )


def pytest_addoption(parser):
    """Register custom ini option for empty tests policy."""
    parser.addini(
        "empty_tests_policy",
        help="Policy for pytest exit code 5 (no tests collected): 'fail' or 'warn'",
        default="fail",
    )


def pytest_sessionfinish(session, exitstatus):
    """Intercept exit status 5 (no tests collected) and handle per empty_tests_policy."""
    if exitstatus == 5:
        try:
            policy = session.config.getini("empty_tests_policy")
        except (AttributeError, ValueError):
            policy = "fail"

        if policy in ("warn", "warning", "ignore_and_warn"):
            session.exitstatus = 0
            msg = (
                "WARNING: pytest exit code 5 (no tests collected) "
                "intercepted and rewritten to 0 per empty_tests_policy=warn"
            )
            sys.stderr.write(f"\n{msg}\n")
            sys.stderr.flush()

            logger = logging.getLogger("pytest")
            logger.warning(msg)

