"""Tests for CollectionStorageWorker."""

import pytest

pytestmark = pytest.mark.timeout(120)

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QSignalSpy

from pypost.core.collection_storage_worker import CollectionStorageWorker
from pypost.models.models import Collection


class TestCollectionStorageWorker(unittest.TestCase):
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

    def test_load_emits_finished_with_collections(self):
        storage = MagicMock()
        expected = [Collection(name="API", requests=[])]
        storage.load_collections.return_value = expected
        worker = CollectionStorageWorker(storage)
        spy = QSignalSpy(worker.load_finished)
        worker.start()
        self._process_until(lambda: spy.count() == 1)
        self.assertEqual(spy.at(0)[0], expected)

    def test_load_emits_failed_on_unexpected_exception(self):
        storage = MagicMock()
        storage.load_collections.side_effect = OSError("read failed")
        worker = CollectionStorageWorker(storage)
        spy = QSignalSpy(worker.load_failed)
        worker.start()
        self._process_until(lambda: spy.count() == 1)
