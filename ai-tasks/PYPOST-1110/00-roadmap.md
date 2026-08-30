# Roadmap: PYPOST-1110

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1110/20-architecture.md`
  - Verification architecture: confirm current file state, run guard test node id
    plus related files, document already-fixed-by-494eb857 finding. No code
    change required. Failing-Repro (Step 3): N/A — no behavioral change (defect
    already fixed on dev HEAD by unrelated commit 494eb857 / PYPOST-1176).
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (defect already fixed by commit 494eb857 / PYPOST-1176; see 20-architecture.md)
- [x] **STEP 4: Development**
  - [x] No code change required — verified target defect already resolved by commit
    494eb857 (PYPOST-1176); guard test (`tests/test_suite_qapp_alignment.py`) and related
    files (`tests/test_mcp_controls_presenter.py`, `tests/test_presenter_font_inheritance.py`)
    pass (3/3 files, 0 failed). Full suite run for regression check: 311 files, 303 passed,
    7 failed, 1 skipped. Failures observed are unrelated to this task's scope (not touched by
    this task; no code was changed) and are treated as pre-existing per
    `_shared/failing-tests-triage.md`, to be triaged/filed by the orchestrator (Phase C/D),
    not fixed here:
    - `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`
    - `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
    - `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
    - `tests/test_main_window_alert_reload.py` (file-level crash, exit_code=-11 / SIGSEGV)
    - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
    - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
    - `tests/test_makefile.py::TestTargetExecution::test_make_test_agent_e2e_selects_agent_e2e_marker` (file-level timeout, exit_code=-9 after 120s)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1110/40-code-cleanup.md`
  - No code changed by this task (target defect already fixed by unrelated commit
    494eb857 / PYPOST-1176; Steps 1-4 confirmed no unused imports/dead code in
    `tests/test_mcp_controls_presenter.py`). Sanity checks re-run: `py_compile`
    OK, `flake8` on the target file reports zero findings.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1110/50-observability.md`
  - N/A — no production code changed by this task (target defect already fixed
    by unrelated commit 494eb857 / PYPOST-1176); this is test-suite hygiene
    with no runtime component, so no logging/metrics are needed.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1110/60-tech-debt.md`
  - No shortcuts/code-quality/missing-test/performance debt from this task (no code changed;
    target defect already fixed by commit 494eb857 / PYPOST-1176). Follow-up Tasks lists the 7
    pre-existing failing test files/clusters found during Step 4's full-suite run, each
    NON-BLOCKER — pre-existing, for the orchestrator to file via jira-create-issue in Phase D.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/gui_testing.md` (§ Shared `qapp`) to note PYPOST-1110's
    verification of `tests/test_mcp_controls_presenter.py` as a confirmed
    conftest-`qapp` consumer, and the already-landed fix reference
    (494eb857 / PYPOST-1176).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1110/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1110/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1110/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1110/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1110/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
