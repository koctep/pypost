"""Integration tests for migration with keyring/secret_store primaries (PYPOST-531)."""


import pytest

import json
from unittest.mock import MagicMock, patch


from pypost.core.encryption_migration import EncryptionMigrationService
from pypost.core.key_provider import build_key_id
from pypost.core.key_sources.env import EnvKeySource
from pypost.core.key_sources.keyring import ACTIVE_ENTRY, SERVICE_NAME
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(120)


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv(EnvKeySource.KEYS_FILE, raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", raising=False)
    return StorageManager()


def _keyring_mock(entries: dict[str, str]) -> MagicMock:
    mock_keyring = MagicMock()

    def get_password(service: str, entry: str) -> str | None:
        if service != SERVICE_NAME:
            return None
        return entries.get(entry)

    mock_keyring.get_password.side_effect = get_password
    return mock_keyring


def _write_secret_store_spec(
    tmp_path,
    *,
    active_key: str,
    keys: dict[str, str],
    keys_file_name: str = "keys.json",
) -> str:
    active_id = build_key_id(active_key)
    keys_file = tmp_path / keys_file_name
    keys_file.write_text(
        json.dumps({"active_key_id": active_id, "keys": keys}),
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": keys,
                "backends": [{"type": "file", "path": str(keys_file)}],
            }
        ),
        encoding="utf-8",
    )
    return str(spec_path)


def _encrypt_with_env(
    storage: StorageManager,
    monkeypatch,
    key: str,
    *,
    secret_value: str = "value",
) -> str:
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": secret_value},
                hidden_keys={"SECRET"},
            )
        ]
    )
    return build_key_id(key)


def test_verify_keyring_primary_decrypts_env_encrypted_data(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    kid = _encrypt_with_env(storage, monkeypatch, key)

    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    mock_keyring = _keyring_mock({ACTIVE_ENTRY: key, kid: key})
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="keyring",
        env_encryption_key_source_fallback=["environment"],
    )

    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        storage.apply_encryption_settings(settings)
        report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is True
    assert report.errors == ()
    assert report.inventory.encrypted_envelope_count == 1


def test_bulk_re_encrypt_keyring_primary_rotates_active_kid(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_id = _encrypt_with_env(storage, monkeypatch, historical_key)
    active_id = build_key_id(active_key)

    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    mock_keyring = _keyring_mock(
        {
            ACTIVE_ENTRY: active_key,
            historical_id: historical_key,
        }
    )
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="keyring",
        env_encryption_key_source_fallback=["environment"],
    )

    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        storage.apply_encryption_settings(settings)
        service = EncryptionMigrationService(storage)
        report = service.bulk_re_encrypt(settings, dry_run=False, backup=False)

    assert report.success is True
    final = service.build_inventory(settings)
    assert final.kid_histogram == {active_id: 1}


def test_verify_secret_store_primary_decrypts_env_encrypted_data(
    tmp_path, monkeypatch
):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    kid = _encrypt_with_env(storage, monkeypatch, key)

    spec_path = _write_secret_store_spec(tmp_path, active_key=key, keys={kid: key})
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", spec_path)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="secret_store",
        env_encryption_key_source_fallback=["environment"],
    )

    storage.apply_encryption_settings(settings)
    report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is True
    assert report.errors == ()
    assert report.inventory.encrypted_envelope_count == 1


def test_bulk_re_encrypt_secret_store_primary_rotates_active_kid(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_id = _encrypt_with_env(storage, monkeypatch, historical_key)
    active_id = build_key_id(active_key)

    spec_path = _write_secret_store_spec(
        tmp_path,
        active_key=active_key,
        keys={active_id: active_key, historical_id: historical_key},
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", spec_path)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="secret_store",
        env_encryption_key_source_fallback=["environment"],
    )

    storage.apply_encryption_settings(settings)
    service = EncryptionMigrationService(storage)
    report = service.bulk_re_encrypt(settings, dry_run=False, backup=False)

    assert report.success is True
    final = service.build_inventory(settings)
    assert final.kid_histogram == {active_id: 1}
