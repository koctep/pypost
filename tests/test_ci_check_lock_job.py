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
_SETUP_UV_STEP = re.compile(
    r"uses:\s*astral-sh/setup-uv@[^\n]*\n(?P<rest>(?:(?!\n\s*- ).)*)",
    re.DOTALL,
)


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


def test_workflow_check_lock_setup_uv_step_pins_version() -> None:
    """check-lock job's setup-uv step must pin a non-empty version: input (PYPOST-984).

    An unpinned `uv` install lets CI resolve `requirements.in` against whatever
    resolver version is "latest" at run time, which can drift from the
    committed `requirements.txt` independent of any repo change.
    """
    workflow_text = _WORKFLOW.read_text(encoding="utf-8")
    job = workflow_job_block(workflow_text, "check-lock", workflow_path=_WORKFLOW)

    step_match = _SETUP_UV_STEP.search(job)
    assert step_match is not None, (
        "check-lock job must contain an astral-sh/setup-uv step"
    )
    step_tail = step_match.group("rest")
    version_match = re.search(r"version:\s*(\S+)", step_tail)
    assert version_match is not None and version_match.group(1).strip("\"'"), (
        "check-lock job's setup-uv step must pin a non-empty `version:` input "
        f"to avoid resolver-version drift; got step body:\n{step_tail!r}"
    )


def test_workflow_check_lock_dev_setup_uv_step_pins_version() -> None:
    """check-lock-dev job's setup-uv step must pin a non-empty version: input (PYPOST-995)."""
    workflow_text = _WORKFLOW.read_text(encoding="utf-8")
    job = workflow_job_block(workflow_text, "check-lock-dev", workflow_path=_WORKFLOW)

    step_match = _SETUP_UV_STEP.search(job)
    assert step_match is not None, (
        "check-lock-dev job must contain an astral-sh/setup-uv step"
    )
    step_tail = step_match.group("rest")
    version_match = re.search(r"version:\s*(\S+)", step_tail)
    assert version_match is not None and version_match.group(1).strip("\"'"), (
        "check-lock-dev job's setup-uv step must pin a non-empty `version:` input "
        f"to avoid resolver-version drift; got step body:\n{step_tail!r}"
    )

