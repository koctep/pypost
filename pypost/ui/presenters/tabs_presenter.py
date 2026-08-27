from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.ui.collection_item_dialogs import (
    prompt_clean_sibling_tab_reload,
    prompt_dirty_sibling_tab_reload,
    prompt_deleted_websocket_profile_tab_close,
    prompt_unsaved_draft_tab_close,
)

from pypost.core.alert_manager import AlertManager
from pypost.core.curl_generator import CurlGenerator
from pypost.core.request_persisted_fields import (
    copy_request_for_isolated_tab,
    persisted_fields_equal,
    snapshot_persisted_fields,
)
from pypost.core.websocket_persisted_fields import snapshot_websocket_persisted_fields
from pypost.core.mcp_client_persisted_fields import snapshot_mcp_client_persisted_fields
from pypost.core.websocket_registry import WebSocketRegistry
from pypost.core.mcp_client_registry import McpClientRegistry
from pypost.ui.presenters.tab_dirty import (
    connection_snapshot_from_tab,
    is_tab_dirty,
    mcp_client_snapshot_from_tab,
)
from pypost.ui.presenters.tabs_presenter_close import close_workspace_tab
from pypost.ui.presenters.tabs_presenter_request_close import (
    close_tabs_for_request_ids as close_tabs_for_request_ids_helper,
)
from pypost.ui.presenters.tabs_presenter_ws_close import (
    close_tabs_for_websocket_ids as close_tabs_for_websocket_ids_ws,
    rename_websocket_tabs as rename_websocket_tabs_ws,
)
from pypost.ui.presenters.tabs_presenter_mcp_close import (
    close_tabs_for_mcp_client_ids as close_tabs_for_mcp_client_ids_mcp,
    rename_mcp_client_tabs as rename_mcp_client_tabs_mcp,
)
from pypost.ui.presenters.tabs_presenter_draft import (
    collect_persistable_open_tab_ids,
    make_mcp_client_saved_predicate,
    make_websocket_saved_predicate,
)
from pypost.ui.presenters import tabs_presenter_hotkeys as tab_hotkeys
from pypost.ui.presenters.tabs_presenter_worker import TabsPresenterWorkerHandlers
from pypost.core.history_manager import HistoryManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.request_manager import RequestManager
from pypost.core.qt.state_manager import StateManager
from pypost.core.template_service import TemplateService
from pypost.core.qt.worker import RequestWorker
from pypost.core.mcp_client_migration import is_legacy_mcp_request, request_data_to_mcp_client
from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection
from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.request_save_orchestrator import (
    RequestSaveOrchestrator,
    SaveAction,
    StaleCheckContext,
)
from pypost.ui.websocket_save_orchestrator import WebSocketSaveOrchestrator
from pypost.ui.mcp_client_save_orchestrator import McpClientSaveOrchestrator
from pypost.ui.theme.json_syntax_theme import resolve_json_syntax_colors
from pypost.ui.widget_ids import REQUEST_TABS, set_widget_id
from pypost.ui.widgets.mcp_client import McpClientTab
from pypost.ui.widgets.new_tab_protocol_picker import (
    NewTabProtocolPicker,
    TabProtocol,
)
from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView
from pypost.ui.widgets.tab_header import PLUS_TAB_MARKER, RequestTabHeader
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

logger = logging.getLogger(__name__)

__all__ = ["PLUS_TAB_MARKER", "RequestTab", "TabsPresenter", "WebSocketTab"]


class RequestTab(QWidget):
    """Container for a single RequestWidget + ResponseView pair."""

    def __init__(
        self,
        request_data: RequestData | None = None,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        super().__init__()
        self.request_data = request_data
        self.persisted_baseline: RequestData | None = None
        self.stale_persisted = False
        self._content_layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Vertical)

        self.request_editor = RequestWidget(request_data, metrics=metrics)
        self.response_view = ResponseView(metrics=metrics)

        self.splitter.addWidget(self.request_editor)
        self.splitter.addWidget(self.response_view)
        self._content_layout.addWidget(self.splitter)

        self.worker: RequestWorker | None = None


