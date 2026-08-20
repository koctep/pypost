"""Unit tests for MetricsServer /metrics HTTP and MCP resource metrics (PYPOST-177)."""

import pytest

import asyncio
import socket
import time
import unittest
from unittest.mock import patch

from prometheus_client import generate_latest
from starlette.testclient import TestClient

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer

pytestmark = pytest.mark.timeout(30)


def _scrape(registry: MetricsRegistry) -> str:
    return generate_latest(registry.registry).decode("utf-8")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_listening(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"server did not listen on {host}:{port}")


class TestMetricsServerHttpEndpoint(unittest.TestCase):
    def test_metrics_endpoint_returns_prometheus_text(self):
        registry = MetricsRegistry()
        registry.track_gui_send_click()
        server = MetricsServer(registry)
        client = TestClient(server._create_app())

        response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.headers.get("content-type", ""))
        self.assertIn("gui_send_clicks_total 1.0", response.text)

    def test_metrics_endpoint_reflects_mcp_counters(self):
        registry = MetricsRegistry()
        registry.track_mcp_request_received("read_resource:metrics")
        registry.track_mcp_response_sent("read_resource:metrics", "success")
        server = MetricsServer(registry)
        client = TestClient(server._create_app())

        response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 1.0',
            response.text,
        )
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            response.text,
        )


class TestMetricsServerLifecycle(unittest.TestCase):
    def test_start_server_restarts_when_thread_alive(self):
        """RLock allows stop_server while start_server holds the lock (PYPOST-590)."""
        registry = MetricsRegistry()
        server = MetricsServer(registry)
        port1 = _free_port()
        port2 = _free_port()
        server.start_server("127.0.0.1", port1)
        try:
            _wait_listening("127.0.0.1", port1)
            server.start_server("127.0.0.1", port2)
            _wait_listening("127.0.0.1", port2)
        finally:
            server.stop_server()


class TestMetricsServerMcpResourceCounters(unittest.TestCase):
    def test_read_resource_success_increments_mcp_counters(self):
        registry = MetricsRegistry()
        server = MetricsServer(registry)

        async def _run():
            contents = await server.read_resource("metrics://all")
            self.assertEqual(len(contents), 1)
            self.assertIn("gui_send_clicks_total", contents[0].text)

        asyncio.run(_run())
        out = _scrape(registry)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 1.0',
            out,
        )
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            out,
        )

    def test_read_resource_unknown_uri_raises_without_counters(self):
        registry = MetricsRegistry()
        server = MetricsServer(registry)

        async def _run():
            with self.assertRaises(ValueError):
                await server.read_resource("metrics://missing")

        asyncio.run(_run())
        out = _scrape(registry)
        self.assertNotRegex(out, r"mcp_requests_received_total\{")
        self.assertNotRegex(out, r"mcp_responses_sent_total\{")

    def test_read_resource_scrape_failure_increments_error_counter(self):
        registry = MetricsRegistry()
        server = MetricsServer(registry)

        async def _run():
            with patch(
                "pypost.core.metrics_server.generate_latest",
                side_effect=RuntimeError("scrape failed"),
            ):
                with self.assertRaises(RuntimeError):
                    await server.read_resource("metrics://all")

        asyncio.run(_run())
        out = _scrape(registry)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 1.0',
            out,
        )
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="error"} 1.0',
            out,
        )


if __name__ == "__main__":
    unittest.main()
