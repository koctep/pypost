import unittest
from unittest.mock import MagicMock, patch

from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.request_service import RequestService


def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body, elapsed_time=0.1, size=len(body)
    )


class TestRequestServiceExecuteHTTP(unittest.TestCase):
    def setUp(self):
        self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
        self.metrics_patcher.start()
        self.svc = RequestService()
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()

    def tearDown(self):
        self.metrics_patcher.stop()

    def test_execute_http_success_returns_execution_result(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x", post_script="")
        result = self.svc.execute(req)
        self.assertEqual(200, result.response.status_code)
        self.assertIsNone(result.script_error)

    def test_execute_passes_variables_to_http_client(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        self.svc.execute(req, variables={"k": "v"})
        call_kwargs = self.svc.http_client.send_request.call_args
        self.assertEqual({"k": "v"}, call_kwargs[0][1])

    def test_execute_stream_callback_forwarded_to_http_client(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        cb = MagicMock()
        self.svc.execute(req, stream_callback=cb)
        call_kwargs = self.svc.http_client.send_request.call_args
        self.assertEqual(cb, call_kwargs[0][2])

    def test_execute_headers_callback_forwarded_to_http_client(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        cb = MagicMock()
        self.svc.execute(req, headers_callback=cb)
        call_kwargs = self.svc.http_client.send_request.call_args
        self.assertEqual(cb, call_kwargs[0][4])


class TestRequestServicePostScript(unittest.TestCase):
    def setUp(self):
        self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
        self.metrics_patcher.start()
        self.svc = RequestService()
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()
        self.svc.http_client.send_request.return_value = _make_response(200)

    def tearDown(self):
        self.metrics_patcher.stop()

    def test_execute_post_script_populates_logs_and_variables(self):
        with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
            mock_executor.execute.return_value = ({"x": 1}, ["log"], None)
            req = RequestData(method="GET", url="http://x", post_script="x=1")
            result = self.svc.execute(req)
        self.assertEqual({"x": 1}, result.updated_variables)
        self.assertEqual(["log"], result.script_logs)

    def test_execute_post_script_error_sets_script_error_field(self):
        with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
            mock_executor.execute.return_value = ({}, [], "SyntaxError")
            req = RequestData(method="GET", url="http://x", post_script="bad")
            result = self.svc.execute(req)
        self.assertEqual("SyntaxError", result.script_error)


class TestRequestServiceMCP(unittest.TestCase):
    def setUp(self):
        self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
        self.metrics_patcher.start()
        self.svc = RequestService()
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()

    def tearDown(self):
        self.metrics_patcher.stop()

    def test_execute_mcp_request_delegates_to_mcp_client(self):
        self.svc.mcp_client.run.return_value = _make_response(200)
        req = RequestData(method="MCP", url="http://x")
        result = self.svc.execute(req)
        self.assertEqual(200, result.response.status_code)

    def test_execute_mcp_does_not_call_http_client(self):
        self.svc.mcp_client.run.return_value = _make_response(200)
        req = RequestData(method="MCP", url="http://x")
        self.svc.execute(req)
        self.svc.http_client.send_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
