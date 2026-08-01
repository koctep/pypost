"""PYPOST-927: CI production lock verification contract."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.helpers.ci_workflow_yaml import workflow_job_block

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"
_SETUP_UV_ACTION = "astral-sh/setup-uv@"


def test_workflow_has_production_check_lock_job() -> None:
    """test.yml must gate production lock drift via make check-lock (PYPOST-927)."""
    workflow_text = _WORKFLOW.read_text(encoding="utf-8")
    job = workflow_job_block(workflow_text, "check-lock", workflow_path=_WORKFLOW)

    assert _SETUP_UV_ACTION in job, (
        "check-lock job must install uv via pinned astral-sh/setup-uv action"
    )
    assert re.search(r"run:\s*make check-lock\b", job), (
        "check-lock job must run `make check-lock`"
    )
