"""Sub-widgets for Library Manager Dialog (PYPOST-1223).

Includes:
- LibraryListWidget: Lists cloned libraries and provides clone trigger.
- LibraryDetailWidget: Displays selected library status, branch, clean/dirty badges,
  sync status, and action buttons.
- LibraryCollectionsWidget: Displays collections contained in the library manifest.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, List, Optional, cast

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.library_status import LibraryStatusResolver
from pypost.models.git_library import GitRepoStatus
from pypost.models.library_manager import (
    LibraryListEntry,
    LibraryRow,
    LibraryStatusSnapshot,
)
from pypost.models.library_manifest import LibraryManifest
from pypost.ui.widget_ids import (
    LIBRARY_BRANCH_BADGE,
    LIBRARY_CLONE_BUTTON,
    LIBRARY_CONNECT_BUTTON,
    LIBRARY_COLLECTIONS_LIST,
    LIBRARY_CLEAR_FILTER_BUTTON,
    LIBRARY_CLEAR_SEARCH_BUTTON,
    LIBRARY_COMMIT_PUSH_BUTTON,
    LIBRARY_DELETE_BUTTON,
    LIBRARY_DISCONNECT_BUTTON,
    LIBRARY_COPY_PATH_BUTTON,
    LIBRARY_DIRTY_BADGE,
    LIBRARY_LIST,
    LIBRARY_PULL_BUTTON,
    LIBRARY_REFRESH_BUTTON,
    LIBRARY_SEARCH_INPUT,
    LIBRARY_SORT_COMBO,
    LIBRARY_STATUS_FILTER,
    LIBRARY_SWITCH_BRANCH_BUTTON,
    LIBRARY_SYNC_BADGE,
    set_widget_id,
)


class LibraryEntryListModel(QAbstractListModel):
    """Typed source model for projected library rows."""

    ROW_ROLE = int(Qt.ItemDataRole.UserRole) + 1

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: list[LibraryRow] = []
        self._sort_field: Optional[str] = None
        self._sort_descending = False

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        """Return the number of projected rows."""
        return 0 if parent.isValid() else len(self._rows)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        """Expose stable identity, typed row data, and accessible text."""
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        role_value = int(role)
        if role_value == int(Qt.ItemDataRole.DisplayRole):
            return row.display_text
        if role_value == int(Qt.ItemDataRole.ToolTipRole):
            return row.display_text
        if role_value == int(Qt.ItemDataRole.UserRole):
            return row.stable_id
        if role_value == self.ROW_ROLE:
            return row
        return None

    def set_rows(self, rows: list[LibraryRow]) -> None:
        """Replace the projected rows in one model reset."""
        self.beginResetModel()
        self._rows = self._sort_rows(rows)
        self.endResetModel()

    def set_sort(self, field: Optional[str], descending: bool = False) -> None:
        """Sort typed rows by one primary field with deterministic tie breakers."""
        self._sort_field = field
        self._sort_descending = descending
        self.beginResetModel()
        self._rows = self._sort_rows(self._rows)
        self.endResetModel()

    def _sort_rows(self, rows: list[LibraryRow]) -> list[LibraryRow]:
        """Return rows in the configured stable order."""
        result = list(rows)
        if self._sort_field == "status":
            result.sort(key=lambda row: (row.display_name.casefold(), row.stable_id.casefold()))
            result.sort(
                key=lambda row: self._status_rank(row.sync_status),
                reverse=self._sort_descending,
            )
        elif self._sort_field == "last_modified":
            timestamped = [row for row in result if row.last_modified is not None]
            missing = [row for row in result if row.last_modified is None]
            timestamped.sort(
                key=lambda row: (
                    row.display_name.casefold(),
                    self._status_rank(row.sync_status),
                    row.stable_id.casefold(),
                )
            )
            timestamped.sort(
                key=lambda row: cast(Any, row.last_modified),
                reverse=self._sort_descending,
            )
            missing.sort(
                key=lambda row: (
                    row.display_name.casefold(),
                    self._status_rank(row.sync_status),
                    row.stable_id.casefold(),
                )
            )
            result = timestamped + missing
        elif self._sort_field == "name":
            result.sort(key=lambda row: row.stable_id.casefold())
            result.sort(
                key=lambda row: row.display_name.casefold(),
                reverse=self._sort_descending,
            )
        return result

    @staticmethod
    def _status_rank(status: str) -> int:
        """Return the stable status ordering used by the manager."""
        return {
            "Checking": 0,
            "Unknown": 1,
            "Local changes and remote updates": 2,
            "Local changes": 3,
            "Remote updates available": 4,
            "Locally ahead": 5,
            "No remote source": 6,
            "Current": 7,
        }.get(status, 1)


class LibraryEntryFilterProxyModel(QSortFilterProxyModel):
    """Filter typed rows by identity and exact status/condition labels."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._query = ""
        self._status_filter: Optional[str] = None

    def set_search_query(self, query: str) -> None:
        """Set a case-insensitive identity search query."""
        self._query = query.casefold()
        self.invalidateFilter()

    def set_status_filter(self, status: Optional[str]) -> None:
        """Set an exact synchronization or condition filter."""
        self._status_filter = status
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        """Return whether one typed source row is visible."""
        source_model = self.sourceModel()
        if source_model is None:
            return False
        index = source_model.index(source_row, 0, cast(QModelIndex, source_parent))
        row = source_model.data(index, LibraryEntryListModel.ROW_ROLE)
        if not isinstance(row, LibraryRow):
            return False
        if self._query and not (
            self._query in row.display_name.casefold()
            or self._query in row.stable_id.casefold()
        ):
            return False
        if self._status_filter and not (
            self._status_filter == row.sync_status
            or self._status_filter in row.conditions
        ):
            return False
        return True


