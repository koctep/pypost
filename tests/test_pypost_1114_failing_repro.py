"""Regression tests for same-tick rewrite races in MtimeFileCache (PYPOST-1114).

Written as the Step 3 failing repro; green since the cache switched to content-digest identity.
Each test forces the "same mtime, different content" state deterministically by pinning the
file mtime with ``os.utime(ns=...)`` after a rewrite, so the result does not depend on the
filesystem timestamp resolution. No cache ``clear()`` / ``clear_registry_cache()`` /
``clear_spec_cache()`` is called after the initial state (the conftest autouse fixture clears
caches only before/after each test).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable

import pytest

from pypost.core.encryption_key import build_key_id
from pypost.core.key_sources.env import EnvKeySource
from pypost.core.key_sources.file_cache import MtimeFileCache
from pypost.core.key_sources.secret_store import SECRETS_FILE_ENV, SecretStoreKeySource

pytestmark = pytest.mark.timeout(30)


def _rewrite_same_mtime(path: Path, text: str) -> None:
    """Rewrite ``path`` with ``text`` and pin mtime back to its pre-write value."""
    st = path.stat()
    path.write_text(text, encoding="utf-8")
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert path.stat().st_mtime_ns == st.st_mtime_ns, "mtime pin did not take effect"


def _counting_text_loader() -> tuple[list[Path], Callable[[Path], str | None]]:
    """Return ``(calls, loader)``; ``loader`` reads UTF-8 text and records each call."""
    calls: list[Path] = []

    def loader(path: Path) -> str | None:
        calls.append(path)
        return path.read_text(encoding="utf-8")

    return calls, loader


def _registry_json(active_id: str, keys: dict[str, str]) -> str:
    """Serialize a key registry payload with ``active_id`` and ``keys``."""
    return json.dumps({"active_key_id": active_id, "keys": keys})


def test_generic_cache_same_mtime_same_length_rewrite_reloads(tmp_path: Path) -> None:
    """AC-3: a same-length rewrite with an unchanged mtime must be reloaded."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "payload.txt"
    target.write_text("AAAA", encoding="utf-8")
    calls, loader = _counting_text_loader()

    assert cache.get(target, loader) == "AAAA"

    _rewrite_same_mtime(target, "BBBB")
    assert cache.get(target, loader) == "BBBB", (
        "stale cached value served after same-mtime same-length rewrite"
    )
    assert len(calls) == 2


def test_registry_two_rapid_rewrites_resolve_latest_active_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-1, AC-4: two rewrites within one mtime tick resolve the latest active key."""
    fernet = pytest.importorskip("cryptography.fernet")
    k1, k2, k3 = (fernet.Fernet.generate_key().decode("utf-8") for _ in range(3))
    id1, id2, id3 = build_key_id(k1), build_key_id(k2), build_key_id(k3)
    registry_path = tmp_path / "keys.json"
    registry_path.write_text(_registry_json(id1, {id1: k1}), encoding="utf-8")
    monkeypatch.setenv(EnvKeySource.KEYS_FILE, str(registry_path))
    monkeypatch.delenv(EnvKeySource.ENV_KEY, raising=False)
    source = EnvKeySource()

    first = source.try_resolve_active()
    assert first is not None and first.key_id == id1

    _rewrite_same_mtime(registry_path, _registry_json(id2, {id1: k1, id2: k2}))
    second = source.try_resolve_active()
    assert second is not None
    assert second.key_id == id2, "stale active key after first same-mtime registry rewrite"

    _rewrite_same_mtime(registry_path, _registry_json(id3, {id1: k1, id2: k2, id3: k3}))
    third = source.try_resolve_active()
    assert third is not None
    assert third.key_id == id3, "stale active key after second same-mtime registry rewrite"

    by_id = source.try_resolve_by_id(id3)
    assert by_id is not None
    assert by_id.key == k3


def test_spec_same_mtime_rewrite_reloads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-2: a same-mtime spec rewrite is visible on the next spec load."""
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps({"marker": "one", "backends": []}), encoding="utf-8")
    monkeypatch.setenv(SECRETS_FILE_ENV, str(spec_path))
    source = SecretStoreKeySource()

    first = source._load_spec()
    assert first is not None and first["marker"] == "one"

    _rewrite_same_mtime(spec_path, json.dumps({"marker": "two", "backends": []}))
    second = source._load_spec()
    assert second is not None
    assert second["marker"] == "two", "stale spec served after same-mtime rewrite"


def test_unchanged_file_is_not_reparsed(tmp_path: Path) -> None:
    """AC-5 guard: an unchanged file is parsed once across repeated lookups."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "payload.txt"
    target.write_text("stable", encoding="utf-8")
    calls, loader = _counting_text_loader()

    for _ in range(3):
        assert cache.get(target, loader) == "stable"
    assert len(calls) == 1


def test_touch_only_change_is_not_reparsed(tmp_path: Path) -> None:
    """Design semantics: an mtime-only change with identical bytes does not re-parse."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "payload.txt"
    target.write_text("same", encoding="utf-8")
    calls, loader = _counting_text_loader()

    assert cache.get(target, loader) == "same"

    st = target.stat()
    bumped_mtime_ns = st.st_mtime_ns + 5_000_000_000
    os.utime(target, ns=(st.st_atime_ns, bumped_mtime_ns))
    assert target.stat().st_mtime_ns == bumped_mtime_ns, "mtime bump did not take effect"

    assert cache.get(target, loader) == "same"
    assert len(calls) == 1, f"loader re-parsed identical bytes after touch: calls={len(calls)}"


def test_rewrite_during_load_is_not_cached_then_rollback_reloads(tmp_path: Path) -> None:
    """Hash/load race: a value loaded while the file changed must not stay cached."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "payload.txt"
    target.write_text("v1", encoding="utf-8")
    st = target.stat()
    calls: list[Path] = []

    def racing_loader(path: Path) -> str | None:
        calls.append(path)
        if len(calls) == 1:
            path.write_text("v2", encoding="utf-8")
        return path.read_text(encoding="utf-8")

    assert cache.get(target, racing_loader) == "v2"

    target.write_text("v1", encoding="utf-8")
    os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert target.stat().st_mtime_ns == st.st_mtime_ns, "mtime pin did not take effect"

    assert cache.get(target, racing_loader) == "v1", (
        "stale value from racing load served after rollback"
    )
    assert len(calls) == 2
