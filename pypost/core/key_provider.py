import hashlib
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EnvironmentEncryptionError(RuntimeError):
    """Raised when encryption/decryption cannot be completed safely."""


@dataclass(frozen=True)
class EncryptionKey:
    key: str
    key_id: str


class KeyProvider:
    """Resolves encryption key material for environment storage."""

    def get_current_key(self) -> EncryptionKey:
        raise NotImplementedError

    def get_key_by_id(self, key_id: str) -> EncryptionKey:
        raise NotImplementedError


class LocalKeyProvider(KeyProvider):
    """
    Local key provider based on process environment variables.

    Supported variables:
    - PYPOST_ENV_ENCRYPTION_KEY: required Fernet key when encryption is enabled.
    """

    ENV_KEY = "PYPOST_ENV_ENCRYPTION_KEY"

    def _read_key(self) -> str:
        key = os.getenv(self.ENV_KEY, "").strip()
        if not key:
            logger.error("env_encryption_key_missing env_var=%s", self.ENV_KEY)
            raise EnvironmentEncryptionError(
                f"Missing encryption key in env var {self.ENV_KEY}."
            )
        logger.debug("env_encryption_key_loaded source=env_var")
        return key

    @staticmethod
    def _build_key_id(key: str) -> str:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return digest[:16]

    def get_current_key(self) -> EncryptionKey:
        key = self._read_key()
        key_id = self._build_key_id(key)
        logger.debug("env_encryption_key_resolved key_id=%s", key_id)
        return EncryptionKey(key=key, key_id=key_id)

    def get_key_by_id(self, key_id: str) -> EncryptionKey:
        key_data = self.get_current_key()
        if key_data.key_id != key_id:
            logger.error(
                "env_encryption_key_id_mismatch expected=%s actual=%s",
                key_id,
                key_data.key_id,
            )
            raise EnvironmentEncryptionError(
                f"Encryption key id mismatch: expected {key_id}, got {key_data.key_id}."
            )
        logger.debug("env_encryption_key_match key_id=%s", key_id)
        return key_data
