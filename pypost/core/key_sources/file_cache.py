"""In-process file payload cache invalidated by path mtime."""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class MtimeFileCache(Generic[T]):
    """Caches a loader result until the source file mtime changes."""

    def __init__(self) -> None:
        self._path: str | None = None
        self._mtime_ns: int | None = None
        self._value: T | None = None

    def get(self, path: Path, loader: Callable[[Path], T | None]) -> T | None:
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError:
            self._clear()
            return None
        path_key = str(path)
        if (
            self._path == path_key
            and self._mtime_ns == mtime_ns
            and self._value is not None
        ):
            return self._value
        value = loader(path)
        if value is None:
            self._clear()
            return None
        self._path = path_key
        self._mtime_ns = mtime_ns
        self._value = value
        return value

    def _clear(self) -> None:
        self._path = None
        self._mtime_ns = None
        self._value = None
