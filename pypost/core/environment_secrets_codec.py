from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from typing import Any, ClassVar, TypeAlias

from pypost.core.key_provider import EncryptionKey, EnvironmentEncryptionError, KeyProvider

try:
    from cryptography.exceptions import InvalidTag
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover - exercised when dependency is absent.
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]
    InvalidTag = Exception  # type: ignore[assignment]
    AESGCM = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EncryptedValueEnvelopeV2:
    """Typed v2 encrypted environment value envelope."""

    enc: bool
    v: int
    alg: str
    kid: str
    ct: str
    iv: str | None = None
    tag: str | None = None
    meta: dict[str, str] | None = None

    VERSION: ClassVar[int] = 2
    FERNET_ALGORITHM: ClassVar[str] = "fernet"
    AES_GCM_ALGORITHM: ClassVar[str] = "aes-gcm"
    SUPPORTED_ALGORITHMS: ClassVar[frozenset[str]] = frozenset(
        {FERNET_ALGORITHM, AES_GCM_ALGORITHM}
    )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EncryptedValueEnvelopeV2":
        """Parse and validate a serialized v2 envelope dict."""
        if payload.get("v") != cls.VERSION:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload version: {payload.get('v')}"
            )
        alg = payload.get("alg")
        if alg not in cls.SUPPORTED_ALGORITHMS:
            raise EnvironmentEncryptionError(
                f"Unsupported encrypted payload algorithm: {alg}"
            )
        kid = payload.get("kid")
        ct = payload.get("ct")
        if kid is None or ct is None:
            raise EnvironmentEncryptionError("Encrypted payload is missing required fields.")
        iv = payload.get("iv")
        tag = payload.get("tag")
        if alg == cls.AES_GCM_ALGORITHM:
            if iv is None or tag is None:
                raise EnvironmentEncryptionError(
                    "Encrypted payload is missing required fields for aes-gcm."
                )
        elif iv is not None or tag is not None:
            raise EnvironmentEncryptionError(
                "Encrypted payload has unexpected fields for fernet."
            )
        raw_meta = payload.get("meta")
        meta: dict[str, str] | None = None
        if raw_meta is not None:
            if not isinstance(raw_meta, dict):
                raise EnvironmentEncryptionError("Encrypted payload meta must be an object.")
            meta = {str(key): str(value) for key, value in raw_meta.items()}
        return cls(
            enc=True,
            v=cls.VERSION,
            alg=str(alg),
            kid=str(kid),
            ct=str(ct),
            iv=str(iv) if iv is not None else None,
            tag=str(tag) if tag is not None else None,
            meta=meta,
        )

    def to_json(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enc": self.enc,
            "v": self.v,
            "alg": self.alg,
            "kid": self.kid,
            "ct": self.ct,
        }
        if self.iv is not None:
            result["iv"] = self.iv
        if self.tag is not None:
            result["tag"] = self.tag
        if self.meta:
            result["meta"] = self.meta
        return result


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
    def from_payload(
        cls, payload: dict[str, Any]
    ) -> "EncryptedValueEnvelope | EncryptedValueEnvelopeV2":
        """Parse and validate a serialized envelope dict (version dispatch)."""
        if not payload.get("enc"):
            raise EnvironmentEncryptionError("Encrypted payload marker is missing.")
        version = payload.get("v")
        if version == cls.VERSION:
            return cls._from_payload_v1(payload)
        if version == EncryptedValueEnvelopeV2.VERSION:
            return EncryptedValueEnvelopeV2.from_payload(payload)
        raise EnvironmentEncryptionError(
            f"Unsupported encrypted payload version: {version}"
        )

    @classmethod
    def _from_payload_v1(cls, payload: dict[str, Any]) -> "EncryptedValueEnvelope":
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


EnvelopePayload: TypeAlias = EncryptedValueEnvelope | EncryptedValueEnvelopeV2


