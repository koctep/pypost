# Roadmap: PYPOST-1255

## Task Metadata

- **Implementation language**: Python 3.11+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1255/10-requirements.md` — business requirements for reducing the
    remaining tracked typing debt across the defined PyPost areas.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1255/20-architecture.md` — high-level design, ratchet
    interfaces, risk controls, validation strategy, and Step 3 repro plan.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1255_mypy_baseline_repro.py` — focused red repro for the selected
    `pypost/core/alert_manager.py` `arg-type` diagnostic and reconciliation guard.
- [x] **STEP 4: Development**
  - [x] Implemented the minimal optional-webhook URL narrowing in
    `pypost/core/alert_manager.py`; the existing request and logging behavior remains
    unchanged for configured webhooks.
  - [x] Ratcheted `mypy-baseline.json` by removing four duplicate
    `_webhook_log_target` `arg-type` occurrences and one `requests.post` `arg-type`
    occurrence, all directly retired by the source change.
  - [x] `make typecheck` — passed with 180 known errors in the exact core/models/ui scope.
  - [x] `make test PYTEST_ARGS=tests/test_pypost_1255_mypy_baseline_repro.py` — focused
    repro passed (2 tests).
  - [x] `make lint` and `make verify-ai-tasks` — passed.
  - Pre-existing metadata mismatch recorded: `error_count` was 189 while the serialized
    `errors` list and live gate contained 185 records; it is now honestly corrected to 180.
    The four-record metadata discrepancy is not claimed as a type fix.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1255/50-observability.md` — audited existing alert-manager structured
    logging and request retry metrics; no new production telemetry was required for the
    typing-only URL narrowing.
  - `make lint`, `make typecheck`, and `make verify-ai-tasks` — passed.
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - `doc/dev/static_type_checking.md` — documented the exact three-directory scope, Counter-key
    ratchet semantics, non-rewriting typecheck behavior, timeout failure, Make validation, and
    local webhook URL narrowing.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1255/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1255/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1255/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1255/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1255/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
