"""Shared helpers for packaging doc-token contract tests (873-style locks)."""

from __future__ import annotations

from pathlib import Path

import pytest


def read_doc(path: Path) -> str:
    """Read a UTF-8 Markdown doc from disk."""
    return path.read_text(encoding="utf-8")


def doc_label(path: Path, repo_root: Path | None = None) -> str:
    """Return a repo-relative path label for failure messages."""
    if repo_root is not None:
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            pass
    return str(path)


def assert_substring(
    text: str,
    token: str,
    *,
    case_insensitive: bool = False,
    doc_label_str: str,
    detail: str,
) -> None:
    """Fail when *token* is absent from *text*."""
    haystack = text.lower() if case_insensitive else text
    needle = token.lower() if case_insensitive else token
    if needle not in haystack:
        suffix = " (case-insensitive)" if case_insensitive else ""
        pytest.fail(
            f"{doc_label_str}: missing {token!r}{suffix} — {detail}"
        )


def assert_any_substring(
    text: str,
    tokens: tuple[str, ...],
    *,
    case_insensitive: bool = False,
    doc_label_str: str,
    detail: str,
) -> None:
    """Fail when none of *tokens* appear in *text*."""
    haystack = text.lower() if case_insensitive else text
    for token in tokens:
        needle = token.lower() if case_insensitive else token
        if needle in haystack:
            return
    suffix = ", case-insensitive" if case_insensitive else ""
    pytest.fail(
        f"{doc_label_str}: missing token lock (need one of {tokens!r}{suffix}) "
        f"— {detail}"
    )
