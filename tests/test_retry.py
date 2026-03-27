"""Unit tests for retry logic in RequestService._execute_http_with_retry."""
import unittest
from unittest.mock import MagicMock

from pypost.core.request_service import RequestService
from pypost.core.alert_manager import AlertManager
from pypost.models.models import RequestData
from pypost.models.retry import RetryPolicy
from pypost.models.response import ResponseData
from pypost.models.errors import ErrorCategory, ExecutionError


def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body,
        elapsed_time=0.1, size=len(body),
    )


def _make_service(metrics=None, alert_manager=None):
    svc = RequestService(metrics=metrics or MagicMock(), alert_manager=alert_manager)
    svc.http_client = MagicMock()
    svc.mcp_client = MagicMock()
    return svc


def _make_request(max_retries=0, retryable_codes=None):
    policy = RetryPolicy(
        max_retries=max_retries,
        retry_delay_seconds=0.0,
        retry_backoff_multiplier=1.0,
        retryable_status_codes=retryable_codes or [429, 500, 502, 503, 504],
    )
    return RequestData(method="GET", url="http://example.com", retry_policy=policy)


class TestNoRetryDefault(unittest.TestCase):
    """AC-7: default retry_policy=None means no retry path taken."""

    def test_no_retry_policy_returns_first_response(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)
        self.assertEqual(svc.http_client.send_request.call_count, 1)

    def test_no_retry_policy_does_not_retry_on_503(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(503)
        req = RequestData(method="GET", url="http://x")
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 503)
        self.assertEqual(svc.http_client.send_request.call_count, 1)

    def test_max_retries_zero_policy_returns_first_response(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(200)
        req = _make_request(max_retries=0)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)
        self.assertEqual(svc.http_client.send_request.call_count, 1)


class TestRetryOnRetryableStatusCode(unittest.TestCase):
    """AC-1: retries up to max_retries on retryable_status_codes."""

    def test_retries_on_503_then_succeeds(self):
        svc = _make_service()
        svc.http_client.send_request.side_effect = [
            _make_response(503),
            _make_response(200),
        ]
        req = _make_request(max_retries=1)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)
        self.assertEqual(svc.http_client.send_request.call_count, 2)

    def test_retries_three_times_then_succeeds(self):
        svc = _make_service()
        svc.http_client.send_request.side_effect = [
            _make_response(503),
            _make_response(503),
            _make_response(503),
            _make_response(200),
        ]
        req = _make_request(max_retries=3)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)
        self.assertEqual(svc.http_client.send_request.call_count, 4)

    def test_non_retryable_status_code_not_retried(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(404)
        req = _make_request(max_retries=3)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 404)
        self.assertEqual(svc.http_client.send_request.call_count, 1)

    def test_200_not_retried(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(200)
        req = _make_request(max_retries=3)
        svc.execute(req)
        self.assertEqual(svc.http_client.send_request.call_count, 1)


class TestRetryOnException(unittest.TestCase):
    """Retry on ExecutionError exceptions."""

    def test_retries_on_network_exception_then_succeeds(self):
        svc = _make_service()
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="conn reset")
        svc.http_client.send_request.side_effect = [exc, _make_response(200)]
        req = _make_request(max_retries=1)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)
        self.assertEqual(svc.http_client.send_request.call_count, 2)

    def test_exhausted_exception_retries_returns_execution_result_with_error(self):
        svc = _make_service()
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="conn reset")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=2)
        result = svc.execute(req)
        self.assertIsNotNone(result.execution_error)
        self.assertEqual(result.execution_error.category, ErrorCategory.NETWORK)
        self.assertEqual(svc.http_client.send_request.call_count, 3)

    def test_detail_contains_retries_attempted_on_exhaustion(self):
        svc = _make_service()
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="conn reset")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=2)
        result = svc.execute(req)
        self.assertIn("retries_attempted: 2", result.execution_error.detail)


