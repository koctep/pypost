"""Tests for EnvironmentStorageGateway queue and coalescing."""

import pytest

pytestmark = pytest.mark.timeout(120)

import unittest
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.models.models import Environment


class TestEnvironmentStorageGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_env(self, name: str) -> Environment:
        return Environment(name=name, variables={"A": "1"})

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
        expected = [self._make_env("Prod")]
        storage.load_environments.return_value = expected
        gateway = EnvironmentStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        self._process_until(lambda: spy.count() == 1)
        self.assertEqual(spy.at(0)[0], expected)

    def test_save_async_emits_save_completed(self):
        storage = MagicMock()
        gateway = EnvironmentStorageGateway(storage)
        spy = QSignalSpy(gateway.save_completed)
        envs = [self._make_env("Staging")]
        gateway.save_async(envs)
        self._process_until(lambda: spy.count() == 1)
        storage.save_environments.assert_called_once()
        saved = storage.save_environments.call_args[0][0]
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].name, "Staging")

    def test_save_coalesces_pending_payload_while_busy(self):
        gateway = EnvironmentStorageGateway(MagicMock())
        gateway._worker = MagicMock()
        gateway._worker.isRunning.return_value = True
        first = [self._make_env("First")]
        second = [self._make_env("Second")]
        gateway.save_async(first)
        gateway.save_async(second)
        self.assertIsNotNone(gateway._pending_save)
        self.assertEqual(gateway._pending_save[0].name, "Second")

    def test_queued_load_runs_after_save(self):
        storage = MagicMock()
        storage.load_environments.return_value = [self._make_env("Loaded")]
        gateway = EnvironmentStorageGateway(storage)
        load_spy = QSignalSpy(gateway.load_completed)
        save_spy = QSignalSpy(gateway.save_completed)
        gateway.save_async([self._make_env("Save")])
        gateway.load_async()
        self._process_until(lambda: save_spy.count() == 1 and load_spy.count() == 1)
        self.assertEqual(save_spy.count(), 1)
        self.assertEqual(load_spy.count(), 1)

    def test_is_busy_false_when_idle(self):
        gateway = EnvironmentStorageGateway(MagicMock())
        self.assertFalse(gateway.is_busy())

    def test_has_pending_work_false_when_idle(self):
        gateway = EnvironmentStorageGateway(MagicMock())
        self.assertFalse(gateway.has_pending_work())

    def test_has_pending_work_true_when_queued_save(self):
        gateway = EnvironmentStorageGateway(MagicMock())
        gateway._worker = MagicMock()
        gateway._worker.isRunning.return_value = True
        gateway.save_async([self._make_env("Queued")])
        self.assertTrue(gateway.has_pending_work())

    def test_wait_idle_returns_immediately_when_idle(self):
        gateway = EnvironmentStorageGateway(MagicMock())
        self.assertTrue(gateway.wait_idle())

    def test_wait_idle_waits_for_running_worker(self):
        storage = MagicMock()
        expected = [self._make_env("Prod")]
        storage.load_environments.return_value = expected
        gateway = EnvironmentStorageGateway(storage)
        spy = QSignalSpy(gateway.load_completed)
        gateway.load_async()
        self.assertTrue(gateway.wait_idle())
        self._process_until(lambda: spy.count() == 1)
        self.assertFalse(gateway.has_pending_work())
