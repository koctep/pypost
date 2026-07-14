"""Tests for CollectionStorageGateway."""

import pytest

pytestmark = pytest.mark.timeout(120)

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.models.models import Collection


class TestCollectionStorageGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _process_until(self, predicate, timeout_ms: int = 5000) -> None:
        loop = QEventLoop()
        elapsed = [0]

        def tick():
            elapsed[0] += 10
            if predicate() or elapsed[0] >= timeout_ms:
                loop.quit()

        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(tick)
        timer.start()
        loop.exec()
        timer.stop()
        self.assertTrue(predicate())

    def test_load_async_emits_load_completed(self):
        storage = MagicMock()
        expected = [Collection(name="Prod", requests=[])]
        storage.load_collections.return_value = expected
        gateway = CollectionStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        self._process_until(lambda: spy.count() == 1)
        self.assertEqual(spy.at(0)[0], expected)

    def test_queued_load_runs_after_first_completes(self):
        storage = MagicMock()
        storage.load_collections.return_value = [Collection(name="Loaded", requests=[])]
        gateway = CollectionStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        gateway.load_async()
        self._process_until(lambda: spy.count() == 2)
        self.assertEqual(spy.count(), 2)

    def test_is_busy_false_when_idle(self):
        gateway = CollectionStorageGateway(MagicMock())
        self.assertFalse(gateway.is_busy())

    def test_has_pending_work_false_when_idle(self):
        gateway = CollectionStorageGateway(MagicMock())
        self.assertFalse(gateway.has_pending_work())
