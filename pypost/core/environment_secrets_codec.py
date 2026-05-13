import logging
from dataclasses import dataclass
from typing import Any

from pypost.core.key_provider import (
    EncryptionKey,
    EnvironmentEncryptionError,
    KeyProvider,
)

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - exercised when dependency is absent.
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EncryptedValueEnvelope:
    enc: bool
    v: int
    alg: str
    kid: str
    ct: str

    def to_json(self) -> dict[str, Any]:
        return {
            "enc": self.enc,
            "v": self.v,
            "alg": self.alg,
            "kid": self.kid,
            "ct": self.ct,
        }


class EnvironmentSecretsCodec:
    """Encodes and decodes encrypted environment values."""

    VERSION = 1
    ALGORITHM = "fernet"

    def __init__(self, key_provider: KeyProvider) -> None:
        self._key_provider = key_provider

    def _ensure_fernet_available(self) -> None:
        if Fernet is None:
            raise EnvironmentEncryptionError(
                "cryptography dependency is missing. Install 'cryptography' to use "
                "encrypted environment storage."
            )

    def encrypt(self, value: str) -> EncryptedValueEnvelope:
        self._ensure_fernet_available()
        key = self._key_provider.get_current_key()
        token = Fernet(key.key.encode("utf-8")).encrypt(value.encode("utf-8"))
        logger.debug(
            "env_value_encrypted algorithm=%s version=%d key_id=%s",
            self.ALGORITHM,
            self.VERSION,
            key.key_id,
        )
        return EncryptedValueEnvelope(
            enc=True,
            v=self.VERSION,
            alg=self.ALGORITHM,
            kid=key.key_id,
            ct=token.decode("utf-8"),
        )

    def decrypt(self, payload: dict[str, Any]) -> str:
        self._ensure_fernet_available()
        self._validate_payload(payload)
        key_id = str(payload["kid"])
        key = self._key_provider.get_key_by_id(key_id)
        logger.debug("env_value_decrypt_attempt key_id=%s", key_id)
        return self._decrypt_token(payload["ct"], key)

    def _decrypt_token(self, token: str, key: EncryptionKey) -> str:
        try:
            raw = Fernet(key.key.encode("utf-8")).decrypt(token.encode("utf-8"))
            logger.debug("env_value_decrypted key_id=%s", key.key_id)
            return raw.decode("utf-8")
        except InvalidToken as exc:
            logger.error("env_value_decrypt_failed reason=invalid_token key_id=%s", key.key_id)
            raise EnvironmentEncryptionError(
                "Encrypted environment value could not be decrypted with current key."
            ) from exc

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        if not payload.get("enc"):
            raise EnvironmentEncryptionError("Encrypted payload marker is missing.")
        if payload.get("v") != self.VERSION:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload version: {payload.get('v')}"
            )
        if payload.get("alg") != self.ALGORITHM:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload algorithm: {payload.get('alg')}"
            )
        if "kid" not in payload or "ct" not in payload:
            raise EnvironmentEncryptionError("Encrypted payload is missing required fields.")
