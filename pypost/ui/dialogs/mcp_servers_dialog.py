"""UI for managing independently configured MCP servers."""

from __future__ import annotations

import logging
import json
import uuid
from collections.abc import Callable, Iterable
from typing import Any, Literal

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
from pypost.ui.widgets.mcp_server_headers_table import McpServerHeadersTable
from pypost.ui.mcp_library_source_picker import LibraryMcpSourcePicker

logger = logging.getLogger(__name__)


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
        save_library: Callable[[McpServerConfiguration, dict, object], None] | None = None,
        remove: Callable[[str], None],
        start: Callable[[str], None],
        stop: Callable[[str], None],
        activity: Callable[[str], list[McpActivityEntry]],
        collections: Callable[[], Iterable[Collection]],
        environments: Callable[[], Iterable[Environment]],
        legacy_environment: Callable[[], Environment | None],
        legacy_host: str,
        legacy_port: int,
        library_service=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("MCP Servers")
        self.resize(940, 480)
        self._configurations = configurations
        self._status_for = status_for
        self._save = save
        self._save_library = save_library
        self._remove = remove
        self._start = start
        self._stop = stop
        self._activity = activity
        self._collections = collections
        self._environments = environments
        self._legacy_environment = legacy_environment
        self._legacy_host = legacy_host
        self._legacy_port = legacy_port
        self._library_service = library_service
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
            if configuration.server_type == "proxy":
                target_desc = (
                    f"Proxy -> {configuration.upstream_url}"
                    if configuration.upstream_url
                    else "Proxy"
                )
            else:
                if configuration.library_id:
                    target_desc = self._library_collection_description(configuration)
                else:
                    cid = configuration.collection_id or ""
                    target_desc = collection_names.get(cid, cid)
            values = (
                configuration.name or configuration.id,
                configuration.id,
                status.state,
                f"{configuration.host}:{configuration.port}",
                target_desc,
                environment_names.get(configuration.environment_id, configuration.environment_id),
                status.message,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 2 and status.message:
                    item.setToolTip(status.message)
                self._table.setItem(row, column, item)
        self._table.resizeColumnsToContents()

    def _library_collection_description(
        self, configuration: McpServerConfiguration
    ) -> str:
        """Describe a library row even though it has no workspace collection ID."""
        library_id = configuration.library_id or "unknown-library"
        library_name = library_id
        collection_name = configuration.library_collection_path or "unknown collection"
        service = self._library_service
        if service is not None:
            try:
                record = service.get_connection(library_id)
                library_name = str(getattr(record, "display_name", None) or library_id)
                entries = service.list_manifest_collections(library_id)
                for entry in entries:
                    if (
                        entry.get("path") == configuration.library_collection_path
                        and (
                            configuration.library_collection_index is None
                            or entry.get("index") == configuration.library_collection_index
                        )
                    ):
                        collection_name = str(
                            entry.get("name") or entry.get("path") or collection_name
                        )
                        break
            except (OSError, ValueError, KeyError, AttributeError):
                pass
        return f"{library_name} / {collection_name} [{library_id}]"

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
            library_service=self._library_service,
            parent=self,
        )
        if dialog.exec():
            try:
                config = dialog.configuration()
                header_count = len(config.headers) if config.headers else 0
                logger.info(
                    "Adding new MCP server: id=%s, type=%s, name=%s (header_count=%d)",
                    config.id,
                    config.server_type,
                    config.name,
                    header_count,
                )
                self._save_configuration(dialog, config)
            except ValueError as exc:
                logger.warning(
                    "Failed to add MCP server %s: %s",
                    getattr(config, "id", "unknown"),
                    exc,
                )
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
            library_service=self._library_service,
            parent=self,
        )
        if dialog.exec():
            try:
                config = dialog.configuration()
                header_count = len(config.headers) if config.headers else 0
                logger.info(
                    "Updating MCP server: id=%s, type=%s, name=%s (header_count=%d)",
                    config.id,
                    config.server_type,
                    config.name,
                    header_count,
                )
                self._save_configuration(dialog, config)
            except ValueError as exc:
                logger.warning(
                    "Failed to update MCP server %s: %s",
                    getattr(config, "id", "unknown"),
                    exc,
                )
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
        logger.info("Removing MCP server: id=%s, name=%s", selected.id, selected.name)
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
        if selected.server_type == "proxy":
            self._show_error("Tool overview is only available for local collection MCP servers.")
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

    def _save_configuration(
        self, dialog: "_McpServerEditor", config: McpServerConfiguration
    ) -> None:
        selection = dialog.library_selection()
        if selection is not None and self._save_library is not None:
            self._save_library(config, selection, dialog.library_handoff())
            return
        self._save(config)


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
        library_selections: list[dict[str, object]] | None = None,
        library_service=None,
        library_worker_factory=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit MCP server" if configuration else "Add MCP server")
        self._id = configuration.id if configuration else str(uuid.uuid4())
        self._enabled = configuration.enabled if configuration else False
        self._layout = QFormLayout(self)
        self._name = QLineEdit(configuration.name or "" if configuration else "")
        self._host = QLineEdit(configuration.host if configuration else default_host)
        self._port = QSpinBox()
        self._port.setRange(1024, 65535)
        self._port.setValue(configuration.port if configuration else default_port)

        self._server_type = QComboBox()
        self._server_type.addItem("Local Collection", "local")
        self._server_type.addItem("Upstream Proxy", "proxy")

        self._collection = QComboBox()
        self._collection_source = QComboBox()
        self._collection_source.addItem("Workspace collection", "workspace")
        self._collection_source.addItem("Connected library", "library")
        self._library = QComboBox()
        self._library_records: dict[str, Any] = {}
        self._library_collection = QComboBox()
        self._library_selections = library_selections or []
        self._library_picker = (
            LibraryMcpSourcePicker(
                library_service=library_service, worker_factory=library_worker_factory
            )
            if library_service is not None
            else None
        )
        self._library_profile = QComboBox()
        self._library_variables = QFormLayout()
        self._library_variable_fields: dict[str, QLineEdit] = {}
        self._library_variable_types: dict[str, str] = {}
        self._library_secret_names: set[str] = set()
        self._library_overlay: dict[str, Any] = {}
        self._library_profile_unavailable = False
        self._library_collection_stale = False
        self._target_library_id = configuration.library_id if configuration else None
        self._target_collection_path = (
            configuration.library_collection_path if configuration else None
        )
        self._target_collection_identity = (
            self._selection_identity(
                {
                    "library_id": configuration.library_id,
                    "manifest_id": configuration.manifest_id,
                    "path": configuration.library_collection_path,
                    "index": configuration.library_collection_index,
                }
            )
            if configuration and configuration.library_id
            else None
        )
        self._library_listing_request: int | None = None
        self._library_manifest_request: int | None = None
        self._last_collection_source = "workspace"
        self._initializing = True
        for item in self._library_selections:
            self._library_collection.addItem(
                str(item.get("name") or item.get("path") or "Library collection"),
                item,
            )
        self._environment = QComboBox()
        self._environments_by_id: dict[str, Environment] = {env.id: env for env in environments}
        for collection in collections:
            self._collection.addItem(collection.name, collection.id)
        for environment in environments:
            self._environment.addItem(environment.name, environment.id)

        self._upstream_url = QLineEdit(
            configuration.upstream_url or "" if configuration else ""
        )
        self._upstream_transport = QComboBox()
        self._upstream_transport.addItem("Streamable HTTP", "streamable_http")
        self._upstream_transport.addItem("Server-Sent Events (SSE)", "sse")

        self._headers_table = McpServerHeadersTable(self)
        self._headers_table.setMinimumHeight(140)
        if configuration and configuration.headers:
            self._headers_table.set_data(configuration.headers)

        target_environment = (
            configuration.environment_id
            if configuration
            else getattr(default_environment, "id", None)
        )
        if configuration:
            if configuration.server_type == "proxy":
                self._select_data(self._server_type, "proxy")
            else:
                self._select_data(self._server_type, "local")
            if configuration.collection_id:
                self._select_data(self._collection, configuration.collection_id)
            if configuration.library_id:
                self._select_data(self._collection_source, "library")
                self._select_data(self._library, configuration.library_id)
            if configuration.upstream_transport:
                self._select_data(self._upstream_transport, configuration.upstream_transport)
        if target_environment:
            self._select_data(self._environment, target_environment)

        self._environment.currentIndexChanged.connect(self._on_environment_changed)
        self._on_environment_changed()

        self._layout.addRow("Name", self._name)
        self._layout.addRow("Host", self._host)
        self._layout.addRow("Port", self._port)
        self._layout.addRow("Server Type", self._server_type)
        self._layout.addRow("Collection Source", self._collection_source)
        self._layout.addRow("Collection", self._collection)
        self._layout.addRow("Connected Library", self._library)
        self._layout.addRow("Library Collection", self._library_collection)
        self._layout.addRow("Library Profile", self._library_profile)
        self._layout.addRow("Library Variables", self._library_variables)
        self._layout.addRow("Upstream URL", self._upstream_url)
        self._layout.addRow("Transport", self._upstream_transport)
        self._layout.addRow("Custom Headers", self._headers_table)
        self._layout.addRow("Environment", self._environment)

        self._error = QLabel()
        self._error.setStyleSheet("color: #b00020;")
        self._error.setWordWrap(True)
        self._layout.addRow(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_complete)
        buttons.rejected.connect(self.reject)
        self._layout.addRow(buttons)

        self._server_type.currentIndexChanged.connect(self._on_server_type_changed)
        self._collection_source.currentIndexChanged.connect(self._on_collection_source_changed)
        self._library.currentIndexChanged.connect(self._on_library_changed)
        self._library_collection.currentIndexChanged.connect(self._on_library_collection_changed)
        self._library_profile.currentIndexChanged.connect(self._on_library_profile_changed)
        self._on_server_type_changed()
        self._last_collection_source = str(self._collection_source.currentData() or "workspace")
        self._initializing = False
        self._on_collection_source_changed()
        if self._collection_source.currentData() == "library":
            self._begin_library_listing()

    def _on_environment_changed(self) -> None:
        env_id = self._environment.currentData()
        env = self._environments_by_id.get(str(env_id)) if env_id else None
        self._headers_table.set_environment(env)

    def _on_server_type_changed(self) -> None:
        is_proxy = self._server_type.currentData() == "proxy"
        self._collection.setVisible(not is_proxy)
        label_collection = self._layout.labelForField(self._collection)
        if label_collection:
            label_collection.setVisible(not is_proxy)

        self._upstream_url.setVisible(is_proxy)
        label_url = self._layout.labelForField(self._upstream_url)
        if label_url:
            label_url.setVisible(is_proxy)

        self._upstream_transport.setVisible(is_proxy)
        label_transport = self._layout.labelForField(self._upstream_transport)
        if label_transport:
            label_transport.setVisible(is_proxy)

        self._headers_table.setVisible(is_proxy)
        label_headers = self._layout.labelForField(self._headers_table)
        if label_headers:
            label_headers.setVisible(is_proxy)
        self._on_collection_source_changed()

    def _on_collection_source_changed(self) -> None:
        is_library = self._collection_source.currentData() == "library"
        is_local = self._server_type.currentData() == "local"
        source = "library" if is_library else "workspace"
        if not self._initializing and source != self._last_collection_source:
            self._cancel_library_discovery()
            # A source switch must never retain an incompatible identity.
            self._collection.setCurrentIndex(-1)
            self._library_collection.setCurrentIndex(-1)
        self._last_collection_source = source
        self._collection.setVisible(is_local and not is_library)
        self._library.setVisible(is_local and is_library)
        self._library_collection.setVisible(is_local and is_library)
        for field in (
            self._collection,
            self._library,
            self._library_collection,
            self._library_profile,
        ):
            label = self._layout.labelForField(field)
            if label:
                label.setVisible(field.isVisible())
        variables_label = self._layout.labelForField(self._library_variables)
        if variables_label:
            variables_label.setVisible(is_local and is_library)
        self._library_profile.setVisible(is_local and is_library)
        self._library_variables_widget_visible(is_local and is_library)
        if is_local and is_library and self._library.count() == 0:
            self._begin_library_listing()

    def _on_library_changed(self) -> None:
        if self._initializing or self._collection_source.currentData() != "library":
            return
        library_id = self._library.currentData()
        if library_id:
            if self._library_manifest_request is not None:
                self._cancel_library_discovery(manifest_only=True)
            self.prepare_library_collections(str(library_id))

    def _begin_library_listing(self) -> None:
        if self._library_picker is None or self._library_listing_request is not None:
            return
        self._error.setText("Loading connected libraries…")
        self._library_listing_request = self._library_picker.begin_library_listing(
            on_complete=self._on_libraries_loaded,
            on_error=self._on_library_error,
        )
        if self._library_picker.active_request_id != self._library_listing_request:
            self._library_listing_request = None

    def _on_libraries_loaded(self, result) -> None:
        self._library_listing_request = None
        self._library.blockSignals(True)
        self._library.clear()
        records = result if isinstance(result, list) else []
        for record in records:
            library_id = str(getattr(record, "stable_id", ""))
            if not library_id:
                continue
            self._library_records[library_id] = record
            self._library.addItem(
                str(getattr(record, "display_name", None) or library_id), library_id
            )
        target = self._target_library_id or self._library.currentData()
        if target:
            self._select_data(self._library, str(target))
        self._library.blockSignals(False)
        if self._library.currentData():
            self._on_library_changed()
        else:
            self._error.setText("No connected collection libraries are available.")

    def prepare_library_collections(self, library_id: str) -> int:
        """Discover collections through the cancellable worker-backed picker."""
        if self._library_picker is None:
            raise ValueError("library_invalid: no connected library service configured")
        self._error.setText("Loading connected library collections…")
        request_id = self._library_picker.begin_manifest_listing(
            library_id,
            on_complete=self._on_library_collections_loaded,
            on_error=lambda error: self._on_library_error(error),
        )
        self._library_manifest_request = (
            request_id
            if self._library_picker.active_request_id == request_id
            else None
        )
        return request_id

    def _on_library_collections_loaded(self, result) -> None:
        self._library_manifest_request = None
        self._replace_library_selections(result)
        if not self._library_collection_stale:
            self._error.clear()

    def _on_library_error(self, error) -> None:
        self._library_listing_request = None
        self._library_manifest_request = None
        self._error.setText(f"Library discovery failed: {error}")

    def cancel_library_preparation(self, request_id: int) -> None:
        if self._library_picker is not None:
            self._library_picker.cancel(request_id)
        if request_id == self._library_manifest_request:
            self._library_manifest_request = None

    def _cancel_library_discovery(self, manifest_only: bool = False) -> None:
        if self._library_picker is None:
            self._library_listing_request = None
            self._library_manifest_request = None
            return
        if manifest_only:
            if self._library_manifest_request is not None:
                self._library_picker.cancel(self._library_manifest_request)
                self._library_manifest_request = None
            return
        self._library_picker.cancel_active()
        self._library_listing_request = None
        self._library_manifest_request = None

    def reject(self) -> None:
        """Invalidate discovery before Qt destroys the editor's callbacks."""
        self._cancel_library_discovery()
        super().reject()

    def _replace_library_selections(self, result) -> None:
        current = self.library_selection()
        current_identity = self._selection_identity(current)
        previous_identity = current_identity
        # The constructor may have temporarily selected the first preloaded row;
        # an edited configuration's persisted identity takes precedence once.
        if self._target_collection_identity is not None and (
            current_identity != self._target_collection_identity
        ):
            previous_identity = self._target_collection_identity
        self._library_collection.clear()
        self._library_collection.setCurrentIndex(-1)
        selections = result if isinstance(result, list) else [result]
        for item in selections:
            self._library_collection.addItem(
                str(item.get("name") or item.get("path") or "Library collection"), item
            )
        if previous_identity is not None:
            self._library_collection.setCurrentIndex(-1)
        if previous_identity is not None:
            for index in range(self._library_collection.count()):
                selection = self._library_collection.itemData(index)
                if self._selection_identity(selection) == previous_identity:
                    self._library_collection.setCurrentIndex(index)
                    self._target_collection_identity = None
                    self._library_collection_stale = False
                    break
        if (
            self._library_collection.currentIndex() < 0
            and self._library_collection.count()
            and previous_identity is None
        ):
            self._library_collection.setCurrentIndex(0)
        if previous_identity is not None and self._library_collection.currentIndex() < 0:
            self._library_collection_stale = True
            self._error.setText(
                "The saved library collection is unavailable or stale. "
                "Select a valid collection before saving."
            )
        elif self._library_collection.currentIndex() >= 0:
            self._populate_library_environment(self.library_selection() or {})

    @staticmethod
    def _selection_identity(selection: object) -> tuple[str, str, str, object] | None:
        if not isinstance(selection, dict):
            return None
        library_id = selection.get("library_id")
        manifest_id = selection.get("manifest_id")
        path = selection.get("path")
        if not library_id or not manifest_id or not path:
            return None
        return (str(library_id), str(manifest_id), str(path), selection.get("index"))

    def _on_library_collection_changed(self) -> None:
        if self._collection_source.currentData() != "library":
            return
        selection = self.library_selection()
        self._populate_library_environment(selection or {})

    def _on_library_profile_changed(self) -> None:
        if self._collection_source.currentData() == "library":
            selected = self._library_profile.currentData()
            selection = self.library_selection()
            profiles = selection.get("manifest_profiles", {}) if selection else {}
            if selected and isinstance(profiles, dict) and selected in profiles:
                self._library_overlay["active_profile"] = selected
                if selection is not None:
                    selection_overlay = selection.get("overlay")
                    if isinstance(selection_overlay, dict):
                        selection_overlay["active_profile"] = selected
            self._populate_library_environment(
                self.library_selection() or {}, preserve_values=True
            )

    def _library_variables_widget_visible(self, visible: bool) -> None:
        for index in range(self._library_variables.rowCount()):
            label = self._library_variables.itemAt(index, QFormLayout.ItemRole.LabelRole)
            field = self._library_variables.itemAt(index, QFormLayout.ItemRole.FieldRole)
            label_widget = label.widget() if label else None
            field_widget = field.widget() if field else None
            if label_widget is not None:
                label_widget.setVisible(visible)
            if field_widget is not None:
                field_widget.setVisible(visible)

    @staticmethod
    def _variable_value(value, variable_type: str):
        if variable_type == "string":
            return value
        try:
            if variable_type == "integer":
                return int(value)
            if variable_type == "number":
                return float(value)
            if variable_type == "boolean":
                lowered = value.strip().lower()
                if lowered in {"true", "false"}:
                    return lowered == "true"
                raise ValueError("expected true or false")
            if variable_type in {"array", "object"}:
                return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("Invalid value for library variable") from error
        return value

    def _populate_library_environment(self, selection, preserve_values=False) -> None:
        variables = selection.get("manifest_variables", [])
        profiles = selection.get("manifest_profiles", {})
        overlay = selection.get("overlay", {})
        if isinstance(overlay, dict):
            self._library_overlay = dict(overlay)
        else:
            self._library_overlay = {}
        old_values = {
            name: field.text() for name, field in self._library_variable_fields.items()
        } if preserve_values else {}
        self._library_variable_fields.clear()
        self._library_variable_types.clear()
        self._library_secret_names.clear()
        while self._library_variables.rowCount():
            self._library_variables.removeRow(0)
        self._library_profile.blockSignals(True)
        self._library_profile.clear()
        if isinstance(profiles, dict):
            for profile_id in profiles:
                self._library_profile.addItem(str(profile_id), str(profile_id))
        active_profile = self._library_overlay.get("active_profile")
        if active_profile and self._library_profile.findData(active_profile) >= 0:
            self._select_data(self._library_profile, active_profile)
            self._library_profile_unavailable = False
        elif active_profile:
            self._library_profile.addItem(
                f"{active_profile} (unavailable)", str(active_profile)
            )
            self._library_profile.setCurrentIndex(self._library_profile.count() - 1)
            self._library_profile_unavailable = True
            self._error.setText(
                f"Saved library profile '{active_profile}' is unavailable. "
                "Select a valid profile before saving."
            )
        elif self._library_profile.count():
            self._library_profile.setCurrentIndex(0)
            self._library_profile_unavailable = False
        self._library_profile.blockSignals(False)
        selected_profile = (
            profiles.get(self._library_profile.currentData(), {})
            if isinstance(profiles, dict) else {}
        )
        if not isinstance(selected_profile, dict):
            selected_profile = {}
        overrides = self._library_overlay.get("overrides", {})
        secrets = self._library_overlay.get("secrets", {})
        for raw in variables if isinstance(variables, list) else []:
            if not isinstance(raw, dict) or not raw.get("name"):
                continue
            name = str(raw["name"])
            variable_type = str(raw.get("type", "string"))
            default = raw.get("default", raw.get("default_value"))
            value = selected_profile.get(name, default)
            if name in overrides:
                value = overrides[name]
            if raw.get("secret") and name in secrets:
                value = secrets[name]
            field = QLineEdit()
            field.setText(
                old_values.get(name, "")
                if name in old_values else "" if value is None else str(value)
            )
            if raw.get("secret"):
                field.setEchoMode(QLineEdit.EchoMode.Password)
                field.setPlaceholderText("Secret value")
                self._library_secret_names.add(name)
            label_value = "<hidden>" if raw.get("secret") else repr(value)
            label = f"{name} (default/profile: {label_value})"
            if raw.get("description"):
                field.setToolTip(str(raw["description"]))
            self._library_variables.addRow(label, field)
            self._library_variable_fields[name] = field
            self._library_variable_types[name] = variable_type
        self._library_variables_widget_visible(
            self._server_type.currentData() == "local"
            and self._collection_source.currentData() == "library"
        )

    def library_selection(self) -> dict[str, object] | None:
        if self._collection_source.currentData() != "library":
            return None
        selection = self._library_collection.currentData()
        return dict(selection) if isinstance(selection, dict) else None

    def library_handoff(self) -> object:
        selection = self.library_selection()
        handoff = self._library_picker.selected_collection if self._library_picker else None
        if selection is None:
            return handoff
        overlay = self._library_overlay_candidate(selection)
        result = dict(selection)
        result["overlay"] = overlay
        if isinstance(handoff, dict) and not isinstance(handoff, list):
            result.update({key: value for key, value in handoff.items() if key not in result})
        return result

    def _library_overlay_candidate(self, selection: dict[str, object]) -> dict[str, Any]:
        """Parse and validate the values currently displayed by the editor."""
        overlay = dict(self._library_overlay)
        overlay["library_id"] = selection.get("library_id")
        overlay["active_profile"] = self._library_profile.currentData()
        overrides = {}
        secrets = {}
        profiles = selection.get("manifest_profiles", {})
        profile = (
            profiles.get(self._library_profile.currentData(), {})
            if isinstance(profiles, dict) else {}
        )
        for name, field in self._library_variable_fields.items():
            text = field.text()
            if not text and name not in self._library_overlay.get("secrets", {}):
                continue
            value = self._variable_value(text, self._library_variable_types[name])
            if name in self._library_secret_names:
                secrets[name] = value
            elif not isinstance(profile, dict) or value != profile.get(name):
                overrides[name] = value
        overlay["overrides"] = overrides
        overlay["secrets"] = secrets
        from pypost.core.library_runtime_resolver import LibraryRuntimeResolver

        defaults = {}
        declarations = {}
        raw_variables = selection.get("manifest_variables", [])
        if not isinstance(raw_variables, list):
            raw_variables = []
        for raw in raw_variables:
            if not isinstance(raw, dict) or not raw.get("name"):
                continue
            name = str(raw["name"])
            declarations[name] = {
                "type": str(raw.get("type", "string")),
                "required": bool(raw.get("required", False)),
            }
            if raw.get("default", raw.get("default_value")) is not None:
                defaults[name] = raw.get("default", raw.get("default_value"))
        profile_values = profile if isinstance(profile, dict) else {}
        LibraryRuntimeResolver().prepare_environment(
            defaults=defaults,
            profile=profile_values,
            overrides=overrides,
            secrets=secrets,
            declarations=declarations,
        )
        return overlay

    def _parse_headers(self) -> dict[str, str]:
        return self._headers_table.get_data()

    @staticmethod
    def _select_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _accept_if_complete(self) -> None:
        if not self._host.text().strip():
            self._error.setText("Host is required.")
            logger.debug("MCP server editor rejected save: host is required")
            return

        is_proxy = self._server_type.currentData() == "proxy"
        is_library = (
            not is_proxy
            and self._collection_source.currentData() == "library"
        )
        if is_library and self._library_collection_stale:
            self._error.setText(
                "The saved library collection is unavailable or stale. "
                "Select a valid collection before saving."
            )
            return
        if is_library:
            selection = self.library_selection()
            profiles = selection.get("manifest_profiles", {}) if selection else {}
            if isinstance(profiles, dict) and profiles:
                profile_id = self._library_profile.currentData()
                if profile_id not in profiles:
                    self._error.setText(
                        "The saved library profile is unavailable. "
                        "Select a valid profile before saving."
                    )
                    return
                self._library_profile_unavailable = False
        if is_proxy:
            if not self._upstream_url.text().strip():
                self._error.setText("Upstream URL is required for proxy servers.")
                logger.debug("MCP server editor rejected save: upstream URL is required")
                return
            if self._headers_table.has_structural_errors():
                err_msg = (self._headers_table.get_validation_errors() or ["syntax error"])[0]
                self._error.setText(f"Custom headers error: {err_msg}")
                logger.warning(
                    "MCP server editor rejected save due to custom headers error: %s",
                    err_msg,
                )
                return
        elif self._environment.currentData() is None or (
            self._collection_source.currentData() == "workspace"
            and self._collection.currentData() is None
        ) or (
            self._collection_source.currentData() == "library"
            and self._library_collection.currentData() is None
        ):
            self._error.setText("Collection and environment are required.")
            logger.debug("MCP server editor rejected save: collection and environment are required")
            return

        if not is_proxy and self._collection_source.currentData() == "library":
            try:
                self._library_overlay_candidate(self.library_selection() or {})
            except ValueError as error:
                self._error.setText(str(error))
                logger.debug("MCP server editor rejected invalid library variable draft")
                return

        logger.debug("MCP server editor accepted configuration for server id=%s", self._id)
        self.accept()

    def configuration(self) -> McpServerConfiguration:
        is_proxy = self._server_type.currentData() == "proxy"
        if is_proxy:
            transport_raw = str(self._upstream_transport.currentData() or "streamable_http")
            upstream_transport: Literal["streamable_http", "sse"] = (
                "sse" if transport_raw == "sse" else "streamable_http"
            )
            return McpServerConfiguration(
                id=self._id,
                name=self._name.text().strip() or None,
                host=self._host.text().strip(),
                port=self._port.value(),
                server_type="proxy",
                upstream_url=self._upstream_url.text().strip(),
                upstream_transport=upstream_transport,
                headers=self._headers_table.get_data(),
                environment_id=str(self._environment.currentData() or ""),
                enabled=self._enabled,
            )
        if self._collection_source.currentData() == "library":
            selection = dict(self._library_collection.currentData() or {})
            return McpServerConfiguration(
                id=self._id,
                name=self._name.text().strip() or None,
                host=self._host.text().strip(),
                port=self._port.value(),
                server_type="local",
                library_id=str(selection.get("library_id")),
                manifest_id=str(selection.get("manifest_id")),
                library_collection_path=str(selection.get("path")),
                library_collection_index=selection.get("index"),
                environment_id=str(self._environment.currentData()),
                enabled=self._enabled,
            )
        return McpServerConfiguration(
            id=self._id,
            name=self._name.text().strip() or None,
            host=self._host.text().strip(),
            port=self._port.value(),
            server_type="local",
            collection_id=str(self._collection.currentData()),
            environment_id=str(self._environment.currentData()),
            enabled=self._enabled,
        )
