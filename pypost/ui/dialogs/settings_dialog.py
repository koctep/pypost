import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from pypost.core.encryption_migration import EncryptionMigrationService, MigrationReport
from pypost.core.key_source_constants import (
    KEY_SOURCE_ENVIRONMENT,
    KEY_SOURCE_KEYRING,
    KEY_SOURCE_SECRET_STORE,
    find_fallback_parse_issues,
    parse_key_source_fallback,
)
from pypost.core.storage import StorageManager
from pypost.models.retry import (
    RetryableCodesValidationFailure,
    RetryPolicy,
    parse_retryable_status_codes,
)
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

ENCRYPTION_MODE_DEFAULT = "default"
ENCRYPTION_MODE_ENABLED = "enabled"
ENCRYPTION_MODE_DISABLED = "disabled"

SECTION_HEADER_STYLE = "font-weight: bold; margin-top: 8px;"


def _make_section_header(title: str) -> QLabel:
    label = QLabel(title)
    label.setStyleSheet(SECTION_HEADER_STYLE)
    return label


def _format_migration_report(report: MigrationReport) -> str:
    inv = report.inventory
    lines = [
        f"Environments: {inv.environment_count}",
        f"Hidden values: {inv.hidden_value_count}",
        f"Encrypted envelopes: {inv.encrypted_envelope_count}",
        f"Plaintext hidden: {inv.plaintext_hidden_count}",
    ]
    if inv.kid_histogram:
        lines.append("Key IDs:")
        for kid, count in sorted(inv.kid_histogram.items()):
            lines.append(f"  {kid}: {count}")
    if inv.missing_kids:
        lines.append("Missing key IDs:")
        for kid in sorted(inv.missing_kids):
            lines.append(f"  {kid}")
    if report.backup_path is not None:
        lines.append(f"Backup: {report.backup_path}")
    if report.errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"  {error}" for error in report.errors)
    return "\n".join(lines)


KEY_SOURCE_HELP = {
    KEY_SOURCE_ENVIRONMENT: (
        "Store the Fernet key in PYPOST_ENV_ENCRYPTION_KEY (shell or service env). "
        "Do not put key material in settings.json."
    ),
    KEY_SOURCE_KEYRING: (
        "Store keys in the OS credential store (keyring service pypost/env-encryption, "
        "entry active for current key). Requires the keyring package."
    ),
    KEY_SOURCE_SECRET_STORE: (
        "Load keys from an operator-managed JSON spec via "
        "PYPOST_ENV_ENCRYPTION_SECRETS_FILE. Do not put key material in settings.json."
    ),
}


