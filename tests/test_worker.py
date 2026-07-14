"""Tests for RequestWorker error signal behavior."""
import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch

from pypost.core.qt.worker import RequestWorker
from pypost.models.models import RequestData
from pypost.models.errors import ErrorCategory, ExecutionError


class TestRequestWorkerError(unittest.TestCase):

    def _make_worker(self):
        req = RequestData(method="GET", url="http://x")
        return RequestWorker(req, variables={}, metrics=MagicMock())

    def test_worker_emits_error_on_cancelled_execution_result(self):
        from pypost.core.request_service import ExecutionResult
        from pypost.models.response import ResponseData

        worker = self._make_worker()
        finished = []
        errors = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.error.connect(lambda e: errors.append(e))

        exc = ExecutionError(
            category=ErrorCategory.CANCELLED,
            message="Request cancelled",
            detail="Cancelled during retry delay",
        )
        resp = ResponseData(
            status_code=0, headers={}, body="", elapsed_time=0.0, size=0,
        )
        result = ExecutionResult(
            response=resp,
            updated_variables={},
            script_logs=[],
            execution_error=exc,
        )
        with patch.object(worker.service, "execute", return_value=result):
            worker.run()

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].category, ErrorCategory.CANCELLED)
        self.assertEqual(len(finished), 0)

    def test_worker_emits_finished_on_execution_result_error(self):
        from pypost.core.request_service import ExecutionResult
        from pypost.models.response import ResponseData

        worker = self._make_worker()
        finished = []
        errors = []
        worker.finished.connect(lambda r: finished.append(r))
        worker.error.connect(lambda e: errors.append(e))

        exc = ExecutionError(category=ErrorCategory.NETWORK, message="no conn")
        resp = ResponseData(
            status_code=0, headers={}, body="", elapsed_time=0.0, size=0,
        )
        result = ExecutionResult(
            response=resp,
            updated_variables={},
            script_logs=[],
            execution_error=exc,
        )
        with patch.object(worker.service, "execute", return_value=result):
            worker.run()

        self.assertEqual(len(finished), 1)
        self.assertEqual(len(errors), 0)

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
            response=resp, updated_variables={}, script_logs=[],
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
                response=resp, updated_variables={}, script_logs=[],
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


class TestRequestWorkerHiddenKeys(unittest.TestCase):

    def test_hidden_keys_forwarded_to_service_execute(self):
        from pypost.models.response import ResponseData
        from pypost.core.request_service import ExecutionResult

        req = RequestData(method="GET", url="http://x")
        worker = RequestWorker(req, variables={}, hidden_keys={"token"})
        resp = ResponseData(
            status_code=200, headers={}, body="ok", elapsed_time=0.1, size=2
        )
        result = ExecutionResult(
            response=resp, updated_variables={}, script_logs=[],
        )
        with patch.object(worker.service, "execute", return_value=result) as exec_mock:
            worker.run()
        self.assertEqual({"token"}, exec_mock.call_args.kwargs["hidden_keys"])


@pytest.mark.timeout(60)
def test_worker_wraps_unexpected_exception_logs_error(caplog):
    """ERROR log is explicit under caplog contract (PYPOST-574)."""
    import logging
    from unittest.mock import MagicMock, patch

    from pypost.core.qt.worker import RequestWorker
    from pypost.models.errors import ErrorCategory, ExecutionError
    from pypost.models.models import RequestData

    req = RequestData(method="GET", url="http://x")
    worker = RequestWorker(req, variables={}, metrics=MagicMock())
    received = []
    worker.error.connect(lambda e: received.append(e))

    with caplog.at_level(logging.ERROR, logger="pypost.core.qt.worker"):
        with patch.object(worker.service, "execute", side_effect=RuntimeError("boom")):
            worker.run()

    assert len(received) == 1
    assert isinstance(received[0], ExecutionError)
    assert received[0].category == ErrorCategory.UNKNOWN
    assert any("unexpected error" in r.message for r in caplog.records)


if __name__ == "__main__":
    unittest.main()
