"""Tests for HTTPClient SSE probe (PYPOST-39)."""
import unittest
from unittest.mock import MagicMock, patch

from pypost.core.http_client import HTTPClient
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData


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
        self.metrics_patcher = patch(
            "pypost.core.http_client.MetricsManager",
            return_value=MagicMock(),
        )
        self.metrics_patcher.start()
        self.client = HTTPClient(template_service=TemplateService())

    def tearDown(self):
        self.metrics_patcher.stop()

    def test_auto_detects_sse_and_handles_read_timeout(self):
        """When server sends 200 but no events (waits for client), return success."""
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

        self.assertEqual(result.status_code, 200)
        self.assertIn("Connection established", result.body)
        self.assertIn("InitializeRequest", result.body)

    def test_auto_detects_sse_by_url_and_content_type(self):
        """When GET to /sse URL, use SSE handling (URL or Content-Type)."""
        client = self.client
        req = RequestData(method="GET", url="http://localhost:9080/sse")
        mock_response = _make_sse_response([("endpoint", "http://localhost:9080")])

        with patch.object(client.session, "request", return_value=mock_response) as m:
            result = client.send_request(req)
            call_kw = m.call_args[1]
            self.assertEqual(call_kw["timeout"], (3.0, 10.0))
            self.assertIn("text/event-stream", call_kw["headers"]["Accept"])

        self.assertEqual(result.status_code, 200)
        self.assertIn("SSE stream opened", result.body)
        self.assertIn("1 event(s)", result.body)

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

        self.assertEqual(result.status_code, 404)
        self.assertIn("Not Found", result.body)
