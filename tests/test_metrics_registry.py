"""Unit tests for MetricsRegistry MCP counter tracking (PYPOST-177)."""

import pytest

pytestmark = pytest.mark.timeout(30)

import unittest

from prometheus_client import generate_latest

from pypost.core.metrics_registry import MetricsRegistry


def _scrape(registry: MetricsRegistry) -> str:
    return generate_latest(registry.registry).decode("utf-8")


class TestMetricsRegistryMcpCounters(unittest.TestCase):
    def test_track_mcp_request_received(self):
        reg = MetricsRegistry()
        reg.track_mcp_request_received("read_resource:metrics")
        reg.track_mcp_request_received("read_resource:metrics")
        out = _scrape(reg)
        self.assertIn(
            'mcp_requests_received_total{method="read_resource:metrics"} 2.0',
            out,
        )

    def test_track_mcp_response_sent_success(self):
        reg = MetricsRegistry()
        reg.track_mcp_response_sent("read_resource:metrics", "success")
        out = _scrape(reg)
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="success"} 1.0',
            out,
        )

    def test_track_mcp_response_sent_error(self):
        reg = MetricsRegistry()
        reg.track_mcp_response_sent("read_resource:metrics", "error")
        out = _scrape(reg)
        self.assertIn(
            'mcp_responses_sent_total{method="read_resource:metrics",status="error"} 1.0',
            out,
        )


if __name__ == "__main__":
    unittest.main()
