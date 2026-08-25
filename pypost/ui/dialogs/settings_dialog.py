from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.core.encryption_migration import EncryptionMigrationService
from pypost.core.key_source_constants import (  # noqa: F401
    KEY_SOURCE_ENVIRONMENT,
    KEY_SOURCE_KEYRING,
    KEY_SOURCE_SECRET_STORE,
)
from pypost.core.storage_interface import StorageInterface
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import (
    confirm_encrypt_plaintext_hidden,
    confirm_re_encrypt_environments,
    show_migration_result,
)
from pypost.ui.collection_item_dialogs import (  # noqa: F401
    show_invalid_bind_address,
    show_invalid_retryable_status_codes,
)
from pypost.ui.widgets.settings import (
    EditorSettingsSection,
    EncryptionConfigSection,
    EncryptionMigrationSection,
    RequestSettingsSection,
    RetryPolicySection,
    SecurityAlertSection,
    ServerBindSettingsSection,
    WebSocketSettingsSection,
)
from pypost.ui.widgets.settings.encryption_config_section import (  # noqa: F401
    ENCRYPTION_MODE_DEFAULT,
    ENCRYPTION_MODE_DISABLED,
    ENCRYPTION_MODE_ENABLED,
    parse_env_encryption_enabled_from_mode,
)
from pypost.ui.widgets.settings.security_alert_section import (  # noqa: F401
    WEBHOOK_AUTH_KEEP_PLACEHOLDER,
    WEBHOOK_AUTH_NEW_PLACEHOLDER,
    _resolve_webhook_auth_header,
)
from pypost.ui.widget_ids import SETTINGS_DIALOG, SETTINGS_TABS, set_widget_id

logger = logging.getLogger(__name__)

SETTINGS_TAB_LABELS: tuple[str, ...] = (
    "General",
    "Requests & Retries",
    "Network",
    "Security & Alerts",
    "Encryption",
)


def _make_tab_page() -> tuple[QWidget, QFormLayout]:
    page = QWidget()
    form = QFormLayout(page)
    return page, form


