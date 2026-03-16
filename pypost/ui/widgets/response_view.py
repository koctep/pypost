import json
import logging
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout,
    QMenu, QLineEdit, QPushButton, QCheckBox
)
from PySide6.QtGui import QTextCursor, QShortcut, QKeySequence, QTextDocument
from PySide6.QtCore import Qt, Signal

from pypost.models.response import ResponseData
from pypost.core.metrics import MetricsManager
from pypost.ui.widgets.json_highlighter import JsonHighlighter

logger = logging.getLogger(__name__)


class ResponseView(QWidget):
    variable_set_requested = Signal(object, str)

    def __init__(self, indent_size=2):
        super().__init__()
        self.indent_size = indent_size
        self.current_env_keys = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Status Bar + Search (one row)
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: -")
        self.time_label = QLabel("Time: -")
        self.size_label = QLabel("Size: -")

        self.status_layout.addWidget(self.status_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.time_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.size_label)
        self.status_layout.addSpacing(20)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(
            lambda: self._find_next(source="enter")
        )
        self.search_prev_btn = QPushButton("Previous")
        self.search_prev_btn.clicked.connect(
            lambda: self._find_previous(source="previous")
        )
        self.search_next_btn = QPushButton("Next")
        self.search_next_btn.clicked.connect(
            lambda: self._find_next(source="next")
        )
        self.search_case_cb = QCheckBox("Match case")
        self.search_case_cb.toggled.connect(self._on_search_text_changed)
        self.search_status_label = QLabel("")

        self.status_layout.addWidget(self.search_input)
        self.status_layout.addWidget(self.search_prev_btn)
        self.status_layout.addWidget(self.search_next_btn)
        self.status_layout.addWidget(self.search_case_cb)
        self.status_layout.addWidget(self.search_status_label)
        self.status_layout.addStretch()

        layout.addLayout(self.status_layout)

        # Ctrl+F to focus search
        QShortcut(
            QKeySequence("Ctrl+F"), self, self.search_input.setFocus
        )

        # Body View
        self.body_view = QTextEdit()
        self.body_view.setReadOnly(True)
        self.body_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.body_view.customContextMenuRequested.connect(
            self.show_context_menu
        )
        self.json_highlighter = JsonHighlighter(self.body_view.document())
        layout.addWidget(self.body_view)

    def set_env_keys(self, keys):
        self.current_env_keys = sorted(keys) if keys is not None else None

    def _search_flags(self, backward: bool = False) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
        if self.search_case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _find_next(self, source: str = "next") -> None:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return
        self.body_view.find(text, self._search_flags(backward=False))
        total = self._update_match_count()
        MetricsManager().track_gui_response_search_action(
            source=source, has_matches=(total > 0)
        )
        logger.debug(
            "response_search_find source=%s matches=%d",
            source, total
        )

    def _find_previous(self, source: str = "previous") -> None:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return
        self.body_view.find(text, self._search_flags(backward=True))
        total = self._update_match_count()
        MetricsManager().track_gui_response_search_action(
            source=source, has_matches=(total > 0)
        )
        logger.debug(
            "response_search_find source=%s matches=%d",
            source, total
        )

    def _count_matches(self) -> int:
        text = self.search_input.text()
        if not text:
            return 0
        saved = self.body_view.textCursor()
        doc = self.body_view.document()
        cursor = QTextCursor(doc)
        flags = self._search_flags(backward=False)
        count = 0
        while True:
            cursor = doc.find(text, cursor, flags)
            if cursor.isNull():
                break
            count += 1
        self.body_view.setTextCursor(saved)
        return count

    def _current_match_index(self) -> int:
        text = self.search_input.text()
        if not text:
            return 0
        current_pos = self.body_view.textCursor().position()
        doc = self.body_view.document()
        cursor = QTextCursor(doc)
        flags = self._search_flags(backward=False)
        idx = 0
        while True:
            cursor = doc.find(text, cursor, flags)
            if cursor.isNull():
                return 0
            idx += 1
            start, end = min(cursor.anchor(), cursor.position()), max(
                cursor.anchor(), cursor.position()
            )
            if start <= current_pos <= end:
                return idx
            if idx > 10000:
                return 0

    def _update_match_count(self) -> int:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return 0
        total = self._count_matches()
        if total == 0:
            self.search_status_label.setText("No matches")
            return 0
        current = self._current_match_index()
        if current > 0:
            self.search_status_label.setText(f"{current} of {total}")
        else:
            self.search_status_label.setText(f"{total} match(es)")
        return total

    def _on_search_text_changed(self) -> None:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return
        self.body_view.moveCursor(QTextCursor.Start)
        self.body_view.find(text, self._search_flags(backward=False))
        total = self._update_match_count()
        MetricsManager().track_gui_response_search_action(
            source="typed", has_matches=(total > 0)
        )
        logger.debug(
            "response_search_typed query_len=%d matches=%d",
            len(text), total
        )

    def show_context_menu(self, pos):
        cursor = self.body_view.textCursor()
        selected_text = cursor.selectedText()
        clean_text = selected_text.strip()

        # Create menu manually to control order
        menu = QMenu(self)

        # 1. Set Variable
        if clean_text and self.current_env_keys is not None:
            env_menu = menu.addMenu("Set Variable")

            # Existing variables
            if self.current_env_keys:
                for key in self.current_env_keys:
                    action = env_menu.addAction(key)
                    action.triggered.connect(
                        partial(self.emit_variable_set, key, clean_text)
                    )
                env_menu.addSeparator()

            # New variable option
            new_var_action = env_menu.addAction("New Variable...")

            def emit_new_var(checked=False, val=clean_text):
                self.variable_set_requested.emit(None, val)

            new_var_action.triggered.connect(emit_new_var)

        # 2. Copy
        if selected_text:
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(self.body_view.copy)

        if not menu.isEmpty():
            menu.addSeparator()

        select_all = menu.addAction("Select All")
        select_all.triggered.connect(self.body_view.selectAll)

        menu.exec(self.body_view.mapToGlobal(pos))

    def emit_variable_set(self, key, value, checked=False):
        self.variable_set_requested.emit(key, value)

    def set_indent_size(self, size: int):
        self.indent_size = size
        # Refresh current view if it contains JSON
        if self.body_view.toPlainText():
            try:
                text = self.body_view.toPlainText()
                parsed = json.loads(text)
                pretty_json = json.dumps(parsed, indent=self.indent_size)
                self.body_view.setText(pretty_json)
            except Exception:
                pass

    def clear_body(self):
        """Clears the response body and status labels."""
        self.body_view.clear()
        self.status_label.setText("Status: -")
        self.time_label.setText("Time: -")
        self.size_label.setText("Size: -")
        self.search_input.clear()
        self.search_status_label.setText("")

    def append_body(self, text):
        """Appends text to the response body."""
        if not isinstance(text, str):
            text = text.decode("utf-8", errors="replace")
        self.body_view.moveCursor(QTextCursor.End)
        self.body_view.insertPlainText(text)
        self.body_view.moveCursor(QTextCursor.End)

    def display_response(self, response: ResponseData):
        self.status_label.setText(f"Status: {response.status_code}")
        self.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        self.size_label.setText(f"Size: {response.size} bytes")
        self.search_input.clear()
        self.search_status_label.setText("")

        body_str = (
            response.body
            if isinstance(response.body, str)
            else response.body.decode("utf-8", errors="replace")
        )
        try:
            parsed = json.loads(body_str)
            pretty_json = json.dumps(parsed, indent=self.indent_size)
            self.body_view.setText(pretty_json)
        except Exception:
            self.body_view.setText(body_str)
