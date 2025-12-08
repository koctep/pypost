from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout)
from pypost.models.response import ResponseData
import json

class ResponseView(QWidget):
    def __init__(self):
        super().__init__()
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
        layout.addWidget(self.body_view)

    def display_response(self, response: ResponseData):
        self.status_label.setText(f"Status: {response.status_code}")
        self.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        self.size_label.setText(f"Size: {response.size} bytes")

        # Try pretty print JSON
        try:
            parsed = json.loads(response.body)
            pretty_json = json.dumps(parsed, indent=2)
            self.body_view.setText(pretty_json)
        except:
            self.body_view.setText(response.body)
