import logging

from pypost.core.encryption_key import EncryptionKey, EnvironmentEncryptionError, build_key_id
from pypost.core.key_sources.chain import KeySourceChain
from pypost.core.key_sources.env import EnvKeySource

logger = logging.getLogger(__name__)

__all__ = [
    "ChainedKeyProvider",
    "EncryptionKey",
    "EnvironmentEncryptionError",
    "KeyProvider",
    "LocalKeyProvider",
    "build_key_id",
]


class KeyProvider:
    """Resolves encryption key material for environment storage."""

    def get_current_key(self) -> EncryptionKey:
        raise NotImplementedError

    def get_key_by_id(self, key_id: str) -> EncryptionKey:
        raise NotImplementedError


class ChainedKeyProvider(KeyProvider):
    """Delegates key resolution to an ordered KeySourceChain."""

    def __init__(self, chain: KeySourceChain) -> None:
        self._chain = chain

    def get_current_key(self) -> EncryptionKey:
        key = self._chain.resolve_active()
        if key is None:
            logger.error("encryption_key_unavailable reason=no_source_provided_active_key")
            raise EnvironmentEncryptionError(
                "Encryption key is unavailable. Configure a supported key source."
            )
        return key

    def get_key_by_id(self, key_id: str) -> EncryptionKey:
        key = self._chain.resolve_by_id(key_id)
        if key is None:
            logger.error(
                "encryption_key_rotation_lookup_failed key_id=%s " "reason=no_source_provided_key",
                key_id,
            )
            raise EnvironmentEncryptionError(f"Encryption key is unavailable for key id {key_id}.")
        return key


class LocalKeyProvider(ChainedKeyProvider):
    """
    Backward-compatible env-only key provider.

    Supported variables:
    - PYPOST_ENV_ENCRYPTION_KEY: required Fernet key when encryption is enabled.
    """

    ENV_KEY = EnvKeySource.ENV_KEY

    def __init__(self) -> None:
        super().__init__(KeySourceChain([EnvKeySource()]))
