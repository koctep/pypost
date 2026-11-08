"""Dialog allowing users to inspect collection variables, select presets, and import."""
from __future__ import annotations

import logging
from typing import Any, Iterable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.collection_variable_import import (
    ConflictStrategy,
    ImportSummary,
    import_collection_variables_to_environment,
)
from pypost.models.models import Collection, Environment
from pypost.ui.delegates.conflict_strategy_delegate import ConflictStrategyDelegate
from pypost.ui.models.collection_variables_table_model import (
    COL_CANDIDATE_VALUE,
    COL_CURRENT_VALUE,
    COL_DESC,
    COL_NAME,
    COL_SECRET,
    COL_SELECT,
    COL_STATUS,
    COL_STRATEGY,
    COL_TYPE,
    HEADERS,
    CollectionVariableRowRecord,
    CollectionVariablesTableModel,
)
from pypost.ui.views.collection_variables_table_view import (
    CollectionVariablesTableView,
    HeaderItemProxy,
    TableItemProxy,
)
from pypost.ui.widget_ids import (
    IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON,
    IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON,
    IMPORT_COLLECTION_CANCEL_DISCOVERY_BUTTON,
    IMPORT_COLLECTION_CANCEL_LOADING_BUTTON,
    IMPORT_COLLECTION_DESELECT_ALL_BUTTON,
    IMPORT_COLLECTION_DISCOVERY_CONTAINER,
    IMPORT_COLLECTION_DISCOVERY_ERROR_CONTAINER,
    IMPORT_COLLECTION_DISCOVERY_ERROR_LABEL,
    IMPORT_COLLECTION_DISCOVERY_LABEL,
    IMPORT_COLLECTION_ERROR_CONTAINER,
    IMPORT_COLLECTION_ERROR_LABEL,
    IMPORT_COLLECTION_LOADING_CONTAINER,
    IMPORT_COLLECTION_LOADING_LABEL,
    IMPORT_COLLECTION_PRESET_COMBO,
    IMPORT_COLLECTION_RETRY_DISCOVERY_BUTTON,
    IMPORT_COLLECTION_RETRY_FETCH_BUTTON,
    IMPORT_COLLECTION_SELECT_ALL_BUTTON,
    IMPORT_COLLECTION_SOURCE_COMBO,
    IMPORT_COLLECTION_VARIABLES_DIALOG,
    IMPORT_COLLECTION_VARS_TABLE,
    set_widget_id,
)
from pypost.ui.workers.collection_fetch_worker import CollectionFetchWorker
from pypost.ui.workers.manifest_discovery_worker import ManifestDiscoveryWorker

logger = logging.getLogger(__name__)

