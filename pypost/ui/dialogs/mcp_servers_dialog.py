"""UI for managing independently configured MCP servers."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import McpServerStatus
from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration
from pypost.ui.dialogs.mcp_activity_dialog import McpActivityDialog
from pypost.ui.dialogs.mcp_tools_overview_dialog import McpToolsOverviewDialog


class McpServersDialog(QDialog):
    """Manage persisted MCP endpoints without coupling rows to UI selection."""

    _COLUMNS = (
        "Name",
        "ID",
        "State",
        "Endpoint",
        "Collection",
        "Environment",
        "Error",
    )

    def __init__(
        self,
        *,
        configurations: Callable[[], list[McpServerConfiguration]],
        status_for: Callable[[str], McpServerStatus],
        save: Callable[[McpServerConfiguration], None],
        remove: Callable[[str], None],
        start: Callable[[str], None],
        stop: Callable[[str], None],
        activity: Callable[[str], list[McpActivityEntry]],
        collections: Callable[[], Iterable[Collection]],
        environments: Callable[[], Iterable[Environment]],
        legacy_environment: Callable[[], Environment | None],
        legacy_host: str,
        legacy_port: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MCP Servers")
        self.resize(940, 480)
        self._configurations = configurations
        self._status_for = status_for
        self._save = save
        self._remove = remove
        self._start = start
        self._stop = stop
        self._activity = activity
        self._collections = collections
        self._environments = environments
        self._legacy_environment = legacy_environment
        self._legacy_host = legacy_host
        self._legacy_port = legacy_port
        self._table = QTableWidget(0, len(self._COLUMNS), self)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        help_text = QLabel(
            "Each row owns its collection, environment and port. Existing legacy "
            "environment MCP settings are never started automatically."
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        self._table.setHorizontalHeaderLabels(self._COLUMNS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

        controls = QHBoxLayout()
        add = QPushButton("Add…")
        add.clicked.connect(self._add)
        edit = QPushButton("Edit…")
        edit.clicked.connect(self._edit)
        start = QPushButton("Start")
        start.clicked.connect(lambda: self._operate(self._start))
        stop = QPushButton("Stop")
        stop.clicked.connect(lambda: self._operate(self._stop))
        activity = QPushButton("Activity…")
        activity.clicked.connect(self._show_activity)
        tools = QPushButton("Tools…")
        tools.clicked.connect(self._show_tools)
        remove = QPushButton("Remove")
        remove.clicked.connect(self._remove_selected)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        for button in (add, edit, start, stop, activity, tools, remove, refresh):
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)

        legacy = self._legacy_environment()
        if legacy is not None and legacy.enable_mcp:
            convert = QPushButton("Convert current legacy MCP setting…")
            convert.setToolTip(
                "Preselects the current legacy environment. Select a collection to "
                "create a new explicit server row; it does not alter the legacy setting."
            )
            convert.clicked.connect(lambda: self._add(legacy_environment=legacy))
            layout.addWidget(convert)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def refresh(self) -> None:
        configurations = self._configurations()
        collection_names = {item.id: item.name for item in self._collections()}
        environment_names = {item.id: item.name for item in self._environments()}
        self._table.setRowCount(len(configurations))
        for row, configuration in enumerate(configurations):
            status = self._status_for(configuration.id)
            values = (
                configuration.name or configuration.id,
                configuration.id,
                status.state,
                f"{configuration.host}:{configuration.port}",
                collection_names.get(configuration.collection_id, configuration.collection_id),
                environment_names.get(configuration.environment_id, configuration.environment_id),
                status.message,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 2 and status.message:
                    item.setToolTip(status.message)
                self._table.setItem(row, column, item)
        self._table.resizeColumnsToContents()

    def _selected(self) -> McpServerConfiguration | None:
        row = self._table.currentRow()
        configurations = self._configurations()
        return configurations[row] if 0 <= row < len(configurations) else None

    def _add(self, _checked: bool = False, legacy_environment: Environment | None = None) -> None:
        dialog = _McpServerEditor(
            collections=list(self._collections()),
            environments=list(self._environments()),
            configuration=None,
            default_environment=legacy_environment,
            default_host=self._legacy_host,
            default_port=self._legacy_port,
            parent=self,
        )
        if dialog.exec():
            try:
                self._save(dialog.configuration())
            except ValueError as exc:
                self._show_error(str(exc))
            else:
                self.refresh()

    def _edit(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        dialog = _McpServerEditor(
            collections=list(self._collections()),
            environments=list(self._environments()),
            configuration=selected,
            default_environment=None,
            default_host=self._legacy_host,
            default_port=self._legacy_port,
            parent=self,
        )
        if dialog.exec():
            try:
                self._save(dialog.configuration())
            except ValueError as exc:
                self._show_error(str(exc))
            else:
                self.refresh()

    def _operate(self, operation: Callable[[str], None]) -> None:
        selected = self._selected()
        if selected is None:
            return
        try:
            operation(selected.id)
        except (KeyError, ValueError) as exc:
            self._show_error(str(exc))
        self.refresh()

    def _remove_selected(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        if QMessageBox.question(
            self, "Remove MCP server", f"Remove {selected.name or selected.id}?"
        ) != QMessageBox.StandardButton.Yes:
            return
        self._remove(selected.id)
        self.refresh()

    def _show_activity(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        dialog = McpActivityDialog(self._activity(selected.id), self)
        dialog.setWindowTitle(f"MCP Activity — {selected.name or selected.id}")
        dialog.exec()

    def _show_tools(self) -> None:
        """Show only tools exposed by the selected server's collection."""
        selected = self._selected()
        if selected is None:
            return
        collection = next(
            (
                item
                for item in self._collections()
                if item.id == selected.collection_id
            ),
            None,
        )
        if collection is None:
            self._show_error("The selected MCP server's collection no longer exists.")
            return
        dialog = McpToolsOverviewDialog(collect_mcp_tool_overview([collection]), self)
        dialog.setWindowTitle(f"MCP Tools — {selected.name or selected.id}")
        dialog.exec()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "MCP server", message)