class TestRetryCallback(unittest.TestCase):
    """AC-2: retry_callback is called for each retry attempt."""

    def test_retry_callback_called_once_on_single_retry(self):
        svc = _make_service()
        svc.http_client.send_request.side_effect = [
            _make_response(503),
            _make_response(200),
        ]
        req = _make_request(max_retries=1)
        callback = MagicMock()
        svc.execute(req, retry_callback=callback)
        callback.assert_called_once()
        attempt, max_r, err = callback.call_args[0]
        self.assertEqual(attempt, 1)
        self.assertEqual(max_r, 1)

    def test_retry_callback_called_for_each_attempt(self):
        svc = _make_service()
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = [exc, exc, _make_response(200)]
        req = _make_request(max_retries=2)
        callback = MagicMock()
        svc.execute(req, retry_callback=callback)
        self.assertEqual(callback.call_count, 2)

    def test_no_callback_does_not_raise(self):
        svc = _make_service()
        svc.http_client.send_request.side_effect = [
            _make_response(503), _make_response(200)
        ]
        req = _make_request(max_retries=1)
        # Should not raise even with no callback
        result = svc.execute(req, retry_callback=None)
        self.assertEqual(result.response.status_code, 200)


class TestStopFlagDuringRetry(unittest.TestCase):
    """AC-3: stop_flag is polled inside back-off sleep loop."""

    def test_stop_flag_cancels_retry(self):
        svc = _make_service()
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=3, retryable_codes=[500])
        stop = MagicMock(return_value=True)
        # First call: stop_flag checked before 2nd attempt
        result = svc.execute(req, stop_flag=stop)
        # Should return a cancelled/network error, not retry 3 times
        self.assertIsNotNone(result.execution_error)
        # stop_flag was checked
        stop.assert_called()


class TestRetryMetrics(unittest.TestCase):
    """AC-4: metrics.track_retry_attempt called per attempt."""

    def test_track_retry_attempt_called_on_each_retry(self):
        metrics = MagicMock()
        svc = _make_service(metrics=metrics)
        svc.http_client.send_request.side_effect = [
            _make_response(503), _make_response(503), _make_response(200)
        ]
        req = _make_request(max_retries=2)
        svc.execute(req)
        self.assertEqual(metrics.track_retry_attempt.call_count, 2)

    def test_track_retry_attempt_passes_method_and_category(self):
        metrics = MagicMock()
        svc = _make_service(metrics=metrics)
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = [exc, _make_response(200)]
        req = _make_request(max_retries=1)
        svc.execute(req)
        metrics.track_retry_attempt.assert_called_once_with("GET", "network")

    def test_no_metrics_no_error_on_retry(self):
        svc = RequestService()
        svc.http_client = MagicMock()
        svc.http_client.send_request.side_effect = [
            _make_response(503), _make_response(200)
        ]
        req = _make_request(max_retries=1)
        result = svc.execute(req)
        self.assertEqual(result.response.status_code, 200)


class TestExhaustionAlert(unittest.TestCase):
    """AC-5/AC-6: metrics and alert_manager called on exhaustion."""

    def test_track_request_retry_exhaustion_called_on_exhaustion(self):
        metrics = MagicMock()
        svc = _make_service(metrics=metrics)
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=1)
        svc.execute(req)
        metrics.track_request_retry_exhaustion.assert_called_once_with(req.url)

    def test_alert_manager_emit_called_on_exhaustion(self):
        alert_manager = MagicMock(spec=AlertManager)
        svc = _make_service(alert_manager=alert_manager)
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="conn fail")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=1)
        svc.execute(req)
        alert_manager.emit.assert_called_once()
        payload = alert_manager.emit.call_args[0][0]
        self.assertEqual(payload.endpoint, req.url)
        self.assertEqual(payload.retries_attempted, 1)
        self.assertEqual(payload.final_error_category, "network")
        self.assertEqual(payload.final_error_message, "conn fail")

    def test_no_alert_manager_does_not_raise_on_exhaustion(self):
        svc = _make_service(alert_manager=None)
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = exc
        req = _make_request(max_retries=1)
        # Should not raise
        result = svc.execute(req)
        self.assertIsNotNone(result.execution_error)

    def test_no_exhaustion_alert_when_retries_succeed(self):
        alert_manager = MagicMock(spec=AlertManager)
        metrics = MagicMock()
        svc = _make_service(metrics=metrics, alert_manager=alert_manager)
        exc = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
        svc.http_client.send_request.side_effect = [exc, _make_response(200)]
        req = _make_request(max_retries=1)
        svc.execute(req)
        alert_manager.emit.assert_not_called()
        metrics.track_request_retry_exhaustion.assert_not_called()


