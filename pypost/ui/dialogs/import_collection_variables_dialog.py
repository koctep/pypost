"""Dialog allowing users to inspect collection variables, select presets, and import."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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

        # Variables Table
        self.vars_table = QTableWidget(0, 9)
        set_widget_id(self.vars_table, IMPORT_COLLECTION_VARS_TABLE)
        self.vars_table.setHorizontalHeaderLabels(
            [
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
        )
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

        # Populate collection options
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

        self.collection_combo.currentIndexChanged.connect(self._on_collection_changed)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        self.vars_table.itemChanged.connect(self._on_table_item_changed)

        if self.collection_combo.count() > 0:
            self._on_collection_changed()
        else:
            self._update_preview_summary()

    @property
    def summary(self) -> ImportSummary | None:
        """The result summary of the completed import, or None if cancelled."""
        return self._summary

    def _get_selected_collection(self) -> Collection | None:
        data = self.collection_combo.currentData()
        if isinstance(data, Collection):
            return data
        if isinstance(data, tuple) and len(data) == 3 and data[0] == "library":
            if self.library_service is not None:
                try:
                    res = self.library_service.read_collection(data[1], data[2])
                    if isinstance(res, Collection):
                        return res
                    return None
                except Exception as exc:
                    logger.error(
                        "collection_variable_import_library_read_failed "
                        "connection_id=%s path=%s error=%s",
                        data[1],
                        data[2],
                        exc,
                        exc_info=True,
                    )
                    return None
        return None

    def _get_selected_preset(self) -> str | None:
        text = self.preset_combo.currentText().strip()
        if not text or text == "(Base Defaults)":
            return None
        return text

    def _on_collection_changed(self) -> None:
        col = self._get_selected_collection()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("(Base Defaults)", userData=None)
        if col and col.presets:
            for preset_name in col.presets.keys():
                self.preset_combo.addItem(preset_name, userData=preset_name)
        self.preset_combo.blockSignals(False)
        self._populate_variables_table()

    def _on_preset_changed(self) -> None:
        col = self._get_selected_collection()
        if col is None:
            return
        preset_name = self._get_selected_preset()
        preset_values = col.presets.get(preset_name, {}) if (preset_name and col.presets) else {}

        var_by_name = {v.name: v for v in (col.variables or [])}
        self.vars_table.blockSignals(True)
        for row in range(self.vars_table.rowCount()):
            name_item = self.vars_table.item(row, COL_NAME)
            if not name_item:
                continue
            var_name = name_item.text().strip()
            var = var_by_name.get(var_name)
            if var:
                is_secret = bool(var.secret) or (var_name in self.target_environment.hidden_keys)
                raw_val = preset_values.get(var.name, var.default)
                val_str = format_variable_value(raw_val)
                display_val = HIDDEN_MASK if is_secret else val_str
                val_item = self.vars_table.item(row, COL_CANDIDATE_VALUE)
                if val_item:
                    val_item.setText(display_val)
                else:
                    new_item = QTableWidgetItem(display_val)
                    new_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    self.vars_table.setItem(row, COL_CANDIDATE_VALUE, new_item)
        self.vars_table.blockSignals(False)
        self._update_preview_summary()

    def _populate_variables_table(self) -> None:
        col = self._get_selected_collection()
        self.vars_table.blockSignals(True)
        self.vars_table.setRowCount(0)
        if col is None or not col.variables:
            self.vars_table.blockSignals(False)
            self._update_preview_summary()
            return

        preset_name = self._get_selected_preset()
        preset_values = col.presets.get(preset_name, {}) if (preset_name and col.presets) else {}

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

        self.vars_table.setRowCount(len(col.variables))
        for i, var in enumerate(col.variables):
            check_item = QTableWidgetItem()
            check_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            check_item.setCheckState(Qt.CheckState.Checked)
            self.vars_table.setItem(i, COL_SELECT, check_item)

            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_NAME, name_item)

            exists = var.name in self.target_environment.variables
            is_secret = bool(var.secret) or (var.name in self.target_environment.hidden_keys)

            if exists:
                raw_current = self.target_environment.variables[var.name]
                current_str = format_variable_value(raw_current)
                current_display = HIDDEN_MASK if is_secret else current_str
            else:
                current_display = "—"

            current_item = QTableWidgetItem(current_display)
            current_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_CURRENT_VALUE, current_item)

            raw_candidate = preset_values.get(var.name, var.default)
            candidate_str = format_variable_value(raw_candidate)
            candidate_display = HIDDEN_MASK if is_secret else candidate_str
            candidate_item = QTableWidgetItem(candidate_display)
            candidate_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_CANDIDATE_VALUE, candidate_item)

            if exists:
                combo = QComboBox()
                set_widget_id(combo, f"{IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX}{var.name}")
                combo.addItem("Keep Current", userData=ConflictStrategy.SKIP)
                combo.addItem("Overwrite", userData=ConflictStrategy.OVERWRITE)
                combo.setCurrentIndex(0)
                combo.currentIndexChanged.connect(self._update_preview_summary)
                self.vars_table.setCellWidget(i, COL_STRATEGY, combo)
            else:
                strategy_item = QTableWidgetItem("—")
                strategy_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.vars_table.setItem(i, COL_STRATEGY, strategy_item)

            type_item = QTableWidgetItem(var.type)
            type_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_TYPE, type_item)

            secret_str = "Yes" if var.secret else "No"
            secret_item = QTableWidgetItem(secret_str)
            secret_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_SECRET, secret_item)

            status_str = "Exists (Collision)" if exists else "New"
            status_item = QTableWidgetItem(status_str)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_STATUS, status_item)

            desc_str = var.description or ""
            desc_item = QTableWidgetItem(desc_str)
            desc_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.vars_table.setItem(i, COL_DESC, desc_item)

        self.vars_table.blockSignals(False)
        self._update_preview_summary()

    def get_row_strategy(self, row: int) -> ConflictStrategy | None:
        """Return the selected ConflictStrategy for row, or None if non-colliding."""
        widget = self.vars_table.cellWidget(row, COL_STRATEGY)
        if isinstance(widget, QComboBox):
            text = widget.currentText()
            if text == "Overwrite":
                return ConflictStrategy.OVERWRITE
            return ConflictStrategy.SKIP
        return None

    def set_row_strategy(self, row: int, strategy: ConflictStrategy) -> None:
        """Set the ConflictStrategy combo box for row if it is a colliding row."""
        widget = self.vars_table.cellWidget(row, COL_STRATEGY)
        if isinstance(widget, QComboBox):
            target_text = "Overwrite" if strategy == ConflictStrategy.OVERWRITE else "Keep Current"
            idx = widget.findText(target_text)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            name_item = self.vars_table.item(row, COL_NAME)
            var_name = name_item.text().strip() if name_item else f"row_{row}"
            logger.debug(
                "collection_variable_import_row_strategy_changed env_name=%s key=%s strategy=%s",
                self.target_environment.name,
                var_name,
                strategy.value,
            )
            self._update_preview_summary()

    def get_variable_conflict_strategies(self) -> dict[str, ConflictStrategy]:
        """Return a mapping of variable name to chosen ConflictStrategy for all colliding rows."""
        result: dict[str, ConflictStrategy] = {}
        for row in range(self.vars_table.rowCount()):
            strat = self.get_row_strategy(row)
            if strat is not None:
                name_item = self.vars_table.item(row, COL_NAME)
                if name_item and name_item.text():
                    result[name_item.text().strip()] = strat
        return result

    def bulk_set_collision_strategy(self, strategy: ConflictStrategy) -> None:
        """Set the ConflictStrategy on all colliding rows to strategy and refresh summary."""
        target_text = "Overwrite" if strategy == ConflictStrategy.OVERWRITE else "Keep Current"
        updated_count = 0
        for row in range(self.vars_table.rowCount()):
            widget = self.vars_table.cellWidget(row, COL_STRATEGY)
            if isinstance(widget, QComboBox):
                idx = widget.findText(target_text)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                    updated_count += 1
        logger.info(
            "collection_variable_import_bulk_strategy_applied env_name=%s strategy=%s count=%d",
            self.target_environment.name,
            strategy.value,
            updated_count,
        )
        self._update_preview_summary()

    def is_row_selected(self, row: int) -> bool:
        widget = self.vars_table.cellWidget(row, COL_SELECT)
        if widget is not None:
            cb = widget.findChild(QCheckBox)
            if cb is not None:
                return cb.isChecked()
        item = self.vars_table.item(row, COL_SELECT)
        if item is not None and (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return item.checkState() == Qt.CheckState.Checked
        return True

    def set_row_selected(self, row: int, selected: bool) -> None:
        widget = self.vars_table.cellWidget(row, COL_SELECT)
        if widget is not None:
            cb = widget.findChild(QCheckBox)
            if cb is not None:
                cb.setChecked(selected)
        item = self.vars_table.item(row, COL_SELECT)
        if item is not None and (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            item.setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)

    def select_all(self) -> None:
        self.vars_table.blockSignals(True)
        for row in range(self.vars_table.rowCount()):
            self.set_row_selected(row, True)
        self.vars_table.blockSignals(False)
        self._update_preview_summary()

    def deselect_all(self) -> None:
        self.vars_table.blockSignals(True)
        for row in range(self.vars_table.rowCount()):
            self.set_row_selected(row, False)
        self.vars_table.blockSignals(False)
        self._update_preview_summary()

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == COL_SELECT:
            self._update_preview_summary()

    def _update_preview_summary(self) -> None:
        col = self._get_selected_collection()
        if col is None or self.vars_table.rowCount() == 0:
            self.summary_label.setText("No collection or variables available.")
            if self.import_button:
                self.import_button.setEnabled(False)
            return

        will_add = 0
        will_overwrite = 0
        will_keep = 0

        for row in range(self.vars_table.rowCount()):
            if not self.is_row_selected(row):
                continue
            name_item = self.vars_table.item(row, COL_NAME)
            if not name_item or not name_item.text():
                continue
            name = name_item.text().strip()
            if name in self.target_environment.variables:
                strat = self.get_row_strategy(row)
                if strat == ConflictStrategy.OVERWRITE:
                    will_overwrite += 1
                else:
                    will_keep += 1
            else:
                will_add += 1

        total_selected = will_add + will_overwrite + will_keep
        if self.import_button:
            self.import_button.setEnabled(total_selected > 0)

        self.summary_label.setText(
            f"{will_add} new to add, {will_overwrite} existing to overwrite, "
            f"{will_keep} existing to keep"
        )

    def reject(self) -> None:
        logger.info(
            "collection_variable_import_dialog_cancelled env_name=%s",
            self.target_environment.name,
        )
        super().reject()

    def accept(self) -> None:
        col = self._get_selected_collection()
        if col is None:
            super().accept()
            return

        preset_name = self._get_selected_preset()
        selected_keys: set[str] = set()
        for row in range(self.vars_table.rowCount()):
            if self.is_row_selected(row):
                name_item = self.vars_table.item(row, COL_NAME)
                if name_item and name_item.text():
                    selected_keys.add(name_item.text().strip())

        variable_conflict_strategies = self.get_variable_conflict_strategies()
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
