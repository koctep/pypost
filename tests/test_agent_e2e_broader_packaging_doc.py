"""PYPOST-922 / PYPOST-938: lock broader-than-golden packaging docs.

873-style substring/token guards (KEEP per PYPOST-938 — see
doc/dev/testing.md § Packaging doc lock strategy).
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_docs_attribute_broader_packaging_to_pypost_922() -> None:
    """At least one packaging doc must anchor PYPOST-922."""
    combined = "\n".join(
        _read(p) for p in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC)
    )
    if _DOC_ANCHOR not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR} in {_AGENT_E2E_DOC.name}, "
            f"{_GOLDEN_DOC.name}, or {_TESTING_DOC.name} — attribute broader "
            "packaging close to this debt"
        )


def test_docs_frame_primary_path_as_broader_beyond_golden() -> None:
    """Umbrella, golden, and testing docs must frame broader beyond golden."""
    for path in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC):
        text = _read(path)
        lower = text.lower()
        if _MAKE_ENTRY not in lower:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing {_MAKE_ENTRY!r} "
                "as the documented packaging entry"
            )
        if _BEYOND_GOLDEN not in lower:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing "
                f"{_BEYOND_GOLDEN!r} (case-insensitive) — frame the pack as "
                "broader agent e2e beyond the golden scenario"
            )
        if "broader" not in lower:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing 'broader' "
                "(case-insensitive) — name the broader pack path"
            )


def test_docs_state_primary_packaging_vs_golden_pytest_args_narrow() -> None:
    """Docs must call out primary broader packaging vs golden PYTEST_ARGS."""
    for path in (_AGENT_E2E_DOC, _GOLDEN_DOC, _TESTING_DOC):
        text = _read(path)
        lower = text.lower()
        if _PRIMARY_BROADER not in lower:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing "
                f"{_PRIMARY_BROADER!r} (case-insensitive) — state that "
                "make test-agent-e2e is the primary packaging path"
            )
        if "pytest_args" not in lower:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing PYTEST_ARGS — "
                "document golden-only / single-module narrow override"
            )
        if "agent_golden_e2e" not in lower and _GOLDEN_NARROW not in text:
            pytest.fail(
                f"{path.relative_to(_REPO_ROOT)}: missing golden module "
                "reference (test_agent_golden_e2e) for the narrow override"
            )