class SettingsDialog(QDialog):
    def __init__(
        self,
        current_settings: AppSettings,
        parent=None,
        *,
        storage: StorageInterface | None = None,
        migration_service: EncryptionMigrationService | None = None,
    ):
        super().__init__(parent)
        set_widget_id(self, SETTINGS_DIALOG)
        self.setWindowTitle("Settings")
        self.resize(520, 480)
        self.current_settings = current_settings
        self.new_settings = None
        self._storage = storage
        self._migration_worker = None

        self.layout = QVBoxLayout(self)

        editor = EditorSettingsSection(current_settings, self)
        request = RequestSettingsSection(current_settings, self)
        server_bind = ServerBindSettingsSection(current_settings, self)
        encryption_config = EncryptionConfigSection(current_settings, self)
        encryption_migration = EncryptionMigrationSection(
            self,
            storage=storage,
            migration_service=migration_service,
            encryption_config=encryption_config,
            current_settings=current_settings,
            show_migration_result=show_migration_result,
            confirm_re_encrypt_environments=confirm_re_encrypt_environments,
            confirm_encrypt_plaintext_hidden=confirm_encrypt_plaintext_hidden,
            host_dialog=self,
        )
        retry_policy = RetryPolicySection(current_settings, self)
        security_alert = SecurityAlertSection(current_settings, self)
        websocket_section = WebSocketSettingsSection(current_settings, self)

        self._editor_section = editor
        self._request_section = request
        self._server_bind_section = server_bind
        self._encryption_config_section = encryption_config
        self._encryption_migration_section = encryption_migration
        self._retry_policy_section = retry_policy
        self._security_alert_section = security_alert
        self._websocket_section = websocket_section

        self.font_size_spin = editor.font_size_spin
        self.indent_size_spin = editor.indent_size_spin
        self.theme_combo = editor.theme_combo
        self.timeout_spin = request.timeout_spin
        self.confirm_overwrite_check = request.confirm_overwrite_check
        self.mcp_port_spin = server_bind.mcp_port_spin
        self.mcp_host_edit = server_bind.mcp_host_edit
        self.metrics_port_spin = server_bind.metrics_port_spin
        self.metrics_host_edit = server_bind.metrics_host_edit
        self.env_encryption_mode_combo = encryption_config.env_encryption_mode_combo
        self.env_encryption_key_source_combo = encryption_config.env_encryption_key_source_combo
        self.env_encryption_key_source_fallback_edit = (
            encryption_config.env_encryption_key_source_fallback_edit
        )
        self.env_encryption_fallback_warning_label = (
            encryption_config.env_encryption_fallback_warning_label
        )
        self.env_encryption_help_label = encryption_config.env_encryption_help_label
        self.encryption_migration_section_label = (
            encryption_migration.encryption_migration_section_label
        )
        self.verify_encryption_btn = encryption_migration.verify_encryption_btn
        self.reencrypt_environments_btn = encryption_migration.reencrypt_environments_btn
        self.encrypt_plaintext_btn = encryption_migration.encrypt_plaintext_btn
        self.max_retries_spin = retry_policy.max_retries_spin
        self.retry_delay_spin = retry_policy.retry_delay_spin
        self.retry_backoff_spin = retry_policy.retry_backoff_spin
        self.retryable_codes_edit = retry_policy.retryable_codes_edit
        self.security_logging_section_label = security_alert.security_logging_section_label
        self.log_hidden_key_names_check = security_alert.log_hidden_key_names_check
        self.alert_log_path_edit = security_alert.alert_log_path_edit
        self.alert_webhook_url_edit = security_alert.alert_webhook_url_edit
        self.alert_webhook_auth_edit = security_alert.alert_webhook_auth_edit
        self.alert_webhook_auth_clear_check = security_alert.alert_webhook_auth_clear_check
        self._had_webhook_auth = security_alert._had_webhook_auth

        self._migration_service = encryption_migration._migration_service

        general_page, general_form = _make_tab_page()
        requests_page, requests_form = _make_tab_page()
        network_page, network_form = _make_tab_page()
        security_page, security_form = _make_tab_page()
        encryption_page, encryption_form = _make_tab_page()

        editor.add_to_form(general_form)
        request.add_timeout_to_form(requests_form)
        request.add_confirm_overwrite_to_form(requests_form)
        retry_policy.add_to_form(requests_form)
        server_bind.add_to_form(network_form)
        websocket_section.add_to_form(network_form)
        security_alert.add_to_form(security_form)
        encryption_config.add_to_form(encryption_form)
        encryption_migration.add_to_form(encryption_form)

        self._tab_pages = (
            general_page,
            requests_page,
            network_page,
            security_page,
            encryption_page,
        )
        self._tab_form_layouts = (
            general_form,
            requests_form,
            network_form,
            security_form,
            encryption_form,
        )

        self.settings_tabs = QTabWidget(self)
        set_widget_id(self.settings_tabs, SETTINGS_TABS)
        for page, label in zip(self._tab_pages, SETTINGS_TAB_LABELS, strict=True):
            self.settings_tabs.addTab(page, label)

        self.layout.addWidget(self.settings_tabs)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def tab_form_layout(self, page: QWidget) -> QFormLayout:
        index = self._tab_pages.index(page)
        return self._tab_form_layouts[index]

    def form_layout_index_of(self, widget: QWidget) -> int:
        for form in self._tab_form_layouts:
            index = form.indexOf(widget)
            if index >= 0:
                return index
        return -1

    def _encryption_settings_from_form(self) -> AppSettings:
        return self._encryption_config_section.encryption_settings_from_form(
            self.current_settings,
        )

    def _on_verify_encryption(self) -> None:
        self._encryption_migration_section.on_verify_encryption()

    def _on_re_encrypt_environments(self) -> None:
        self._encryption_migration_section.on_re_encrypt_environments()

    def _on_encrypt_plaintext_hidden(self) -> None:
        self._encryption_migration_section.on_encrypt_plaintext_hidden()

    def accept(self):
        bind_values = self._server_bind_section.validate(self)
        if bind_values is None:
            return

        retry_policy = self._retry_policy_section.validate(self)
        if retry_policy is None:
            return

        fields: dict = {}
        fields.update(self._editor_section.collect_fields())
        fields.update(self._request_section.collect_fields())
        fields.update(self._server_bind_section.collect_validated_fields(bind_values))
        fields.update(self._encryption_config_section.collect_fields())
        fields.update(self._retry_policy_section.collect_fields(retry_policy))
        fields.update(self._security_alert_section.collect_fields())
        fields.update(self._websocket_section.collect_fields())

        self.new_settings = AppSettings(
            config_version=self.current_settings.config_version,
            revision=self.current_settings.revision,
            last_environment_id=self.current_settings.last_environment_id,
            open_tabs=self.current_settings.open_tabs,
            expanded_collections=self.current_settings.expanded_collections,
            **fields,
        )
        super().accept()

    def get_settings(self) -> AppSettings:
        return self.new_settings
