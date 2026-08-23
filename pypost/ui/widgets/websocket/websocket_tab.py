"""WebSocket session workspace tab widget (PYPOST-1132 / WS-4).

Hosts endpoint configuration editor, accessible state badge, chronological stream view,
and interactive message composer.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pypost.models.websocket import WebSocketConnection
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

        self._init_ui()
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