class TabsPresenter(QObject, TabsPresenterWorkerHandlers):
    """Owns the QTabWidget: opening, closing, restoring tabs and worker lifecycle."""

    variable_set_requested = Signal(object, str)  # (key: str | None, value: str)
    env_update_requested = Signal(dict)  # payload from RequestWorker
    request_saved = Signal()  # after save, triggers collections tree refresh
    request_save_as_completed = Signal(RequestData, str)  # request, collection_id
    request_persisted = Signal(str, RequestData, RequestTab)  # id, snapshot, source_tab
    request_executed = Signal()  # emitted after each completed request
    websocket_saved = Signal()  # after WS profile save, triggers collections tree refresh
    websocket_save_as_completed = Signal(WebSocketConnection, str)  # connection, collection_id
    websocket_persisted = Signal(str, WebSocketConnection, WebSocketTab)
    mcp_client_saved = Signal()  # after MCP Client save, triggers collections tree refresh
    mcp_client_save_as_completed = Signal(McpClientConnection, str)
    mcp_client_persisted = Signal(str, McpClientConnection, McpClientTab)

    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsTrackerProtocol | None = None,
        history_manager: HistoryManager | None = None,
        template_service: TemplateService | None = None,
        alert_manager: AlertManager | None = None,
        protocol_picker: Callable[..., TabProtocol | None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._settings = settings
        self._metrics = resolve_metrics(metrics)
        self._protocol_picker = protocol_picker or NewTabProtocolPicker().prompt
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
        storage = getattr(request_manager, "storage", None)
        self._ws_registry = WebSocketRegistry(request_manager, storage)
        self._ws_save_orchestrator = WebSocketSaveOrchestrator(
            self._ws_registry,
            state_manager,
            settings,
            metrics=metrics,
        )
        self._mcp_registry = McpClientRegistry(request_manager, storage)
        self._mcp_save_orchestrator = McpClientSaveOrchestrator(
            self._mcp_registry,
            state_manager,
            settings,
            metrics=metrics,
        )
        self._current_variables: dict = {}
        self._current_hidden_keys: set = set()
        self._chunk_buffers: dict[int, list[str]] = {}
        self._chunk_flush_timers: dict[int, QTimer] = {}
        self._chunk_flush_ms = 33

        self._tabs = QTabWidget()
        set_widget_id(self._tabs, REQUEST_TABS)
        self._header = RequestTabHeader(self)
        self._header.attach(self._tabs)
        self._header.new_tab_requested.connect(
            lambda: self.handle_new_tab("plus_button"),
        )
        self._tabs.tabCloseRequested.connect(self.close_tab)
        self.request_persisted.connect(self._on_request_persisted)

    @property
    def widget(self) -> QTabWidget:
        return self._tabs

    def add_new_tab(self, request_data: RequestData | None = None, save_state: bool = True) -> None:
        if request_data is not None and is_legacy_mcp_request(request_data):
            self.open_legacy_mcp_request_tab(request_data, save_state=save_state)
            return
        if request_data is not None:
            request_data = copy_request_for_isolated_tab(request_data)
        tab = self._create_request_tab(request_data)

        if request_data:
            tab.persisted_baseline = snapshot_persisted_fields(request_data)

        name = request_data.name if request_data else "New Request"
        plus_idx = self._header.insert_index_before_plus()
        if plus_idx >= 0:
            self._tabs.insertTab(plus_idx, tab, name)
        else:
            self._tabs.addTab(tab, name)
            self._header.ensure_plus_tab()
        self._tabs.setCurrentWidget(tab)

        if save_state:
            self.save_tabs_state()

    def open_websocket_tab(
        self,
        connection: WebSocketConnection,
        save_state: bool = True,
    ) -> WebSocketTab:
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, WebSocketTab)
                and tab.connection_data
                and tab.connection_data.id == connection.id
            ):
                self._tabs.setCurrentWidget(tab)
                return tab
        return self._insert_websocket_tab(connection, save_state=save_state)

    def open_websocket_isolated_tab(
        self,
        connection: WebSocketConnection,
        *,
        save_state: bool = True,
    ) -> WebSocketTab:
        """Always insert a new WebSocket tab; never focus-dedup by profile id."""
        return self._insert_websocket_tab(connection, save_state=save_state)

    def add_blank_websocket_tab(self, *, save_state: bool = True) -> WebSocketTab:
        return self._insert_websocket_tab(WebSocketConnection(), save_state=save_state)

    def open_mcp_client_isolated_tab(
        self,
        connection: McpClientConnection,
        *,
        save_state: bool = True,
    ) -> McpClientTab:
        """Always insert a new MCP Client tab; never focus-dedup by profile id."""
        return self._insert_mcp_client_tab(connection, save_state=save_state)

    def add_blank_mcp_client_tab(self, *, save_state: bool = True) -> McpClientTab:
        return self._insert_mcp_client_tab(McpClientConnection(), save_state=save_state)

    def open_mcp_client_tab(
        self,
        connection: McpClientConnection,
        *,
        save_state: bool = True,
    ) -> McpClientTab:
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if (
                isinstance(tab, McpClientTab)
                and tab.connection_data
                and tab.connection_data.id == connection.id
            ):
                self._tabs.setCurrentWidget(tab)
                return tab
        return self._insert_mcp_client_tab(connection, save_state=save_state)

    def open_legacy_mcp_request_tab(
        self,
        request: RequestData,
        *,
        save_state: bool = True,
    ) -> McpClientTab:
        """Open a legacy method:MCP collection item as an MCP Client tab."""
        connection = request_data_to_mcp_client(request)
        return self.open_mcp_client_tab(connection, save_state=save_state)

    def _insert_mcp_client_tab(
        self,
        connection: McpClientConnection,
        *,
        save_state: bool = True,
    ) -> McpClientTab:
        presenter = McpClientPresenter(
            connection,
            env_vars=self._current_variables,
            hidden_keys=self._current_hidden_keys,
        )
        tab = McpClientTab(connection, presenter)
        if make_mcp_client_saved_predicate(self._request_manager)(connection.id):
            tab.persisted_baseline = snapshot_mcp_client_persisted_fields(connection)
        self._wire_mcp_client_tab_signals(tab)
        name = connection.name if connection.name else "New MCP Client"
        plus_idx = self._header.insert_index_before_plus()
        if plus_idx >= 0:
            self._tabs.insertTab(plus_idx, tab, name)
        else:
            self._tabs.addTab(tab, name)
            self._header.ensure_plus_tab()
        self._tabs.setCurrentWidget(tab)
        if save_state:
            self.save_tabs_state()
        return tab

    def _insert_websocket_tab(
        self,
        connection: WebSocketConnection,
        *,
        save_state: bool = True,
    ) -> WebSocketTab:
        presenter = WebSocketPresenter(
            connection=connection,
            env_vars=self._current_variables,
            hidden_keys=self._current_hidden_keys,
            metrics=self._metrics,
        )
        tab = WebSocketTab(connection=connection, presenter=presenter)
        if make_websocket_saved_predicate(self._request_manager)(connection.id):
            tab.persisted_baseline = snapshot_websocket_persisted_fields(connection)
        presenter.tab_title_changed.connect(
            lambda glyph, title, t=tab: self._on_websocket_title_changed(t, glyph, title)
        )
        self._wire_websocket_tab_signals(tab)

        name = connection.name if connection.name else "WebSocket"
        plus_idx = self._header.insert_index_before_plus()
        if plus_idx >= 0:
            self._tabs.insertTab(plus_idx, tab, name)
        else:
            self._tabs.addTab(tab, name)
            self._header.ensure_plus_tab()
        self._tabs.setCurrentWidget(tab)

        if save_state:
            self.save_tabs_state()
        return tab

    def _on_websocket_title_changed(self, tab: WebSocketTab, glyph: str, title: str) -> None:
        idx = self._tabs.indexOf(tab)
        if idx >= 0:
            self._header.set_tab_label(idx, f"{glyph} {title}".strip())

    def _ensure_current_is_navigable(self, preferred_index: int) -> None:
        """If current is not a request tab, select preferred or last navigable."""
        indices = self._header.navigable_tab_indices()
        current = self._tabs.currentIndex()
        if indices and current not in indices:
            preferred = preferred_index
            if preferred not in indices:
                preferred = indices[-1]
            self._tabs.setCurrentIndex(preferred)

    def close_tab(self, index: int) -> None:
        close_workspace_tab(
            self, index, prompt_close=prompt_unsaved_draft_tab_close,
        )

    def restore_tabs(self) -> None:
        """Restores tabs from StateManager."""
        from pypost.core.websocket_registry import WebSocketRegistry
        from pypost.core.mcp_client_registry import McpClientRegistry

        tabs_restored = False
        restored_count = 0
        storage = getattr(self._request_manager, "storage", None)
        ws_registry = WebSocketRegistry(self._request_manager, storage)
        mcp_registry = McpClientRegistry(self._request_manager, storage)
        for tab_id in self._state_manager.get_open_tabs():
            item_match = ws_registry.find_item(tab_id)
            if item_match is not None:
                kind, item_data, _ = item_match
                if kind == "websocket" and isinstance(item_data, WebSocketConnection):
                    self.open_websocket_tab(item_data, save_state=False)
                    tabs_restored = True
                    restored_count += 1
                elif kind == "request" and isinstance(item_data, RequestData):
                    self.add_new_tab(copy_request_for_isolated_tab(item_data), save_state=False)
                    tabs_restored = True
                    restored_count += 1
                continue

            mcp_match = mcp_registry.find_item(tab_id)
            if mcp_match is not None:
                kind, item_data, _ = mcp_match
                if kind == "mcp_client" and isinstance(item_data, McpClientConnection):
                    self.open_mcp_client_tab(item_data, save_state=False)
                    tabs_restored = True
                    restored_count += 1
                continue

            result = self._request_manager.find_request(tab_id)
            if result:
                found_request, _ = result
                self.add_new_tab(
                    copy_request_for_isolated_tab(found_request),
                    save_state=False,
                )
                tabs_restored = True
                restored_count += 1
            else:
                logger.warning("restore_tabs_item_not_found item_id=%s", tab_id)

        if not tabs_restored:
            self.add_new_tab(save_state=False)
            logger.info("restore_tabs_no_saved_tabs opened_blank_tab=true")
        else:
            logger.info("restore_tabs_completed restored_count=%d", restored_count)

    def save_tabs_state(self) -> None:
        """Persists open tab IDs to StateManager."""
        open_ids = collect_persistable_open_tab_ids(
            self._tabs,
            websocket_id_is_saved=make_websocket_saved_predicate(self._request_manager),
            mcp_client_id_is_saved=make_mcp_client_saved_predicate(
                self._request_manager
            ),
        )
        self._state_manager.set_open_tabs(open_ids)

    def on_env_variables_changed(self, variables: dict) -> None:
        """React to env variable changes and push snapshots into open tabs.

        Connected from EnvPresenter.env_variables_changed in main_window_signals.
        Caches variables for new tabs and calls set_variables on each tab.
        See doc/dev/variable_propagation.md.
        """
        self._current_variables = variables
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, "set_variables"):
                    tab.request_editor.set_variables(variables)
                if hasattr(tab.response_view, "set_env_keys"):
                    keys = list(variables.keys()) if variables else None
                    tab.response_view.set_env_keys(keys)
            else:
                setter = getattr(getattr(tab, "presenter", None), "set_variables", None)
                if callable(setter):
                    setter(variables)

    def on_env_keys_changed(self, keys: object) -> None:
        """Pushes env key list to all ResponseView widgets."""
        if keys is not None and not isinstance(keys, list):
            logger.warning(
                "env_keys_update_ignored reason=invalid_payload_type type=%s",
                type(keys).__name__,
            )
            return
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
            else:
                setter = getattr(
                    getattr(tab, "presenter", None), "set_hidden_keys", None
                )
                if callable(setter):
                    setter(hidden_keys)

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

    def rename_websocket_tabs(self, ws_id: str, new_name: str) -> None:
        rename_websocket_tabs_ws(self, ws_id, new_name)

    def rename_mcp_client_tabs(self, profile_id: str, new_name: str) -> None:
        rename_mcp_client_tabs_mcp(self, profile_id, new_name)

    def close_tabs_for_request_ids(self, request_ids: list) -> None:
        close_tabs_for_request_ids_helper(self, request_ids)

    def close_tabs_for_websocket_ids(
        self,
        ws_ids: list[str],
        *,
        prompt: Callable[[QWidget, str, bool, bool], bool] | None = None,
    ) -> None:
        close_tabs_for_websocket_ids_ws(
            self,
            ws_ids,
            prompt=prompt or prompt_deleted_websocket_profile_tab_close,
        )

    def close_tabs_for_mcp_client_ids(
        self,
        profile_ids: list[str],
        *,
        prompt: Callable[[QWidget, str, bool, bool], bool] | None = None,
    ) -> None:
        close_tabs_for_mcp_client_ids_mcp(
            self,
            profile_ids,
            prompt=prompt or prompt_deleted_websocket_profile_tab_close,
        )

    def set_alert_manager(self, alert_manager: AlertManager | None) -> None:
        self._alert_manager = alert_manager
        logger.debug(
            "TabsPresenter: alert_manager_updated=%s", alert_manager is not None
        )

    def apply_settings(self, settings: AppSettings) -> None:
        """Updates indent, JSON syntax colors, and body reformat in all tabs."""
        self._settings = settings
        json_colors = resolve_json_syntax_colors(theme=settings.theme)
        for i in range(self._tabs.count()):
            tab = self._tabs.widget(i)
            if isinstance(tab, RequestTab):
                if hasattr(tab.request_editor, "body_edit"):
                    tab.request_editor.body_edit.update_indent_size(settings.indent_size)
                    tab.request_editor.body_edit.reformat_text()
                if hasattr(tab.request_editor, "json_highlighter"):
                    tab.request_editor.json_highlighter.set_colors(json_colors)
                if hasattr(tab.response_view, "set_indent_size"):
                    tab.response_view.set_indent_size(settings.indent_size)
                if hasattr(tab.response_view, "json_highlighter"):
                    tab.response_view.json_highlighter.set_colors(json_colors)

    def handle_new_tab(self, source: str = "unknown") -> None:
        tabs_before = self._request_tab_count()
        logger.info("new_tab_action_triggered source=%s tabs_before=%d", source, tabs_before)
        protocol = self._protocol_picker(self._tabs)
        if protocol is None:
            logger.info("new_tab_action_cancelled source=%s", source)
            return
        self.open_blank_tab(protocol, source)

    def open_blank_tab(self, protocol: TabProtocol, source: str) -> None:
        logger.info(
            "new_tab_action_completed source=%s protocol=%s",
            source,
            protocol.value,
        )
        self._metrics.track_gui_new_tab_action(source, protocol=protocol.value)
        if protocol == TabProtocol.WEBSOCKET:
            self.add_blank_websocket_tab()
            return
        if protocol == TabProtocol.MCP_CLIENT:
            self.add_blank_mcp_client_tab()
            return
        self.add_new_tab()

    def handle_close_tab(self) -> None:
        current_index = self._tabs.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)

    def handle_next_tab(self) -> None:
        indices = self._header.navigable_tab_indices()
        if not indices:
            return
        current = self._tabs.currentIndex()
        if current not in indices:
            self._tabs.setCurrentIndex(indices[0])
            return
        pos = indices.index(current)
        self._tabs.setCurrentIndex(indices[(pos + 1) % len(indices)])

    def handle_previous_tab(self) -> None:
        indices = self._header.navigable_tab_indices()
        if not indices:
            return
        current = self._tabs.currentIndex()
        if current not in indices:
            self._tabs.setCurrentIndex(indices[-1])
            return
        pos = indices.index(current)
        self._tabs.setCurrentIndex(indices[(pos - 1) % len(indices)])

    def handle_switch_to_tab(self, index: int) -> None:
        if 0 <= index < self._tabs.count() and not self._header.is_plus_tab_index(index):
            self._tabs.setCurrentIndex(index)

    def active_tab_kind(self) -> TabProtocol | None:
        return tab_hotkeys.active_tab_kind(self)

    def handle_send_request_global(self) -> None:
        tab_hotkeys.handle_send_request_global(self)

    def handle_websocket_connect_global(self) -> None:
        tab_hotkeys.handle_websocket_connect_global(self)

    def handle_websocket_send_global(self) -> None:
        tab_hotkeys.handle_websocket_send_global(self)

    def handle_websocket_format_json_global(self) -> None:
        tab_hotkeys.handle_websocket_format_json_global(self)

    def handle_mcp_client_connect_global(self) -> None:
        tab_hotkeys.handle_mcp_client_connect_global(self)

    def handle_mcp_client_invoke_global(self) -> None:
        tab_hotkeys.handle_mcp_client_invoke_global(self)

    def handle_mcp_client_send_global(self) -> None:
        tab_hotkeys.handle_mcp_client_send_global(self)

    def handle_focus_url(self) -> None:
        tab_hotkeys.handle_focus_url(self)

    def handle_switch_to_params_global(self) -> None:
        tab_hotkeys.handle_switch_to_params_global(self)

    def handle_switch_to_headers_global(self) -> None:
        tab_hotkeys.handle_switch_to_headers_global(self)

    def handle_switch_to_body_global(self) -> None:
        tab_hotkeys.handle_switch_to_body_global(self)

    def handle_switch_to_script_global(self) -> None:
        tab_hotkeys.handle_switch_to_script_global(self)

    def _current_tab(self) -> RequestTab | None:
        return tab_hotkeys.current_request_tab(self)

    def _create_request_tab(self, request_data: RequestData | None) -> RequestTab:
        """Creates a RequestTab and wires all per-tab signals."""
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
        if self._template_service and hasattr(
            tab.request_editor, "set_template_service"
        ):
            tab.request_editor.set_template_service(self._template_service)

        self._wire_tab_signals(tab)
        return tab

    def _wire_websocket_tab_signals(self, tab: WebSocketTab) -> None:
        tab.save_requested.connect(
            lambda conn, t=tab: self._handle_save_websocket(t, conn)
        )
        tab.save_as_requested.connect(
            lambda conn, t=tab: self._handle_save_as_websocket(t, conn)
        )

    def _wire_mcp_client_tab_signals(self, tab: McpClientTab) -> None:
        tab.save_requested.connect(
            lambda conn, t=tab: self._handle_save_mcp_client(t, conn)
        )
        tab.save_as_requested.connect(
            lambda conn, t=tab: self._handle_save_as_mcp_client(t, conn)
        )

    def _wire_tab_signals(self, tab: RequestTab) -> None:
        """Connects tab's internal signals to self."""
        tab.request_editor.send_requested.connect(
            lambda data, t=tab: self._handle_send_request(t, data)
        )
        tab.request_editor.save_requested.connect(
            lambda data, t=tab: self._handle_save_request(t, data)
        )
        tab.request_editor.save_as_requested.connect(
            lambda data, t=tab: self._handle_save_as_request(t, data)
        )
        tab.request_editor.copy_curl_requested.connect(self._handle_copy_curl_request)
        tab.response_view.variable_set_requested.connect(self.variable_set_requested)

    def _handle_send_request(self, sender_tab: RequestTab, request_data: RequestData) -> None:
        if sender_tab.worker is not None and not sender_tab.worker.isRunning():
            self._clear_tab_worker(sender_tab, reason="stale", request_data=request_data)

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
        self._metrics.track_request_sent(request_data.method)

        sender_tab.response_view.clear_body()
        self._discard_chunk_buffer(sender_tab)
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
            max_response_bytes=self._settings.max_response_bytes,
        )
        worker.request_finished.connect(
            lambda resp: self._on_request_finished(sender_tab, resp)
        )
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
        # Deferred deletion follows native thread termination on every exit path.
        worker.finished.connect(worker.deleteLater)
        sender_tab.worker = worker
        worker.start()

    def load_request_from_history(self, request_data: RequestData) -> None:
        """Opens a new scratch tab pre-populated with data from a history entry."""
        logger.info(
            "history_request_loaded_into_editor method=%s url=%s",
            request_data.method,
            request_data.url,
        )
        self._metrics.track_history_load_into_editor()
        self.add_new_tab(request_data)

    def _request_tab_count(self) -> int:
        return sum(
            1
            for i in range(self._tabs.count())
            if isinstance(
                self._tabs.widget(i), (RequestTab, WebSocketTab, McpClientTab)
            )
        )

    def _index_of_tab(self, tab: RequestTab | WebSocketTab) -> int | None:
        for i in range(self._tabs.count()):
            if self._tabs.widget(i) is tab:
                return i
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
                self._header.set_tab_label(i, new_name)

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

    def _stale_context_for_websocket_tab(
        self, source_tab: WebSocketTab
    ) -> StaleCheckContext | None:
        return StaleCheckContext(
            persisted_baseline=source_tab.persisted_baseline,
            stale_persisted=source_tab.stale_persisted,
        )

    def _apply_ws_save_result_to_tab(
        self, tab: WebSocketTab, connection: WebSocketConnection
    ) -> None:
        tab.connection_data = connection
        tab.persisted_baseline = snapshot_websocket_persisted_fields(connection)
        tab.stale_persisted = False
        tab.presenter.connection = connection
        tab.connection_editor.load_connection(connection)

    def _stale_context_for_mcp_client_tab(
        self, source_tab: McpClientTab
    ) -> StaleCheckContext | None:
        return StaleCheckContext(
            persisted_baseline=source_tab.persisted_baseline,
            stale_persisted=source_tab.stale_persisted,
        )

    def _apply_mcp_save_result_to_tab(
        self, tab: McpClientTab, connection: McpClientConnection
    ) -> None:
        tab.connection_data = connection
        tab.persisted_baseline = snapshot_mcp_client_persisted_fields(connection)
        tab.stale_persisted = False
        tab.presenter.connection = connection

    def _handle_save_mcp_client(
        self, source_tab: McpClientTab, connection: McpClientConnection
    ) -> None:
        snapshot = mcp_client_snapshot_from_tab(source_tab)
        result = self._mcp_save_orchestrator.save_profile(
            snapshot,
            self._tabs,
            stale_context=self._stale_context_for_mcp_client_tab(source_tab),
        )
        if result.action == SaveAction.CANCELLED:
            return

        if result.action == SaveAction.OVERWRITE:
            saved = result.request
            if saved is None:
                logger.error(
                    "mcp_client_save_overwrite_failed reason=missing_snapshot profile_id=%s",
                    connection.id,
                )
                return
            self._apply_mcp_save_result_to_tab(source_tab, saved)
            self.mcp_client_persisted.emit(connection.id, saved, source_tab)
            tab_index = self._index_of_tab(source_tab)
            if tab_index is not None:
                self._header.set_tab_label(tab_index, saved.name)
            self.mcp_client_saved.emit()
            return

        if result.action == SaveAction.CREATED_NEW and result.request is not None:
            tab_index = self._index_of_tab(source_tab)
            if tab_index is not None:
                self._header.set_tab_label(tab_index, result.request.name)
            self._apply_mcp_save_result_to_tab(source_tab, result.request)
            self.save_tabs_state()
            self.mcp_client_saved.emit()

    def _handle_save_as_mcp_client(
        self, source_tab: McpClientTab, connection: McpClientConnection
    ) -> None:
        snapshot = mcp_client_snapshot_from_tab(source_tab)
        result = self._mcp_save_orchestrator.save_as_profile(snapshot, self._tabs)
        if result.action != SaveAction.SAVE_AS or result.request is None:
            return

        new_conn = result.request
        tab_index = self._index_of_tab(source_tab)
        if tab_index is not None:
            self._header.set_tab_label(tab_index, new_conn.name)
        self._apply_mcp_save_result_to_tab(source_tab, new_conn)
        self.save_tabs_state()
        self.mcp_client_save_as_completed.emit(new_conn, result.collection_id or "")

    def _handle_save_websocket(
        self, source_tab: WebSocketTab, connection: WebSocketConnection
    ) -> None:
        snapshot = connection_snapshot_from_tab(source_tab)
        result = self._ws_save_orchestrator.save_profile(
            snapshot,
            self._tabs,
            stale_context=self._stale_context_for_websocket_tab(source_tab),
        )
        if result.action == SaveAction.CANCELLED:
            return

        if result.action == SaveAction.OVERWRITE:
            saved = result.request
            if saved is None:
                logger.error(
                    "ws_save_overwrite_failed reason=missing_snapshot ws_id=%s",
                    connection.id,
                )
                return
            self._apply_ws_save_result_to_tab(source_tab, saved)
            self.websocket_persisted.emit(connection.id, saved, source_tab)
            tab_index = self._index_of_tab(source_tab)
            if tab_index is not None:
                self._header.set_tab_label(tab_index, saved.name)
            self.websocket_saved.emit()
            return

        if result.action == SaveAction.CREATED_NEW and result.request is not None:
            tab_index = self._index_of_tab(source_tab)
            if tab_index is not None:
                self._header.set_tab_label(tab_index, result.request.name)
            self._apply_ws_save_result_to_tab(source_tab, result.request)
            self.save_tabs_state()
            self.websocket_saved.emit()

    def _handle_save_as_websocket(
        self, source_tab: WebSocketTab, connection: WebSocketConnection
    ) -> None:
        snapshot = connection_snapshot_from_tab(source_tab)
        result = self._ws_save_orchestrator.save_as_profile(snapshot, self._tabs)
        if result.action != SaveAction.SAVE_AS or result.request is None:
            return

        new_conn = result.request
        tab_index = self._index_of_tab(source_tab)
        if tab_index is not None:
            self._header.set_tab_label(tab_index, new_conn.name)
        self._apply_ws_save_result_to_tab(source_tab, new_conn)
        self.save_tabs_state()
        self.websocket_save_as_completed.emit(new_conn, result.collection_id or "")

    def _handle_save_request(self, source_tab: RequestTab, request_data: RequestData) -> None:
        result = self._save_orchestrator.save_request(
            request_data,
            self._tabs,
            stale_context=self._stale_context_for_tab(source_tab),
        )
        if result.action == SaveAction.CANCELLED:
            return

        if result.action == SaveAction.OVERWRITE:
            snapshot = result.request
            if snapshot is None:
                logger.error(
                    "save_request_overwrite_failed reason=missing_snapshot request_id=%s",
                    request_data.id,
                )
                return
            source_tab.request_data = snapshot
            source_tab.persisted_baseline = snapshot_persisted_fields(snapshot)
            source_tab.stale_persisted = False
            self.request_persisted.emit(request_data.id, snapshot, source_tab)
            self._sync_tab_labels_for_request(request_data.id, request_data.name)
            self.request_saved.emit()
            return

        if result.action == SaveAction.CREATED_NEW and result.request is not None:
            tab_index = self._index_of_tab(source_tab)
            if tab_index is not None:
                self._header.set_tab_label(tab_index, result.request.name)
            self._apply_save_result_to_tab(source_tab, result.request)
            self.save_tabs_state()
            self.request_saved.emit()

    def _handle_save_as_request(self, source_tab: RequestTab, request_data: RequestData) -> None:
        result = self._save_orchestrator.save_as_request(request_data, self._tabs)
        if result.action != SaveAction.SAVE_AS or result.request is None:
            return

        new_request = result.request
        tab_index = self._index_of_tab(source_tab)
        if tab_index is not None:
            self._header.set_tab_label(tab_index, new_request.name)
        source_tab.request_data = new_request
        source_tab.request_editor.request_data = new_request
        self._apply_save_result_to_tab(source_tab, new_request)

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
