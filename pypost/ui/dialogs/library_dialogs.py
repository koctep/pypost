"""Dialogs for Collection Library management, cloning, and commit/push flows (PYPOST-1223)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pypost.models.git_library import (
    GitAuthConfig,
    GitAuthMode,
    GitBranchInfo,
)
from pypost.models.library_manager import LibrarySourceType
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.ui.presenters.library_presenter import LibraryPresenter
from pypost.ui.widget_ids import (
    LIBRARY_BRANCH_SWITCH_DIALOG,
    LIBRARY_CLONE_DIALOG,
    LIBRARY_COMMIT_PUSH_DIALOG,
    LIBRARY_DIRTY_PULL_WARNING_DIALOG,
    LIBRARY_MANAGER_DIALOG,
    set_widget_id,
)
from pypost.ui.widgets.library_manager_panel import (
    LibraryCollectionsWidget,
    LibraryDetailWidget,
    LibraryListWidget,
)

logger = logging.getLogger(__name__)


class LibraryDirtyPullWarningDialog(QDialog):
    """Guard modal warning about uncommitted local changes before pulling."""

    def __init__(
        self,
        library_id: str,
        dirty_files: List[str],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, LIBRARY_DIRTY_PULL_WARNING_DIALOG)
        self.setWindowTitle("Uncommitted Changes Detected")
        self.resize(480, 320)

        layout = QVBoxLayout(self)

        warning_label = QLabel(
            f"<b>Warning:</b> Local modifications exist in library <code>{library_id}</code>.<br>"
            "Pulling remote updates without committing may overwrite work or cause conflicts."
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        layout.addWidget(QLabel("<b>Modified / Untracked Files:</b>"))
        file_list = QListWidget(self)
        for f in dirty_files:
            file_list.addItem(f)
        layout.addWidget(file_list)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.commit_btn = QPushButton("Commit Changes First...", self)
        self.commit_btn.clicked.connect(self._on_commit_first)
        btn_layout.addWidget(self.commit_btn)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.setDefault(True)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.action_selected: str = "cancel"

    def _on_commit_first(self) -> None:
        self.action_selected = "commit_first"
        self.accept()


class LibraryCommitPushDialog(QDialog):
    """Dialog for authoring a Git commit and pushing to remote tracking branch."""

    def __init__(
        self,
        library_id: str,
        dirty_files: List[str],
        current_branch: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, LIBRARY_COMMIT_PUSH_DIALOG)
        self.setWindowTitle(f"Commit & Push — {library_id}")
        self.resize(520, 420)

        self.library_id = library_id
        self.selected_action: str = "cancel"  # "commit", "commit_and_push", "cancel"

        layout = QVBoxLayout(self)

        info_text = f"<b>Target Branch:</b> {current_branch or 'main'}"
        layout.addWidget(QLabel(info_text))

        layout.addWidget(QLabel("<b>Files to Commit:</b>"))
        self.files_list = QListWidget(self)
        for f in dirty_files:
            item = QListWidgetItem(f, self.files_list)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
        layout.addWidget(self.files_list)

        layout.addWidget(QLabel("<b>Commit Message:</b> (Required)"))
        self.message_edit = QTextEdit(self)
        self.message_edit.setPlaceholderText("Enter a descriptive commit message...")
        self.message_edit.setMaximumHeight(90)
        layout.addWidget(self.message_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.commit_btn = QPushButton("Commit Only", self)
        self.commit_btn.clicked.connect(self._on_commit_only)
        btn_layout.addWidget(self.commit_btn)

        self.commit_push_btn = QPushButton("Commit & Push", self)
        self.commit_push_btn.setDefault(True)
        self.commit_push_btn.setStyleSheet(
            "font-weight: bold; background-color: #007bff; color: white;"
        )
        self.commit_push_btn.clicked.connect(self._on_commit_and_push)
        btn_layout.addWidget(self.commit_push_btn)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def get_commit_message(self) -> str:
        return self.message_edit.toPlainText().strip()

    def get_selected_files(self) -> List[str]:
        selected: List[str] = []
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

    def _on_commit_only(self) -> None:
        if not self.get_commit_message():
            QMessageBox.warning(self, "Validation Error", "Please enter a commit message.")
            return
        self.selected_action = "commit"
        self.accept()

    def _on_commit_and_push(self) -> None:
        if not self.get_commit_message():
            QMessageBox.warning(self, "Validation Error", "Please enter a commit message.")
            return
        self.selected_action = "commit_and_push"
        self.accept()


class LibraryCloneDialog(QDialog):
    """Dialog for cloning a remote Git collection library with hybrid authentication."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        set_widget_id(self, LIBRARY_CLONE_DIALOG)
        self.setWindowTitle("Clone Collection Library")
        self.resize(500, 360)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText(
            "https://github.com/org/repo.git or git@github.com:org/repo.git"
        )
        form.addRow("Repository URL:", self.url_input)

        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("Optional local folder/ID (defaults to repo name)")
        form.addRow("Library ID:", self.id_input)

        self.branch_input = QLineEdit(self)
        self.branch_input.setPlaceholderText("Optional branch name (defaults to remote HEAD)")
        form.addRow("Branch:", self.branch_input)

        self.auth_mode_combo = QComboBox(self)
        self.auth_mode_combo.addItem("SSH Agent (System default)", GitAuthMode.SSH_AGENT)
        self.auth_mode_combo.addItem("Personal Access Token (PAT / HTTPS)", GitAuthMode.PAT)
        self.auth_mode_combo.addItem("Custom SSH Private Key", GitAuthMode.CUSTOM_SSH_KEY)
        self.auth_mode_combo.currentIndexChanged.connect(self._on_auth_mode_changed)
        form.addRow("Authentication:", self.auth_mode_combo)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username (e.g. git / oauth2)")
        form.addRow("Username:", self.username_input)

        self.token_input = QLineEdit(self)
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("Personal Access Token or Password")
        form.addRow("Token / Password:", self.token_input)

        key_layout = QHBoxLayout()
        self.key_path_input = QLineEdit(self)
        self.key_path_input.setPlaceholderText("Path to private key (e.g. ~/.ssh/id_ed25519)")
        key_layout.addWidget(self.key_path_input)

        self.browse_key_btn = QPushButton("Browse...", self)
        self.browse_key_btn.clicked.connect(self._browse_key_file)
        key_layout.addWidget(self.browse_key_btn)
        form.addRow("SSH Private Key:", key_layout)

        self.passphrase_input = QLineEdit(self)
        self.passphrase_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase_input.setPlaceholderText("Optional passphrase for private key")
        form.addRow("Passphrase:", self.passphrase_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.clone_btn = QPushButton("Clone", self)
        self.clone_btn.setDefault(True)
        self.clone_btn.clicked.connect(self._on_clone)
        btn_layout.addWidget(self.clone_btn)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self._on_auth_mode_changed()

    def _on_auth_mode_changed(self) -> None:
        mode = self.auth_mode_combo.currentData()
        is_pat = mode == GitAuthMode.PAT
        is_key = mode == GitAuthMode.CUSTOM_SSH_KEY

        self.username_input.setEnabled(is_pat)
        self.token_input.setEnabled(is_pat)
        self.key_path_input.setEnabled(is_key)
        self.browse_key_btn.setEnabled(is_key)
        self.passphrase_input.setEnabled(is_key)

    def _browse_key_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSH Private Key",
            str(Path.home() / ".ssh"),
            "SSH Keys (*);;All Files (*)",
        )
        if file_path:
            self.key_path_input.setText(file_path)

    def _on_clone(self) -> None:
        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Repository URL is required.")
            return
        self.accept()

    def get_clone_params(self) -> tuple[str, Optional[str], Optional[str], GitAuthConfig]:
        url = self.url_input.text().strip()
        lib_id = self.id_input.text().strip() or None
        branch = self.branch_input.text().strip() or None
        mode = self.auth_mode_combo.currentData()

        auth = GitAuthConfig(
            mode=mode,
            username=self.username_input.text().strip() or None,
            token=self.token_input.text().strip() or None,
            key_path=self.key_path_input.text().strip() or None,
            passphrase=self.passphrase_input.text().strip() or None,
        )
        return url, lib_id, branch, auth


