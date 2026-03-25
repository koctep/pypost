import unittest
from unittest.mock import MagicMock, patch

from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.core.request_service import RequestService, ExecutionResult
from pypost.core.template_service import TemplateService
from pypost.core.history_manager import HistoryManager


def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body, elapsed_time=0.1, size=len(body)
    )


class TestRequestServiceExecuteHTTP(unittest.TestCase):
    def setUp(self):
        self.svc = RequestService(metrics=MagicMock())
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()

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
        self.assertEqual({"k": "v"}, call_kwargs.kwargs["variables"])

    def test_execute_stream_callback_forwarded_to_http_client(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        cb = MagicMock()
        self.svc.execute(req, stream_callback=cb)
        call_kwargs = self.svc.http_client.send_request.call_args
        self.assertEqual(cb, call_kwargs.kwargs["stream_callback"])

    def test_execute_headers_callback_forwarded_to_http_client(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        cb = MagicMock()
        self.svc.execute(req, headers_callback=cb)
        call_kwargs = self.svc.http_client.send_request.call_args
        self.assertEqual(cb, call_kwargs.kwargs["headers_callback"])


class TestRequestServicePostScript(unittest.TestCase):
    def setUp(self):
        self.svc = RequestService(metrics=MagicMock())
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()
        self.svc.http_client.send_request.return_value = _make_response(200)

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
        self.svc = RequestService(metrics=MagicMock(), template_service=TemplateService())
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()

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


class TestRequestServiceInjection(unittest.TestCase):
    def test_injected_template_service_forwarded_to_http_client(self):
        """TemplateService passed to RequestService is the same instance in http_client."""
        from pypost.core.template_service import TemplateService
        ts = TemplateService()
        svc = RequestService(template_service=ts)
        self.assertIs(ts, svc._template_service)
        self.assertIs(ts, svc.http_client._template_service)

    def test_no_injection_sets_template_service_to_none(self):
        """RequestService() with no template_service stores None (no silent fallback)."""
        svc = RequestService()
        self.assertIsNone(svc._template_service)


class TestRequestServiceHistory(unittest.TestCase):
    def setUp(self):
        self.history_manager = MagicMock(spec=HistoryManager)
        self.svc = RequestService(
            metrics=MagicMock(),
            history_manager=self.history_manager,
            template_service=TemplateService(),
        )
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()
        self.svc.http_client.send_request.return_value = _make_response(200)

    def test_history_entry_recorded_after_execute(self):
        req = RequestData(method="GET", url="http://example.com", post_script="")
        self.svc.execute(req)
        self.history_manager.append.assert_called_once()
        entry = self.history_manager.append.call_args[0][0]
        self.assertEqual("GET", entry.method)
        self.assertEqual(200, entry.status_code)

    def test_history_records_resolved_url(self):
        from pypost.core.template_service import TemplateService
        ts = TemplateService()
        self.svc._template_service = ts
        req = RequestData(method="GET", url="http://{{host}}/api", post_script="")
        self.svc.execute(req, variables={"host": "myserver.com"})
        entry = self.history_manager.append.call_args[0][0]
        self.assertEqual("http://myserver.com/api", entry.url)

    def test_history_not_recorded_on_exception(self):
        self.svc.http_client.send_request.side_effect = RuntimeError("network error")
        req = RequestData(method="GET", url="http://example.com", post_script="")
        with self.assertRaises(RuntimeError):
            self.svc.execute(req)
        self.history_manager.append.assert_not_called()

    def test_history_failure_tracked_via_metrics(self):
        mock_metrics = MagicMock()
        self.svc._metrics = mock_metrics
        self.history_manager.append.side_effect = OSError("disk full")
        req = RequestData(method="GET", url="http://example.com", post_script="")
        self.svc.execute(req)
        mock_metrics.track_history_record_error.assert_called_once()

    def test_no_history_manager_no_error(self):
        svc = RequestService()
        svc.http_client = MagicMock()
        svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://example.com", post_script="")
        result = svc.execute(req)
        self.assertEqual(200, result.response.status_code)

    def test_collection_name_propagated(self):
        req = RequestData(method="GET", url="http://example.com", post_script="")
        self.svc.execute(req, collection_name="MyCol")
        entry = self.history_manager.append.call_args[0][0]
        self.assertEqual("MyCol", entry.collection_name)


class TestRequestServiceErrorHandling(unittest.TestCase):
    def setUp(self):
        self.svc = RequestService(
            metrics=MagicMock(), template_service=TemplateService()
        )
        self.svc.http_client = MagicMock()
        self.svc.mcp_client = MagicMock()

    def test_execution_error_from_http_client_returns_execution_result(self):
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        self.svc.http_client.send_request.side_effect = exc
        req = RequestData(method="GET", url="http://x", post_script="")
        result = self.svc.execute(req)
        self.assertIsInstance(result, ExecutionResult)
        self.assertIs(result.execution_error, exc)

    def test_network_error_populates_execution_error_category(self):
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        self.svc.http_client.send_request.side_effect = exc
        req = RequestData(method="GET", url="http://x", post_script="")
        result = self.svc.execute(req)
        self.assertEqual(result.execution_error.category, ErrorCategory.NETWORK)

    def test_network_error_response_has_status_code_zero(self):
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        self.svc.http_client.send_request.side_effect = exc
        req = RequestData(method="GET", url="http://x", post_script="")
        result = self.svc.execute(req)
        self.assertEqual(result.response.status_code, 0)

    def test_template_error_populates_execution_error_template_category(self):
        svc = RequestService(
            metrics=MagicMock(), template_service=TemplateService()
        )
        svc.http_client = MagicMock()
        # Force template rendering to fail
        svc._template_service = MagicMock()
        svc._template_service.render_string.side_effect = Exception("bad template")
        req = RequestData(method="GET", url="{{ broken", post_script="")
        with self.assertRaises(ExecutionError) as ctx:
            svc.execute(req)
        self.assertEqual(ctx.exception.category, ErrorCategory.TEMPLATE)

    def test_script_error_populates_execution_error_script_category(self):
        self.svc.http_client.send_request.return_value = _make_response(200)
        with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
            mock_executor.execute.return_value = ({}, [], "NameError: x not defined")
            req = RequestData(method="GET", url="http://x", post_script="bad")
            result = self.svc.execute(req)
        self.assertEqual(result.execution_error.category, ErrorCategory.SCRIPT)
        self.assertEqual(result.script_error, "NameError: x not defined")

    def test_network_error_tracks_metrics(self):
        mock_metrics = MagicMock()
        self.svc._metrics = mock_metrics
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        self.svc.http_client.send_request.side_effect = exc
        req = RequestData(method="GET", url="http://x", post_script="")
        self.svc.execute(req)
        mock_metrics.track_request_error.assert_called_once_with(ErrorCategory.NETWORK)

    def test_script_error_tracks_metrics(self):
        mock_metrics = MagicMock()
        self.svc._metrics = mock_metrics
        self.svc.http_client.send_request.return_value = _make_response(200)
        with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
            mock_executor.execute.return_value = ({}, [], "err")
            req = RequestData(method="GET", url="http://x", post_script="bad")
            self.svc.execute(req)
        mock_metrics.track_request_error.assert_called_once_with(ErrorCategory.SCRIPT)


if __name__ == "__main__":
    unittest.main()
