"""PYPOST-909: lock ENABLE matrix upload of agent e2e failure artifacts."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FAILURE_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e_failure_artifacts.md"
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

# Stable anchors for matrix ENABLE decision (must appear in developer docs).
_DOC_ANCHOR = "PYPOST-909"
_ENABLE_PHRASE = "enable"
_MATRIX_UPLOAD_PHRASE = "agent-e2e-failure-artifacts-${{ matrix.python-version }}"
_FAILURE_GATE = "if: failure()"
_ARTIFACT_PATH = "artifacts/agent_e2e/"


def _test_job_block(workflow_text: str) -> str:
    """Return the main `test` job YAML block (until next top-level job)."""
    marker = "\n  test:"
    start = workflow_text.find(marker)
    if start < 0:
        alt = "  test:"
        start = workflow_text.find(alt)
        if start < 0:
            pytest.fail(
                f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job test"
            )
        start = workflow_text.rfind("\n", 0, start) + 1
    else:
        start += 1  # skip leading newline so block starts at "  test:"
    rest = workflow_text[start:]
    lines = rest.splitlines(keepends=True)
    collected: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("   "):
            if line.strip().endswith(":") and not line.strip().startswith("#"):
                key = line.strip()[:-1]
                if key and " " not in key and key != "test":
                    break
        collected.append(line)
    return "".join(collected)


def test_docs_record_enable_matrix_failure_artifact_upload() -> None:
    """ENABLE decision must be documented for main matrix failure upload."""
    failure = _FAILURE_DOC.read_text(encoding="utf-8")
    agent = _AGENT_E2E_DOC.read_text(encoding="utf-8")
    testing = _TESTING_DOC.read_text(encoding="utf-8")
    combined = f"{failure}\n{agent}\n{testing}"
    lower = combined.lower()
    if _DOC_ANCHOR not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR} in failure-artifacts / agent_e2e / "
            "testing docs — document ENABLE matrix failure upload"
        )
    if _ENABLE_PHRASE not in lower:
        pytest.fail(
            f"Missing {_ENABLE_PHRASE!r} (case-insensitive) — document "
            "ENABLE decision for main test matrix failure artifact upload"
        )
    if "matrix" not in lower:
        pytest.fail(
            "Missing 'matrix' (case-insensitive) — document main test "
            "matrix agent e2e failure artifact upload"
        )
    if "agent-e2e-failure-artifacts-" not in combined:
        pytest.fail(
            "Missing matrix artifact name prefix "
            "'agent-e2e-failure-artifacts-' — name the per-version "
            "Actions artifact for download after matrix failure"
        )


def test_workflow_uploads_agent_e2e_artifacts_on_test_matrix_failure() -> None:
    """Job test must upload artifacts/agent_e2e/ when the matrix cell fails."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    block = _test_job_block(text)
    if "upload-artifact" not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job test: missing "
            "actions/upload-artifact (expected existing + failure dumps)"
        )
    if _ARTIFACT_PATH not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job test: upload path "
            f"must include {_ARTIFACT_PATH!r}"
        )
    if _FAILURE_GATE not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job test: agent e2e "
            f"dump upload must use {_FAILURE_GATE!r} (failure-only)"
        )
    if _MATRIX_UPLOAD_PHRASE not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job test: artifact "
            f"name must be {_MATRIX_UPLOAD_PHRASE!r}"
        )