class TestRetryableStatusExhaustion(unittest.TestCase):
    """Retry exhaustion after retryable HTTP status codes (not only exceptions)."""

    def test_exhausted_status_retries_returns_execution_error(self):
        svc = _make_service()
        svc.http_client.send_request.return_value = _make_response(503)
        req = _make_request(max_retries=1)
        result = svc.execute(req)
        self.assertIsNotNone(result.execution_error)
        self.assertEqual(result.execution_error.category, ErrorCategory.NETWORK)
        self.assertEqual(result.execution_error.message, "HTTP 503")
        self.assertEqual(svc.http_client.send_request.call_count, 2)

    def test_detail_contains_retries_attempted_on_status_exhaustion(self):
        svc = _make_service()
        svc.http_client.send_request.side_effect = [
            _make_response(503),
            _make_response(503),
            _make_response(503),
        ]
        req = _make_request(max_retries=2)
        result = svc.execute(req)
        self.assertIn("retries_attempted: 2", result.execution_error.detail)

    def test_track_request_retry_exhaustion_on_status_exhaustion(self):
        metrics = MagicMock()
        svc = _make_service(metrics=metrics)
        svc.http_client.send_request.return_value = _make_response(502)
        req = _make_request(max_retries=0)
        svc.execute(req)
        metrics.track_request_retry_exhaustion.assert_called_once_with(req.url)

    def test_alert_manager_emit_on_status_exhaustion(self):
        alert_manager = MagicMock(spec=AlertManager)
        svc = _make_service(alert_manager=alert_manager)
        svc.http_client.send_request.return_value = _make_response(503)
        req = _make_request(max_retries=0)
        svc.execute(req)
        alert_manager.emit.assert_called_once()
        payload = alert_manager.emit.call_args[0][0]
        self.assertEqual(payload.endpoint, req.url)
        self.assertEqual(payload.retries_attempted, 0)
        self.assertEqual(payload.final_error_category, "network")
        self.assertEqual(payload.final_error_message, "HTTP 503")


class TestRetryPolicyModel(unittest.TestCase):
    """RetryPolicy Pydantic model validation."""

    def test_defaults(self):
        p = RetryPolicy()
        self.assertEqual(p.max_retries, 0)
        self.assertEqual(p.retry_delay_seconds, 1.0)
        self.assertEqual(p.retry_backoff_multiplier, 2.0)
        self.assertIn(503, p.retryable_status_codes)

    def test_serialise_and_deserialise(self):
        p = RetryPolicy(max_retries=3, retry_delay_seconds=0.5)
        data = p.model_dump()
        p2 = RetryPolicy(**data)
        self.assertEqual(p, p2)

    def test_request_data_with_retry_policy(self):
        policy = RetryPolicy(max_retries=2)
        req = RequestData(method="POST", url="http://x", retry_policy=policy)
        self.assertEqual(req.retry_policy.max_retries, 2)

    def test_request_data_retry_policy_defaults_none(self):
        req = RequestData(method="GET", url="http://x")
        self.assertIsNone(req.retry_policy)


if __name__ == "__main__":
    unittest.main()
