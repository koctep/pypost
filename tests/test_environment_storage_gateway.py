"""Tests for EnvironmentStorageGateway queue and coalescing."""

from unittest.mock import MagicMock

import pytest
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.models.models import Environment
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)


def _make_env(name: str) -> Environment:
    return Environment(name=name, variables={"A": "1"})


def test_load_async_emits_load_completed(qapp):
    storage = MagicMock()
    expected = [_make_env("Prod")]
    storage.load_environments.return_value = expected
    gateway = EnvironmentStorageGateway(storage)
    spy = QSignalSpy(gateway.load_completed)
    gateway.load_async()
    process_until(
        lambda: spy.count() == 1,
        timeout_ms=5_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    assert spy.at(0)[0] == expected


def test_save_async_emits_save_completed(qapp):
    storage = MagicMock()
    gateway = EnvironmentStorageGateway(storage)
    spy = QSignalSpy(gateway.save_completed)
    envs = [_make_env("Staging")]
    gateway.save_async(envs)
    process_until(
        lambda: spy.count() == 1,
        timeout_ms=5_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    storage.save_environments.assert_called_once()
    saved = storage.save_environments.call_args[0][0]
    assert len(saved) == 1
    assert saved[0].name == "Staging"


def test_save_coalesces_pending_payload_while_busy(qapp):
    gateway = EnvironmentStorageGateway(MagicMock())
    gateway._worker = MagicMock()
    gateway._worker.isRunning.return_value = True
    first = [_make_env("First")]
    second = [_make_env("Second")]
    gateway.save_async(first)
    gateway.save_async(second)
    assert gateway._pending_save is not None
    assert gateway._pending_save[0].name == "Second"


def test_queued_load_runs_after_save(qapp):
    storage = MagicMock()
    storage.load_environments.return_value = [_make_env("Loaded")]
    gateway = EnvironmentStorageGateway(storage)
    load_spy = QSignalSpy(gateway.load_completed)
    save_spy = QSignalSpy(gateway.save_completed)
    gateway.save_async([_make_env("Save")])
    gateway.load_async()
    process_until(
        lambda: save_spy.count() == 1 and load_spy.count() == 1,
        timeout_ms=5_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    assert save_spy.count() == 1
    assert load_spy.count() == 1


def test_is_busy_false_when_idle(qapp):
    gateway = EnvironmentStorageGateway(MagicMock())
    assert not gateway.is_busy()


def test_has_pending_work_false_when_idle(qapp):
    gateway = EnvironmentStorageGateway(MagicMock())
    assert not gateway.has_pending_work()


def test_has_pending_work_true_when_queued_save(qapp):
    gateway = EnvironmentStorageGateway(MagicMock())
    gateway._worker = MagicMock()
    gateway._worker.isRunning.return_value = True
    gateway.save_async([_make_env("Queued")])
    assert gateway.has_pending_work()


def test_wait_idle_returns_immediately_when_idle(qapp):
    gateway = EnvironmentStorageGateway(MagicMock())
    assert gateway.wait_idle()


def test_wait_idle_waits_for_running_worker(qapp):
    storage = MagicMock()
    expected = [_make_env("Prod")]
    storage.load_environments.return_value = expected
    gateway = EnvironmentStorageGateway(storage)
    spy = QSignalSpy(gateway.load_completed)
    gateway.load_async()
    assert gateway.wait_idle()
    process_until(
        lambda: spy.count() == 1,
        timeout_ms=5_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    assert not gateway.has_pending_work()
