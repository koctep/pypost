from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.environment_export import (
    EnvironmentExportError,
    ExportPlanResult,
    environments_for_export,
    export_includes_hidden,
    format_export_result,
    suggested_export_filename,
    write_export_file,
)
from pypost.core.environment_import import (
    EnvironmentImportFileError,
    ImportConflictDecision,
    find_conflicts,
    format_import_result,
    plan_import,
)
from pypost.core.environment_messages import (
    ACTION_COPY,
    ACTION_DELETE,
    ACTION_RENAME,
    BUTTON_ADD,
    BUTTON_EXPORT,
    BUTTON_IMPORT,
    DIALOG_TITLE_COPY_ENVIRONMENT,
    DIALOG_TITLE_NEW_ENVIRONMENT,
    INPUT_LABEL_NAME,
    MSG_IMPORT_NO_VALID_ENVIRONMENTS,
    format_copy_of_name,
)
from pypost.core.environment_ops import clone_environment, validate_environment_rename
from pypost.models.models import Environment
from pypost.ui.collection_item_dialogs import (
    confirm_delete_environment,
    confirm_export_includes_secrets,
    prompt_export_environments_file,
    prompt_export_scope,
    prompt_import_conflict,
    prompt_import_environments_file,
    show_copy_environment_duplicate_name_error,
    show_copy_environment_empty_name_error,
    show_export_error,
    show_export_no_selection_error,
    show_export_result,
    show_import_invalid_file_error,
    show_import_result,
)
from pypost.ui.delegates import EnvironmentNameDelegate
from pypost.ui.widget_ids import ENV_EXPORT_BUTTON, ENV_IMPORT_BUTTON, set_widget_id

logger = logging.getLogger(__name__)


