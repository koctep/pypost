from __future__ import annotations

import hashlib
from dataclasses import dataclass


class EnvironmentEncryptionError(RuntimeError):
    """Raised when encryption/decryption cannot be completed safely."""


@dataclass(frozen=True)
class EncryptionKey:
    key: str
    key_id: str


def build_key_id(key: str) -> str:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return digest[:16]
