"""Tests for HTTPClient SSE probe (PYPOST-39, PYPOST-430)."""
import pytest

import unittest
from unittest.mock import MagicMock, patch

from pypost.core.http_client import HTTPClient
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData

pytestmark = pytest.mark.timeout(60)


def _make_sse_response(events_data):
    """Build a mock Response that yields SSE-formatted chunks (bytes)."""
    chunks = []
    for event_type, data in events_data:
        chunk = f"event: {event_type}\ndata: {data}\n\n"
        chunks.append(chunk.encode("utf-8"))

    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Type": "text/event-stream"}
    response.close = MagicMock()
    # sseclient iterates over response; it expects bytes
    response.__iter__ = lambda self: iter(chunks)
    return response


class HTTPClientSSEProbeTests(unittest.TestCase):
    def setUp(self):
        self.client = HTTPClient(
            metrics=MagicMock(),
            template_service=TemplateService(),
        )

    def test_handles_sse_read_timeout_by_content_type(self):
        """When server sends 200 SSE but no events, return success."""
        import requests

        class TimeoutIterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise requests.exceptions.ReadTimeout("Read timed out")

        client = self.client
        req = RequestData(method="GET", url="http://localhost:9080/sse")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.close = MagicMock()
        mock_response.__iter__ = lambda self: TimeoutIterator()

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.send_request(req)

        self.assertEqual(result.response.status_code, 200)
        self.assertIn("Connection established", result.response.body)
        self.assertIn("InitializeRequest", result.response.body)

    def test_handles_sse_response_by_content_type(self):
        """When GET response is text/event-stream, use SSE handling."""
        client = self.client
        req = RequestData(method="GET", url="http://localhost:9080/sse")
        mock_response = _make_sse_response([("endpoint", "http://localhost:9080")])

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.send_request(req)

        self.assertEqual(result.response.status_code, 200)
        self.assertIn("SSE stream opened", result.response.body)
        self.assertIn("1 event(s)", result.response.body)

    def test_detects_sse_without_sse_substring_in_url(self):
        """Content-Type detection works for non-/sse URLs (e.g. legacy paths)."""
        client = self.client
        req = RequestData(method="GET", url="http://localhost:1080/mcp")
        mock_response = _make_sse_response([("message", "ok")])

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.send_request(req)

        self.assertIn("SSE stream opened", result.response.body)

    def test_no_false_positive_when_url_contains_sse_substring(self):
        """URL containing /sse without SSE content-type uses normal response path."""
        client = self.client
        req = RequestData(method="GET", url="http://example.com/api/sse-metrics")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.iter_content = MagicMock(
            return_value=[b'{"ok":true}'],
        )

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.send_request(req)

        self.assertEqual('{"ok":true}', result.response.body)

    def test_applies_sse_probe_timeout_when_accept_header_set(self):
        """Explicit Accept: text/event-stream uses SSE probe timeouts before send."""
        client = self.client
        req = RequestData(
            method="GET",
            url="http://localhost:9080/stream",
            headers={"Accept": "text/event-stream"},
        )
        mock_response = _make_sse_response([("endpoint", "http://localhost:9080")])

        with patch.object(client.session, "request", return_value=mock_response) as m:
            client.send_request(req)
            call_kw = m.call_args[1]
            self.assertEqual(call_kw["timeout"], (3.0, 10.0))
            self.assertIn("text/event-stream", call_kw["headers"]["Accept"])

    def test_handles_non_200_sse_response(self):
        """When SSE endpoint returns non-200, return that status."""
        client = self.client
        req = RequestData(method="GET", url="http://localhost:1080/sse")
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {"Content-Type": "text/event-stream"}
        mock_response.text = "Not Found"
        mock_response.close = MagicMock()

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.send_request(req)

        self.assertEqual(result.response.status_code, 404)
        self.assertIn("Not Found", result.response.body)
