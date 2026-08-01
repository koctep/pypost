# Roadmap: PYPOST-931

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_refresh_ci_duration_evidence.py` (script + Makefile + doc lock)
- [x] **STEP 4: Development**
  - [x] `scripts/refresh_ci_duration_evidence.py` (Actions API scrape + markdown)
  - [x] Makefile `refresh-ci-duration-evidence` / `check-ci-duration-evidence`
  - [x] `doc/dev/testing.md` refresh procedure + harness row
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (stdlib HTTP client + pytest contract/doc guards); English Markdown docs.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-931/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-931/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_refresh_ci_duration_evidence.py`

### STEP 4: Development

- `scripts/refresh_ci_duration_evidence.py`
- `Makefile`
- `doc/dev/testing.md`
- `doc/dev/agent_e2e.md`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-931/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-931/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-931/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (refresh procedure)
- `ai-tasks/PYPOST-931/70-dev-docs.md`
