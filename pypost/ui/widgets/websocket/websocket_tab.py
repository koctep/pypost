"""WebSocket session workspace tab widget (PYPOST-1132 / WS-4).

Hosts endpoint configuration editor, accessible state badge, chronological stream view,
and interactive message composer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.metrics_protocol import resolve_metrics
from pypost.models.websocket import WebSocketConnection
from pypost.ui.hotkeys import tag_action
from pypost.ui.presenters.tab_dirty import connection_snapshot_from_tab
from pypost.ui.widget_ids import (
    WS_CONNECT_BUTTON,
    WS_TAB_PAGE,
    set_widget_id,
)
from pypost.ui.widgets.websocket.composer import WebSocketComposer
from pypost.ui.widgets.websocket.connection_editor import WebSocketConnectionEditor
from pypost.ui.widgets.websocket.presets_panel import WebSocketPresetsPanel
from pypost.ui.widgets.websocket.state_badge import WebSocketStateBadge
from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

if TYPE_CHECKING:
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

logger = logging.getLogger(__name__)

__all__ = ["WebSocketTab"]


class WebSocketTab(QWidget):
    """Top-level workspace tab container for an active WebSocket session."""

    save_requested = Signal(WebSocketConnection)
    save_as_requested = Signal(WebSocketConnection)

    def __init__(
        self,
        connection: WebSocketConnection,
        presenter: WebSocketPresenter,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, WS_TAB_PAGE)
        self.connection_data: WebSocketConnection = connection
        self.presenter: WebSocketPresenter = presenter
        self.persisted_baseline: WebSocketConnection | None = None
        self.stale_persisted = False

        self._init_ui()
        self._setup_save_shortcuts()
        self._connection_editor.load_connection(connection)
        self.presenter.set_tab(self)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Header controls row (Connect button + State badge)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.connect_btn = QPushButton("Connect", self)
        set_widget_id(self.connect_btn, WS_CONNECT_BUTTON)
        header_row.addWidget(self.connect_btn)

        self._state_badge = WebSocketStateBadge(self)
        header_row.addWidget(self._state_badge)
        header_row.addStretch()

        self.actions_btn = QToolButton(self)
        self.actions_btn.setText("Actions")
        self.actions_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_menu = QMenu(self.actions_btn)
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.triggered.connect(self.handle_save_as_menu_action)
        self.actions_menu.addAction(self.save_as_action)
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.handle_save_menu_action)
        self.actions_menu.addAction(self.save_action)
        self.actions_btn.setMenu(self.actions_menu)
        header_row.addWidget(self.actions_btn)

        main_layout.addLayout(header_row)

        # Vertical splitter dividing connection editor, stream log, and composer
        v_splitter = QSplitter(Qt.Orientation.Vertical, self)

        # Top section: Connection configuration editor
        self._connection_editor = WebSocketConnectionEditor(v_splitter)
        v_splitter.addWidget(self._connection_editor)

        # Middle section: Stream inspector view
        self._stream_view = WebSocketStreamView(
            stream_model=self.presenter.stream_model,
            presenter=self.presenter,
            parent=v_splitter,
        )
        v_splitter.addWidget(self._stream_view)

        # Bottom section: Multi-format message composer
        self._composer = WebSocketComposer(presenter=self.presenter, parent=v_splitter)
        self.composer_edit = self._composer.payload_edit
        self.send_btn = self._composer.send_btn
        v_splitter.addWidget(self._composer)

        # Messages sub-tab in connection editor detail tabs
        self._presets_panel = WebSocketPresetsPanel(
            presenter=self.presenter,
            composer=self._composer,
            parent=self._connection_editor.detail_tabs,
        )
        self._connection_editor.detail_tabs.addTab(self._presets_panel, "Messages")

        v_splitter.setSizes([200, 300, 150])
        main_layout.addWidget(v_splitter)

    @property
    def connection_editor(self) -> WebSocketConnectionEditor:
        """Return the embedded WebSocketConnectionEditor widget."""
        return self._connection_editor

    @property
    def state_badge(self) -> WebSocketStateBadge:
        """Return the embedded WebSocketStateBadge widget."""
        return self._state_badge

    @property
    def stream_view(self) -> WebSocketStreamView:
        """Return the embedded WebSocketStreamView widget."""
        return self._stream_view

    @property
    def composer(self) -> WebSocketComposer:
        """Return the embedded WebSocketComposer widget."""
        return self._composer

    @property
    def presets_panel(self) -> WebSocketPresetsPanel:
        """Return the embedded WebSocketPresetsPanel widget."""
        return self._presets_panel

    def _setup_save_shortcuts(self) -> None:
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.addAction(self.save_action)
        self.addAction(self.save_as_action)
        tag_action(
            self.save_action,
            section="WebSocket Session",
            order=2,
            keys=("Ctrl+S",),
            label="Save WebSocket Profile",
        )
        tag_action(
            self.save_as_action,
            section="WebSocket Session",
            order=3,
            keys=("Ctrl+Shift+S",),
            label="Save As WebSocket Profile",
        )

    def _emit_save(self, source: str) -> None:
        logger.info("ws_save_action_triggered source=%s", source)
        resolve_metrics(getattr(self.presenter, "_metrics", None)).track_gui_save_action(
            source
        )
        snapshot = connection_snapshot_from_tab(self)
        self.connection_data = snapshot
        self.save_requested.emit(snapshot)

    def _emit_save_as(self, source: str) -> None:
        logger.info("ws_save_as_action_triggered source=%s", source)
        resolve_metrics(getattr(self.presenter, "_metrics", None)).track_gui_save_as_action(
            source
        )
        snapshot = connection_snapshot_from_tab(self)
        self.connection_data = snapshot
        self.save_as_requested.emit(snapshot)

    def handle_save_request_shortcut(self) -> None:
        self._emit_save("shortcut")

    def handle_save_menu_action(self) -> None:
        self._emit_save("menu")

    def handle_save_as_shortcut(self) -> None:
        self._emit_save_as("shortcut")

    def handle_save_as_menu_action(self) -> None:
        self._emit_save_as("menu")
