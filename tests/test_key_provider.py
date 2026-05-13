import hashlib

import pytest

from pypost.core.key_provider import EnvironmentEncryptionError, LocalKeyProvider


def test_get_key_by_id_raises_when_current_key_id_does_not_match(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv(LocalKeyProvider.ENV_KEY, key)
    provider = LocalKeyProvider()

    with pytest.raises(EnvironmentEncryptionError, match="Encryption key id mismatch"):
        provider.get_key_by_id("0000000000000000")


def test_build_key_id_is_stable_and_matches_sha256_prefix():
    key = "sample-stable-key-material"
    expected = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    key_id_first = LocalKeyProvider._build_key_id(key)
    key_id_second = LocalKeyProvider._build_key_id(key)

    assert key_id_first == expected
    assert key_id_first == key_id_second
