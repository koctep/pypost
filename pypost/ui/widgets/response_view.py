from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout)
from pypost.models.response import ResponseData
from pypost.ui.widgets.json_highlighter import JsonHighlighter
import json

class ResponseView(QWidget):
    def __init__(self, indent_size=2):
        super().__init__()
        self.indent_size = indent_size
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
        self.json_highlighter = JsonHighlighter(self.body_view.document())
        layout.addWidget(self.body_view)

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
