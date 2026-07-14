"""Background worker for encryption migration operations (PYPOST-642)."""

from __future__ import annotations

import logging
from typing import Literal

from PySide6.QtCore import QThread, Signal

from pypost.core.encryption_migration import EncryptionMigrationService
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

MigrationOperation = Literal["re_encrypt", "encrypt_plaintext"]


class EncryptionMigrationWorker(QThread):
    """Runs bulk migration off the Qt UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service: EncryptionMigrationService,
        operation: MigrationOperation,
        settings: AppSettings,
    ) -> None:
        super().__init__()
        self._service = service
        self._operation = operation
        self._settings = settings

    def run(self) -> None:
        logger.info("encryption_migration_worker_started operation=%s", self._operation)
        try:
            if self._operation == "re_encrypt":
                report = self._service.bulk_re_encrypt(
                    self._settings,
                    backup=True,
                )
            else:
                report = self._service.encrypt_plaintext_hidden(
                    self._settings,
                    backup=True,
                )
            logger.info(
                "encryption_migration_worker_completed operation=%s success=%s",
                self._operation,
                report.success,
            )
            self.finished.emit(report)
        except Exception as exc:
            logger.error(
                "encryption_migration_worker_failed operation=%s error=%s",
                self._operation,
                exc,
                exc_info=True,
            )
            self.failed.emit(str(exc))
