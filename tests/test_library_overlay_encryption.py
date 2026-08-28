"""Tests for at-rest encryption of local overlay secrets (PYPOST-1225)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from cryptography.fernet import Fernet

from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec
from pypost.core.key_provider import EncryptionKey, KeyProvider
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.models.library_manifest import LocalLibraryOverlay

pytestmark = pytest.mark.timeout(30)


class DummyKeyProvider(KeyProvider):
    def __init__(self, key: str, key_id: str = "k1"):
        self._key = EncryptionKey(key=key, key_id=key_id)

    def get_current_key(self) -> EncryptionKey:
        return self._key

    def get_key_by_id(self, key_id: str) -> EncryptionKey | None:
        if key_id == self._key.key_id:
            return self._key
        return None


@pytest.fixture
def crypto_codec():
    fernet_key = Fernet.generate_key().decode("utf-8")
    provider = DummyKeyProvider(key=fernet_key, key_id="k-test-1225")
    return EnvironmentSecretsCodec(provider)


def test_overlay_secrets_encrypted_on_disk(tmp_path, crypto_codec):
    """Saving overlay with secrets_codec writes encrypted envelope objects in overlay.json."""
    mgr = LocalOverlayManager(base_dir=tmp_path, secrets_codec=crypto_codec)
    overlay = LocalLibraryOverlay(
        library_id="lib-sec-1",
        secrets={"api_key": "sk_live_secret_123"},
        overrides={"timeout": 15},
    )
    mgr.save_overlay(overlay)

    # Read raw JSON from disk
    saved_file = tmp_path / "lib-sec-1" / "overlay.json"
    assert saved_file.is_file()
    raw_data = json.loads(saved_file.read_text(encoding="utf-8"))

    # Assert secret on disk is not plaintext and is formatted as an encrypted envelope
    assert raw_data["secrets"]["api_key"] != "sk_live_secret_123"
    assert isinstance(raw_data["secrets"]["api_key"], dict)
    assert raw_data["secrets"]["api_key"].get("enc") is True
    assert raw_data["secrets"]["api_key"].get("kid") == "k-test-1225"
    # Non-secret override remains unencrypted
    assert raw_data["overrides"]["timeout"] == 15


def test_overlay_secrets_transparently_decrypted_on_load(tmp_path, crypto_codec):
    """Loading encrypted overlay with secrets_codec restores plaintext secrets in memory."""
    mgr = LocalOverlayManager(base_dir=tmp_path, secrets_codec=crypto_codec)
    overlay = LocalLibraryOverlay(
        library_id="lib-sec-2",
        secrets={"db_pass": "super_secret_password"},
        overrides={"port": 5432},
    )
    mgr.save_overlay(overlay)

    # Load via new manager instance with codec
    mgr2 = LocalOverlayManager(base_dir=tmp_path, secrets_codec=crypto_codec)
    loaded = mgr2.get_overlay("lib-sec-2")
    assert loaded.library_id == "lib-sec-2"
    assert loaded.secrets["db_pass"] == "super_secret_password"
    assert loaded.overrides["port"] == 5432


def test_overlay_backward_compatibility_legacy_plaintext(tmp_path, crypto_codec):
    """Legacy plaintext overlay files load cleanly when codec is configured."""
    overlay_dir = tmp_path / "lib-legacy"
    overlay_dir.mkdir(parents=True)
    overlay_file = overlay_dir / "overlay.json"
    overlay_file.write_text(
        json.dumps({
            "library_id": "lib-legacy",
            "secrets": {"token": "plain_legacy_token"},
            "overrides": {"env": "prod"},
        }),
        encoding="utf-8",
    )

    mgr = LocalOverlayManager(base_dir=tmp_path, secrets_codec=crypto_codec)
    loaded = mgr.get_overlay("lib-legacy")
    assert loaded.secrets["token"] == "plain_legacy_token"
    assert loaded.overrides["env"] == "prod"
