from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QPlainTextEdit, QTabWidget)
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import Signal, Qt
from pypost.models.models import RequestData
from pypost.ui.widgets.json_highlighter import JsonHighlighter
from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.variable_aware_widgets import VariableAwareLineEdit, VariableAwarePlainTextEdit

class RequestWidget(QWidget):
    send_requested = Signal(RequestData)
    save_requested = Signal(RequestData)

    def __init__(self, request_data: RequestData = None):
        super().__init__()
        self.request_data = request_data or RequestData()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # URL Bar
        url_layout = QHBoxLayout()

        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        self.method_combo.setCurrentText(self.request_data.method)

        self.url_input = VariableAwareLineEdit(self.request_data.url)
        self.url_input.setPlaceholderText("Enter request URL")

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.on_save)

        url_layout.addWidget(self.method_combo)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.save_btn)
        url_layout.addWidget(self.send_btn)

        layout.addLayout(url_layout)

        # Tabs for Params, Headers, Body
        self.detail_tabs = QTabWidget()

        # Params
        self.params_table = KeyValueTable()
        self.detail_tabs.addTab(self.params_table, "Params")

        # Headers
        self.headers_table = KeyValueTable()
        self.detail_tabs.addTab(self.headers_table, "Headers")

        # Body
        # We need a CodeEditor that is also VariableAware.
        # Since CodeEditor inherits QPlainTextEdit, we can create a mixin or just use VariableAwarePlainTextEdit logic in CodeEditor.
        # For now, let's mixin VariableAwarePlainTextEdit into CodeEditor or make a new class VariableAwareCodeEditor.
        # Wait, the requirements said replace QPlainTextEdit. CodeEditor was introduced in PYPOST-15.
        # Let's inspect CodeEditor in pypost/ui/widgets/code_editor.py first to decide how to merge.
        # But based on the previous context, CodeEditor was likely just created.
        # I'll use CodeEditor as base but inject VariableAware capabilities.
        # Actually, let's just make CodeEditor inherit from VariableAwarePlainTextEdit instead of QPlainTextEdit if possible.
        # But I don't want to modify CodeEditor directly if I can avoid it or I should modify it.
        # Let's look at CodeEditor content first.
        
        self.body_edit = CodeEditor() 
        self.json_highlighter = JsonHighlighter(self.body_edit.document())
        self.detail_tabs.addTab(self.body_edit, "Body")

        # Post-Script
        self.script_edit = QPlainTextEdit()
        self.script_edit.setPlaceholderText("# Python script to run after request\n# Available: pypost, request, response\n# Example: pypost.env.set('token', response.json()['token'])")
        self.detail_tabs.addTab(self.script_edit, "Script")

        layout.addWidget(self.detail_tabs)

        # Load initial data
        self.load_data()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def set_variables(self, variables: dict):
        """Update environment variables for child widgets."""
        self.url_input.set_variables(variables)
        if hasattr(self.body_edit, 'set_variables'):
            self.body_edit.set_variables(variables)


    def load_data(self):
        self.url_input.setText(self.request_data.url)
        self.method_combo.setCurrentText(self.request_data.method)
        self.params_table.set_data(self.request_data.params)
        self.headers_table.set_data(self.request_data.headers)
        self.body_edit.setPlainText(self.request_data.body)
        self.script_edit.setPlainText(self.request_data.post_script)

    def update_request_data(self):
        self.request_data.url = self.url_input.text()
        self.request_data.method = self.method_combo.currentText()
        self.request_data.params = self.params_table.get_data()
        self.request_data.headers = self.headers_table.get_data()
        self.request_data.body = self.body_edit.toPlainText()
        self.request_data.post_script = self.script_edit.toPlainText()

    def on_send(self):
        self.update_request_data()
        self.send_requested.emit(self.request_data)

    def on_save(self):
        self.update_request_data()
        self.save_requested.emit(self.request_data)

    def _setup_shortcuts(self):
        """Initializes context shortcuts."""
        # Save request (Ctrl+S)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.handle_save_request_shortcut)

    def handle_save_request_shortcut(self):
        """Handler for saving request via shortcut (Ctrl+S)."""
        self.on_save()

class KeyValueTable(QTableWidget):
    def __init__(self):
        super().__init__(1, 2) # Start with 1 empty row
        self.setHorizontalHeaderLabels(["Key", "Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        # Add new row if last row is edited
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
