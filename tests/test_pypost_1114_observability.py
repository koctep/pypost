"""Observability contract for MtimeFileCache race paths (PYPOST-1114, AC-7).

The cache logs only the path (and an ``OSError`` reason) when a loaded value is returned
uncached. No file content, digest or other content-derived value may appear in log records,
and the normal miss/hit paths stay silent.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pytest

from pypost.core.key_sources import file_cache as file_cache_module
from pypost.core.key_sources.file_cache import MtimeFileCache

pytestmark = pytest.mark.timeout(30)

LOGGER_NAME = "pypost.core.key_sources.file_cache"
V1 = "KEYMATERIAL-v1-7f3a"
V2 = "KEYMATERIAL-v2-9c1e"


def _forbidden_fragments(*contents: str) -> list[str]:
    """Return content and every digest encoding that must never reach the logs."""
    fragments: list[str] = []
    for text in contents:
        raw = text.encode("utf-8")
        digest = hashlib.sha256(raw).digest()
        fragments += [text, digest.hex(), repr(digest)]
    return fragments


def _assert_no_content_leak(caplog: pytest.LogCaptureFixture, *contents: str) -> None:
    """Assert no captured record text or args contain content-derived values."""
    for record in caplog.records:
        rendered = record.getMessage()
        args_text = repr(record.args)
        for fragment in _forbidden_fragments(*contents):
            assert fragment not in rendered, f"leaked {fragment!r} in {rendered!r}"
            assert fragment not in args_text, f"leaked {fragment!r} in args {args_text!r}"


def test_rewrite_during_load_logs_path_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A rewrite during load emits one DEBUG event with the path and no content/digest."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "keys.json"
    target.write_text(V1, encoding="utf-8")

    def racing_loader(path: Path) -> str | None:
        path.write_text(V2, encoding="utf-8")
        return V1

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        assert cache.get(target, racing_loader) == V1

    records = [r for r in caplog.records if r.name == LOGGER_NAME]
    assert [r.levelno for r in records] == [logging.DEBUG]
    assert records[0].getMessage() == f"file_cache_rewrite_during_load path={target}"
    _assert_no_content_leak(caplog, V1, V2)


def test_recheck_failure_logs_path_and_reason_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed post-load re-read emits one DEBUG event with path and OSError reason."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "keys.json"
    target.write_text(V1, encoding="utf-8")
    real_digest = file_cache_module._digest_file
    calls: list[Path] = []

    def flaky_digest(path: Path) -> bytes:
        calls.append(path)
        if len(calls) == 2:
            raise PermissionError("permission denied")
        return real_digest(path)

    monkeypatch.setattr(file_cache_module, "_digest_file", flaky_digest)

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        assert cache.get(target, lambda p: p.read_text(encoding="utf-8")) == V1

    records = [r for r in caplog.records if r.name == LOGGER_NAME]
    assert [r.levelno for r in records] == [logging.DEBUG]
    assert records[0].getMessage() == (
        f"file_cache_recheck_failed path={target} reason=permission denied"
    )
    _assert_no_content_leak(caplog, V1)


def test_normal_miss_and_hit_are_silent(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The steady-state miss and hit paths emit no log records (no hot-path noise)."""
    cache: MtimeFileCache[str] = MtimeFileCache()
    target = tmp_path / "keys.json"
    target.write_text(V1, encoding="utf-8")

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        assert cache.get(target, lambda p: p.read_text(encoding="utf-8")) == V1
        assert cache.get(target, lambda p: p.read_text(encoding="utf-8")) == V1
        target.write_text(V2, encoding="utf-8")
        assert cache.get(target, lambda p: p.read_text(encoding="utf-8")) == V2

    assert [r for r in caplog.records if r.name == LOGGER_NAME] == []
