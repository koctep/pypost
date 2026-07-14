from __future__ import annotations

from typing import Protocol

from pypost.core.encryption_key import EncryptionKey


class KeySource(Protocol):
    @property
    def name(self) -> str: ...

    def try_resolve_active(self) -> EncryptionKey | None: ...

    def try_resolve_by_id(self, key_id: str) -> EncryptionKey | None: ...
