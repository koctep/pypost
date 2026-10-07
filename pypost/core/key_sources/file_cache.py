"""In-process file payload cache keyed by path and content digest.

Identity is ``(path, sha256(file bytes))``; mtime is not used, so rewrites that land within one
timestamp tick (or keep the mtime) are still detected. The digest stays in a private attribute
and is never logged or returned; log events carry only the path and an ``OSError`` reason.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable, Generic, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def _digest_file(path: Path) -> bytes:
    """Return the SHA-256 digest of the file bytes; raises ``OSError`` if unreadable."""
    return hashlib.sha256(path.read_bytes()).digest()


class MtimeFileCache(Generic[T]):
    """Caches a loader result until the source file content changes.

    The class name is historical: invalidation is content-based, not mtime-based.
    """

    def __init__(self) -> None:
        self._path: str | None = None
        self._digest: bytes | None = None
        self._value: T | None = None

    def get(self, path: Path, loader: Callable[[Path], T | None]) -> T | None:
        """Return the cached value for ``path`` or (re)load it when the content changed.

        On a miss the file is re-hashed after loading; the value is cached only if the content
        did not change during the load, otherwise it is returned uncached.
        """
        try:
            digest = _digest_file(path)
        except OSError:
            self._clear()
            return None
        path_key = str(path)
        if (
            self._path == path_key
            and self._digest == digest
            and self._value is not None
        ):
            return self._value
        value = loader(path)
        if value is None:
            self._clear()
            return None
        try:
            digest_after = _digest_file(path)
        except OSError as exc:
            logger.debug("file_cache_recheck_failed path=%s reason=%s", path, exc)
            self._clear()
            return value
        if digest_after != digest:
            logger.debug("file_cache_rewrite_during_load path=%s", path)
            self._clear()
            return value
        self._path = path_key
        self._digest = digest
        self._value = value
        return value

    def clear(self) -> None:
        """Clear cached state."""
        self._path = None
        self._digest = None
        self._value = None

    def _clear(self) -> None:
        self.clear()
