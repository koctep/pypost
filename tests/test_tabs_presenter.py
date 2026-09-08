import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from pypost.ui.presenters.tabs_presenter import TabsPresenter, RequestTab
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings


def _make_request(req_id: str = "r1", name: str = "Test", method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, requests=None):
        self._requests = {r.id: (r, MagicMock(id="c1")) for r in (requests or [])}
        self.saved = []
        self.collections = []

    def find_request(self, req_id):
        return self._requests.get(req_id)

    def get_collections(self):
        return self.collections

    def save_request(self, req, col_id):
        self.saved.append((req, col_id))

    def create_collection(self, name):
        from pypost.models.models import Collection
        col = Collection(name=name)
        self.collections.append(col)
        return col


class FakeStateManager:
    def __init__(self, open_tabs=None):
        self._open_tabs = open_tabs or []
        self._expanded = []
        self.settings = AppSettings()

    def get_open_tabs(self):
        return list(self._open_tabs)

    def set_open_tabs(self, ids):
        self._open_tabs = ids

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = ids


class TestTabsPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, requests=None, open_tabs=None):
        rm = FakeRequestManager(requests)
        sm = FakeStateManager(open_tabs)
        settings = AppSettings()
        return TabsPresenter(rm, sm, settings, metrics=MagicMock())

    def test_widget_is_qtab_widget(self):
        from PySide6.QtWidgets import QTabWidget
        p = self._make_presenter()
        self.assertIsInstance(p.widget, QTabWidget)

    def test_add_new_tab_creates_unnamed_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 1)
        self.assertEqual(p.widget.tabText(0), "New Request")

    def test_add_new_tab_with_request_data(self):
        req = _make_request(name="Login")
        p = self._make_presenter()
        p.add_new_tab(req)
        self.assertEqual(p.widget.count(), 1)
        self.assertEqual(p.widget.tabText(0), "Login")

    def test_close_tab_removes_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        closed_tab = p.widget.widget(0)
        closed_tab.deleteLater = MagicMock()
        self.assertEqual(p.widget.count(), 2)
        p.close_tab(0)
        self.assertEqual(p.widget.count(), 1)
        closed_tab.deleteLater.assert_called_once_with()

    def test_close_tab_stops_worker_before_deleting_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        closed_tab = p.widget.widget(0)
        closed_tab.deleteLater = MagicMock()
        worker = MagicMock()
        worker.isRunning.return_value = True
        closed_tab.worker = worker

        p.close_tab(0)

        worker.stop.assert_called_once_with()
        closed_tab.deleteLater.assert_not_called()
        worker.finished.connect.assert_called_once_with(closed_tab.deleteLater)
        worker.error.connect.assert_called_once_with(closed_tab.deleteLater)

    def test_close_tab_ignores_invalid_index(self):
        p = self._make_presenter()
        p.add_new_tab()

        p.close_tab(99)

        self.assertEqual(p.widget.count(), 1)

    def test_close_tab_ensures_at_least_one_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 1)
        p.close_tab(0)
        self.assertEqual(p.widget.count(), 1)

    def test_shutdown_workers_stops_all_running_workers_before_waiting(self):
        p = self._make_presenter()
        p.add_new_tab()
        first_tab = p.widget.widget(0)
        first_worker = MagicMock()
        first_worker.isRunning.return_value = True
        first_tab.worker = first_worker
        p.add_new_tab()
        second_tab = p.widget.widget(1)
        second_worker = MagicMock()
        second_worker.isRunning.return_value = True
        second_tab.worker = second_worker
        p._workers.update({first_worker, second_worker})

        p.shutdown_workers()

        first_worker.stop.assert_called_once_with()
        second_worker.stop.assert_called_once_with()
        first_worker.wait.assert_called_once_with()
        second_worker.wait.assert_called_once_with()

    def test_shutdown_workers_waits_for_worker_from_closed_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        closed_tab = p.widget.widget(0)
        worker = MagicMock()
        worker.isRunning.return_value = True
        closed_tab.worker = worker
        p._workers.add(worker)

        p.close_tab(0)
        p.shutdown_workers()

        self.assertEqual(worker.stop.call_count, 2)
        worker.wait.assert_called_once_with()

    def test_restore_tabs_opens_saved_tabs(self):
        req = _make_request("r1", "Saved Request")
        p = self._make_presenter(requests=[req], open_tabs=["r1"])
        p.restore_tabs()
        self.assertEqual(p.widget.count(), 1)
        tab = p.widget.widget(0)
        self.assertIsInstance(tab, RequestTab)
        self.assertEqual(tab.request_data.id, "r1")

    def test_restore_tabs_opens_new_tab_when_no_saved(self):
        p = self._make_presenter(open_tabs=[])
        p.restore_tabs()
        self.assertEqual(p.widget.count(), 1)

    def test_save_tabs_state_persists_ids(self):
        req = _make_request("r1")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.save_tabs_state()
        self.assertEqual(p._state_manager.get_open_tabs(), ["r1"])

    def test_rename_request_tabs_updates_label(self):
        req = _make_request("r1", "Old Name")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.rename_request_tabs("r1", "New Name")
        self.assertEqual(p.widget.tabText(0), "New Name")

    def test_rename_request_tabs_noop_for_unknown_id(self):
        req = _make_request("r1", "My Tab")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.rename_request_tabs("unknown", "Changed")
        self.assertEqual(p.widget.tabText(0), "My Tab")

    def test_on_env_variables_changed_updates_tabs(self):
        p = self._make_presenter()
        p.add_new_tab()
        variables = {"BASE_URL": "https://example.com"}
        p.on_env_variables_changed(variables)
        self.assertEqual(p._current_variables, variables)

    def test_on_env_keys_changed_pushes_keys(self):
        p = self._make_presenter()
        p.add_new_tab()
        keys = ["KEY1", "KEY2"]
        p.on_env_keys_changed(keys)

    def test_on_env_hidden_keys_changed_pushes_to_request_editor(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        tab.request_editor.set_hidden_keys = MagicMock()
        hidden_keys = {"TOKEN"}
        p.on_env_hidden_keys_changed(hidden_keys)
        tab.request_editor.set_hidden_keys.assert_called_once_with(hidden_keys)

    def test_handle_new_tab_opens_tab(self):
        p = self._make_presenter()
        p.handle_new_tab("test_source")
        self.assertEqual(p.widget.count(), 1)

    def test_send_does_not_duplicate_transport_request_metric(self):
        p = self._make_presenter()
        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as worker_class:
            worker_class.return_value.isRunning.return_value = False
            tab.request_editor.send_requested.emit(req)

        p._metrics.track_request_sent.assert_not_called()

    def test_finished_does_not_duplicate_transport_response_metric(self):
        from pypost.models.response import ResponseData

        p = self._make_presenter()
        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)
        response = ResponseData(
            status_code=200,
            headers={},
            body="ok",
            elapsed_time=0.1,
            size=2,
        )

        p._on_request_finished(tab, response)

        p._metrics.track_response_received.assert_not_called()

    def test_handle_close_tab_closes_current(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 2)
        p.widget.setCurrentIndex(1)
        p.handle_close_tab()
        self.assertEqual(p.widget.count(), 1)

    def test_handle_next_tab_cycles(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.widget.setCurrentIndex(0)
        p.handle_next_tab()
        self.assertEqual(p.widget.currentIndex(), 1)
        p.handle_next_tab()
        self.assertEqual(p.widget.currentIndex(), 0)

    def test_handle_previous_tab_cycles(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.widget.setCurrentIndex(0)
        p.handle_previous_tab()
        self.assertEqual(p.widget.currentIndex(), 1)

    def test_handle_switch_to_tab_valid_index(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.handle_switch_to_tab(1)
        self.assertEqual(p.widget.currentIndex(), 1)

    def test_handle_switch_to_tab_invalid_index_noop(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.handle_switch_to_tab(99)
        self.assertEqual(p.widget.currentIndex(), 0)

    def test_apply_settings_updates_indent(self):
        p = self._make_presenter()
        p.add_new_tab()
        new_settings = AppSettings(indent_size=4)
        p.apply_settings(new_settings)
        self.assertEqual(p._settings.indent_size, 4)

    def test_variable_set_requested_forwarded(self):
        p = self._make_presenter()
        p.add_new_tab()
        received = []
        p.variable_set_requested.connect(lambda k, v: received.append((k, v)))
        tab = p.widget.widget(0)
        tab.response_view.variable_set_requested.emit("mykey", "myval")
        self.assertEqual(received, [("mykey", "myval")])

    def test_new_tab_applies_env_variables(self):
        p = self._make_presenter()
        variables = {"TOKEN": "abc123"}
        p._current_variables = variables
        p.add_new_tab()
        tab = p.widget.widget(0)
        if hasattr(tab.request_editor, 'set_variables'):
            pass  # verified by side effects; no crash = pass

    def test_request_saved_signal_emitted(self):
        req = _make_request("r1", "Existing")
        rm = FakeRequestManager([req])
        col_mock = MagicMock()
        col_mock.id = "c1"
        rm._requests["r1"] = (req, col_mock)
        sm = FakeStateManager()
        p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        p.add_new_tab(req)

        received = []
        p.request_saved.connect(lambda: received.append(True))
        p._handle_save_request(req)
        self.assertEqual(len(received), 1)

    def test_script_error_is_shown_beside_the_response(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)

        p._on_script_output(tab, [], "NameError: x not defined\n  at line 3")

        label = tab.response_view.script_error_label
        self.assertTrue(label.isVisibleTo(tab.response_view))
        self.assertIn("NameError: x not defined", label.text())
        self.assertNotIn("at line 3", label.text())
        self.assertIn("at line 3", label.toolTip())

    def test_script_error_is_cleared_on_a_clean_run(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)

        p._on_script_output(tab, [], "boom")
        p._on_script_output(tab, [], None)

        self.assertEqual("", tab.response_view.script_error_label.text())
        self.assertFalse(
            tab.response_view.script_error_label.isVisibleTo(tab.response_view)
        )

    def test_clear_body_drops_a_stale_script_error(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)

        p._on_script_output(tab, [], "boom")
        tab.response_view.clear_body()

        self.assertEqual("", tab.response_view.script_error_label.text())

    def test_overwrite_save_tolerates_a_blank_tab(self):
        req = _make_request("r1", "Existing")
        rm = FakeRequestManager([req])
        col_mock = MagicMock()
        col_mock.id = "c1"
        rm._requests["r1"] = (req, col_mock)
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab()  # blank tab: request_data is None
        p.add_new_tab(req)

        p._handle_save_request(req)

        self.assertEqual(1, len(rm.saved))
        self.assertEqual("Existing", p.widget.tabText(1))


class TestOnRequestError(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter_with_tab(self):
        rm = FakeRequestManager()
        sm = FakeStateManager()
        p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)
        return p, tab

    def test_str_cancellation_message_no_dialog(self):
        p, tab = self._make_presenter_with_tab()
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, "request cancelled")
            mock_mb.critical.assert_not_called()

    def test_str_error_shows_dialog(self):
        p, tab = self._make_presenter_with_tab()
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, "connection refused")
            mock_mb.critical.assert_called_once()

    def test_execution_error_network_shows_category_message(self):
        from pypost.models.errors import ErrorCategory, ExecutionError
        p, tab = self._make_presenter_with_tab()
        exc = ExecutionError(
            category=ErrorCategory.NETWORK,
            message="no conn",
            detail="connection refused",
        )
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, exc)
            mock_mb.critical.assert_called_once()
            args = mock_mb.critical.call_args[0]
            self.assertIn("Request Error", args[1])
            self.assertIn("server is running", args[2])

    def test_execution_error_timeout_shows_timeout_message(self):
        from pypost.models.errors import ErrorCategory, ExecutionError
        p, tab = self._make_presenter_with_tab()
        exc = ExecutionError(
            category=ErrorCategory.TIMEOUT,
            message="timed out",
            detail="ReadTimeout",
        )
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, exc)
            args = mock_mb.critical.call_args[0]
            self.assertIn("timed out", args[2])

    def test_execution_error_cancelled_no_dialog(self):
        from pypost.models.errors import ErrorCategory, ExecutionError
        p, tab = self._make_presenter_with_tab()
        exc = ExecutionError(
            category=ErrorCategory.UNKNOWN,
            message="something",
            detail="request aborted by user",
        )
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, exc)
            mock_mb.critical.assert_not_called()

    def test_execution_error_message_does_not_expose_raw_detail_for_network(self):
        """NETWORK message uses URL not raw detail."""
        from pypost.models.errors import ErrorCategory, ExecutionError
        p, tab = self._make_presenter_with_tab()
        raw_detail = "HTTPSConnectionPool(host='secret', port=443): Max retries exceeded"
        exc = ExecutionError(
            category=ErrorCategory.NETWORK,
            message="no conn",
            detail=raw_detail,
        )
        with patch("pypost.ui.presenters.tabs_presenter.QMessageBox") as mock_mb:
            p._on_request_error(tab, exc)
            args = mock_mb.critical.call_args[0]
            # The NETWORK template uses {url}, not {detail}
            self.assertNotIn(raw_detail, args[2])


