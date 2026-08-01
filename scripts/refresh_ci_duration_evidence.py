#!/usr/bin/env python3
"""Refresh agent-e2e CI duration evidence from GitHub Actions (PYPOST-931)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTING_DOC = REPO_ROOT / "doc" / "dev" / "testing.md"

DEFAULT_OWNER = "koctep"
DEFAULT_REPO = "pypost"
DEFAULT_WORKFLOW = "test.yml"
DEFAULT_RUN_LIMIT = 15

MAIN_TEST_JOB = "pytest (Python 3.11)"
AGENT_E2E_JOB = "make test-agent-e2e (env pack)"
MAIN_TEST_STEP = "Run tests"
AGENT_E2E_STEP = "Run agent e2e env pack via make"

DOC_ANCHOR_931 = "PYPOST-931"
MAKE_TARGET = "refresh-ci-duration-evidence"


@dataclass(frozen=True)
class StepTiming:
    name: str
    seconds: int


@dataclass(frozen=True)
class JobTiming:
    name: str
    seconds: int
    steps: tuple[StepTiming, ...]


@dataclass(frozen=True)
class RunEvidence:
    run_number: int
    run_id: int
    main_test: JobTiming
    agent_e2e: JobTiming


def _parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _duration_seconds(start: str | None, end: str | None) -> int:
    started = _parse_iso8601(start)
    finished = _parse_iso8601(end)
    if started is None or finished is None:
        return 0
    return max(int((finished - started).total_seconds()), 0)


def format_duration_minutes(seconds: int) -> str:
    """Format job totals like existing evidence (~11.8m, ~3.6m)."""
    if seconds <= 0:
        return "n/a"
    return f"~{seconds / 60:.1f}m"


def format_duration_seconds(seconds: int) -> str:
    """Format step timings like existing evidence (~670s, ~172s)."""
    if seconds <= 0:
        return "n/a"
    return f"~{seconds}s"


def format_duration(seconds: int) -> str:
    """Backward-compatible alias — prefer minutes/seconds helpers."""
    if seconds >= 120:
        return format_duration_minutes(seconds)
    return format_duration_seconds(seconds)


def _github_request(url: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pypost-refresh-ci-duration-evidence",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API HTTP {exc.code} for {url}: {body}") from exc


def fetch_completed_runs(
    owner: str,
    repo: str,
    workflow: str,
    *,
    limit: int,
    token: str | None,
) -> list[dict[str, Any]]:
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/"
        f"{workflow}/runs?status=completed&per_page={limit}"
    )
    payload = _github_request(url, token)
    return list(payload.get("workflow_runs", []))


def fetch_run_jobs(
    owner: str,
    repo: str,
    run_id: int,
    *,
    token: str | None,
) -> list[dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
    payload = _github_request(url, token)
    return list(payload.get("jobs", []))


def _job_timing(job: dict[str, Any]) -> JobTiming:
    steps = tuple(
        StepTiming(
            name=str(step.get("name", "")),
            seconds=_duration_seconds(step.get("started_at"), step.get("completed_at")),
        )
        for step in job.get("steps", [])
    )
    return JobTiming(
        name=str(job.get("name", "")),
        seconds=_duration_seconds(job.get("started_at"), job.get("completed_at")),
        steps=steps,
    )


def _find_step(job: JobTiming, step_name: str) -> StepTiming | None:
    for step in job.steps:
        if step.name == step_name:
            return step
    return None


def extract_run_evidence(
    run_number: int,
    run_id: int,
    jobs: list[dict[str, Any]],
) -> RunEvidence | None:
    main_raw = next((job for job in jobs if job.get("name") == MAIN_TEST_JOB), None)
    agent_raw = next((job for job in jobs if job.get("name") == AGENT_E2E_JOB), None)
    if main_raw is None or agent_raw is None:
        return None
    return RunEvidence(
        run_number=run_number,
        run_id=run_id,
        main_test=_job_timing(main_raw),
        agent_e2e=_job_timing(agent_raw),
    )


def collect_evidence(
    owner: str,
    repo: str,
    workflow: str,
    *,
    limit: int,
    token: str | None,
) -> list[RunEvidence]:
    evidence: list[RunEvidence] = []
    for run in fetch_completed_runs(owner, repo, workflow, limit=limit, token=token):
        run_id = int(run["id"])
        run_number = int(run["run_number"])
        jobs = fetch_run_jobs(owner, repo, run_id, token=token)
        row = extract_run_evidence(run_number, run_id, jobs)
        if row is not None:
            evidence.append(row)
    return evidence


def format_main_test_cell(row: RunEvidence) -> str:
    total = format_duration_minutes(row.main_test.seconds)
    step = _find_step(row.main_test, MAIN_TEST_STEP)
    if step is None or step.seconds <= 0:
        return total
    return (
        f"{total} total; pytest step "
        f"{format_duration_seconds(step.seconds)}"
    )


def format_agent_e2e_cell(row: RunEvidence) -> str:
    total = format_duration_minutes(row.agent_e2e.seconds)
    step = _find_step(row.agent_e2e, AGENT_E2E_STEP)
    if step is None or step.seconds <= 0:
        return total
    return (
        f"{total} total; `make test-agent-e2e` "
        f"{format_duration_seconds(step.seconds)}"
    )


def render_markdown_table(rows: list[RunEvidence]) -> str:
    lines = [
        "| Run | Main `test` 3.11 | Job `agent-e2e` |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"#{row.run_number} (`{row.run_id}`) | "
            f"{format_main_test_cell(row)} | "
            f"{format_agent_e2e_cell(row)} |"
        )
    return "\n".join(lines)


def render_report(
    rows: list[RunEvidence],
    *,
    owner: str,
    repo: str,
    fetched_at: datetime,
) -> str:
    header = (
        f"<!-- Generated by scripts/refresh_ci_duration_evidence.py "
        f"({owner}/{repo}) on {fetched_at.date().isoformat()}. "
        f"Paste into doc/dev/testing.md § CI duration evidence; "
        f"review before commit. -->\n"
    )
    if not rows:
        return (
            f"{header}\n"
            f"No completed runs with job `{AGENT_E2E_JOB}` in the last fetch."
        )
    sample = len(rows)
    body = (
        f"From completed `Tests` workflow runs on `{owner}/{repo}` that include "
        f"job `agent-e2e` (n={sample} in fetch window):\n\n"
        f"{render_markdown_table(rows)}"
    )
    return header + body


def verify_doc_procedure(testing_doc: Path = TESTING_DOC) -> list[str]:
    """Return list of missing anchors for --check mode."""
    if not testing_doc.is_file():
        return [f"missing {testing_doc.relative_to(REPO_ROOT)}"]
    text = testing_doc.read_text(encoding="utf-8")
    issues: list[str] = []
    if DOC_ANCHOR_931 not in text:
        issues.append(f"missing {DOC_ANCHOR_931} in {testing_doc.name}")
    if MAKE_TARGET not in text:
        issues.append(
            f"missing make target {MAKE_TARGET!r} in {testing_doc.name}",
        )
    if "scripts/refresh_ci_duration_evidence.py" not in text:
        issues.append(
            "missing scripts/refresh_ci_duration_evidence.py reference in "
            f"{testing_doc.name}",
        )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch GitHub Actions timings for agent-e2e overlap evidence "
            "(PYPOST-931)."
        ),
    )
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RUN_LIMIT,
        help="Completed workflow runs to scan (default: 15)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify doc/dev/testing.md documents the refresh procedure",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of markdown (for tooling/tests)",
    )
    args = parser.parse_args(argv)

    if args.check:
        issues = verify_doc_procedure()
        if issues:
            for issue in issues:
                print(f"ERROR: {issue}", file=sys.stderr)
            return 1
        print("OK: CI duration evidence refresh procedure documented.")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    rows = collect_evidence(
        args.owner,
        args.repo,
        args.workflow,
        limit=args.limit,
        token=token,
    )
    if args.json:
        payload = [
            {
                "run_number": row.run_number,
                "run_id": row.run_id,
                "main_test_seconds": row.main_test.seconds,
                "agent_e2e_seconds": row.agent_e2e.seconds,
            }
            for row in rows
        ]
        print(json.dumps(payload, indent=2))
        return 0

    report = render_report(
        rows,
        owner=args.owner,
        repo=args.repo,
        fetched_at=datetime.now().astimezone(),
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