# Backward-compatible re-exports for existing tests and callers.
__all__ = [
    "COL_CANDIDATE_VALUE",
    "COL_CURRENT_VALUE",
    "COL_DESC",
    "COL_NAME",
    "COL_SECRET",
    "COL_SELECT",
    "COL_STATUS",
    "COL_STRATEGY",
    "COL_TYPE",
    "HEADERS",
    "CollectionFetchWorker",
    "CollectionVariableRowRecord",
    "CollectionVariablesTableModel",
    "CollectionVariablesTableView",
    "ConflictStrategyDelegate",
    "HeaderItemProxy",
    "ImportCollectionVariablesDialog",
    "ManifestDiscoveryWorker",
    "TableItemProxy",
]


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
        self._discovery_generation: int = 0
        self._active_discovery_worker: ManifestDiscoveryWorker | None = None

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

        # Discovery container (Dedicated UI for background manifest/catalog discovery)
        self.discovery_container = QWidget()
        set_widget_id(self.discovery_container, IMPORT_COLLECTION_DISCOVERY_CONTAINER)
        discovery_layout = QHBoxLayout(self.discovery_container)
        discovery_layout.setContentsMargins(0, 4, 0, 4)
        self.discovery_label = QLabel("Discovering library collections...")
        set_widget_id(self.discovery_label, IMPORT_COLLECTION_DISCOVERY_LABEL)
        self.cancel_discovery_btn = QPushButton("Cancel")
        set_widget_id(
            self.cancel_discovery_btn, IMPORT_COLLECTION_CANCEL_DISCOVERY_BUTTON
        )
        self.cancel_discovery_btn.clicked.connect(self._on_cancel_discovery)
        discovery_layout.addWidget(self.discovery_label)
        discovery_layout.addWidget(self.cancel_discovery_btn)
        discovery_layout.addStretch()
        self.discovery_container.setVisible(False)
        layout.addWidget(self.discovery_container)

        # Discovery error container
        self.discovery_error_container = QWidget()
        set_widget_id(
            self.discovery_error_container,
            IMPORT_COLLECTION_DISCOVERY_ERROR_CONTAINER,
        )
        discovery_error_layout = QHBoxLayout(self.discovery_error_container)
        discovery_error_layout.setContentsMargins(0, 4, 0, 4)
        self.discovery_error_label = QLabel()
        set_widget_id(
            self.discovery_error_label, IMPORT_COLLECTION_DISCOVERY_ERROR_LABEL
        )
        self.discovery_error_label.setStyleSheet("color: red;")
        self.retry_discovery_btn = QPushButton("Retry")
        set_widget_id(
            self.retry_discovery_btn, IMPORT_COLLECTION_RETRY_DISCOVERY_BUTTON
        )
        self.retry_discovery_btn.clicked.connect(self._on_retry_discovery)
        discovery_error_layout.addWidget(self.discovery_error_label)
        discovery_error_layout.addWidget(self.retry_discovery_btn)
        discovery_error_layout.addStretch()
        self.discovery_error_container.setVisible(False)
        layout.addWidget(self.discovery_error_container)

        # Loading container (Dedicated fetch chrome for remote collection contents)
        self.loading_container = QWidget()
        set_widget_id(self.loading_container, IMPORT_COLLECTION_LOADING_CONTAINER)
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 4, 0, 4)
        self.loading_label = QLabel("Loading collection...")
        set_widget_id(self.loading_label, IMPORT_COLLECTION_LOADING_LABEL)
        self.cancel_loading_btn = QPushButton("Cancel")
        set_widget_id(
            self.cancel_loading_btn, IMPORT_COLLECTION_CANCEL_LOADING_BUTTON
        )
        self.cancel_loading_btn.clicked.connect(self._on_cancel_loading)
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.cancel_loading_btn)
        loading_layout.addStretch()
        self.loading_container.setVisible(False)
        layout.addWidget(self.loading_container)

        # Error container (Dedicated fetch error banner for remote collection contents)
        self.error_container = QWidget()
        set_widget_id(self.error_container, IMPORT_COLLECTION_ERROR_CONTAINER)
        error_layout = QHBoxLayout(self.error_container)
        error_layout.setContentsMargins(0, 4, 0, 4)
        self.error_label = QLabel()
        set_widget_id(self.error_label, IMPORT_COLLECTION_ERROR_LABEL)
        self.error_label.setStyleSheet("color: red;")
        self.retry_fetch_btn = QPushButton("Retry")
        set_widget_id(self.retry_fetch_btn, IMPORT_COLLECTION_RETRY_FETCH_BUTTON)
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

        # Populate workspace collections synchronously; library catalogs async.
        self.collection_combo.blockSignals(True)
        for col in self.workspace_collections:
            self.collection_combo.addItem(f"{col.name} (Workspace)", userData=col)

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

        if self.library_service is not None:
            self._start_manifest_discovery()

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

    def _cancel_discovery_worker(self) -> None:
        if self._active_discovery_worker is not None:
            self._active_discovery_worker.cancel()
            self._active_discovery_worker.wait(1000)
            self._active_discovery_worker = None

    def _start_manifest_discovery(self) -> None:
        self._discovery_generation += 1
        gen = self._discovery_generation
        self._cancel_discovery_worker()

        logger.info(
            "collection_variable_manifest_discovery_started gen=%d",
            gen,
        )
        self.discovery_error_container.setVisible(False)
        self.discovery_container.setVisible(True)
        self.discovery_label.setText("Discovering library collections...")
        self.cancel_discovery_btn.setEnabled(True)

        worker = ManifestDiscoveryWorker(
            library_service=self.library_service,
            generation_id=gen,
            parent=self,
        )
        worker.discovery_completed.connect(self._on_discovery_completed)
        worker.discovery_failed.connect(self._on_discovery_failed)
        self._active_discovery_worker = worker
        worker.start()

    def _on_discovery_completed(self, entries: Any, gen: int) -> None:
        if gen != self._discovery_generation:
            logger.warning(
                "collection_variable_manifest_discovery_stale_discarded gen=%d "
                "current_gen=%d",
                gen,
                self._discovery_generation,
            )
            return

        self._active_discovery_worker = None
        self.discovery_container.setVisible(False)

        entry_list = list(entries or [])
        logger.info(
            "collection_variable_manifest_discovery_completed gen=%d entry_count=%d",
            gen,
            len(entry_list),
        )

        # Preserve the pre-discovery selection. Qt may auto-select index 0 when
        # the first item is inserted into an empty combo; without restoring -1,
        # remote fetch would never start on a later setCurrentIndex(0).
        previous_index = self.collection_combo.currentIndex()
        self.collection_combo.blockSignals(True)
        for label, user_data in entry_list:
            self.collection_combo.addItem(label, userData=user_data)
        self.collection_combo.setCurrentIndex(previous_index)
        self.collection_combo.blockSignals(False)

    def _on_discovery_failed(self, exc: Exception, gen: int) -> None:
        if gen != self._discovery_generation:
            logger.warning(
                "collection_variable_manifest_discovery_error_stale_discarded gen=%d "
                "current_gen=%d error=%s",
                gen,
                self._discovery_generation,
                exc,
            )
            return

        self._active_discovery_worker = None
        self.discovery_container.setVisible(False)

        logger.warning(
            "collection_variable_manifest_discovery_failed gen=%d error=%s",
            gen,
            exc,
            exc_info=True,
        )
        self.discovery_error_container.setVisible(True)
        self.discovery_error_label.setText(
            f"Failed to discover library collections: {exc}"
        )
        self.retry_discovery_btn.setEnabled(True)

    def _on_cancel_discovery(self) -> None:
        logger.info(
            "collection_variable_manifest_discovery_cancelled gen=%d",
            self._discovery_generation,
        )
        self._discovery_generation += 1
        self._cancel_discovery_worker()
        self.discovery_container.setVisible(False)
        self.discovery_error_container.setVisible(False)

    def _on_retry_discovery(self) -> None:
        logger.info(
            "collection_variable_manifest_discovery_retry_requested env_name=%s",
            self.target_environment.name,
        )
        self.discovery_error_container.setVisible(False)
        if self.library_service is not None:
            self._start_manifest_discovery()

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
            self.error_container.setVisible(False)
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
        self._discovery_generation += 1
        self._cancel_discovery_worker()
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
        self._discovery_generation += 1
        self._cancel_discovery_worker()
        if self._active_fetch_worker is not None:
            self._active_fetch_worker.cancel()
            self._active_fetch_worker.wait(1000)
            self._active_fetch_worker = None
        super().closeEvent(event)

    def accept(self) -> None:
        self._discovery_generation += 1
        self._cancel_discovery_worker()
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
