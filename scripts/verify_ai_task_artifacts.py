#!/usr/bin/env python3
"""Verify closed ai-tasks folders include required workflow artifacts (PYPOST-816)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AI_TASKS_DIR = REPO_ROOT / "ai-tasks"
BASELINE_PATH = REPO_ROOT / "ai-tasks-artifacts-baseline.json"
ROADMAP_NAME = "00-roadmap.md"

# PYPOST-1071: `70-dev-docs.md` was retired as a required artifact because Step 8's output is
# reviewed developer documentation under `doc/dev/` (see td-70-dev-docs), not a task-local
# summary file.
# PYPOST-1079: Automated verification of Step 8 is established via `is_roadmap_completed`, which
# requires all steps in range(1, 9) (steps 1 through 8) or collapsed STEP 1-8 to be marked complete.
STANDARD_FILES: tuple[str, ...] = (
    "00-roadmap.md",
    "10-requirements.md",
    "20-architecture.md",
    "40-code-cleanup.md",
    "50-observability.md",
    "60-tech-debt.md",
)

AUDIT_FILES: tuple[str, ...] = (
    "00-roadmap.md",
    "10-requirements.md",
    "20-architecture.md",
    "30-audit-report.md",
    "40-code-cleanup.md",
    "50-observability.md",
    "60-tech-debt.md",
)

CODE_AUDIT_TASKS = frozenset(f"PYPOST-{number}" for number in range(684, 690))

_COLLAPSED_STEP_RE = re.compile(
    r"^\s*-\s*\[(?P<mark>x| )\]\s+\*?\*?STEP\s+1[\-–]8",
    re.IGNORECASE | re.MULTILINE,
)
_STEP_LINE_RE = re.compile(
    r"^\s*-\s*\[(?P<mark>x| )\]\s+\*?\*?STEP\s+(?P<number>\d+)\s*:",
    re.IGNORECASE | re.MULTILINE,
)


def required_files_for_task(task_id: str) -> tuple[str, ...]:
    if task_id in CODE_AUDIT_TASKS:
        return AUDIT_FILES
    return STANDARD_FILES


def is_roadmap_completed(roadmap_text: str) -> bool:
    collapsed = _COLLAPSED_STEP_RE.search(roadmap_text)
    if collapsed is not None:
        return collapsed.group("mark").lower() == "x"

    step_status: dict[int, bool] = {}
    for match in _STEP_LINE_RE.finditer(roadmap_text):
        step_status[int(match.group("number"))] = match.group("mark").lower() == "x"

    if not step_status:
        return False
    return all(step_status.get(step, False) for step in range(1, 9))


def missing_required_files(task_dir: Path, task_id: str) -> list[str]:
    required = required_files_for_task(task_id)
    return sorted(
        filename
        for filename in required
        if not (task_dir / filename).is_file()
    )


def collect_violations(ai_tasks_dir: Path = AI_TASKS_DIR) -> dict[str, list[str]]:
    violations: dict[str, list[str]] = {}

    if not ai_tasks_dir.is_dir():
        return violations

    for task_dir in sorted(ai_tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        task_id = task_dir.name
        if not task_id.startswith("PYPOST-"):
            continue

        roadmap_path = task_dir / ROADMAP_NAME
        if not roadmap_path.is_file():
            continue

        roadmap_text = roadmap_path.read_text(encoding="utf-8")
        if not is_roadmap_completed(roadmap_text):
            continue

        missing = missing_required_files(task_dir, task_id)
        if missing:
            violations[task_id] = missing

    return violations


def _load_baseline(path: Path = BASELINE_PATH) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks", {})
    return {task_id: sorted(files) for task_id, files in sorted(tasks.items())}


def _write_baseline(violations: dict[str, list[str]], path: Path = BASELINE_PATH) -> None:
    payload = {
        "violation_count": len(violations),
        "tasks": {task_id: files for task_id, files in sorted(violations.items())},
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare_violations(
    current: dict[str, list[str]],
    baseline: dict[str, list[str]],
) -> tuple[list[str], list[str], list[tuple[str, list[str], list[str]]]]:
    current_ids = set(current)
    baseline_ids = set(baseline)

    new_tasks = sorted(current_ids - baseline_ids)
    resolved_tasks = sorted(baseline_ids - current_ids)

    changed: list[tuple[str, list[str], list[str]]] = []
    for task_id in sorted(current_ids & baseline_ids):
        if current[task_id] != baseline[task_id]:
            changed.append((task_id, baseline[task_id], current[task_id]))

    return new_tasks, resolved_tasks, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite ai-tasks-artifacts-baseline.json from the current scan",
    )
    parser.add_argument(
        "--ai-tasks-dir",
        type=Path,
        default=AI_TASKS_DIR,
        help="Path to ai-tasks directory (default: repo ai-tasks/)",
    )
    args = parser.parse_args()

    current = collect_violations(args.ai_tasks_dir)

    if args.update_baseline:
        _write_baseline(current)
        print(
            f"Updated {BASELINE_PATH.name}: "
            f"{len(current)} tasks with missing artifacts",
        )
        return 0

    if not BASELINE_PATH.is_file():
        print(
            f"Missing {BASELINE_PATH.name}; run with --update-baseline",
            file=sys.stderr,
        )
        return 1

    baseline = _load_baseline()
    new_tasks, resolved_tasks, changed = compare_violations(current, baseline)

    if new_tasks or resolved_tasks or changed:
        if new_tasks:
            print("New artifact violations (not in baseline):", file=sys.stderr)
            for task_id in new_tasks:
                missing = ", ".join(current[task_id])
                print(f"  + {task_id}: missing {missing}", file=sys.stderr)
        if resolved_tasks:
            print("Resolved baseline violations (update baseline):", file=sys.stderr)
            for task_id in resolved_tasks:
                print(f"  - {task_id}: now compliant", file=sys.stderr)
        if changed:
            print("Changed baseline violations (update baseline):", file=sys.stderr)
            for task_id, before, after in changed:
                print(
                    f"  ~ {task_id}: was {before}; now {after}",
                    file=sys.stderr,
                )
        print(
            f"Baseline: {len(baseline)} tasks; current: {len(current)} tasks",
            file=sys.stderr,
        )
        return 1

    compliant_count = 0
    for task_dir in args.ai_tasks_dir.iterdir():
        if not task_dir.is_dir() or not task_dir.name.startswith("PYPOST-"):
            continue
        roadmap = task_dir / ROADMAP_NAME
        if roadmap.is_file() and is_roadmap_completed(roadmap.read_text(encoding="utf-8")):
            compliant_count += 1
    print(
        f"ai-tasks artifacts baseline OK "
        f"({compliant_count} completed tasks; "
        f"{len(baseline)} grandfathered legacy gaps)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
