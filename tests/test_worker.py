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


if __name__ == "__main__":
    unittest.main()
