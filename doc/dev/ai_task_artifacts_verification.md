# AI Task Artifacts Verification (PYPOST-816, PYPOST-1071, PYPOST-1079)

## Overview

The AI task artifacts verification subsystem (`scripts/verify_ai_task_artifacts.py`) enforces that completed task folders under `ai-tasks/` contain all mandatory workflow artifacts prescribed by the Top-Down development process. It acts as an automated quality gate in the CI and local verification pipeline (`make verify-ai-tasks` and `make check`), preventing tasks from being marked completed without producing the required documentation and audit trails.

Under the current 8-step Top-Down workflow:
- A task is considered **completed** when all steps (Step 1 through Step 8) are marked `[x]` in its roadmap (`00-roadmap.md`), or when a collapsed `STEP 1–8` completion mark is present.
- Every completed standard task must contain 6 required task-local artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`, and `60-tech-debt.md`).
- Step 8 outputs reviewed developer documentation under `doc/dev/` rather than a task-local summary file (PYPOST-1071). Automated verification of Step 8 completion is enforced through the 8-step roadmap completion gate (PYPOST-1079).
- Historical completed tasks with grandfathered missing artifacts are tracked in `ai-tasks-artifacts-baseline.json` to prevent baseline drift while allowing older tasks to remain as historical records.

## Architecture

The verification pipeline operates entirely offline without external dependencies or network access.

```
┌────────────────────────────────────────────────────────┐
│             ai-tasks/<TASK_ID>/00-roadmap.md           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │   is_roadmap_completed    │ (Steps 1..8 == [x])
              └─────────────┬─────────────┘
                            │ (Yes)
                            ▼
              ┌───────────────────────────┐
              │  missing_required_files   │ (STANDARD_FILES / AUDIT_FILES)
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │    compare_violations     │ ◄─── ai-tasks-artifacts-baseline.json
              └─────────────┬─────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
         [Match Baseline]       [Drift / New Violation]
             (Exit 0)                   (Exit 1)
```

### 1. Roadmap Completion Detection (`is_roadmap_completed`)

A task is evaluated for artifact compliance only after it has reached full workflow completion. The function `is_roadmap_completed` inspects the task's `00-roadmap.md`:
- **Individual step lines**: Matches lines conforming to `^\s*-\s*\[(?P<mark>x| )\]\s+\*?\*?STEP\s+(?P<number>\d+)\s*:`. It requires every step in `range(1, 9)` (Step 1 through Step 8) to have `[x]`. Tasks with missing steps, in-progress steps (`[/]`), or unstarted steps (`[ ]`) return `False` and are skipped during the verification scan.
- **Collapsed step notation**: Matches `^\s*-\s*\[(?P<mark>x| )\]\s+\*?\*?STEP\s+1[\-–]8`. Returns `True` if marked `[x]`. Legacy collapsed ranges like `STEP 1–7` are not accepted.
- **Sub-items**: Nested bullet points or sub-item checkboxes do not override main step lines.

### 2. Required Artifact Contracts (`required_files_for_task`)

Each completed task directory must contain its designated set of markdown artifacts:

| Task Category | Task ID Pattern | Required Artifacts |
| ------------- | --------------- | ------------------ |
| **Standard Task** | `PYPOST-*` | `00-roadmap.md`<br>`10-requirements.md`<br>`20-architecture.md`<br>`40-code-cleanup.md`<br>`50-observability.md`<br>`60-tech-debt.md` (6 files) |
| **Code Audit Task** | `PYPOST-684` .. `PYPOST-689` | Standard files + `30-audit-report.md` (7 files) |

*Note on Step 3 and Step 8:*
- Step 3 produces red repro tests under `tests/` or records an `N/A` justification in `00-roadmap.md` (no task-local markdown file is generated).
- Step 8 produces developer documentation in `doc/dev/` (such as this document). The obsolete `70-dev-docs.md` task-local file is retired and forbidden from being required (PYPOST-1071).

### 3. Violation Collection & Baseline Comparison

- `collect_violations(ai_tasks_dir)`: Iterates over all `ai-tasks/PYPOST-*` directories, filters for completed tasks via `is_roadmap_completed`, and checks for missing files. Returns a dictionary mapping `task_id -> list_of_missing_files`.
- `compare_violations(current, baseline)`: Compares the current scan against `ai-tasks-artifacts-baseline.json` and classifies discrepancies into:
  - `new_tasks`: Completed tasks not present in baseline with missing artifacts.
  - `resolved_tasks`: Grandfathered baseline tasks that now have all required files.
  - `changed`: Grandfathered tasks whose set of missing files has changed.

## Usage

### Running the Verifier

Run the verifier through the Makefile target:

```bash
make verify-ai-tasks
```

Or execute the Python script directly within the virtual environment:

```bash
.venv/bin/python scripts/verify_ai_task_artifacts.py
```

### Full Quality Gate

The verifier is included as part of `make check`:

```bash
make check
```

### Updating the Baseline

When historical tasks are intentionally updated or grandfathered gaps are resolved, regenerate `ai-tasks-artifacts-baseline.json` using the `--update-baseline` flag:

```bash
.venv/bin/python scripts/verify_ai_task_artifacts.py --update-baseline
```

### Custom AI Tasks Directory

To scan a custom directory (e.g. during integration testing or staging):

```bash
.venv/bin/python scripts/verify_ai_task_artifacts.py --ai-tasks-dir /path/to/custom_ai_tasks/
```

### Automated Testing

Run the unit tests covering roadmap parsing, file requirements, violation collection, baseline comparison, and committed baseline integrity:

```bash
make test PYTEST_ARGS="tests/test_verify_ai_task_artifacts.py -v"
```

## Configuration

### Baseline File (`ai-tasks-artifacts-baseline.json`)

The baseline file stores grandfathered legacy gaps in JSON format:

```json
{
  "tasks": {
    "PYPOST-88": [
      "60-tech-debt.md"
    ],
    "PYPOST-89": [
      "60-tech-debt.md"
    ]
  },
  "violation_count": 2
}
```

- Keys under `tasks` are sorted task identifiers.
- Values are sorted lists of missing file names.
- `violation_count` matches the total number of tasks with grandfathered violations.

## Troubleshooting

### 1. New Artifact Violations (Not in Baseline)

**Symptom:**
```
New artifact violations (not in baseline):
  + PYPOST-1234: missing 40-code-cleanup.md, 60-tech-debt.md
