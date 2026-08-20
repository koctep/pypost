"""Unit tests for encryption settings resolution (PYPOST-481/483)."""


import pytest

import json


from pypost.core.encryption_config import (
    build_key_provider,
    resolve_encryption_enabled,
    resolve_key_source,
    resolve_key_source_chain,
)
from pypost.core.key_provider import ChainedKeyProvider, LocalKeyProvider, build_key_id
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(30)


def test_resolve_encryption_enabled_uses_settings_when_set(monkeypatch):
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    settings = AppSettings(env_encryption_enabled=True)
    assert resolve_encryption_enabled(settings) is True


def test_resolve_encryption_enabled_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    settings = AppSettings(env_encryption_enabled=None)
    assert resolve_encryption_enabled(settings) is True


def test_resolve_key_source_defaults_to_environment():
    assert resolve_key_source(AppSettings()) == "environment"


def test_resolve_key_source_uses_settings_value():
    settings = AppSettings(env_encryption_key_source="environment")
    assert resolve_key_source(settings) == "environment"


def test_resolve_key_source_unsupported_falls_back(monkeypatch):
    monkeypatch.setattr(
        "pypost.core.encryption_config.logger.warning",
        lambda *args, **kwargs: None,
    )
    settings = AppSettings(env_encryption_key_source="vault")
    assert resolve_key_source(settings) == "environment"


def test_resolve_key_source_chain_primary_only():
    settings = AppSettings(env_encryption_key_source="keyring")
    assert resolve_key_source_chain(settings) == ["keyring"]


def test_resolve_key_source_chain_with_fallback_deduped():
    settings = AppSettings(
        env_encryption_key_source="keyring",
        env_encryption_key_source_fallback=["environment", "keyring", "secret_store"],
    )
    assert resolve_key_source_chain(settings) == ["keyring", "environment", "secret_store"]


def test_build_key_provider_environment_returns_chained_provider():
    provider = build_key_provider(AppSettings(env_encryption_key_source="environment"))
    assert isinstance(provider, ChainedKeyProvider)
    assert isinstance(provider, LocalKeyProvider) is False


def test_build_key_provider_secret_store_from_spec(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(active_key)
    keys_file = tmp_path / "keys.json"
    keys_file.write_text(
        json.dumps({"active_key_id": active_id, "keys": {active_id: active_key}}),
        encoding="utf-8",
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key},
                "backends": [{"type": "file", "path": str(keys_file)}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", str(spec_path))
    settings = AppSettings(env_encryption_key_source="secret_store")
    provider = build_key_provider(settings)
    assert provider.get_current_key().key_id == active_id


def test_build_key_provider_default_is_env_chain(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    provider = build_key_provider(None)
    assert provider.get_current_key().key == key


def test_build_key_provider_keyring_unavailable_falls_back_to_env(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setitem(__import__("sys").modules, "keyring", None)
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    settings = AppSettings(
        env_encryption_key_source="keyring",
        env_encryption_key_source_fallback=["environment"],
    )
    provider = build_key_provider(settings)
    assert provider.get_current_key().key == key
