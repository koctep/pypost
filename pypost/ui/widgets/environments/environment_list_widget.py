import logging
from collections.abc import Callable
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.environment_messages import (
    ACTION_COPY,
    ACTION_DELETE,
    ACTION_RENAME,
    BUTTON_ADD,
    DIALOG_TITLE_COPY_ENVIRONMENT,
    DIALOG_TITLE_NEW_ENVIRONMENT,
    INPUT_LABEL_NAME,
    format_copy_of_name,
)
from pypost.core.environment_ops import clone_environment, validate_environment_rename
from pypost.models.models import Environment
from pypost.ui.collection_item_dialogs import (
    confirm_delete_environment,
    show_copy_environment_duplicate_name_error,
    show_copy_environment_empty_name_error,
)
from pypost.ui.delegates import EnvironmentNameDelegate

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
    ) -> None:
        super().__init__(parent)
        self.environments = environments
        self._initial_current_env_name = current_env_name
        self._get_current_env_name = get_current_env_name or (lambda: current_env_name)
        self._set_current_env_name = set_current_env_name or (
            lambda name: setattr(self, "_initial_current_env_name", name)
        )

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

        layout.addWidget(self.env_list)
        layout.addWidget(add_btn)

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
