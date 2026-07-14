"""Environment encryption configuration section."""

from __future__ import annotations


from typing import Any

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit, QWidget

from pypost.core.key_source_constants import (
    KEY_SOURCE_ENVIRONMENT,
    KEY_SOURCE_KEYRING,
    KEY_SOURCE_SECRET_STORE,
    find_fallback_parse_issues,
    parse_key_source_fallback,
)
from pypost.models.settings import AppSettings

ENCRYPTION_MODE_DEFAULT = "default"
ENCRYPTION_MODE_ENABLED = "enabled"
ENCRYPTION_MODE_DISABLED = "disabled"

ENCRYPTION_SCOPE_HELP = (
    "Encrypts values for variables marked Hidden in each environment only. "
    "Non-hidden variables stay plaintext on disk even when encryption is enabled."
)


def parse_env_encryption_enabled_from_mode(encryption_mode: str) -> bool | None:
    """Map Settings encryption mode combo value to tri-state env_encryption_enabled."""
    if encryption_mode == ENCRYPTION_MODE_ENABLED:
        return True
    if encryption_mode == ENCRYPTION_MODE_DISABLED:
        return False
    return None


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


class EncryptionConfigSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.env_encryption_mode_combo = QComboBox(parent)
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

        self.env_encryption_key_source_combo = QComboBox(parent)
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

        self.env_encryption_key_source_fallback_edit = QLineEdit(parent)
        self.env_encryption_key_source_fallback_edit.setPlaceholderText(
            "e.g. environment, secret_store",
        )
        fallback = current_settings.env_encryption_key_source_fallback
        if fallback:
            self.env_encryption_key_source_fallback_edit.setText(",".join(fallback))

        self.env_encryption_fallback_warning_label = QLabel(parent)
        self.env_encryption_fallback_warning_label.setWordWrap(True)
        self.env_encryption_key_source_fallback_edit.textChanged.connect(
            self._update_fallback_warning,
        )
        self._update_fallback_warning()

        self.env_encryption_help_label = QLabel(parent)
        self.env_encryption_help_label.setWordWrap(True)
        self.env_encryption_scope_label = QLabel(ENCRYPTION_SCOPE_HELP, parent)
        self.env_encryption_scope_label.setWordWrap(True)
        self.env_encryption_key_source_combo.currentIndexChanged.connect(
            self._update_encryption_key_source_help,
        )
        self._update_encryption_key_source_help()

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow(
            "Environment encryption at rest:",
            self.env_encryption_mode_combo,
        )
        form.addRow(
            "Encryption key source:",
            self.env_encryption_key_source_combo,
        )
        form.addRow(
            "Encryption key source fallback:",
            self.env_encryption_key_source_fallback_edit,
        )
        form.addRow("", self.env_encryption_scope_label)
        form.addRow("", self.env_encryption_fallback_warning_label)
        form.addRow("", self.env_encryption_help_label)

    def collect_fields(self) -> dict[str, Any]:
        return {
            "env_encryption_enabled": parse_env_encryption_enabled_from_mode(
                self.env_encryption_mode_combo.currentData(),
            ),
            "env_encryption_key_source": self.env_encryption_key_source_combo.currentData(),
            "env_encryption_key_source_fallback": parse_key_source_fallback(
                self.env_encryption_key_source_fallback_edit.text(),
            ),
        }

    def encryption_settings_from_form(self, base: AppSettings) -> AppSettings:
        return base.model_copy(update=self.collect_fields())

    def _update_encryption_key_source_help(self) -> None:
        source = self.env_encryption_key_source_combo.currentData()
        help_text = KEY_SOURCE_HELP.get(source, KEY_SOURCE_HELP[KEY_SOURCE_ENVIRONMENT])
        self.env_encryption_help_label.setText(help_text)

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
