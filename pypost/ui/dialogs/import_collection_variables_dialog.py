"""Dialog allowing users to inspect collection variables, select presets, and import."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable

from PySide6.QtCore import (
    QAbstractItemModel,
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    QThread,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from pypost.core.collection_variable_import import (
    ConflictStrategy,
    ImportSummary,
    format_variable_value,
    import_collection_variables_to_environment,
)
from pypost.core.constants import HIDDEN_MASK
from pypost.models.models import Collection, Environment
from pypost.ui.widget_ids import (
    IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON,
    IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON,
    IMPORT_COLLECTION_DESELECT_ALL_BUTTON,
    IMPORT_COLLECTION_PRESET_COMBO,
    IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX,
    IMPORT_COLLECTION_SELECT_ALL_BUTTON,
    IMPORT_COLLECTION_SOURCE_COMBO,
    IMPORT_COLLECTION_VARIABLES_DIALOG,
    IMPORT_COLLECTION_VARS_TABLE,
    set_widget_id,
)

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


class HeaderItemProxy:
    """Backward-compatibility proxy for horizontalHeaderItem(col)."""

    def __init__(self, text: str) -> None:
        self._text = text

    def text(self) -> str:
        return self._text


class TableItemProxy:
    """Backward-compatibility proxy mimicking QTableWidgetItem."""

    def __init__(
        self,
        model: CollectionVariablesTableModel,
        row: int,
        col: int,
    ) -> None:
        self._model = model
        self._row = row
        self._col = col

    def text(self) -> str:
        idx = self._model.index(self._row, self._col)
        val = self._model.data(idx, Qt.ItemDataRole.DisplayRole)
        return str(val) if val is not None else ""

    def setText(self, text: str) -> None:
        idx = self._model.index(self._row, self._col)
        self._model.setData(idx, text, Qt.ItemDataRole.DisplayRole)

    def checkState(self) -> Qt.CheckState:
        idx = self._model.index(self._row, self._col)
        val = self._model.data(idx, Qt.ItemDataRole.CheckStateRole)
        if isinstance(val, Qt.CheckState):
            return val
        return Qt.CheckState.Checked if val else Qt.CheckState.Unchecked

    def setCheckState(self, state: Qt.CheckState) -> None:
        idx = self._model.index(self._row, self._col)
        self._model.setData(idx, state, Qt.ItemDataRole.CheckStateRole)

    def flags(self) -> Qt.ItemFlag:
        idx = self._model.index(self._row, self._col)
        return self._model.flags(idx)


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


class ConflictStrategyDelegate(QStyledItemDelegate):
    """Delegate providing on-demand QComboBox editing for colliding strategy cells."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def createEditor(
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        if index.column() != COL_STRATEGY:
            return super().createEditor(parent, option, index)
        model = index.model()
        if not isinstance(model, CollectionVariablesTableModel):
            return super().createEditor(parent, option, index)
        rec = model.get_record(index.row())
        if rec is None or not rec.is_collision:
            return super().createEditor(parent, option, index)

        combo = QComboBox(parent)
        set_widget_id(combo, f"{IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX}{rec.name}")
        combo.addItem("Keep Current", userData=ConflictStrategy.SKIP)
        combo.addItem("Overwrite", userData=ConflictStrategy.OVERWRITE)
        combo.currentIndexChanged.connect(lambda: self.commitAndCloseEditor(combo))
        return combo

    def commitAndCloseEditor(self, editor: QWidget) -> None:
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)

    def setEditorData(
        self,
        editor: QWidget,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, QComboBox):
            val = index.data(Qt.ItemDataRole.DisplayRole)
            idx = editor.findText(val)
            if idx >= 0:
                editor.setCurrentIndex(idx)

    def setModelData(
        self,
        editor: QWidget,
        model: QAbstractItemModel,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        if isinstance(editor, QComboBox):
            text = editor.currentText()
            strat = ConflictStrategy.OVERWRITE if text == "Overwrite" else ConflictStrategy.SKIP
            logger.debug(
                "conflict_strategy_delegate_committed row=%d strategy=%s",
                index.row(),
                strat.value,
            )
            model.setData(index, strat, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(
        self,
        editor: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        editor.setGeometry(option.rect)


class CollectionVariablesTableView(QTableView):
    """Virtualized table view with backward-compatibility proxies for legacy tests."""

    itemChanged = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proxies: dict[tuple[int, int], TableItemProxy] = {}
        self._strategy_combos: dict[int, QComboBox] = {}

    def setModel(self, model: QAbstractItemModel | None) -> None:
        old_model = self.model()
        if old_model is not None:
            try:
                old_model.dataChanged.disconnect(self._on_model_data_changed)
            except Exception:
                pass
        super().setModel(model)
        self._proxies.clear()
        self._strategy_combos.clear()
        if model is not None:
            model.dataChanged.connect(self._on_model_data_changed)

    def _on_model_data_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        roles: list[int] | None = None,
    ) -> None:
        for r in range(top_left.row(), bottom_right.row() + 1):
            if r in self._strategy_combos:
                combo = self._strategy_combos[r]
                m = self.model()
                if isinstance(m, CollectionVariablesTableModel):
                    strat = m.get_strategy(r)
                    target_text = (
                        "Overwrite" if strat == ConflictStrategy.OVERWRITE else "Keep Current"
                    )
                    idx = combo.findText(target_text)
                    if idx >= 0 and combo.currentIndex() != idx:
                        combo.blockSignals(True)
                        combo.setCurrentIndex(idx)
                        combo.blockSignals(False)
            if top_left.row() == bottom_right.row():
                for c in range(top_left.column(), bottom_right.column() + 1):
                    proxy = self.item(r, c)
                    if proxy is not None:
                        self.itemChanged.emit(proxy)

    def columnCount(self) -> int:
        m = self.model()
        return m.columnCount() if m is not None else 0

    def rowCount(self) -> int:
        m = self.model()
        return m.rowCount() if m is not None else 0

    def horizontalHeaderItem(self, col: int) -> HeaderItemProxy | None:
        m = self.model()
        if m is None or col < 0 or col >= m.columnCount():
            return None
        text = str(
            m.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) or ""
        )
        return HeaderItemProxy(text)

    def item(self, row: int, col: int) -> TableItemProxy | None:
        m = self.model()
        if not isinstance(m, CollectionVariablesTableModel):
            return None
        if row < 0 or row >= m.rowCount() or col < 0 or col >= m.columnCount():
            return None
        key = (row, col)
        if key not in self._proxies:
            self._proxies[key] = TableItemProxy(m, row, col)
        return self._proxies[key]

    def cellWidget(self, row: int, col: int) -> QWidget | None:
        m = self.model()
        if not isinstance(m, CollectionVariablesTableModel):
            return None
        if col != COL_STRATEGY:
            return None
        rec = m.get_record(row)
        if rec is None or not rec.is_collision:
            return None
        if row not in self._strategy_combos:
            combo = QComboBox(parent=None)
            set_widget_id(combo, f"{IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX}{rec.name}")
            combo.addItem("Keep Current", userData=ConflictStrategy.SKIP)
            combo.addItem("Overwrite", userData=ConflictStrategy.OVERWRITE)
            if rec.strategy == ConflictStrategy.OVERWRITE:
                combo.setCurrentIndex(1)
            else:
                combo.setCurrentIndex(0)

            def _on_combo_index_changed(idx: int, target_row: int = row) -> None:
                strat = ConflictStrategy.OVERWRITE if idx == 1 else ConflictStrategy.SKIP
                m.setData(
                    m.index(target_row, COL_STRATEGY),
                    strat,
                    Qt.ItemDataRole.EditRole,
                )

            combo.currentIndexChanged.connect(_on_combo_index_changed)
            self._strategy_combos[row] = combo
        return self._strategy_combos[row]


class CollectionFetchWorker(QThread):
    """Background worker for non-blocking remote collection retrieval."""

    fetch_completed = Signal(object, int)
    fetch_failed = Signal(Exception, int)

    def __init__(
        self,
        library_service: Any,
        connection_id: str,
        collection_path: str,
        generation_id: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.library_service = library_service
        self.connection_id = connection_id
        self.collection_path = collection_path
        self.generation_id = generation_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()
        logger.debug(
            "collection_variable_fetch_worker_cancelled generation_id=%d connection_id=%s",
            self.generation_id,
            self.connection_id,
        )

    def run(self) -> None:
        logger.debug(
            "collection_variable_fetch_worker_started generation_id=%d connection_id=%s path=%s",
            self.generation_id,
            self.connection_id,
            self.collection_path,
        )
        try:
            col = self.library_service.read_collection(
                self.connection_id,
                self.collection_path,
            )
            if not self._cancelled and not self.isInterruptionRequested():
                logger.debug(
                    "collection_variable_fetch_worker_completed generation_id=%d",
                    self.generation_id,
                )
                self.fetch_completed.emit(col, self.generation_id)
            else:
                logger.debug(
                    "collection_variable_fetch_worker_interrupted generation_id=%d",
                    self.generation_id,
                )
        except Exception as exc:
            if not self._cancelled and not self.isInterruptionRequested():
                logger.warning(
                    "collection_variable_fetch_worker_failed generation_id=%d error=%s",
                    self.generation_id,
                    exc,
                )
                self.fetch_failed.emit(exc, self.generation_id)
            else:
                logger.debug(
                    "collection_variable_fetch_worker_interrupted_on_error generation_id=%d "
                    "error=%s",
                    self.generation_id,
                    exc,
                )


class ImportCollectionVariablesDialog(QDialog):
    """Dialog allowing users to inspect collection variables, choose presets and conflict policies.
    """

    def __init__(
        self,
        target_environment: Environment,
        workspace_collections: list[Collection] | Iterable[Collection] | None = None,
        library_service: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Collection Variables")
        self.resize(850, 520)
        set_widget_id(self, IMPORT_COLLECTION_VARIABLES_DIALOG)

        self.target_environment = target_environment
        self.workspace_collections: list[Collection] = list(workspace_collections or [])
        self.library_service = library_service
        self._summary: ImportSummary | None = None
        self._current_collection: Collection | None = None
        self._fetch_generation: int = 0
        self._active_fetch_worker: CollectionFetchWorker | None = None

        logger.info(
            "collection_variable_import_dialog_opened env_name=%s",
            self.target_environment.name,
        )

        layout = QVBoxLayout(self)

        # Source Selection (Collection + Preset)
        source_layout = QHBoxLayout()

        col_label = QLabel("Source Collection:")
        self.collection_combo = QComboBox()
        set_widget_id(self.collection_combo, IMPORT_COLLECTION_SOURCE_COMBO)
        source_layout.addWidget(col_label)
        source_layout.addWidget(self.collection_combo, 2)

        preset_label = QLabel("Preset Profile:")
        self.preset_combo = QComboBox()
        set_widget_id(self.preset_combo, IMPORT_COLLECTION_PRESET_COMBO)
        source_layout.addWidget(preset_label)
        source_layout.addWidget(self.preset_combo, 1)

        layout.addLayout(source_layout)

        # Loading container
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 4, 0, 4)
        self.loading_label = QLabel("Loading collection...")
        self.cancel_loading_btn = QPushButton("Cancel")
        self.cancel_loading_btn.clicked.connect(self._on_cancel_loading)
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.cancel_loading_btn)
        loading_layout.addStretch()
        self.loading_container.setVisible(False)
        layout.addWidget(self.loading_container)

        # Error container
        self.error_container = QWidget()
        error_layout = QHBoxLayout(self.error_container)
        error_layout.setContentsMargins(0, 4, 0, 4)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.retry_fetch_btn = QPushButton("Retry")
        self.retry_fetch_btn.clicked.connect(self._on_retry_fetch)
        error_layout.addWidget(self.error_label)
        error_layout.addWidget(self.retry_fetch_btn)
        error_layout.addStretch()
        self.error_container.setVisible(False)
        layout.addWidget(self.error_container)

        # Virtualized variables table
        self.vars_table = CollectionVariablesTableView()
        set_widget_id(self.vars_table, IMPORT_COLLECTION_VARS_TABLE)
        self._model = CollectionVariablesTableModel(self.target_environment, self)
        self.vars_table.setModel(self._model)
        self._strategy_delegate = ConflictStrategyDelegate(self.vars_table)
        self.vars_table.setItemDelegateForColumn(COL_STRATEGY, self._strategy_delegate)

        header = self.vars_table.horizontalHeader()
        header.setSectionResizeMode(COL_SELECT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_CURRENT_VALUE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_CANDIDATE_VALUE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_STRATEGY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_SECRET, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_DESC, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.vars_table)

        # Table quick actions and bulk controls
        table_actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        set_widget_id(self.select_all_btn, IMPORT_COLLECTION_SELECT_ALL_BUTTON)
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("Deselect All")
        set_widget_id(self.deselect_all_btn, IMPORT_COLLECTION_DESELECT_ALL_BUTTON)
        self.deselect_all_btn.clicked.connect(self.deselect_all)

        self.bulk_keep_current_btn = QPushButton("Keep All Collisions")
        set_widget_id(self.bulk_keep_current_btn, IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON)
        self.bulk_keep_current_btn.clicked.connect(
            lambda: self.bulk_set_collision_strategy(ConflictStrategy.SKIP)
        )
        self.bulk_overwrite_btn = QPushButton("Overwrite All Collisions")
        set_widget_id(self.bulk_overwrite_btn, IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON)
        self.bulk_overwrite_btn.clicked.connect(
            lambda: self.bulk_set_collision_strategy(ConflictStrategy.OVERWRITE)
        )

        table_actions_layout.addWidget(self.select_all_btn)
        table_actions_layout.addWidget(self.deselect_all_btn)
        table_actions_layout.addWidget(self.bulk_keep_current_btn)
        table_actions_layout.addWidget(self.bulk_overwrite_btn)
        table_actions_layout.addStretch()
        layout.addLayout(table_actions_layout)

        # Summary label
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        # Button Box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.import_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if self.import_button:
            self.import_button.setText("Import")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Hook signals
        self._model.selection_changed.connect(self._update_preview_summary)
        self._model.strategy_changed.connect(self._on_model_strategy_changed)

        # Populate collection options
        self.collection_combo.blockSignals(True)
        for col in self.workspace_collections:
            self.collection_combo.addItem(f"{col.name} (Workspace)", userData=col)

        if self.library_service is not None:
            try:
                connections = self.library_service.list_connections()
                for conn in connections:
                    manifest_cols = self.library_service.list_manifest_collections(conn.stable_id)
                    for mcol in manifest_cols:
                        col_name = mcol.get("name") or mcol.get("path")
                        label = f"{col_name} ({conn.name or conn.stable_id})"
                        self.collection_combo.addItem(
                            label,
                            userData=("library", conn.stable_id, mcol["path"]),
                        )
            except Exception as exc:
                logger.warning(
                    "collection_variable_import_library_populate_failed error=%s",
                    exc,
                    exc_info=True,
                )

        if self.workspace_collections:
            self.collection_combo.setCurrentIndex(0)
        else:
            self.collection_combo.setCurrentIndex(-1)
        self.collection_combo.blockSignals(False)

        self.collection_combo.currentIndexChanged.connect(self._on_collection_changed)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)

        if self.workspace_collections:
            self._load_collection_into_view(self.workspace_collections[0])
        else:
            self._update_preview_summary()

        self.show()

    @property
    def summary(self) -> ImportSummary | None:
        """The result summary of the completed import, or None if cancelled."""
        return self._summary

    def _get_selected_collection(self) -> Collection | None:
        data = self.collection_combo.currentData()
        if isinstance(data, Collection):
            return data
        if isinstance(data, tuple) and len(data) == 3 and data[0] == "library":
            return self._current_collection
        return None

    def _get_selected_preset(self) -> str | None:
        text = self.preset_combo.currentText().strip()
        if not text or text == "(Base Defaults)":
            return None
        return text

    def _on_collection_changed(self) -> None:
        data = self.collection_combo.currentData()
        if isinstance(data, Collection):
            self._fetch_generation += 1
            if self._active_fetch_worker is not None:
                logger.debug(
                    "collection_variable_fetch_cancelled_by_selection gen=%d",
                    self._active_fetch_worker.generation_id,
                )
                self._active_fetch_worker.cancel()
                self._active_fetch_worker = None
            self.loading_container.setVisible(False)
            self.error_container.setVisible(False)
            self.preset_combo.setEnabled(True)
            self.vars_table.setEnabled(True)
            self._load_collection_into_view(data)
        elif isinstance(data, tuple) and len(data) == 3 and data[0] == "library":
            self._start_fetch_remote_collection(data[1], data[2])
        else:
            self._fetch_generation += 1
            if self._active_fetch_worker is not None:
                logger.debug(
                    "collection_variable_fetch_cancelled_by_selection gen=%d",
                    self._active_fetch_worker.generation_id,
                )
                self._active_fetch_worker.cancel()
                self._active_fetch_worker = None
            self.loading_container.setVisible(False)
            self.error_container.setVisible(False)
            self._load_collection_into_view(None)

    def _start_fetch_remote_collection(self, conn_id: str, path: str) -> None:
        self._fetch_generation += 1
        gen = self._fetch_generation

        if self._active_fetch_worker is not None:
            logger.debug(
                "collection_variable_cancelling_previous_worker gen=%d",
                self._active_fetch_worker.generation_id,
            )
            self._active_fetch_worker.cancel()
            self._active_fetch_worker = None

        logger.info(
            "collection_variable_remote_fetch_started connection_id=%s path=%s gen=%d",
            conn_id,
            path,
            gen,
        )

        self.error_container.setVisible(False)
        self.loading_container.setVisible(True)
        self.loading_label.setText("Loading collection from library...")
        self.cancel_loading_btn.setEnabled(True)

        if self.import_button is not None:
            self.import_button.setEnabled(False)
        self.preset_combo.setEnabled(False)
        self.vars_table.setEnabled(False)

        self._model.load_collection(None)
        self._update_preview_summary()

        worker = CollectionFetchWorker(
            library_service=self.library_service,
            connection_id=conn_id,
            collection_path=path,
            generation_id=gen,
            parent=self,
        )
        worker.fetch_completed.connect(self._on_fetch_completed)
        worker.fetch_failed.connect(self._on_fetch_failed)
        self._active_fetch_worker = worker
        worker.start()

    def _on_fetch_completed(self, col: Any, gen: int) -> None:
        if gen != self._fetch_generation:
            logger.warning(
                "collection_variable_remote_fetch_stale_discarded gen=%d current_gen=%d",
                gen,
                self._fetch_generation,
            )
            return

        self._active_fetch_worker = None
        self.loading_container.setVisible(False)
        self.error_container.setVisible(False)
        self.preset_combo.setEnabled(True)
        self.vars_table.setEnabled(True)

        col_name = getattr(col, "name", None) or "None"
        vars_count = len(getattr(col, "variables", []) or [])
        logger.info(
            "collection_variable_remote_fetch_completed gen=%d collection_name=%s vars_count=%d",
            gen,
            col_name,
            vars_count,
        )

        self._load_collection_into_view(col)

    def _on_fetch_failed(self, exc: Exception, gen: int) -> None:
        if gen != self._fetch_generation:
            logger.warning(
                "collection_variable_remote_fetch_error_stale_discarded gen=%d current_gen=%d "
                "error=%s",
                gen,
                self._fetch_generation,
                exc,
            )
            return

        logger.error(
            "collection_variable_remote_fetch_failed gen=%d error=%s",
            gen,
            exc,
            exc_info=True,
        )

        self._active_fetch_worker = None
        self.loading_container.setVisible(False)
        self.error_container.setVisible(True)
        self.error_label.setText(f"Failed to fetch collection: {exc}")
        self.retry_fetch_btn.setEnabled(True)
        self.preset_combo.setEnabled(False)
        self.vars_table.setEnabled(True)

        self._model.load_collection(None)
        self._update_preview_summary()

    def _on_cancel_loading(self) -> None:
        logger.info(
            "collection_variable_remote_fetch_cancelled gen=%d",
            self._fetch_generation,
        )
        self._fetch_generation += 1
        if self._active_fetch_worker is not None:
            self._active_fetch_worker.cancel()
            self._active_fetch_worker = None
        self.loading_container.setVisible(False)
        self.preset_combo.setEnabled(True)
        self.vars_table.setEnabled(True)
        self._model.load_collection(None)
        self._update_preview_summary()

    def _on_retry_fetch(self) -> None:
        logger.info(
            "collection_variable_remote_fetch_retry_requested env_name=%s",
            self.target_environment.name,
        )
        data = self.collection_combo.currentData()
        if isinstance(data, tuple) and len(data) == 3 and data[0] == "library":
            self._start_fetch_remote_collection(data[1], data[2])

    def _load_collection_into_view(self, col: Collection | None) -> None:
        self._current_collection = col
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("(Base Defaults)", userData=None)
        if col and col.presets:
            for preset_name in col.presets.keys():
                self.preset_combo.addItem(preset_name, userData=preset_name)
        self.preset_combo.blockSignals(False)

        self._populate_variables_table()

    def _on_preset_changed(self) -> None:
        preset_name = self._get_selected_preset()
        self._model.update_preset(preset_name)
        self._update_preview_summary()

    def _populate_variables_table(self) -> None:
        col = self._get_selected_collection()
        preset_name = self._get_selected_preset()
        self._model.load_collection(col, preset_name)

        if col is not None and col.variables:
            collision_count = sum(
                1 for v in col.variables if v.name in self.target_environment.variables
            )
            logger.debug(
                "collection_variable_import_table_populated env_name=%s collection_name=%s "
                "total_vars=%d collisions=%d",
                self.target_environment.name,
                col.name,
                len(col.variables),
                collision_count,
            )

        self._update_preview_summary()

    def _on_model_strategy_changed(self, row: int, strategy: Any) -> None:
        rec = self._model.get_record(row)
        var_name = rec.name if rec else f"row_{row}"
        logger.info(
            "collection_variable_import_row_strategy_changed env_name=%s key=%s strategy=%s",
            self.target_environment.name,
            var_name,
            strategy.value,
        )
        self._update_preview_summary()

    def get_row_strategy(self, row: int) -> ConflictStrategy | None:
        """Return the selected ConflictStrategy for row, or None if non-colliding."""
        return self._model.get_strategy(row)

    def set_row_strategy(self, row: int, strategy: ConflictStrategy) -> None:
        """Set the ConflictStrategy combo box for row if it is a colliding row."""
        self._model.set_row_strategy(row, strategy)

    def get_variable_conflict_strategies(self) -> dict[str, ConflictStrategy]:
        """Return a mapping of variable name to chosen ConflictStrategy for all colliding rows."""
        return self._model.get_conflict_strategies()

    def bulk_set_collision_strategy(self, strategy: ConflictStrategy) -> None:
        """Set the ConflictStrategy on all colliding rows to strategy and refresh summary."""
        updated_count = self._model.set_all_collision_strategy(strategy)
        logger.info(
            "collection_variable_import_bulk_strategy_applied env_name=%s strategy=%s count=%d",
            self.target_environment.name,
            strategy.value,
            updated_count,
        )
        self._update_preview_summary()

    def is_row_selected(self, row: int) -> bool:
        rec = self._model.get_record(row)
        if rec is not None:
            return rec.is_selected
        return True

    def set_row_selected(self, row: int, selected: bool) -> None:
        self._model.set_row_selected(row, selected)
        self._update_preview_summary()

    def select_all(self) -> None:
        self._model.set_all_selected(True)
        logger.debug(
            "collection_variable_import_select_all env_name=%s row_count=%d",
            self.target_environment.name,
            self._model.rowCount(),
        )
        self._update_preview_summary()

    def deselect_all(self) -> None:
        self._model.set_all_selected(False)
        logger.debug(
            "collection_variable_import_deselect_all env_name=%s row_count=%d",
            self.target_environment.name,
            self._model.rowCount(),
        )
        self._update_preview_summary()

    def _update_preview_summary(self) -> None:
        col = self._get_selected_collection()
        if col is None or self._model.rowCount() == 0:
            self.summary_label.setText("No collection or variables available.")
            if self.import_button:
                self.import_button.setEnabled(False)
            return

        will_add, will_overwrite, will_keep = self._model.get_summary_counts()
        total_selected = will_add + will_overwrite + will_keep
        if self.import_button:
            self.import_button.setEnabled(total_selected > 0)

        self.summary_label.setText(
            f"{will_add} new to add, {will_overwrite} existing to overwrite, "
            f"{will_keep} existing to keep"
        )

    def reject(self) -> None:
        if self._active_fetch_worker is not None:
            self._active_fetch_worker.cancel()
            self._active_fetch_worker.wait(1000)
            self._active_fetch_worker = None
        logger.info(
            "collection_variable_import_dialog_cancelled env_name=%s",
            self.target_environment.name,
        )
        super().reject()

    def closeEvent(self, event: Any) -> None:
        if self._active_fetch_worker is not None:
            self._active_fetch_worker.cancel()
            self._active_fetch_worker.wait(1000)
            self._active_fetch_worker = None
        super().closeEvent(event)

    def accept(self) -> None:
        if self._active_fetch_worker is not None:
            self._active_fetch_worker.cancel()
            self._active_fetch_worker.wait(1000)
            self._active_fetch_worker = None

        col = self._get_selected_collection()
        if col is None:
            super().accept()
            return

        preset_name = self._get_selected_preset()
        selected_keys: set[str] = self._model.get_selected_keys()
        variable_conflict_strategies = self._model.get_conflict_strategies()
        overwrite_count = sum(
            1 for s in variable_conflict_strategies.values() if s == ConflictStrategy.OVERWRITE
        )
        keep_count = sum(
            1 for s in variable_conflict_strategies.values() if s == ConflictStrategy.SKIP
        )

        logger.info(
            "collection_variable_import_dialog_accepted env_name=%s collection_name=%s "
            "preset=%s selected_count=%d collisions=%d overwrite_collisions=%d keep_collisions=%d",
            self.target_environment.name,
            col.name,
            preset_name,
            len(selected_keys),
            len(variable_conflict_strategies),
            overwrite_count,
            keep_count,
        )

        try:
            self._summary = import_collection_variables_to_environment(
                environment=self.target_environment,
                collection=col,
                conflict_strategy=ConflictStrategy.SKIP,
                selected_keys=selected_keys,
                preset_name=preset_name,
                variable_conflict_strategies=variable_conflict_strategies,
            )
        except Exception as exc:
            logger.error(
                "collection_variable_import_dialog_execution_failed env_name=%s "
                "collection_name=%s error=%s",
                self.target_environment.name,
                col.name,
                exc,
                exc_info=True,
            )
            raise

        logger.info(
            "env_collection_variables_imported env_name=%s collection_name=%s "
            "total=%d added=%d updated=%d skipped=%d invalid=%d newly_hidden=%d",
            self.target_environment.name,
            col.name,
            self._summary.total_imported,
            len(self._summary.added_keys),
            len(self._summary.updated_keys),
            len(self._summary.skipped_keys),
            len(self._summary.invalid_keys),
            len(self._summary.newly_hidden_keys),
        )
        super().accept()
