from __future__ import annotations

import logging

from pypost.core.encryption_key import EncryptionKey
from pypost.core.key_sources.protocol import KeySource

logger = logging.getLogger(__name__)


class KeySourceChain:
    """Ordered fallback across key sources for active and by-id resolution."""

    def __init__(self, sources: list[KeySource]) -> None:
        self._sources = sources

    def _source_names(self) -> str:
        return ",".join(source.name for source in self._sources)

    def resolve_active(self) -> EncryptionKey | None:
        if not self._sources:
            return None
        logger.info("key_source_chain_active_attempt sources=%s", self._source_names())
        for index, source in enumerate(self._sources):
            key = source.try_resolve_active()
            if key is not None:
                logger.debug(
                    "key_source_chain_active_resolved source=%s key_id=%s",
                    source.name,
                    key.key_id,
                )
                if index > 0:
                    skipped = ",".join(s.name for s in self._sources[:index])
                    logger.info(
                        "key_source_chain_active_resolved_via_fallback "
                        "source=%s key_id=%s skipped_sources=%s",
                        source.name,
                        key.key_id,
                        skipped,
                    )
                return key
            logger.debug("key_source_chain_active_unavailable source=%s", source.name)
            if index + 1 < len(self._sources):
                logger.warning(
                    "key_source_chain_active_fallback failed_source=%s next_source=%s",
                    source.name,
                    self._sources[index + 1].name,
                )
        return None

    def resolve_by_id(self, key_id: str) -> EncryptionKey | None:
        if not self._sources:
            return None
        logger.info(
            "key_source_chain_by_id_attempt key_id=%s sources=%s",
            key_id,
            self._source_names(),
        )
        for index, source in enumerate(self._sources):
            key = source.try_resolve_by_id(key_id)
            if key is not None:
                logger.debug(
                    "key_source_chain_by_id_resolved source=%s key_id=%s",
                    source.name,
                    key_id,
                )
                if index > 0:
                    skipped = ",".join(s.name for s in self._sources[:index])
                    logger.info(
                        "key_source_chain_by_id_resolved_via_fallback "
                        "source=%s key_id=%s skipped_sources=%s",
                        source.name,
                        key_id,
                        skipped,
                    )
                return key
            logger.debug(
                "key_source_chain_by_id_unavailable source=%s key_id=%s",
                source.name,
                key_id,
            )
            if index + 1 < len(self._sources):
                logger.warning(
                    "key_source_chain_by_id_fallback failed_source=%s key_id=%s " "next_source=%s",
                    source.name,
                    key_id,
                    self._sources[index + 1].name,
                )
        return None
