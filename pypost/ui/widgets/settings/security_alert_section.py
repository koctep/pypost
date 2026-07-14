"""Security, logging, and alerting settings section."""

from __future__ import annotations


from pathlib import Path
from typing import Any

from platformdirs import user_data_dir
from PySide6.QtWidgets import QCheckBox, QFormLayout, QLineEdit, QWidget

from pypost.models.settings import AppSettings
from pypost.ui.widgets.settings._common import make_section_header

ALERT_LOG_FILENAME = "pypost-alerts.log"
WEBHOOK_AUTH_KEEP_PLACEHOLDER = "Leave blank to keep configured value"
WEBHOOK_AUTH_NEW_PLACEHOLDER = "Bearer <token>"


def _default_alert_log_path() -> str:
    return str(Path(user_data_dir("pypost")) / ALERT_LOG_FILENAME)


def _resolve_webhook_auth_header(
    entered: str,
    *,
    had_stored_auth: bool,
    stored_auth: str | None,
    clear_requested: bool,
) -> str | None:
    if clear_requested:
        return None
    stripped = entered.strip()
    if stripped:
        return stripped
    if had_stored_auth:
        return stored_auth
    return None


class SecurityAlertSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self._had_webhook_auth = bool(current_settings.alert_webhook_auth_header)
        self._stored_auth = current_settings.alert_webhook_auth_header

        self.log_hidden_key_names_check = QCheckBox(
            "Log variable key names when hidden flag is toggled",
            parent,
        )
        self.log_hidden_key_names_check.setChecked(
            current_settings.log_hidden_key_names,
        )

        self.alert_log_path_edit = QLineEdit(parent)
        self.alert_log_path_edit.setPlaceholderText(
            f"Empty for default ({_default_alert_log_path()})",
        )
        self.alert_log_path_edit.setText(current_settings.alert_log_path or "")

        self.alert_webhook_url_edit = QLineEdit(parent)
        self.alert_webhook_url_edit.setPlaceholderText("https://hooks.example.com/alert")
        self.alert_webhook_url_edit.setText(current_settings.alert_webhook_url or "")

        self.alert_webhook_auth_edit = QLineEdit(parent)
        self.alert_webhook_auth_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_placeholder = (
            WEBHOOK_AUTH_KEEP_PLACEHOLDER
            if self._had_webhook_auth
            else WEBHOOK_AUTH_NEW_PLACEHOLDER
        )
        self.alert_webhook_auth_edit.setPlaceholderText(auth_placeholder)

        self.alert_webhook_auth_clear_check = QCheckBox(
            "Remove stored authorization header",
            parent,
        )
        self.alert_webhook_auth_clear_check.setVisible(self._had_webhook_auth)

        self.security_logging_section_label = make_section_header("Security / Logging")

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow(self.security_logging_section_label)
        form.addRow("", self.log_hidden_key_names_check)
        form.addRow("Alert Log Path:", self.alert_log_path_edit)
        form.addRow("Alert Webhook URL:", self.alert_webhook_url_edit)
        form.addRow("Alert Webhook Auth Header:", self.alert_webhook_auth_edit)
        if self._had_webhook_auth:
            form.addRow("", self.alert_webhook_auth_clear_check)

    def collect_fields(self) -> dict[str, Any]:
        alert_log_path = self.alert_log_path_edit.text().strip() or None
        webhook_url = self.alert_webhook_url_edit.text().strip() or None
        webhook_auth = _resolve_webhook_auth_header(
            self.alert_webhook_auth_edit.text(),
            had_stored_auth=self._had_webhook_auth,
            stored_auth=self._stored_auth,
            clear_requested=self.alert_webhook_auth_clear_check.isChecked(),
        )
        return {
            "log_hidden_key_names": self.log_hidden_key_names_check.isChecked(),
            "alert_log_path": alert_log_path,
            "alert_webhook_url": webhook_url,
            "alert_webhook_auth_header": webhook_auth,
        }
