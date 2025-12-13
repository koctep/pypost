from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                               QSpinBox, QDialogButtonBox, QCheckBox)
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
        
        self.indent_size_spin = QSpinBox()
        self.indent_size_spin.setRange(2, 8)
        self.indent_size_spin.setValue(current_settings.indent_size)

        self.mcp_port_spin = QSpinBox()
        self.mcp_port_spin.setRange(1024, 65535)
        self.mcp_port_spin.setValue(current_settings.mcp_port)

        self.confirm_overwrite_check = QCheckBox()

        self.confirm_overwrite_check.setChecked(current_settings.confirm_overwrite_request)

        self.form_layout.addRow("Application Font Size:", self.font_size_spin)
        self.form_layout.addRow("JSON Indent Size:", self.indent_size_spin)
        self.form_layout.addRow("MCP Server Port:", self.mcp_port_spin)
        self.form_layout.addRow("Confirm before overwriting requests:", self.confirm_overwrite_check)
        self.layout.addLayout(self.form_layout)


        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def accept(self):
        # Create new settings object
        self.new_settings = AppSettings(
            font_size=self.font_size_spin.value(),
            indent_size=self.indent_size_spin.value(),
            config_version=self.current_settings.config_version,
            revision=self.current_settings.revision,
            last_environment_id=self.current_settings.last_environment_id,
            open_tabs=self.current_settings.open_tabs,
            expanded_collections=self.current_settings.expanded_collections,
            confirm_overwrite_request=self.confirm_overwrite_check.isChecked(),
            mcp_port=self.mcp_port_spin.value()
        )
        super().accept()
    
    def get_settings(self) -> AppSettings:
        return self.new_settings