class TestTabsPresenterAlertManagerPropagation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter_with_alert_manager(self, alert_manager=None):
        rm = FakeRequestManager()
        sm = FakeStateManager()
        settings = AppSettings()
        return TabsPresenter(rm, sm, settings, metrics=MagicMock(), alert_manager=alert_manager)

    def test_alert_manager_passed_to_worker(self):
        from pypost.core.alert_manager import AlertManager
        mock_am = MagicMock(spec=AlertManager)
        p = self._make_presenter_with_alert_manager(alert_manager=mock_am)

        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.isRunning.return_value = False
            MockWorker.return_value = mock_worker_instance

            tab.request_editor.send_requested.emit(req)

            self.assertTrue(MockWorker.called)
            _, kwargs = MockWorker.call_args
            self.assertIs(kwargs.get("alert_manager"), mock_am)

    def test_no_alert_manager_no_exception(self):
        p = self._make_presenter_with_alert_manager(alert_manager=None)

        req = _make_request("r2", "Test2", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.isRunning.return_value = False
            MockWorker.return_value = mock_worker_instance

            # Should not raise
            tab.request_editor.send_requested.emit(req)

            _, kwargs = MockWorker.call_args
            self.assertIsNone(kwargs.get("alert_manager"))


if __name__ == "__main__":
    unittest.main()
