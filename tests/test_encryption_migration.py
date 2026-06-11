"""Tests for encryption migration service (PYPOST-487)."""

import json

import pytest

from pypost.core.encryption_migration import (
    EncryptionMigrationService,
    backup_environments_file,
)
from pypost.core.key_provider import build_key_id
from pypost.core.key_sources.env import EnvKeySource
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv(EnvKeySource.KEYS_FILE, raising=False)
    return StorageManager()


def test_build_inventory_counts_plaintext_and_encrypted(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)

    encrypted_env = Environment(
        id="e1",
        name="Encrypted",
        variables={"SECRET": "hidden"},
        hidden_keys={"SECRET"},
    )
    storage.apply_encryption_settings(settings)
    storage.save_environments([encrypted_env])

    plain_payload = {
        "id": "e2",
        "name": "Plain",
        "variables": {"TOKEN": "plain"},
        "hidden_keys": ["TOKEN"],
        "enable_mcp": False,
    }
    with open(storage.environments_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.append(plain_payload)
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    service = EncryptionMigrationService(storage)
    inventory = service.build_inventory(settings)

    assert inventory.environment_count == 2
    assert inventory.hidden_value_count == 2
    assert inventory.encrypted_envelope_count == 1
    assert inventory.plaintext_hidden_count == 1
    assert len(inventory.kid_histogram) == 1


def test_verify_decrypt_access_success(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is True
    assert report.errors == ()
    assert report.inventory.encrypted_envelope_count == 1


def test_verify_decrypt_access_detects_missing_kid(tmp_path, monkeypatch, caplog):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    with caplog.at_level("WARNING"):
        report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is False
    assert report.inventory.missing_kids
    assert any("Missing key material" in error for error in report.errors)
    assert any(
        "encryption_migration_missing_kids count=" in record.message
        for record in caplog.records
    )
    assert any(
        "encryption_migration_verify_completed success=false" in record.message
        for record in caplog.records
    )


def test_bulk_re_encrypt_dry_run_projects_active_kid(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(active_key)
    historical_id = build_key_id(historical_key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": historical_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    settings = AppSettings(env_encryption_enabled=True)

    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": historical_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )

    service = EncryptionMigrationService(storage)
    report = service.bulk_re_encrypt(settings, dry_run=True, backup=False)

    assert report.success is True
    assert report.dry_run is True
    assert report.inventory.kid_histogram == {historical_id: 1}

    write_report = service.bulk_re_encrypt(settings, dry_run=False, backup=True)
    assert write_report.success is True
    assert write_report.backup_path is not None
    final = service.build_inventory(settings)
    assert final.kid_histogram == {historical_id: 1}


def test_encrypt_plaintext_hidden_encrypts_on_save(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)

    plain_payload = [
        {
            "id": "e1",
            "name": "Plain",
            "variables": {"SECRET": "plain"},
            "hidden_keys": ["SECRET"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(plain_payload, handle, indent=2)

    service = EncryptionMigrationService(storage)
    before = service.build_inventory(settings)
    assert before.plaintext_hidden_count == 1

    report = service.encrypt_plaintext_hidden(settings, backup=False)
    assert report.success is True
    after = service.build_inventory(settings)
    assert after.plaintext_hidden_count == 0
    assert after.encrypted_envelope_count == 1


def test_encrypt_plaintext_hidden_dry_run_projects_active_kid(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(key)
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)

    plain_payload = [
        {
            "id": "e1",
            "name": "Plain",
            "variables": {"SECRET": "plain"},
            "hidden_keys": ["SECRET"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(plain_payload, handle, indent=2)

    service = EncryptionMigrationService(storage)
    before = service.build_inventory(settings)
    assert before.plaintext_hidden_count == 1

    report = service.encrypt_plaintext_hidden(settings, dry_run=True, backup=False)

    assert report.success is True
    assert report.dry_run is True
    assert report.inventory.plaintext_hidden_count == 0
    assert report.inventory.encrypted_envelope_count == 1
    assert report.inventory.kid_histogram == {active_id: 1}
    after = service.build_inventory(settings)
    assert after.plaintext_hidden_count == 1


def test_encrypt_plaintext_hidden_when_encryption_disabled(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    settings = AppSettings(env_encryption_enabled=False)

    plain_payload = [
        {
            "id": "e1",
            "name": "Plain",
            "variables": {"SECRET": "plain"},
            "hidden_keys": ["SECRET"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(plain_payload, handle, indent=2)

    report = EncryptionMigrationService(storage).encrypt_plaintext_hidden(
        settings,
        backup=False,
    )

    assert report.success is False
    assert report.errors == ("Encryption is not enabled.",)


def test_encrypt_plaintext_hidden_succeeds_when_no_plaintext(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    report = EncryptionMigrationService(storage).encrypt_plaintext_hidden(
        settings,
        backup=False,
    )

    assert report.success is True
    assert report.errors == ()
    assert report.inventory.plaintext_hidden_count == 0


def test_verify_decrypt_access_detects_corrupt_ciphertext(tmp_path, monkeypatch, caplog):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    kid = build_key_id(key)
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    with open(storage.environments_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data[0]["variables"]["SECRET"] = {
        "enc": True,
        "v": 1,
        "alg": "fernet",
        "kid": kid,
        "ct": "this-is-not-a-valid-fernet-token",
    }
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    with caplog.at_level("WARNING"):
        report = EncryptionMigrationService(storage).verify_decrypt_access(settings)

    assert report.success is False
    assert len(report.errors) == 1
    assert "Dev:" in report.errors[0]
    assert "could not be decrypted" in report.errors[0]
    assert any(
        "encryption_migration_decrypt_failed error_count=1" in record.message
        for record in caplog.records
    )
    assert any(
        "encryption_migration_verify_completed success=false" in record.message
        for record in caplog.records
    )


def test_verify_decrypt_access_uses_build_inventory(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    service = EncryptionMigrationService(storage)
    settings = AppSettings(env_encryption_enabled=True)
    inventory_called = False
    original_build = service.build_inventory

    def spy_build(s):
        nonlocal inventory_called
        inventory_called = True
        return original_build(s)

    monkeypatch.setattr(service, "build_inventory", spy_build)
    report = service.verify_decrypt_access(settings)

    assert inventory_called
    assert report.inventory.environment_count == 0


def test_deserialize_all_uses_public_storage_api(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    service = EncryptionMigrationService(storage)
    settings = AppSettings(env_encryption_enabled=True)
    env = Environment(name="Dev", variables={"A": "1"})

    load_called = False
    deserialize_called = False

    def spy_load():
        nonlocal load_called
        load_called = True
        return [env], ()

    original_deserialize = storage._env_adapter.deserialize_environment

    def spy_deserialize(item):
        nonlocal deserialize_called
        deserialize_called = True
        return original_deserialize(item)

    monkeypatch.setattr(storage, "load_environments_with_errors", spy_load)
    monkeypatch.setattr(storage._env_adapter, "deserialize_environment", spy_deserialize)

    environments, errors = service._deserialize_all(settings)

    assert load_called
    assert not deserialize_called
    assert environments == [env]
    assert errors == ()


def test_bulk_re_encrypt_skips_when_already_on_active_kid(tmp_path, monkeypatch, caplog):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)
    storage.apply_encryption_settings(settings)
    storage.save_environments(
        [
            Environment(
                name="Dev",
                variables={"SECRET": "value"},
                hidden_keys={"SECRET"},
            )
        ]
    )

    before_mtime = storage.environments_file.stat().st_mtime
    service = EncryptionMigrationService(storage)

    with caplog.at_level("INFO"):
        report = service.bulk_re_encrypt(settings, dry_run=False, backup=True)

    assert report.success is True
    assert report.backup_path is None
    assert storage.environments_file.stat().st_mtime == before_mtime
    assert any(
        "encryption_migration_operation_skipped operation=re_encrypt "
        "reason=already_on_active_kid" in record.message
        for record in caplog.records
    )


def test_bulk_re_encrypt_does_not_skip_with_plaintext_hidden(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(env_encryption_enabled=True)

    encrypted_env = Environment(
        id="e1",
        name="Encrypted",
        variables={"SECRET": "hidden"},
        hidden_keys={"SECRET"},
    )
    storage.apply_encryption_settings(settings)
    storage.save_environments([encrypted_env])

    plain_payload = {
        "id": "e2",
        "name": "Plain",
        "variables": {"TOKEN": "plain"},
        "hidden_keys": ["TOKEN"],
        "enable_mcp": False,
    }
    with open(storage.environments_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.append(plain_payload)
    with open(storage.environments_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    before_mtime = storage.environments_file.stat().st_mtime
    report = EncryptionMigrationService(storage).bulk_re_encrypt(
        settings,
        dry_run=False,
        backup=False,
    )

    assert report.success is True
    assert storage.environments_file.stat().st_mtime > before_mtime
    after = EncryptionMigrationService(storage).build_inventory(settings)
    assert after.plaintext_hidden_count == 0


def test_backup_environments_file_creates_timestamped_copy(tmp_path):
    source = tmp_path / "environments.json"
    source.write_text("[]", encoding="utf-8")
    backup = backup_environments_file(source)
    assert backup.exists()
    assert backup.name.startswith("environments.backup.")
    assert backup.read_text(encoding="utf-8") == "[]"
