import unittest
from unittest.mock import MagicMock
import requests as requests_lib

from pypost.core.http_client import HTTPClient
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from pypost.models.errors import ErrorCategory, ExecutionError


def _make_response(status=200, headers=None, chunks=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = {"Content-Type": "application/json", **(headers or {})}
    resp.iter_content.return_value = iter(chunks or [b"body"])
    resp.close.return_value = None
    return resp


class TestHTTPClientSendRequest(unittest.TestCase):
    def setUp(self):
        self.client = HTTPClient(metrics=MagicMock(), template_service=TemplateService())
        self.mock_session = MagicMock()
        self.client.session = self.mock_session

    def test_get_200_returns_response_data_with_correct_fields(self):
        self.mock_session.request.return_value = _make_response(
            status=200, chunks=[b'{"ok":true}']
        )
        req = RequestData(method="GET", url="http://x")
        result = self.client.send_request(req)
        self.assertEqual(200, result.status_code)
        self.assertEqual('{"ok":true}', result.body)
        self.assertGreater(result.elapsed_time, 0)

    def test_post_with_json_body_serialises_body_correctly(self):
        self.mock_session.request.return_value = _make_response(status=200)
        req = RequestData(method="POST", url="http://x", body='{"k":"v"}', body_type="json")
        self.client.send_request(req)
        call_kwargs = self.mock_session.request.call_args[1]
        self.assertEqual({"k": "v"}, call_kwargs.get("json"))
        self.assertNotIn("data", call_kwargs)

    def test_template_variables_substituted_in_url(self):
        self.mock_session.request.return_value = _make_response(status=200)
        req = RequestData(method="GET", url="{{ base }}/api")
        self.client.send_request(req, variables={"base": "http://host"})
        call_kwargs = self.mock_session.request.call_args[1]
        self.assertEqual("http://host/api", call_kwargs["url"])

    def test_template_variables_substituted_in_headers(self):
        self.mock_session.request.return_value = _make_response(status=200)
        req = RequestData(method="GET", url="http://x", headers={"X-Key": "{{ token }}"})
        self.client.send_request(req, variables={"token": "abc123"})
        call_kwargs = self.mock_session.request.call_args[1]
        self.assertEqual("abc123", call_kwargs["headers"]["X-Key"])

    def test_stop_flag_stops_streaming_and_returns_partial_body(self):
        resp = _make_response(status=200, chunks=[b"chunk1", b"chunk2", b"chunk3"])
        self.mock_session.request.return_value = resp

        call_count = [0]

        def stop_flag():
            call_count[0] += 1
            return call_count[0] > 1

        req = RequestData(method="GET", url="http://x")
        result = self.client.send_request(req, stop_flag=stop_flag)
        resp.close.assert_called()
        self.assertNotIn("chunk2", result.body)

    def test_non_2xx_response_returns_correct_status_code(self):
        self.mock_session.request.return_value = _make_response(status=404)
        req = RequestData(method="GET", url="http://x")
        result = self.client.send_request(req)
        self.assertEqual(404, result.status_code)

    def test_connection_error_raises_execution_error_network(self):
        self.mock_session.request.side_effect = requests_lib.ConnectionError("refused")
        req = RequestData(method="GET", url="http://x")
        with self.assertRaises(ExecutionError) as ctx:
            self.client.send_request(req)
        self.assertEqual(ctx.exception.category, ErrorCategory.NETWORK)

    def test_timeout_raises_execution_error_timeout(self):
        self.mock_session.request.side_effect = requests_lib.Timeout("timed out")
        req = RequestData(method="GET", url="http://x")
        with self.assertRaises(ExecutionError) as ctx:
            self.client.send_request(req)
        self.assertEqual(ctx.exception.category, ErrorCategory.TIMEOUT)

    def test_request_exception_raises_execution_error_unknown(self):
        self.mock_session.request.side_effect = requests_lib.RequestException("fail")
        req = RequestData(method="GET", url="http://x")
        with self.assertRaises(ExecutionError) as ctx:
            self.client.send_request(req)
        self.assertEqual(ctx.exception.category, ErrorCategory.UNKNOWN)

    def test_execution_error_detail_contains_original_message(self):
        self.mock_session.request.side_effect = requests_lib.ConnectionError("conn refused")
        req = RequestData(method="GET", url="http://x")
        with self.assertRaises(ExecutionError) as ctx:
            self.client.send_request(req)
        self.assertIn("conn refused", ctx.exception.detail)


class TestHTTPClientInjection(unittest.TestCase):
    def test_injected_template_service_is_used_not_default(self):
        """A TemplateService passed at construction is the one called during send_request."""
        mock_ts = MagicMock()
        mock_ts.render_string.side_effect = lambda s, v: s  # passthrough
        client = HTTPClient(template_service=mock_ts)
        client.session = MagicMock()
        client.session.request.return_value = _make_response(200, chunks=[b"ok"])
        req = RequestData(method="GET", url="http://x/{{ path }}")
        client.send_request(req, variables={"path": "items"})
        mock_ts.render_string.assert_called()

    def test_no_injection_creates_default_template_service(self):
        """HTTPClient() with no template_service creates a default TemplateService instance."""
        from pypost.core.template_service import TemplateService
        client = HTTPClient()
        self.assertIsInstance(client._template_service, TemplateService)


if __name__ == "__main__":
    unittest.main()
