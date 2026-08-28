"""Sub-widgets for Library Manager Dialog (PYPOST-1223).

Includes:
- LibraryListWidget: Lists cloned libraries and provides clone trigger.
- LibraryDetailWidget: Displays selected library status, branch, clean/dirty badges,
  sync status, and action buttons.
- LibraryCollectionsWidget: Displays collections contained in the library manifest.
"""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.models.git_library import GitRepoStatus
from pypost.models.library_manifest import LibraryManifest
from pypost.ui.widget_ids import (
    LIBRARY_BRANCH_BADGE,
    LIBRARY_CLONE_BUTTON,
    LIBRARY_COLLECTIONS_LIST,
    LIBRARY_COMMIT_PUSH_BUTTON,
    LIBRARY_DELETE_BUTTON,
    LIBRARY_DIRTY_BADGE,
    LIBRARY_LIST,
    LIBRARY_PULL_BUTTON,
    LIBRARY_SWITCH_BRANCH_BUTTON,
    LIBRARY_SYNC_BADGE,
    set_widget_id,
)


class LibraryListWidget(QWidget):
    """List of connected Git collection libraries with clone action."""

    library_selected = Signal(str)
    clone_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("<b>Connected Libraries</b>")
        layout.addWidget(header)

        self.list_widget = QListWidget(self)
        set_widget_id(self.list_widget, LIBRARY_LIST)
        self.list_widget.currentTextChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget)

        self.clone_button = QPushButton("Clone New Library...", self)
        set_widget_id(self.clone_button, LIBRARY_CLONE_BUTTON)
        self.clone_button.clicked.connect(self.clone_clicked.emit)
        layout.addWidget(self.clone_button)

    def set_libraries(self, libraries: List[str], current: Optional[str] = None) -> None:
        """Populate library list and restore current selection."""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        selected_row = -1
        for i, lib in enumerate(libraries):
            self.list_widget.addItem(lib)
            if lib == current:
                selected_row = i
        self.list_widget.blockSignals(False)

        if selected_row >= 0:
            self.list_widget.setCurrentRow(selected_row)
        elif self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def select_library(self, library_id: str) -> None:
        """Select item matching library_id."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == library_id:
                self.list_widget.setCurrentRow(i)
                break

    def _on_item_changed(self, text: str) -> None:
        if text:
            self.library_selected.emit(text)


class LibraryDetailWidget(QWidget):
    """Header and controls for the selected library."""

    pull_clicked = Signal()
    commit_push_clicked = Signal()
    switch_branch_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Overview Header
        self.title_label = QLabel("<h2>No Library Selected</h2>", self)
        layout.addWidget(self.title_label)

        self.desc_label = QLabel("", self)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        self.path_label = QLabel("", self)
        self.path_label.setStyleSheet("color: gray;")
        layout.addWidget(self.path_label)

        # Status Badges Bar
        badge_group = QGroupBox("Git Status", self)
        badge_layout = QHBoxLayout(badge_group)

        self.branch_badge = QLabel("Branch: -", self)
        set_widget_id(self.branch_badge, LIBRARY_BRANCH_BADGE)
        self.branch_badge.setStyleSheet(
            "font-weight: bold; padding: 4px 8px; background: #e0e0e0; border-radius: 4px;"
        )
        badge_layout.addWidget(self.branch_badge)

        self.dirty_badge = QLabel("Clean", self)
        set_widget_id(self.dirty_badge, LIBRARY_DIRTY_BADGE)
        self.dirty_badge.setStyleSheet(
            "font-weight: bold; padding: 4px 8px; background: #d4edda; color: #155724; "
            "border-radius: 4px;"
        )
        badge_layout.addWidget(self.dirty_badge)

        self.sync_badge = QLabel("Up to date", self)
        set_widget_id(self.sync_badge, LIBRARY_SYNC_BADGE)
        self.sync_badge.setStyleSheet(
            "font-weight: bold; padding: 4px 8px; background: #e0e0e0; border-radius: 4px;"
        )
        badge_layout.addWidget(self.sync_badge)

        badge_layout.addStretch()
        layout.addWidget(badge_group)

        # Actions Toolbar
        actions_layout = QHBoxLayout()
        self.pull_button = QPushButton("Sync / Pull", self)
        set_widget_id(self.pull_button, LIBRARY_PULL_BUTTON)
        self.pull_button.clicked.connect(self.pull_clicked.emit)
        actions_layout.addWidget(self.pull_button)

        self.commit_push_button = QPushButton("Commit & Push...", self)
        set_widget_id(self.commit_push_button, LIBRARY_COMMIT_PUSH_BUTTON)
        self.commit_push_button.clicked.connect(self.commit_push_clicked.emit)
        actions_layout.addWidget(self.commit_push_button)

        self.switch_branch_button = QPushButton("Switch Branch...", self)
        set_widget_id(self.switch_branch_button, LIBRARY_SWITCH_BRANCH_BUTTON)
        self.switch_branch_button.clicked.connect(self.switch_branch_clicked.emit)
        actions_layout.addWidget(self.switch_branch_button)

        actions_layout.addStretch()

        self.delete_button = QPushButton("Remove Library", self)
        set_widget_id(self.delete_button, LIBRARY_DELETE_BUTTON)
        self.delete_button.setStyleSheet("color: #721c24; background-color: #f8d7da;")
        self.delete_button.clicked.connect(self.delete_clicked.emit)
        actions_layout.addWidget(self.delete_button)

        layout.addLayout(actions_layout)

        self.setEnabled(False)

    def update_manifest(
        self,
        manifest: Optional[LibraryManifest],
        library_id: Optional[str] = None,
    ) -> None:
        """Update display title, description, and metadata from manifest."""
        if not manifest and not library_id:
            self.title_label.setText("<h2>No Library Selected</h2>")
            self.desc_label.setText("")
            self.path_label.setText("")
            self.setEnabled(False)
            return

        self.setEnabled(True)
        title = manifest.name if manifest else library_id
        version = f" (v{manifest.version})" if manifest and manifest.version else ""
        self.title_label.setText(f"<h2>{title}{version}</h2>")
        desc = manifest.description if manifest and manifest.description else "No description."
        self.desc_label.setText(desc)

    def update_status(self, status: Optional[GitRepoStatus]) -> None:
        """Update status badges based on GitRepoStatus."""
        if not status:
            self.branch_badge.setText("Branch: -")
            self.dirty_badge.setText("Status: -")
            self.sync_badge.setText("Sync: -")
            return

        # Branch badge
        branch = status.current_branch or "detached"
        self.branch_badge.setText(f"Branch: {branch}")
        self.path_label.setText(f"Path: {status.repo_path}")

        # Dirty badge
        if status.is_clean:
            self.dirty_badge.setText("Clean")
            self.dirty_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #d4edda; color: #155724; "
                "border-radius: 4px;"
            )
        else:
            dirty_count = len(status.dirty_files)
            self.dirty_badge.setText(f"Dirty ({dirty_count} uncommitted)")
            self.dirty_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #fff3cd; color: #856404; "
                "border-radius: 4px;"
            )

        # Sync badge (ahead/behind)
        if status.ahead_count > 0 and status.behind_count > 0:
            self.sync_badge.setText(f"↑{status.ahead_count} ↓{status.behind_count}")
            self.sync_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #fff3cd; color: #856404; "
                "border-radius: 4px;"
            )
        elif status.ahead_count > 0:
            self.sync_badge.setText(f"Ahead by {status.ahead_count} (↑{status.ahead_count})")
            self.sync_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #cce5ff; color: #004085; "
                "border-radius: 4px;"
            )
        elif status.behind_count > 0:
            self.sync_badge.setText(f"Behind by {status.behind_count} (↓{status.behind_count})")
            self.sync_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #fff3cd; color: #856404; "
                "border-radius: 4px;"
            )
        else:
            self.sync_badge.setText("Up to date")
            self.sync_badge.setStyleSheet(
                "font-weight: bold; padding: 4px 8px; background: #d4edda; color: #155724; "
                "border-radius: 4px;"
            )


class LibraryCollectionsWidget(QWidget):
    """Lists collections contained inside the library manifest."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("<b>Bundled Collections</b>", self)
        layout.addWidget(header)

        self.collections_list = QListWidget(self)
        set_widget_id(self.collections_list, LIBRARY_COLLECTIONS_LIST)
        layout.addWidget(self.collections_list)

    def update_manifest(self, manifest: Optional[LibraryManifest]) -> None:
        """Display collection items from manifest."""
        self.collections_list.clear()
        if not manifest or not manifest.collections:
            item = QListWidgetItem("No collections declared in manifest", self.collections_list)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            return

        for coll_decl in manifest.collections:
            if isinstance(coll_decl, str):
                item_text = coll_decl
            else:
                path_str = str(getattr(coll_decl, "path", coll_decl))
                name_str = getattr(coll_decl, "name", None) or path_str
                desc = getattr(coll_decl, "description", "")
                desc_str = f" - {desc}" if desc else ""
                item_text = f"{name_str} ({path_str}){desc_str}"
            QListWidgetItem(item_text, self.collections_list)
