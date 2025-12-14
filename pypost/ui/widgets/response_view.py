from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, QMenu)
from PySide6.QtCore import Qt, Signal
from pypost.models.response import ResponseData
from pypost.ui.widgets.json_highlighter import JsonHighlighter
import json
from functools import partial

class ResponseView(QWidget):
    variable_set_requested = Signal(object, str)

    def __init__(self, indent_size=2):
        super().__init__()
        self.indent_size = indent_size
        self.current_env_keys = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Status Bar
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: -")
        self.time_label = QLabel("Time: -")
        self.size_label = QLabel("Size: -")

        self.status_layout.addWidget(self.status_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.time_label)
        self.status_layout.addSpacing(20)
        self.status_layout.addWidget(self.size_label)
        self.status_layout.addStretch()

        layout.addLayout(self.status_layout)

        # Body View
        self.body_view = QTextEdit()
        self.body_view.setReadOnly(True)
        self.body_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.body_view.customContextMenuRequested.connect(self.show_context_menu)
        self.json_highlighter = JsonHighlighter(self.body_view.document())
        layout.addWidget(self.body_view)

    def set_env_keys(self, keys):
        self.current_env_keys = sorted(keys) if keys is not None else None

    def show_context_menu(self, pos):
        cursor = self.body_view.textCursor()
        selected_text = cursor.selectedText()
        clean_text = selected_text.strip()

        # Create menu manually to control order
        menu = QMenu(self)

        # 1. Set Variable
        if clean_text and self.current_env_keys is not None:
            env_menu = menu.addMenu("Set Variable")
            
            # Existing variables
            if self.current_env_keys:
                for key in self.current_env_keys:
                    action = env_menu.addAction(key)
                    # Use partial to safely bind loop variable. triggered emits (checked)
                    action.triggered.connect(partial(self.emit_variable_set, key, clean_text))
                env_menu.addSeparator()
            
            # New variable option
            new_var_action = env_menu.addAction("New Variable...")
            new_var_action.triggered.connect(lambda checked=False, v=clean_text: self.variable_set_requested.emit(None, v))

        # 2. Copy
        if selected_text:
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(self.body_view.copy)
        
        if not menu.isEmpty():
             menu.addSeparator()

        select_all = menu.addAction("Select All")
        select_all.triggered.connect(self.body_view.selectAll)

        menu.exec(self.body_view.mapToGlobal(pos))

    def emit_variable_set(self, key, value, checked=False):
        self.variable_set_requested.emit(key, value)

    def set_indent_size(self, size: int):
        self.indent_size = size
        # Refresh current view if it contains JSON
        if self.body_view.toPlainText():
             try:
                # We need to re-parse original body if possible, 
                # but we only store displayed text here. 
                # For now, let's try to re-parse the displayed text.
                text = self.body_view.toPlainText()
                parsed = json.loads(text)
                pretty_json = json.dumps(parsed, indent=self.indent_size)
                self.body_view.setText(pretty_json)
             except:
                pass

    def display_response(self, response: ResponseData):
        self.status_label.setText(f"Status: {response.status_code}")
        self.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        self.size_label.setText(f"Size: {response.size} bytes")

        # Try pretty print JSON
        try:
            parsed = json.loads(response.body)
            pretty_json = json.dumps(parsed, indent=self.indent_size)
            self.body_view.setText(pretty_json)
        except:
            self.body_view.setText(response.body)
