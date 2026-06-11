"""Settings UI for encryption migration verify and re-encrypt (PYPOST-527)."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from pypost.core.encryption_migration import MigrationReport
from pypost.core.storage import StorageManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _empty_report(*, success: bool = True) -> MigrationReport:
    from pypost.core.encryption_migration import EnvironmentInventory

    inventory = EnvironmentInventory(
        environment_count=0,
        hidden_value_count=0,
        encrypted_envelope_count=0,
        plaintext_hidden_count=0,
        kid_histogram={},
        missing_kids=frozenset(),
    )
    return MigrationReport(
        inventory=inventory,
        dry_run=False,
        backup_path=None,
        errors=() if success else ("example error",),
        success=success,
    )


class TestSettingsDialogEncryptionMigration:
    def test_migration_buttons_on_form_with_storage(self, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(), storage=storage)
        try:
            assert dlg.form_layout.indexOf(dlg.encryption_migration_section_label) >= 0
            assert dlg.form_layout.indexOf(dlg.verify_encryption_btn) >= 0
            assert dlg.form_layout.indexOf(dlg.reencrypt_environments_btn) >= 0
            assert dlg.verify_encryption_btn.isEnabled()
            assert dlg.reencrypt_environments_btn.isEnabled()
        finally:
            dlg.close()

    def test_migration_buttons_disabled_without_storage(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert not dlg.verify_encryption_btn.isEnabled()
            assert not dlg.reencrypt_environments_btn.isEnabled()
        finally:
            dlg.close()

    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.information")
    def test_verify_delegates_to_migration_service(self, mock_info, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.verify_decrypt_access = MagicMock(return_value=_empty_report())
        try:
            dlg._on_verify_encryption()
        finally:
            dlg.close()

        service.verify_decrypt_access.assert_called_once()
        settings_arg = service.verify_decrypt_access.call_args[0][0]
        assert settings_arg.env_encryption_enabled is True
        mock_info.assert_called_once()

    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.question")
    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.information")
    def test_reencrypt_skipped_when_not_confirmed(self, mock_info, mock_question, qapp):
        mock_question.return_value = QMessageBox.StandardButton.No
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.bulk_re_encrypt = MagicMock()
        try:
            dlg._on_re_encrypt_environments()
        finally:
            dlg.close()

        service.bulk_re_encrypt.assert_not_called()
        mock_info.assert_not_called()

    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.question")
    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.information")
    def test_reencrypt_runs_when_confirmed(self, mock_info, mock_question, qapp):
        mock_question.return_value = QMessageBox.StandardButton.Yes
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.bulk_re_encrypt = MagicMock(return_value=_empty_report())
        try:
            dlg._on_re_encrypt_environments()
        finally:
            dlg.close()

        service.bulk_re_encrypt.assert_called_once()
        call_kwargs = service.bulk_re_encrypt.call_args.kwargs
        assert call_kwargs["backup"] is True
        mock_info.assert_called_once()

    @patch("pypost.ui.dialogs.settings_dialog.QMessageBox.warning")
    def test_verify_shows_warning_on_failure(self, mock_warning, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(), storage=storage)
        dlg._migration_service.verify_decrypt_access = MagicMock(
            return_value=_empty_report(success=False),
        )
        try:
            dlg._on_verify_encryption()
        finally:
            dlg.close()

        mock_warning.assert_called_once()