class _McpServerEditor(QDialog):
    """Small validated editor shared by Add, Edit and legacy conversion."""

    def __init__(
        self,
        *,
        collections: list[Collection],
        environments: list[Environment],
        configuration: McpServerConfiguration | None,
        default_environment: Environment | None,
        default_host: str,
        default_port: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit MCP server" if configuration else "Add MCP server")
        self._id = configuration.id if configuration else str(uuid.uuid4())
        self._enabled = configuration.enabled if configuration else False
        layout = QFormLayout(self)
        self._name = QLineEdit(configuration.name or "" if configuration else "")
        self._host = QLineEdit(configuration.host if configuration else default_host)
        self._port = QSpinBox()
        self._port.setRange(1024, 65535)
        self._port.setValue(configuration.port if configuration else default_port)
        self._collection = QComboBox()
        self._environment = QComboBox()
        for collection in collections:
            self._collection.addItem(collection.name, collection.id)
        for environment in environments:
            self._environment.addItem(environment.name, environment.id)
        target_environment = (
            configuration.environment_id
            if configuration
            else getattr(default_environment, "id", None)
        )
        if configuration:
            self._select_data(self._collection, configuration.collection_id)
        if target_environment:
            self._select_data(self._environment, target_environment)
        layout.addRow("Name", self._name)
        layout.addRow("Host", self._host)
        layout.addRow("Port", self._port)
        layout.addRow("Collection", self._collection)
        layout.addRow("Environment", self._environment)
        self._error = QLabel()
        self._error.setStyleSheet("color: #b00020;")
        self._error.setWordWrap(True)
        layout.addRow(self._error)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_complete)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _accept_if_complete(self) -> None:
        if self._collection.currentData() is None or self._environment.currentData() is None:
            self._error.setText("Collection and environment are required.")
            return
        if not self._host.text().strip():
            self._error.setText("Host is required.")
            return
        self.accept()

    def configuration(self) -> McpServerConfiguration:
        return McpServerConfiguration(
            id=self._id,
            name=self._name.text().strip() or None,
            host=self._host.text().strip(),
            port=self._port.value(),
            collection_id=str(self._collection.currentData()),
            environment_id=str(self._environment.currentData()),
            enabled=self._enabled,
        )
