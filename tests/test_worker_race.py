"""Tests for race condition fixes in RequestWorker and TabsPresenter."""
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.request_service import ExecutionResult


def _make_worker():
    req = RequestData(method="GET", url="http://x")
    return RequestWorker(req, variables={}, metrics=MagicMock())


def _ok_result():
    resp = ResponseData(status_code=200, headers={}, body="ok", elapsed_time=0.1, size=2)
    return ExecutionResult(response=resp, updated_variables={}, script_logs=[], script_error=None)


class TestWorkerRaceCondition(unittest.TestCase):

    def test_stop_before_run_check_stop_is_true(self):
        """REQ-5.2a: stop() called before run() must make check_stop return True."""
        worker = _make_worker()
        worker.stop()
        with patch.object(worker.service, "execute", return_value=_ok_result()) as mock_exec:
            worker.run()
        call_kwargs = mock_exec.call_args.kwargs
        self.assertTrue(call_kwargs["stop_flag"]())

    def test_stop_flag_not_overwritten_after_stop(self):
        """REQ-5.2b: run() must not overwrite a stop() that occurred before it started."""
        worker = _make_worker()
        worker.stop()
        captured_check_stop = None

        def capture_stop_flag(*args, **kwargs):
            nonlocal captured_check_stop
            captured_check_stop = kwargs["stop_flag"]
            return _ok_result()

        with patch.object(worker.service, "execute", side_effect=capture_stop_flag):
            worker.run()

        self.assertIsNotNone(captured_check_stop)
        self.assertTrue(captured_check_stop())

    def test_second_send_while_running_does_not_create_second_worker(self):
        """REQ-5.2c: firing a second send while a worker is running must not create another."""
        from pypost.ui.presenters.tabs_presenter import TabsPresenter, RequestTab
        from pypost.models.settings import AppSettings

        app = QApplication.instance() or QApplication([])

        request_data = RequestData(id="r1", name="Test", method="GET", url="http://x")

        rm = MagicMock()
        rm.find_request.return_value = None
        rm.get_collections.return_value = []
        sm = MagicMock()
        sm.get_open_tabs.return_value = []
        sm.get_expanded_collections.return_value = []
        sm.settings = AppSettings()

        p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        p.add_new_tab(request_data)
        tab = p.widget.widget(0)

        fake_worker = MagicMock()
        fake_worker.isRunning.return_value = True
        tab.worker = fake_worker

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            p._handle_send_request(request_data)
            MockWorker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
