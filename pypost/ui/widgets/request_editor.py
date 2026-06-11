import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.mcp_tool_contract import (
    build_mcp_tool_contract_preview,
    format_mcp_tool_contract_preview,
)
from pypost.core.metrics import MetricsManager
from pypost.core.request_sync import copy_request_for_isolated_tab
from pypost.core.template_service import TemplateService
from pypost.models.models import McpToolParam, RequestData
from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.json_highlighter import JsonHighlighter
from pypost.ui.widgets.mixins import VariableHoverHelper
from pypost.ui.widgets.variable_aware_widgets import VariableAwareLineEdit, VariableAwareTableWidget

logger = logging.getLogger(__name__)

_BODY_FORMAT_OPTIONS = (BodyFormat.JSON, BodyFormat.YAML, BodyFormat.XML)


def body_type_to_body_format(body_type: str) -> BodyFormat:
    try:
        fmt = BodyFormat(body_type.lower())
    except ValueError:
        return BodyFormat.JSON
    if fmt in _BODY_FORMAT_OPTIONS:
        return fmt
    return BodyFormat.JSON


def body_format_to_body_type(body_format: BodyFormat) -> str:
    return body_format.value


class RequestWidget(QWidget):
    send_requested = Signal(RequestData)
    save_requested = Signal(RequestData)
    save_as_requested = Signal(RequestData)
    copy_curl_requested = Signal(RequestData)

    def __init__(self, request_data: RequestData = None, metrics: MetricsManager | None = None):
        super().__init__()
        self._loading = False
        self._metrics = metrics
        self._template_service: TemplateService | None = None
        self._hidden_keys: set[str] = set()
        VariableHoverHelper.set_metrics(metrics)
        self.request_data = request_data or RequestData()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        url_layout = QHBoxLayout()

        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "MCP"])
        self.method_combo.setCurrentText(self.request_data.method)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)

        self.url_input = VariableAwareLineEdit(self.request_data.url)
        self.url_input.setPlaceholderText("Enter request URL")

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)

        self.actions_btn = QToolButton()
        self.actions_btn.setText("Actions")
        self.actions_btn.setPopupMode(QToolButton.InstantPopup)

        self.actions_menu = QMenu(self.actions_btn)
        self.save_as_action = QAction("Save As...", self)
        self.save_as_action.triggered.connect(self.handle_save_as_menu_action)
        self.actions_menu.addAction(self.save_as_action)
        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.handle_save_menu_action)
        self.actions_menu.addAction(self.save_action)
        self.copy_curl_action = QAction("Copy cURL", self)
        self.copy_curl_action.triggered.connect(self.handle_copy_curl_menu_action)
        self.actions_menu.addAction(self.copy_curl_action)
        self.actions_btn.setMenu(self.actions_menu)

        url_layout.addWidget(self.method_combo)
        url_layout.addWidget(self.url_input)

        self.mcp_check = QCheckBox("MCP Tool")
        self.mcp_check.setToolTip("Expose as MCP Tool")
        url_layout.addWidget(self.mcp_check)

        url_layout.addWidget(self.send_btn)
        url_layout.addWidget(self.actions_btn)

        layout.addLayout(url_layout)

        self.detail_tabs = QTabWidget()

        self.params_table = KeyValueTable()
        self.detail_tabs.addTab(self.params_table, "Params")

        self.headers_table = KeyValueTable()
        self.detail_tabs.addTab(self.headers_table, "Headers")

        self.body_edit = CodeEditor()
        self.json_highlighter = JsonHighlighter(self.body_edit.document())

        self.body_format_combo = QComboBox()
        for fmt in _BODY_FORMAT_OPTIONS:
            self.body_format_combo.addItem(fmt.name, fmt)
        self.body_format_combo.currentIndexChanged.connect(self._on_body_format_changed)

        body_tab = QWidget()
        body_tab_layout = QVBoxLayout(body_tab)
        body_tab_layout.setContentsMargins(0, 0, 0, 0)
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        format_row.addWidget(self.body_format_combo)
        self.yaml_as_json_check = QCheckBox("YAML as JSON")
        self.yaml_as_json_check.setToolTip(
            "When enabled, YAML body is converted to JSON at send time; "
            "pasted JSON is converted to YAML in the editor."
        )
        self.yaml_as_json_check.toggled.connect(self._on_yaml_as_json_toggled)
        format_row.addWidget(self.yaml_as_json_check)
        format_row.addStretch()
        body_tab_layout.addLayout(format_row)
        body_tab_layout.addWidget(self.body_edit)
        self.body_tab = body_tab
        self.detail_tabs.addTab(self.body_tab, "Body")
        self._on_method_changed(self.method_combo.currentText())

        self.script_edit = QPlainTextEdit()
        script_hint = (
            "# Python script to run after request\n"
            "# Available: pypost, request, response\n"
            "# Example: pypost.env.set('token', response.json()['token'])"
        )
        self.script_edit.setPlaceholderText(script_hint)
        self.detail_tabs.addTab(self.script_edit, "Script")

        self.mcp_description_edit = QPlainTextEdit()
        self.mcp_description_edit.setPlaceholderText(
            "Description shown to AI agents when this request is an MCP tool"
        )
        self.mcp_params_table = McpParamsTable()
        mcp_tab = QWidget()
        mcp_tab_layout = QVBoxLayout(mcp_tab)
        mcp_tab_layout.setContentsMargins(0, 0, 0, 0)
        mcp_tab_layout.addWidget(QLabel("Tool description"))
        mcp_tab_layout.addWidget(self.mcp_description_edit)
        mcp_tab_layout.addWidget(QLabel("Parameters"))
        mcp_tab_layout.addWidget(self.mcp_params_table)
        mcp_tab_layout.addWidget(QLabel("Agent preview (list_tools)"))
        self.mcp_preview_edit = QPlainTextEdit()
        self.mcp_preview_edit.setReadOnly(True)
        self.mcp_preview_edit.setPlaceholderText(
            "Enable MCP Tool to preview the agent-visible contract."
        )
        preview_font = QFont(self.mcp_preview_edit.font())
        if preview_font.family():
            preview_font.setStyleHint(QFont.Monospace)
        else:
            preview_font.setFamily("monospace")
        self.mcp_preview_edit.setFont(preview_font)
        mcp_tab_layout.addWidget(self.mcp_preview_edit)
        self.detail_tabs.addTab(mcp_tab, "MCP")

        layout.addWidget(self.detail_tabs)

        self.load_data()
        self._setup_shortcuts()
        self._wire_mcp_preview_refresh()

    def set_variables(self, variables: dict):
        self.url_input.set_variables(variables)
        self.params_table.set_variables(variables)
        self.headers_table.set_variables(variables)
        if hasattr(self.body_edit, "set_variables"):
            self.body_edit.set_variables(variables)

    def set_template_service(self, template_service: TemplateService | None) -> None:
        self._template_service = template_service
        self._refresh_mcp_preview()

    def set_hidden_keys(self, hidden_keys: set):
        self._hidden_keys = set(hidden_keys)
        self.url_input.set_hidden_keys(hidden_keys)
        self.params_table.set_hidden_keys(hidden_keys)
        self.headers_table.set_hidden_keys(hidden_keys)
        if hasattr(self.body_edit, "set_hidden_keys"):
            self.body_edit.set_hidden_keys(hidden_keys)
        self._refresh_mcp_preview()

    def _on_method_changed(self, method: str):
        if method == "MCP":
            self.body_edit.setPlaceholderText(
                "Empty = list tools. JSON {name, arguments} = call tool."
            )
        else:
            self.body_edit.setPlaceholderText("")
        if not self._loading and method in ("POST", "PUT"):
            self.detail_tabs.setCurrentWidget(self.body_tab)
            if self._metrics:
                self._metrics.track_gui_method_body_autoswitch(method)

    def _set_body_format_combo(self, body_format: BodyFormat) -> None:
        index = self.body_format_combo.findData(body_format)
        if index >= 0:
            self.body_format_combo.setCurrentIndex(index)

    def _on_body_format_changed(self, _index: int) -> None:
        body_format = self.body_format_combo.currentData()
        if body_format is None:
            return
        self.body_edit.set_body_format(body_format)
        self.yaml_as_json_check.setEnabled(body_format == BodyFormat.YAML)
        self._sync_yaml_as_json_to_editor()

    def _on_yaml_as_json_toggled(self, _checked: bool) -> None:
        self._sync_yaml_as_json_to_editor()

    def _sync_yaml_as_json_to_editor(self) -> None:
        body_format = self.body_format_combo.currentData()
        enabled = (
            body_format == BodyFormat.YAML and self.yaml_as_json_check.isChecked()
        )
        self.body_edit.set_yaml_as_json(enabled)

    def _update_yaml_as_json_enabled(self) -> None:
        body_format = self.body_format_combo.currentData()
        self.yaml_as_json_check.setEnabled(body_format == BodyFormat.YAML)

    def load_data(self):
        self._loading = True
        try:
            self.url_input.setText(self.request_data.url)
            self.method_combo.setCurrentText(self.request_data.method)
            self._on_method_changed(self.request_data.method)
            self.params_table.set_data(self.request_data.params)
            self.headers_table.set_data(self.request_data.headers)
            self.body_edit.setPlainText(self.request_data.body)
            body_format = body_type_to_body_format(self.request_data.body_type)
            self._set_body_format_combo(body_format)
            self.body_edit.set_body_format(body_format)
            self.yaml_as_json_check.setChecked(self.request_data.yaml_as_json)
            self._update_yaml_as_json_enabled()
            self._sync_yaml_as_json_to_editor()
            self.script_edit.setPlainText(self.request_data.post_script)
            self.mcp_check.setChecked(self.request_data.expose_as_mcp)
            self.mcp_description_edit.setPlainText(self.request_data.mcp_description)
            self.mcp_params_table.set_data(self.request_data.mcp_params)
            self._refresh_mcp_preview()
        finally:
            self._loading = False

    def _wire_mcp_preview_refresh(self) -> None:
        self.mcp_check.toggled.connect(self._on_mcp_preview_source_changed)
        self.mcp_description_edit.textChanged.connect(self._on_mcp_preview_source_changed)
        self.mcp_params_table.itemChanged.connect(self._on_mcp_preview_source_changed)
        self.url_input.textChanged.connect(self._on_mcp_preview_source_changed)
        self.params_table.itemChanged.connect(self._on_mcp_preview_source_changed)
        self.headers_table.itemChanged.connect(self._on_mcp_preview_source_changed)
        self.body_edit.textChanged.connect(self._on_mcp_preview_source_changed)

    def _on_mcp_preview_source_changed(self, *_args) -> None:
        if self._loading:
            return
        self._refresh_mcp_preview()

    def _refresh_mcp_preview(self) -> None:
        if not self.mcp_check.isChecked():
            self.mcp_preview_edit.setPlainText(
                "This request is not exposed as an MCP tool."
            )
            return

        preview = build_mcp_tool_contract_preview(
            self.get_request_data_from_ui(),
            hidden_keys=self._hidden_keys,
            template_service=self._template_service,
        )
        if preview is None:
            self.mcp_preview_edit.setPlainText(
                "This request is not exposed as an MCP tool."
            )
            return
        self.mcp_preview_edit.setPlainText(format_mcp_tool_contract_preview(preview))

    def _body_type_from_ui(self) -> str:
        body_format = self.body_format_combo.currentData()
        if body_format is None:
            return BodyFormat.JSON.value
        return body_format_to_body_type(body_format)

    def update_request_data(self):
        self.request_data.url = self.url_input.text()
        self.request_data.method = self.method_combo.currentText()
        self.request_data.params = self.params_table.get_data()
        self.request_data.headers = self.headers_table.get_data()
        self.request_data.body = self.body_edit.toPlainText()
        self.request_data.body_type = self._body_type_from_ui()
        self.request_data.yaml_as_json = self.yaml_as_json_check.isChecked()
        self.request_data.post_script = self.script_edit.toPlainText()
        self.request_data.expose_as_mcp = self.mcp_check.isChecked()
        self.request_data.mcp_description = self.mcp_description_edit.toPlainText()
        self.request_data.mcp_params = self.mcp_params_table.get_data()

    def get_request_data_from_ui(self) -> RequestData:
        request_data = copy_request_for_isolated_tab(self.request_data)
        request_data.url = self.url_input.text()
        request_data.method = self.method_combo.currentText()
        request_data.params = self.params_table.get_data()
        request_data.headers = self.headers_table.get_data()
        request_data.body = self.body_edit.toPlainText()
        request_data.body_type = self._body_type_from_ui()
        request_data.yaml_as_json = self.yaml_as_json_check.isChecked()
        request_data.post_script = self.script_edit.toPlainText()
        request_data.expose_as_mcp = self.mcp_check.isChecked()
        request_data.mcp_description = self.mcp_description_edit.toPlainText()
        request_data.mcp_params = self.mcp_params_table.get_data()
        return request_data

    def on_send(self):
        if self._metrics:
            self._metrics.track_gui_send_click()
        current_request = self.get_request_data_from_ui()
        self.request_data = current_request
        self.send_requested.emit(current_request)

    def on_save(self, source: str = "unknown"):
        logger.info("save_action_triggered source=%s", source)
        if self._metrics:
            self._metrics.track_gui_save_action(source)
        current_request = self.get_request_data_from_ui()
        self.request_data = current_request
        self.save_requested.emit(current_request)

    def _setup_shortcuts(self):
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.handle_save_request_shortcut)
        save_as_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        save_as_shortcut.activated.connect(self.handle_save_as_shortcut)

    def handle_save_request_shortcut(self):
        self.on_save("shortcut")

    def handle_save_menu_action(self):
        self.on_save("menu")

    def handle_save_as_shortcut(self):
        self.on_save_as("shortcut")

    def on_save_as(self, source: str = "unknown"):
        logger.info("save_as_action_triggered source=%s", source)
        if self._metrics:
            self._metrics.track_gui_save_as_action(source)
        current_request = self.get_request_data_from_ui()
        self.save_as_requested.emit(current_request)

    def handle_save_as_menu_action(self):
        self.on_save_as("menu")

    def handle_copy_curl_menu_action(self):
        logger.info("copy_curl_action_triggered")
        if self._metrics:
            self._metrics.track_gui_copy_curl_action()
        current_request = self.get_request_data_from_ui()
        self.copy_curl_requested.emit(current_request)


