"""PYPOST-922 / PYPOST-938 / PYPOST-954: lock broader-than-golden packaging docs.

873-style substring/token guards via tests.helpers.packaging_doc_lock — see
doc/dev/testing.md § Packaging doc lock strategy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.packaging_doc_lock import (
    assert_substring,
    doc_label,
    read_doc,
)

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_GOLDEN_DOC = _REPO_ROOT / "doc" / "dev" / "agent_golden_e2e.md"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"

_DOC_ANCHOR = "PYPOST-922"
_BEYOND_GOLDEN = "beyond golden"
_PRIMARY_BROADER = "primary packaging"
_MAKE_ENTRY = "make test-agent-e2e"
_GOLDEN_NARROW = "test_agent_golden_e2e.py"


def test_docs_attribute_broader_packaging_to_pypost_922() -> None:
    """At least one packaging doc must anchor PYPOST-922."""
    combined = "\n".join(
        read_doc(p) for p in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC)
    )
    assert_substring(
        combined,
        _DOC_ANCHOR,
        doc_label_str=f"{_AGENT_E2E_DOC.name}, {_GOLDEN_DOC.name}, or "
        f"{_TESTING_DOC.name}",
        detail="attribute broader packaging close to this debt",
    )


def test_docs_frame_primary_path_as_broader_beyond_golden() -> None:
    """Umbrella, golden, and testing docs must frame broader beyond golden."""
    for path in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC):
        text = read_doc(path)
        label = doc_label(path, _REPO_ROOT)
        assert_substring(
            text,
            _MAKE_ENTRY,
            case_insensitive=True,
            doc_label_str=label,
            detail="document the packaging entry",
        )
        assert_substring(
            text,
            _BEYOND_GOLDEN,
            case_insensitive=True,
            doc_label_str=label,
            detail=(
                "frame the pack as broader agent e2e beyond the golden scenario"
            ),
        )
        assert_substring(
            text,
            "broader",
            case_insensitive=True,
            doc_label_str=label,
            detail="name the broader pack path",
        )


def test_docs_state_primary_packaging_vs_golden_pytest_args_narrow() -> None:
    """Docs must call out primary broader packaging vs golden PYTEST_ARGS."""
    for path in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC):
        text = read_doc(path)
        label = doc_label(path, _REPO_ROOT)
        assert_substring(
            text,
            _PRIMARY_BROADER,
            case_insensitive=True,
            doc_label_str=label,
            detail="state that make test-agent-e2e is the primary packaging path",
        )
        assert_substring(
            text,
            "pytest_args",
            case_insensitive=True,
            doc_label_str=label,
            detail="document golden-only / single-module narrow override",
        )
        lower = text.lower()
        if "agent_golden_e2e" not in lower and _GOLDEN_NARROW not in text:
            pytest.fail(
                f"{label}: missing golden module reference "
                "(test_agent_golden_e2e) for the narrow override"
            )
