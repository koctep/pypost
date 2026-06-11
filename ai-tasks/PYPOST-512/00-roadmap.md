# Roadmap: PYPOST-512

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `validate/` package: `ValidationError`, `BodyValidator` registry,
    `JsonBodyValidator`, YAML/XML stubs, `ValidationController` with debounced scan
  - [x] Integrated validation into `CodeEditor` (line highlight, column underline,
    error banner)
  - [x] Added `tests/test_code_editor_validation.py`; all tests pass (`make test`)
- [x] **STEP 4: Code Cleanup**
  - [x] `40-code-cleanup.md`; full suite passes
- [x] **STEP 5: Observability**
  - [x] `50-observability.md`; no body-content logging added
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md`; Jira Debt follow-ups created
- [x] **STEP 7: Dev Docs**
  - [x] `doc/dev/body_editor_validation.md`; folding doc cross-reference

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-512/10-requirements.md`
- Programming Language: Python 3.10+

### STEP 2: Architecture

- `ai-tasks/PYPOST-512/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-512/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-512/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-512/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/body_editor_validation.md`

## Recommended Branch

`feature/PYPOST-512-body-format-validation`
