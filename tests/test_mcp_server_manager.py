"""Tests for MCPServerManager startup signaling (PYPOST-556)."""
import pytest

pytestmark = pytest.mark.timeout(60)

import socket
import time
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from pypost.core.mcp_server import MCPServerManager, format_mcp_bind_error
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
        manager._impl.request_service = MagicMock()
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

    def test_port_busy_emits_start_failed(self):
        port = _free_port()
        blocker = _occupy_port(port)
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
            blocker.close()
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
        manager._impl.request_service = MagicMock()
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
        manager._impl.request_service = MagicMock()
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


if __name__ == "__main__":
    unittest.main()