class SettingsDialog(QDialog):
    def __init__(
        self,
        current_settings: AppSettings,
        parent=None,
        *,
        storage: StorageManager | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 400)
        self.current_settings = current_settings
        self.new_settings = None
        self._storage = storage
        self._migration_service = (
            EncryptionMigrationService(storage) if storage is not None else None
        )

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

        self.log_hidden_key_names_check = QCheckBox(
            "Log variable key names when hidden flag is toggled",
        )
        self.log_hidden_key_names_check.setChecked(
            current_settings.log_hidden_key_names,
        )

        self.env_encryption_mode_combo = QComboBox()
        self.env_encryption_mode_combo.addItem(
            "Use environment variable default",
            ENCRYPTION_MODE_DEFAULT,
        )
        self.env_encryption_mode_combo.addItem("Enabled", ENCRYPTION_MODE_ENABLED)
        self.env_encryption_mode_combo.addItem("Disabled", ENCRYPTION_MODE_DISABLED)
        if current_settings.env_encryption_enabled is True:
            self.env_encryption_mode_combo.setCurrentIndex(1)
        elif current_settings.env_encryption_enabled is False:
            self.env_encryption_mode_combo.setCurrentIndex(2)
        else:
            self.env_encryption_mode_combo.setCurrentIndex(0)

        self.env_encryption_key_source_combo = QComboBox()
        self.env_encryption_key_source_combo.addItem(
            "Environment variable (PYPOST_ENV_ENCRYPTION_KEY)",
            KEY_SOURCE_ENVIRONMENT,
        )
        self.env_encryption_key_source_combo.addItem(
            "OS keyring (pypost/env-encryption)",
            KEY_SOURCE_KEYRING,
        )
        self.env_encryption_key_source_combo.addItem(
            "Secret store spec file (PYPOST_ENV_ENCRYPTION_SECRETS_FILE)",
            KEY_SOURCE_SECRET_STORE,
        )
        key_source = current_settings.env_encryption_key_source or KEY_SOURCE_ENVIRONMENT
        source_index = self.env_encryption_key_source_combo.findData(key_source)
        self.env_encryption_key_source_combo.setCurrentIndex(
            source_index if source_index >= 0 else 0,
        )

        self.env_encryption_key_source_fallback_edit = QLineEdit()
        self.env_encryption_key_source_fallback_edit.setPlaceholderText(
            "e.g. environment, secret_store",
        )
        fallback = current_settings.env_encryption_key_source_fallback
        if fallback:
            self.env_encryption_key_source_fallback_edit.setText(",".join(fallback))

        self.env_encryption_fallback_warning_label = QLabel()
        self.env_encryption_fallback_warning_label.setWordWrap(True)
        self.env_encryption_key_source_fallback_edit.textChanged.connect(
            self._update_fallback_warning,
        )
        self._update_fallback_warning()

        self.env_encryption_help_label = QLabel()
        self.env_encryption_help_label.setWordWrap(True)
        self.env_encryption_key_source_combo.currentIndexChanged.connect(
            self._update_encryption_key_source_help,
        )
        self._update_encryption_key_source_help()

        self.encryption_migration_section_label = _make_section_header(
            "Encryption migration",
        )
        self.verify_encryption_btn = QPushButton("Verify encryption")
        self.verify_encryption_btn.clicked.connect(self._on_verify_encryption)
        self.reencrypt_environments_btn = QPushButton("Re-encrypt all environments")
        self.reencrypt_environments_btn.clicked.connect(self._on_re_encrypt_environments)
        migration_enabled = self._migration_service is not None
        self.verify_encryption_btn.setEnabled(migration_enabled)
        self.reencrypt_environments_btn.setEnabled(migration_enabled)

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
        self.form_layout.addRow("Request Timeout (seconds):", self.timeout_spin)
        self.form_layout.addRow("MCP Server Port:", self.mcp_port_spin)
        self.form_layout.addRow("MCP Server Host:", self.mcp_host_edit)
        self.form_layout.addRow("Metrics Server Port:", self.metrics_port_spin)
        self.form_layout.addRow("Metrics Server Host:", self.metrics_host_edit)
        self.form_layout.addRow(
            "Confirm before overwriting requests:", self.confirm_overwrite_check
        )
        self.form_layout.addRow(
            "Environment encryption at rest:",
            self.env_encryption_mode_combo,
        )
        self.form_layout.addRow(
            "Encryption key source:",
            self.env_encryption_key_source_combo,
        )
        self.form_layout.addRow(
            "Encryption key source fallback:",
            self.env_encryption_key_source_fallback_edit,
        )
        self.form_layout.addRow("", self.env_encryption_fallback_warning_label)
        self.form_layout.addRow("", self.env_encryption_help_label)
        self.form_layout.addRow(self.encryption_migration_section_label)
        self.form_layout.addRow("", self.verify_encryption_btn)
        self.form_layout.addRow("", self.reencrypt_environments_btn)
        self.form_layout.addRow("Max Retries (0 = disabled):", self.max_retries_spin)
        self.form_layout.addRow("Retry Delay (seconds):", self.retry_delay_spin)
        self.form_layout.addRow("Retry Backoff Multiplier:", self.retry_backoff_spin)
        self.form_layout.addRow("Retryable Status Codes:", self.retryable_codes_edit)
        self.security_logging_section_label = _make_section_header("Security / Logging")
        self.form_layout.addRow(self.security_logging_section_label)
        self.form_layout.addRow("", self.log_hidden_key_names_check)
        self.form_layout.addRow("Alert Webhook URL:", self.alert_webhook_url_edit)
        self.form_layout.addRow("Alert Webhook Auth Header:", self.alert_webhook_auth_edit)
        self.layout.addLayout(self.form_layout)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def _update_encryption_key_source_help(self) -> None:
        source = self.env_encryption_key_source_combo.currentData()
        help_text = KEY_SOURCE_HELP.get(source, KEY_SOURCE_HELP[KEY_SOURCE_ENVIRONMENT])
        self.env_encryption_help_label.setText(help_text)

    def _encryption_settings_from_form(self) -> AppSettings:
        encryption_mode = self.env_encryption_mode_combo.currentData()
        if encryption_mode == ENCRYPTION_MODE_ENABLED:
            env_encryption_enabled = True
        elif encryption_mode == ENCRYPTION_MODE_DISABLED:
            env_encryption_enabled = False
        else:
            env_encryption_enabled = None
        return self.current_settings.model_copy(
            update={
                "env_encryption_enabled": env_encryption_enabled,
                "env_encryption_key_source": self.env_encryption_key_source_combo.currentData(),
                "env_encryption_key_source_fallback": parse_key_source_fallback(
                    self.env_encryption_key_source_fallback_edit.text(),
                ),
            },
        )

    def _show_migration_result(self, title: str, report: MigrationReport) -> None:
        body = _format_migration_report(report)
        if report.success:
            QMessageBox.information(self, title, body)
        else:
            QMessageBox.warning(self, title, body)

    def _on_verify_encryption(self) -> None:
        if self._migration_service is None:
            return
        settings = self._encryption_settings_from_form()
        logger.info("settings_encryption_verify_started")
        report = self._migration_service.verify_decrypt_access(settings)
        logger.info(
            "settings_encryption_verify_completed success=%s error_count=%d",
            report.success,
            len(report.errors),
        )
        self._show_migration_result("Verify encryption", report)

    def _on_re_encrypt_environments(self) -> None:
        if self._migration_service is None:
            return
        confirm = QMessageBox.question(
            self,
            "Re-encrypt all environments",
            "This rewrites all encrypted hidden values under the current active key. "
            "A timestamped backup of environments.json is created before writing.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            logger.info("settings_encryption_reencrypt_cancelled")
            return
        settings = self._encryption_settings_from_form()
        logger.info("settings_encryption_reencrypt_started")
        report = self._migration_service.bulk_re_encrypt(settings, backup=True)
        logger.info(
            "settings_encryption_reencrypt_completed success=%s backup=%s error_count=%d",
            report.success,
            report.backup_path,
            len(report.errors),
        )
        self._show_migration_result("Re-encrypt all environments", report)

    def _update_fallback_warning(self) -> None:
        issues = find_fallback_parse_issues(
            self.env_encryption_key_source_fallback_edit.text(),
        )
        if not issues:
            self.env_encryption_fallback_warning_label.clear()
            return
        self.env_encryption_fallback_warning_label.setText(
            "Ignored fallback entries: " + ", ".join(issues),
        )

    def accept(self):
        parsed_codes = parse_retryable_status_codes(self.retryable_codes_edit.text())
        if isinstance(parsed_codes, RetryableCodesValidationFailure):
            logger.warning(
                "retryable_codes_settings_validation_failed reason=%s",
                parsed_codes.reason,
            )
            QMessageBox.warning(
                self,
                "Invalid retryable status codes",
                parsed_codes.message,
            )
            return
        retry_policy = RetryPolicy(
            max_retries=self.max_retries_spin.value(),
            retry_delay_seconds=self.retry_delay_spin.value(),
            retry_backoff_multiplier=self.retry_backoff_spin.value(),
            retryable_status_codes=parsed_codes,
        )
        webhook_url = self.alert_webhook_url_edit.text().strip() or None
        webhook_auth = self.alert_webhook_auth_edit.text().strip() or None
        encryption_mode = self.env_encryption_mode_combo.currentData()
        if encryption_mode == ENCRYPTION_MODE_ENABLED:
            env_encryption_enabled = True
        elif encryption_mode == ENCRYPTION_MODE_DISABLED:
            env_encryption_enabled = False
        else:
            env_encryption_enabled = None

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
            log_hidden_key_names=self.log_hidden_key_names_check.isChecked(),
            mcp_port=self.mcp_port_spin.value(),
            mcp_host=self.mcp_host_edit.text(),
            metrics_port=self.metrics_port_spin.value(),
            metrics_host=self.metrics_host_edit.text(),
            default_retry_policy=retry_policy,
            alert_webhook_url=webhook_url,
            alert_webhook_auth_header=webhook_auth,
            alert_log_path=self.current_settings.alert_log_path,
            env_encryption_enabled=env_encryption_enabled,
            env_encryption_key_source=self.env_encryption_key_source_combo.currentData(),
            env_encryption_key_source_fallback=parse_key_source_fallback(
                self.env_encryption_key_source_fallback_edit.text(),
            ),
        )
        super().accept()

    def get_settings(self) -> AppSettings:
        return self.new_settings
