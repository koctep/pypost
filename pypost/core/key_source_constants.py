"""Shared encryption key source identifiers and fallback parsing."""

from typing import Literal

EncryptionKeySource = Literal["environment", "keyring", "secret_store"]

KEY_SOURCE_ENVIRONMENT: EncryptionKeySource = "environment"
KEY_SOURCE_KEYRING: EncryptionKeySource = "keyring"
KEY_SOURCE_SECRET_STORE: EncryptionKeySource = "secret_store"

DEFAULT_KEY_SOURCE: EncryptionKeySource = KEY_SOURCE_ENVIRONMENT

SUPPORTED_KEY_SOURCES = frozenset(
    {KEY_SOURCE_ENVIRONMENT, KEY_SOURCE_KEYRING, KEY_SOURCE_SECRET_STORE},
)


def parse_key_source_fallback(text: str) -> list[str] | None:
    if not text.strip():
        return None
    result: list[str] = []
    for part in text.split(","):
        source = part.strip()
        if source in SUPPORTED_KEY_SOURCES and source not in result:
            result.append(source)
    return result or None
