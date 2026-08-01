# Roadmap: PYPOST-928

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ci_workflow_yaml_helper.py::test_ci_contract_modules_use_shared_workflow_job_block`
- [x] **STEP 4: Development**
  - [x] Added `tests/helpers/ci_workflow_yaml.py` with PyYAML-validated `workflow_job_block`
  - [x] Migrated five CI contract modules to shared helper
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest contract tests under `tests/`)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-928/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-928/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ci_workflow_yaml_helper.py`

### STEP 4: Development

- `tests/helpers/ci_workflow_yaml.py`
- Updated CI contract test modules (874/909/910/923/927 locks)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-928/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-928/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-928/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (CI workflow contract helper section)
