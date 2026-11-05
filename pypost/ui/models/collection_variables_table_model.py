"""Virtualized collection variables table model for import dialog."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
)

from pypost.core.collection_variable_import import (
    ConflictStrategy,
    format_variable_value,
)
from pypost.core.constants import HIDDEN_MASK
from pypost.models.models import Collection, Environment

logger = logging.getLogger(__name__)

COL_SELECT = 0
COL_NAME = 1
COL_CURRENT_VALUE = 2
COL_CANDIDATE_VALUE = 3
COL_STRATEGY = 4
COL_TYPE = 5
COL_SECRET = 6
COL_STATUS = 7
COL_DESC = 8

HEADERS = [
    "",
    "Name",
    "Current Value",
    "Candidate Value",
    "Conflict Strategy",
    "Type",
    "Secret",
    "Status",
    "Description",
]


@dataclass
class CollectionVariableRowRecord:
    """Internal model record holding variable diff and strategy metadata."""

    name: str
    current_display: str
    candidate_display: str
    raw_current: Any
    raw_candidate: Any
    var_default: Any
    strategy: ConflictStrategy
    var_type: str
    is_collection_secret: bool
    is_env_secret: bool
    is_effective_secret: bool
    is_collision: bool
    status: str
    description: str
    is_selected: bool = True


class CollectionVariablesTableModel(QAbstractTableModel):
    """Virtualized table model representing collection variables and conflict diffs."""

    selection_changed = Signal()
    strategy_changed = Signal(int, object)

    def __init__(
        self,
        target_environment: Environment,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._target_environment = target_environment
        self._collection: Collection | None = None
        self._records: list[CollectionVariableRowRecord] = []

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
        return len(HEADERS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(HEADERS):
                return HEADERS[section]
        return None

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._records):
            return None
        rec = self._records[row]

        if role == Qt.ItemDataRole.CheckStateRole:
            if col == COL_SELECT:
                return Qt.CheckState.Checked if rec.is_selected else Qt.CheckState.Unchecked
            return None

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if col == COL_SELECT:
                return ""
            if col == COL_NAME:
                return rec.name
            if col == COL_CURRENT_VALUE:
                return rec.current_display
            if col == COL_CANDIDATE_VALUE:
                return rec.candidate_display
            if col == COL_STRATEGY:
                if rec.is_collision:
                    return (
                        "Overwrite"
                        if rec.strategy == ConflictStrategy.OVERWRITE
                        else "Keep Current"
                    )
                return "—"
            if col == COL_TYPE:
                return rec.var_type
            if col == COL_SECRET:
                return "Yes" if rec.is_collection_secret else "No"
            if col == COL_STATUS:
                return rec.status
            if col == COL_DESC:
                return rec.description

        if role == Qt.ItemDataRole.ToolTipRole:
            if col == COL_DESC:
                return rec.description
            if col in (COL_CURRENT_VALUE, COL_CANDIDATE_VALUE):
                if not rec.is_effective_secret:
                    return (
                        rec.candidate_display
                        if col == COL_CANDIDATE_VALUE
                        else rec.current_display
                    )

        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == COL_SELECT:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        elif index.column() == COL_STRATEGY:
            if 0 <= index.row() < len(self._records) and self._records[index.row()].is_collision:
                flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._records):
            return False
        rec = self._records[row]

        if col == COL_SELECT and role == Qt.ItemDataRole.CheckStateRole:
            checked = (
                value == Qt.CheckState.Checked
                or value == Qt.CheckState.Checked.value
                or value is True
            )
            if rec.is_selected != checked:
                rec.is_selected = checked
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole])
                self.selection_changed.emit()
            return True

        if col == COL_STRATEGY and role in (
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.DisplayRole,
        ):
            if not rec.is_collision:
                return False
            if isinstance(value, ConflictStrategy):
                strat = value
            elif value == "Overwrite":
                strat = ConflictStrategy.OVERWRITE
            else:
                strat = ConflictStrategy.SKIP
            if rec.strategy != strat:
                rec.strategy = strat
                logger.debug(
                    "collection_variables_table_model_strategy_changed row=%d var_name=%s "
                    "strategy=%s",
                    row,
                    rec.name,
                    strat.value,
                )
                self.dataChanged.emit(
                    index,
                    index,
                    [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
                )
                self.strategy_changed.emit(row, strat)
            return True

        if col == COL_CANDIDATE_VALUE and role in (
            Qt.ItemDataRole.EditRole,
            Qt.ItemDataRole.DisplayRole,
        ):
            rec.candidate_display = str(value)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True

        return False

    def get_record(self, row: int) -> CollectionVariableRowRecord | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    def get_strategy(self, row: int) -> ConflictStrategy | None:
        if 0 <= row < len(self._records) and self._records[row].is_collision:
            return self._records[row].strategy
        return None

    def set_row_strategy(self, row: int, strategy: ConflictStrategy) -> None:
        if 0 <= row < len(self._records) and self._records[row].is_collision:
            self.setData(
                self.index(row, COL_STRATEGY),
                strategy,
                Qt.ItemDataRole.EditRole,
            )

    def set_row_selected(self, row: int, selected: bool) -> None:
        if 0 <= row < len(self._records):
            self.setData(
                self.index(row, COL_SELECT),
                Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole,
            )

    def set_all_selected(self, selected: bool) -> None:
        if not self._records:
            return
        changed = False
        for rec in self._records:
            if rec.is_selected != selected:
                rec.is_selected = selected
                changed = True
        if changed:
            top_left = self.index(0, COL_SELECT)
            bottom_right = self.index(len(self._records) - 1, COL_SELECT)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.ItemDataRole.CheckStateRole],
            )
            self.selection_changed.emit()

    def set_all_collision_strategy(self, strategy: ConflictStrategy) -> int:
        if not self._records:
            return 0
        colliding_count = 0
        changed = False
        for rec in self._records:
            if rec.is_collision:
                colliding_count += 1
                if rec.strategy != strategy:
                    rec.strategy = strategy
                    changed = True
        if changed:
            top_left = self.index(0, COL_STRATEGY)
            bottom_right = self.index(len(self._records) - 1, COL_STRATEGY)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
            )
        logger.debug(
            "collection_variables_table_model_bulk_strategy_set strategy=%s "
            "affected_rows=%d total_rows=%d",
            strategy.value,
            colliding_count,
            len(self._records),
        )
        return colliding_count

    def get_summary_counts(self) -> tuple[int, int, int]:
        will_add = 0
        will_overwrite = 0
        will_keep = 0
        for rec in self._records:
            if not rec.is_selected:
                continue
            if rec.is_collision:
                if rec.strategy == ConflictStrategy.OVERWRITE:
                    will_overwrite += 1
                else:
                    will_keep += 1
            else:
                will_add += 1
        return will_add, will_overwrite, will_keep

    def get_selected_keys(self) -> set[str]:
        return {rec.name for rec in self._records if rec.is_selected}

    def get_conflict_strategies(self) -> dict[str, ConflictStrategy]:
        return {rec.name: rec.strategy for rec in self._records if rec.is_collision}

    def load_collection(
        self,
        collection: Collection | None,
        preset_name: str | None = None,
    ) -> None:
        self.beginResetModel()
        self._collection = collection
        self._records.clear()
        if collection and collection.variables:
            preset_values = (
                collection.presets.get(preset_name, {})
                if (preset_name and collection.presets)
                else {}
            )
            for var in collection.variables:
                name = var.name
                is_env_secret = name in self._target_environment.hidden_keys
                is_col_secret = bool(var.secret)
                is_effective_secret = is_env_secret or is_col_secret
                is_collision = name in self._target_environment.variables

                if is_collision:
                    raw_curr = self._target_environment.variables[name]
                    curr_str = format_variable_value(raw_curr)
                    curr_display = HIDDEN_MASK if is_effective_secret else curr_str
                else:
                    raw_curr = None
                    curr_display = "—"

                raw_cand = preset_values.get(name, var.default)
                cand_str = format_variable_value(raw_cand)
                cand_display = HIDDEN_MASK if is_effective_secret else cand_str

                status_str = "Exists (Collision)" if is_collision else "New"
                desc_str = var.description or ""

                rec = CollectionVariableRowRecord(
                    name=name,
                    current_display=curr_display,
                    candidate_display=cand_display,
                    raw_current=raw_curr,
                    raw_candidate=raw_cand,
                    var_default=var.default,
                    strategy=ConflictStrategy.SKIP,
                    var_type=var.type,
                    is_collection_secret=is_col_secret,
                    is_env_secret=is_env_secret,
                    is_effective_secret=is_effective_secret,
                    is_collision=is_collision,
                    status=status_str,
                    description=desc_str,
                    is_selected=True,
                )
                self._records.append(rec)
        self.endResetModel()
        logger.debug(
            "collection_variables_table_model_loaded collection_name=%s row_count=%d "
            "collisions=%d preset=%s",
            self._collection.name if self._collection else "None",
            len(self._records),
            sum(1 for r in self._records if r.is_collision),
            preset_name,
        )

    def update_preset(self, preset_name: str | None) -> None:
        if not self._collection or not self._records:
            return
        preset_values = (
            self._collection.presets.get(preset_name, {})
            if (preset_name and self._collection.presets)
            else {}
        )
        for rec in self._records:
            raw_cand = preset_values.get(rec.name, rec.var_default)
            cand_str = format_variable_value(raw_cand)
            rec.candidate_display = HIDDEN_MASK if rec.is_effective_secret else cand_str
            rec.raw_candidate = raw_cand
        top_left = self.index(0, COL_CANDIDATE_VALUE)
        bottom_right = self.index(len(self._records) - 1, COL_CANDIDATE_VALUE)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
