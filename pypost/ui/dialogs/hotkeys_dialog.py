from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from pypost.ui.hotkeys import collect_hotkey_rows


class HotkeysDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys")
        self.setMinimumSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        root = self.parent() or self
        shortcuts = collect_hotkey_rows(root)

        self.table.setRowCount(len(shortcuts))

        for row, (action, key) in enumerate(shortcuts):
            action_item = QTableWidgetItem(action)
            key_item = QTableWidgetItem(key)

            if not key:
                action_item.setFlags(Qt.NoItemFlags)
                action_item.setBackground(Qt.lightGray)
                action_item.setForeground(Qt.black)
                key_item.setFlags(Qt.NoItemFlags)
                key_item.setBackground(Qt.lightGray)

                font = action_item.font()
                font.setBold(True)
                action_item.setFont(font)

            self.table.setItem(row, 0, action_item)

            key_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, key_item)

        layout.addWidget(self.table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
