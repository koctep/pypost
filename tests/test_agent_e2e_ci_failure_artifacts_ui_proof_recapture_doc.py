"""PYPOST-933: lock PYPOST-911 live proof re-scan record in notes."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_NOTES = _REPO_ROOT / "ai-tasks" / "PYPOST-911" / "live-proof-notes.md"
_FAILURE_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e_failure_artifacts.md"

_RECAPTURE_ANCHOR = "PYPOST-933"
_DEFER_PHRASE = "defer"
_CAPTURED_PHRASE = "captured"
_RESCAN_HINT = "re-scan"


def test_live_proof_notes_record_pypost_933_rescan() -> None:
    """Notes must record the PYPOST-933 re-scan and honest status."""
    if not _NOTES.is_file():
        pytest.fail(
            f"Missing {_NOTES.relative_to(_REPO_ROOT)} — restore PYPOST-911 "
            "notes stub before recording PYPOST-933 re-scan"
        )
    text = _NOTES.read_text(encoding="utf-8")
    lower = text.lower()
    if _RECAPTURE_ANCHOR not in text:
        pytest.fail(
            f"{_NOTES.name}: must name {_RECAPTURE_ANCHOR} re-scan section"
        )
    if _RESCAN_HINT not in lower:
        pytest.fail(
            f"{_NOTES.name}: must document the {_RESCAN_HINT!r} performed "
            "for PYPOST-933"
        )
    if _DEFER_PHRASE not in lower and _CAPTURED_PHRASE not in lower:
        pytest.fail(
            f"{_NOTES.name}: must state DEFER or CAPTURED status honestly"
        )


def test_failure_doc_references_pypost_933_rescan() -> None:
    """Developer docs must mention PYPOST-933 re-check of proof status."""
    failure = _FAILURE_DOC.read_text(encoding="utf-8")
    if _RECAPTURE_ANCHOR not in failure:
        pytest.fail(
            f"Missing {_RECAPTURE_ANCHOR} in agent_e2e_failure_artifacts.md "
            "— document PYPOST-933 re-scan of live proof status"
        )
