"""Lifecycle tests for RequestExecution: workers, cancellation and teardown."""
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.request_execution import (
    WORKER_SHUTDOWN_TIMEOUT_MS,
    RequestExecution,
)


def _request(request_id: str = "r1") -> RequestData:
    return RequestData(id=request_id, name="Test", method="GET", url="http://x")


def _running_worker() -> MagicMock:
    worker = MagicMock()
    worker.isRunning.return_value = True
    return worker


class RequestExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _execution(self, **kwargs):
        return RequestExecution(AppSettings(), metrics=MagicMock(), **kwargs)

    def _patched_worker(self, running=False):
        worker = MagicMock()
        worker.isRunning.return_value = running
        # start() is what makes a real worker report as running.
        worker.start.side_effect = lambda: worker.isRunning.configure_mock(
            return_value=True
        )
        return patch(
            "pypost.ui.presenters.request_execution.RequestWorker",
            return_value=worker,
        ), worker

    def test_send_starts_a_worker_and_announces_it(self):
        execution = self._execution()
        key = object()
        seen = []
        execution.started.connect(seen.append)
        patcher, worker = self._patched_worker()

        with patcher:
            execution.send(key, _request())

        worker.start.assert_called_once_with()
        self.assertEqual([key], seen)
        self.assertTrue(execution.is_running(key))

    def test_second_send_cancels_instead_of_starting_another(self):
        execution = self._execution()
        key = object()
        running = _running_worker()
        execution._by_key[key] = running
        seen = []
        execution.cancelling.connect(seen.append)
        patcher, _worker = self._patched_worker()

        with patcher as MockWorker:
            execution.send(key, _request())
            MockWorker.assert_not_called()

        running.stop.assert_called_once_with()
        self.assertEqual([key], seen)

    def test_send_after_the_previous_one_finished_starts_a_new_worker(self):
        execution = self._execution()
        key = object()
        stale = MagicMock()
        stale.isRunning.return_value = False
        execution._by_key[key] = stale
        patcher, worker = self._patched_worker()

        with patcher:
            execution.send(key, _request())

        worker.start.assert_called_once_with()
        stale.stop.assert_not_called()

    def test_settings_reach_the_next_worker(self):
        execution = self._execution()
        execution.apply_settings(AppSettings(request_timeout=41))
        patcher, _worker = self._patched_worker()

        with patcher as MockWorker:
            execution.send(object(), _request())

        self.assertEqual(41, MockWorker.call_args.kwargs["request_timeout"])

    def test_release_cancels_and_defers_the_callback(self):
        execution = self._execution()
        key = object()
        running = _running_worker()
        execution._by_key[key] = running
        on_finished = MagicMock()

        released = execution.release(key, on_finished)

        self.assertTrue(released)
        running.stop.assert_called_once_with()
        # QThread.finished, not the result signal: it fires on every outcome.
        running.finished.connect.assert_called_once_with(on_finished)
        on_finished.assert_not_called()
        self.assertFalse(execution.is_running(key))

    def test_release_reports_when_nothing_was_running(self):
        execution = self._execution()

        self.assertFalse(execution.release(object(), MagicMock()))

    def test_shutdown_stops_then_joins_every_worker(self):
        execution = self._execution()
        first, second = _running_worker(), _running_worker()
        execution._active.update({first, second})

        execution.shutdown()

        first.stop.assert_called_once_with()
        second.stop.assert_called_once_with()
        first.wait.assert_called_once_with(WORKER_SHUTDOWN_TIMEOUT_MS)
        second.wait.assert_called_once_with(WORKER_SHUTDOWN_TIMEOUT_MS)

    def test_shutdown_gives_up_on_a_worker_that_will_not_stop(self):
        execution = self._execution()
        stuck = _running_worker()
        stuck.wait.return_value = False  # still running when the timeout expires
        execution._active.add(stuck)

        execution.shutdown()  # must return rather than block

        stuck.wait.assert_called_once_with(WORKER_SHUTDOWN_TIMEOUT_MS)

    def test_a_released_request_is_still_joined_at_shutdown(self):
        execution = self._execution()
        key = object()
        running = _running_worker()
        execution._by_key[key] = running
        execution._active.add(running)

        execution.release(key, MagicMock())
        execution.shutdown()

        self.assertEqual(2, running.stop.call_count)
        running.wait.assert_called_once_with(WORKER_SHUTDOWN_TIMEOUT_MS)


if __name__ == "__main__":
    unittest.main()
