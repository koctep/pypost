import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.key_provider import (
    ChainedKeyProvider,
    EnvironmentEncryptionError,
    LocalKeyProvider,
    build_key_id,
)
from pypost.core.key_sources.chain import KeySourceChain
from pypost.core.key_sources.env import EnvKeySource
from pypost.core.key_sources.keyring import KeyringKeySource


def test_get_key_by_id_raises_when_current_key_id_does_not_match(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv(LocalKeyProvider.ENV_KEY, key)
    provider = LocalKeyProvider()

    with pytest.raises(EnvironmentEncryptionError, match="unavailable for key id"):
        provider.get_key_by_id("0000000000000000")


def test_build_key_id_is_stable_and_matches_sha256_prefix():
    key = "sample-stable-key-material"
    expected = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    key_id_first = build_key_id(key)
    key_id_second = build_key_id(key)

    assert key_id_first == expected
    assert key_id_first == key_id_second


def test_local_key_provider_env_backward_compat(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv(LocalKeyProvider.ENV_KEY, key)
    provider = LocalKeyProvider()

    current = provider.get_current_key()
    assert current.key == key
    assert provider.get_key_by_id(current.key_id) == current


def test_env_key_source_rotation_via_keys_file(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(active_key)
    historical_id = build_key_id(historical_key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))

    source = EnvKeySource()
    assert source.try_resolve_active().key_id == active_id
    assert source.try_resolve_by_id(historical_id).key == historical_key


def test_key_source_chain_fallback(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)

    unavailable = MagicMock()
    unavailable.name = "mock_unavailable"
    unavailable.try_resolve_active.return_value = None
    unavailable.try_resolve_by_id.return_value = None

    env_source = EnvKeySource()
    monkeypatch.setenv(EnvKeySource.ENV_KEY, key)
    chain = KeySourceChain([unavailable, env_source])
    provider = ChainedKeyProvider(chain)

    current = provider.get_current_key()
    assert current.key == key


def test_keyring_source_returns_none_when_package_missing(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "keyring", None)
    source = KeyringKeySource()
    assert source.try_resolve_active() is None


def test_keyring_source_resolves_active_key(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = key
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        source = KeyringKeySource()
        resolved = source.try_resolve_active()
    assert resolved is not None
    assert resolved.key == key


def test_keyring_source_resolves_historical_key_by_id(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_id = build_key_id(historical_key)
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = historical_key
    with patch.dict("sys.modules", {"keyring": mock_keyring}):
        source = KeyringKeySource()
        resolved = source.try_resolve_by_id(historical_id)
    assert resolved is not None
    assert resolved.key == historical_key
    assert resolved.key_id == historical_id
    mock_keyring.get_password.assert_called_once_with("pypost/env-encryption", historical_id)


def test_codec_missing_historical_key_raises(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_id = build_key_id(historical_key)
    monkeypatch.setenv(LocalKeyProvider.ENV_KEY, active_key)

    from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec

    provider = LocalKeyProvider()
    codec = EnvironmentSecretsCodec(provider)
    historical_token = fernet.Fernet(historical_key.encode()).encrypt(b"secret").decode()
    payload = {
        "enc": True,
        "v": 1,
        "alg": "fernet",
        "kid": historical_id,
        "ct": historical_token,
    }

    with pytest.raises(EnvironmentEncryptionError, match="unavailable for key id"):
        codec.decrypt(payload)


def test_chained_provider_rotation_encrypt_active_decrypt_historical(monkeypatch, tmp_path):
    fernet = pytest.importorskip("cryptography.fernet")
    active_key = fernet.Fernet.generate_key().decode("utf-8")
    historical_key = fernet.Fernet.generate_key().decode("utf-8")
    active_id = build_key_id(active_key)
    historical_id = build_key_id(historical_key)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(
        json.dumps(
            {
                "active_key_id": active_id,
                "keys": {active_id: active_key, historical_id: historical_key},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))

    from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec

    provider = ChainedKeyProvider(KeySourceChain([EnvKeySource()]))
    codec = EnvironmentSecretsCodec(provider)

    historical_token = fernet.Fernet(historical_key.encode()).encrypt(b"secret").decode()
    historical_payload = {
        "enc": True,
        "v": 1,
        "alg": "fernet",
        "kid": historical_id,
        "ct": historical_token,
    }

    assert codec.decrypt(historical_payload) == "secret"
    new_envelope = codec.encrypt("new-value")
    assert new_envelope.kid == active_id
