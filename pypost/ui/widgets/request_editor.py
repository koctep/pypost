import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QTableWidgetItem,
    QHeaderView,
    QPlainTextEdit,
    QTabWidget,
    QCheckBox,
    QToolButton,
    QMenu,
)
from PySide6.QtGui import QShortcut, QKeySequence, QAction
from PySide6.QtCore import Signal
from pypost.models.models import RequestData
from pypost.ui.widgets.json_highlighter import JsonHighlighter
from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.variable_aware_widgets import (
    VariableAwareLineEdit,
    VariableAwareTableWidget,
)
from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


class RequestWidget(QWidget):
    send_requested = Signal(RequestData)
    save_requested = Signal(RequestData)
    save_as_requested = Signal(RequestData)

    def __init__(self, request_data: RequestData = None, metrics: MetricsManager | None = None):
        super().__init__()
        self._loading = False
        self._metrics = metrics
        self.request_data = request_data or RequestData()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        url_layout = QHBoxLayout()

        self.method_combo = QComboBox()
        self.method_combo.addItems(
            ["GET", "POST", "PUT", "DELETE", "PATCH", "MCP"]
        )
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
        self.detail_tabs.addTab(self.body_edit, "Body")
        self._on_method_changed(self.method_combo.currentText())

        self.script_edit = QPlainTextEdit()
        script_hint = (
            "# Python script to run after request\n"
            "# Available: pypost, request, response\n"
            "# Example: pypost.env.set('token', response.json()['token'])"
        )
        self.script_edit.setPlaceholderText(script_hint)
        self.detail_tabs.addTab(self.script_edit, "Script")

        layout.addWidget(self.detail_tabs)

        self.load_data()
        self._setup_shortcuts()

    def set_variables(self, variables: dict):
        self.url_input.set_variables(variables)
        self.params_table.set_variables(variables)
        self.headers_table.set_variables(variables)
        if hasattr(self.body_edit, 'set_variables'):
            self.body_edit.set_variables(variables)

    def _on_method_changed(self, method: str):
        if method == "MCP":
            self.body_edit.setPlaceholderText(
                "Empty = list tools. JSON {name, arguments} = call tool."
            )
        else:
            self.body_edit.setPlaceholderText("")
        if not self._loading and method in ("POST", "PUT"):
            self.detail_tabs.setCurrentWidget(self.body_edit)
            if self._metrics:
                self._metrics.track_gui_method_body_autoswitch(method)

    def load_data(self):
        self._loading = True
        try:
            self.url_input.setText(self.request_data.url)
            self.method_combo.setCurrentText(self.request_data.method)
            self._on_method_changed(self.request_data.method)
            self.params_table.set_data(self.request_data.params)
            self.headers_table.set_data(self.request_data.headers)
            self.body_edit.setPlainText(self.request_data.body)
            self.script_edit.setPlainText(self.request_data.post_script)
            self.mcp_check.setChecked(self.request_data.expose_as_mcp)
        finally:
            self._loading = False

    def update_request_data(self):
        self.request_data.url = self.url_input.text()
        self.request_data.method = self.method_combo.currentText()
        self.request_data.params = self.params_table.get_data()
        self.request_data.headers = self.headers_table.get_data()
        self.request_data.body = self.body_edit.toPlainText()
        self.request_data.post_script = self.script_edit.toPlainText()
        self.request_data.expose_as_mcp = self.mcp_check.isChecked()

    def get_request_data_from_ui(self) -> RequestData:
        request_data = self.request_data.model_copy(deep=True)
        request_data.url = self.url_input.text()
        request_data.method = self.method_combo.currentText()
        request_data.params = self.params_table.get_data()
        request_data.headers = self.headers_table.get_data()
        request_data.body = self.body_edit.toPlainText()
        request_data.post_script = self.script_edit.toPlainText()
        request_data.expose_as_mcp = self.mcp_check.isChecked()
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
