# Roadmap: PYPOST-457

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `test_catalog_allow_list_matches_env_globals` in `tests/test_function_registry.py`
  - [x] Added `test_catalog_allow_list_matches_jinja_globals` in `tests/test_template_service.py`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

**Python** — same as the pypost application codebase (see `.cursor/lsr/do-python.md`).

## Branch

`test/PYPOST-457-registry-globals-parity-test`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-457/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-457/20-architecture.md`

### STEP 3: Development

- `tests/test_function_registry.py`
- `tests/test_template_service.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-457/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-457/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-457/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/template_expression_functions.md`
- `ai-tasks/PYPOST-457/70-dev-docs.md`
