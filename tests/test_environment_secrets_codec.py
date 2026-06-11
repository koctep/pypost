import pytest

pytestmark = pytest.mark.timeout(30)

import base64
from unittest.mock import MagicMock


from pypost.core.encryption_key import build_key_id
from pypost.core.environment_secrets_codec import (
    EncryptedValueEnvelope,
    EncryptedValueEnvelopeV2,
    EnvironmentSecretsCodec,
)
from pypost.core.key_provider import (
    EncryptionKey,
    EnvironmentEncryptionError,
    KeyProvider,
)


@pytest.fixture
def codec() -> EnvironmentSecretsCodec:
    pytest.importorskip("cryptography.fernet")
    key_provider = MagicMock(spec=KeyProvider)
    return EnvironmentSecretsCodec(key_provider)


def _build_key_provider_with_active_key(raw_key: str) -> MagicMock:
    key_provider = MagicMock(spec=KeyProvider)
    key_data = EncryptionKey(key=raw_key, key_id="kid-1")
    key_provider.get_current_key.return_value = key_data
    key_provider.get_key_by_id.return_value = key_data
    return key_provider


@pytest.mark.parametrize(
    "payload,expected_message",
    [
        (
            {"enc": False, "v": 1, "alg": "fernet", "kid": "abc", "ct": "token"},
            "Encrypted payload marker is missing",
        ),
        (
            {"enc": True, "v": 999, "alg": "fernet", "kid": "abc", "ct": "token"},
            "Unsupported encrypted payload version",
        ),
        (
            {"enc": True, "v": 1, "alg": "aes-gcm", "kid": "abc", "ct": "token"},
            "Unsupported encrypted payload algorithm",
        ),
        (
            {"enc": True, "v": 1, "alg": "fernet", "ct": "token"},
            "Encrypted payload is missing required fields",
        ),
        (
            {"enc": True, "v": 1, "alg": "fernet", "kid": "abc"},
            "Encrypted payload is missing required fields",
        ),
    ],
)
def test_from_payload_rejects_invalid_shapes(
    payload: dict[str, object],
    expected_message: str,
):
    with pytest.raises(EnvironmentEncryptionError, match=expected_message):
        EncryptedValueEnvelope.from_payload(payload)


@pytest.mark.parametrize(
    "payload,expected_message",
    [
        (
            {"enc": False, "v": 1, "alg": "fernet", "kid": "abc", "ct": "token"},
            "Encrypted payload marker is missing",
        ),
        (
            {"enc": True, "v": 999, "alg": "fernet", "kid": "abc", "ct": "token"},
            "Unsupported encrypted payload version",
        ),
        (
            {"enc": True, "v": 1, "alg": "aes-gcm", "kid": "abc", "ct": "token"},
            "Unsupported encrypted payload algorithm",
        ),
        (
            {"enc": True, "v": 1, "alg": "fernet", "ct": "token"},
            "Encrypted payload is missing required fields",
        ),
        (
            {"enc": True, "v": 1, "alg": "fernet", "kid": "abc"},
            "Encrypted payload is missing required fields",
        ),
    ],
)
def test_decrypt_rejects_invalid_payload_shapes(
    codec: EnvironmentSecretsCodec,
    payload: dict[str, object],
    expected_message: str,
):
    with pytest.raises(EnvironmentEncryptionError, match=expected_message):
        codec.decrypt(payload)


def test_from_payload_dispatches_v2_fernet_with_meta():
    envelope = EncryptedValueEnvelope.from_payload(
        {
            "enc": True,
            "v": 2,
            "alg": "fernet",
            "kid": "kid-2",
            "ct": "token-value",
            "meta": {"rotated_from": "kid-1"},
        }
    )
    assert isinstance(envelope, EncryptedValueEnvelopeV2)
    assert envelope.meta == {"rotated_from": "kid-1"}
    assert envelope.to_json() == {
        "enc": True,
        "v": 2,
        "alg": "fernet",
        "kid": "kid-2",
        "ct": "token-value",
        "meta": {"rotated_from": "kid-1"},
    }


def test_from_payload_dispatches_v2_aes_gcm():
    envelope = EncryptedValueEnvelope.from_payload(
        {
            "enc": True,
            "v": 2,
            "alg": "aes-gcm",
            "kid": "kid-3",
            "ct": "ciphertext",
            "iv": "nonce",
            "tag": "auth-tag",
        }
    )
    assert isinstance(envelope, EncryptedValueEnvelopeV2)
    assert envelope.iv == "nonce"
    assert envelope.tag == "auth-tag"


@pytest.mark.parametrize(
    "payload,expected_message",
    [
        (
            {
                "enc": True,
                "v": 2,
                "alg": "aes-gcm",
                "kid": "kid-3",
                "ct": "ciphertext",
            },
            "missing required fields for aes-gcm",
        ),
        (
            {
                "enc": True,
                "v": 2,
                "alg": "fernet",
                "kid": "kid-3",
                "ct": "token",
                "iv": "unexpected",
            },
            "unexpected fields for fernet",
        ),
        (
            {"enc": True, "v": 2, "alg": "chacha20", "kid": "kid-3", "ct": "token"},
            "Unsupported encrypted payload algorithm",
        ),
    ],
)
def test_from_payload_rejects_invalid_v2_shapes(
    payload: dict[str, object],
    expected_message: str,
):
    with pytest.raises(EnvironmentEncryptionError, match=expected_message):
        EncryptedValueEnvelope.from_payload(payload)


