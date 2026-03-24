from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QSpinBox, QDoubleSpinBox, QDialogButtonBox, QCheckBox, QLineEdit,
)
from pypost.models.settings import AppSettings
from pypost.models.retry import RetryPolicy


class SettingsDialog(QDialog):
    def __init__(self, current_settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 400)
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

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(current_settings.request_timeout)

        self.mcp_port_spin = QSpinBox()
        self.mcp_port_spin.setRange(1024, 65535)
        self.mcp_port_spin.setValue(current_settings.mcp_port)

        self.mcp_host_edit = QLineEdit()
        self.mcp_host_edit.setText(current_settings.mcp_host)

        self.metrics_port_spin = QSpinBox()
        self.metrics_port_spin.setRange(1024, 65535)
        self.metrics_port_spin.setValue(current_settings.metrics_port)

        self.metrics_host_edit = QLineEdit()
        self.metrics_host_edit.setText(current_settings.metrics_host)

        self.confirm_overwrite_check = QCheckBox()
        self.confirm_overwrite_check.setChecked(current_settings.confirm_overwrite_request)

        # Retry policy defaults
        default_policy = RetryPolicy()
        current_policy = current_settings.default_retry_policy or default_policy

        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(current_policy.max_retries)

        self.retry_delay_spin = QDoubleSpinBox()
        self.retry_delay_spin.setRange(0.1, 30.0)
        self.retry_delay_spin.setSingleStep(0.1)
        self.retry_delay_spin.setDecimals(1)
        self.retry_delay_spin.setValue(current_policy.retry_delay_seconds)

        self.retry_backoff_spin = QDoubleSpinBox()
        self.retry_backoff_spin.setRange(1.0, 5.0)
        self.retry_backoff_spin.setSingleStep(0.1)
        self.retry_backoff_spin.setDecimals(1)
        self.retry_backoff_spin.setValue(current_policy.retry_backoff_multiplier)

        self.retryable_codes_edit = QLineEdit()
        self.retryable_codes_edit.setPlaceholderText("e.g. 429,500,502,503,504")
        self.retryable_codes_edit.setText(
            ",".join(str(c) for c in current_policy.retryable_status_codes)
        )

        self.alert_webhook_url_edit = QLineEdit()
        self.alert_webhook_url_edit.setPlaceholderText("https://hooks.example.com/alert")
        self.alert_webhook_url_edit.setText(current_settings.alert_webhook_url or "")

        self.alert_webhook_auth_edit = QLineEdit()
        self.alert_webhook_auth_edit.setPlaceholderText("Bearer <token>")
        self.alert_webhook_auth_edit.setText(current_settings.alert_webhook_auth_header or "")

        self.form_layout.addRow("Application Font Size:", self.font_size_spin)
        self.form_layout.addRow("JSON Indent Size:", self.indent_size_spin)
        self.form_layout.addRow("MCP Server Port:", self.mcp_port_spin)
        self.form_layout.addRow("MCP Server Host:", self.mcp_host_edit)
        self.form_layout.addRow("Metrics Server Port:", self.metrics_port_spin)
        self.form_layout.addRow("Metrics Server Host:", self.metrics_host_edit)
        self.form_layout.addRow(
            "Confirm before overwriting requests:", self.confirm_overwrite_check
        )
        self.form_layout.addRow("Max Retries (0 = disabled):", self.max_retries_spin)
        self.form_layout.addRow("Retry Delay (seconds):", self.retry_delay_spin)
        self.form_layout.addRow("Retry Backoff Multiplier:", self.retry_backoff_spin)
        self.form_layout.addRow("Retryable Status Codes:", self.retryable_codes_edit)
        self.form_layout.addRow("Alert Webhook URL:", self.alert_webhook_url_edit)
        self.form_layout.addRow("Alert Webhook Auth Header:", self.alert_webhook_auth_edit)
        self.layout.addLayout(self.form_layout)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def _parse_retryable_codes(self) -> list:
        raw = self.retryable_codes_edit.text().strip()
        if not raw:
            return []
        codes = []
        for part in raw.split(","):
            part = part.strip()
            if part.isdigit():
                codes.append(int(part))
        return codes

    def accept(self):
        retry_policy = RetryPolicy(
            max_retries=self.max_retries_spin.value(),
            retry_delay_seconds=self.retry_delay_spin.value(),
            retry_backoff_multiplier=self.retry_backoff_spin.value(),
            retryable_status_codes=self._parse_retryable_codes(),
        )
        webhook_url = self.alert_webhook_url_edit.text().strip() or None
        webhook_auth = self.alert_webhook_auth_edit.text().strip() or None

        self.new_settings = AppSettings(
            font_size=self.font_size_spin.value(),
            indent_size=self.indent_size_spin.value(),
            request_timeout=self.timeout_spin.value(),
            config_version=self.current_settings.config_version,
            revision=self.current_settings.revision,
            last_environment_id=self.current_settings.last_environment_id,
            open_tabs=self.current_settings.open_tabs,
            expanded_collections=self.current_settings.expanded_collections,
            confirm_overwrite_request=self.confirm_overwrite_check.isChecked(),
            mcp_port=self.mcp_port_spin.value(),
            mcp_host=self.mcp_host_edit.text(),
            metrics_port=self.metrics_port_spin.value(),
            metrics_host=self.metrics_host_edit.text(),
            default_retry_policy=retry_policy,
            alert_webhook_url=webhook_url,
            alert_webhook_auth_header=webhook_auth,
        )
        super().accept()

    def get_settings(self) -> AppSettings:
        return self.new_settings