class LibraryListWidget(QWidget):
    """Searchable, sortable list of connected collection libraries."""

    library_selected = Signal(str)
    selection_cleared = Signal()
    clone_clicked = Signal()
    connect_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("<b>Connected Libraries</b>")
        layout.addWidget(header)

        self.guidance_label = QLabel(self)
        self.guidance_label.setWordWrap(True)
        layout.addWidget(self.guidance_label)

        controls = QHBoxLayout()
        self.search_input = QLineEdit(self)
        set_widget_id(self.search_input, LIBRARY_SEARCH_INPUT)
        self.search_input.setPlaceholderText("Search by library name or ID")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.set_search_query)
        controls.addWidget(self.search_input)
        self.clear_search_button = QPushButton("Clear Search", self)
        set_widget_id(self.clear_search_button, LIBRARY_CLEAR_SEARCH_BUTTON)
        self.clear_search_button.clicked.connect(self.clear_search)
        controls.addWidget(self.clear_search_button)
        self.status_filter_combo = QComboBox(self)
        set_widget_id(self.status_filter_combo, LIBRARY_STATUS_FILTER)
        self.status_filter_combo.addItem("All statuses", None)
        for label in (
            "Checking", "Unknown", "Local changes and remote updates", "Local changes",
            "Remote updates available", "Locally ahead", "No remote source", "Current",
            "Offline", "Unavailable", "Invalid", "Error",
        ):
            self.status_filter_combo.addItem(label, label)
        self.status_filter_combo.currentIndexChanged.connect(
            lambda index: self.set_status_filter(self.status_filter_combo.itemData(index))
        )
        controls.addWidget(self.status_filter_combo)
        self.clear_filter_button = QPushButton("Clear Filter", self)
        set_widget_id(self.clear_filter_button, LIBRARY_CLEAR_FILTER_BUTTON)
        self.clear_filter_button.clicked.connect(self.clear_filter)
        controls.addWidget(self.clear_filter_button)
        self.sort_combo = QComboBox(self)
        set_widget_id(self.sort_combo, LIBRARY_SORT_COMBO)
        self.sort_combo.addItem("Input order", None)
        self.sort_combo.addItem("Name", "name")
        self.sort_combo.addItem("Status", "status")
        self.sort_combo.addItem("Last modified", "last_modified")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        controls.addWidget(self.sort_combo)
        self.sort_direction_button = QPushButton("Ascending", self)
        self.sort_direction_button.setCheckable(True)
        self.sort_direction_button.toggled.connect(self._on_sort_direction_changed)
        controls.addWidget(self.sort_direction_button)
        layout.addLayout(controls)

        self.list_widget = QListView(self)
        set_widget_id(self.list_widget, LIBRARY_LIST)
        self._entry_model = LibraryEntryListModel(self)
        self._entry_proxy = LibraryEntryFilterProxyModel(self)
        self._entry_proxy.setSourceModel(self._entry_model)
        self.list_widget.setModel(self._entry_proxy)
        self.list_widget.selectionModel().currentChanged.connect(self._on_index_changed)
        layout.addWidget(self.list_widget)

        self.clone_button = QPushButton("Clone New Library...", self)
        set_widget_id(self.clone_button, LIBRARY_CLONE_BUTTON)
        self.clone_button.clicked.connect(self.clone_clicked.emit)
        layout.addWidget(self.clone_button)

        self.connect_button = QPushButton("Connect Local Directory...", self)
        set_widget_id(self.connect_button, LIBRARY_CONNECT_BUTTON)
        self.connect_button.clicked.connect(self.connect_clicked.emit)
        layout.addWidget(self.connect_button)

        self._entries: List[Any] = []
        self._search_query = ""
        self._status_filter: Optional[str] = None
        self._sort_field: Optional[str] = None
        self._sort_descending = False
        self._operation_states: dict[str, str] = {}
        self.selected_library_id: Optional[str] = None
        self.selection_guidance = "Select a library to see its details."
        self.last_confirmation = ""
        self._suppress_selection = False
        self.guidance_label.setText(self.selection_guidance)

    def _on_sort_changed(self, index: int) -> None:
        field = self.sort_combo.itemData(index)
        if field:
            self.set_sort(field, self.sort_direction_button.isChecked())

    def _on_sort_direction_changed(self, descending: bool) -> None:
        field = self.sort_combo.currentData()
        self.sort_direction_button.setText("Descending" if descending else "Ascending")
        if field:
            self.set_sort(field, descending)

    def set_libraries(self, libraries: List[str], current: Optional[str] = None) -> None:
        """Populate library list and restore current selection."""
        self._entries = [
            type("LibraryRow", (), {"stable_id": library, "display_name": library})()
            for library in libraries
        ]
        self._render_entries(current)

    def set_entries(self, entries: List[Any]) -> None:
        """Populate rows from typed records or compatible test doubles."""
        previous = self.selected_library_id
        self._entries = list(entries)
        self._render_entries(previous)

    @staticmethod
    def _id(entry: Any) -> str:
        """Return the stable identity from a row, record, or nested record."""
        value = getattr(entry, "stable_id", None) or getattr(entry, "library_id", None)
        record = getattr(entry, "connection", None)
        if not value and record is not None:
            value = getattr(record, "stable_id", None)
        return str(value or "")

    @classmethod
    def _name(cls, entry: Any) -> str:
        """Return display name, falling back to the stable identity."""
        value = getattr(entry, "display_name", None)
        if value is None:
            record = getattr(entry, "connection", None)
            value = getattr(record, "display_name", None) if record is not None else None
        return str(value or cls._id(entry))

    @staticmethod
    def _status(entry: Any) -> str:
        status = getattr(entry, "sync_status", None)
        if status is None:
            snapshot = getattr(entry, "status", None)
            status = getattr(snapshot, "sync_status", None)
        if status is None and hasattr(entry, "is_clean"):
            status = LibraryStatusResolver.sync_status(entry)
        return str(getattr(status, "value", status) or "Unknown")

    @staticmethod
    def _conditions(entry: Any) -> List[str]:
        values = getattr(entry, "conditions", None)
        if values is None:
            snapshot = getattr(entry, "status", None)
            values = getattr(snapshot, "conditions", []) if snapshot is not None else []
        return [str(getattr(value, "value", value)) for value in values or []]

    def _row(self, entry: Any) -> LibraryRow:
        """Create the UI-facing row projection without performing I/O."""
        stable_id = self._id(entry)
        conditions = self._conditions(entry)
        source = getattr(entry, "source_type", None)
        if source is None:
            source = getattr(getattr(entry, "connection", None), "source_type", "")
        clean = getattr(entry, "is_clean", None)
        if clean is None:
            snapshot = getattr(entry, "status", None)
            clean = getattr(snapshot, "is_clean", None)
        badges = [self._status(entry)]
        badges.append(
            "Clean"
            if clean is True
            else "Local changes"
            if clean is False
            else "Local state unavailable"
        )
        badges.extend(conditions)
        is_stale = getattr(entry, "is_stale", False)
        if is_stale is False:
            is_stale = bool(getattr(getattr(entry, "status", None), "is_stale", False))
        if is_stale and "Stale" not in badges:
            badges.append("Stale")
        snapshot = getattr(entry, "status", None)
        last_modified = getattr(entry, "last_modified", None)
        if last_modified is None:
            last_modified = getattr(snapshot, "last_modified", None)
        last_checked = getattr(snapshot, "last_successful_check", None)
        last_checked = last_checked or getattr(snapshot, "last_checked_at", None)
        ahead = getattr(entry, "ahead_count", None)
        if ahead is None:
            ahead = getattr(snapshot, "ahead_count", 0)
        behind = getattr(entry, "behind_count", None)
        if behind is None:
            behind = getattr(snapshot, "behind_count", 0)
        return LibraryRow(
            stable_id=stable_id,
            display_name=self._name(entry),
            source_type=str(getattr(source, "value", source) or ""),
            local_path=getattr(entry, "local_path", None)
            or getattr(getattr(entry, "connection", None), "local_path", None),
            sync_status=self._status(entry),
            conditions=conditions,
            badges=badges,
            is_clean=clean,
            last_modified=last_modified,
            last_checked_at=last_checked,
            ahead_count=int(ahead or 0),
            behind_count=int(behind or 0),
            is_stale=bool(is_stale),
            diagnostic=getattr(entry, "diagnostic", None)
            or getattr(snapshot, "diagnostic", None),
            is_read_only=bool(
                getattr(entry, "is_read_only", False)
                or getattr(getattr(entry, "connection", None), "is_read_only", False)
            ),
        )

    @staticmethod
    def _display_time(value: object) -> str:
        """Render a known timestamp without inventing one for unavailable data."""
        return value.isoformat() if hasattr(value, "isoformat") else "Unavailable"

    def _row_text(self, row: LibraryRow) -> str:
        """Render all actionable row facts as text and accessible item content."""
        position = f"↑{row.ahead_count} ↓{row.behind_count}"
        diagnostic = row.diagnostic
        guidance = f" | Guidance: {diagnostic}" if diagnostic else ""
        return (
            f"{row.display_name} — {row.source_type or 'Source unavailable'}\n"
            f"{' | '.join(row.badges)} | Sync position: {position}\n"
            f"Path: {row.local_path or 'Unavailable'} | "
            f"Last modified: {self._display_time(row.last_modified)} | "
            f"Last checked: {self._display_time(row.last_checked_at)}{guidance}"
        )

    def _visible_entries(self) -> List[Any]:
        by_id = {self._id(entry): entry for entry in self._entries}
        return [
            by_id[
                str(
                    self._entry_proxy.data(
                        self._entry_proxy.index(row, 0), Qt.ItemDataRole.UserRole
                    )
                )
            ]
            for row in range(self._entry_proxy.rowCount())
        ]

    def _render_entries(self, current: Optional[str]) -> None:
        rows: list[LibraryRow] = []
        for entry in self._entries:
            row = self._row(entry)
            operation = self._operation_states.get(row.stable_id)
            if operation:
                row = replace(row, badges=[*row.badges, f"{operation} in progress"])
            row = replace(row, display_text=self._row_text(row))
            rows.append(row)
        self._suppress_selection = True
        self._entry_model.set_rows(rows)
        self._entry_model.set_sort(self._sort_field, self._sort_descending)
        self._entry_proxy.set_search_query(self._search_query)
        self._entry_proxy.set_status_filter(self._status_filter)
        visible = self._visible_entries()
        visible_ids = [self._id(entry) for entry in visible]
        selected_row = visible_ids.index(current) if current in visible_ids else -1
        self._suppress_selection = False
        self.selected_library_id = current if selected_row >= 0 else None
        if selected_row >= 0:
            self.selection_guidance = ""
            self.list_widget.setCurrentIndex(self._entry_proxy.index(selected_row, 0))
        elif visible:
            self.selection_guidance = "Select a library to see its details."
            if any("Offline" in self._row(entry).conditions for entry in visible):
                self.selection_guidance += (
                    " Offline rows retain last-known local information; remote actions "
                    "require connectivity."
                )
        else:
            self.selection_guidance = (
                "No matching libraries. Clear the search or status filter."
                if self._entries
                else "No libraries are connected. Clone or connect a library."
            )
        self.guidance_label.setText(self.selection_guidance)
        if current and selected_row < 0:
            self.selection_cleared.emit()

    def set_search_query(self, query: str) -> None:
        """Apply a case-insensitive search and preserve selection by stable ID."""
        self._search_query = query
        self._render_entries(self.selected_library_id)

    def clear_search(self) -> None:
        """Clear the current search query."""
        self._search_query = ""
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._render_entries(self.selected_library_id)

    def set_status_filter(self, status: Optional[str]) -> None:
        """Apply one exact synchronization or condition label."""
        self._status_filter = status
        self._render_entries(self.selected_library_id)

    def clear_filter(self) -> None:
        """Reset the status filter to all statuses."""
        self._status_filter = None
        self.status_filter_combo.blockSignals(True)
        self.status_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.blockSignals(False)
        self._render_entries(self.selected_library_id)

    def set_sort(self, field: str, descending: bool = False) -> None:
        """Set name, status, or last-modified sorting."""
        if field not in {"name", "status", "last_modified"}:
            raise ValueError(f"Unsupported library sort field: {field}")
        self._sort_field = field
        self._sort_descending = descending
        self._render_entries(self.selected_library_id)

    def visible_library_ids(self) -> List[str]:
        """Return visible stable IDs in active filter and sort order."""
        return [
            str(
                self._entry_proxy.data(
                    self._entry_proxy.index(row, 0), Qt.ItemDataRole.UserRole
                )
            )
            for row in range(self._entry_proxy.rowCount())
        ]

    def row_for_library(self, library_id: str) -> Optional[LibraryRow]:
        """Return a row projection by stable ID."""
        for entry in self._entries:
            if self._id(entry) == library_id:
                return self._row(entry)
        return None

    def update_entry(self, library_id: str, status: object) -> None:
        """Update one projected row by stable ID without replacing other records."""
        for index, entry in enumerate(self._entries):
            if self._id(entry) != library_id:
                continue
            if isinstance(status, LibraryListEntry):
                self._entries[index] = status
            elif not isinstance(entry, LibraryListEntry):
                continue
            elif isinstance(status, LibraryStatusSnapshot):
                snapshot = status
            else:
                snapshot = LibraryStatusResolver.successful(status)
            if not isinstance(status, LibraryListEntry):
                self._entries[index] = entry.model_copy(update={"status": snapshot})
            self._render_entries(self.selected_library_id)
            return

    def set_operation_state(self, library_id: str, operation: str, active: bool) -> None:
        """Show or clear one operation's in-progress badge by stable ID."""
        if active:
            self._operation_states[library_id] = operation
        else:
            self._operation_states.pop(library_id, None)
        self._render_entries(self.selected_library_id)

    def select_library(self, library_id: str) -> None:
        """Select item matching library_id."""
        for i in range(self._entry_proxy.rowCount()):
            index = self._entry_proxy.index(i, 0)
            item_id = self._entry_proxy.data(index, Qt.ItemDataRole.UserRole)
            if item_id == library_id:
                self.list_widget.setCurrentIndex(index)
                self.selected_library_id = library_id
                self.selection_guidance = ""
                break
        else:
            self.selected_library_id = None
            self.selection_guidance = "Select a visible library to see its details."

    def actions_for_library(self, library_id: str) -> List[str]:
        """Return safe actions available for a row's source type."""
        row = self.row_for_library(library_id)
        if row is None:
            return []
        if row.is_read_only:
            return ["refresh", "copy_path", "copy_to_editable"]
        actions = ["refresh", "pull", "switch_branch", "copy_path", "disconnect"]
        if row.source_type != "Registered local directory":
            actions.append("delete")
        return actions

    def copy_library_path(self, library_id: str) -> str:
        """Copy the exact stored local path and expose a short confirmation."""
        row = self.row_for_library(library_id)
        path = str(row.local_path) if row is not None and row.local_path else ""
        QApplication.clipboard().setText(path)
        self.last_confirmation = f"Copied library path: {path}"
        return path

    def _on_index_changed(self, current: QModelIndex, _previous: QModelIndex) -> None:
        """Publish selection changes using the stable identity role."""
        if self._suppress_selection:
            return
        library_id = self._entry_proxy.data(current, Qt.ItemDataRole.UserRole)
        if library_id:
            self.selected_library_id = str(library_id)
            self.library_selected.emit(str(library_id))


