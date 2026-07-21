"""PYPOST-883 Probe C canary: QComboBox GC churn vs env save-completed wait.

Permanent cheap canary kept after Phase 2a close-with-evidence (hang
not_reproduced). Creates/destroys QComboBox widgets (presenter-like affinity),
schedules deleteLater, forces gc.collect between batches, and drives
EnvironmentStorageGateway save_async + process_until for >=200 save-completed
waits.

Not a classic red product assertion — regression signal if teardown vs worker
ordering later stalls under synthetic pressure (see 30-findings.md).
"""

from __future__ import annotations

import gc
import unittest
from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QComboBox, QWidget

from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.models.models import Environment
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)

# Architecture: >=200 save-completed waits with forced widget GC between batches.
_CYCLE_COUNT = 200
_BATCH_SIZE = 25
_WAIT_MS = 5_000


def _make_env(name: str) -> Environment:
    return Environment(name=name, variables={"A": "1"})


def _churn_combo_widgets() -> None:
    """Build/tear down QComboBox (+ parent) like EnvPresenter selector pressure."""
    parent = QWidget()
    combo = QComboBox(parent)
    combo.addItems(["Staging", "Prod", "Dev"])
    combo.setCurrentIndex(1)
    parent.deleteLater()
    combo.deleteLater()
    del combo
    del parent


@pytest.mark.usefixtures("qapp")
class TestPypost883SaveAsyncGcProbe(unittest.TestCase):
    def test_save_completed_survives_qcombobox_gc_churn(self):
        """>=200 save_async waits with QComboBox deleteLater + gc between batches."""
        storage = MagicMock()
        gateway = EnvironmentStorageGateway(storage)
        spy = QSignalSpy(gateway.save_completed)
        fail_spy = QSignalSpy(gateway.save_failed)

        for i in range(_CYCLE_COUNT):
            _churn_combo_widgets()
            gateway.save_async([_make_env(f"Probe-{i}")])
            process_until(
                lambda c=i + 1: spy.count() >= c or fail_spy.count() >= 1,
                timeout_ms=_WAIT_MS,
                timeout_detail=gateway_timeout_detail(gateway),
            )
            self.assertEqual(fail_spy.count(), 0, "unexpected save_failed")
            self.assertGreaterEqual(spy.count(), i + 1)

            if (i + 1) % _BATCH_SIZE == 0:
                self.assertFalse(gateway.is_busy())
                self.assertFalse(gateway.has_pending_work())
                gc.collect()

        self.assertEqual(spy.count(), _CYCLE_COUNT)
        self.assertFalse(gateway.is_busy())
        self.assertFalse(gateway.has_pending_work())
