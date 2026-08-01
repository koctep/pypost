"""PYPOST-911: lock DEFER live Artifacts UI proof procedure in docs."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FAILURE_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e_failure_artifacts.md"
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_NOTES = _REPO_ROOT / "ai-tasks" / "PYPOST-911" / "live-proof-notes.md"

_DOC_ANCHOR = "PYPOST-911"
_DEFER_PHRASE = "defer"
_UPLOAD_PHRASE = "agent-e2e-failure-artifacts"
_CHECKLIST_HINT = "what to capture"
_NOTES_HINT = "live-proof-notes.md"


def test_docs_record_deferred_artifacts_ui_proof_procedure() -> None:
    """Docs must name PYPOST-911 and the DEFER / capture procedure."""
    failure = _FAILURE_DOC.read_text(encoding="utf-8")
    agent = _AGENT_E2E_DOC.read_text(encoding="utf-8")
    testing = _TESTING_DOC.read_text(encoding="utf-8")
    combined = f"{failure}\n{agent}\n{testing}"
    lower = combined.lower()
    if _DOC_ANCHOR not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR} in failure-artifacts / agent_e2e / "
            "testing docs — document deferred Artifacts UI proof"
        )
    if _DEFER_PHRASE not in lower:
        pytest.fail(
            f"Missing {_DEFER_PHRASE!r} (case-insensitive) — document "
            "honest DEFER of live Artifacts UI screenshot/notes"
        )
    if _UPLOAD_PHRASE not in combined:
        pytest.fail(
            f"Missing {_UPLOAD_PHRASE!r} — name the Actions artifact for "
            "the live proof checklist"
        )
    if _CHECKLIST_HINT not in lower:
        pytest.fail(
            f"Missing {_CHECKLIST_HINT!r} — document checklist of what to "
            "capture from a failing Actions run"
        )
    if _NOTES_HINT not in combined:
        pytest.fail(
            f"Missing {_NOTES_HINT!r} — document where maintainers put "
            "proof notes / screenshot references"
        )


def test_live_proof_notes_stub_exists_for_maintainers() -> None:
    """Task notes stub must exist so maintainers know where to record proof."""
    if not _NOTES.is_file():
        pytest.fail(
            f"Missing {_NOTES.relative_to(_REPO_ROOT)} — create a stub "
            "with checklist and DEFER status for future live proof"
        )
    text = _NOTES.read_text(encoding="utf-8")
    lower = text.lower()
    if _DOC_ANCHOR not in text:
        pytest.fail(f"{_NOTES.name}: must name {_DOC_ANCHOR}")
    if _DEFER_PHRASE not in lower and "captured" not in lower:
        pytest.fail(
            f"{_NOTES.name}: must state DEFER status or that proof was "
            "captured (do not leave status ambiguous)"
        )
    if "checklist" not in lower:
        pytest.fail(f"{_NOTES.name}: must include a capture checklist")
