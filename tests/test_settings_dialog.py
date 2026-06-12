"""Qt-level tests for SettingsDialog (request timeout visibility and persistence)."""


import logging

import pytest

pytestmark = pytest.mark.timeout(60)

from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from PySide6.QtWidgets import QLineEdit

from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import (
    SettingsDialog,
    WEBHOOK_AUTH_KEEP_PLACEHOLDER,
    WEBHOOK_AUTH_NEW_PLACEHOLDER,
    _resolve_webhook_auth_header,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestSettingsDialogRequestTimeout:
    def test_request_timeout_spin_is_on_form_layout(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert dlg.timeout_spin.parent() is dlg
            assert dlg.form_layout.indexOf(dlg.timeout_spin) >= 0
        finally:
            dlg.close()

    def test_request_timeout_loads_from_settings(self, qapp):
        dlg = SettingsDialog(AppSettings(request_timeout=142))
        try:
            assert dlg.timeout_spin.value() == 142
        finally:
            dlg.close()

    def test_accept_includes_request_timeout_in_result(self, qapp):
        dlg = SettingsDialog(AppSettings(request_timeout=60))
        try:
            dlg.timeout_spin.setValue(99)
            dlg.accept()
            assert dlg.get_settings().request_timeout == 99
        finally:
            dlg.close()


class TestSettingsDialogLogHiddenKeyNames:
    def test_log_hidden_key_names_checkbox_on_form(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert dlg.log_hidden_key_names_check.parent() is dlg
            assert dlg.form_layout.indexOf(dlg.log_hidden_key_names_check) >= 0
        finally:
            dlg.close()

    def test_log_hidden_key_names_loads_from_settings(self, qapp):
        dlg = SettingsDialog(AppSettings(log_hidden_key_names=True))
        try:
            assert dlg.log_hidden_key_names_check.isChecked()
        finally:
            dlg.close()

    def test_accept_includes_log_hidden_key_names_in_result(self, qapp):
        dlg = SettingsDialog(AppSettings(log_hidden_key_names=False))
        try:
            dlg.log_hidden_key_names_check.setChecked(True)
            dlg.accept()
            assert dlg.get_settings().log_hidden_key_names is True
        finally:
            dlg.close()


class TestSettingsDialogSecurityLoggingSection:
    def test_security_logging_section_header_visible(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert dlg.security_logging_section_label.text() == "Security / Logging"
            assert dlg.form_layout.indexOf(dlg.security_logging_section_label) >= 0
        finally:
            dlg.close()

    def test_security_logging_fields_grouped_after_retry_policy(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            retry_idx = dlg.form_layout.indexOf(dlg.retryable_codes_edit)
            header_idx = dlg.form_layout.indexOf(dlg.security_logging_section_label)
            hidden_idx = dlg.form_layout.indexOf(dlg.log_hidden_key_names_check)
            log_path_idx = dlg.form_layout.indexOf(dlg.alert_log_path_edit)
            webhook_idx = dlg.form_layout.indexOf(dlg.alert_webhook_url_edit)
            auth_idx = dlg.form_layout.indexOf(dlg.alert_webhook_auth_edit)
            assert (
                retry_idx
                < header_idx
                < hidden_idx
                < log_path_idx
                < webhook_idx
                < auth_idx
            )
        finally:
            dlg.close()


class TestSettingsDialogAlertSettings:
    def test_alert_log_path_loads_from_settings(self, qapp):
        dlg = SettingsDialog(AppSettings(alert_log_path="/tmp/custom-alerts.log"))
        try:
            assert dlg.alert_log_path_edit.text() == "/tmp/custom-alerts.log"
        finally:
            dlg.close()

    def test_accept_persists_alert_log_path(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.alert_log_path_edit.setText("/var/log/pypost-alerts.log")
            dlg.accept()
            assert dlg.get_settings().alert_log_path == "/var/log/pypost-alerts.log"
        finally:
            dlg.close()

    def test_accept_clears_alert_log_path_when_empty(self, qapp):
        dlg = SettingsDialog(AppSettings(alert_log_path="/tmp/old.log"))
        try:
            dlg.alert_log_path_edit.clear()
            dlg.accept()
            assert dlg.get_settings().alert_log_path is None
        finally:
            dlg.close()

    def test_webhook_auth_uses_password_echo_mode(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert (
                dlg.alert_webhook_auth_edit.echoMode() == QLineEdit.EchoMode.Password
            )
        finally:
            dlg.close()

    def test_webhook_auth_does_not_display_stored_value(self, qapp):
        dlg = SettingsDialog(
            AppSettings(alert_webhook_auth_header="Bearer secret-token"),
        )
        try:
            assert dlg.alert_webhook_auth_edit.text() == ""
            assert dlg.alert_webhook_auth_edit.placeholderText() == WEBHOOK_AUTH_KEEP_PLACEHOLDER
            assert dlg.form_layout.indexOf(dlg.alert_webhook_auth_clear_check) >= 0
        finally:
            dlg.close()

    def test_webhook_auth_placeholder_when_not_configured(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert dlg.alert_webhook_auth_edit.placeholderText() == WEBHOOK_AUTH_NEW_PLACEHOLDER
            assert dlg.form_layout.indexOf(dlg.alert_webhook_auth_clear_check) < 0
        finally:
            dlg.close()

    def test_accept_keeps_webhook_auth_when_field_empty(self, qapp):
        dlg = SettingsDialog(
            AppSettings(alert_webhook_auth_header="Bearer keep-me"),
        )
        try:
            dlg.accept()
            assert dlg.get_settings().alert_webhook_auth_header == "Bearer keep-me"
        finally:
            dlg.close()

    def test_accept_updates_webhook_auth_when_entered(self, qapp):
        dlg = SettingsDialog(AppSettings(alert_webhook_auth_header="Bearer old"))
        try:
            dlg.alert_webhook_auth_edit.setText("Bearer new-token")
            dlg.accept()
            assert dlg.get_settings().alert_webhook_auth_header == "Bearer new-token"
        finally:
            dlg.close()

    def test_accept_clears_webhook_auth_when_remove_checked(self, qapp):
        dlg = SettingsDialog(
            AppSettings(alert_webhook_auth_header="Bearer remove-me"),
        )
        try:
            dlg.alert_webhook_auth_clear_check.setChecked(True)
            dlg.accept()
            assert dlg.get_settings().alert_webhook_auth_header is None
        finally:
            dlg.close()

    def test_accept_persists_webhook_url(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.alert_webhook_url_edit.setText("https://hooks.example.com/alert")
            dlg.accept()
            assert (
                dlg.get_settings().alert_webhook_url == "https://hooks.example.com/alert"
            )
        finally:
            dlg.close()


class TestSettingsDialogBindAddressValidation:
    @patch("pypost.ui.dialogs.settings_dialog.show_invalid_bind_address")
    def test_accept_blocks_save_on_invalid_mcp_host(
        self,
        mock_show_invalid,
        qapp,
        caplog,
    ):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.mcp_host_edit.setText("not a host!")
            with caplog.at_level(
                logging.WARNING,
                logger="pypost.ui.dialogs.settings_dialog",
            ):
                dlg.accept()
            assert dlg.new_settings is None
            mock_show_invalid.assert_called_once()
            assert mock_show_invalid.call_args.args[0] is dlg
            assert "valid IP address" in mock_show_invalid.call_args.args[1]
            assert any(
                "bind_address_settings_validation_failed" in record.message
                and "reason=invalid_format" in record.message
                for record in caplog.records
            )
        finally:
            dlg.close()

    @patch("pypost.ui.dialogs.settings_dialog.show_invalid_bind_address")
    def test_accept_blocks_save_on_empty_metrics_host(
        self,
        mock_show_invalid,
        qapp,
    ):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.metrics_host_edit.setText("   ")
            dlg.accept()
            assert dlg.new_settings is None
            mock_show_invalid.assert_called_once()
            assert "cannot be empty" in mock_show_invalid.call_args.args[1]
        finally:
            dlg.close()

    def test_accept_persists_valid_bind_addresses(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.mcp_host_edit.setText("0.0.0.0")
            dlg.mcp_port_spin.setValue(2080)
            dlg.metrics_host_edit.setText("127.0.0.1")
            dlg.metrics_port_spin.setValue(9081)
            dlg.accept()
            settings = dlg.get_settings()
            assert settings.mcp_host == "0.0.0.0"
            assert settings.mcp_port == 2080
            assert settings.metrics_host == "127.0.0.1"
            assert settings.metrics_port == 9081
        finally:
            dlg.close()


class TestSettingsDialogRetryableCodesValidation:
    @pytest.mark.parametrize(
        "codes,expected_reason,message_fragment",
        [
            ("500,abc", "invalid_token", "whole number"),
            ("500,", "empty_segment", "empty entries"),
            ("99", "out_of_range", "100 and 599"),
        ],
    )
    @patch("pypost.ui.dialogs.settings_dialog.show_invalid_retryable_status_codes")
    def test_accept_blocks_save_and_shows_warning_on_invalid_codes(
        self,
        mock_show_invalid,
        codes,
        expected_reason,
        message_fragment,
        qapp,
        caplog,
    ):
        dlg = SettingsDialog(AppSettings())
        try:
            dlg.retryable_codes_edit.setText(codes)
            with caplog.at_level(
                logging.WARNING,
                logger="pypost.ui.dialogs.settings_dialog",
            ):
                dlg.accept()
            assert dlg.new_settings is None
            mock_show_invalid.assert_called_once()
            assert mock_show_invalid.call_args.args[0] is dlg
            message = mock_show_invalid.call_args.args[1]
            assert message_fragment in message
            assert any(
                "retryable_codes_settings_validation_failed" in record.message
                and f"reason={expected_reason}" in record.message
                for record in caplog.records
            )
        finally:
            dlg.close()


class TestResolveWebhookAuthHeader:
    def test_returns_none_when_clear_requested(self):
        assert _resolve_webhook_auth_header(
            "",
            had_stored_auth=True,
            stored_auth="Bearer old",
            clear_requested=True,
        ) is None

    def test_returns_entered_value_when_non_empty(self):
        assert _resolve_webhook_auth_header(
            "Bearer new",
            had_stored_auth=True,
            stored_auth="Bearer old",
            clear_requested=False,
        ) == "Bearer new"

    def test_keeps_stored_when_empty_and_had_auth(self):
        assert _resolve_webhook_auth_header(
            "",
            had_stored_auth=True,
            stored_auth="Bearer old",
            clear_requested=False,
        ) == "Bearer old"

    def test_returns_none_when_empty_and_no_stored_auth(self):
        assert _resolve_webhook_auth_header(
            "",
            had_stored_auth=False,
            stored_auth=None,
            clear_requested=False,
        ) is None
