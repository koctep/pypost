"""Qt-level tests for SettingsDialog (request timeout visibility and persistence)."""


import pytest

pytestmark = pytest.mark.timeout(60)

from PySide6.QtWidgets import QApplication

from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog


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
            webhook_idx = dlg.form_layout.indexOf(dlg.alert_webhook_url_edit)
            auth_idx = dlg.form_layout.indexOf(dlg.alert_webhook_auth_edit)
            assert retry_idx < header_idx < hidden_idx < webhook_idx < auth_idx
        finally:
            dlg.close()
