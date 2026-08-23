"""WebSocket stream inspector view, delegate, proxy model, and detail pane (PYPOST-1133 / WS-5).

Provides high-performance virtualized stream rendering, multi-dimensional filtering,
text search with match accounting, follow-tail with honest display pause, drop accounting,
detail inspection with word wrap & hex mode, and dual-format transcript export.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import (
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QRect,
    QSize,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QPushButton,
    QSplitter,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.core.websocket_stream import (
    MessageStream,
    StreamEntry,
    StreamQuery,
)
from pypost.core.websocket_stream_export import (
    export_stream_to_json_file,
    export_stream_to_text_file,
)
from pypost.ui.widget_ids import (
    WS_STREAM_CLEAR_BUTTON,
    WS_STREAM_CLEAR_FILTER_BUTTON,
    WS_STREAM_DETAIL,
    WS_STREAM_DETAIL_COPY_BUTTON,
    WS_STREAM_DETAIL_HEX_BUTTON,
    WS_STREAM_DETAIL_SET_VAR_BUTTON,
    WS_STREAM_DETAIL_WRAP_BUTTON,
    WS_STREAM_DIRECTION_FILTER,
    WS_STREAM_DROP_NOTICE,
    WS_STREAM_EXPORT_BUTTON,
    WS_STREAM_FOLLOW_TAIL_BADGE,
    WS_STREAM_KIND_FILTER,
    WS_STREAM_MATCH_COUNT,
    WS_STREAM_PAUSE_BUTTON,
    WS_STREAM_SEARCH_INPUT,
    WS_STREAM_VIEW,
    set_widget_id,
)
from pypost.ui.widgets.websocket.stream_model import StreamListModel

if TYPE_CHECKING:
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

logger = logging.getLogger(__name__)

__all__ = [
    "StreamFilterProxyModel",
    "StreamItemDelegate",
    "StreamDetailPane",
    "WebSocketStreamView",
]


class StreamFilterProxyModel(QSortFilterProxyModel):
    """Sort/filter proxy model wrapping StreamListModel with StreamQuery predicate."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._query = StreamQuery()

    @property
    def query(self) -> StreamQuery:
        """Return the underlying StreamQuery predicate."""
        return self._query

    def _trigger_filter_update(self) -> None:
        self.invalidate()

    def set_direction_filter(self, direction: Optional[str]) -> None:
        """Filter by transmission direction ('in', 'out', or None for all)."""
        self._query.direction = direction
        self._trigger_filter_update()

    def set_kind_filter(self, kind: Optional[str]) -> None:
        """Filter by entry kind ('message', 'lifecycle', or None for all)."""
        self._query.kind = kind
        self._trigger_filter_update()

    def set_search_text(self, text: str) -> None:
        """Filter by substring match against payload and detail."""
        self._query.search_text = text
        self._trigger_filter_update()

    def set_show_heartbeats(self, show: bool) -> None:
        """Toggle suppression of routine heartbeat pings/pongs."""
        self._query.show_heartbeats = show
        self._trigger_filter_update()

    def reset_filters(self) -> None:
        """Reset all filter dimensions to their default states."""
        self._query = StreamQuery()
        self._trigger_filter_update()

    def get_entry(self, row: int) -> StreamEntry:
        """Return the StreamEntry at the specified proxy row index."""
        model = self.sourceModel()
        if isinstance(model, StreamListModel):
            source_idx = self.mapToSource(self.index(row, 0))
            return model.get_entry(source_idx.row())
        raise IndexError("Source model is not StreamListModel")

    @property
    def stream(self) -> MessageStream:
        """Return the underlying MessageStream from source model."""
        model = self.sourceModel()
        if isinstance(model, StreamListModel):
            return model.stream
        raise AttributeError("Source model has no stream")

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        """Evaluate whether entry at source_row satisfies the active query."""
        model = self.sourceModel()
        if not isinstance(model, StreamListModel):
            return True
        if not (0 <= source_row < model.rowCount()):
            return False
        entry = model.get_entry(source_row)
        return self._query.matches(entry)


