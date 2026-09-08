import logging

from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QSplitter,
    QPushButton, QTabBar, QMessageBox,
)
from PySide6.QtCore import QObject, Qt, Signal

from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView
from pypost.ui.presenters.request_execution import RequestExecution
from pypost.ui.presenters.request_store import RequestStore
from pypost.ui.presenters.error_presentation import describe
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.metrics import MetricsManager
from pypost.core.history_manager import HistoryManager
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.save_dialog import SaveRequestDialog
from pypost.core.template_service import TemplateService
from pypost.core.alert_manager import AlertManager
from pypost.models.errors import ExecutionError

logger = logging.getLogger(__name__)


class RequestTab(QWidget):
    """Container for a single RequestWidget + ResponseView pair."""

    def __init__(
        self,
        request_data: RequestData | None = None,
        metrics: MetricsManager | None = None,
    ) -> None:
        super().__init__()
        self.request_data = request_data
        self.layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Vertical)

        self.request_editor = RequestWidget(request_data, metrics=metrics)
        self.response_view = ResponseView(metrics=metrics)

        self.splitter.addWidget(self.request_editor)
        self.splitter.addWidget(self.response_view)
        self.layout.addWidget(self.splitter)


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
    """Owns the QTabWidget: opening, closing and restoring tabs.

    Requests in flight belong to RequestExecution; the slots here are view
    updates driven by its signals.
    """

    variable_set_requested = Signal(object, str)   # (key: str | None, value: str)
    env_update_requested = Signal(object)           # payload: dict (from RequestWorker)
    request_saved = Signal()                        # after save, triggers collections reload
    request_executed = Signal()                     # emitted after each completed request

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
        self._execution = RequestExecution(
            settings,
            metrics=metrics,
            history_manager=history_manager,
            template_service=template_service,
            alert_manager=alert_manager,
            parent=self,
        )
        self._wire_execution_signals()
        self._store = RequestStore(request_manager, state_manager, metrics)
        logger.debug("TabsPresenter: alert_manager_injected=%s", alert_manager is not None)
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

    @property
    def widget(self) -> QTabWidget:
        return self._tabs

    def add_new_tab(
        self, request_data: RequestData | None = None, save_state: bool = True
    ) -> None:
        tab = RequestTab(request_data, metrics=self._metrics)

        if hasattr(tab.request_editor, 'body_edit'):
            tab.request_editor.body_edit.update_indent_size(self._settings.indent_size)
        if hasattr(tab.response_view, 'set_indent_size'):
            tab.response_view.set_indent_size(self._settings.indent_size)

        if self._current_variables:
            if hasattr(tab.request_editor, 'set_variables'):
                tab.request_editor.set_variables(self._current_variables)
            if hasattr(tab.response_view, 'set_env_keys'):
                tab.response_view.set_env_keys(
                    list(self._current_variables.keys()),
                )
        if self._current_hidden_keys:
            if hasattr(tab.request_editor, 'set_hidden_keys'):
                tab.request_editor.set_hidden_keys(
                    self._current_hidden_keys,
                )

        self._wire_tab_signals(tab)

        name = request_data.name if request_data else "New Request"
        self._tabs.addTab(tab, name)
        self._tabs.setCurrentWidget(tab)
        self._position_add_tab_button()

        if save_state:
            self.save_tabs_state()

    def close_tab(self, index: int) -> None:
        tab = self._tabs.widget(index)
        if tab is None:
            return

        self._tabs.removeTab(index)
        # A tab whose request is still in flight must outlive the worker: release()
        # cancels it and defers the deletion until the thread has actually ended.
        if not self._execution.release(tab, tab.deleteLater):
            tab.deleteLater()

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
                self.add_new_tab(found_request.model_copy(deep=True), save_state=False)
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

    def shutdown_workers(self) -> None:
        """Cancel and join every request worker before application teardown."""
        self._execution.shutdown()

    def on_env_variables_changed(self, variables: dict) -> None:
        """Pushes new env vars to all open tabs."""
        self._current_variables = variables
        self._execution.set_variables(variables)
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, 'set_variables'):
                    tab.request_editor.set_variables(variables)
                if hasattr(tab.response_view, 'set_env_keys'):
                    keys = list(variables.keys()) if variables else None
                    tab.response_view.set_env_keys(keys)

    def on_env_keys_changed(self, keys: list | None) -> None:
        """Pushes env key list to all ResponseView widgets."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.response_view, 'set_env_keys'):
                    tab.response_view.set_env_keys(keys)

    def on_env_hidden_keys_changed(
        self, hidden_keys: set,
    ) -> None:
        """Pushes hidden-key set to all open tabs."""
        self._current_hidden_keys = hidden_keys
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, 'set_hidden_keys'):
                    tab.request_editor.set_hidden_keys(hidden_keys)

    def rename_request_tabs(self, request_id: str, new_name: str) -> None:
        """Updates tab labels after a request rename."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, RequestTab)
                and tab.request_data
                and tab.request_data.id == request_id
            ):
                tab.request_data.name = new_name
                self._tabs.setTabText(i, new_name)

    def apply_settings(self, settings: AppSettings) -> None:
        """Updates font/indent in all tabs."""
        self._settings = settings
        self._execution.apply_settings(settings)
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, 'body_edit'):
                    tab.request_editor.body_edit.update_indent_size(settings.indent_size)
                    tab.request_editor.body_edit.reformat_text()
                if hasattr(tab.response_view, 'set_indent_size'):
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
        tab.response_view.variable_set_requested.connect(self.variable_set_requested)

    def _wire_execution_signals(self) -> None:
        """Requests report back per tab; every slot below is a view update."""
        self._execution.started.connect(self._on_request_started)
        self._execution.cancelling.connect(self._on_request_cancelling)
        self._execution.finished.connect(self._on_request_finished)
        self._execution.failed.connect(self._on_request_error)
        self._execution.script_output.connect(self._on_script_output)
        self._execution.headers_received.connect(self._on_headers_received)
        self._execution.chunk_received.connect(self._on_chunk_received)
        self._execution.retry_attempt.connect(self._on_retry_attempt)
        self._execution.env_update.connect(self.env_update_requested)

    def _handle_send_request(self, request_data: RequestData) -> None:
        sender_tab = None
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_editor == self.sender():
                sender_tab = tab
                break

        if not sender_tab:
            return

        collection_name = None
        result = self._request_manager.find_request(request_data.id)
        if result:
            _, found_collection = result
            collection_name = found_collection.name

        self._execution.send(sender_tab, request_data, collection_name)

    def _on_request_started(self, tab: RequestTab) -> None:
        tab.response_view.clear_body()
        tab.request_editor.send_btn.setText("Stop")

    def _on_request_cancelling(self, tab: RequestTab) -> None:
        tab.request_editor.send_btn.setEnabled(False)
        tab.request_editor.send_btn.setText("Stopping...")

    def load_request_from_history(self, request_data: RequestData) -> None:
        """Opens a new scratch tab pre-populated with data from a history entry."""
        logger.info(
            "history_request_loaded_into_editor method=%s url=%s",
            request_data.method, request_data.url,
        )
        if self._metrics:
            self._metrics.track_history_load_into_editor()
        self.add_new_tab(request_data)

    def _on_request_finished(self, tab: RequestTab, response) -> None:
        method = tab.request_data.method if tab.request_data else "UNKNOWN"
        logger.info(
            "request_finished method=%s status_code=%s elapsed_time=%.3fs size=%s",
            method, response.status_code, response.elapsed_time, response.size,
        )
        tab.response_view.display_response(response)
        self._reset_tab_ui_state(tab)
        tab.response_view.status_label.setText(f"Status: {response.status_code}")
        tab.response_view.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        tab.response_view.size_label.setText(f"Size: {response.size} bytes")
        self.request_executed.emit()

    def _on_request_error(self, tab: RequestTab, error) -> None:
        self._reset_tab_ui_state(tab)

        url = tab.request_data.url if tab.request_data else ""
        prompt = describe(error, url)
        if prompt is None:
            logger.info("request_cancelled error=%s", error)
            return

        if isinstance(error, ExecutionError):
            logger.error(
                "request_error category=%s message=%s detail=%s",
                error.category, error.message, error.detail,
            )
        else:
            logger.error("request_error error_msg=%s", error)
        QMessageBox.critical(self._tabs, prompt.title, prompt.message)

    def _on_script_output(self, tab: RequestTab, logs, err) -> None:
        if logs:
            for line in str(logs).splitlines():
                logger.debug("script_output tab_id=%s line=%s", id(tab), line)
        if err:
            logger.warning("script_error tab_id=%s error=%s", id(tab), err)
            tab.response_view.set_script_error(err)
        else:
            tab.response_view.clear_script_error()

    def _on_headers_received(self, tab: RequestTab, status: int, headers: dict) -> None:
        tab.response_view.status_label.setText(f"Status: {status}")

    def _on_chunk_received(self, tab: RequestTab, chunk: str) -> None:
        tab.response_view.append_body(chunk)
        current_text = tab.response_view.body_view.toPlainText()
        size_bytes = len(current_text.encode('utf-8'))
        tab.response_view.size_label.setText(f"Size: {size_bytes} bytes")

    def _on_retry_attempt(self, tab: RequestTab, attempt: int, max_retries: int) -> None:
        # Whatever the failed attempt streamed is not part of the answer. Without
        # this the next attempt appends to it and the bodies concatenate.
        tab.response_view.clear_body()
        tab.request_editor.send_btn.setText(
            f"Retrying\u2026 ({attempt} of {max_retries})"
        )

    def _reset_tab_ui_state(self, tab: RequestTab) -> None:
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")

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

    def _handle_save_request(self, request_data: RequestData) -> None:
        existing = self._store.find_existing(request_data.id)

        if existing:
            existing_request, found_collection = existing
            if (
                self._settings.confirm_overwrite_request
                and not self._confirm_overwrite(existing_request.name)
            ):
                logger.info(
                    "save_request_overwrite_cancelled request_id=%s", request_data.id
                )
                return

            self._store.overwrite(request_data, found_collection.id)
            self._relabel_tab_for(request_data)
            self.request_saved.emit()
            return

        answer = self._ask_where_to_save()
        if answer is None:
            return

        request_data.name = answer.request_name
        target_collection_id = self._store.resolve_target(
            answer.selected_collection_id, answer.new_collection_name,
        )
        if not target_collection_id:
            logger.warning("save_request_failed reason=missing_target_collection")
            return

        self._store.store(request_data, target_collection_id)
        self._adopt_into_current_tab(request_data)
        self.save_tabs_state()
        self.request_saved.emit()

    def _handle_save_as_request(self, request_data: RequestData) -> None:
        logger.info("save_as_flow_started source_request_id=%s", request_data.id)
        answer = self._ask_where_to_save()
        if answer is None:
            logger.info("save_as_flow_cancelled source_request_id=%s", request_data.id)
            return

        target_collection_id = self._store.resolve_target(
            answer.selected_collection_id, answer.new_collection_name,
        )
        if not target_collection_id:
            logger.warning("save_as_flow_failed reason=missing_target_collection")
            return

        new_request = self._store.store_copy(
            request_data, target_collection_id, answer.request_name,
        )
        self._adopt_into_current_tab(new_request, adopt_in_editor=True)
        self.save_tabs_state()
        self.request_saved.emit()

    def _ask_where_to_save(self) -> SaveRequestDialog | None:
        """The dialog itself carries the answer; None means the user cancelled."""
        dialog = SaveRequestDialog(self._store.collections(), self._tabs)
        return dialog if dialog.exec() else None

    def _confirm_overwrite(self, existing_name: str) -> bool:
        reply = QMessageBox.question(
            self._tabs,
            "Overwrite Request?",
            (
                "This will overwrite the existing request "
                f"'{existing_name}'. Continue?"
            ),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        return reply != QMessageBox.No

    def _relabel_tab_for(self, request_data: RequestData) -> None:
        """Point the tab already showing this request at the saved version."""
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, RequestTab)
                and tab.request_data
                and tab.request_data.id == request_data.id
            ):
                self._tabs.setTabText(i, request_data.name)
                tab.request_data = request_data
                return

    def _adopt_into_current_tab(
        self, request_data: RequestData, adopt_in_editor: bool = False,
    ) -> None:
        """The current tab now shows the saved request, under its saved name."""
        current_index = self._tabs.currentIndex()
        self._tabs.setTabText(current_index, request_data.name)
        tab = self._tabs.widget(current_index)
        if isinstance(tab, RequestTab):
            tab.request_data = request_data
            if adopt_in_editor:
                tab.request_editor.request_data = request_data
