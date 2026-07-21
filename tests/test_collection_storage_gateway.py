"""Tests for CollectionStorageGateway."""

import unittest
from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.models.models import Collection
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)


@pytest.mark.usefixtures("qapp")
class TestCollectionStorageGateway(unittest.TestCase):
    def test_load_async_emits_load_completed(self):
        storage = MagicMock()
        expected = [Collection(name="Prod", requests=[])]
        storage.load_collections.return_value = expected
        gateway = CollectionStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        process_until(
            lambda: spy.count() == 1,
            timeout_ms=5_000,
            timeout_detail=gateway_timeout_detail(gateway),
        )
        self.assertEqual(spy.at(0)[0], expected)

    def test_queued_load_runs_after_first_completes(self):
        storage = MagicMock()
        storage.load_collections.return_value = [Collection(name="Loaded", requests=[])]
        gateway = CollectionStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        gateway.load_async()
        process_until(
            lambda: spy.count() == 2,
            timeout_ms=5_000,
            timeout_detail=gateway_timeout_detail(gateway),
        )
        self.assertEqual(spy.count(), 2)

    def test_is_busy_false_when_idle(self):
        gateway = CollectionStorageGateway(MagicMock())
        self.assertFalse(gateway.is_busy())

    def test_has_pending_work_false_when_idle(self):
        gateway = CollectionStorageGateway(MagicMock())
        self.assertFalse(gateway.has_pending_work())
