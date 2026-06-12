"""Request settings section (timeout, confirm overwrite)."""

from typing import Any

from PySide6.QtWidgets import QCheckBox, QFormLayout, QSpinBox, QWidget

from pypost.models.settings import AppSettings


class RequestSettingsSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.timeout_spin = QSpinBox(parent)
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(current_settings.request_timeout)

        self.confirm_overwrite_check = QCheckBox(parent)
        self.confirm_overwrite_check.setChecked(current_settings.confirm_overwrite_request)

    def add_timeout_to_form(self, form: QFormLayout) -> None:
        form.addRow("Request Timeout (seconds):", self.timeout_spin)

    def add_confirm_overwrite_to_form(self, form: QFormLayout) -> None:
        form.addRow(
            "Confirm before overwriting requests:",
            self.confirm_overwrite_check,
        )

    def collect_fields(self) -> dict[str, Any]:
        return {
            "request_timeout": self.timeout_spin.value(),
            "confirm_overwrite_request": self.confirm_overwrite_check.isChecked(),
        }
