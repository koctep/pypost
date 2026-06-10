import json

import pytest

from pypost.core.key_provider import build_key_id
from pypost.core.key_sources.secret_store import (
    FileSecretBackend,
    SecretBackendChain,
    SecretStoreKeySource,
)


def test_file_secret_backend_loads_registry(tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    backend = FileSecretBackend()
    registry = backend.try_load_registry({"type": "file", "path": str(path)})
    assert registry is not None
    assert registry.active_key_id == key_id
    assert registry.keys[key_id] == key


def test_secret_store_key_source_inline_spec(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_SECRETS_FILE", str(spec_path))
    source = SecretStoreKeySource()
    resolved = source.try_resolve_active()
    assert resolved is not None
    assert resolved.key_id == key_id


def test_secret_backend_chain_falls_back_to_second_backend(tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(key)
    missing_path = tmp_path / "missing.json"
    valid_path = tmp_path / "valid.json"
    valid_path.write_text(
        json.dumps({"active_key_id": key_id, "keys": {key_id: key}}),
        encoding="utf-8",
    )
    spec = {"active_key_id": key_id, "keys": {key_id: key}}
    backends = [
        {"type": "file", "path": str(missing_path)},
        {"type": "file", "path": str(valid_path)},
    ]
    chain = SecretBackendChain([])
    registry = chain.resolve_registry(spec, backends)
    assert registry is not None
    assert registry.active_key_id == key_id
    assert registry.keys[key_id] == key
