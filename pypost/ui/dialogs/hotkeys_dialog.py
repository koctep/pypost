from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt

class HotkeysDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys")
        self.setMinimumSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        
        # Data
        shortcuts = [
            ("General", ""),
            ("Quit Application", "Ctrl+Q"),
            ("Settings", "Ctrl+, / F12"),
            ("Environment Manager", "Ctrl+E"),
            ("Tabs", ""),
            ("New Tab", "Ctrl+N"),
            ("Close Tab", "Ctrl+W"),
            ("Next Tab", "Ctrl+Tab"),
            ("Previous Tab", "Ctrl+Shift+Tab"),
            ("Switch to Tab 1-9", "Alt+1 ... Alt+9"),
            ("Request Editor", ""),
            ("Send Request", "F5 / Ctrl+Enter"),
            ("Save Request", "Ctrl+S"),
            ("Focus URL Bar", "Ctrl+L / Alt+D"),
            ("Switch to Params", "Ctrl+P"),
            ("Switch to Headers", "Ctrl+H"),
            ("Switch to Body", "Ctrl+B"),
            ("Switch to Script", "Ctrl+T"),
        ]

        self.table.setRowCount(len(shortcuts))
        
        for row, (action, key) in enumerate(shortcuts):
            action_item = QTableWidgetItem(action)
            key_item = QTableWidgetItem(key)
            
            if not key:  # Section header
                action_item.setFlags(Qt.NoItemFlags)
                action_item.setBackground(Qt.lightGray)
                action_item.setForeground(Qt.black)
                key_item.setFlags(Qt.NoItemFlags)
                key_item.setBackground(Qt.lightGray)
                
                # Make section header span both columns? Or just look distinct
                # Spanning isn't trivial in QTableWidget without setSpan, let's just style it
                font = action_item.font()
                font.setBold(True)
                action_item.setFont(font)
            
            self.table.setItem(row, 0, action_item)
            
            # Align shortcuts to the right
            key_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, key_item)

        layout.addWidget(self.table)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

