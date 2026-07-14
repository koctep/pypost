# Roadmap: PYPOST-787

**Branch (reference):** `chore/PYPOST-787-optional-otel-deps`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Removed OTel from `requirements.in` and `[project].dependencies`
  - [x] Added `requirements-otel.in` / `requirements-otel.txt` overlay
  - [x] Added Makefile `lock-otel`, `check-lock-otel`, `venv-otel`
  - [x] Updated CI to install OTel overlay for tests
  - [x] Extended `tests/test_pyproject.py` and `tests/test_makefile.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-787/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-787/20-architecture.md`

### STEP 3: Development

- `requirements.in`, `requirements.txt`, `requirements-otel.in`, `requirements-otel.txt`
- `pyproject.toml`, `Makefile`, `.github/workflows/test.yml`
- `tests/test_pyproject.py`, `tests/test_makefile.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-787/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-787/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-787/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/dependencies_audit.md`
- `ai-tasks/PYPOST-787/70-dev-docs.md`
