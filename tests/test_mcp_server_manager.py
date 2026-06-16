"""Tests for MCPServerManager startup signaling (PYPOST-556, PYPOST-719, PYPOST-726, PYPOST-727)."""
import asyncio
import errno
import logging
import socket
import warnings
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server import MCPServerManager, format_mcp_bind_error
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.helpers.qt_wait import wait_until

pytestmark = pytest.mark.timeout(60)


def test_format_mcp_bind_error_addr_in_use():
    exc = OSError("Address already in use")
    exc.errno = 48
    message = format_mcp_bind_error(exc, "127.0.0.1", 1080)
    assert "1080" in message
    assert "busy" in message.lower()


def test_status_true_when_port_is_listening(qapp):
    port = free_port()
    tool = RequestData(name="Ping", expose_as_mcp=True, method="GET", url="http://x")
    manager = MCPServerManager()
    statuses: list[bool] = []
    manager.status_changed.connect(statuses.append)
    manager.start_server(port, [tool], host="127.0.0.1")
    try:
        wait_until(
            lambda: bool(statuses) and statuses[-1] is True,
            message="MCP server did not emit running status",
        )
        wait_for_port("127.0.0.1", port)
    finally:
        manager.stop_server()


@patch("uvicorn.Server.serve", side_effect=OSError(errno.EADDRINUSE, "Address already in use"))
def test_port_busy_emits_start_failed(mock_serve, qapp):
    port = free_port()
    failures: list[str] = []
    statuses: list[bool] = []
    manager = MCPServerManager()
    manager.start_failed.connect(failures.append)
    manager.status_changed.connect(statuses.append)
    try:
        manager.start_server(port, [], host="127.0.0.1")
        wait_until(lambda: bool(failures), message="start_failed was not emitted")
        assert len(failures) == 1
        assert str(port) in failures[0]
        assert statuses
        assert statuses[-1] is False
    finally:
        manager.stop_server()


def test_stop_emits_false(qapp):
    port = free_port()
    manager = MCPServerManager()
    statuses: list[bool] = []
    manager.status_changed.connect(statuses.append)
    manager.start_server(port, [], host="127.0.0.1")
    wait_until(lambda: bool(statuses), message="MCP server did not emit initial status")
    manager.stop_server()
    assert statuses
    assert statuses[-1] is False


def test_set_variable_supplier_forwards_to_impl():
    manager = MCPServerManager()
    supplier = lambda: {"token": "abc"}

    manager.set_variable_supplier(supplier)

    assert manager._impl._variable_supplier is supplier
    assert manager._impl._variable_supplier() == {"token": "abc"}


def test_update_tools_restarts_when_exposed_set_changes(qapp):
    port = free_port()
    tool_a = RequestData(
        name="A", id="a", expose_as_mcp=True, method="GET", url="http://a"
    )
    tool_b = RequestData(
        name="B", id="b", expose_as_mcp=True, method="GET", url="http://b"
    )
    manager = MCPServerManager()
    manager.start_server(port, [tool_a], host="127.0.0.1")
    try:
        wait_until(lambda: manager.is_running(), message="MCP server did not start")
        assert manager.update_tools([tool_a, tool_b])
        wait_until(
            lambda: manager.is_running(),
            message="MCP server did not restart after tool update",
        )
    finally:
        manager.stop_server()


def test_update_tools_noop_when_signature_unchanged(qapp):
    port = free_port()
    tool = RequestData(
        name="Ping", expose_as_mcp=True, method="GET", url="http://x"
    )
    manager = MCPServerManager()
    manager.start_server(port, [tool], host="127.0.0.1")
    try:
        wait_until(lambda: manager.is_running(), message="MCP server did not start")
        assert manager.update_tools([tool]) is False
    finally:
        manager.stop_server()


def test_update_tools_noop_when_server_stopped():
    tool = RequestData(
        name="Ping", expose_as_mcp=True, method="GET", url="http://x"
    )
    manager = MCPServerManager()
    assert manager.update_tools([tool]) is False


