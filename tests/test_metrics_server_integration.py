"""Integration tests: live MetricsManager uvicorn HTTP and MCP (PYPOST-169, PYPOST-563)."""

import pytest

pytestmark = pytest.mark.timeout(120)

import socket
import time
import unittest
import urllib.error
import urllib.request

import anyio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.metrics import MetricsManager


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"Metrics server did not listen on {host}:{port} within {timeout}s")


def _fetch_metrics_http(
    host: str, port: int, path: str = "/metrics"
) -> tuple[int, dict[str, str], str]:
    url = f"http://{host}:{port}{path}"
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=5.0) as response:
        body = response.read().decode("utf-8")
        headers = {key.lower(): value for key, value in response.headers.items()}
        return response.status, headers, body


async def _read_metrics_over_streamable_http(mcp_url: str) -> str:
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.read_resource("metrics://all")
                return result.contents[0].text


async def _read_metrics_over_sse(sse_url: str) -> str:
    async with sse_client(sse_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.read_resource("metrics://all")
            return result.contents[0].text


class TestMetricsServerHttpIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._host = "127.0.0.1"
        self._port = _free_port()
        self._metrics = MetricsManager()
        self._metrics.start_server(self._host, self._port)
        _wait_for_port(self._host, self._port)

    def tearDown(self) -> None:
        self._metrics.stop_server()

    def test_metrics_http_serves_prometheus_text_after_start(self):
        status, headers, body = _fetch_metrics_http(self._host, self._port)

        self.assertEqual(status, 200)
        self.assertIn("text/plain", headers.get("content-type", ""))
        self.assertIn("requests_sent_total", body)

    def test_metrics_http_reflects_tracked_counters(self):
        self._metrics.track_gui_send_click()

        status, _, body = _fetch_metrics_http(self._host, self._port)

        self.assertEqual(status, 200)
        self.assertIn("gui_send_clicks_total 1.0", body)


class TestMetricsServerMcpIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self._host = "127.0.0.1"
        self._port = _free_port()
        self._metrics = MetricsManager()
        self._metrics.start_server(self._host, self._port)
        _wait_for_port(self._host, self._port)

    def tearDown(self) -> None:
        self._metrics.stop_server()

    def _assert_mcp_resource_counters(self, registry) -> None:
        from prometheus_client import generate_latest

        payload = generate_latest(registry).decode("utf-8")
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 1.0',
            payload,
        )
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            payload,
        )

    def test_read_metrics_resource_over_live_streamable_http(self):
        mcp_url = f"http://{self._host}:{self._port}/mcp"
        payload = anyio.run(_read_metrics_over_streamable_http, mcp_url)
        self.assertIn("requests_sent_total", payload)
        self._assert_mcp_resource_counters(self._metrics.registry)

    def test_read_metrics_resource_over_live_sse(self):
        sse_url = f"http://{self._host}:{self._port}/sse"
        payload = anyio.run(_read_metrics_over_sse, sse_url)
        self.assertIn("requests_sent_total", payload)
        self._assert_mcp_resource_counters(self._metrics.registry)


if __name__ == "__main__":
    unittest.main()