class EnvironmentListWidget(QWidget):
    """Left-pane QListWidget for managing environment names."""

    environment_selected = Signal(int)

    def __init__(
        self,
        environments: List[Environment],
        parent: QWidget | None = None,
        *,
        current_env_name: str | None = None,
        get_current_env_name: Callable[[], str | None] | None = None,
        set_current_env_name: Callable[[str | None], None] | None = None,
        read_import_file: Callable[[Path], tuple[list[Environment], list[str]]] | None = None,
        serialize_export_records: Callable[[list[Environment]], list[dict]] | None = None,
    ) -> None:
        super().__init__(parent)
        self.environments = environments
        self._initial_current_env_name = current_env_name
        self._get_current_env_name = get_current_env_name or (lambda: current_env_name)
        self._set_current_env_name = set_current_env_name or (
            lambda name: setattr(self, "_initial_current_env_name", name)
        )
        self._read_import_file = read_import_file
        self._serialize_export_records = serialize_export_records

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.env_list = QListWidget()
        self.env_list.currentRowChanged.connect(self.environment_selected.emit)
        self.env_list.setItemDelegate(
            EnvironmentNameDelegate(
                get_existing_names=lambda: [e.name for e in self.environments],
                on_rename_accepted=self._on_environment_renamed,
                parent=self.env_list,
            )
        )
        self.env_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.env_list.customContextMenuRequested.connect(self._on_env_list_context_menu)

        rename_shortcut = QShortcut(QKeySequence("F2"), self.env_list)
        rename_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        rename_shortcut.activated.connect(self._rename_current_environment)

        add_btn = QPushButton(BUTTON_ADD)
        add_btn.clicked.connect(self.add_environment)

        import_btn = QPushButton(BUTTON_IMPORT)
        set_widget_id(import_btn, ENV_IMPORT_BUTTON)
        import_btn.clicked.connect(self.import_environments)

        export_btn = QPushButton(BUTTON_EXPORT)
        set_widget_id(export_btn, ENV_EXPORT_BUTTON)
        export_btn.clicked.connect(self.export_environments)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(add_btn)
        buttons_row.addWidget(import_btn)
        buttons_row.addWidget(export_btn)

        layout.addWidget(self.env_list)
        layout.addLayout(buttons_row)

        self.load_list()

    def load_list(self) -> None:
        self.env_list.blockSignals(True)
        self.env_list.clear()
        target_row = 0
        current_name = self._get_current_env_name()
        for i, env in enumerate(self.environments):
            item = QListWidgetItem(env.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.env_list.addItem(item)
            if current_name and env.name == current_name:
                target_row = i

        if self.environments:
            self.env_list.setCurrentRow(target_row)
        self.env_list.blockSignals(False)

    def add_environment(self) -> None:
        name, ok = QInputDialog.getText(
            self,
            DIALOG_TITLE_NEW_ENVIRONMENT,
            INPUT_LABEL_NAME,
        )
        if ok and name:
            env = Environment(name=name)
            self.environments.append(env)
            self.env_list.blockSignals(True)
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.env_list.addItem(item)
            self.env_list.setCurrentRow(len(self.environments) - 1)
            self.env_list.blockSignals(False)

    def delete_environment(self, row: int | None = None) -> None:
        if row is None:
            row = self.env_list.currentRow()
        if row < 0:
            return

        deleted_env = self.environments[row]
        if not confirm_delete_environment(self, deleted_env.name):
            return

        logger.info("environment_deleted env_name=%s", deleted_env.name)
        del self.environments[row]
        self.env_list.takeItem(row)

    def _on_env_list_context_menu(self, pos) -> None:
        item = self.env_list.itemAt(pos)
        if item is None:
            return
        row = self.env_list.row(item)
        menu = QMenu(self)
        rename_action = menu.addAction(ACTION_RENAME)
        copy_action = menu.addAction(ACTION_COPY)
        delete_action = menu.addAction(ACTION_DELETE)
        chosen = menu.exec(self.env_list.mapToGlobal(pos))
        if chosen == rename_action:
            self._rename_environment_at_row(row)
        elif chosen == copy_action:
            self._duplicate_environment_at_row(row)
        elif chosen == delete_action:
            self.delete_environment(row)

    def _rename_current_environment(self) -> None:
        row = self.env_list.currentRow()
        if row >= 0:
            self._rename_environment_at_row(row)

    def _rename_environment_at_row(self, row: int) -> None:
        item = self.env_list.item(row)
        if item:
            self.env_list.editItem(item)

    def apply_environment_rename(self, row: int, new_name: str) -> bool:
        """Commit an environment rename programmatically (used by tests and delegate)."""
        if row < 0 or row >= len(self.environments):
            return False

        env = self.environments[row]
        old_name = env.name
        accepted, normalized, _error = validate_environment_rename(
            new_name,
            old_name,
            [e.name for e in self.environments],
            row,
        )
        if not accepted:
            return False
        if normalized == old_name:
            return True

        env.name = normalized
        if self._get_current_env_name() == old_name:
            self._set_current_env_name(normalized)

        item = self.env_list.item(row)
        if item:
            self.env_list.blockSignals(True)
            item.setText(normalized)
            self.env_list.blockSignals(False)

        logger.info(
            "environment_renamed old_name=%s new_name=%s",
            old_name,
            normalized,
        )
        return True

    def _on_environment_renamed(self, row: int, old_name: str, new_name: str) -> None:
        if row < 0 or row >= len(self.environments):
            return

        env = self.environments[row]
        env.name = new_name
        if self._get_current_env_name() == old_name:
            self._set_current_env_name(new_name)

        logger.info(
            "environment_renamed old_name=%s new_name=%s",
            old_name,
            new_name,
        )

    def _duplicate_environment_at_row(self, row: int) -> None:
        if row < 0 or row >= len(self.environments):
            return
        source = self.environments[row]
        default_name = format_copy_of_name(source.name)
        while True:
            name, ok = QInputDialog.getText(
                self,
                DIALOG_TITLE_COPY_ENVIRONMENT,
                INPUT_LABEL_NAME,
                text=default_name,
            )
            if not ok:
                return
            stripped = name.strip()
            if not stripped:
                show_copy_environment_empty_name_error(self)
                default_name = name
                continue
            if any(e.name == stripped for e in self.environments):
                show_copy_environment_duplicate_name_error(self, stripped)
                default_name = stripped
                continue
            break
        new_env = clone_environment(source, stripped)
        logger.info(
            "environment_copied source_name=%s new_name=%s",
            source.name,
            stripped,
        )
        insert_at = row + 1
        self.environments.insert(insert_at, new_env)
        self.load_list()
        self.env_list.setCurrentRow(insert_at)

    def import_environments(self) -> None:
        """Pick a file, resolve name conflicts, and merge into the working list."""
        if self._read_import_file is None:
            return

        path = prompt_import_environments_file(self)
        if path is None:
            return

        try:
            candidates, parse_errors = self._read_import_file(path)
        except EnvironmentImportFileError as exc:
            logger.warning("environment_import_file_invalid reason=%s", exc)
            show_import_invalid_file_error(self, str(exc))
            return

        if not candidates:
            logger.warning("environment_import_file_invalid reason=no_valid_environments")
            message = MSG_IMPORT_NO_VALID_ENVIRONMENTS
            if parse_errors:
                message = "\n".join([message, ""] + parse_errors)
            show_import_invalid_file_error(self, message)
            return

        decisions = self._resolve_import_conflicts(candidates)
        result = plan_import(self.environments, candidates, decisions)
        result.parse_errors.extend(parse_errors)

        self.environments[:] = result.environments
        self.load_list()

        logger.info(
            "environment_import_completed added_count=%d updated_count=%d "
            "skipped_count=%d renamed_count=%d error_count=%d",
            len(result.added),
            len(result.updated),
            len(result.skipped),
            len(result.renamed),
            len(result.parse_errors),
        )
        summary_text = format_import_result(result)
        success = bool(result.added or result.updated or result.renamed)
        show_import_result(self, summary_text, success=success)

    def _resolve_import_conflicts(
        self, candidates: list[Environment]
    ) -> dict[str, ImportConflictDecision]:
        conflicts = find_conflicts(self.environments, candidates)
        decisions: dict[str, ImportConflictDecision] = {}
        apply_to_all: ImportConflictDecision | None = None
        for i, name in enumerate(conflicts):
            if apply_to_all is not None:
                decisions[name] = apply_to_all
                continue
            remaining_count = len(conflicts) - i - 1
            decision, use_for_all = prompt_import_conflict(
                self, name, remaining_count=remaining_count
            )
            decisions[name] = decision
            if use_for_all:
                apply_to_all = decision
        return decisions

    def export_environments(self) -> None:
        """Choose scope, confirm secrets if needed, and write environments to a file."""
        if self._serialize_export_records is None:
            return

        scope = prompt_export_scope(self)
        if scope is None:
            return

        selected_row = self.env_list.currentRow()
        targets = environments_for_export(
            self.environments,
            scope=scope,
            selected_index=selected_row,
        )
        if not targets:
            logger.warning("environment_export_no_selection scope=%s", scope.value)
            show_export_no_selection_error(self)
            return

        includes_hidden = export_includes_hidden(targets)
        if includes_hidden and not confirm_export_includes_secrets(
            self, [env.name for env in targets if env.hidden_keys]
        ):
            return

        suggested_name = suggested_export_filename(targets)
        path = prompt_export_environments_file(self, suggested_name=suggested_name)
        if path is None:
            return

        try:
            records = self._serialize_export_records(targets)
            payload = records[0] if len(records) == 1 else records
            write_export_file(path, payload)
        except EnvironmentExportError as exc:
            logger.warning("environment_export_failed reason=%s", exc)
            show_export_error(self, str(exc))
            return

        result = ExportPlanResult(
            exported_count=len(targets),
            environment_names=[env.name for env in targets],
            includes_hidden=includes_hidden,
            path=path,
        )
        logger.info(
            "environment_export_completed count=%d includes_hidden=%s path=%s",
            result.exported_count,
            result.includes_hidden,
            result.path,
        )
        show_export_result(self, format_export_result(result), success=True)