def test_decrypt_v2_fernet_payload():
    fernet = pytest.importorskip("cryptography.fernet")
    raw_key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(raw_key)
    token = fernet.Fernet(raw_key.encode("utf-8")).encrypt(b"secret-value").decode("utf-8")
    key_provider = _build_key_provider_with_active_key(raw_key)
    key_provider.get_key_by_id.return_value = EncryptionKey(key=raw_key, key_id=key_id)
    codec = EnvironmentSecretsCodec(key_provider)

    assert (
        codec.decrypt(
            {
                "enc": True,
                "v": 2,
                "alg": "fernet",
                "kid": key_id,
                "ct": token,
            }
        )
        == "secret-value"
    )


def test_decrypt_v2_aes_gcm_payload():
    aesgcm = pytest.importorskip("cryptography.hazmat.primitives.ciphers.aead").AESGCM
    fernet = pytest.importorskip("cryptography.fernet")
    raw_key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(raw_key)
    aes_key = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
    nonce = b"\x00" * 12
    encrypted = aesgcm(aes_key).encrypt(nonce, b"secret-value", None)
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]
    key_provider = _build_key_provider_with_active_key(raw_key)
    key_provider.get_key_by_id.return_value = EncryptionKey(key=raw_key, key_id=key_id)
    codec = EnvironmentSecretsCodec(key_provider)

    assert (
        codec.decrypt(
            {
                "enc": True,
                "v": 2,
                "alg": "aes-gcm",
                "kid": key_id,
                "ct": base64.b64encode(ciphertext).decode("utf-8"),
                "iv": base64.b64encode(nonce).decode("utf-8"),
                "tag": base64.b64encode(tag).decode("utf-8"),
            }
        )
        == "secret-value"
    )


def test_decrypt_v2_aes_gcm_invalid_tag_raises():
    aesgcm = pytest.importorskip("cryptography.hazmat.primitives.ciphers.aead").AESGCM
    fernet = pytest.importorskip("cryptography.fernet")
    raw_key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(raw_key)
    aes_key = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
    nonce = b"\x00" * 12
    encrypted = aesgcm(aes_key).encrypt(nonce, b"secret-value", None)
    ciphertext = encrypted[:-16]
    key_provider = _build_key_provider_with_active_key(raw_key)
    key_provider.get_key_by_id.return_value = EncryptionKey(key=raw_key, key_id=key_id)
    codec = EnvironmentSecretsCodec(key_provider)

    with pytest.raises(
        EnvironmentEncryptionError,
        match="Encrypted environment value could not be decrypted with current key",
    ):
        codec.decrypt(
            {
                "enc": True,
                "v": 2,
                "alg": "aes-gcm",
                "kid": key_id,
                "ct": base64.b64encode(ciphertext).decode("utf-8"),
                "iv": base64.b64encode(nonce).decode("utf-8"),
                "tag": base64.b64encode(b"invalid-tag-bytes").decode("utf-8"),
            }
        )


def test_from_payload_accepts_valid_v1_envelope():
    envelope = EncryptedValueEnvelope.from_payload(
        {
            "enc": True,
            "v": 1,
            "alg": "fernet",
            "kid": "kid-1",
            "ct": "token-value",
        }
    )
    assert envelope.kid == "kid-1"
    assert envelope.ct == "token-value"
    assert envelope.to_json() == {
        "enc": True,
        "v": 1,
        "alg": "fernet",
        "kid": "kid-1",
        "ct": "token-value",
    }


def test_encrypt_v2_fernet_roundtrip():
    fernet = pytest.importorskip("cryptography.fernet")
    raw_key = fernet.Fernet.generate_key().decode("utf-8")
    key_id = build_key_id(raw_key)
    key_provider = _build_key_provider_with_active_key(raw_key)
    key_provider.get_current_key.return_value = EncryptionKey(key=raw_key, key_id=key_id)
    codec = EnvironmentSecretsCodec(key_provider)

    envelope = codec.encrypt_v2("secret-value")

    assert envelope.v == 2
    assert envelope.alg == "fernet"
    assert envelope.kid == key_id
    assert codec.decrypt(envelope.to_json()) == "secret-value"


def test_decrypt_raises_on_invalid_ciphertext_token():
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    key_provider = _build_key_provider_with_active_key(key)
    codec = EnvironmentSecretsCodec(key_provider)

    with pytest.raises(
        EnvironmentEncryptionError,
        match="Encrypted environment value could not be decrypted with current key",
    ):
        codec.decrypt(
            {
                "enc": True,
                "v": 1,
                "alg": "fernet",
                "kid": "kid-1",
                "ct": "this-is-not-a-valid-fernet-token",
            }
        )
