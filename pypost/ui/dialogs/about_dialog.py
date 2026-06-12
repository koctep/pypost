from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from pypost.version import __version__


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PyPost")
        self.setMinimumSize(300, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # App Name
        name_label = QLabel("PyPost")
        name_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        version_label = QLabel(f"Version {__version__}")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Description
        desc_label = QLabel(
            "A lightweight HTTP client for testing APIs.\nBuilt with Python and PySide6."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("margin: 10px 0;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Close Button
        close_btn = QPushButton("OK")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
