"""Encrypt sensitive AppSettings fields at rest (PYPOST-708)."""

from __future__ import annotations

import logging
from typing import Any

from pypost.core.encryption_config import build_key_provider
from pypost.core.encryption_key import EnvironmentEncryptionError
from pypost.core.environment_secrets_codec import EnvironmentSecretsCodec
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

_ENCRYPTED_WEBHOOK_AUTH_KEY = "alert_webhook_auth_header_encrypted"
_PLAINTEXT_WEBHOOK_AUTH_KEY = "alert_webhook_auth_header"


def serialize_settings_for_disk(settings: AppSettings) -> dict[str, Any]:
    """Return settings dict with webhook auth stored encrypted when possible."""
    data = settings.model_dump()
    auth = data.pop(_PLAINTEXT_WEBHOOK_AUTH_KEY, None)
    data.pop(_ENCRYPTED_WEBHOOK_AUTH_KEY, None)
    if not auth:
        return data
    try:
        codec = EnvironmentSecretsCodec(build_key_provider(settings))
        envelope = codec.encrypt(auth)
        data[_ENCRYPTED_WEBHOOK_AUTH_KEY] = envelope.to_json()
    except EnvironmentEncryptionError as exc:
        logger.warning("webhook_auth_encrypt_failed reason=%s", exc)
        data[_PLAINTEXT_WEBHOOK_AUTH_KEY] = auth
    return data


def parse_settings_from_disk(data: dict[str, Any]) -> AppSettings:
    """Build AppSettings, decrypting webhook auth envelope when present."""
    payload = dict(data)
    encrypted = payload.pop(_ENCRYPTED_WEBHOOK_AUTH_KEY, None)
    legacy_plain = payload.get(_PLAINTEXT_WEBHOOK_AUTH_KEY)
    if encrypted is not None:
        settings_stub = AppSettings(**payload)
        try:
            codec = EnvironmentSecretsCodec(build_key_provider(settings_stub))
            payload[_PLAINTEXT_WEBHOOK_AUTH_KEY] = codec.decrypt(encrypted)
        except EnvironmentEncryptionError as exc:
            logger.error("webhook_auth_decrypt_failed reason=%s", exc)
            if legacy_plain is None:
                payload[_PLAINTEXT_WEBHOOK_AUTH_KEY] = None
    return AppSettings(**payload)
