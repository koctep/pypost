"""Tests for RequestWorker error signal behavior."""
import unittest
from unittest.mock import MagicMock, patch

from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData
from pypost.models.errors import ErrorCategory, ExecutionError


class TestRequestWorkerError(unittest.TestCase):

    def _make_worker(self):
        req = RequestData(method="GET", url="http://x")
        return RequestWorker(req, variables={}, metrics=MagicMock())

    def test_worker_emits_execution_error_on_execution_error(self):
        worker = self._make_worker()
        received = []
        worker.error.connect(lambda e: received.append(e))

        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        with patch.object(worker.service, "execute", side_effect=exc):
            worker.run()

        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], ExecutionError)
        self.assertEqual(received[0].category, ErrorCategory.NETWORK)

    def test_worker_wraps_unexpected_exception_as_execution_error_unknown(self):
        worker = self._make_worker()
        received = []
        worker.error.connect(lambda e: received.append(e))

        with patch.object(worker.service, "execute", side_effect=RuntimeError("boom")):
            worker.run()

        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], ExecutionError)
        self.assertEqual(received[0].category, ErrorCategory.UNKNOWN)

    def test_worker_emits_finished_on_success(self):
        from pypost.models.response import ResponseData
        from pypost.core.request_service import ExecutionResult

        worker = self._make_worker()
        finished = []
        worker.finished.connect(lambda r: finished.append(r))

        resp = ResponseData(status_code=200, headers={}, body="ok", elapsed_time=0.1, size=2)
        result = ExecutionResult(
            response=resp, updated_variables={}, script_logs=[], script_error=None
        )
        with patch.object(worker.service, "execute", return_value=result):
            worker.run()

        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0].status_code, 200)


class TestRequestWorkerRetrySignal(unittest.TestCase):

    def _make_worker(self):
        req = RequestData(method="GET", url="http://x")
        return RequestWorker(req, variables={}, metrics=MagicMock())

    def test_worker_emits_retry_attempt_signal(self):
        from pypost.core.request_service import ExecutionResult
        from pypost.models.response import ResponseData
        from pypost.models.retry import RetryPolicy

        worker = self._make_worker()
        retry_events = []
        worker.retry_attempt.connect(
            lambda attempt, max_r, err: retry_events.append((attempt, max_r, err))
        )

        # Simulate service.execute calling retry_callback once
        def fake_execute(request, variables=None, **kwargs):
            cb = kwargs.get("retry_callback")
            if cb:
                err = ExecutionError(category=ErrorCategory.NETWORK, message="fail")
                cb(1, 2, err)
            resp = ResponseData(
                status_code=200, headers={}, body="ok", elapsed_time=0.1, size=2
            )
            return ExecutionResult(
                response=resp, updated_variables={}, script_logs=[], script_error=None
            )

        with patch.object(worker.service, "execute", side_effect=fake_execute):
            worker.run()

        self.assertEqual(len(retry_events), 1)
        attempt, max_r, err = retry_events[0]
        self.assertEqual(attempt, 1)
        self.assertEqual(max_r, 2)
        self.assertIsInstance(err, ExecutionError)


class TestRequestWorkerAlertManagerInjection(unittest.TestCase):

    def test_alert_manager_forwarded_to_service(self):
        from pypost.core.alert_manager import AlertManager
        req = RequestData(method="GET", url="http://x")
        mock_am = MagicMock(spec=AlertManager)
        worker = RequestWorker(req, alert_manager=mock_am)
        self.assertIs(worker.service._alert_manager, mock_am)

    def test_alert_manager_none_by_default(self):
        req = RequestData(method="GET", url="http://x")
        worker = RequestWorker(req)
        self.assertIsNone(worker.service._alert_manager)


if __name__ == "__main__":
    unittest.main()
