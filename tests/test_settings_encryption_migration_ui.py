"""Settings UI for encryption migration verify and re-encrypt (PYPOST-527)."""


import pytest

pytestmark = pytest.mark.timeout(120)

from dataclasses import replace
import time
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.core.encryption_migration import MigrationReport, ReencryptStats
from pypost.core.storage import StorageManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _wait_for_migration_worker(dlg, timeout_s: float = 5.0) -> None:
    deadline = time.time() + timeout_s
    while dlg._migration_worker is not None and time.time() < deadline:
        QCoreApplication.processEvents()
        QTest.qWait(10)


def _empty_report(*, success: bool = True) -> MigrationReport:
    from pypost.core.encryption_migration import EnvironmentInventory

    inventory = EnvironmentInventory(
        environment_count=0,
        hidden_value_count=0,
        encrypted_envelope_count=0,
        v1_envelope_count=0,
        v2_envelope_count=0,
        plaintext_hidden_count=0,
        invalid_hidden_count=0,
        kid_histogram={},
        missing_kids=frozenset(),
        data_quality_errors=(),
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
            assert dlg.form_layout.indexOf(dlg.encrypt_plaintext_btn) >= 0
            assert dlg.verify_encryption_btn.isEnabled()
            assert dlg.reencrypt_environments_btn.isEnabled()
            assert dlg.encrypt_plaintext_btn.isEnabled()
        finally:
            dlg.close()

    def test_migration_buttons_disabled_without_storage(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert not dlg.verify_encryption_btn.isEnabled()
            assert not dlg.reencrypt_environments_btn.isEnabled()
            assert not dlg.encrypt_plaintext_btn.isEnabled()
        finally:
            dlg.close()

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    def test_verify_delegates_to_migration_service(self, mock_show, qapp):
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
        mock_show.assert_called_once()
        assert mock_show.call_args.kwargs["success"] is True

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_re_encrypt_environments",
        return_value=False,
    )
    def test_reencrypt_skipped_when_not_confirmed(self, mock_confirm, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.bulk_re_encrypt = MagicMock()
        try:
            dlg._on_re_encrypt_environments()
        finally:
            dlg.close()

        service.bulk_re_encrypt.assert_not_called()
        mock_show.assert_not_called()

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_re_encrypt_environments",
        return_value=True,
    )
    def test_reencrypt_runs_when_confirmed(self, mock_confirm, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.bulk_re_encrypt = MagicMock(return_value=_empty_report())
        try:
            dlg._on_re_encrypt_environments()
            _wait_for_migration_worker(dlg)
        finally:
            dlg.close()

        service.bulk_re_encrypt.assert_called_once()
        call_kwargs = service.bulk_re_encrypt.call_args.kwargs
        assert call_kwargs["backup"] is True
        mock_show.assert_called_once()

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_encrypt_plaintext_hidden",
        return_value=True,
    )
    def test_encrypt_plaintext_runs_when_confirmed(self, mock_confirm, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.encrypt_plaintext_hidden = MagicMock(return_value=_empty_report())
        try:
            dlg._on_encrypt_plaintext_hidden()
            _wait_for_migration_worker(dlg)
        finally:
            dlg.close()

        service.encrypt_plaintext_hidden.assert_called_once()
        call_kwargs = service.encrypt_plaintext_hidden.call_args.kwargs
        assert call_kwargs["backup"] is True
        mock_show.assert_called_once()

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_re_encrypt_environments",
        return_value=True,
    )
    def test_reencrypt_shows_reencrypt_stats(self, mock_confirm, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        report = replace(
            _empty_report(),
            reencrypt_stats=ReencryptStats(encrypted_count=2, reused_count=1),
        )
        service.bulk_re_encrypt = MagicMock(return_value=report)
        try:
            dlg._on_re_encrypt_environments()
            _wait_for_migration_worker(dlg)
        finally:
            dlg.close()

        mock_show.assert_called_once()
        body = mock_show.call_args[0][2]
        assert "Re-encrypted: 2" in body
        assert "Reused: 1" in body

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    def test_verify_shows_warning_on_failure(self, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(), storage=storage)
        dlg._migration_service.verify_decrypt_access = MagicMock(
            return_value=_empty_report(success=False),
        )
        try:
            dlg._on_verify_encryption()
        finally:
            dlg.close()

        mock_show.assert_called_once()
        assert mock_show.call_args.kwargs["success"] is False
