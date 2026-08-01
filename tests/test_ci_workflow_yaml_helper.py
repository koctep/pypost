"""PYPOST-928: shared workflow job-block helper for CI contract tests."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest
from _pytest.outcomes import Failed

from tests.helpers.ci_workflow_yaml import workflow_job_block

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "test.yml"

_CONTRACT_MODULES = (
    "tests.test_ci_make_install_smoke_qt_runtime",
    "tests.test_ci_check_lock_job",
    "tests.test_agent_e2e_ci_failure_upload_doc",
    "tests.test_agent_e2e_ci_matrix_failure_upload_doc",
    "tests.test_agent_e2e_ci_failure_retention_doc",
)


def test_workflow_job_block_extracts_known_jobs() -> None:
    """Helper must slice sibling jobs from committed test.yml."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    for job_id in ("test", "agent-e2e", "make-install-smoke", "check-lock"):
        block = workflow_job_block(text, job_id, workflow_path=_WORKFLOW)
        assert block.startswith(f"  {job_id}:"), (
            f"expected block to start with job key line for {job_id!r}"
        )
        assert len(block) > len(job_id) + 4


def test_workflow_job_block_fails_for_missing_job() -> None:
    """Missing jobs must fail with pytest.fail (contract tests rely on this)."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    with pytest.raises(Failed, match="missing job 'no-such-job'"):
        workflow_job_block(text, "no-such-job", workflow_path=_WORKFLOW)


def test_ci_contract_modules_use_shared_workflow_job_block() -> None:
    """CI workflow lock modules must import workflow_job_block from shared helper."""
    missing: list[str] = []
    for mod_name in _CONTRACT_MODULES:
        mod = importlib.import_module(mod_name)
        source = inspect.getsource(mod)
        if "from tests.helpers.ci_workflow_yaml import workflow_job_block" not in source:
            missing.append(mod_name)
        if hasattr(mod, "_job_block"):
            missing.append(f"{mod_name} (local _job_block)")
        for legacy in ("_agent_e2e_job_block", "_test_job_block"):
            if hasattr(mod, legacy):
                missing.append(f"{mod_name} ({legacy})")
    if missing:
        pytest.fail(
            "CI contract modules must use tests.helpers.ci_workflow_yaml: "
            + ", ".join(missing)
        )
