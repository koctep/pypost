from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                               QSpinBox, QDialogButtonBox)
from pypost.models.settings import AppSettings

class SettingsDialog(QDialog):
    def __init__(self, current_settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(300, 150)
        self.current_settings = current_settings
        self.new_settings = None

        self.layout = QVBoxLayout(self)

        # Form
        self.form_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 48)
        self.font_size_spin.setValue(current_settings.font_size)
        
        self.form_layout.addRow("Application Font Size:", self.font_size_spin)
        self.layout.addLayout(self.form_layout)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def accept(self):
        # Create new settings object
        self.new_settings = AppSettings(
            font_size=self.font_size_spin.value()
        )
        super().accept()
    
    def get_settings(self) -> AppSettings:
        return self.new_settings

