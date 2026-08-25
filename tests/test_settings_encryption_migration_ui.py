"""Settings UI for encryption migration verify and re-encrypt (PYPOST-527)."""

import logging
from collections.abc import Callable
from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication

from pypost.core.encryption_migration import MigrationReport, ReencryptStats
from pypost.core.storage import StorageManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from tests.helpers.process_until import (
    format_storage_async_timeout_detail,
    process_until,
)

pytestmark = pytest.mark.timeout(120)


class _FakeSignal:
    def __init__(self) -> None:
        self._callbacks: list[Callable[..., object]] = []

    def connect(self, callback: Callable[..., object]) -> None:
        self._callbacks.append(callback)

    def emit(self, *args: object) -> None:
        callbacks = self._callbacks
        self._callbacks = []
        for callback in callbacks:
            callback(*args)


class _DeterministicMigrationWorker:
    def __init__(
        self,
        report: MigrationReport,
        retained_check: Callable[[], bool],
        result_requested_check: Callable[[], bool],
        *,
        wait_result: bool = True,
    ) -> None:
        self.succeeded = _FakeSignal()
        self.failed = _FakeSignal()
        self.finished = _FakeSignal()
        self._report = report
        self._retained_check = retained_check
        self._result_requested_check = result_requested_check
        self._wait_result = wait_result
        self.operation = "re_encrypt"
        self.retained_after_success: bool | None = None
        self.result_requested_after_success: bool | None = None
        self.delete_later_called = False

    def start(self) -> None:
        self.succeeded.emit(self._report)
        self.result_requested_after_success = self._result_requested_check()
        self.retained_after_success = self._retained_check()
        self.finished.emit()

    def deleteLater(self) -> None:
        self.delete_later_called = True

    def wait(self, timeout_ms: int) -> bool:
        return self._wait_result


def _wait_for_migration_worker(dlg: SettingsDialog, timeout_ms: int = 5_000) -> None:
    def timeout_detail() -> str:
        worker = dlg._migration_worker
        operation = getattr(worker, "operation", None) if worker is not None else None
        return format_storage_async_timeout_detail(
            worker_running=worker.isRunning() if worker is not None else False,
            worker_operation=operation if isinstance(operation, str) else None,
        )

    process_until(
        lambda: dlg._migration_worker is None,
        timeout_ms=timeout_ms,
        timeout_detail=timeout_detail,
    )


def _close_dialog(dlg: SettingsDialog) -> None:
    dlg.close()
    dlg.deleteLater()
    QCoreApplication.sendPostedEvents(dlg, QEvent.Type.DeferredDelete)


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
            assert dlg.form_layout_index_of(dlg.encryption_migration_section_label) >= 0
            assert dlg.form_layout_index_of(dlg.verify_encryption_btn) >= 0
            assert dlg.form_layout_index_of(dlg.reencrypt_environments_btn) >= 0
            assert dlg.form_layout_index_of(dlg.encrypt_plaintext_btn) >= 0
            assert dlg.verify_encryption_btn.isEnabled()
            assert dlg.reencrypt_environments_btn.isEnabled()
            assert dlg.encrypt_plaintext_btn.isEnabled()
        finally:
            _close_dialog(dlg)

    def test_migration_buttons_disabled_without_storage(self, qapp):
        dlg = SettingsDialog(AppSettings())
        try:
            assert not dlg.verify_encryption_btn.isEnabled()
            assert not dlg.reencrypt_environments_btn.isEnabled()
            assert not dlg.encrypt_plaintext_btn.isEnabled()
        finally:
            _close_dialog(dlg)

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_re_encrypt_environments",
        return_value=True,
    )
    def test_migration_worker_is_retained_until_thread_completion(
        self,
        mock_confirm: MagicMock,
        mock_show: MagicMock,
        qapp: QApplication,
    ) -> None:
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        worker = _DeterministicMigrationWorker(
            _empty_report(),
            lambda: dlg._migration_worker is worker,
            lambda: mock_show.called,
        )
        try:
            with patch(
                "pypost.ui.widgets.settings.encryption_migration_section."
                "EncryptionMigrationWorker",
                return_value=worker,
            ):
                dlg._on_re_encrypt_environments()

            assert worker.result_requested_after_success is True
            assert worker.retained_after_success is True
            assert dlg._migration_worker is None
            assert worker.delete_later_called is True
            mock_confirm.assert_called_once()
            mock_show.assert_called_once()
            assert dlg.verify_encryption_btn.isEnabled()
            assert dlg.reencrypt_environments_btn.isEnabled()
            assert dlg.encrypt_plaintext_btn.isEnabled()
        finally:
            _close_dialog(dlg)

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    @patch(
        "pypost.ui.dialogs.settings_dialog.confirm_re_encrypt_environments",
        return_value=True,
    )
    def test_migration_worker_logs_bounded_cleanup_timeout(
        self,
        mock_confirm: MagicMock,
        mock_show: MagicMock,
        qapp: QApplication,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        worker = _DeterministicMigrationWorker(
            _empty_report(),
            lambda: dlg._migration_worker is worker,
            lambda: mock_show.called,
            wait_result=False,
        )
        try:
            with (
                patch(
                    "pypost.ui.widgets.settings.encryption_migration_section."
                    "EncryptionMigrationWorker",
                    return_value=worker,
                ),
                caplog.at_level(
                    logging.WARNING,
                    logger="pypost.ui.dialogs.settings_dialog",
                ),
            ):
                dlg._on_re_encrypt_environments()

            assert any(
                record.getMessage()
                == (
                    "settings_encryption_migration_worker_finish_wait_timeout "
                    "wait_ms=100 operation=re_encrypt"
                )
                for record in caplog.records
            )
            assert dlg._migration_worker is None
            assert dlg.reencrypt_environments_btn.isEnabled()
        finally:
            _close_dialog(dlg)

    @patch("pypost.ui.dialogs.settings_dialog.show_migration_result")
    def test_verify_delegates_to_migration_service(self, mock_show, qapp):
        storage = MagicMock(spec=StorageManager)
        dlg = SettingsDialog(AppSettings(env_encryption_enabled=True), storage=storage)
        service = dlg._migration_service
        service.verify_decrypt_access = MagicMock(return_value=_empty_report())
        try:
            dlg._on_verify_encryption()
        finally:
            _close_dialog(dlg)

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
            _close_dialog(dlg)

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
            _close_dialog(dlg)

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
            _close_dialog(dlg)

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
            _close_dialog(dlg)

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
            _close_dialog(dlg)

        mock_show.assert_called_once()
        assert mock_show.call_args.kwargs["success"] is False
