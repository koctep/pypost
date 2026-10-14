from __future__ import annotations

import json
import logging
from functools import partial

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from typing import Sequence

from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.models.response import ResponseData
from pypost.ui.widget_ids import (
    RESPONSE_BODY,
    RESPONSE_PANEL,
    RESPONSE_STATUS,
    set_widget_id,
)
from pypost.ui.widgets.fold import BodyFormat, detect_body_format
from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.json_highlighter import JsonHighlighter
from pypost.ui.widgets.response_mask_controller import (
    ResponseMaskController,
    format_masked_json,
)

logger = logging.getLogger(__name__)

LARGE_DOC_CHAR_THRESHOLD = 100 * 1024
MATCH_COUNT_CAP = 1000
MATCH_INDEX_SAFETY_LIMIT = 10000
SEARCH_DEBOUNCE_MS = 250


class ResponseView(QWidget):
    variable_set_requested = Signal(object, str)
    body_view: FoldableCodeView

    def __init__(self, indent_size=2, metrics: MetricsTrackerProtocol | None = None):
        super().__init__()
        set_widget_id(self, RESPONSE_PANEL)
        self.indent_size = indent_size
        self._metrics = resolve_metrics(metrics)
        self.current_env_keys = None
        self._last_response: ResponseData | None = None
        self._last_hidden_fields: list[str] | None = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Status Bar + Search (one row)
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: -")
        set_widget_id(self.status_label, RESPONSE_STATUS)
        self.time_label = QLabel("Time: -")
        self.size_label = QLabel("Size: -")

        self.status_layout.addWidget(self.status_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.time_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.size_label)
        self.status_layout.addSpacing(20)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._search_timer.timeout.connect(self._on_search_text_changed)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._schedule_search_text_changed)
        self.search_input.returnPressed.connect(lambda: self._find_next(source="enter"))
        self.search_prev_btn = QPushButton("Previous")
        self.search_prev_btn.clicked.connect(lambda: self._find_previous(source="previous"))
        self.search_next_btn = QPushButton("Next")
        self.search_next_btn.clicked.connect(lambda: self._find_next(source="next"))
        self.search_case_cb = QCheckBox("Match case")
        self.search_case_cb.toggled.connect(self._schedule_search_text_changed)
        self.search_status_label = QLabel("")
        self.fold_all_btn = QPushButton("Fold All")
        self.fold_all_btn.clicked.connect(lambda: self.body_view.fold_all())
        self.unfold_all_btn = QPushButton("Unfold All")
        self.unfold_all_btn.clicked.connect(lambda: self.body_view.unfold_all())

        self.status_layout.addWidget(self.search_input)
        self.status_layout.addWidget(self.search_prev_btn)
        self.status_layout.addWidget(self.search_next_btn)
        self.status_layout.addWidget(self.search_case_cb)
        self.status_layout.addWidget(self.search_status_label)
        self.status_layout.addWidget(self.fold_all_btn)
        self.status_layout.addWidget(self.unfold_all_btn)
        self.status_layout.addStretch()

        layout.addLayout(self.status_layout)

        # Ctrl+F to focus search
        QShortcut(QKeySequence("Ctrl+F"), self, self.search_input.setFocus)

        # Body View
        self.body_view = FoldableCodeView(self, indent_size=self.indent_size)
        set_widget_id(self.body_view, RESPONSE_BODY)
        self.body_view.setReadOnly(True)
        self.body_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.body_view.customContextMenuRequested.connect(self.show_context_menu)
        self.json_highlighter = JsonHighlighter(self.body_view.document())
        self.mask_controller = ResponseMaskController(self.body_view, self)
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

    def _search_text_or_clear(self) -> str | None:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return None
        return text

    def _track_search_result(self, source: str) -> None:
        total = self._update_match_count()
        self._metrics.track_gui_response_search_action(
            source=source, has_matches=(total > 0)
        )
        logger.debug("response_search_find source=%s matches=%d", source, total)

    def _find_next(self, source: str = "next") -> None:
        text = self._search_text_or_clear()
        if text is None:
            return
        found = self.body_view.find(text, self._search_flags(backward=False))
        if found:
            self.body_view.reveal_block(self.body_view.textCursor().blockNumber())
        self._track_search_result(source)

    def _find_previous(self, source: str = "previous") -> None:
        text = self._search_text_or_clear()
        if text is None:
            return
        found = self.body_view.find(text, self._search_flags(backward=True))
        if found:
            self.body_view.reveal_block(self.body_view.textCursor().blockNumber())
        self._track_search_result(source)

    def _is_large_document(self) -> bool:
        return len(self.body_view.toPlainText()) > LARGE_DOC_CHAR_THRESHOLD

    def _count_matches(self) -> tuple[int, bool]:
        text = self.search_input.text()
        if not text:
            return 0, False
        saved = self.body_view.textCursor()
        doc = self.body_view.document()
        cursor = QTextCursor(doc)
        flags = self._search_flags(backward=False)
        count = 0
        capped = False
        match_cap = MATCH_COUNT_CAP if self._is_large_document() else None
        while True:
            cursor = doc.find(text, cursor, flags)
            if cursor.isNull():
                break
            count += 1
            if match_cap is not None and count >= match_cap:
                probe = doc.find(text, cursor, flags)
                capped = not probe.isNull()
                break
        self.body_view.setTextCursor(saved)
        return count, capped

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
            if idx > MATCH_INDEX_SAFETY_LIMIT:
                return 0

    def _update_match_count(self) -> int:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return 0
        total, capped = self._count_matches()
        if total == 0:
            self.search_status_label.setText("No matches")
            return 0
        current = self._current_match_index()
        total_label = f"{total}+" if capped else str(total)
        if current > 0:
            self.search_status_label.setText(f"{current} of {total_label}")
        else:
            suffix = "+" if capped else ""
            self.search_status_label.setText(f"{total}{suffix} match(es)")
        return total

    def _schedule_search_text_changed(self) -> None:
        if not self.search_input.text():
            self._search_timer.stop()
            self._on_search_text_changed()
            return
        if self._is_large_document():
            self._search_timer.start()
            return
        self._search_timer.stop()
        self._on_search_text_changed()

    def _on_search_text_changed(self) -> None:
        text = self.search_input.text()
        if not text:
            self.search_status_label.setText("")
            return
        self.body_view.moveCursor(QTextCursor.Start)
        found = self.body_view.find(text, self._search_flags(backward=False))
        if found:
            self.body_view.reveal_block(self.body_view.textCursor().blockNumber())
        total = self._update_match_count()
        self._metrics.track_gui_response_search_action(source="typed", has_matches=(total > 0))
        logger.debug("response_search_typed query_len=%d matches=%d", len(text), total)

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
                    action.triggered.connect(partial(self.emit_variable_set, key, clean_text))
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

        # 3. Fold actions (if fold regions exist)
        if self.body_view.fold_controller().regions():
            menu.addSeparator()
            fold_all_action = menu.addAction("Fold All")
            fold_all_action.triggered.connect(self.body_view.fold_all)
            unfold_all_action = menu.addAction("Unfold All")
            unfold_all_action.triggered.connect(self.body_view.unfold_all)

        menu.exec(self.body_view.mapToGlobal(pos))

    def emit_variable_set(self, key, value, checked=False):
        self.variable_set_requested.emit(key, value)

    def set_indent_size(self, size: int):
        self.indent_size = size
        if self._last_response is not None:
            self.display_response(self._last_response, hidden_fields=self._last_hidden_fields)
            return
        # Refresh current view if it contains JSON
        text = self.body_view.toPlainText()
        if not text or len(text) > LARGE_DOC_CHAR_THRESHOLD:
            return
        try:
            parsed = json.loads(text)
            pretty_json = json.dumps(parsed, indent=self.indent_size)
            self.body_view.setText(pretty_json)
        except Exception:
            pass

    def clear_body(self):
        """Clears the response body and status labels."""
        self._search_timer.stop()
        self.mask_controller.clear()
        self._last_response = None
        self._last_hidden_fields = None
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

    def display_response(
        self,
        response: ResponseData,
        hidden_fields: Sequence[str] | None = None,
    ):
        self._search_timer.stop()
        self.status_label.setText(f"Status: {response.status_code}")
        self.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        self.size_label.setText(f"Size: {response.size} bytes")
        self.search_input.clear()
        self.search_status_label.setText("")

        self._last_response = response
        self._last_hidden_fields = list(hidden_fields) if hidden_fields is not None else None
        self.mask_controller.clear()

        body_str = (
            response.body
            if isinstance(response.body, str)
            else response.body.decode("utf-8", errors="replace")
        )
        detected_format = detect_body_format(response.headers, body_str)
        self.body_view.set_body_format(detected_format)
        logger.info(
            "response_view_displayed status=%s size=%d format=%s",
            response.status_code,
            response.size,
            detected_format.value,
        )

        if detected_format == BodyFormat.JSON:
            self.json_highlighter.setDocument(self.body_view.document())
        else:
            self.json_highlighter.setDocument(None)

        if len(body_str) > LARGE_DOC_CHAR_THRESHOLD:
            logger.info(
                "display_response_skip_pretty_print body_chars=%d threshold=%d",
                len(body_str),
                LARGE_DOC_CHAR_THRESHOLD,
            )
            if hidden_fields:
                logger.debug(
                    "response_masking_large_doc_fallback payload_size=%d threshold=%d",
                    len(body_str),
                    LARGE_DOC_CHAR_THRESHOLD,
                )
            self.body_view.setText(body_str)
        else:
            if detected_format == BodyFormat.JSON:
                if hidden_fields:
                    try:
                        pretty_json, spans = format_masked_json(
                            body_str, hidden_fields, indent=self.indent_size
                        )
                        self.body_view.setText(pretty_json)
                        self.mask_controller.set_masked_spans(spans)
                        if spans:
                            self._metrics.track_hidden_value_mask_applied("gui_response")
                        logger.debug(
                            "response_masking_initialized span_count=%d selectors_count=%d",
                            len(spans),
                            len(hidden_fields),
                        )
                    except Exception:
                        logger.debug("response_masking_failed")
                        self.body_view.setText(body_str)
                else:
                    try:
                        parsed = json.loads(body_str)
                        pretty_json = json.dumps(parsed, indent=self.indent_size)
                        self.body_view.setText(pretty_json)
                    except Exception:
                        self.body_view.setText(body_str)
            else:
                self.body_view.setText(body_str)

        self.body_view.fold_controller().ensure_scanned()
