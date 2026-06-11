"""Debounced format validation and inline error display."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QTextEdit

from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.validate.body_validator import get_validator
from pypost.ui.widgets.validate.validation_error import ValidationError

_DEBOUNCE_MS = 200
_LINE_ERROR_COLOR = QColor(255, 220, 220)
_COLUMN_ERROR_COLOR = QColor(220, 50, 50)


class ValidationController:
    def __init__(
        self,
        editor: QPlainTextEdit,
        body_format: BodyFormat = BodyFormat.JSON,
    ):
        self._editor = editor
        self._body_format = body_format
        self._errors: list[ValidationError] = []

        self._error_label = QLabel(editor)
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        self._style_error_label()

        self._validate_timer = QTimer(editor)
        self._validate_timer.setSingleShot(True)
        self._validate_timer.setInterval(_DEBOUNCE_MS)
        self._validate_timer.timeout.connect(self._run_validate)

        editor.document().contentsChanged.connect(self._schedule_validate)

    def set_body_format(self, body_format: BodyFormat) -> None:
        self._body_format = body_format
        self._schedule_validate()

    def body_format(self) -> BodyFormat:
        return self._body_format

    def errors(self) -> list[ValidationError]:
        return list(self._errors)

    def layout_error_banner(self) -> None:
        if not self._errors:
            self._error_label.hide()
            return

        label_height = self._error_label.sizeHint().height()
        editor_rect = self._editor.contentsRect()
        self._error_label.setGeometry(
            editor_rect.left(),
            editor_rect.bottom() - label_height,
            editor_rect.width(),
            label_height,
        )
        self._error_label.show()
        self._error_label.raise_()

    def clear(self) -> None:
        self._errors = []
        self._editor.setExtraSelections([])
        self._error_label.hide()

    def _style_error_label(self) -> None:
        self._error_label.setStyleSheet(
            "background-color: #fdd; color: #900; padding: 2px 6px; font-size: 11px;"
        )

    def _schedule_validate(self) -> None:
        self._validate_timer.start()

    def _run_validate(self) -> None:
        validator = get_validator(self._body_format)
        self._errors = validator.validate(self._editor.document())
        self._apply_error_display()

    def _apply_error_display(self) -> None:
        if not self._errors:
            self.clear()
            return

        error = self._errors[0]
        self._error_label.setText(
            f"Line {error.line}, column {error.column}: {error.message}"
        )
        self._editor.setExtraSelections(self._build_extra_selections(error))
        self.layout_error_banner()

    def _build_extra_selections(
        self, error: ValidationError
    ) -> list[QTextEdit.ExtraSelection]:
        doc = self._editor.document()
        block = doc.findBlockByNumber(error.line - 1)
        if not block.isValid():
            return []

        selections: list[QTextEdit.ExtraSelection] = []

        line_selection = QTextEdit.ExtraSelection()
        line_format = QTextCharFormat()
        line_format.setBackground(_LINE_ERROR_COLOR)
        line_selection.format = line_format

        line_cursor = QTextCursor(block)
        line_cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock,
            QTextCursor.MoveMode.KeepAnchor,
        )
        line_selection.cursor = line_cursor
        selections.append(line_selection)

        column = max(1, error.column)
        column_pos = block.position() + column - 1
        if column_pos <= block.position() + block.length() - 1:
            column_selection = QTextEdit.ExtraSelection()
            column_format = QTextCharFormat()
            column_format.setUnderlineColor(_COLUMN_ERROR_COLOR)
            column_format.setUnderlineStyle(
                QTextCharFormat.UnderlineStyle.WaveUnderline
            )
            column_selection.format = column_format

            column_cursor = QTextCursor(doc)
            column_cursor.setPosition(column_pos)
            column_cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                1,
            )
            column_selection.cursor = column_cursor
            selections.append(column_selection)

        return selections
