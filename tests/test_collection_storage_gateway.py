"""Tests for CollectionStorageGateway."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.models.models import Collection
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)


def test_load_async_emits_load_completed(qapp):
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
    assert spy.at(0)[0] == expected


def test_queued_load_runs_after_first_completes(qapp):
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
    assert spy.count() == 2


def test_is_busy_false_when_idle(qapp):
    gateway = CollectionStorageGateway(MagicMock())
    assert not gateway.is_busy()


def test_has_pending_work_false_when_idle(qapp):
    gateway = CollectionStorageGateway(MagicMock())
    assert not gateway.has_pending_work()
