import logging

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QSplitter,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.ui.collection_item_dialogs import (
    prompt_clean_sibling_tab_reload,
    prompt_dirty_sibling_tab_reload,
    show_request_error,
    show_request_failed_error,
)

from pypost.core.alert_manager import AlertManager
from pypost.core.curl_generator import CurlGenerator
from pypost.core.request_sync import (
    copy_request_for_isolated_tab,
    is_tab_dirty,
    persisted_fields_equal,
    snapshot_persisted_fields,
)
from pypost.core.history_manager import HistoryManager
from pypost.core.metrics import MetricsManager
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.template_service import TemplateService
from pypost.core.worker import RequestWorker
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.ui.request_save_orchestrator import (
    RequestSaveOrchestrator,
    SaveAction,
    StaleCheckContext,
)
from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView

logger = logging.getLogger(__name__)

_ERROR_MESSAGES = {
    ErrorCategory.NETWORK: (
        "Could not connect to {url}. Check that the server is running and reachable."
    ),
    ErrorCategory.TIMEOUT: (
        "Request to {url} timed out. Try increasing the timeout or check server load."
    ),
    ErrorCategory.TEMPLATE: (
        "Template rendering failed: {detail}. Check variable names and syntax."
    ),
    ErrorCategory.BODY: (
        "Could not convert YAML body to JSON: {detail}. Check YAML syntax and structure."
    ),
    ErrorCategory.SCRIPT: ("Post-script execution failed: {detail}. Review the script for errors."),
    ErrorCategory.HISTORY: ("History could not be recorded: {detail}."),
    ErrorCategory.UNKNOWN: ("An unexpected error occurred: {detail}."),
}


class RequestTab(QWidget):
    """Container for a single RequestWidget + ResponseView pair."""

    def __init__(
        self,
        request_data: RequestData | None = None,
        metrics: MetricsManager | None = None,
    ) -> None:
        super().__init__()
        self.request_data = request_data
        self.persisted_baseline: RequestData | None = None
        self.stale_persisted = False
        self.layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Vertical)

        self.request_editor = RequestWidget(request_data, metrics=metrics)
        self.response_view = ResponseView(metrics=metrics)

        self.splitter.addWidget(self.request_editor)
        self.splitter.addWidget(self.response_view)
        self.layout.addWidget(self.splitter)

        self.worker: RequestWorker | None = None


class TabBarWithAddButton(QTabBar):
    """Tab bar that emits layout_changed so '+' button can be repositioned."""

    layout_changed = Signal()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.layout_changed.emit()

    def tabLayoutChange(self) -> None:
        super().tabLayoutChange()
        self.layout_changed.emit()