class LibraryBranchSwitchDialog(QDialog):
    """Dialog for switching active branch of a library."""

    def __init__(
        self,
        library_id: str,
        branches: List[GitBranchInfo],
        current_branch: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, LIBRARY_BRANCH_SWITCH_DIALOG)
        self.setWindowTitle(f"Switch Branch — {library_id}")
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Select Target Branch:</b>"))
        self.branch_combo = QComboBox(self)

        selected_idx = 0
        for i, b in enumerate(branches):
            remote_tag = "(remote)" if b.is_remote else ""
            current_tag = "(current)" if b.is_current else ""
            parts = [b.short_name, remote_tag, current_tag]
            display_text = " ".join(p for p in parts if p)
            self.branch_combo.addItem(display_text, b.short_name)
            if b.is_current or b.short_name == current_branch:
                selected_idx = i

        self.branch_combo.setCurrentIndex(selected_idx)
        layout.addWidget(self.branch_combo)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.switch_btn = QPushButton("Switch", self)
        self.switch_btn.setDefault(True)
        self.switch_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.switch_btn)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def get_selected_branch(self) -> str:
        return self.branch_combo.currentData() or self.branch_combo.currentText()


class LibraryManagerDialog(QDialog):
    """Main management dialog for collection libraries."""

    def __init__(
        self,
        presenter: Optional[LibraryPresenter] = None,
        parent: Optional[QWidget] = None,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, LIBRARY_MANAGER_DIALOG)
        self.setWindowTitle("Collection Libraries Manager")
        self.resize(800, 520)

        self.presenter = presenter or LibraryPresenter(metrics=metrics)

        main_layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        # Left panel: Library list
        self.list_panel = LibraryListWidget(splitter)
        splitter.addWidget(self.list_panel)

        # Right panel: Details + Collections
        right_container = QWidget(splitter)
        right_layout = QVBoxLayout(right_container)

        self.detail_panel = LibraryDetailWidget(right_container)
        right_layout.addWidget(self.detail_panel)

        self.collections_panel = LibraryCollectionsWidget(right_container)
        right_layout.addWidget(self.collections_panel)

        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Connect Presenter Signals
        self.presenter.libraries_loaded.connect(self._on_libraries_loaded)
        self.presenter.entries_loaded.connect(self._on_entries_loaded)
        self.presenter.entry_updated.connect(self._on_entry_updated)
        self.presenter.status_updated.connect(self._on_status_updated)
        self.presenter.operation_state_changed.connect(self._on_operation_state_changed)
        self.presenter.operation_completed_for_library.connect(
            self._on_operation_completed
        )
        self.presenter.operation_failed_for_library.connect(self._on_operation_failed)
        self.presenter.operation_blocked.connect(self._on_operation_blocked)
        self.presenter.branches_loaded.connect(self._on_branches_loaded)
        self.presenter.dirty_files_loaded.connect(self._on_dirty_files_loaded)
        self.presenter.manifest_loaded.connect(lambda m: self.collections_panel.update_manifest(m))

        # Connect Widget Signals
        self.list_panel.library_selected.connect(self._on_library_selected)
        self.list_panel.selection_cleared.connect(self._on_selection_cleared)
        self.list_panel.clone_clicked.connect(self._on_clone_clicked)
        self.list_panel.connect_clicked.connect(self._on_connect_clicked)

        self.detail_panel.pull_clicked.connect(self._on_pull_clicked)
        self.detail_panel.commit_push_clicked.connect(self._on_commit_push_clicked)
        self.detail_panel.switch_branch_clicked.connect(self._on_switch_branch_clicked)
        self.detail_panel.delete_clicked.connect(self._on_delete_clicked)
        self.detail_panel.refresh_clicked.connect(self._on_refresh_clicked)
        self.detail_panel.copy_path_clicked.connect(self._on_copy_path_clicked)
        self.detail_panel.disconnect_clicked.connect(self._on_disconnect_clicked)

        # Initial Load
        self.presenter.load_libraries()

    def _on_libraries_loaded(self, _libraries: List[str]) -> None:
        """Keep the compatibility signal from replacing projected rows with IDs."""
        self._on_entries_loaded(self.presenter.list_entries())

    def _on_entries_loaded(self, entries: List[Any]) -> None:
        """Render the presenter's complete row projections."""
        self.list_panel.set_entries(entries)

    def _on_entry_updated(self, library_id: str, status: object) -> None:
        """Update one row and its detail view without disturbing other entries."""
        self.list_panel.update_entry(library_id, status)
        if library_id == self.presenter.selected_library_id:
            self.detail_panel.update_status(status)  # type: ignore[arg-type]
            record = self.presenter.get_connection_record(library_id)
            self.detail_panel.set_source_type(record.source_type if record else None)

    def _on_status_updated(self, status: object) -> None:
        """Apply legacy status signals only to the library they describe."""
        is_selected = getattr(status, "library_id", None) == self.presenter.selected_library_id
        if status is None or is_selected:
            self.detail_panel.update_status(status)  # type: ignore[arg-type]

    def _on_operation_state_changed(
        self, library_id: str, operation: str, active: bool
    ) -> None:
        """Show operation progress in both the affected row and selected details."""
        self.list_panel.set_operation_state(library_id, operation, active)
        if library_id == self.presenter.selected_library_id:
            self.detail_panel.set_operation_state(operation, active)

    def _on_selection_cleared(self) -> None:
        """Clear presenter and detail state when filtering removes the selection."""
        self.presenter.select_library(None, refresh=False)
        self.detail_panel.clear_details()
        self.collections_panel.update_manifest(None)

    def _on_library_selected(self, library_id: str) -> None:
        self.detail_panel.clear_details()
        self.presenter.select_library(library_id, refresh=False)
        manifest = self.presenter.cached_manifest
        self.detail_panel.update_manifest(manifest, library_id=library_id)
        record = self.presenter.get_connection_record(library_id)
        self.detail_panel.set_source_type(record.source_type if record else None)
        self.detail_panel.update_status(self.presenter.cached_status)  # type: ignore[arg-type]

    def _on_branches_loaded(self, library_id: str, branches: List[GitBranchInfo]) -> None:
        """Open branch selection only for the library that requested the listing."""
        if library_id != self.presenter.selected_library_id:
            return
        status = self.presenter.cached_status
        current_branch = status.current_branch if status else None
        dialog = LibraryBranchSwitchDialog(
            library_id, branches, current_branch=current_branch, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.presenter.switch_branch_async(library_id, dialog.get_selected_branch())

    def _on_operation_blocked(
        self, library_id: str, operation: str, guard: object
    ) -> None:
        """Show the dirty-worktree safeguard after the worker checks local files."""
        if operation not in {"pull", "switch_branch"}:
            return
        dirty_files = [str(item) for item in getattr(guard, "files", []) or []]
        warning_dialog = LibraryDirtyPullWarningDialog(library_id, dirty_files, self)
        if (
            warning_dialog.exec() == QDialog.DialogCode.Accepted
            and warning_dialog.action_selected == "commit_first"
        ):
            self._open_commit_push_dialog(library_id, dirty_files)

    def _on_operation_completed(
        self, library_id: str, operation: str, result: object
    ) -> None:
        """Announce only successful asynchronous lifecycle operations."""
        if result is False or getattr(result, "success", True) is False:
            return
        if operation == "pull":
            QMessageBox.information(
                self, "Pull Complete", f"Library '{library_id}' is up to date."
            )
        elif operation == "switch_branch":
            branch = getattr(result, "current_branch", None) or "the selected branch"
            QMessageBox.information(self, "Branch Switched", f"Switched to {branch}.")
        elif operation == "connect":
            QMessageBox.information(
                self, "Connected", "The local library was connected in place."
            )
        elif operation == "disconnect":
            QMessageBox.information(
                self, "Disconnected", f"Library '{library_id}' was disconnected."
            )
        elif operation == "delete":
            QMessageBox.information(self, "Removed", f"Library '{library_id}' was removed.")
        elif operation == "clone":
            QMessageBox.information(self, "Success", "Library cloned successfully.")
        elif operation == "commit":
            QMessageBox.information(self, "Success", "Changes committed locally.")
        elif operation == "push":
            QMessageBox.information(self, "Success", "Changes pushed to remote.")
        elif operation == "commit_and_push":
            QMessageBox.information(
                self, "Success", "Changes committed and pushed to remote."
            )

    def _on_operation_failed(self, _library_id: str, _operation: str, error: object) -> None:
        """Show safe diagnostics for asynchronous failures; raw errors stay in the presenter."""
        exception = error if isinstance(error, Exception) else RuntimeError("operation failed")
        title, description = self.presenter.get_diagnostic_message(exception)
        QMessageBox.critical(self, title, description)

    def _on_clone_clicked(self) -> None:
        dialog = LibraryCloneDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url, lib_id, branch, auth = dialog.get_clone_params()
            try:
                self.presenter.clone_library_async(
                    url=url, library_id=lib_id, branch=branch, auth=auth
                )
            except Exception as ex:
                title, desc = self.presenter.get_diagnostic_message(ex)
                QMessageBox.critical(self, title, desc)

    def _on_connect_clicked(self) -> None:
        """Register a selected directory in place after the user confirms a choice."""
        path = QFileDialog.getExistingDirectory(self, "Connect Collection Library")
        if not path:
            return
        try:
            if not self.presenter.connect_local_library_async(Path(path)):
                return
        except Exception as ex:
            title, desc = self.presenter.get_diagnostic_message(ex)
            QMessageBox.critical(self, title, desc)

    def _on_refresh_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if lib_id:
            self.presenter.refresh_status_async(lib_id)

    def _path_for_library(self, library_id: str) -> str:
        """Return an exact path without reaching into the presenter's service union."""
        path = self.presenter.get_local_path(library_id)
        return str(path) if path else "Unavailable"

    def _on_copy_path_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return
        path = self._path_for_library(lib_id)
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(path)
        QMessageBox.information(self, "Path Copied", f"Copied local path:\n{path}")

    def _on_disconnect_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return
        record = self.presenter.get_connection_record(lib_id)
        if record is None:
            QMessageBox.information(
                self, "Library Unavailable", "The selected library is no longer connected."
            )
            return
        name = record.display_name if record else lib_id
        source = record.source_type.value if record else LibrarySourceType.CLONED.value
        path = self._path_for_library(lib_id)
        reply = QMessageBox.question(
            self,
            "Disconnect Library",
            f"Disconnect '{name}' ({source}) at {path}?\nAll local files will be retained.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.presenter.disconnect_library_async(lib_id)

    def _on_pull_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return

        self.presenter.pull_library_async(lib_id)

    def _on_commit_push_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return
        self.presenter.check_dirty_async(lib_id)

    def _on_dirty_files_loaded(self, library_id: str, dirty_files: List[str]) -> None:
        """Open commit controls only after the worker has read the selected tree."""
        if library_id == self.presenter.selected_library_id:
            self._open_commit_push_dialog(library_id, dirty_files)

    def _open_commit_push_dialog(self, lib_id: str, dirty_files: List[str]) -> None:
        status = self.presenter.cached_status
        current_branch = status.current_branch if status else None
        dialog = LibraryCommitPushDialog(
            lib_id, dirty_files, current_branch=current_branch, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            msg = dialog.get_commit_message()
            files = dialog.get_selected_files()
            try:
                if dialog.selected_action == "commit_and_push":
                    self.presenter.commit_and_push_async(
                        lib_id, message=msg, files=files, branch=current_branch
                    )
                elif dialog.selected_action == "commit":
                    self.presenter.commit_library_async(lib_id, message=msg, files=files)
            except Exception as ex:
                title, desc = self.presenter.get_diagnostic_message(ex)
                QMessageBox.critical(self, title, desc)

    def _on_switch_branch_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return

        self.presenter.list_branches_async(lib_id, remote=True)

    def _on_delete_clicked(self) -> None:
        lib_id = self.presenter.selected_library_id
        if not lib_id:
            return

        record = self.presenter.get_connection_record(lib_id)
        if record is None:
            QMessageBox.information(
                self, "Delete Unavailable", "The selected library is no longer connected."
            )
            return
        if record.source_type == LibrarySourceType.REGISTERED:
            QMessageBox.information(
                self, "Delete Unavailable", "Registered local directories can only be disconnected."
            )
            return
        name = record.display_name or lib_id
        source = record.source_type.value
        path = self._path_for_library(lib_id)
        reply = QMessageBox.question(
            self,
            "Delete Local Clone",
            f"Permanently delete '{name}' ({source}) at {path}?\n"
            "The local clone, overlay, and local changes will be removed; the remote is unchanged.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.presenter.delete_library_async(lib_id, confirmed=True)
