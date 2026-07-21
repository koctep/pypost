# Roadmap: PYPOST-883

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — investigation-first; classic red deferred (no stable hang).
    Campaign done: B×3 green + Probe C (200 cycles) green → outcome
    not_reproduced. Evidence: `30-findings.md`. Probe:
    `tests/test_pypost_883_save_async_gc_probe.py`.*
- [x] **STEP 4: Development**
  - [x] Phase 2a close-with-evidence: no speculative product/harness harden
  - [x] Kept Probe C as permanent canary
    (`tests/test_pypost_883_save_async_gc_probe.py`)
  - [x] Re-verified DoD clusters + canary: 111 passed (~17.8s); findings
    updated
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; flake8 clean; DoD + canary 111 passed
    (~18.3s)
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — N/A (investigation/harness; no production logs)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; no Debt tickets
- [x] **STEP 8: Dev Docs**
  - [x] `gui_testing.md` + `environment_storage_async.md` Probe C notes; `70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-883/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-883/20-architecture.md` (done; investigation-first;
  failing repro N/A with suite-pressure repro plan; Probe C mandatory for
  unreproducible close; B path list pinned; findings → `30-findings.md`)

### STEP 3: Failing Repro

- N/A — investigation-first (no classic pre-fix red); campaign executed
- Evidence: `ai-tasks/PYPOST-883/30-findings.md` — outcome **not_reproduced**
- Probe B: pinned suite-prefix ×3 — 110 passed each (~15s)
- Probe C: `tests/test_pypost_883_save_async_gc_probe.py` — 200 save-completed
  waits + QComboBox/`deleteLater`/`gc.collect` — passed (~2.8s)

### STEP 4: Development

- Phase 2a close-with-evidence (no production lifecycle harden)
- Probe C kept as permanent canary (docstring adjusted)
- Focused DoD clusters + canary re-verified: 111 passed (~17.8s)
- Findings Decision / Green clusters updated for Step 4

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-883/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-883/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-883/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-883/70-dev-docs.md`
- `doc/dev/gui_testing.md` (Probe C canary + troubleshooting)
- `doc/dev/environment_storage_async.md` (PYPOST-883 canary section)

## Suggested branch name

`chore/PYPOST-883-investigate-save-async-hang`
