# Roadmap: PYPOST-879

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change (YAGNI deferral; inventory evidence only)
- [x] **STEP 4: Development**
  - [x] Decision: **defer** shared `worker_timeout_detail` extraction
  - [x] Inventory: single consumer module
    `tests/test_collection_storage_worker.py` (local helper + 2 call sites)
  - [x] No second worker-only consumer; no harness refactor
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE (YAGNI deferral with inventory evidence)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/gui_testing.md` (worker-only helper stays local)
  - [x] Artifact: `ai-tasks/PYPOST-879/70-dev-docs.md`

## Programming Language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-879/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-879/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (documented in roadmap + architecture)

### STEP 4: Development

- Decision + inventory only (no production or harness extraction)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-879/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-879/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-879/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `ai-tasks/PYPOST-879/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-879-defer-worker-timeout-detail`

## Decision summary

**Defer extraction.** PYPOST-828 TD-2 allowed extracting local
`_worker_timeout_detail` into `tests/helpers/process_until.py` only if a
second worker-only consumer appears. Inventory (2026-07-22) still shows a
single consumer module. Prefer honest YAGNI close over forced refactor.
