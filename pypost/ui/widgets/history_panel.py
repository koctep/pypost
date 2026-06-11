import logging
from typing import List

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pypost.ui.collection_item_dialogs import confirm_clear_history
from pypost.core.curl_generator import CurlGenerator
from pypost.core.history_manager import HistoryManager
from pypost.models.models import HistoryEntry, RequestData

logger = logging.getLogger(__name__)


class HistoryPanel(QWidget):
    """Sidebar panel for browsing, filtering, and reloading request history."""

    load_into_editor = Signal(RequestData)
    curl_copied = Signal()

    def __init__(
        self, history_manager: HistoryManager, icons: dict | None = None, parent=None
    ) -> None:
        super().__init__(parent)
        self._history_manager = history_manager
        self._icons = icons or {}
        self._entries: List[HistoryEntry] = []

        self._build_ui()
        self.refresh()

    def refresh(self) -> None:
        """Reloads entries from HistoryManager and re-applies filter."""
        self._entries = self._history_manager.get_entries()
        logger.debug("history_panel_refreshed entry_count=%d", len(self._entries))
        self._apply_filter(self._filter_input.text())

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter by URL…")
        self._filter_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self._filter_input)

        splitter = QSplitter(Qt.Vertical)

        self._list_widget = QListWidget()
        self._list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self._list_widget.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self._list_widget)

        # Add shortcut for Copy as cURL
        self._copy_shortcut = QShortcut(QKeySequence.Copy, self._list_widget)
        self._copy_shortcut.activated.connect(self._copy_as_curl)

        detail_container = QWidget()
        detail_layout = QFormLayout(detail_container)
        detail_layout.setContentsMargins(4, 4, 4, 4)

        self._detail_method = QLabel()
        self._detail_url = QLabel()
        self._detail_url.setWordWrap(True)
        self._detail_status = QLabel()
        self._detail_time = QLabel()
        self._detail_headers = QTextEdit()
        self._detail_headers.setReadOnly(True)
        self._detail_headers.setFixedHeight(60)
        self._detail_body = QTextEdit()
        self._detail_body.setReadOnly(True)
        self._detail_body.setFixedHeight(80)

        detail_layout.addRow("Method:", self._detail_method)
        detail_layout.addRow("URL:", self._detail_url)
        detail_layout.addRow("Status:", self._detail_status)
        detail_layout.addRow("Time:", self._detail_time)
        detail_layout.addRow("Headers:", self._detail_headers)
        detail_layout.addRow("Body:", self._detail_body)

        splitter.addWidget(detail_container)
        layout.addWidget(splitter)

        btn_row = QHBoxLayout()
        self._load_btn = QPushButton("Load into Editor")
        self._load_btn.setEnabled(False)
        self._load_btn.clicked.connect(self._on_load_into_editor)
        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.clicked.connect(self._on_clear_history)
        btn_row.addWidget(self._load_btn)
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _apply_filter(self, text: str) -> None:
        """Repopulates list with entries whose URL contains `text`."""
        self._list_widget.clear()
        needle = text.lower()
        for entry in self._entries:
            if needle and needle not in entry.url.lower():
                continue
            label = (
                f"[{entry.method}]  {entry.timestamp[:16].replace('T', ' ')}  "
                f"{entry.status_code}\n{entry.url}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, entry.id)
            if entry.method in self._icons:
                item.setIcon(self._icons[entry.method])
            self._list_widget.addItem(item)
        self._load_btn.setEnabled(False)
        self._clear_detail()

    def _on_selection_changed(self) -> None:
        """Populates the detail pane for the selected entry."""
        entry = self._selected_entry()
        if entry is None:
            self._load_btn.setEnabled(False)
            self._clear_detail()
            return
        self._load_btn.setEnabled(True)
        self._detail_method.setText(entry.method)
        self._detail_url.setText(entry.url)
        self._detail_status.setText(str(entry.status_code))
        self._detail_time.setText(f"{entry.response_time_ms:.1f} ms")
        headers_text = "\n".join(f"{k}: {v}" for k, v in entry.headers.items())
        self._detail_headers.setPlainText(headers_text)
        self._detail_body.setPlainText(entry.body)

    def _on_load_into_editor(self) -> None:
        """Converts selected HistoryEntry to RequestData and emits load_into_editor."""
        entry = self._selected_entry()
        if entry is None:
            return
        request_data = RequestData(
            method=entry.method,
            url=entry.url,
            headers=entry.headers,
            body=entry.body,
        )
        logger.info(
            "history_load_into_editor method=%s url=%s", entry.method, entry.url
        )
        self.load_into_editor.emit(request_data)

    def _on_clear_history(self) -> None:
        """Confirms then clears all history entries."""
        if not confirm_clear_history(self):
            return
        self._history_manager.clear()
        self.refresh()
        logger.info("history_cleared")

    def _on_context_menu(self, pos: QPoint) -> None:
        """Shows context menu with 'Copy as cURL' and 'Delete' actions for right-clicked entry."""
        item = self._list_widget.itemAt(pos)
        if item is None:
            return

        # Select the item if it was right-clicked but not currently selected
        if self._list_widget.currentItem() != item:
            self._list_widget.setCurrentItem(item)

        menu = QMenu(self)
        copy_curl_action = menu.addAction("Copy as cURL")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self._list_widget.mapToGlobal(pos))
        if action == copy_curl_action:
            self._copy_as_curl()
        elif action == delete_action:
            entry_id = item.data(Qt.UserRole)
            self._history_manager.delete_entry(entry_id)
            logger.info("history_entry_deleted entry_id=%s", entry_id)
            self.refresh()

    def _copy_as_curl(self) -> None:
        """Copies the selected history entry as a cURL command to the clipboard."""
        entry = self._selected_entry()
        if entry is None:
            return

        try:
            curl_cmd = CurlGenerator.generate_from_history(entry)
            QApplication.clipboard().setText(curl_cmd)
            logger.info("history_curl_copied method=%s url=%s", entry.method, entry.url)
            self.curl_copied.emit()
        except Exception as e:
            logger.error(
                "history_curl_copy_failed entry_id=%s error=%s",
                entry.id,
                str(e),
                exc_info=True,
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _selected_entry(self) -> HistoryEntry | None:
        item = self._list_widget.currentItem()
        if item is None:
            return None
        entry_id = item.data(Qt.UserRole)
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def _clear_detail(self) -> None:
        self._detail_method.clear()
        self._detail_url.clear()
        self._detail_status.clear()
        self._detail_time.clear()
        self._detail_headers.clear()
        self._detail_body.clear()