def test_activity_log_property_returns_same_instance():
    manager = MCPServerManager()
    log = manager.activity_log
    assert manager.activity_log is log


def test_emit_activity_emits_activity_recorded_signal():
    manager = MCPServerManager()
    received = []
    manager.activity_recorded.connect(received.append)
    entry = McpActivityEntry.new_list_tools(tool_count=2)
    manager._emit_activity(entry)
    assert received == [entry]


def test_set_hidden_keys_supplier_forwards_to_impl():
    manager = MCPServerManager()
    supplier = lambda: {"secret", "token"}
    manager.set_hidden_keys_supplier(supplier)
    assert manager._impl._hidden_keys_supplier is supplier


def test_init_with_template_service_logs_debug(caplog):
    ts = MagicMock(spec=TemplateService)
    with caplog.at_level(logging.DEBUG, logger="pypost.core.mcp_server"):
        MCPServerManager(template_service=ts)
    assert any("propagating TemplateService" in m for m in caplog.messages)


def test_generic_exception_in_run_uvicorn_emits_start_failed():
    manager = MCPServerManager()
    failures: list[str] = []
    statuses: list[bool] = []
    manager.start_failed.connect(failures.append)
    manager.status_changed.connect(statuses.append)

    with patch.object(manager._impl, "create_app", side_effect=RuntimeError("kaboom")):
        manager._current_port = 0
        manager._current_host = "127.0.0.1"
        manager._startup_notified = False
        manager._stop_event.clear()
        manager._run_uvicorn()

    assert len(failures) == 1
    assert "kaboom" in failures[0]
    assert statuses[-1] is False


def test_start_server_stops_existing_server_when_already_running():
    manager = MCPServerManager()
    with (
        patch.object(manager, "is_running", return_value=True),
        patch.object(manager, "stop_server") as mock_stop,
        patch.object(manager, "_server_thread", create=True, new=None),
        patch("threading.Thread"),
    ):
        manager.start_server(9999, [], host="127.0.0.1")
    mock_stop.assert_called_once()


def test_unexpected_server_exit_emits_false_and_warns(caplog):
    manager = MCPServerManager()
    statuses: list[bool] = []
    manager.status_changed.connect(statuses.append)

    async def serve_noop(self_server):
        return

    with (
        patch.object(manager._impl, "create_app", return_value=MagicMock()),
        patch("uvicorn.Server.serve", serve_noop),
        caplog.at_level(logging.WARNING, logger="pypost.core.mcp_server"),
    ):
        manager._current_port = 0
        manager._current_host = "127.0.0.1"
        manager._startup_notified = True
        manager._stop_event.clear()
        manager._run_uvicorn()

    assert any("unexpected_exit" in m for m in caplog.messages)
    assert statuses[-1] is False


def test_run_uvicorn_drains_pending_task_without_destroyed_warning():
    """Regression test for PYPOST-726.

    Mirrors an sse_starlette-style watcher task still pending on the loop
    when uvicorn's serve() returns. Without draining, asyncio would log
    "Task was destroyed but it is pending!" once the orphaned Task is
    garbage-collected after loop.close().
    """
    manager = MCPServerManager()
    leftover_tasks: list[asyncio.Task] = []

    async def serve_leaves_pending_task(self_server):
        task = asyncio.get_event_loop().create_task(asyncio.sleep(100))
        leftover_tasks.append(task)
        await asyncio.sleep(0)

    with (
        patch.object(manager._impl, "create_app", return_value=MagicMock()),
        patch("uvicorn.Server.serve", serve_leaves_pending_task),
    ):
        manager._current_port = 0
        manager._current_host = "127.0.0.1"
        manager._startup_notified = True
        manager._stop_event.set()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            manager._run_uvicorn()
            leftover_tasks.clear()
            import gc

            gc.collect()

    messages = [str(w.message) for w in caught]
    assert not any("was destroyed but it is pending" in m for m in messages)
