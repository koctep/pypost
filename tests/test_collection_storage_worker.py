"""Tests for CollectionStorageWorker."""

import unittest
from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.collection_storage_worker import CollectionStorageWorker
from pypost.models.models import Collection
from tests.helpers.process_until import (
    format_storage_async_timeout_detail,
    process_until,
)

pytestmark = pytest.mark.timeout(120)


def _worker_timeout_detail(worker: CollectionStorageWorker):
    def detail() -> str:
        return format_storage_async_timeout_detail(
            worker_running=worker.isRunning(),
        )

    return detail


@pytest.mark.usefixtures("qapp")
class TestCollectionStorageWorker(unittest.TestCase):
    def test_load_emits_finished_with_collections(self):
        storage = MagicMock()
        expected = [Collection(name="API", requests=[])]
        storage.load_collections.return_value = expected
        worker = CollectionStorageWorker(storage)
        spy = QSignalSpy(worker.load_finished)
        worker.start()
        process_until(
            lambda: spy.count() == 1,
            timeout_ms=5_000,
            timeout_detail=_worker_timeout_detail(worker),
        )
        self.assertEqual(spy.at(0)[0], expected)

    def test_load_emits_failed_on_unexpected_exception(self):
        storage = MagicMock()
        storage.load_collections.side_effect = OSError("read failed")
        worker = CollectionStorageWorker(storage)
        spy = QSignalSpy(worker.load_failed)
        worker.start()
        process_until(
            lambda: spy.count() == 1,
            timeout_ms=5_000,
            timeout_detail=_worker_timeout_detail(worker),
        )