class LibraryDetailWidget(QWidget):
    """Header and controls for the selected library."""

    pull_clicked = Signal()
    commit_push_clicked = Signal()
    switch_branch_clicked = Signal()
    delete_clicked = Signal()
    refresh_clicked = Signal()
    copy_path_clicked = Signal()
    disconnect_clicked = Signal()

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

        self.source_label = QLabel("Source: -", self)
        layout.addWidget(self.source_label)

        self.metadata_label = QLabel("Last modified: Unavailable | Last checked: Unavailable", self)
        self.metadata_label.setWordWrap(True)
        layout.addWidget(self.metadata_label)

        self.progress_label = QLabel("", self)
        self.progress_label.setWordWrap(True)
        layout.addWidget(self.progress_label)

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

        self.refresh_button = QPushButton("Refresh", self)
        set_widget_id(self.refresh_button, LIBRARY_REFRESH_BUTTON)
        self.refresh_button.clicked.connect(self.refresh_clicked.emit)
        actions_layout.addWidget(self.refresh_button)

        self.copy_path_button = QPushButton("Copy Path", self)
        set_widget_id(self.copy_path_button, LIBRARY_COPY_PATH_BUTTON)
        self.copy_path_button.clicked.connect(self.copy_path_clicked.emit)
        actions_layout.addWidget(self.copy_path_button)

        self.disconnect_button = QPushButton("Disconnect", self)
        set_widget_id(self.disconnect_button, LIBRARY_DISCONNECT_BUTTON)
        self.disconnect_button.clicked.connect(self.disconnect_clicked.emit)
        actions_layout.addWidget(self.disconnect_button)

        actions_layout.addStretch()

        self.delete_button = QPushButton("Remove Library", self)
        set_widget_id(self.delete_button, LIBRARY_DELETE_BUTTON)
        self.delete_button.setStyleSheet("color: #721c24; background-color: #f8d7da;")
        self.delete_button.clicked.connect(self.delete_clicked.emit)
        actions_layout.addWidget(self.delete_button)

        layout.addLayout(actions_layout)

        self.setEnabled(False)

    def clear_details(self) -> None:
        """Clear all selected-library data so a filtered-out row cannot remain visible."""
        self.title_label.setText("<h2>No Library Selected</h2>")
        self.desc_label.setText("Select a library to see its details.")
        self.path_label.setText("")
        self.source_label.setText("Source: -")
        self.metadata_label.setText("Last modified: Unavailable | Last checked: Unavailable")
        self.progress_label.setText("")
        self.update_status(None)
        self.set_source_type(None)
        self.setEnabled(False)

    def set_source_type(self, source_type: Optional[object]) -> None:
        """Show destructive controls only for managed clones."""
        source = str(getattr(source_type, "value", source_type) or "")
        self.source_label.setText(f"Source: {source or 'Unavailable'}")
        is_clone = source == "Cloned managed copy"
        self.delete_button.setVisible(is_clone)
        self.delete_button.setEnabled(is_clone and self.isEnabled())

    def set_operation_state(self, operation: str, active: bool) -> None:
        """Render progress and disable controls while the selected operation runs."""
        if active:
            self.progress_label.setText(f"{operation.replace('_', ' ').title()} in progress...")
            for button in self.findChildren(QPushButton):
                button.setEnabled(False)
        else:
            self.progress_label.setText("")
            enabled = self.isEnabled()
            for button in self.findChildren(QPushButton):
                button.setEnabled(enabled)
            self.set_source_type(self.source_label.text().removeprefix("Source: ").strip())

    @staticmethod
    def _display_time(value: object) -> str:
        """Render a known timestamp without substituting the dialog-open time."""
        return value.isoformat() if hasattr(value, "isoformat") else "Unavailable"

    def update_manifest(
        self,
        manifest: Optional[LibraryManifest],
        library_id: Optional[str] = None,
    ) -> None:
        """Update display title, description, and metadata from manifest."""
        if not manifest and not library_id:
            self.clear_details()
            return

        self.setEnabled(True)
        title = manifest.name if manifest else library_id
        version = f" (v{manifest.version})" if manifest and manifest.version else ""
        self.title_label.setText(f"<h2>{title}{version}</h2>")
        desc = manifest.description if manifest and manifest.description else "No description."
        self.desc_label.setText(desc)

    def update_status(
        self, status: Optional[GitRepoStatus | LibraryStatusSnapshot]
    ) -> None:
        """Update status badges based on GitRepoStatus."""
        if not status:
            self.branch_badge.setText("Branch: -")
            self.dirty_badge.setText("Status: -")
            self.sync_badge.setText("Sync: -")
            self.path_label.setText("")
            return

        if hasattr(status, "sync_status"):
            branch = getattr(status, "current_branch", None) or "No active branch"
            self.branch_badge.setText(f"Branch: {branch}")
            local_path = getattr(status, "local_path", None)
            self.path_label.setText(f"Path: {local_path}" if local_path else "Path: Unavailable")
            last_modified = self._display_time(getattr(status, "last_modified", None))
            last_checked = self._display_time(
                getattr(status, "last_successful_check", None)
                or getattr(status, "last_checked_at", None)
            )
            self.metadata_label.setText(
                f"Last modified: {last_modified} | Last checked: {last_checked}"
            )
            is_clean = getattr(status, "is_clean", None)
            dirty_files = list(getattr(status, "dirty_files", []) or [])
            self.dirty_badge.setText(
                "Clean"
                if is_clean is True
                else (
                    f"Local changes ({len(dirty_files)})"
                    if is_clean is False
                    else "Status unavailable"
                )
            )
            sync = getattr(status.sync_status, "value", status.sync_status)
            conditions = [
                str(getattr(condition, "value", condition))
                for condition in getattr(status, "conditions", [])
            ]
            badges = [str(sync), *conditions]
            if getattr(status, "is_stale", False) and "Stale" not in badges:
                badges.append("Stale")
            position = (
                f"↑{getattr(status, 'ahead_count', 0)} "
                f"↓{getattr(status, 'behind_count', 0)}"
            )
            self.sync_badge.setText(" | ".join([*badges, f"Position: {position}"]))
            diagnostic = getattr(status, "diagnostic", None)
            if diagnostic:
                self.desc_label.setText(diagnostic)
            return

        # Branch badge
        branch = status.current_branch or "No active branch"
        self.branch_badge.setText(f"Branch: {branch}")
        self.path_label.setText(f"Path: {status.repo_path}")
        self.metadata_label.setText("Last modified: Unavailable | Last checked: Unavailable")

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

        sync = LibraryStatusResolver.sync_status(status).value
        self.sync_badge.setText(f"Sync: {sync}")


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
