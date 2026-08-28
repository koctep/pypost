"""Tests for default runtime encrypt to v2 (PYPOST-1018)."""
from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from pypost.core.environment_secrets_codec import (
    EncryptedValueEnvelope,
    EncryptedValueEnvelopeV2,
    EnvironmentSecretsCodec,
)
from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.core.key_provider import EncryptionKey, KeyProvider
from pypost.models.models import Environment

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def key_provider() -> MagicMock:
    fernet = pytest.importorskip("cryptography.fernet")
    raw_key = fernet.Fernet.generate_key().decode("utf-8")
    provider = MagicMock(spec=KeyProvider)
    key_data = EncryptionKey(key=raw_key, key_id="kid-test-1")
    provider.get_current_key.return_value = key_data
    provider.get_key_by_id.return_value = key_data
    return provider


def test_codec_encrypt_defaults_to_v2(key_provider):
    """EnvironmentSecretsCodec.encrypt defaults to v2 envelope."""
    codec = EnvironmentSecretsCodec(key_provider)
    envelope = codec.encrypt("super-secret")

    assert isinstance(envelope, EncryptedValueEnvelopeV2)
    assert envelope.v == 2
    assert envelope.enc is True
    assert envelope.kid == "kid-test-1"
    assert envelope.ct is not None
    assert EnvironmentSecretsCodec.VERSION == 2


def test_codec_encrypt_v1_explicit(key_provider):
    """EnvironmentSecretsCodec.encrypt_v1 explicitly produces v1 envelope."""
    codec = EnvironmentSecretsCodec(key_provider)
    envelope = codec.encrypt_v1("super-secret")

    assert isinstance(envelope, EncryptedValueEnvelope)
    assert envelope.v == 1
    assert envelope.enc is True
    assert envelope.kid == "kid-test-1"


def test_adapter_serialize_environment_defaults_to_v2(monkeypatch):
    """EnvironmentVariablesAdapter defaults to v2 envelope when serializing hidden variables."""
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    adapter = EnvironmentVariablesAdapter()
    env = Environment(
        name="Production",
        variables={"API_KEY": "secret-value-123", "PUBLIC_VAR": "hello"},
        hidden_keys={"API_KEY"},
    )

    payload, stats = adapter.serialize_environment(env)
    assert stats.encrypted_count == 1

    encrypted_var = payload["variables"]["API_KEY"]
    assert isinstance(encrypted_var, dict)
    assert encrypted_var["enc"] is True
    assert encrypted_var["v"] == 2
