"""Virtualized collection variables table model for import dialog.

Supports extreme catalogs (50k–100k variables) via LRU chunk materialization and
sparse selection/strategy overlays so model cache overhead stays bounded.
"""
from __future__ import annotations

from collections import OrderedDict
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
from pypost.models.collection_variable import CollectionVariable
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

# Paged materialization budget (PYPOST-1427).
CHUNK_SIZE = 256
MAX_CACHED_CHUNKS = 8


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
    """Virtualized table model representing collection variables and conflict diffs.

    Row records are materialized in fixed-size LRU chunks. Selection and conflict
    strategy mutations are stored in sparse overlays so eviction does not lose
    import decisions across extreme catalogs.
    """

    CHUNK_SIZE = CHUNK_SIZE
    MAX_CACHED_CHUNKS = MAX_CACHED_CHUNKS

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
        self._variables: list[CollectionVariable] = []
        self._preset_name: str | None = None
        self._preset_values: dict[str, Any] = {}
        self._chunk_cache: OrderedDict[int, list[CollectionVariableRowRecord]] = (
            OrderedDict()
        )
        self._selected_default = True
        self._selection_overrides: dict[int, bool] = {}
        self._strategy_default = ConflictStrategy.SKIP
        self._strategy_overrides: dict[int, ConflictStrategy] = {}

    @property
    def cached_record_count(self) -> int:
        """Number of currently materialized row records across the LRU cache."""
        return sum(len(chunk) for chunk in self._chunk_cache.values())

    def rowCount(
        self,
        parent: QModelIndex | QPersistentModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0
        return len(self._variables)

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
        rec = self._ensure_record(row)
        if rec is None:
            return None

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
            rec = self._ensure_record(index.row())
            if rec is not None and rec.is_collision:
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
        rec = self._ensure_record(row)
        if rec is None:
            return False

        if col == COL_SELECT and role == Qt.ItemDataRole.CheckStateRole:
            checked = (
                value == Qt.CheckState.Checked
                or value == Qt.CheckState.Checked.value
                or value is True
            )
            if rec.is_selected != checked:
                rec.is_selected = checked
                self._store_selection_override(row, checked)
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
                self._store_strategy_override(row, strat)
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
        return self._ensure_record(row)

    def get_strategy(self, row: int) -> ConflictStrategy | None:
        rec = self._ensure_record(row)
        if rec is not None and rec.is_collision:
            return rec.strategy
        return None

    def set_row_strategy(self, row: int, strategy: ConflictStrategy) -> None:
        rec = self._ensure_record(row)
        if rec is not None and rec.is_collision:
            self.setData(
                self.index(row, COL_STRATEGY),
                strategy,
                Qt.ItemDataRole.EditRole,
            )

    def set_row_selected(self, row: int, selected: bool) -> None:
        if self._ensure_record(row) is not None:
            self.setData(
                self.index(row, COL_SELECT),
                Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole,
            )

    def set_all_selected(self, selected: bool) -> None:
        if not self._variables:
            return
        self._selected_default = selected
        self._selection_overrides.clear()
        for chunk in self._chunk_cache.values():
            for rec in chunk:
                rec.is_selected = selected
        top_left = self.index(0, COL_SELECT)
        bottom_right = self.index(len(self._variables) - 1, COL_SELECT)
        self.dataChanged.emit(
            top_left,
            bottom_right,
            [Qt.ItemDataRole.CheckStateRole],
        )
        self.selection_changed.emit()

    def set_all_collision_strategy(self, strategy: ConflictStrategy) -> int:
        if not self._variables:
            return 0
        env_vars = self._target_environment.variables
        colliding_count = 0
        for var in self._variables:
            if var.name in env_vars:
                colliding_count += 1
        self._strategy_default = strategy
        self._strategy_overrides.clear()
        for chunk in self._chunk_cache.values():
            for rec in chunk:
                if rec.is_collision:
                    rec.strategy = strategy
        if colliding_count:
            top_left = self.index(0, COL_STRATEGY)
            bottom_right = self.index(len(self._variables) - 1, COL_STRATEGY)
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
            )
        logger.debug(
            "collection_variables_table_model_bulk_strategy_set strategy=%s "
            "affected_rows=%d total_rows=%d cached_records=%d",
            strategy.value,
            colliding_count,
            len(self._variables),
            self.cached_record_count,
        )
        return colliding_count

    def get_summary_counts(self) -> tuple[int, int, int]:
        will_add = 0
        will_overwrite = 0
        will_keep = 0
        env_vars = self._target_environment.variables
        for row, var in enumerate(self._variables):
            if not self._is_selected(row):
                continue
            if var.name in env_vars:
                if self._strategy_for_row(row) == ConflictStrategy.OVERWRITE:
                    will_overwrite += 1
                else:
                    will_keep += 1
            else:
                will_add += 1
        return will_add, will_overwrite, will_keep

    def get_selected_keys(self) -> set[str]:
        return {
            var.name
            for row, var in enumerate(self._variables)
            if self._is_selected(row)
        }

    def get_conflict_strategies(self) -> dict[str, ConflictStrategy]:
        env_vars = self._target_environment.variables
        return {
            var.name: self._strategy_for_row(row)
            for row, var in enumerate(self._variables)
            if var.name in env_vars
        }

    def load_collection(
        self,
        collection: Collection | None,
        preset_name: str | None = None,
    ) -> None:
        self.beginResetModel()
        self._collection = collection
        # Bind catalog list by reference — do not eagerly copy/materialize records.
        self._variables = (
            collection.variables
            if collection and collection.variables
            else []
        )
        self._preset_name = preset_name
        self._preset_values = (
            collection.presets.get(preset_name, {})
            if (collection and preset_name and collection.presets)
            else {}
        )
        self._chunk_cache.clear()
        self._selection_overrides.clear()
        self._strategy_overrides.clear()
        self._selected_default = True
        self._strategy_default = ConflictStrategy.SKIP
        self.endResetModel()
        collisions = sum(
            1
            for var in self._variables
            if var.name in self._target_environment.variables
        )
        logger.debug(
            "collection_variables_table_model_loaded collection_name=%s "
            "row_count=%d collisions=%d preset=%s cached_records=%d "
            "chunk_size=%d max_cached_chunks=%d",
            self._collection.name if self._collection else "None",
            len(self._variables),
            collisions,
            preset_name,
            self.cached_record_count,
            self.CHUNK_SIZE,
            self.MAX_CACHED_CHUNKS,
        )

    def update_preset(self, preset_name: str | None) -> None:
        if not self._collection or not self._variables:
            return
        self._preset_name = preset_name
        self._preset_values = (
            self._collection.presets.get(preset_name, {})
            if (preset_name and self._collection.presets)
            else {}
        )
        # Drop cached candidate displays; rematerialize on next access.
        evicted = len(self._chunk_cache)
        self._chunk_cache.clear()
        top_left = self.index(0, COL_CANDIDATE_VALUE)
        bottom_right = self.index(len(self._variables) - 1, COL_CANDIDATE_VALUE)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
        logger.debug(
            "collection_variables_table_model_preset_updated preset=%s "
            "row_count=%d evicted_chunks=%d",
            preset_name,
            len(self._variables),
            evicted,
        )

    def _is_selected(self, row: int) -> bool:
        if row in self._selection_overrides:
            return self._selection_overrides[row]
        return self._selected_default

    def _strategy_for_row(self, row: int) -> ConflictStrategy:
        if row in self._strategy_overrides:
            return self._strategy_overrides[row]
        return self._strategy_default

    def _store_selection_override(self, row: int, selected: bool) -> None:
        if selected == self._selected_default:
            self._selection_overrides.pop(row, None)
        else:
            self._selection_overrides[row] = selected

    def _store_strategy_override(self, row: int, strategy: ConflictStrategy) -> None:
        if strategy == self._strategy_default:
            self._strategy_overrides.pop(row, None)
        else:
            self._strategy_overrides[row] = strategy

    def _ensure_record(self, row: int) -> CollectionVariableRowRecord | None:
        if row < 0 or row >= len(self._variables):
            return None
        chunk_idx = row // self.CHUNK_SIZE
        chunk = self._touch_chunk(chunk_idx)
        return chunk[row % self.CHUNK_SIZE]

    def _touch_chunk(self, chunk_idx: int) -> list[CollectionVariableRowRecord]:
        cached = self._chunk_cache.get(chunk_idx)
        if cached is not None:
            self._chunk_cache.move_to_end(chunk_idx)
            return cached
        records = self._materialize_chunk(chunk_idx)
        self._chunk_cache[chunk_idx] = records
        self._chunk_cache.move_to_end(chunk_idx)
        while len(self._chunk_cache) > self.MAX_CACHED_CHUNKS:
            evicted_idx, evicted_rows = self._chunk_cache.popitem(last=False)
            logger.debug(
                "collection_variables_table_model_chunk_evicted chunk_idx=%d "
                "rows=%d cached_chunks=%d cached_records=%d",
                evicted_idx,
                len(evicted_rows),
                len(self._chunk_cache),
                self.cached_record_count,
            )
        return records

    def _materialize_chunk(
        self,
        chunk_idx: int,
    ) -> list[CollectionVariableRowRecord]:
        start = chunk_idx * self.CHUNK_SIZE
        end = min(start + self.CHUNK_SIZE, len(self._variables))
        records = [self._build_record(row) for row in range(start, end)]
        logger.debug(
            "collection_variables_table_model_chunk_fetched chunk_idx=%d "
            "start_row=%d end_row=%d rows=%d cached_chunks=%d",
            chunk_idx,
            start,
            end,
            len(records),
            len(self._chunk_cache) + 1,
        )
        return records

    def _build_record(self, row: int) -> CollectionVariableRowRecord:
        var = self._variables[row]
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

        raw_cand = self._preset_values.get(name, var.default)
        cand_str = format_variable_value(raw_cand)
        cand_display = HIDDEN_MASK if is_effective_secret else cand_str

        status_str = "Exists (Collision)" if is_collision else "New"
        strategy = (
            self._strategy_for_row(row) if is_collision else ConflictStrategy.SKIP
        )
        return CollectionVariableRowRecord(
            name=name,
            current_display=curr_display,
            candidate_display=cand_display,
            raw_current=raw_curr,
            raw_candidate=raw_cand,
            var_default=var.default,
            strategy=strategy,
            var_type=var.type,
            is_collection_secret=is_col_secret,
            is_env_secret=is_env_secret,
            is_effective_secret=is_effective_secret,
            is_collision=is_collision,
            status=status_str,
            description=var.description or "",
            is_selected=self._is_selected(row),
        )
