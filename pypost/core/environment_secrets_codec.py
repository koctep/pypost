import logging
from dataclasses import dataclass
from typing import Any, ClassVar

from pypost.core.key_provider import EncryptionKey, EnvironmentEncryptionError, KeyProvider

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - exercised when dependency is absent.
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EncryptedValueEnvelope:
    """Typed v1 encrypted environment value envelope."""

    enc: bool
    v: int
    alg: str
    kid: str
    ct: str

    VERSION: ClassVar[int] = 1
    ALGORITHM: ClassVar[str] = "fernet"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EncryptedValueEnvelope":
        """Parse and validate a serialized envelope dict (v1 backward compatible)."""
        if not payload.get("enc"):
            raise EnvironmentEncryptionError("Encrypted payload marker is missing.")
        if payload.get("v") != cls.VERSION:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload version: {payload.get('v')}"
            )
        if payload.get("alg") != cls.ALGORITHM:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload algorithm: {payload.get('alg')}"
            )
        kid = payload.get("kid")
        ct = payload.get("ct")
        if kid is None or ct is None:
            raise EnvironmentEncryptionError("Encrypted payload is missing required fields.")
        return cls(
            enc=True,
            v=cls.VERSION,
            alg=cls.ALGORITHM,
            kid=str(kid),
            ct=str(ct),
        )

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

    VERSION = EncryptedValueEnvelope.VERSION
    ALGORITHM = EncryptedValueEnvelope.ALGORITHM

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
        envelope = EncryptedValueEnvelope.from_payload(payload)
        key = self._key_provider.get_key_by_id(envelope.kid)
        logger.debug("env_value_decrypt_attempt key_id=%s", envelope.kid)
        return self._decrypt_token(envelope.ct, key)

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

