"""PYPOST-931: lock CI duration evidence refresh script + Makefile + docs."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "refresh_ci_duration_evidence.py"
_TESTING_DOC = _REPO_ROOT / "doc" / "dev" / "testing.md"
_MAKEFILE = _REPO_ROOT / "Makefile"

_DOC_ANCHOR_931 = "PYPOST-931"
_MAKE_TARGET = "refresh-ci-duration-evidence"
_CHECK_TARGET = "check-ci-duration-evidence"


def test_refresh_script_exists() -> None:
    assert _SCRIPT.is_file(), (
        f"Missing {_SCRIPT.relative_to(_REPO_ROOT)} — add Actions refresh script"
    )


def test_makefile_lists_refresh_targets() -> None:
    text = _MAKEFILE.read_text(encoding="utf-8")
    assert f"{_MAKE_TARGET}:" in text, (
        f"Makefile missing target {_MAKE_TARGET} — expose refresh via make help"
    )
    assert f"{_CHECK_TARGET}:" in text, (
        f"Makefile missing target {_CHECK_TARGET} — doc procedure check for CI"
    )
    help_result = subprocess.run(
        ["make", "help"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert _MAKE_TARGET in help_result.stdout, (
        f"make help must list {_MAKE_TARGET}"
    )


def test_testing_doc_documents_refresh_procedure() -> None:
    text = _TESTING_DOC.read_text(encoding="utf-8")
    if _DOC_ANCHOR_931 not in text:
        pytest.fail(
            f"Missing {_DOC_ANCHOR_931} in {_TESTING_DOC.name} — link refresh "
            "automation from the evidence section",
        )
    if _MAKE_TARGET not in text:
        pytest.fail(
            f"Missing make target {_MAKE_TARGET!r} in {_TESTING_DOC.name} — "
            "document maintainer refresh command",
        )
    if "scripts/refresh_ci_duration_evidence.py" not in text:
        pytest.fail(
            "Missing script path in testing.md — document "
            "scripts/refresh_ci_duration_evidence.py",
        )
    if "manual paste" not in text.lower() and "pastes into" not in text.lower():
        pytest.fail(
            "testing.md must state numbers are pasted manually after refresh "
            "(do not auto-commit scraped timings)",
        )


def test_check_cli_exits_zero_for_documented_procedure() -> None:
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--check"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_format_duration_matches_evidence_style() -> None:
    from scripts.refresh_ci_duration_evidence import (
        format_duration_minutes,
        format_duration_seconds,
    )

    assert format_duration_seconds(172) == "~172s"
    assert format_duration_minutes(708) == "~11.8m"
    assert format_duration_seconds(0) == "n/a"


def test_extract_run_evidence_from_fixture_jobs() -> None:
    from scripts.refresh_ci_duration_evidence import (
        AGENT_E2E_JOB,
        AGENT_E2E_STEP,
        MAIN_TEST_JOB,
        MAIN_TEST_STEP,
        extract_run_evidence,
        format_agent_e2e_cell,
        format_main_test_cell,
    )

    jobs = [
        {
            "name": MAIN_TEST_JOB,
            "started_at": "2026-08-01T10:00:00Z",
            "completed_at": "2026-08-01T10:11:48Z",
            "steps": [
                {
                    "name": MAIN_TEST_STEP,
                    "started_at": "2026-08-01T10:00:30Z",
                    "completed_at": "2026-08-01T10:11:40Z",
                },
            ],
        },
        {
            "name": AGENT_E2E_JOB,
            "started_at": "2026-08-01T10:00:00Z",
            "completed_at": "2026-08-01T10:03:36Z",
            "steps": [
                {
                    "name": AGENT_E2E_STEP,
                    "started_at": "2026-08-01T10:02:44Z",
                    "completed_at": "2026-08-01T10:05:36Z",
                },
            ],
        },
    ]
    row = extract_run_evidence(21, 29912105656, jobs)
    assert row is not None
    assert format_main_test_cell(row).startswith("~11.8m")
    assert "`make test-agent-e2e`" in format_agent_e2e_cell(row)
    assert re.search(r"~172s", format_agent_e2e_cell(row))


def test_render_markdown_table_includes_run_ids() -> None:
    from scripts.refresh_ci_duration_evidence import (
        JobTiming,
        RunEvidence,
        StepTiming,
        render_markdown_table,
    )

    row = RunEvidence(
        run_number=21,
        run_id=29912105656,
        main_test=JobTiming(
            name="pytest (Python 3.11)",
            seconds=708,
            steps=(StepTiming(name="Run tests", seconds=670),),
        ),
        agent_e2e=JobTiming(
            name="make test-agent-e2e (env pack)",
            seconds=216,
            steps=(StepTiming(name="Run agent e2e env pack via make", seconds=172),),
        ),
    )
    table = render_markdown_table([row])
    assert "#21 (`29912105656`)" in table
    assert "make test-agent-e2e" in table
