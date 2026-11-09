# Roadmap: PYPOST-1530

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_hidden_fields_selector_only_repro.py`
- [x] **STEP 4: Development**
  - Iteration 1: remove dormant activation state and preserve selector roles and notifications.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1530/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1530/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_hidden_fields_selector_only_repro.py`: parameterized checks for both configured
  rows and the trailing blank row; unsupported writes preserve selectors and emit no signals.
- Command: `make test PYTEST_ARGS='tests/test_hidden_fields_selector_only_repro.py -q'`.
- Red result: 6 failed, 3 passed. Configured rows return `Checked` instead of `None` in
  `test_check_state_read_is_unsupported[0]` and `[1]`; both checked/unchecked writes return
  `True` instead of `False` in `test_check_state_write_is_ignored` for rows 0 and 1.
  The trailing-row cases already pass. No production changes were made.

### STEP 4: Development

- Iteration 1 removed `HiddenFieldRecord.enabled`, the factory's unused argument, and
  check-state read/write handling. Selector roles, cached syntax, flags, and notifications
  retain their existing behavior; unsupported check state now uses the standard fallbacks.
- Before the change, `make test
  PYTEST_ARGS='tests/test_hidden_fields_virtualization_repro.py
  tests/test_hidden_fields_syntax_validation_repro.py
  tests/test_request_hidden_fields_model_and_ui.py -q'` passed all 3 selected files.
- After the change, `make test
  PYTEST_ARGS='tests/test_hidden_fields_selector_only_repro.py
  tests/test_hidden_fields_virtualization_repro.py
  tests/test_hidden_fields_syntax_validation_repro.py
  tests/test_request_hidden_fields_model_and_ui.py -q'` passed all 4 selected files,
  including all 9 selector-only regression cases.
- `make lint` passed: test lint baseline, production flake8, Markdown lint, and relative links.
- No production callers depended on the removed state; no test or unrelated source edits
  were needed in this step.

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1530/40-code-cleanup.md`
- Full `make check`: lint passed; 454 passed, 19 failed, 7 skipped files.
- Six failed nodes reproduced at base `97e8dc5f`: PYPOST-1474, PYPOST-1475,
  PYPOST-1553, and PYPOST-1554 (NON-BLOCKER — pre-existing).
- Thirteen flaky files passed twice with targeted `make test WORKERS=1`:
  PYPOST-1555 and PYPOST-1556 (NON-BLOCKER — confirmed flaky).
- Root editable installation restored with `make install`; `make verify-ai-tasks` passed.

### STEP 6: Observability

- `ai-tasks/PYPOST-1530/50-observability.md`
- Existing count, length, and syntax DEBUG diagnostics remain sufficient; no new logging or
  metrics are needed for removing unsupported activation state.

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1530/60-tech-debt.md`
- No new task-specific debt; baseline failures and confirmed flakes are NON-BLOCKER follow-ups
  linked to PYPOST-1474, PYPOST-1475, and PYPOST-1553 through PYPOST-1556.

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md`: selector-only records, unchanged list configuration,
  unsupported check-state contract, troubleshooting, and regression command.
- `make lint-docs check-docs-links` passed (these targets cover user guides and README links;
  the developer-documentation change is verified by independent review).

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