class EnvironmentSecretsCodec:
    """Encodes and decodes encrypted environment values."""

    VERSION = EncryptedValueEnvelopeV2.VERSION
    ALGORITHM = EncryptedValueEnvelopeV2.FERNET_ALGORITHM

    def __init__(self, key_provider: KeyProvider) -> None:
        self._key_provider = key_provider

    def _ensure_crypto_available(self) -> None:
        if Fernet is None or AESGCM is None:
            raise EnvironmentEncryptionError(
                "cryptography dependency is missing. Install 'cryptography' to use "
                "encrypted environment storage."
            )

    def encrypt(
        self,
        value: str,
        *,
        algorithm: str = EncryptedValueEnvelopeV2.FERNET_ALGORITHM,
    ) -> EncryptedValueEnvelopeV2:
        return self.encrypt_v2(value, algorithm=algorithm)

    def encrypt_v1(self, value: str) -> EncryptedValueEnvelope:
        self._ensure_crypto_available()
        key = self._key_provider.get_current_key()
        token = Fernet(key.key.encode("utf-8")).encrypt(value.encode("utf-8"))
        logger.debug(
            "env_value_encrypted algorithm=%s version=%d key_id=%s",
            EncryptedValueEnvelope.ALGORITHM,
            EncryptedValueEnvelope.VERSION,
            key.key_id,
        )
        return EncryptedValueEnvelope(
            enc=True,
            v=EncryptedValueEnvelope.VERSION,
            alg=EncryptedValueEnvelope.ALGORITHM,
            kid=key.key_id,
            ct=token.decode("utf-8"),
        )

    def encrypt_v2(
        self,
        value: str,
        *,
        algorithm: str = EncryptedValueEnvelopeV2.FERNET_ALGORITHM,
    ) -> EncryptedValueEnvelopeV2:
        self._ensure_crypto_available()
        key = self._key_provider.get_current_key()
        if algorithm == EncryptedValueEnvelopeV2.FERNET_ALGORITHM:
            token = Fernet(key.key.encode("utf-8")).encrypt(value.encode("utf-8"))
            logger.debug(
                "env_value_encrypted algorithm=%s version=%d key_id=%s",
                algorithm,
                EncryptedValueEnvelopeV2.VERSION,
                key.key_id,
            )
            return EncryptedValueEnvelopeV2(
                enc=True,
                v=EncryptedValueEnvelopeV2.VERSION,
                alg=algorithm,
                kid=key.key_id,
                ct=token.decode("utf-8"),
            )
        if algorithm == EncryptedValueEnvelopeV2.AES_GCM_ALGORITHM:
            aes_key = self._fernet_key_to_aes_bytes(key.key)
            nonce = os.urandom(12)
            encrypted = AESGCM(aes_key).encrypt(nonce, value.encode("utf-8"), None)
            ciphertext = encrypted[:-16]
            tag = encrypted[-16:]
            logger.debug(
                "env_value_encrypted algorithm=%s version=%d key_id=%s",
                algorithm,
                EncryptedValueEnvelopeV2.VERSION,
                key.key_id,
            )
            return EncryptedValueEnvelopeV2(
                enc=True,
                v=EncryptedValueEnvelopeV2.VERSION,
                alg=algorithm,
                kid=key.key_id,
                ct=base64.b64encode(ciphertext).decode("utf-8"),
                iv=base64.b64encode(nonce).decode("utf-8"),
                tag=base64.b64encode(tag).decode("utf-8"),
            )
        raise EnvironmentEncryptionError(
            f"Unsupported encrypted payload algorithm: {algorithm}"
        )

    def decrypt(self, payload: dict[str, Any]) -> str:
        self._ensure_crypto_available()
        envelope = EncryptedValueEnvelope.from_payload(payload)
        if isinstance(envelope, EncryptedValueEnvelopeV2):
            return self._decrypt_v2(envelope)
        key = self._key_provider.get_key_by_id(envelope.kid)
        logger.debug("env_value_decrypt_attempt key_id=%s", envelope.kid)
        return self._decrypt_token(envelope.ct, key)

    def _decrypt_v2(self, envelope: EncryptedValueEnvelopeV2) -> str:
        key = self._key_provider.get_key_by_id(envelope.kid)
        logger.debug(
            "env_value_decrypt_attempt key_id=%s version=%d algorithm=%s",
            envelope.kid,
            envelope.v,
            envelope.alg,
        )
        if envelope.alg == EncryptedValueEnvelopeV2.FERNET_ALGORITHM:
            return self._decrypt_token(envelope.ct, key)
        if envelope.alg == EncryptedValueEnvelopeV2.AES_GCM_ALGORITHM:
            return self._decrypt_aes_gcm(envelope, key)
        raise EnvironmentEncryptionError(
            f"Unsupported encrypted payload algorithm: {envelope.alg}"
        )

    @staticmethod
    def _fernet_key_to_aes_bytes(key_material: str) -> bytes:
        return base64.urlsafe_b64decode(key_material.encode("utf-8"))

    def _decrypt_aes_gcm(self, envelope: EncryptedValueEnvelopeV2, key: EncryptionKey) -> str:
        assert envelope.iv is not None
        assert envelope.tag is not None
        try:
            aes_key = self._fernet_key_to_aes_bytes(key.key)
            nonce = base64.b64decode(envelope.iv.encode("utf-8"))
            ciphertext = base64.b64decode(envelope.ct.encode("utf-8"))
            tag = base64.b64decode(envelope.tag.encode("utf-8"))
            raw = AESGCM(aes_key).decrypt(nonce, ciphertext + tag, None)
            logger.debug(
                "env_value_decrypted key_id=%s algorithm=%s",
                key.key_id,
                EncryptedValueEnvelopeV2.AES_GCM_ALGORITHM,
            )
            return raw.decode("utf-8")
        except (InvalidTag, ValueError, UnicodeDecodeError) as exc:
            logger.error(
                "env_value_decrypt_failed reason=invalid_token key_id=%s algorithm=%s",
                key.key_id,
                EncryptedValueEnvelopeV2.AES_GCM_ALGORITHM,
            )
            raise EnvironmentEncryptionError(
                "Encrypted environment value could not be decrypted with current key."
            ) from exc

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
