"""PYPOST-873 / PYPOST-907: lock deferred CI agent-e2e double-run + evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

# Stable anchors for DEFER decision (must appear in developer docs).
_DOC_ANCHOR_873 = "PYPOST-873"
_DOC_ANCHOR_907 = "PYPOST-907"
_DOUBLE_RUN_PHRASE = "intentional double-run"
_REVISIT_PHRASE = "revisit when"
_EVIDENCE_PHRASE = "CI duration evidence"
_DEFER_AFTER_EVIDENCE = "DEFER after evidence"


def test_docs_record_deferred_ci_cost_trim() -> None:
    """DEFER decision, evidence review, and revisit criteria must be documented."""
    testing = _TESTING_DOC.read_text(encoding="utf-8")
    agent = _AGENT_E2E_DOC.read_text(encoding="utf-8")
    combined = f"{testing}\n{agent}"
    lower = combined.lower()
    if _DOC_ANCHOR_873 not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR_873} in {_TESTING_DOC.name} or "
            f"{_AGENT_E2E_DOC.name} — document DEFER CI cost trim"
        )
    if _DOC_ANCHOR_907 not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR_907} in {_TESTING_DOC.name} or "
            f"{_AGENT_E2E_DOC.name} — document evidence revisit"
        )
    if _DOUBLE_RUN_PHRASE not in lower:
        pytest.fail(
            f"Missing {_DOUBLE_RUN_PHRASE!r} (case-insensitive) in agent e2e / "
            "testing docs — explain intentional 3.11 overlap"
        )
    if _REVISIT_PHRASE not in lower:
        pytest.fail(
            f"Missing {_REVISIT_PHRASE!r} (case-insensitive) — document when "
            "to ENABLE a trim later"
        )
    if _EVIDENCE_PHRASE.lower() not in lower:
        pytest.fail(
            f"Missing {_EVIDENCE_PHRASE!r} (case-insensitive) — publish "
            "Actions timing notes for the overlap"
        )
    if _DEFER_AFTER_EVIDENCE.lower() not in lower:
        pytest.fail(
            f"Missing {_DEFER_AFTER_EVIDENCE!r} (case-insensitive) — state "
            "continued DEFER after the evidence review"
        )


def test_workflow_keeps_dual_agent_e2e_coverage() -> None:
    """Until ENABLE, main matrix must not exclude agent_e2e; job exists."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "\n  agent-e2e:\n" in text or "\n  agent-e2e:" in text, (
        f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job agent-e2e"
    )
    assert '-m "not slow"' in text, (
        f"{_WORKFLOW.relative_to(_REPO_ROOT)}: main pytest must use "
        '-m "not slow"'
    )
    assert "not agent_e2e" not in text, (
        f"{_WORKFLOW.relative_to(_REPO_ROOT)}: DEFER forbids excluding "
        "agent_e2e from the main matrix until an ENABLE story updates "
        "this lock"
    )
