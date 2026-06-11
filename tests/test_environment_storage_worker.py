"""Tests for EnvironmentStorageWorker."""

import unittest
from unittest.mock import MagicMock

from pypost.core.environment_storage_worker import EnvironmentStorageWorker
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.models.models import Environment


class TestEnvironmentStorageWorker(unittest.TestCase):
    def _make_env(self, name: str = "Dev") -> Environment:
        return Environment(name=name, variables={"KEY": "value"}, hidden_keys={"KEY"})

    def test_load_emits_finished_with_environments(self):
        storage = MagicMock()
        expected = [self._make_env()]
        storage.load_environments.return_value = expected
        worker = EnvironmentStorageWorker(storage, operation="load")
        received = []
        worker.load_finished.connect(received.append)
        worker.run()
        self.assertEqual(received, [expected])
        storage.load_environments.assert_called_once_with()

    def test_load_emits_failed_on_unexpected_exception(self):
        storage = MagicMock()
        storage.load_environments.side_effect = RuntimeError("read failed")
        worker = EnvironmentStorageWorker(storage, operation="load")
        received = []
        worker.load_failed.connect(received.append)
        worker.run()
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], RuntimeError)

    def test_save_emits_finished_on_success(self):
        storage = MagicMock()
        envs = [self._make_env()]
        worker = EnvironmentStorageWorker(storage, operation="save", environments=envs)
        finished = []
        worker.save_finished.connect(lambda: finished.append(True))
        worker.run()
        self.assertEqual(len(finished), 1)
        storage.save_environments.assert_called_once_with(envs)

    def test_save_emits_failed_on_encryption_error(self):
        storage = MagicMock()
        storage.save_environments.side_effect = EnvironmentEncryptionError(
            "Encryption key is unavailable."
        )
        worker = EnvironmentStorageWorker(
            storage,
            operation="save",
            environments=[self._make_env()],
        )
        received = []
        worker.save_failed.connect(received.append)
        worker.run()
        self.assertEqual(len(received), 1)
        self.assertIsInstance(received[0], EnvironmentEncryptionError)
