"""Shared GitHub Actions workflow YAML helpers for CI contract tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_JOBS_KEY = "jobs"
_JOB_SIBLING_INDENT = "  "


def _workflow_label(workflow_path: Path | str | None) -> str:
    if workflow_path is None:
        return "workflow"
    return str(workflow_path)


def _parse_jobs_mapping(workflow_text: str, *, workflow_path: Path | str | None) -> dict[str, Any]:
    """Parse workflow YAML and return the top-level ``jobs`` mapping."""
    label = _workflow_label(workflow_path)
    try:
        data = yaml.safe_load(workflow_text)
    except yaml.YAMLError as exc:
        pytest.fail(f"{label}: invalid workflow YAML: {exc}")

    if not isinstance(data, dict):
        pytest.fail(f"{label}: workflow root must be a mapping")

    jobs = data.get(_JOBS_KEY)
    if not isinstance(jobs, dict):
        pytest.fail(f"{label}: workflow must define top-level {_JOBS_KEY!r} mapping")

    return jobs


def _jobs_section_text(workflow_text: str, *, workflow_path: Path | str | None) -> str:
    """Return workflow text from the ``jobs:`` line through EOF."""
    label = _workflow_label(workflow_path)
    lines = workflow_text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.strip() == f"{_JOBS_KEY}:" and not line.startswith(" "):
            return "".join(lines[index:])

    pytest.fail(f"{label}: missing top-level {_JOBS_KEY!r} section")


def _collect_job_block_from_jobs_section(jobs_text: str, job_id: str) -> str:
    """Slice a sibling job block from text that starts at ``jobs:``."""
    marker = f"\n{_JOB_SIBLING_INDENT}{job_id}:"
    start = jobs_text.find(marker)
    if start < 0:
        alt = f"{_JOB_SIBLING_INDENT}{job_id}:"
        start = jobs_text.find(alt)
        if start < 0:
            return ""
        start = jobs_text.rfind("\n", 0, start) + 1
    else:
        start += 1

    rest = jobs_text[start:]
    block_lines = rest.splitlines(keepends=True)
    if not block_lines:
        return ""

    collected: list[str] = [block_lines[0]]
    for line in block_lines[1:]:
        if line.startswith(_JOB_SIBLING_INDENT) and not line.startswith("   "):
            stripped = line.strip()
            if (
                stripped.endswith(":")
                and not stripped.startswith("#")
                and " " not in stripped[:-1]
            ):
                sibling_key = stripped[:-1]
                if sibling_key and sibling_key != job_id:
                    break
        collected.append(line)
    return "".join(collected)


def workflow_job_block(
    workflow_text: str,
    job_id: str,
    *,
    workflow_path: Path | str | None = None,
) -> str:
    """Return the named job YAML block as text (until the next sibling job).

    Validates structure with ``yaml.safe_load`` (job must exist under ``jobs``),
    then extracts the raw block from the ``jobs`` section for substring contract
    assertions used by CI lock tests.
    """
    label = _workflow_label(workflow_path)
    jobs = _parse_jobs_mapping(workflow_text, workflow_path=workflow_path)
    if job_id not in jobs:
        pytest.fail(f"{label}: missing job {job_id!r}")

    jobs_text = _jobs_section_text(workflow_text, workflow_path=workflow_path)
    block = _collect_job_block_from_jobs_section(jobs_text, job_id)
    if not block:
        pytest.fail(f"{label}: could not extract job block for {job_id!r}")
    return block
