"""Encryption migration actions section (verify, re-encrypt, encrypt plaintext)."""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QFormLayout, QPushButton, QWidget

from pypost.core.encryption_migration import (
    EncryptionMigrationService,
    MigrationReport,
    format_migration_report,
)
from pypost.core.encryption_migration_worker import EncryptionMigrationWorker
from pypost.core.storage_interface import StorageInterface
from pypost.models.settings import AppSettings
from pypost.ui.widgets.settings._common import make_section_header

if TYPE_CHECKING:
    from pypost.ui.widgets.settings.encryption_config_section import (
        EncryptionConfigSection,
    )

logger = logging.getLogger("pypost.ui.dialogs.settings_dialog")


class EncryptionMigrationSection:
    def __init__(
        self,
        parent: QWidget,
        *,
        storage: StorageInterface | None,
        migration_service: EncryptionMigrationService | None,
        encryption_config: "EncryptionConfigSection",
        current_settings: AppSettings,
        show_migration_result: Callable[..., None],
        confirm_re_encrypt_environments: Callable[[QWidget], bool],
        confirm_encrypt_plaintext_hidden: Callable[[QWidget], bool],
        host_dialog: QWidget,
    ) -> None:
        self._parent = parent
        self._encryption_config = encryption_config
        self._current_settings = current_settings
        self._show_migration_result_fn = show_migration_result
        self._confirm_re_encrypt = confirm_re_encrypt_environments
        self._confirm_encrypt_plaintext = confirm_encrypt_plaintext_hidden
        self._host_dialog = host_dialog

        if migration_service is not None:
            self._migration_service = migration_service
        elif storage is not None:
            self._migration_service = EncryptionMigrationService(storage)
        else:
            self._migration_service = None

        self.encryption_migration_section_label = make_section_header(
            "Encryption migration",
        )
        self.verify_encryption_btn = QPushButton("Verify encryption", parent)
        self.verify_encryption_btn.clicked.connect(self.on_verify_encryption)
        self.reencrypt_environments_btn = QPushButton(
            "Re-encrypt all environments",
            parent,
        )
        self.reencrypt_environments_btn.clicked.connect(self.on_re_encrypt_environments)
        self.encrypt_plaintext_btn = QPushButton(
            "Encrypt plaintext hidden values",
            parent,
        )
        self.encrypt_plaintext_btn.clicked.connect(self.on_encrypt_plaintext_hidden)

        migration_enabled = self._migration_service is not None
        self.verify_encryption_btn.setEnabled(migration_enabled)
        self.reencrypt_environments_btn.setEnabled(migration_enabled)
        self.encrypt_plaintext_btn.setEnabled(migration_enabled)

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow(self.encryption_migration_section_label)
        form.addRow("", self.verify_encryption_btn)
        form.addRow("", self.reencrypt_environments_btn)
        form.addRow("", self.encrypt_plaintext_btn)

    @property
    def migration_worker(self) -> EncryptionMigrationWorker | None:
        return self._host_dialog._migration_worker

    @migration_worker.setter
    def migration_worker(self, worker: EncryptionMigrationWorker | None) -> None:
        self._host_dialog._migration_worker = worker

    def encryption_settings_from_form(self) -> AppSettings:
        return self._encryption_config.encryption_settings_from_form(self._current_settings)

    def on_verify_encryption(self) -> None:
        if self._migration_service is None:
            return
        settings = self.encryption_settings_from_form()
        logger.info("settings_encryption_verify_started")
        report = self._migration_service.verify_decrypt_access(settings)
        logger.info(
            "settings_encryption_verify_completed success=%s error_count=%d",
            report.success,
            len(report.errors),
        )
        self._show_migration_result("Verify encryption", report)

    def on_re_encrypt_environments(self) -> None:
        self._start_migration_worker(
            "re_encrypt",
            title="Re-encrypt all environments",
            confirm=self._confirm_re_encrypt,
        )

    def on_encrypt_plaintext_hidden(self) -> None:
        self._start_migration_worker(
            "encrypt_plaintext",
            title="Encrypt plaintext hidden values",
            confirm=self._confirm_encrypt_plaintext,
        )

    def _show_migration_result(self, title: str, report: MigrationReport) -> None:
        body = format_migration_report(report)
        self._show_migration_result_fn(
            self._parent,
            title,
            body,
            success=report.success,
        )

    def _set_migration_buttons_enabled(self, enabled: bool) -> None:
        has_service = self._migration_service is not None
        for button in (
            self.verify_encryption_btn,
            self.reencrypt_environments_btn,
            self.encrypt_plaintext_btn,
        ):
            button.setEnabled(enabled and has_service)

    def _start_migration_worker(
        self,
        operation: str,
        *,
        title: str,
        confirm: Callable[[QWidget], bool],
    ) -> None:
        if self._migration_service is None or self.migration_worker is not None:
            return
        if not confirm(self._parent):
            logger.info("settings_encryption_%s_cancelled", operation)
            return
        settings = self.encryption_settings_from_form()
        logger.info("settings_encryption_%s_started", operation)
        worker = EncryptionMigrationWorker(self._migration_service, operation, settings)
        worker.finished.connect(
            lambda report, op=operation, result_title=title: self._on_migration_worker_finished(
                op,
                result_title,
                report,
            )
        )
        worker.failed.connect(self._on_migration_worker_failed)
        self.migration_worker = worker
        self._set_migration_buttons_enabled(False)
        worker.start()

    def _on_migration_worker_finished(
        self,
        operation: str,
        title: str,
        report: MigrationReport,
    ) -> None:
        self.migration_worker = None
        self._set_migration_buttons_enabled(True)
        logger.info(
            "settings_encryption_%s_completed success=%s backup=%s error_count=%d",
            operation,
            report.success,
            report.backup_path,
            len(report.errors),
        )
        self._show_migration_result(title, report)

    def _on_migration_worker_failed(self, message: str) -> None:
        self.migration_worker = None
        self._set_migration_buttons_enabled(True)
        logger.error("settings_encryption_migration_worker_failed error=%s", message)
        self._show_migration_result_fn(
            self._parent,
            "Encryption migration",
            f"Migration failed: {message}",
            success=False,
        )
