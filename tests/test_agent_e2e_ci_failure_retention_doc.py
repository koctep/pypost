"""PYPOST-910: lock retention-days on agent e2e failure artifact uploads."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FAILURE_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e_failure_artifacts.md"
_AGENT_E2E_DOC = _REPO_ROOT / "doc" / "dev" / "agent_e2e.md"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

_DOC_ANCHOR = "PYPOST-910"
_RETENTION_DAYS = "14"
_RETENTION_KEY = "retention-days: 14"
_ARTIFACT_PATH = "artifacts/agent_e2e/"


def _job_block(workflow_text: str, job_key: str) -> str:
    """Return a top-level job YAML block (until next sibling job)."""
    marker = f"\n  {job_key}:"
    start = workflow_text.find(marker)
    if start < 0:
        alt = f"  {job_key}:"
        start = workflow_text.find(alt)
        if start < 0:
            pytest.fail(
                f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job {job_key}"
            )
        start = workflow_text.rfind("\n", 0, start) + 1
    else:
        start += 1  # skip leading newline so block starts at "  {job}:"
    rest = workflow_text[start:]
    lines = rest.splitlines(keepends=True)
    collected: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("   "):
            if line.strip().endswith(":") and not line.strip().startswith("#"):
                key = line.strip()[:-1]
                if key and " " not in key and key != job_key:
                    break
        collected.append(line)
    return "".join(collected)


def _assert_failure_upload_has_retention(block: str, job_key: str) -> None:
    """Require retention-days near the agent e2e failure dump upload."""
    if _ARTIFACT_PATH not in block:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job {job_key}: missing "
            f"failure dump path {_ARTIFACT_PATH!r}"
        )
    # Slice from the dump path step onward so junit/coverage retention
    # (if ever added) does not satisfy this assert by accident.
    path_idx = block.find(_ARTIFACT_PATH)
    dump_region = block[path_idx:]
    if _RETENTION_KEY not in dump_region:
        pytest.fail(
            f"{_WORKFLOW.relative_to(_REPO_ROOT)} job {job_key}: agent e2e "
            f"failure upload must set {_RETENTION_KEY!r}"
        )


def test_docs_record_failure_artifact_retention_days() -> None:
    """Docs must name PYPOST-910 and the 14-day retention policy."""
    failure = _FAILURE_DOC.read_text(encoding="utf-8")
    agent = _AGENT_E2E_DOC.read_text(encoding="utf-8")
    testing = _TESTING_DOC.read_text(encoding="utf-8")
    combined = f"{failure}\n{agent}\n{testing}"
    lower = combined.lower()
    if _DOC_ANCHOR not in combined:
        pytest.fail(
            f"Missing {_DOC_ANCHOR} in failure-artifacts / agent_e2e / "
            "testing docs — document retention-days for failure uploads"
        )
    if "retention" not in lower:
        pytest.fail(
            "Missing 'retention' (case-insensitive) — document Actions "
            "artifact retention for agent e2e failure uploads"
        )
    if _RETENTION_DAYS not in combined:
        pytest.fail(
            f"Missing retention value {_RETENTION_DAYS!r} — docs must "
            "state how many days failure artifacts are kept"
        )


def test_workflow_sets_retention_on_agent_e2e_failure_uploads() -> None:
    """Both agent-e2e and test matrix failure uploads set retention-days."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    _assert_failure_upload_has_retention(_job_block(text, "agent-e2e"), "agent-e2e")
    _assert_failure_upload_has_retention(_job_block(text, "test"), "test")
