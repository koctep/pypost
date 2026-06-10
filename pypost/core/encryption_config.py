import logging
import os
from typing import Literal, Optional

from pypost.core.key_provider import KeyProvider, LocalKeyProvider
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

EncryptionKeySource = Literal["environment"]
DEFAULT_KEY_SOURCE: EncryptionKeySource = "environment"
ENCRYPTION_ENABLED_ENV = "PYPOST_ENV_ENCRYPTION_ENABLED"
SUPPORTED_KEY_SOURCES = frozenset({"environment"})


def _env_encryption_enabled() -> bool:
    value = os.getenv(ENCRYPTION_ENABLED_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def resolve_encryption_enabled(settings: Optional[AppSettings]) -> bool:
    if settings is not None and settings.env_encryption_enabled is not None:
        return settings.env_encryption_enabled
    return _env_encryption_enabled()


def resolve_key_source(settings: Optional[AppSettings]) -> EncryptionKeySource:
    if settings is not None and settings.env_encryption_key_source is not None:
        source = settings.env_encryption_key_source
        if source not in SUPPORTED_KEY_SOURCES:
            logger.warning(
                "encryption_key_source_unsupported source=%s fallback=%s",
                source,
                DEFAULT_KEY_SOURCE,
            )
            return DEFAULT_KEY_SOURCE
        return source  # type: ignore[return-value]
    return DEFAULT_KEY_SOURCE


def build_key_provider(source: EncryptionKeySource) -> KeyProvider:
    if source == "environment":
        return LocalKeyProvider()
    raise ValueError(f"Unsupported encryption key source: {source}")
