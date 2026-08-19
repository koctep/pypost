"""PYPOST-502: expanded key provider chain and secret-store unit coverage."""


import json
from unittest.mock import MagicMock

import pytest

from pypost.core.key_provider import ChainedKeyProvider, build_key_id
from pypost.core.key_sources.chain import KeySourceChain
from pypost.core.key_sources.env import EnvKeySource, clear_registry_cache
from pypost.core.key_sources.file_cache import MtimeFileCache
from pypost.core.key_sources.secret_store import (
    SecretBackendChain,
    SecretStoreKeySource,
    clear_spec_cache,
)
from pypost.core.key_source_constants import parse_key_source_fallback

pytestmark = pytest.mark.timeout(30)


def test_parse_key_source_fallback_empty_returns_none():
    assert parse_key_source_fallback("") is None
    assert parse_key_source_fallback("   ") is None


def test_parse_key_source_fallback_dedupes_and_drops_invalid():
    result = parse_key_source_fallback("environment, vault, keyring, environment, bogus")
    assert result == ["environment", "keyring"]


def test_key_source_chain_resolve_by_id_falls_back_to_env(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    monkeypatch.setenv(EnvKeySource.ENV_KEY, key)

    unavailable = MagicMock()
    unavailable.name = "mock_unavailable"
    unavailable.try_resolve_by_id.return_value = None

    chain = KeySourceChain([unavailable, EnvKeySource()])
    resolved = chain.resolve_by_id(key_id)
    assert resolved is not None
    assert resolved.key == key


def test_secret_store_resolve_historical_key_by_id(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(active_key)
    historical_id = build_key_id(historical_key)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            },
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", str(spec_path))
    source = SecretStoreKeySource()
    resolved = source.try_resolve_by_id(historical_id)
    assert resolved is not None
    assert resolved.key == historical_key


def test_secret_backend_chain_inline_spec_fallback_when_backends_fail(tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    spec = {"active_key_id": key_id, "keys": {key_id: key}}
    backends = [{"type": "file", "path": str(tmp_path / "missing.json")}]
    chain = SecretBackendChain([])
    registry = chain.resolve_registry(spec, backends)
    assert registry is not None
    assert registry.keys[key_id] == key


def test_env_key_source_keys_file_takes_precedence_over_env_var(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    file_key = fernet.Fernet.generate_key().decode("utf-8")
    env_key = fernet.Fernet.generate_key().decode("utf-8")
    file_id = build_key_id(file_key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps({"active_key_id": file_id, "keys": {file_id: file_key}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.ENV_KEY, env_key)
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    source = EnvKeySource()
    assert source.try_resolve_active().key == file_key


def test_env_key_source_malformed_keys_file_returns_none(monkeypatch, tmp_path):
    bad_path = tmp_path / "keys.json"
    bad_path.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(bad_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    assert EnvKeySource().try_resolve_active() is None


def test_env_key_source_rejects_invalid_fernet_material(monkeypatch, tmp_path):
    pytest.importorskip("cryptography.fernet")
    bad_path = tmp_path / "keys.json"
    bad_path.write_text(
        json.dumps({"active_key_id": "kid1", "keys": {"kid1": "not-a-fernet-key"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(bad_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    assert EnvKeySource().try_resolve_active() is None


def test_env_key_source_empty_registry_returns_none(monkeypatch, tmp_path):
    empty_path = tmp_path / "keys.json"
    empty_path.write_text(json.dumps({"active_key_id": "", "keys": {}}), encoding="utf-8")
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(empty_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    assert EnvKeySource().try_resolve_active() is None


def test_env_keys_file_cache_avoids_reread(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    calls: list[int] = []
    original = EnvKeySource._read_registry_file

    def counting(self, path):
        calls.append(1)
        return original(self, path)

    monkeypatch.setattr(EnvKeySource, "_read_registry_file", counting)
    source = EnvKeySource()
    assert source.try_resolve_active() is not None
    assert source.try_resolve_active() is not None
    assert len(calls) == 1


def test_chained_provider_by_id_uses_chain_fallback(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    monkeypatch.setenv(EnvKeySource.ENV_KEY, key)

    unavailable = MagicMock()
    unavailable.name = "mock_unavailable"
    unavailable.try_resolve_by_id.return_value = None

    provider = ChainedKeyProvider(KeySourceChain([unavailable, EnvKeySource()]))
    resolved = provider.get_key_by_id(key_id)
    assert resolved.key == key


def test_mtime_file_cache_clear(tmp_path):
    cache = MtimeFileCache[str]()
    target = tmp_path / "sample.txt"
    target.write_text("initial", encoding="utf-8")

    calls = 0

    def loader(path):
        nonlocal calls
        calls += 1
        return path.read_text(encoding="utf-8")

    assert cache.get(target, loader) == "initial"
    assert cache.get(target, loader) == "initial"
    assert calls == 1

    cache.clear()
    assert cache.get(target, loader) == "initial"
    assert calls == 2


def test_clear_registry_cache_forces_reload(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    calls = 0
    original = EnvKeySource._read_registry_file

    def counting(self, path):
        nonlocal calls
        calls += 1
        return original(self, path)

    monkeypatch.setattr(EnvKeySource, "_read_registry_file", counting)
    source = EnvKeySource()
    assert source.try_resolve_active() is not None
    assert calls == 1

    clear_registry_cache()
    assert source.try_resolve_active() is not None
    assert calls == 2


def test_clear_spec_cache_forces_reload(monkeypatch, tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps({"active_key_id": "dummy", "keys": {"dummy": "fake"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", str(spec_path))
    calls = 0
    original = SecretStoreKeySource._read_spec_file

    def counting(self, path):
        nonlocal calls
        calls += 1
        return original(self, path)

    monkeypatch.setattr(SecretStoreKeySource, "_read_spec_file", counting)
    source = SecretStoreKeySource()
    source._load_spec()
    assert calls == 1

    clear_spec_cache()
    source._load_spec()
    assert calls == 2
