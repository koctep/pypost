"""Virtualized table model for hidden response field selectors."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush

from pypost.core.field_selector_syntax import (
    FieldSelectorSyntaxResult,
    validate_field_selector,
)
from pypost.ui.styles.ui_tokens import VALIDATION_LINE_BACKGROUND

__all__ = ["HiddenFieldRecord", "HiddenFieldsTableModel"]

HEADER = "Field Selector"
TOOLTIP = "Response field selector or dot-notation path"
_ERROR_BACKGROUND = QBrush(VALIDATION_LINE_BACKGROUND)
_DATA_ROLES = [
    Qt.ItemDataRole.DisplayRole,
    Qt.ItemDataRole.EditRole,
    Qt.ItemDataRole.BackgroundRole,
    Qt.ItemDataRole.ToolTipRole,
]

logger = logging.getLogger(__name__)


def _syntax_for(selector: str) -> FieldSelectorSyntaxResult:
    return validate_field_selector(selector)


@dataclass
class HiddenFieldRecord:
    """Internal record representing a single row in the hidden fields table."""

    selector: str = ""
    syntax: FieldSelectorSyntaxResult = field(
        default_factory=lambda: validate_field_selector("")
    )


def _make_record(selector: str = "") -> HiddenFieldRecord:
    return HiddenFieldRecord(
        selector=selector,
        syntax=_syntax_for(selector),
    )


def _syntax_counts(records: list[HiddenFieldRecord]) -> tuple[int, int, int]:
    """Return (ok_count, invalid_count, empty_count) for cached syntax results."""
    ok_count = 0
    invalid_count = 0
    empty_count = 0
    for record in records:
        if record.syntax.is_empty:
            empty_count += 1
        elif record.syntax.ok:
            ok_count += 1
        else:
            invalid_count += 1
    return ok_count, invalid_count, empty_count


class HiddenFieldsTableModel(QAbstractTableModel):
    """QAbstractTableModel backing HiddenFieldsTable with a trailing blank row."""

    data_changed = Signal()
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._records: list[HiddenFieldRecord] = [_make_record()]

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0
        return len(self._records)

    def columnCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0
        return 1

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and section == 0:
            return HEADER
        if orientation == Qt.Orientation.Vertical and 0 <= section < len(self._records):
            if section == len(self._records) - 1:
                return "*"
            return section + 1
        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or index.column() != 0:
            return None
        row = index.row()
        if row < 0 or row >= len(self._records):
            return None
        record = self._records[row]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return record.selector
        if role == Qt.ItemDataRole.BackgroundRole:
            if not record.syntax.ok and not record.syntax.is_empty:
                return _ERROR_BACKGROUND
            return None
        if role == Qt.ItemDataRole.ToolTipRole:
            if not record.syntax.ok and not record.syntax.is_empty:
                return f"{record.syntax.message} {record.syntax.suggestions}".strip()
            if record.selector.strip():
                return TOOLTIP
            return None
        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid() or index.column() != 0:
            return False
        row = index.row()
        if row < 0 or row >= len(self._records):
            return False

        if role not in (Qt.ItemDataRole.EditRole, Qt.ItemDataRole.DisplayRole):
            return False

        text = str(value).strip()
        is_trailing = row == len(self._records) - 1
        if is_trailing and not text:
            return False

        self._records[row].selector = text
        syntax = _syntax_for(text)
        self._records[row].syntax = syntax
        self.dataChanged.emit(index, index, list(_DATA_ROLES))
        logger.debug(
            "hidden_fields_table_model_set_data_cell "
            "row=%d selector_len=%d ok=%s is_empty=%s",
            row,
            len(text),
            syntax.ok,
            syntax.is_empty,
        )

        if is_trailing and text:
            insert_at = len(self._records)
            self.beginInsertRows(QModelIndex(), insert_at, insert_at)
            self._records.append(_make_record())
            self.endInsertRows()
            logger.debug(
                "hidden_fields_table_model_trailing_row_expanded "
                "edited_row=%d selector_len=%d row_count=%d",
                row,
                len(text),
                len(self._records),
            )

        self.data_changed.emit()
        self.changed.emit()
        return True

    def get_data(self) -> list[str]:
        """Return non-empty selector strings in row order."""
        return [
            record.selector.strip()
            for record in self._records
            if record.selector.strip()
        ]

    def set_data(self, selectors: list[str]) -> None:
        """Replace rows with selectors and ensure one trailing blank row."""
        input_count = len(selectors)
        self.beginResetModel()
        valid = [str(s).strip() for s in selectors if str(s).strip()]
        self._records = [_make_record(s) for s in valid]
        self._records.append(_make_record())
        self.endResetModel()
        ok_count, invalid_count, empty_count = _syntax_counts(self._records)
        logger.debug(
            "hidden_fields_table_model_set_data input_count=%d "
            "valid_count=%d row_count=%d ok_count=%d invalid_count=%d "
            "empty_count=%d",
            input_count,
            len(valid),
            len(self._records),
            ok_count,
            invalid_count,
            empty_count,
        )
        self.data_changed.emit()
        self.changed.emit()

    def add_row(self, selector: str = "") -> int:
        """Append selector or reuse trailing blank; return focused row index."""
        text = str(selector).strip()
        last = len(self._records) - 1
        if last >= 0 and not self._records[last].selector.strip():
            mode = "reuse_trailing" if text else "focus_trailing"
            if text:
                index = self.index(last, 0)
                self.setData(index, text, Qt.ItemDataRole.EditRole)
            syntax_ok = self._records[last].syntax.ok if text else True
            logger.debug(
                "hidden_fields_table_model_add_row mode=%s "
                "focus_row=%d has_text=%s ok=%s row_count=%d",
                mode,
                last,
                bool(text),
                syntax_ok,
                len(self._records),
            )
            return last

        insert_at = len(self._records)
        self.beginInsertRows(QModelIndex(), insert_at, insert_at)
        self._records.append(_make_record(text))
        self.endInsertRows()
        if text:
            blank_at = len(self._records)
            self.beginInsertRows(QModelIndex(), blank_at, blank_at)
            self._records.append(_make_record())
            self.endInsertRows()
        self.data_changed.emit()
        self.changed.emit()
        syntax_ok = self._records[insert_at].syntax.ok if text else True
        logger.debug(
            "hidden_fields_table_model_add_row mode=insert "
            "focus_row=%d has_text=%s ok=%s row_count=%d",
            insert_at,
            bool(text),
            syntax_ok,
            len(self._records),
        )
        return insert_at

    def remove_rows(self, row_indices: list[int]) -> None:
        """Remove selected non-trailing rows; keep exactly one blank trailing row."""
        if not row_indices:
            return
        trailing = len(self._records) - 1
        to_remove = sorted(
            {
                row
                for row in row_indices
                if 0 <= row < len(self._records) and row != trailing
            },
            reverse=True,
        )
        if not to_remove:
            return

        removed = 0
        for row in to_remove:
            if row >= len(self._records):
                continue
            # Skip current trailing blank if indices shifted oddly
            if (
                row == len(self._records) - 1
                and not self._records[row].selector.strip()
            ):
                continue
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._records[row]
            self.endRemoveRows()
            removed += 1

        if not self._records:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self._records.append(_make_record())
            self.endInsertRows()
        elif self._records[-1].selector.strip():
            insert_at = len(self._records)
            self.beginInsertRows(QModelIndex(), insert_at, insert_at)
            self._records.append(_make_record())
            self.endInsertRows()

        logger.debug(
            "hidden_fields_table_model_remove_rows requested=%d removed=%d "
            "row_count=%d",
            len(row_indices),
            removed,
            len(self._records),
        )
        self.data_changed.emit()
        self.changed.emit()
