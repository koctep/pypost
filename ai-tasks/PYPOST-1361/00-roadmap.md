# Roadmap: PYPOST-1361

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_solid_audit_baseline.py`:
        `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  - [x] `tests/test_pypost_1077_verification_artifacts.py`:
        `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  - [x] `tests/test_pypost_1287_failing_repro.py`:
        `test_live_report_inventory_loc_matches_discovery`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Regenerate SOLID baseline metrics snapshot via `make baseline-metrics`
    and synchronize `30-dialogs-audit-report.md` inventory table and totals to 2,693 LOC.
    All 3 regression tests green.
- [x] **STEP 5: Code Cleanup**
  - [x] Line length <= 100 chars and table formatting verified in `baseline-metrics.md`
    and `30-dialogs-audit-report.md`. `make lint`, `make check-baseline-metrics`,
    and targeted tests green. Created `ai-tasks/PYPOST-1361/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Assessed technical debt for refreshed snapshots and audit reports.
    Recorded zero introduced debt; documented pre-existing Sprint 2026 backlog
    failures (PYPOST-1363 and PYPOST-1306). Created 60-tech-debt.md.
- [x] **STEP 8: Dev Docs**
  - [x] Documented snapshot refresh procedures
    (`make baseline-metrics`, `make check-baseline-metrics`)
    and dialog LOC synchronization in `doc/dev/testing.md` and `doc/dev/solid_audit.md`.
    Verified `make lint` passes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1361/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1361/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1361/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1361/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1361/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
