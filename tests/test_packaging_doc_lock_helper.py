"""PYPOST-954: shared packaging doc-lock helper for contract tests."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest
from _pytest.outcomes import Failed

from tests.helpers.packaging_doc_lock import (
    assert_any_substring,
    assert_substring,
    doc_label,
    read_doc,
)

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SAMPLE_DOC = _REPO_ROOT / "doc" / "dev" / "ui_actions.md"

_CONTRACT_MODULES = (
    "tests.test_ui_actions_mcp_packaging_doc",
    "tests.test_agent_e2e_broader_packaging_doc",
)


def test_read_doc_reads_committed_ui_actions_doc() -> None:
    """read_doc must load UTF-8 Markdown from the repo."""
    text = read_doc(_SAMPLE_DOC)
    assert "ui_actions" in text.lower() or "UI Action" in text


def test_doc_label_relative_to_repo_root() -> None:
    """doc_label prefers repo-relative paths in failure messages."""
    label = doc_label(_SAMPLE_DOC, repo_root=_REPO_ROOT)
    assert label == "doc/dev/ui_actions.md"


def test_assert_substring_passes_when_present() -> None:
    """assert_substring is a no-op when the token exists."""
    assert_substring(
        "Hello World",
        "world",
        case_insensitive=True,
        doc_label_str="sample",
        detail="demo",
    )


def test_assert_substring_fails_when_missing() -> None:
    """Missing tokens must fail with pytest.fail."""
    with pytest.raises(Failed, match="missing 'nope'"):
        assert_substring(
            "Hello",
            "nope",
            doc_label_str="sample",
            detail="demo",
        )


def test_assert_any_substring_passes_on_first_match() -> None:
    """assert_any_substring succeeds when any token matches."""
    assert_any_substring(
        "never mount",
        ("never register", "never mount"),
        case_insensitive=True,
        doc_label_str="sample",
        detail="demo",
    )


def test_assert_any_substring_fails_when_none_match() -> None:
    """assert_any_substring fails when no token matches."""
    with pytest.raises(Failed, match="missing token lock"):
        assert_any_substring(
            "Hello",
            ("never mount", "never register"),
            doc_label_str="sample",
            detail="demo",
        )


def test_packaging_doc_lock_modules_use_shared_helper() -> None:
    """Packaging doc-lock modules must import shared helper (PYPOST-954)."""
    missing: list[str] = []
    for mod_name in _CONTRACT_MODULES:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        if "from tests.helpers.packaging_doc_lock import" not in source:
            missing.append(mod_name)
        if hasattr(mod, "_read"):
            missing.append(f"{mod_name} (local _read)")
    if missing:
        pytest.fail(
            "Packaging doc-lock modules must use tests.helpers.packaging_doc_lock: "
            + ", ".join(missing)
        )
