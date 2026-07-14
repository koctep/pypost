"""Unit tests for scripts/verify_ai_task_artifacts.py (PYPOST-816)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_ai_task_artifacts import (
    BASELINE_PATH,
    AUDIT_FILES,
    STANDARD_FILES,
    collect_violations,
    compare_violations,
    is_roadmap_completed,
    missing_required_files,
    required_files_for_task,
)

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_roadmap(task_dir: Path, body: str) -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "00-roadmap.md").write_text(body, encoding="utf-8")


def _write_completed_standard(task_dir: Path) -> None:
    _write_roadmap(
        task_dir,
        "\n".join(
            f"- [x] **STEP {step}: Step {step}**"
            for step in range(1, 8)
        )
        + "\n",
    )
    for filename in STANDARD_FILES:
        (task_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")


class TestRoadmapParsing:
    def test_individual_steps_all_complete(self) -> None:
        text = "\n".join(
            f"- [x] **STEP {step}: Step {step}**" for step in range(1, 8)
        )
        assert is_roadmap_completed(text) is True

    def test_individual_steps_incomplete(self) -> None:
        text = "\n".join(
            f"- [{'x' if step < 7 else ' '}] **STEP {step}: Step {step}**"
            for step in range(1, 8)
        )
        assert is_roadmap_completed(text) is False

    def test_collapsed_step_range_complete(self) -> None:
        text = "- [x] **STEP 1–7** — legacy closure\n"
        assert is_roadmap_completed(text) is True

    def test_collapsed_step_range_incomplete(self) -> None:
        text = "- [ ] STEP 1–7 complete\n"
        assert is_roadmap_completed(text) is False

    def test_substeps_do_not_count_as_main_steps(self) -> None:
        text = "\n".join(
            [
                "- [x] **STEP 1: Requirements**",
                "- [x] **STEP 2: Architecture**",
                "- [x] **STEP 3: Development**",
                "  - [x] nested sub-item only",
                "- [ ] **STEP 4: Cleanup**",
                "- [x] **STEP 5: Observability**",
                "- [x] **STEP 6: Debt**",
                "- [x] **STEP 7: Dev Docs**",
            ]
        )
        assert is_roadmap_completed(text) is False


class TestRequiredFiles:
    def test_standard_task_requires_seven_files(self) -> None:
        assert required_files_for_task("PYPOST-816") == STANDARD_FILES

    def test_code_audit_task_requires_eight_files(self) -> None:
        assert required_files_for_task("PYPOST-684") == AUDIT_FILES
        assert "30-audit-report.md" in AUDIT_FILES

    def test_missing_required_files_reports_sorted_gaps(self, tmp_path: Path) -> None:
        task_dir = tmp_path / "PYPOST-TEST"
        _write_completed_standard(task_dir)
        (task_dir / "70-dev-docs.md").unlink()

        assert missing_required_files(task_dir, "PYPOST-TEST") == ["70-dev-docs.md"]


class TestCollectViolations:
    def test_completed_compliant_task_has_no_violation(self, tmp_path: Path) -> None:
        task_dir = tmp_path / "PYPOST-900"
        _write_completed_standard(task_dir)

        assert collect_violations(tmp_path) == {}

    def test_completed_incomplete_task_is_reported(self, tmp_path: Path) -> None:
        task_dir = tmp_path / "PYPOST-901"
        _write_roadmap(
            task_dir,
            "\n".join(
                f"- [x] **STEP {step}: Step {step}**" for step in range(1, 8)
            )
            + "\n",
        )
        (task_dir / "10-requirements.md").write_text("# ok\n", encoding="utf-8")

        violations = collect_violations(tmp_path)
        assert "PYPOST-901" in violations
        assert "20-architecture.md" in violations["PYPOST-901"]

    def test_incomplete_roadmap_is_ignored(self, tmp_path: Path) -> None:
        task_dir = tmp_path / "PYPOST-902"
        _write_roadmap(task_dir, "- [ ] **STEP 1: Requirements**\n")

        assert collect_violations(tmp_path) == {}


class TestBaselineComparison:
    def test_new_violation_detected(self) -> None:
        current = {"PYPOST-999": ["70-dev-docs.md"]}
        baseline: dict[str, list[str]] = {}
        new_tasks, resolved, changed = compare_violations(current, baseline)
        assert new_tasks == ["PYPOST-999"]
        assert resolved == []
        assert changed == []

    def test_exact_match_passes(self) -> None:
        baseline = {"PYPOST-328": ["10-requirements.md"]}
        current = {"PYPOST-328": ["10-requirements.md"]}
        new_tasks, resolved, changed = compare_violations(current, baseline)
        assert new_tasks == []
        assert resolved == []
        assert changed == []


class TestCommittedBaseline:
    def test_baseline_file_exists(self) -> None:
        assert BASELINE_PATH.is_file()

    def test_baseline_matches_current_scan(self) -> None:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        current = collect_violations()
        assert data["violation_count"] == len(current)
        assert data["tasks"] == current
