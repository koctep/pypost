"""Tests for MCPServerManager startup signaling (PYPOST-556, PYPOST-719)."""
import pytest

pytestmark = pytest.mark.timeout(60)

import errno
import socket
import time
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server import MCPServerManager, format_mcp_bind_error
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _occupy_port(port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)
    return sock


class TestFormatMcpBindError(unittest.TestCase):
    def test_addr_in_use_message(self):
        exc = OSError("Address already in use")
        exc.errno = 48
        message = format_mcp_bind_error(exc, "127.0.0.1", 1080)
        self.assertIn("1080", message)
        self.assertIn("busy", message.lower())


class TestMCPServerManagerStartup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_status_true_when_port_is_listening(self):
        port = _free_port()
        tool = RequestData(name="Ping", expose_as_mcp=True, method="GET", url="http://x")
        manager = MCPServerManager()
        statuses: list[bool] = []
        manager.status_changed.connect(statuses.append)
        manager.start_server(port, [tool], host="127.0.0.1")
        try:
            deadline = time.time() + 10.0
            while time.time() < deadline:
                QCoreApplication.processEvents()
                if statuses and statuses[-1] is True:
                    with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                        pass
                    return
                time.sleep(0.05)
            self.fail("MCP server did not emit running status")
        finally:
            manager.stop_server()

    @patch("uvicorn.Server.serve", side_effect=OSError(errno.EADDRINUSE, "Address already in use"))
    def test_port_busy_emits_start_failed(self, mock_serve):
        port = _free_port()
        failures: list[str] = []
        statuses: list[bool] = []
        manager = MCPServerManager()
        manager.start_failed.connect(failures.append)
        manager.status_changed.connect(statuses.append)
        try:
            manager.start_server(port, [], host="127.0.0.1")
            deadline = time.time() + 10.0
            while time.time() < deadline and not failures:
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertEqual(len(failures), 1)
            self.assertIn(str(port), failures[0])
            self.assertTrue(statuses)
            self.assertFalse(statuses[-1])
        finally:
            manager.stop_server()

    def test_stop_emits_false(self):
        port = _free_port()
        manager = MCPServerManager()
        statuses: list[bool] = []
        manager.status_changed.connect(statuses.append)
        manager.start_server(port, [], host="127.0.0.1")
        deadline = time.time() + 10.0
        while time.time() < deadline and not any(statuses):
            QCoreApplication.processEvents()
            time.sleep(0.05)
        manager.stop_server()
        self.assertTrue(statuses)
        self.assertFalse(statuses[-1])

    def test_set_variable_supplier_forwards_to_impl(self):
        manager = MCPServerManager()
        supplier = lambda: {"token": "abc"}

        manager.set_variable_supplier(supplier)

        self.assertIs(manager._impl._variable_supplier, supplier)
        self.assertEqual(manager._impl._variable_supplier(), {"token": "abc"})


class TestMCPServerManagerUpdateTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_update_tools_restarts_when_exposed_set_changes(self):
        port = _free_port()
        tool_a = RequestData(
            name="A", id="a", expose_as_mcp=True, method="GET", url="http://a"
        )
        tool_b = RequestData(
            name="B", id="b", expose_as_mcp=True, method="GET", url="http://b"
        )
        manager = MCPServerManager()
        manager.start_server(port, [tool_a], host="127.0.0.1")
        try:
            deadline = time.time() + 10.0
            while time.time() < deadline and not manager.is_running():
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertTrue(manager.update_tools([tool_a, tool_b]))
            deadline = time.time() + 10.0
            while time.time() < deadline and not manager.is_running():
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertTrue(manager.is_running())
        finally:
            manager.stop_server()

    def test_update_tools_noop_when_signature_unchanged(self):
        port = _free_port()
        tool = RequestData(
            name="Ping", expose_as_mcp=True, method="GET", url="http://x"
        )
        manager = MCPServerManager()
        manager.start_server(port, [tool], host="127.0.0.1")
        try:
            deadline = time.time() + 10.0
            while time.time() < deadline and not manager.is_running():
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertFalse(manager.update_tools([tool]))
        finally:
            manager.stop_server()

    def test_update_tools_noop_when_server_stopped(self):
        tool = RequestData(
            name="Ping", expose_as_mcp=True, method="GET", url="http://x"
        )
        manager = MCPServerManager()
        self.assertFalse(manager.update_tools([tool]))


class TestMCPServerManagerUnit(unittest.TestCase):
    """Pure unit tests — no real server, no ports, no threads blocked (PYPOST-719)."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_activity_log_property_returns_same_instance(self):
        manager = MCPServerManager()
        log = manager.activity_log
        self.assertIs(manager.activity_log, log)

    def test_emit_activity_emits_activity_recorded_signal(self):
        manager = MCPServerManager()
        received = []
        manager.activity_recorded.connect(received.append)
        entry = McpActivityEntry.new_list_tools(tool_count=2)
        manager._emit_activity(entry)
        self.assertEqual(received, [entry])

    def test_set_hidden_keys_supplier_forwards_to_impl(self):
        manager = MCPServerManager()
        supplier = lambda: {"secret", "token"}
        manager.set_hidden_keys_supplier(supplier)
        self.assertIs(manager._impl._hidden_keys_supplier, supplier)

    def test_init_with_template_service_logs_debug(self):
        ts = MagicMock(spec=TemplateService)
        with self.assertLogs("pypost.core.mcp_server", level="DEBUG") as cm:
            MCPServerManager(template_service=ts)
        self.assertTrue(any("propagating TemplateService" in m for m in cm.output))

    def test_generic_exception_in_run_uvicorn_emits_start_failed(self):
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

        self.assertEqual(len(failures), 1)
        self.assertIn("kaboom", failures[0])
        self.assertFalse(statuses[-1])

    def test_start_server_stops_existing_server_when_already_running(self):
        manager = MCPServerManager()
        with (
            patch.object(manager, "is_running", return_value=True),
            patch.object(manager, "stop_server") as mock_stop,
            patch.object(manager, "_server_thread", create=True, new=None),
            patch("threading.Thread"),
        ):
            manager.start_server(9999, [], host="127.0.0.1")
        mock_stop.assert_called_once()

    def test_unexpected_server_exit_emits_false_and_warns(self):
        manager = MCPServerManager()
        statuses: list[bool] = []
        manager.status_changed.connect(statuses.append)

        async def serve_noop(self_server):
            return  # server exits without stop_event being set

        with (
            patch.object(manager._impl, "create_app", return_value=MagicMock()),
            patch("uvicorn.Server.serve", serve_noop),
        ):
            manager._current_port = 0
            manager._current_host = "127.0.0.1"
            manager._startup_notified = True  # startup already signalled
            manager._stop_event.clear()
            with self.assertLogs("pypost.core.mcp_server", level="WARNING") as cm:
                manager._run_uvicorn()

        self.assertTrue(any("unexpected_exit" in m for m in cm.output))
        self.assertFalse(statuses[-1])


if __name__ == "__main__":
    unittest.main()
