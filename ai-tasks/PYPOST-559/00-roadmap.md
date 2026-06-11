# Roadmap: PYPOST-559

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `@pytest.mark.slow` install smoke with real `requirements.txt`
  - [x] Registered `slow` marker; excluded from default CI and `make test`
  - [x] Added `make-install-smoke` CI job with pip cache
  - [x] Added `make test-slow` target
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest + subprocess + GitHub Actions YAML)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-559/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-559/20-architecture.md`

### STEP 3: Development

- `tests/test_makefile.py`
- `pytest.ini`
- `.github/workflows/test.yml`
- `Makefile`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-559/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-559/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-559/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-559/70-dev-docs.md`
