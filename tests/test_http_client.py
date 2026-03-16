import unittest
from unittest.mock import MagicMock
import requests as requests_lib

from pypost.core.http_client import HTTPClient
from pypost.models.models import RequestData


def _make_response(status=200, headers=None, chunks=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = {"Content-Type": "application/json", **(headers or {})}
    resp.iter_content.return_value = iter(chunks or ["body"])
    resp.close.return_value = None
    return resp


class TestHTTPClientSendRequest(unittest.TestCase):
    def setUp(self):
        self.client = HTTPClient(metrics=MagicMock())
        self.mock_session = MagicMock()
        self.client.session = self.mock_session

    def test_get_200_returns_response_data_with_correct_fields(self):
        self.mock_session.request.return_value = _make_response(
            status=200, chunks=['{"ok":true}']
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
        resp = _make_response(status=200, chunks=["chunk1", "chunk2", "chunk3"])
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

    def test_connection_error_propagates(self):
        self.mock_session.request.side_effect = requests_lib.ConnectionError("refused")
        req = RequestData(method="GET", url="http://x")
        with self.assertRaises(requests_lib.ConnectionError):
            self.client.send_request(req)


if __name__ == "__main__":
    unittest.main()