class StreamItemDelegate(QStyledItemDelegate):
    """High-performance canvas painter for virtualized stream entries."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex
    ) -> QSize:
        """Return fixed row height for O(1) uniform virtualized scrolling."""
        return QSize(option.rect.width(), 26)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        """Paint timestamp, direction glyph, payload snippet, and wire size."""
        painter.save()

        # Draw selection / hover background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_color = option.palette.highlightedText().color()
            dim_color = text_color
        else:
            text_color = option.palette.text().color()
            dim_color = QColor(128, 128, 128)

        rect = option.rect
        ts_utc = str(index.data(StreamListModel.TimestampRole) or "")
        direction = str(index.data(StreamListModel.DirectionRole) or "")
        kind = str(index.data(StreamListModel.KindRole) or "")
        byte_size = index.data(StreamListModel.ByteSizeRole)
        truncated = bool(index.data(StreamListModel.TruncatedRole))
        payload = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        detail = str(index.data(StreamListModel.DetailRole) or "")

        # Format timestamp to HH:MM:SS.mmm if ISO format
        if "T" in ts_utc:
            time_part = ts_utc.split("T")[1].rstrip("Z")
        else:
            time_part = ts_utc

        # Determine glyph and color
        if direction == "in":
            glyph = "<-"
            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            glyph_color = text_color if is_selected else QColor("#2196F3")
        elif direction == "out":
            glyph = "->"
            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            glyph_color = text_color if is_selected else QColor("#4CAF50")
        elif kind == "lifecycle":
            glyph = "(i)"
            is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
            glyph_color = text_color if is_selected else QColor("#AB47BC")
        else:
            glyph = "·"
            glyph_color = dim_color

        # Content snippet
        if kind == "lifecycle":
            content_snippet = detail or payload
        else:
            content_snippet = payload.replace("\n", " ").strip()

        # Wire size string
        size_str = ""
        if byte_size is not None and kind == "message":
            if byte_size < 1024:
                size_str = f"{byte_size} B"
            elif byte_size < 1024 * 1024:
                size_str = f"{byte_size / 1024:.1f} KB"
            else:
                size_str = f"{byte_size / (1024 * 1024):.1f} MB"
            if truncated:
                size_str += " [TRUNC]"

        # Paint elements
        x = rect.x() + 6
        y = rect.y()
        h = rect.height()

        # 1. Timestamp (gray)
        painter.setPen(dim_color)
        ts_width = 90
        _vcenter_left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        _vcenter_center = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
        _vcenter_right = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        painter.drawText(QRect(x, y, ts_width, h), _vcenter_left, time_part[:12])
        x += ts_width + 4

        # 2. Glyph (colored)
        painter.setPen(glyph_color)
        glyph_width = 24
        painter.drawText(QRect(x, y, glyph_width, h), _vcenter_center, glyph)
        x += glyph_width + 6

        # 3. Wire size (right-aligned)
        size_width = 80 if size_str else 0
        if size_str:
            painter.setPen(dim_color)
            size_rect = QRect(rect.right() - size_width - 8, y, size_width, h)
            painter.drawText(size_rect, _vcenter_right, size_str)

        # 4. Payload snippet (fills remaining width)
        snippet_width = max(10, rect.right() - x - size_width - 12)
        painter.setPen(text_color)
        metrics = painter.fontMetrics()
        elided = metrics.elidedText(
            content_snippet, Qt.TextElideMode.ElideRight, snippet_width
        )
        painter.drawText(
            QRect(x, y, snippet_width, h), _vcenter_left, elided
        )

        painter.restore()


def _format_hex_dump(payload: str | bytes) -> str:
    """Format payload string or bytes into a standard 16-byte hex dump."""
    if isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = bytes(payload)

    if not data:
        return ""

    lines: list[str] = []
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        hex_bytes_part1 = " ".join(f"{b:02x}" for b in chunk[:8])
        hex_bytes_part2 = " ".join(f"{b:02x}" for b in chunk[8:])

        # 8 bytes is 8*2 + 7 spaces = 23 chars
        hex_col1 = f"{hex_bytes_part1:<23}"
        hex_col2 = f"{hex_bytes_part2:<23}"

        ascii_col = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{offset:08x}: {hex_col1}  {hex_col2}  |{ascii_col}|")

    return "\n".join(lines)


class StreamDetailPane(QWidget):
    """Detailed single-entry inspector with formatting, hex dump, wrap, and variable capture."""

    variable_capture_requested = Signal(str, str)  # (suggested_name, value)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        set_widget_id(self, WS_STREAM_DETAIL)
        self._current_entry: Optional[StreamEntry] = None
        self._is_wrap: bool = True
        self._is_hex_mode: bool = False
        self._is_truncated_flag: bool = False
        self._env_vars: dict[str, str] = {}
        self._hidden_keys: set[str] = set()

        self._init_ui()
        if parent is None:
            self.show()

    def set_variables(self, variables: dict[str, str]) -> None:
        """Update environment variables snapshot for egress sanitization."""
        self._env_vars = dict(variables)

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Update hidden keys snapshot for egress sanitization."""
        self._hidden_keys = set(hidden_keys)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header metadata & truncation row
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self._meta_lbl = QLabel("No message selected", self)
        header_layout.addWidget(self._meta_lbl)
        header_layout.addStretch()

        self._truncation_banner = QLabel("(!) Truncated for display", self)
        self._truncation_banner.setStyleSheet("color: #FF9800; font-weight: bold;")
        self._truncation_banner.setVisible(False)
        header_layout.addWidget(self._truncation_banner)

        layout.addLayout(header_layout)

        # Actions toolbar row
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)

        self._copy_btn = QPushButton("Copy", self)
        set_widget_id(self._copy_btn, WS_STREAM_DETAIL_COPY_BUTTON)
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        toolbar.addWidget(self._copy_btn)

        self._set_var_btn = QPushButton("Set as variable...", self)
        set_widget_id(self._set_var_btn, WS_STREAM_DETAIL_SET_VAR_BUTTON)
        self._set_var_btn.clicked.connect(self._on_set_variable_clicked)
        toolbar.addWidget(self._set_var_btn)

        self._wrap_btn = QPushButton("Wrap", self)
        set_widget_id(self._wrap_btn, WS_STREAM_DETAIL_WRAP_BUTTON)
        self._wrap_btn.clicked.connect(self._on_toggle_wrap)
        toolbar.addWidget(self._wrap_btn)

        self._hex_btn = QPushButton("Hex", self)
        set_widget_id(self._hex_btn, WS_STREAM_DETAIL_HEX_BUTTON)
        self._hex_btn.clicked.connect(self._on_toggle_hex)
        toolbar.addWidget(self._hex_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Payload display editor
        self._editor = QTextEdit(self)
        self._editor.setReadOnly(True)
        self._editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._editor.setFont(font)
        layout.addWidget(self._editor)

    @property
    def current_entry(self) -> Optional[StreamEntry]:
        """Currently inspected StreamEntry."""
        return self._current_entry

    @property
    def is_wrap_mode(self) -> bool:
        """Return True if word wrapping is enabled."""
        return self._is_wrap

    @property
    def is_hex_mode(self) -> bool:
        """Return True if hexadecimal view mode is active."""
        return self._is_hex_mode

    @property
    def is_truncated_notice_visible(self) -> bool:
        """Return True if the truncation warning banner is visible."""
        return self._is_truncated_flag and not self._truncation_banner.isHidden()

    @property
    def truncation_banner(self) -> QLabel:
        """Return the truncation banner label widget."""
        return self._truncation_banner

    def set_entry(self, entry: Optional[StreamEntry]) -> None:
        """Display metadata and payload for the given StreamEntry."""
        self._current_entry = entry
        if entry is None:
            self._meta_lbl.setText("No message selected")
            self._is_truncated_flag = False
            self._truncation_banner.setVisible(False)
            self._editor.setPlainText("")
            return

        # Format metadata string
        if entry.direction == "in":
            dir_symbol = "<- inbound"
        elif entry.direction == "out":
            dir_symbol = "-> outbound"
        else:
            dir_symbol = "(i) lifecycle"
        if entry.byte_size < 1024:
            size_str = f"{entry.byte_size} B"
        else:
            size_str = f"{entry.byte_size / 1024:.1f} KB"
        self._meta_lbl.setText(
            f"{dir_symbol} · {entry.payload_format} · {size_str} · {entry.ts_utc}"
        )

        # Truncation banner
        self._is_truncated_flag = bool(entry.truncated)
        if entry.truncated:
            self._truncation_banner.setText(f"(!) Display truncated (wire size: {size_str})")
            self._truncation_banner.setVisible(True)
        else:
            self._truncation_banner.setVisible(False)

        self._render_payload()

    def _render_payload(self) -> None:
        if self._current_entry is None:
            self._editor.setPlainText("")
            return

        content = self._current_entry.payload
        if self._is_hex_mode:
            self._editor.setPlainText(_format_hex_dump(content))
        else:
            self._editor.setPlainText(content)

    def _on_copy_clicked(self) -> None:
        cursor = self._editor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text:
            text_to_copy = selected_text
        elif self._current_entry is not None:
            text_to_copy = self._current_entry.payload
        else:
            text_to_copy = self._editor.toPlainText()

        sanitized_text = sanitize_text(
            text_to_copy, env_vars=self._env_vars, hidden_keys=self._hidden_keys
        )
        QApplication.clipboard().setText(sanitized_text)
        logger.debug("websocket_detail_payload_copied length=%d", len(sanitized_text))

    def _on_set_variable_clicked(self) -> None:
        cursor = self._editor.textCursor()
        selected_text = cursor.selectedText()
        if selected_text:
            val = selected_text
        else:
            val = self._current_entry.payload if self._current_entry else ""
        if not val:
            return

        var_name, ok = QInputDialog.getText(
            self,
            "Set as Variable",
            "Variable name:",
            text="CAPTURED_TOKEN",
        )
        if ok and var_name.strip():
            clean_name = var_name.strip()
            self.variable_capture_requested.emit(clean_name, val)
            logger.info("websocket_variable_capture_requested name=%s", clean_name)

    def _on_toggle_wrap(self) -> None:
        self._is_wrap = not self._is_wrap
        if self._is_wrap:
            self._editor.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self._wrap_btn.setText("Wrap: ON")
        else:
            self._editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self._wrap_btn.setText("Wrap: OFF")
        logger.debug("websocket_detail_wrap_toggled wrap=%s", self._is_wrap)

    def _on_toggle_hex(self) -> None:
        self._is_hex_mode = not self._is_hex_mode
        if self._is_hex_mode:
            self._hex_btn.setText("Hex: ON")
        else:
            self._hex_btn.setText("Hex: OFF")
        self._render_payload()
        logger.debug("websocket_detail_hex_toggled hex=%s", self._is_hex_mode)


class WebSocketStreamView(QWidget):
    """Main Stream Inspector container combining virtualized list, filters, notices,
    and detail pane."""

    def __init__(
        self,
        stream_model: StreamListModel,
        presenter: Optional[WebSocketPresenter] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, WS_STREAM_VIEW)
        self._stream_model = stream_model
        self.presenter: Optional[WebSocketPresenter] = presenter
        self._proxy_model = StreamFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._stream_model)
        self._is_paused: bool = False
        self._unread_count: int = 0

        self._init_ui()
        self._wire_signals()
        self._update_counts()
        self._update_drop_notice()
        if parent is None:
            self.show()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # 1. Filter Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(6)

        self._search_input = QLineEdit(self)
        set_widget_id(self._search_input, WS_STREAM_SEARCH_INPUT)
        self._search_input.setPlaceholderText("Search stream...")
        self._search_input.setClearButtonEnabled(True)
        toolbar.addWidget(self._search_input)

        self._dir_combo = QComboBox(self)
        set_widget_id(self._dir_combo, WS_STREAM_DIRECTION_FILTER)
        self._dir_combo.addItem("Dir: All", None)
        self._dir_combo.addItem("Inbound (<-)", "in")
        self._dir_combo.addItem("Outbound (->)", "out")
        toolbar.addWidget(self._dir_combo)

        self._kind_combo = QComboBox(self)
        set_widget_id(self._kind_combo, WS_STREAM_KIND_FILTER)
        self._kind_combo.addItem("Kind: All", None)
        self._kind_combo.addItem("Messages", "message")
        self._kind_combo.addItem("Lifecycle", "lifecycle")
        toolbar.addWidget(self._kind_combo)

        self._heartbeats_check = QCheckBox("Heartbeats", self)
        self._heartbeats_check.setChecked(False)
        self._heartbeats_check.setToolTip("Show or hide routine heartbeat ping/pong events")
        toolbar.addWidget(self._heartbeats_check)

        self._pause_btn = QPushButton("Pause", self)
        set_widget_id(self._pause_btn, WS_STREAM_PAUSE_BUTTON)
        self._pause_btn.setToolTip(
            "Pause display tracking (network intake continues in background)"
        )
        toolbar.addWidget(self._pause_btn)

        self._clear_btn = QPushButton("Clear", self)
        set_widget_id(self._clear_btn, WS_STREAM_CLEAR_BUTTON)
        self._clear_btn.setToolTip("Clear stream buffer and drop counters")
        toolbar.addWidget(self._clear_btn)

        self._export_btn = QPushButton("Export", self)
        set_widget_id(self._export_btn, WS_STREAM_EXPORT_BUTTON)
        self._export_btn.setToolTip("Export masked stream transcript (JSON or Plain Text)")
        toolbar.addWidget(self._export_btn)

        self._match_count_lbl = QLabel("0 entries", self)
        set_widget_id(self._match_count_lbl, WS_STREAM_MATCH_COUNT)
        toolbar.addWidget(self._match_count_lbl)

        main_layout.addLayout(toolbar)

        # 2. Drop Notice Banner
        self._drop_notice = QWidget(self)
        set_widget_id(self._drop_notice, WS_STREAM_DROP_NOTICE)
        drop_layout = QHBoxLayout(self._drop_notice)
        drop_layout.setContentsMargins(6, 4, 6, 4)
        self._drop_notice_lbl = QLabel(self._drop_notice)
        self._drop_notice_lbl.setStyleSheet("color: #D32F2F; font-weight: bold;")
        drop_layout.addWidget(self._drop_notice_lbl)
        drop_layout.addStretch()
        self._drop_notice.setVisible(False)
        main_layout.addWidget(self._drop_notice)

        # 3. Vertical Splitter hosting Stream List View and Detail Pane
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # Stream list container with floating follow-tail badge and empty overlay
        list_container = QWidget(splitter)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)

        self._list_view = QListView(list_container)
        set_widget_id(self._list_view, WS_STREAM_VIEW)
        self._list_view.setModel(self._proxy_model)
        self._delegate = StreamItemDelegate(self._list_view)
        self._list_view.setItemDelegate(self._delegate)
        self._list_view.setUniformItemSizes(True)
        list_layout.addWidget(self._list_view)

        # Empty filter state overlay container
        self._empty_filter_widget = QWidget(list_container)
        empty_layout = QVBoxLayout(self._empty_filter_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_filter_lbl = QLabel("No messages match filter", self._empty_filter_widget)
        empty_layout.addWidget(self._empty_filter_lbl)

        self._clear_filter_btn = QPushButton("Clear filter", self._empty_filter_widget)
        set_widget_id(self._clear_filter_btn, WS_STREAM_CLEAR_FILTER_BUTTON)
        self._clear_filter_btn.clicked.connect(self._on_clear_filter_clicked)
        empty_layout.addWidget(self._clear_filter_btn)
        self._empty_filter_widget.setVisible(False)
        self._clear_filter_btn.setVisible(False)
        list_layout.addWidget(self._empty_filter_widget)

        # Follow-tail floating badge button
        self._follow_tail_badge = QPushButton("↓ New messages", list_container)
        set_widget_id(self._follow_tail_badge, WS_STREAM_FOLLOW_TAIL_BADGE)
        self._follow_tail_badge.setStyleSheet(
            "QPushButton { background-color: #1976D2; color: white;"
            " border-radius: 12px; padding: 4px 12px; font-weight: bold; }"
        )
        self._follow_tail_badge.setVisible(False)
        self._follow_tail_badge.clicked.connect(self._on_follow_tail_clicked)
        list_layout.addWidget(self._follow_tail_badge)

        splitter.addWidget(list_container)

        # Detail Pane
        self._detail_pane = StreamDetailPane(splitter)
        splitter.addWidget(self._detail_pane)

        splitter.setSizes([300, 150])
        main_layout.addWidget(splitter)

    def _wire_signals(self) -> None:
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._dir_combo.currentIndexChanged.connect(self._on_direction_changed)
        self._kind_combo.currentIndexChanged.connect(self._on_kind_changed)
        self._heartbeats_check.toggled.connect(self._on_heartbeats_toggled)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._export_btn.clicked.connect(self._on_export_menu_requested)

        # Selection changes in list view
        self._list_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Model row changes
        self._stream_model.rowsInserted.connect(self._on_rows_inserted)
        self._stream_model.rowsRemoved.connect(self._on_model_rows_changed)
        self._stream_model.modelReset.connect(self._on_model_rows_changed)

        # Scrollbar tracking
        scrollbar = self._list_view.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_value_changed)

    @property
    def is_paused(self) -> bool:
        """Return True if follow-tail tracking is paused."""
        return self._is_paused

    @property
    def unread_count(self) -> int:
        """Return number of new messages arrived while paused or detached from tail."""
        return self._unread_count

    @property
    def detail_pane(self) -> StreamDetailPane:
        """Return the embedded StreamDetailPane widget."""
        return self._detail_pane

    def _on_search_text_changed(self, text: str) -> None:
        self._proxy_model.set_search_text(text.strip())
        self._update_counts()
        logger.debug("websocket_stream_filter_search_changed query_len=%d", len(text.strip()))

    def _on_direction_changed(self) -> None:
        direction = self._dir_combo.currentData()
        self._proxy_model.set_direction_filter(direction)
        self._update_counts()
        logger.debug("websocket_stream_filter_direction_changed direction=%s", direction)

    def _on_kind_changed(self) -> None:
        kind = self._kind_combo.currentData()
        self._proxy_model.set_kind_filter(kind)
        self._update_counts()
        logger.debug("websocket_stream_filter_kind_changed kind=%s", kind)

    def _on_heartbeats_toggled(self, checked: bool) -> None:
        self._proxy_model.set_show_heartbeats(checked)
        self._update_counts()
        logger.debug("websocket_stream_filter_heartbeats_toggled show_heartbeats=%s", checked)

    def _on_clear_filter_clicked(self) -> None:
        self._search_input.setText("")
        self._dir_combo.setCurrentIndex(0)
        self._kind_combo.setCurrentIndex(0)
        self._heartbeats_check.setChecked(False)
        self._proxy_model.reset_filters()
        self._update_counts()
        logger.debug("websocket_stream_filters_reset")

    def _on_pause_clicked(self) -> None:
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.setText("Resume")
            logger.info("websocket_stream_display_paused")
        else:
            self._pause_btn.setText("Pause")
            self._unread_count = 0
            self._follow_tail_badge.setVisible(False)
            self._list_view.scrollToBottom()
            logger.info("websocket_stream_display_resumed")

    def _on_clear_clicked(self) -> None:
        self._stream_model.clear()
        self._unread_count = 0
        self._follow_tail_badge.setVisible(False)
        self._detail_pane.set_entry(None)
        self._update_counts()
        self._update_drop_notice()
        logger.info("websocket_stream_view_cleared")

    def _on_follow_tail_clicked(self) -> None:
        self._is_paused = False
        self._pause_btn.setText("Pause")
        self._unread_count = 0
        self._follow_tail_badge.setVisible(False)
        self._list_view.scrollToBottom()

    def _on_selection_changed(self) -> None:
        indexes = self._list_view.selectionModel().selectedIndexes()
        if not indexes:
            self._detail_pane.set_entry(None)
            return

        proxy_idx = indexes[0]
        entry = proxy_idx.data(StreamListModel.StreamEntryRole)
        if isinstance(entry, StreamEntry):
            self._detail_pane.set_entry(entry)
            logger.debug(
                "websocket_stream_entry_inspected seq=%d kind=%s direction=%s "
                "byte_size=%d truncated=%s",
                entry.seq,
                entry.kind,
                entry.direction,
                entry.byte_size,
                entry.truncated,
            )

    def _on_rows_inserted(self, parent: QModelIndex, start: int, end: int) -> None:
        count = end - start + 1
        self._update_counts()
        self._update_drop_notice()

        scrollbar = self._list_view.verticalScrollBar()
        is_at_bottom = scrollbar.value() >= scrollbar.maximum() - 4

        if self._is_paused or not is_at_bottom:
            self._unread_count += count
            self._follow_tail_badge.setText(f"↓ {self._unread_count} new messages")
            self._follow_tail_badge.setVisible(True)
        else:
            self._list_view.scrollToBottom()

    def _on_model_rows_changed(self) -> None:
        self._update_counts()
        self._update_drop_notice()

    def _on_scroll_value_changed(self, value: int) -> None:
        scrollbar = self._list_view.verticalScrollBar()
        if value >= scrollbar.maximum() - 2 and not self._is_paused:
            self._unread_count = 0
            self._follow_tail_badge.setVisible(False)

    def _update_counts(self) -> None:
        total = self._stream_model.rowCount()
        visible = self._proxy_model.rowCount()
        hidden = total - visible

        if total == 0:
            self._match_count_lbl.setText("0 entries")
            self._empty_filter_widget.setVisible(False)
            self._clear_filter_btn.setVisible(False)
        elif hidden > 0:
            self._match_count_lbl.setText(f"{visible} matches ({hidden} hidden)")
            if visible == 0:
                self._empty_filter_lbl.setText(
                    f"No messages match filter. {hidden} hidden by current filter."
                )
                self._empty_filter_widget.setVisible(True)
                self._clear_filter_btn.setVisible(True)
            else:
                self._empty_filter_widget.setVisible(False)
                self._clear_filter_btn.setVisible(False)
        else:
            self._match_count_lbl.setText(f"{total} entries")
            self._empty_filter_widget.setVisible(False)
            self._clear_filter_btn.setVisible(False)

    def _update_drop_notice(self) -> None:
        dropped = self._stream_model.stream.dropped
        cap = dropped.get("capacity", 0)
        mem = dropped.get("memory_budget", 0)

        if cap > 0 and mem > 0:
            total_dropped = cap + mem
            self._drop_notice_lbl.setText(
                f"(!) {total_dropped} messages dropped ({cap} capacity, {mem} memory_budget)"
            )
            self._drop_notice.setVisible(True)
        elif cap > 0:
            self._drop_notice_lbl.setText(f"(!) {cap} messages dropped (capacity)")
            self._drop_notice.setVisible(True)
        elif mem > 0:
            self._drop_notice_lbl.setText(f"(!) {mem} messages dropped (memory_budget)")
            self._drop_notice.setVisible(True)
        else:
            self._drop_notice.setVisible(False)

    def _on_export_menu_requested(self) -> None:
        menu = QMenu(self)
        json_act = menu.addAction("Export as JSON Transcript...")
        text_act = menu.addAction("Export as Plain Text Transcript...")
        badge_pos = self._export_btn.mapToGlobal(self._export_btn.rect().bottomLeft())
        action = menu.exec(badge_pos)

        if action == json_act:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export JSON Transcript", "transcript.json", "JSON Files (*.json)"
            )
            if path:
                self.export_json(path)
        elif action == text_act:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Text Transcript", "transcript.txt", "Text Files (*.txt)"
            )
            if path:
                self.export_text(path)

    def set_variables(self, variables: dict[str, str]) -> None:
        """Propagate environment variables to child detail pane."""
        self._detail_pane.set_variables(variables)

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Propagate hidden keys to child detail pane."""
        self._detail_pane.set_hidden_keys(hidden_keys)

    def export_json(self, path: Path | str) -> None:
        """Export stream to a JSON transcript file."""
        try:
            env_vars = getattr(self.presenter, "_env_vars", self._detail_pane._env_vars)
            hidden_keys = getattr(self.presenter, "_hidden_keys", self._detail_pane._hidden_keys)
            export_stream_to_json_file(
                Path(path),
                self._stream_model.stream,
                env_vars=env_vars,
                hidden_keys=hidden_keys,
            )
        except Exception as exc:
            logger.error("websocket_stream_json_export_failed path=%s error=%s", path, exc)
            raise

    def export_text(self, path: Path | str) -> None:
        """Export stream to a Plain Text transcript file."""
        try:
            env_vars = getattr(self.presenter, "_env_vars", self._detail_pane._env_vars)
            hidden_keys = getattr(self.presenter, "_hidden_keys", self._detail_pane._hidden_keys)
            export_stream_to_text_file(
                Path(path),
                self._stream_model.stream,
                env_vars=env_vars,
                hidden_keys=hidden_keys,
            )
        except Exception as exc:
            logger.error("websocket_stream_text_export_failed path=%s error=%s", path, exc)
            raise