```

**Cause:** Task `PYPOST-1234` has all 8 steps marked complete (`[x]`) in `00-roadmap.md`, but one or more mandatory artifact files are missing from `ai-tasks/PYPOST-1234/`.

**Resolution:** Create the missing artifact files in `ai-tasks/PYPOST-1234/` following their respective workflow step templates (e.g., `40-code-cleanup.md`, `50-observability.md`, `60-tech-debt.md`).

---

### 2. Resolved Baseline Violations (Update Baseline)

**Symptom:**
```
Resolved baseline violations (update baseline):
  - PYPOST-88: now compliant
Baseline: 2 tasks; current: 1 tasks
```

**Cause:** A grandfathered legacy task previously recorded in `ai-tasks-artifacts-baseline.json` has had its missing artifacts populated or its roadmap modified.

**Resolution:** Run `.venv/bin/python scripts/verify_ai_task_artifacts.py --update-baseline` to synchronize `ai-tasks-artifacts-baseline.json` and commit the updated baseline.

---

### 3. Changed Baseline Violations

**Symptom:**
```
Changed baseline violations (update baseline):
  ~ PYPOST-88: was ['60-tech-debt.md']; now ['40-code-cleanup.md']
```

**Cause:** The set of missing files for a grandfathered task changed.

**Resolution:** Inspect `ai-tasks/PYPOST-88/` to verify why the artifact set changed, fix any inadvertent file deletions, and run `--update-baseline` if the change was deliberate.

---

### 4. Task Not Evaluated by Verifier

**Symptom:** The task directory has missing files, but `scripts/verify_ai_task_artifacts.py` does not report any violation.

**Cause:** The task's `00-roadmap.md` is not yet marked fully completed. If any step from Step 1 to Step 8 is unmarked (`[ ]`), in-progress (`[/]`), or omitted, `is_roadmap_completed` returns `False`, and the verifier intentionally skips incomplete tasks during development.

**Resolution:** This is expected behavior during active development. Once Step 8 passes review and the orchestrator marks all steps `[x]`, the task will be verified upon closure.
