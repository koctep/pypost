# Roadmap: PYPOST-823

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Hardened `_process_until` with wall-clock deadline + daemon
    `QTimer.singleShot(0, loop, loop.quit)` posted quit; switched to shared
    `qapp`; added hang-regression tests (incl. no-poll-timer watchdog path)
- [x] **STEP 4: Code Cleanup**
  - [x] flake8 clean on scoped test; import order / `Callable` annotation;
    `40-code-cleanup.md`; 5/5 responsiveness tests passed
- [x] **STEP 5: Observability**
  - [x] No production logging/metrics; test-only hang fix documented in
    `50-observability.md` (wall-clock + posted-quit assertion as quality signal)
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md`: sibling `_process_until` helpers, richer timeout
    diagnostics, deferred H3 lifecycle; full `make test` suite results
    (hang gone; 3 unrelated tabs-presenter failures out of scope);
    SAFE TO CLOSE
- [x] **STEP 7: Dev Docs**
  - [x] Documented dual-deadline `_process_until` (wall-clock + posted quit) in
    `doc/dev/gui_testing.md`, `doc/dev/testing.md`, `doc/dev/environment_storage_async.md`;
    `70-dev-docs.md`

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-823/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-823/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-823/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-823/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-823/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-823/70-dev-docs.md`
- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
