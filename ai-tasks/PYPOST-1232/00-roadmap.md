# Roadmap: PYPOST-1232

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [ ] Red repro (pre-existing test, no new test file authored — per architecture plan):
    `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import`
    - Command: `make test PYTEST_ARGS="tests/test_environment_export.py -k test_write_encrypted_export_file_round_trips_through_import"`
    - Result: 1 failed, 11 deselected. Failure at `tests/test_environment_export.py:141`:
      `assert envelope.v == 1` → `AssertionError: assert 2 == 1` (envelope is
      `EncryptedValueEnvelopeV2(enc=True, v=2, alg='fernet', ...)`).
    - Confirmed intended-reason failure: stale `v == 1` assertion vs. current production
      default of v2 envelopes (`EnvironmentSecretsCodec` `VERSION = 2`). No fixture/import
      errors; all other assertions in the test pass up to that line.
- [x] **STEP 4: Development**
  - [x] One-line test fix in `tests/test_environment_export.py` (line 141):
    `assert envelope.v == 1` → `assert envelope.v == 2`, aligning the round-trip test with
    production's actual v2 envelope default (`EnvironmentSecretsCodec.VERSION = 2`). No
    production code touched.
    - Step 3 red test now green: `make test PYTEST_ARGS="tests/test_environment_export.py"`
      → `Total Files: 1 | Passed: 1 | Failed: 0 | Skipped: 0` (all 12 tests in the file pass,
      including the round-trip import assertions after line 141).
    - Full suite (`make test`): `Total Files: 311 | Passed: 304 | Failed: 6 | Skipped: 1`.
      All 6 failing files are pre-existing / already tracked in this sprint, none caused by
      this change:
      - `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir` —
        PYPOST-1233 (E402 lint)
      - `tests/test_main_window_alert_reload.py` (exit -11, segfault) — PYPOST-1251
      - `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
        (dialog LOC drift, mcp_servers_dialog.py 446 LOC) — PYPOST-1252
      - `tests/test_makefile.py` (worker timed out after 120s) — PYPOST-1234
      - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_audit_module_inventory_within_caps`
        and `::test_markdown_snapshot_matches_current_metrics` (template_service.py 241 LOC
        exceeds 225 cap) — confirmed covered by PYPOST-1111 (audit/baseline snapshot drift;
        both node ids already tracked there via its comment history)
      - `tests/test_pytest_exit_policy.py::test_make_test_fails_with_exit_code_5_when_no_tests_collected`
        (subprocess `make install` `TimeoutExpired` after 25s) — same root-cause cluster as
        PYPOST-1234 (Makefile subprocess calls timing out under full-suite parallel load, just
        a different mechanism/file); recorded as a comment on PYPOST-1234 rather than a new
        issue (dedup per failing-tests-triage.md)
    - Orchestrator triage (Phase C/D context): all 6 pre-existing failing files/clusters above
      are now linked to an existing sprint Jira issue — no new Jira issue was needed.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1232/40-code-cleanup.md` — flake8 clean, no further cleanup needed
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1232/50-observability.md` — N/A, test-only change, no runtime behavior
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1232/60-tech-debt.md` — 6 pre-existing failures, all linked to existing
    Jira issues (PYPOST-1233, 1234, 1111, 1251, 1252); no new issue filed
- [x] **STEP 8: Dev Docs**
  - `doc/dev/environment_encryption_at_rest.md` checked — already accurate (documents v2
    envelope on export), no edit needed; see `ai-tasks/PYPOST-1232/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1232/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1232/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1232/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1232/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1232/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
