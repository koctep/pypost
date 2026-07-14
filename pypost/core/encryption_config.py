from __future__ import annotations

import logging
import os
from typing import Optional

from pypost.core.key_provider import ChainedKeyProvider, KeyProvider
from pypost.core.key_source_constants import (
    DEFAULT_KEY_SOURCE,
    EncryptionKeySource,
    SUPPORTED_KEY_SOURCES,
)
from pypost.core.key_sources.chain import KeySourceChain
from pypost.core.key_sources.factory import create_key_source
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

ENCRYPTION_ENABLED_ENV = "PYPOST_ENV_ENCRYPTION_ENABLED"


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


def resolve_key_source_chain(settings: Optional[AppSettings]) -> list[str]:
    primary = resolve_key_source(settings)
    chain = [primary]
    if settings is not None and settings.env_encryption_key_source_fallback:
        for source in settings.env_encryption_key_source_fallback:
            if source in SUPPORTED_KEY_SOURCES and source not in chain:
                chain.append(source)
    return chain


def build_key_provider(settings: Optional[AppSettings] = None) -> KeyProvider:
    source_chain = resolve_key_source_chain(settings)
    logger.info(
        "encryption_key_provider_built source_chain=%s",
        ",".join(source_chain),
    )
    sources = [create_key_source(source) for source in source_chain]
    return ChainedKeyProvider(KeySourceChain(sources))
