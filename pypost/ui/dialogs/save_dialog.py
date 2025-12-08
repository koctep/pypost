from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                               QComboBox, QDialogButtonBox, QMessageBox)
from typing import List
from pypost.models.models import Collection

class SaveRequestDialog(QDialog):
    def __init__(self, collections: List[Collection], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Request")
        self.collections = collections
        self.selected_collection_id = None
        self.request_name = ""

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Request Name
        layout.addWidget(QLabel("Request Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Collection Selector
        layout.addWidget(QLabel("Collection:"))
        self.collection_combo = QComboBox()

        # Add "New Collection" option
        self.collection_combo.addItem("Create New Collection...", None)

        for col in self.collections:
            self.collection_combo.addItem(col.name, col.id)

        layout.addWidget(self.collection_combo)

        # New Collection Name (hidden by default)
        self.new_col_input = QLineEdit()
        self.new_col_input.setPlaceholderText("New Collection Name")
        self.new_col_input.hide()
        layout.addWidget(self.new_col_input)

        self.collection_combo.currentIndexChanged.connect(self.on_collection_changed)

        # Initial state
        self.on_collection_changed(self.collection_combo.currentIndex())

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_collection_changed(self, index):
        if index == 0:
            self.new_col_input.show()
        else:
            self.new_col_input.hide()

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a request name")
            return

        self.request_name = name

        if self.collection_combo.currentIndex() == 0:
            new_col_name = self.new_col_input.text().strip()
            if not new_col_name:
                QMessageBox.warning(self, "Error", "Please enter a new collection name")
                return
            self.new_collection_name = new_col_name
            self.selected_collection_id = None # Signal to create new
        else:
            self.selected_collection_id = self.collection_combo.currentData()
            self.new_collection_name = None

        self.accept()