class TabsPresenter(QObject):
    """Owns the QTabWidget: opening, closing, restoring tabs and worker lifecycle."""

    variable_set_requested = Signal(object, str)  # (key: str | None, value: str)
    env_update_requested = Signal(object)  # payload: dict (from RequestWorker)
    request_saved = Signal()  # after save, triggers collections tree refresh
    request_save_as_completed = Signal(object, str)  # RequestData, collection_id
    request_persisted = Signal(str, object, object)  # id, snapshot, source_tab
    request_executed = Signal()  # emitted after each completed request

    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,
        template_service: TemplateService | None = None,
        alert_manager: AlertManager | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._settings = settings
        self._metrics = metrics
        self._history_manager = history_manager
        self._template_service = template_service
        self._alert_manager = alert_manager
        logger.debug("TabsPresenter: alert_manager_injected=%s", alert_manager is not None)
        self._save_orchestrator = RequestSaveOrchestrator(
            request_manager,
            state_manager,
            settings,
            metrics=metrics,
        )
        self._current_variables: dict = {}
        self._current_hidden_keys: set = set()

        self._tab_bar = TabBarWithAddButton()
        self._tab_bar.setExpanding(False)

        self._tabs = QTabWidget()
        self._tabs.setTabBar(self._tab_bar)
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self.close_tab)

        self._add_tab_btn = QPushButton("+", self._tabs)
        self._add_tab_btn.setToolTip("New Tab (Ctrl+N)")
        self._add_tab_btn.setFixedSize(24, 24)
        self._add_tab_btn.clicked.connect(lambda: self.handle_new_tab("plus_button"))
        self._tab_bar.layout_changed.connect(self._position_add_tab_button)
        self._position_add_tab_button()
        self.request_persisted.connect(self._on_request_persisted)

    @property
    def widget(self) -> QTabWidget:
        return self._tabs

    def add_new_tab(self, request_data: RequestData | None = None, save_state: bool = True) -> None:
        if request_data is not None:
            request_data = copy_request_for_isolated_tab(request_data)
        tab = RequestTab(request_data, metrics=self._metrics)

        if hasattr(tab.request_editor, "body_edit"):
            tab.request_editor.body_edit.update_indent_size(self._settings.indent_size)
        if hasattr(tab.response_view, "set_indent_size"):
            tab.response_view.set_indent_size(self._settings.indent_size)

        if self._current_variables:
            if hasattr(tab.request_editor, "set_variables"):
                tab.request_editor.set_variables(self._current_variables)
            if hasattr(tab.response_view, "set_env_keys"):
                tab.response_view.set_env_keys(
                    list(self._current_variables.keys()),
                )
        if self._current_hidden_keys:
            if hasattr(tab.request_editor, "set_hidden_keys"):
                tab.request_editor.set_hidden_keys(
                    self._current_hidden_keys,
                )

        self._wire_tab_signals(tab)

        if request_data:
            tab.persisted_baseline = snapshot_persisted_fields(request_data)

        name = request_data.name if request_data else "New Request"
        self._tabs.addTab(tab, name)
        self._tabs.setCurrentWidget(tab)
        self._position_add_tab_button()

        if save_state:
            self.save_tabs_state()

    def close_tab(self, index: int) -> None:
        self._tabs.removeTab(index)
        if self._tabs.count() == 0:
            self.add_new_tab(save_state=False)
        self._position_add_tab_button()
        self.save_tabs_state()

    def restore_tabs(self) -> None:
        """Restores tabs from StateManager."""
        tabs_restored = False
        restored_count = 0
        for request_id in self._state_manager.get_open_tabs():
            result = self._request_manager.find_request(request_id)
            if result:
                found_request, _ = result
                self.add_new_tab(
                    copy_request_for_isolated_tab(found_request),
                    save_state=False,
                )
                tabs_restored = True
                restored_count += 1
            else:
                logger.warning("restore_tabs_request_not_found request_id=%s", request_id)

        if not tabs_restored:
            self.add_new_tab(save_state=False)
            logger.info("restore_tabs_no_saved_tabs opened_blank_tab=true")
        else:
            logger.info("restore_tabs_completed restored_count=%d", restored_count)

    def save_tabs_state(self) -> None:
        """Persists open tab IDs to StateManager."""
        open_ids = []
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_data and tab.request_data.id:
                open_ids.append(tab.request_data.id)
        self._state_manager.set_open_tabs(open_ids)

    def on_env_variables_changed(self, variables: dict) -> None:
        """Pushes new env vars to all open tabs."""
        self._current_variables = variables
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, "set_variables"):
                    tab.request_editor.set_variables(variables)
                if hasattr(tab.response_view, "set_env_keys"):
                    keys = list(variables.keys()) if variables else None
                    tab.response_view.set_env_keys(keys)

    def on_env_keys_changed(self, keys: list | None) -> None:
        """Pushes env key list to all ResponseView widgets."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.response_view, "set_env_keys"):
                    tab.response_view.set_env_keys(keys)

    def on_env_hidden_keys_changed(
        self,
        hidden_keys: set,
    ) -> None:
        """Pushes hidden-key set to all open tabs."""
        self._current_hidden_keys = hidden_keys
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, "set_hidden_keys"):
                    tab.request_editor.set_hidden_keys(hidden_keys)

    def rename_request_tabs(self, request_id: str, new_name: str) -> None:
        """Updates tab labels after a request rename."""
        self._sync_tab_labels_for_request(request_id, new_name)
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, RequestTab)
                and tab.request_data
                and tab.request_data.id == request_id
                and tab.persisted_baseline is not None
            ):
                tab.persisted_baseline.name = new_name

    def close_tabs_for_request_ids(self, request_ids: list) -> None:
        """Closes tabs that reference deleted collection requests."""
        if not request_ids:
            return
        ids_to_close = set(request_ids)
        indices_to_close = []
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, RequestTab)
                and tab.request_data
                and tab.request_data.id in ids_to_close
            ):
                indices_to_close.append(i)
        for index in reversed(indices_to_close):
            self._tabs.removeTab(index)
        if self._tabs.count() == 0:
            self.add_new_tab(save_state=False)
        self._position_add_tab_button()
        self.save_tabs_state()
        logger.info(
            "close_tabs_for_deleted_requests closed_count=%d request_ids=%s",
            len(indices_to_close),
            sorted(ids_to_close),
        )

    def apply_settings(self, settings: AppSettings) -> None:
        """Updates font/indent in all tabs."""
        self._settings = settings
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, "body_edit"):
                    tab.request_editor.body_edit.update_indent_size(settings.indent_size)
                    tab.request_editor.body_edit.reformat_text()
                if hasattr(tab.response_view, "set_indent_size"):
                    tab.response_view.set_indent_size(settings.indent_size)

    def handle_new_tab(self, source: str = "unknown") -> None:
        tabs_before = self._tabs.count()
        logger.info("new_tab_action_triggered source=%s tabs_before=%d", source, tabs_before)
        if self._metrics:
            self._metrics.track_gui_new_tab_action(source)
        self.add_new_tab()

    def handle_close_tab(self) -> None:
        current_index = self._tabs.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)

    def handle_next_tab(self) -> None:
        count = self._tabs.count()
        if count > 0:
            self._tabs.setCurrentIndex((self._tabs.currentIndex() + 1) % count)

    def handle_previous_tab(self) -> None:
        count = self._tabs.count()
        if count > 0:
            self._tabs.setCurrentIndex((self._tabs.currentIndex() - 1) % count)

    def handle_switch_to_tab(self, index: int) -> None:
        if 0 <= index < self._tabs.count():
            self._tabs.setCurrentIndex(index)

    def handle_send_request_global(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.on_send()

    def handle_focus_url(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.url_input.setFocus()
            tab.request_editor.url_input.selectAll()

    def handle_switch_to_params_global(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.detail_tabs.setCurrentIndex(0)

    def handle_switch_to_headers_global(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.detail_tabs.setCurrentIndex(1)

    def handle_switch_to_body_global(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.detail_tabs.setCurrentIndex(2)

    def handle_switch_to_script_global(self) -> None:
        tab = self._current_tab()
        if tab:
            tab.request_editor.detail_tabs.setCurrentIndex(3)

    def _current_tab(self) -> RequestTab | None:
        tab = self._tabs.currentWidget()
        return tab if isinstance(tab, RequestTab) else None

    def _wire_tab_signals(self, tab: RequestTab) -> None:
        """Connects tab's internal signals to self."""
        tab.request_editor.send_requested.connect(self._handle_send_request)
        tab.request_editor.save_requested.connect(self._handle_save_request)
        tab.request_editor.save_as_requested.connect(self._handle_save_as_request)
        tab.request_editor.copy_curl_requested.connect(self._handle_copy_curl_request)
        tab.response_view.variable_set_requested.connect(self.variable_set_requested)

    def _handle_send_request(self, request_data: RequestData) -> None:
        sender_tab = None
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_editor == self.sender():
                sender_tab = tab
                break

        if not sender_tab:
            return

        if sender_tab.worker is not None and not sender_tab.worker.isRunning():
            logger.debug(
                "stale_worker_cleared method=%s url=%s",
                request_data.method,
                request_data.url,
            )
            sender_tab.worker = None

        if sender_tab.worker is not None and sender_tab.worker.isRunning():
            logger.info(
                "request_stop_requested method=%s url=%s",
                request_data.method,
                request_data.url,
            )
            sender_tab.worker.stop()
            sender_tab.request_editor.send_btn.setEnabled(False)
            sender_tab.request_editor.send_btn.setText("Stopping...")
            return

        logger.info(
            "request_send_initiated method=%s url=%s request_id=%s",
            request_data.method,
            request_data.url,
            request_data.id,
        )
        if self._metrics:
            self._metrics.track_request_sent(request_data.method)

        sender_tab.response_view.clear_body()
        sender_tab.request_editor.send_btn.setText("Stop")

        collection_name = None
        result = self._request_manager.find_request(request_data.id)
        if result:
            _, found_collection = result
            collection_name = found_collection.name

        worker = RequestWorker(
            request_data,
            variables=self._current_variables,
            hidden_keys=self._current_hidden_keys,
            metrics=self._metrics,
            history_manager=self._history_manager,
            collection_name=collection_name,
            template_service=self._template_service,
            alert_manager=self._alert_manager,
            default_retry_policy=self._settings.default_retry_policy,
        )
        worker.finished.connect(lambda resp: self._on_request_finished(sender_tab, resp))
        worker.error.connect(lambda err: self._on_request_error(sender_tab, err))
        worker.env_update.connect(lambda vars: self.env_update_requested.emit(vars))
        worker.script_output.connect(
            lambda logs, err: self._on_script_output(sender_tab, logs, err)
        )
        worker.chunk_received.connect(lambda chunk: self._on_chunk_received(sender_tab, chunk))
        worker.headers_received.connect(
            lambda status, headers: self._on_headers_received(sender_tab, status, headers)
        )
        worker.retry_attempt.connect(
            lambda attempt, max_r, _err, tab=sender_tab: self._on_retry_attempt(tab, attempt, max_r)
        )
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        sender_tab.worker = worker
        worker.start()

    def load_request_from_history(self, request_data: RequestData) -> None:
        """Opens a new scratch tab pre-populated with data from a history entry."""
        logger.info(
            "history_request_loaded_into_editor method=%s url=%s",
            request_data.method,
            request_data.url,
        )
        if self._metrics:
            self._metrics.track_history_load_into_editor()
        self.add_new_tab(request_data)

    def _on_request_finished(self, tab: RequestTab, response) -> None:
        method = tab.request_data.method if tab.request_data else "UNKNOWN"
        logger.info(
            "request_finished method=%s status_code=%s elapsed_time=%.3fs size=%s",
            method,
            response.status_code,
            response.elapsed_time,
            response.size,
        )
        if self._metrics:
            self._metrics.track_response_received(method, str(response.status_code))
        tab.response_view.display_response(response)
        self._reset_tab_ui_state(tab)
        tab.response_view.status_label.setText(f"Status: {response.status_code}")
        tab.response_view.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        tab.response_view.size_label.setText(f"Size: {response.size} bytes")
        self.request_executed.emit()

    def _on_request_error(self, tab: RequestTab, error) -> None:
        self._reset_tab_ui_state(tab)

        # Cancellation path (still a plain string)
        if isinstance(error, str):
            if "cancelled" in error.lower() or "aborted" in error.lower():
                logger.info("request_cancelled error_msg=%s", error)
                return
            logger.error("request_error error_msg=%s", error)
            show_request_failed_error(self._tabs, error)
            return

        # Structured ExecutionError path
        if isinstance(error, ExecutionError):
            if error.category == ErrorCategory.CANCELLED:
                logger.info("request_cancelled category=%s", error.category)
                return

            url = tab.request_data.url if tab.request_data else ""
            template = _ERROR_MESSAGES.get(error.category, _ERROR_MESSAGES[ErrorCategory.UNKNOWN])
            user_msg = template.format(url=url, detail=error.detail or error.message)

            logger.error(
                "request_error category=%s message=%s detail=%s",
                error.category,
                error.message,
                error.detail,
            )
            show_request_error(self._tabs, user_msg)

    def _on_script_output(self, tab: RequestTab, logs, err) -> None:
        if logs:
            for line in str(logs).splitlines():
                logger.debug("script_output tab_id=%s line=%s", id(tab), line)
        if err:
            logger.warning("script_error tab_id=%s error=%s", id(tab), err)

    def _on_headers_received(self, tab: RequestTab, status: int, headers: dict) -> None:
        tab.response_view.status_label.setText(f"Status: {status}")

    def _on_chunk_received(self, tab: RequestTab, chunk: str) -> None:
        tab.response_view.append_body(chunk)
        current_text = tab.response_view.body_view.toPlainText()
        size_bytes = len(current_text.encode("utf-8"))
        tab.response_view.size_label.setText(f"Size: {size_bytes} bytes")

    def _on_retry_attempt(self, tab: RequestTab, attempt: int, max_retries: int) -> None:
        tab.request_editor.send_btn.setText(f"Retrying\u2026 ({attempt} of {max_retries})")

    def _reset_tab_ui_state(self, tab: RequestTab) -> None:
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")
        tab.worker = None

    def _position_add_tab_button(self) -> None:
        tab_count = self._tabs.count()
        tab_bar_rect = self._tab_bar.geometry()

        if tab_count > 0:
            last_rect = self._tab_bar.tabRect(tab_count - 1)
            x_pos = tab_bar_rect.x() + last_rect.right() + 6
            y_pos = tab_bar_rect.y() + last_rect.top()
            y_pos += max(0, (last_rect.height() - self._add_tab_btn.height()) // 2)
        else:
            x_pos = tab_bar_rect.x() + 6
            y_pos = tab_bar_rect.y()
            y_pos += max(0, (self._tab_bar.height() - self._add_tab_btn.height()) // 2)

        max_x = max(0, self._tabs.width() - self._add_tab_btn.width() - 6)
        x_pos = min(x_pos, max_x)
        self._add_tab_btn.move(x_pos, y_pos)
        self._add_tab_btn.raise_()
        self._add_tab_btn.show()

    def _find_tab_for_sender(self) -> RequestTab | None:
        sender = self.sender()
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_editor == sender:
                return tab
        return None

    def _sync_tab_labels_for_request(self, request_id: str, new_name: str) -> None:
        """Updates tab labels and in-memory names for all tabs sharing a request id."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, RequestTab)
                and tab.request_data
                and tab.request_data.id == request_id
            ):
                tab.request_data.name = new_name
                self._tabs.setTabText(i, new_name)

    def _on_request_persisted(
        self,
        request_id: str,
        snapshot: RequestData,
        source_tab: RequestTab | None,
    ) -> None:
        """Notifies sibling tabs that the persisted copy changed elsewhere."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if not isinstance(tab, RequestTab) or not tab.request_data:
                continue
            if tab.request_data.id != request_id or tab is source_tab:
                continue
            if tab.persisted_baseline and persisted_fields_equal(tab.persisted_baseline, snapshot):
                continue
            self._offer_stale_tab_resolution(tab, snapshot)
        self._sync_tab_labels_for_request(request_id, snapshot.name)

    def _offer_stale_tab_resolution(self, tab: RequestTab, snapshot: RequestData) -> None:
        """Prompts the user when a sibling tab saved a newer persisted version."""
        name = snapshot.name
        if is_tab_dirty(tab):
            if prompt_dirty_sibling_tab_reload(self._tabs, name):
                self._reload_tab_from_persisted(tab, snapshot)
            else:
                tab.stale_persisted = True
        elif prompt_clean_sibling_tab_reload(self._tabs, name):
            self._reload_tab_from_persisted(tab, snapshot)
        else:
            tab.stale_persisted = True

    def _reload_tab_from_persisted(self, tab: RequestTab, snapshot: RequestData) -> None:
        """Replaces tab editor content with the latest persisted snapshot."""
        adopted = snapshot_persisted_fields(snapshot)
        tab.request_data = adopted
        tab.persisted_baseline = snapshot_persisted_fields(snapshot)
        tab.request_editor.request_data = adopted
        tab.request_editor.load_data()
        tab.stale_persisted = False

    def _stale_context_for_tab(self, source_tab: RequestTab | None) -> StaleCheckContext | None:
        if source_tab is None:
            return None
        return StaleCheckContext(
            persisted_baseline=source_tab.persisted_baseline,
            stale_persisted=source_tab.stale_persisted,
        )

    def _apply_save_result_to_tab(self, tab: RequestTab, request: RequestData) -> None:
        tab.request_data = request
        tab.persisted_baseline = snapshot_persisted_fields(request)
        tab.stale_persisted = False

    def _handle_save_request(self, request_data: RequestData) -> None:
        source_tab = self._find_tab_for_sender()
        result = self._save_orchestrator.save_request(
            request_data,
            self._tabs,
            stale_context=self._stale_context_for_tab(source_tab),
        )
        if result.action == SaveAction.CANCELLED:
            return

        if result.action == SaveAction.OVERWRITE:
            snapshot = result.request
            if source_tab is not None and snapshot is not None:
                source_tab.request_data = snapshot
                source_tab.persisted_baseline = snapshot_persisted_fields(snapshot)
                source_tab.stale_persisted = False
            self.request_persisted.emit(request_data.id, snapshot, source_tab)
            self._sync_tab_labels_for_request(request_data.id, request_data.name)
            self.request_saved.emit()
            return

        if result.action == SaveAction.CREATED_NEW and result.request is not None:
            current_index = self._tabs.currentIndex()
            self._tabs.setTabText(current_index, result.request.name)
            tab = self._tabs.widget(current_index)
            if isinstance(tab, RequestTab):
                self._apply_save_result_to_tab(tab, result.request)
            self.save_tabs_state()
            self.request_saved.emit()

    def _handle_save_as_request(self, request_data: RequestData) -> None:
        result = self._save_orchestrator.save_as_request(request_data, self._tabs)
        if result.action != SaveAction.SAVE_AS or result.request is None:
            return

        new_request = result.request
        current_index = self._tabs.currentIndex()
        self._tabs.setTabText(current_index, new_request.name)
        tab = self._tabs.widget(current_index)
        if isinstance(tab, RequestTab):
            tab.request_data = new_request
            tab.request_editor.request_data = new_request
            self._apply_save_result_to_tab(tab, new_request)

        self.save_tabs_state()
        self.request_save_as_completed.emit(new_request, result.collection_id or "")

    def _handle_copy_curl_request(self, request_data: RequestData) -> None:
        try:
            curl_cmd = CurlGenerator.generate(
                request_data, self._current_variables, self._template_service
            )
            QApplication.clipboard().setText(curl_cmd)
            self._tabs.window().statusBar().showMessage("cURL copied to clipboard", 3000)
            logger.info("copy_curl_success request_id=%s length=%d", request_data.id, len(curl_cmd))
        except Exception as e:
            logger.error("copy_curl_failed request_id=%s error=%s", request_data.id, e)
            self._tabs.window().statusBar().showMessage(f"Failed to copy cURL: {str(e)}", 5000)
