# Roadmap: PYPOST-828

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extended `process_until` with optional lazy `timeout_detail`; added
    `format_storage_async_timeout_detail`; neutralized default timeout wording
    (no `load_completed/load_failed`); hang-defense timing unchanged
  - [x] Wired gateway call sites (env responsiveness, env/collection gateways)
    with busy/pending + optional worker; wired collection worker waits with
    optional `worker_running`
  - [x] Added focused diagnostic tests in `tests/test_process_until_diagnostics.py`
  - [x] Verified: 27 focused tests passed; flake8 clean on touched files;
    DoD met (richer timeout text; busy/pending on gateway waits; hang defense
    preserved)
- [x] **STEP 4: Code Cleanup**
  - [x] Deduplicated `_gateway_timeout_detail` into shared
    `gateway_timeout_detail()`; flake8/`make lint` clean; 28 focused tests
    passed; `40-code-cleanup.md` written
- [x] **STEP 5: Observability**
  - [x] Documented harness-only observability: AssertionError is the diagnostic
    channel; no production logging/metrics; `50-observability.md` written
- [x] **STEP 6: Review and Technical Debt**
  - [x] Created `60-tech-debt.md`; SAFE TO CLOSE; Jira links empty for Phase D
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/gui_testing.md` (timeout diagnostics API + examples)
  - [x] Updated `doc/dev/environment_storage_async.md` and `doc/dev/testing.md`
  - [x] Created `ai-tasks/PYPOST-828/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-828/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-828/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-828/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-828/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-828/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/environment_storage_async.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-828/70-dev-docs.md`

## Suggested branch name

`test/PYPOST-828-timeout-diagnostics`
