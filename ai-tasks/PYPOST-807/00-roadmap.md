# Roadmap: PYPOST-807

**Branch (reference):** `chore/PYPOST-807-pytest-pyproject`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Move `pytest.ini` settings to `[tool.pytest.ini_options]` in `pyproject.toml`
  - [x] Remove root `pytest.ini`
  - [x] Update developer docs referencing pytest config location
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

- `ai-tasks/PYPOST-807/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-807/20-architecture.md`

### STEP 3: Development

- `pyproject.toml` (pytest section), deleted `pytest.ini`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-807/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-807/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-807/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`, `doc/dev/testing.md`, `doc/dev/observability_audit.md`,
  `doc/dev/test_audit.md`, `doc/dev/tech-debt/PYPOST-434.md`
- `ai-tasks/PYPOST-807/70-dev-docs.md`
