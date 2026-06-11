"""Integration tests for migration with Vault secret-store backend (PYPOST-543)."""


import pytest

pytestmark = pytest.mark.timeout(120)

import json
from unittest.mock import MagicMock, patch

from pypost.core.encryption_migration import EncryptionMigrationService
from pypost.core.key_provider import build_key_id
from pypost.core.key_sources.env import EnvKeySource
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings

VAULT_URL = "https://vault.example/v1/secret/data/pypost"


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv(EnvKeySource.KEYS_FILE, raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", raising=False)
    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    return StorageManager()


def _vault_kv_v2_payload(active_key_id: str, keys: dict[str, str]) -> dict:
    return {
        "data": {
            "data": {
                "active_key_id": active_key_id,
                "keys": keys,
            },
        },
    }


def _write_vault_secret_store_spec(
    tmp_path,
    *,
    active_key: str,
    keys: dict[str, str],
) -> str:
    active_id = build_key_id(active_key)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": keys,
                "backends": [{"type": "vault", "url": VAULT_URL}],
            }
        ),
        encoding="utf-8",
    )
    return str(spec_path)


def _mock_vault_response(active_key_id: str, keys: dict[str, str]) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = _vault_kv_v2_payload(active_key_id, keys)
    mock_response.raise_for_status = MagicMock()
    return mock_response


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


def test_verify_vault_backend_primary_decrypts_env_encrypted_data(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    kid = _encrypt_with_env(storage, monkeypatch, key)

    spec_path = _write_vault_secret_store_spec(tmp_path, active_key=key, keys={kid: key})
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", spec_path)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="secret_store",
        env_encryption_key_source_fallback=["environment"],
    )

    mock_response = _mock_vault_response(kid, {kid: key})
    with patch(
        "pypost.core.key_sources.secret_store.requests.get",
        return_value=mock_response,
    ) as mock_get:
        storage.apply_encryption_settings(settings)
        report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is True
    assert report.errors == ()
    assert report.inventory.encrypted_envelope_count == 1
    assert mock_get.call_count >= 1
    for call in mock_get.call_args_list:
        assert call.kwargs["headers"]["X-Vault-Token"] == "test-token"
        assert call.args[0] == VAULT_URL


def test_bulk_re_encrypt_vault_backend_primary_rotates_active_kid(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_id = _encrypt_with_env(storage, monkeypatch, historical_key)
    active_id = build_key_id(active_key)

    spec_path = _write_vault_secret_store_spec(
        tmp_path,
        active_key=active_key,
        keys={active_id: active_key, historical_id: historical_key},
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", spec_path)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    settings = AppSettings(
        env_encryption_enabled=True,
        env_encryption_key_source="secret_store",
        env_encryption_key_source_fallback=["environment"],
    )

    mock_response = _mock_vault_response(
        active_id,
        {active_id: active_key, historical_id: historical_key},
    )
    with patch(
        "pypost.core.key_sources.secret_store.requests.get",
        return_value=mock_response,
    ):
        storage.apply_encryption_settings(settings)
        service = EncryptionMigrationService(storage)
        report = service.bulk_re_encrypt(settings, dry_run=False, backup=False)

    assert report.success is True
    final = service.build_inventory(settings)
    assert final.kid_histogram == {active_id: 1}