class McpParamsTable(QTableWidget):
    _TYPE_OPTIONS = ("string", "integer", "number", "boolean")

    def __init__(self):
        super().__init__(0, 4)
        self.setHorizontalHeaderLabels(["Name", "Type", "Description", "Required"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.itemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.row() == self.rowCount() - 1 and item.column() == 0 and item.text():
            self.setRowCount(self.rowCount() + 1)

    def set_data(self, params: dict[str, McpToolParam]) -> None:
        self.blockSignals(True)
        try:
            self.setRowCount(len(params) + 1)
            for row, (name, spec) in enumerate(sorted(params.items())):
                self._set_row(row, name, spec)
            self._set_row(self.rowCount() - 1, "", McpToolParam())
        finally:
            self.blockSignals(False)

    def _set_row(self, row: int, name: str, spec: McpToolParam) -> None:
        self.setItem(row, 0, QTableWidgetItem(name))
        type_combo = QComboBox()
        type_combo.addItems(list(self._TYPE_OPTIONS))
        idx = type_combo.findText(spec.type)
        if idx >= 0:
            type_combo.setCurrentIndex(idx)
        self.setCellWidget(row, 1, type_combo)
        self.setItem(row, 2, QTableWidgetItem(spec.description))
        required_item = QTableWidgetItem()
        required_item.setFlags(
            Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        )
        required_item.setCheckState(
            Qt.Checked if spec.required else Qt.Unchecked
        )
        self.setItem(row, 3, required_item)

    def get_data(self) -> dict[str, McpToolParam]:
        params: dict[str, McpToolParam] = {}
        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            if not name_item or not name_item.text().strip():
                continue
            name = name_item.text().strip()
            type_combo = self.cellWidget(row, 1)
            param_type = (
                type_combo.currentText()
                if isinstance(type_combo, QComboBox)
                else "string"
            )
            desc_item = self.item(row, 2)
            description = desc_item.text() if desc_item else ""
            required_item = self.item(row, 3)
            required = (
                required_item.checkState() == Qt.Checked
                if required_item
                else True
            )
            params[name] = McpToolParam(
                type=param_type,
                description=description,
                required=required,
            )
        return params


class KeyValueTable(VariableAwareTableWidget):
    def __init__(self):
        super().__init__(1, 2)
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        if item.row() == self.rowCount() - 1:
            if item.text():
                self.setRowCount(self.rowCount() + 1)

    def set_data(self, data: dict):
        self.setRowCount(len(data) + 1)
        for i, (k, v) in enumerate(data.items()):
            self.setItem(i, 0, QTableWidgetItem(k))
            self.setItem(i, 1, QTableWidgetItem(v))

    def get_data(self) -> dict:
        data = {}
        for i in range(self.rowCount()):
            key_item = self.item(i, 0)
            val_item = self.item(i, 1)
            if key_item and key_item.text():
                data[key_item.text()] = val_item.text() if val_item else ""
        return data
