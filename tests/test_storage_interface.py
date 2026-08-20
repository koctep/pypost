"""Tests for StorageInterface and StorageManager compliance."""

import pytest

from unittest.mock import MagicMock

from pypost.core.request_manager import RequestManager
from pypost.core.storage import StorageManager
from pypost.core.storage_interface import StorageInterface
from tests.helpers import FakeStorageManager

pytestmark = pytest.mark.timeout(10)


def test_storage_manager_satisfies_protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda *args, **kwargs: str(tmp_path),
    )
    assert isinstance(StorageManager(), StorageInterface)


def test_fake_storage_manager_satisfies_protocol():
    assert isinstance(FakeStorageManager(), StorageInterface)


def test_magic_mock_can_stand_in_for_storage_interface():
    mock = MagicMock(spec=StorageInterface)
    manager = RequestManager(mock)
    assert isinstance(manager.storage, StorageInterface)


def test_request_manager_default_storage_is_storage_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda *args, **kwargs: str(tmp_path),
    )
    manager = RequestManager(StorageManager())
    assert isinstance(manager.storage, StorageInterface)
