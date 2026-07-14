# Roadmap: PYPOST-806

**Branch (reference):** `chore/PYPOST-806-editable-install`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `make install` → `pip install -e ".[dev,otel]"`
  - [x] `make venv-test` / `make venv-otel` → editable extras
  - [x] CI main, smoke, and security-audit jobs updated
  - [x] `tests/test_makefile.py` fixtures use `pyproject.toml`
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

- `ai-tasks/PYPOST-806/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-806/20-architecture.md`

### STEP 3: Development

- `Makefile`, `.github/workflows/test.yml`, `tests/test_makefile.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-806/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-806/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-806/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/testing.md`, `doc/dev/dependencies_audit.md`,
  `doc/dev/static_type_checking.md`, `README.md`
- `ai-tasks/PYPOST-806/70-dev-docs.md`
