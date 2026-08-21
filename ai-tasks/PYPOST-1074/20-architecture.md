# PYPOST-1074: Extend 3+-Conflict Apply-to-All Test Matrix to OVERWRITE/KEEP_BOTH Decisions

## Research

### Existing Test Suite Analysis
In `tests/test_environment_list_widget.py`, the `TestImportEnvironments` class covers:
- `test_overwrite_conflict_keeps_existing_id` (single conflict OVERWRITE)
- `test_keep_both_adds_renamed_copy` (single conflict KEEP_BOTH)
- `test_apply_to_all_conflicts_prompts_only_once` (2-conflict SKIP)
- `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts` (3-conflict SKIP)

The loop in `EnvironmentListWidget._resolve_import_conflicts` sets `apply_to_all = decision` when `use_for_all` is True, propagating whatever decision was made to all subsequent items in the conflict list. However, tests for 3+ conflicts only validated the SKIP decision.

### Architectural Plan
Extend `TestImportEnvironments` in `tests/test_environment_list_widget.py` with two new test methods:
1. `test_apply_to_all_conflicts_applies_overwrite_to_third_and_later_conflicts`:
   - 3 existing environments: `Dev` (id `dev-id`), `Prod` (id `prod-id`), `Staging` (id `staging-id`).
   - 3 incoming environments with the same names but updated variables.
   - `prompt_import_conflict` returns `(ImportConflictDecision.OVERWRITE, True)`.
   - Asserts that only 1 prompt occurs, all 3 existing IDs are preserved, and all 3 variable payloads are updated.
2. `test_apply_to_all_conflicts_applies_keep_both_to_third_and_later_conflicts`:
   - 3 existing environments: `Dev`, `Prod`, `Staging`.
   - 3 incoming environments with the same names.
   - `prompt_import_conflict` returns `(ImportConflictDecision.KEEP_BOTH, True)`.
   - Asserts that only 1 prompt occurs, all 3 original environments remain untouched, and 3 numbered copies ("Dev (1)", "Prod (1)", "Staging (1)") are created and appended.

## Implementation Plan

1. **Step 3 (Failing Repro)**:
   - Add the two test methods to `TestImportEnvironments` in `tests/test_environment_list_widget.py`.
   - Run pytest and confirm test correctness.
2. **Step 4 (Development)**:
   - Verify green test suite execution.
3. **Step 5-8**:
   - Code cleanup, observability review, tech-debt recording, and developer documentation updates.

## Architecture

```text
EnvironmentListWidget.import_environments()
  ├── find_conflicts(existing, incoming) ──> ['Dev', 'Prod', 'Staging']
  ├── _resolve_import_conflicts()
  │     ├── Conflict 1 ('Dev'): prompt_import_conflict() ──> (OVERWRITE/KEEP_BOTH, use_for_all=True)
  │     ├── Conflict 2 ('Prod'): apply_to_all propagated
  │     └── Conflict 3 ('Staging'): apply_to_all propagated
  └── plan_import(existing, incoming, decisions)
```

### Components
- `pypost.ui.widgets.environments.environment_list_widget.EnvironmentListWidget`
- `pypost.core.environment_import.plan_import`
- `tests.test_environment_list_widget.TestImportEnvironments`

## Q&A

### Q1: Does this task introduce changes to production code?
**A:** No, the loop in `EnvironmentListWidget._resolve_import_conflicts` already handles arbitrary `ImportConflictDecision` values. This task completes the test matrix coverage for `OVERWRITE` and `KEEP_BOTH` decisions across 3+ conflicts.

### Q2: Why are two separate test methods added?
**A:** Testing `OVERWRITE` and `KEEP_BOTH` in distinct tests ensures isolation and verifies the specific side effects (in-place ID preservation vs numbered copy creation) across multiple colliding entries independently.
