"""Editor settings section (font size, JSON indent)."""

from __future__ import annotations


from typing import Any

from PySide6.QtWidgets import QComboBox, QFormLayout, QSpinBox, QWidget

from pypost.models.settings import AppSettings, ThemeSetting

_THEME_OPTIONS: list[tuple[ThemeSetting, str]] = [
    ("system", "System"),
    ("light", "Light"),
    ("dark", "Dark"),
]


class EditorSettingsSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.font_size_spin = QSpinBox(parent)
        self.font_size_spin.setRange(8, 48)
        self.font_size_spin.setValue(current_settings.font_size)

        self.indent_size_spin = QSpinBox(parent)
        self.indent_size_spin.setRange(2, 8)
        self.indent_size_spin.setValue(current_settings.indent_size)

        self.theme_combo = QComboBox(parent)
        for value, label in _THEME_OPTIONS:
            self.theme_combo.addItem(label, value)
        theme_index = self.theme_combo.findData(current_settings.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow("Application Font Size:", self.font_size_spin)
        form.addRow("JSON Indent Size:", self.indent_size_spin)
        form.addRow("Theme:", self.theme_combo)

    def collect_fields(self) -> dict[str, Any]:
        return {
            "font_size": self.font_size_spin.value(),
            "indent_size": self.indent_size_spin.value(),
            "theme": self.theme_combo.currentData(),
        }
