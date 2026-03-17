import logging
import uuid

from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QSplitter,
    QPushButton, QTabBar, QMessageBox, QApplication,
)
from PySide6.QtCore import QObject, Qt, Signal

from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView
from pypost.core.worker import RequestWorker
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.metrics import MetricsManager
from pypost.core.history_manager import HistoryManager
from pypost.models.models import RequestData, Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.save_dialog import SaveRequestDialog

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
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._settings = settings
        self._metrics = metrics
        self._history_manager = history_manager
        self._current_variables: dict = {}

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
                tab.response_view.set_env_keys(list(self._current_variables.keys()))

        self._wire_tab_signals(tab)

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
                self.add_new_tab(found_request, save_state=False)
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

    def _handle_send_request(self, request_data: RequestData) -> None:
        sender_tab = None
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab) and tab.request_editor == self.sender():
                sender_tab = tab
                break

        if not sender_tab:
            return

        if sender_tab.worker and sender_tab.worker.isRunning():
            logger.info(
                "request_stop_requested method=%s url=%s",
                request_data.method, request_data.url,
            )
            sender_tab.worker.stop()
            sender_tab.request_editor.send_btn.setEnabled(False)
            sender_tab.request_editor.send_btn.setText("Stopping...")
            return

        logger.info(
            "request_send_initiated method=%s url=%s request_id=%s",
            request_data.method, request_data.url, request_data.id,
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
            metrics=self._metrics,
            history_manager=self._history_manager,
            collection_name=collection_name,
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
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.start()
        sender_tab.worker = worker

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
        if self._metrics:
            self._metrics.track_response_received(method, str(response.status_code))
        tab.response_view.display_response(response)
        self._reset_tab_ui_state(tab)
        tab.response_view.status_label.setText(f"Status: {response.status_code}")
        tab.response_view.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        tab.response_view.size_label.setText(f"Size: {response.size} bytes")
        self.request_executed.emit()

    def _on_request_error(self, tab: RequestTab, error_msg: str) -> None:
        self._reset_tab_ui_state(tab)
        if "cancelled" in error_msg.lower() or "aborted" in error_msg.lower():
            logger.info("request_cancelled error_msg=%s", error_msg)
            return
        logger.error("request_error error_msg=%s", error_msg)
        QMessageBox.critical(self._tabs, "Error", f"Request failed: {error_msg}")

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
        size_bytes = len(current_text.encode('utf-8'))
        tab.response_view.size_label.setText(f"Size: {size_bytes} bytes")

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

    def _handle_save_request(self, request_data: RequestData) -> None:
        existing_result = self._request_manager.find_request(request_data.id)

        if existing_result:
            existing_request, found_collection = existing_result
            if self._settings.confirm_overwrite_request:
                reply = QMessageBox.question(
                    self._tabs,
                    "Overwrite Request?",
                    (
                        "This will overwrite the existing request "
                        f"'{existing_request.name}'. Continue?"
                    ),
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    logger.info(
                        "save_request_overwrite_cancelled request_id=%s", request_data.id
                    )
                    return

            self._request_manager.save_request(request_data, found_collection.id)
            logger.info(
                "save_request_overwrite_succeeded request_id=%s collection_id=%s",
                request_data.id, found_collection.id,
            )
            if self._metrics:
                self._metrics.track_gui_save_action("overwrite")

            for i in range(self._tabs.count()):
                tab = self._tabs.widget(i)
                if isinstance(tab, RequestTab) and tab.request_data.id == request_data.id:
                    self._tabs.setTabText(i, request_data.name)
                    tab.request_data = request_data
                    break

            self.request_saved.emit()
            return

        collections = self._request_manager.get_collections()
        dialog = SaveRequestDialog(collections, self._tabs)
        if not dialog.exec():
            return

        request_data.name = dialog.request_name
        target_collection_id = dialog.selected_collection_id

        if not target_collection_id and dialog.new_collection_name:
            new_col = self._request_manager.create_collection(dialog.new_collection_name)
            target_collection_id = new_col.id

        if not target_collection_id:
            logger.warning("save_request_failed reason=missing_target_collection")
            return

        self._request_manager.save_request(request_data, target_collection_id)
        logger.info(
            "save_request_new_succeeded request_id=%s name=%s collection_id=%s",
            request_data.id, request_data.name, target_collection_id,
        )
        if self._metrics:
            self._metrics.track_gui_save_action("new")

        current_expanded = self._state_manager.get_expanded_collections()
        if target_collection_id not in current_expanded:
            current_expanded.append(target_collection_id)
            self._state_manager.set_expanded_collections(current_expanded)

        current_index = self._tabs.currentIndex()
        self._tabs.setTabText(current_index, request_data.name)
        tab = self._tabs.widget(current_index)
        if isinstance(tab, RequestTab):
            tab.request_data = request_data

        self.save_tabs_state()
        self.request_saved.emit()

    def _handle_save_as_request(self, request_data: RequestData) -> None:
        logger.info("save_as_flow_started source_request_id=%s", request_data.id)
        collections = self._request_manager.get_collections()
        dialog = SaveRequestDialog(collections, self._tabs)
        if not dialog.exec():
            logger.info("save_as_flow_cancelled source_request_id=%s", request_data.id)
            return

        target_collection_id = dialog.selected_collection_id
        if not target_collection_id and dialog.new_collection_name:
            new_col = self._request_manager.create_collection(dialog.new_collection_name)
            target_collection_id = new_col.id

        if not target_collection_id:
            logger.warning("save_as_flow_failed reason=missing_target_collection")
            return

        new_request = request_data.model_copy(
            deep=True,
            update={"id": str(uuid.uuid4()), "name": dialog.request_name},
        )
        self._request_manager.save_request(new_request, target_collection_id)
        logger.info(
            "save_as_flow_completed source_request_id=%s new_request_id=%s"
            " target_collection_id=%s",
            request_data.id, new_request.id, target_collection_id,
        )

        current_expanded = self._state_manager.get_expanded_collections()
        if target_collection_id not in current_expanded:
            current_expanded.append(target_collection_id)
            self._state_manager.set_expanded_collections(current_expanded)

        current_index = self._tabs.currentIndex()
        self._tabs.setTabText(current_index, new_request.name)
        tab = self._tabs.widget(current_index)
        if isinstance(tab, RequestTab):
            tab.request_data = new_request
            tab.request_editor.request_data = new_request

        self.save_tabs_state()
        self.request_saved.emit()
