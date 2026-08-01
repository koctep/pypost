"""PYPOST-927: CI production lock verification contract."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"
_SETUP_UV_ACTION = "astral-sh/setup-uv@"


def _job_block(workflow_text: str, job_id: str) -> str:
    """Return the named job YAML block (until next top-level job)."""
    marker = f"\n  {job_id}:"
    start = workflow_text.find(marker)
    if start < 0:
        alt = f"  {job_id}:"
        start = workflow_text.find(alt)
        if start < 0:
            pytest.fail(
                f"{_WORKFLOW.relative_to(_REPO_ROOT)}: missing job {job_id}"
            )
        start = workflow_text.rfind("\n", 0, start) + 1
    else:
        start += 1
    rest = workflow_text[start:]
    lines = rest.splitlines(keepends=True)
    collected: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("  ") and not line.startswith("   "):
            if line.strip().endswith(":") and not line.strip().startswith("#"):
                key = line.strip()[:-1]
                if key and " " not in key and key != job_id:
                    break
        collected.append(line)
    return "".join(collected)


def test_workflow_has_production_check_lock_job() -> None:
    """test.yml must gate production lock drift via make check-lock (PYPOST-927)."""
    workflow_text = _WORKFLOW.read_text(encoding="utf-8")
    job = _job_block(workflow_text, "check-lock")

    assert _SETUP_UV_ACTION in job, (
        "check-lock job must install uv via pinned astral-sh/setup-uv action"
    )
    assert re.search(r"run:\s*make check-lock\b", job), (
        "check-lock job must run `make check-lock`"
    )
