"""Editor settings section (font size, JSON indent)."""

from typing import Any

from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget

from pypost.models.settings import AppSettings


class EditorSettingsSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.font_size_spin = QSpinBox(parent)
        self.font_size_spin.setRange(8, 48)
        self.font_size_spin.setValue(current_settings.font_size)

        self.indent_size_spin = QSpinBox(parent)
        self.indent_size_spin.setRange(2, 8)
        self.indent_size_spin.setValue(current_settings.indent_size)

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow("Application Font Size:", self.font_size_spin)
        form.addRow("JSON Indent Size:", self.indent_size_spin)

    def collect_fields(self) -> dict[str, Any]:
        return {
            "font_size": self.font_size_spin.value(),
            "indent_size": self.indent_size_spin.value(),
        }
