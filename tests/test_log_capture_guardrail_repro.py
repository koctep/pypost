"""Automated failing repro tests for log capture guardrails (PYPOST-1081).

Demonstrates that starting embedded uvicorn servers (MetricsServer, MCPServerManager,
AgentAppSession) closes active logging.FileHandler instances (including pytest's
--log-file handler) because uvicorn.Config reconfigures process-wide logging via dictConfig.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.models.models import RequestData
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.helpers.qt_wait import wait_until

pytestmark = pytest.mark.timeout(60)


@pytest.fixture
def active_file_handler(tmp_path: Path) -> Generator[tuple[logging.FileHandler, Path], None, None]:
    """Attach a standard logging.FileHandler to the root logger and ensure clean teardown."""
    log_file = tmp_path / "test_captured.log"
    handler = logging.FileHandler(str(log_file), mode="w", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        yield handler, log_file
    finally:
        root_logger.removeHandler(handler)
        if handler.stream is not None and not handler.stream.closed:
            handler.close()


def test_metrics_server_start_preserves_logging_file_handlers(
    active_file_handler: tuple[logging.FileHandler, Path],
) -> None:
    """MetricsServer start must not close active FileHandlers or discard emitted logs."""
    handler, log_file = active_file_handler
    port = free_port()
    registry = MetricsRegistry()
    server = MetricsServer(registry)

    logging.getLogger("test.guardrail").warning("guardrail_metrics_before_start")
    handler.flush()
    assert "guardrail_metrics_before_start" in log_file.read_text(encoding="utf-8")
    assert handler.stream is not None
    assert not handler.stream.closed

    server.start_server("127.0.0.1", port)
    try:
        wait_for_port("127.0.0.1", port, timeout=10.0)

        logging.getLogger("test.guardrail").error("guardrail_metrics_after_start")

        # Intended failure on unpatched code:
        # uvicorn.Config() invokes dictConfig(), which runs logging.shutdown()
        # and closes handler (handler.stream is set to None).
        assert handler.stream is not None, (
            "FileHandler stream was closed/nulled by MetricsServer uvicorn initialization"
        )
        assert not handler.stream.closed, (
            "FileHandler underlying stream was closed by MetricsServer uvicorn initialization"
        )

        handler.flush()
        content = log_file.read_text(encoding="utf-8")
        assert "guardrail_metrics_after_start" in content, (
            "Log emitted after MetricsServer startup was not written to active FileHandler"
        )
    finally:
        server.stop_server()


def test_mcp_server_manager_start_preserves_logging_file_handlers(
    qapp: QApplication,
    active_file_handler: tuple[logging.FileHandler, Path],
) -> None:
    """MCPServerManager start must not close active FileHandlers or discard emitted logs."""
    handler, log_file = active_file_handler
    port = free_port()
    tool = RequestData(name="Ping", expose_as_mcp=True, method="GET", url="http://127.0.0.1")
    manager = MCPServerManager()

    logging.getLogger("test.guardrail").warning("guardrail_mcp_before_start")
    handler.flush()
    assert "guardrail_mcp_before_start" in log_file.read_text(encoding="utf-8")
    assert handler.stream is not None
    assert not handler.stream.closed

    statuses: list[bool] = []
    manager.status_changed.connect(statuses.append)
    manager.start_server(port, [tool], host="127.0.0.1")
    try:
        wait_until(
            lambda: bool(statuses) and statuses[-1] is True,
            message="MCP server did not emit running status",
        )
        wait_for_port("127.0.0.1", port, timeout=10.0)

        logging.getLogger("test.guardrail").error("guardrail_mcp_after_start")

        # Intended failure on unpatched code:
        # uvicorn.Config() invokes dictConfig(), which runs logging.shutdown()
        # and closes handler (handler.stream is set to None).
        assert handler.stream is not None, (
            "FileHandler stream was closed/nulled by MCPServerManager uvicorn initialization"
        )
        assert not handler.stream.closed, (
            "FileHandler underlying stream was closed by MCPServerManager uvicorn initialization"
        )

        handler.flush()
        content = log_file.read_text(encoding="utf-8")
        assert "guardrail_mcp_after_start" in content, (
            "Log emitted after MCPServerManager startup was not written to active FileHandler"
        )
    finally:
        manager.stop_server()


def test_agent_app_session_preserves_file_logging_and_captures_errors(
    qapp: QApplication,
    active_file_handler: tuple[logging.FileHandler, Path],
) -> None:
    """AgentAppSession launch must preserve active FileHandlers so subsequent error logs are
    captured.
    """
    handler, log_file = active_file_handler

    logging.getLogger("test.guardrail").warning("guardrail_session_before_launch")
    handler.flush()
    assert "guardrail_session_before_launch" in log_file.read_text(encoding="utf-8")

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
        assert session.window.is_ui_ready is True

        logging.getLogger("test.guardrail").error("guardrail_session_during_lifecycle")

    logging.getLogger("test.guardrail").error("guardrail_session_after_shutdown")

    assert handler.stream is not None, (
        "FileHandler stream was closed/nulled during AgentAppSession lifecycle"
    )
    assert not handler.stream.closed, (
        "FileHandler underlying stream was closed during AgentAppSession lifecycle"
    )

    handler.flush()
    content = log_file.read_text(encoding="utf-8")
    assert "guardrail_session_during_lifecycle" in content, (
        "Log emitted during session lifecycle was not captured in FileHandler"
    )
    assert "guardrail_session_after_shutdown" in content, (
        "Log emitted after session shutdown was not captured in FileHandler"
    )
