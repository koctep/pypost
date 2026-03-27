"""Qt-level tests for SettingsDialog (request timeout visibility and persistence)."""

import pytest
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
