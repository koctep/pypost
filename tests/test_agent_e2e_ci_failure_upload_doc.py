"""PYPOST-874: lock ENABLE CI upload of agent e2e failure artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FAILURE_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e_failure_artifacts.md"
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

# Stable anchors for ENABLE decision (must appear in developer docs).
_DOC_ANCHOR = "PYPOST-874"
_ENABLE_PHRASE = "enable"
_UPLOAD_PHRASE = "agent-e2e-failure-artifacts"
_FAILURE_GATE = "if: failure()"
_ARTIFACT_PATH = "artifacts/agent_e2e/"


def _agent_e2e_job_block(workflow_text: str) -> str:
    """Return the agent-e2e job YAML block (until next top-level job)."""
    marker = "\n  agent-e2e:"
    start = workflow_text.find(marker)
    if start < 0:
        # Allow job at file start without leading newline.
        alt = "  agent-e2e:"
        start = workflow_text.find(alt)
        if start < 0:
            pytest.fail(
                f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job agent-e2e"
            )
        start = workflow_text.rfind("\n", 0, start) + 1
    else:
        start += 1  # skip leading newline so block starts at "  agent-e2e:"
    rest = workflow_text[start:]
    # Next job at indent of two spaces then name then colon (siblings).
    lines = rest.splitlines(keepends=True)
    collected: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("   "):
            # Another top-level job key under `jobs:` (two-space indent, no deeper).
            if line.strip().endswith(":") and not line.strip().startswith("#"):
                key = line.strip()[:-1]
                if key and " " not in key and key != "agent-e2e":
                    break
        collected.append(line)
    return "".join(collected)


def test_docs_record_enable_failure_artifact_upload() -> None:
    """ENABLE decision must be documented for CI failure artifact upload."""
    failure = _FAILURE_DOC.read_text(encoding="utf-8")
    agent = _AGENT_E2E_DOC.read_text(encoding="utf-8")
    testing = _TESTING_DOC.read_text(encoding="utf-8")
    combined = f"{failure}\n{agent}\n{testing}"
    lower = combined.lower()
    if _DOC_ANCHOR not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR} in failure-artifacts / agent_e2e / "
            "testing docs — document ENABLE CI failure upload"
        )
    if _ENABLE_PHRASE not in lower:
        pytest.fail(
            f"Missing {_ENABLE_PHRASE!r} (case-insensitive) — document "
            "ENABLE decision for agent-e2e failure artifact upload"
        )
    if _UPLOAD_PHRASE not in combined:
        pytest.fail(
            f"Missing {_UPLOAD_PHRASE!r} — name the Actions artifact for "
            "download after agent-e2e failure"
        )


def test_workflow_uploads_agent_e2e_artifacts_on_failure() -> None:
    """Job agent-e2e must upload artifacts/agent_e2e/ when the job fails."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    block = _agent_e2e_job_block(text)
    if "upload-artifact" not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job agent-e2e: missing "
            "actions/upload-artifact for failure dumps"
        )
    if _ARTIFACT_PATH not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job agent-e2e: upload path "
            f"must include {_ARTIFACT_PATH!r}"
        )
    if _FAILURE_GATE not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job agent-e2e: upload must "
            f"use {_FAILURE_GATE!r} (failure-only)"
        )
    if _UPLOAD_PHRASE not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job agent-e2e: artifact "
            f"name must be {_UPLOAD_PHRASE!r}"
        )
