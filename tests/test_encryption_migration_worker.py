"""Direct tests for EncryptionMigrationWorker (PYPOST-724)."""

from __future__ import annotations

import logging
import unittest
from unittest.mock import MagicMock

import pytest

from pypost.core.encryption_migration import (
    EnvironmentInventory,
    MigrationReport,
)
from pypost.core.qt.encryption_migration_worker import EncryptionMigrationWorker
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(30)


def _empty_report(*, success: bool = True) -> MigrationReport:
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


class TestEncryptionMigrationWorker(unittest.TestCase):
    def test_re_encrypt_emits_succeeded_with_report(self) -> None:
        service = MagicMock()
        report = _empty_report()
        service.bulk_re_encrypt.return_value = report
        settings = AppSettings()
        worker = EncryptionMigrationWorker(service, "re_encrypt", settings)
        succeeded: list[MigrationReport] = []
        worker.succeeded.connect(succeeded.append)
        worker.run()
        self.assertEqual(succeeded, [report])
        service.bulk_re_encrypt.assert_called_once_with(settings, backup=True)

    def test_encrypt_plaintext_emits_succeeded_with_report(self) -> None:
        service = MagicMock()
        report = _empty_report()
        service.encrypt_plaintext_hidden.return_value = report
        settings = AppSettings()
        worker = EncryptionMigrationWorker(service, "encrypt_plaintext", settings)
        succeeded: list[MigrationReport] = []
        worker.succeeded.connect(succeeded.append)
        worker.run()
        self.assertEqual(succeeded, [report])
        service.encrypt_plaintext_hidden.assert_called_once_with(settings, backup=True)

    def test_run_emits_failed_on_service_exception(self) -> None:
        service = MagicMock()
        service.bulk_re_encrypt.side_effect = RuntimeError("migration failed")
        worker = EncryptionMigrationWorker(service, "re_encrypt", AppSettings())
        succeeded: list[MigrationReport] = []
        failed: list[str] = []
        worker.succeeded.connect(succeeded.append)
        worker.failed.connect(failed.append)
        worker.run()
        self.assertEqual(failed, ["migration failed"])
        self.assertEqual(succeeded, [])

    def test_run_logs_error_on_failure(self) -> None:
        service = MagicMock()
        service.bulk_re_encrypt.side_effect = RuntimeError("migration failed")
        worker = EncryptionMigrationWorker(service, "re_encrypt", AppSettings())
        with self.assertLogs(
            "pypost.core.qt.encryption_migration_worker",
            level=logging.ERROR,
        ) as logs:
            worker.run()
        self.assertTrue(
            any("encryption_migration_worker_failed" in r.message for r in logs.records)
        )
