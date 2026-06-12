"""Tests for MetricsServer startup signaling (PYPOST-153)."""
import pytest

pytestmark = pytest.mark.timeout(60)

import errno
import socket
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from pypost.core.metrics import MetricsManager
from pypost.core.server_bind import format_bind_error


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


class TestFormatBindError(unittest.TestCase):
    def test_metrics_addr_in_use_message(self):
        exc = OSError("Address already in use")
        exc.errno = 48
        message = format_bind_error(exc, "127.0.0.1", 9080, "metrics server")
        self.assertIn("9080", message)
        self.assertIn("busy", message.lower())


class TestMetricsServerStartup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_port_listening_after_start(self):
        port = _free_port()
        manager = MetricsManager()
        manager.start_server("127.0.0.1", port)
        try:
            deadline = time.time() + 10.0
            while time.time() < deadline:
                QCoreApplication.processEvents()
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                        return
                except OSError:
                    time.sleep(0.05)
            self.fail("Metrics server did not listen on port")
        finally:
            manager.stop_server()

    @patch("uvicorn.Server.serve", side_effect=OSError(errno.EADDRINUSE, "Address already in use"))
    def test_port_busy_emits_start_failed(self, mock_serve):
        port = _free_port()
        failures: list[str] = []
        manager = MetricsManager()
        manager.connect_start_failed(failures.append)
        try:
            manager.start_server("127.0.0.1", port)
            deadline = time.time() + 10.0
            while time.time() < deadline and not failures:
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertEqual(len(failures), 1)
            self.assertIn(str(port), failures[0])
        finally:
            manager.stop_server()

    @patch("uvicorn.Server.serve", side_effect=OSError(errno.EADDRINUSE, "Address already in use"))
    def test_pending_failure_delivered_when_handler_connected_late(self, mock_serve):
        port = _free_port()
        manager = MetricsManager()
        try:
            manager.start_server("127.0.0.1", port)
            deadline = time.time() + 10.0
            while time.time() < deadline and manager._pending_start_failure is None:
                QCoreApplication.processEvents()
                time.sleep(0.05)
            self.assertIsNotNone(manager._pending_start_failure)
            failures: list[str] = []
            manager.connect_start_failed(failures.append)
            self.assertEqual(len(failures), 1)
            self.assertIn(str(port), failures[0])
        finally:
            manager.stop_server()


if __name__ == "__main__":
    unittest.main()
