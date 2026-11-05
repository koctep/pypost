# Roadmap: PYPOST-1320

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1320/00-roadmap.md`
  - `ai-tasks/PYPOST-1320/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1320/20-architecture.md`
  - Direction: replace per-wait `threading.Timer.start` with a long-lived daemon
    deadline scheduler in `tests/helpers/process_until.py`; keep
    `use_poll_timer=False` posted-quit hang-regression; product unchanged by default
- [x] **STEP 3: Failing Repro Test**
  - Red: `tests/test_process_until_watchdog_repro.py::test_process_until_exits_near_deadline_under_qthread_exc_info`
  - Asserts `process_until(..., use_poll_timer=False)` finishes within ~2×`timeout_ms` while a QThread holds limbo mid-`logger.error(..., exc_info=True)`; currently fails because GUI blocks in `Timer.start` / `_started.wait` past the bound
- [x] **STEP 4: Development**
  - [x] Started Step 4: replace per-wait ``Timer.start`` with long-lived deadline scheduler in ``tests/helpers/process_until.py``
  - [x] Implemented ``_DeadlineScheduler`` + ``_arm_posted_quit``; ``process_until`` arms/cancels via shared daemon (no per-wait ``Timer.start``)
  - [x] Green: ``test_process_until_exits_near_deadline_under_qthread_exc_info``; hang-regression + diagnostics stay green
  - [x] Stress: 12× watchdog repro green; 7× parallel faulthandler runs of teardown-repro + zero-candidates + watchdog repro green
  - [x] ``make lint`` OK; product code unchanged; public ``process_until`` API unchanged
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1320/40-code-cleanup.md`
  - Stale Step-3 comments cleaned in `tests/test_process_until_watchdog_repro.py`
  - `make lint` OK; focused `make test` (watchdog repro + diagnostics + env
    storage responsiveness) 3/3 green; no unused imports/debug/dead Timer path
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1320/50-observability.md`
  - Decision: N/A for production logs/metrics (harness-only `_DeadlineScheduler`)
  - Retained: `timeout_detail` / `gateway_timeout_detail` AssertionError channel
  - Documented hang / timeout failure modes for CI triage; no new helper logging
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1320/60-tech-debt.md`
  - Analyzed `_DeadlineScheduler` / `_arm_posted_quit`, watchdog repro, hang-regression
    retention, and stale Timer docs; timeout markers OK (no BLOCKER)
  - Follow-ups recorded with empty Jira links for Phase D
- [x] **STEP 8: Dev Docs**
  - `doc/dev/gui_testing.md` — shared `_DeadlineScheduler` / posted-quit backstop;
    bootstrap note (TD-5); watchdog repro coverage; PYPOST-1320 reference
  - `doc/dev/testing.md` — no per-wait `threading.Timer.start` wording
  - `doc/dev/environment_storage_async.md` — dual-deadline uses module-scoped scheduler
  - `doc/dev/collection_import.md` — PYPOST-1320 historical hang note updated (mitigated)
  - TD-2 covered (primary + siblings); TD-5 bootstrap documented as residual first-wait only
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1320/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1320/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_process_until_watchdog_repro.py` (red until Step 4 scheduler)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1320/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1320/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1320/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
- `doc/dev/collection_import.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
