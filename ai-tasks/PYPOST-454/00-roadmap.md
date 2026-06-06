# Roadmap: PYPOST-454

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] **Iteration 1 (edge-case test matrices):** Added table-driven `subTest` tests per
    architecture Phase 1–2. Resolver: `test_malformed_nested_expressions` (M1–M4),
    `test_nested_spacing_variants` (S1–S5). TemplateService:
    `test_runtime_hover_parity_valid_spaced_nested` (S1–S3),
    `test_runtime_hover_parity_malformed_nested` (M1–M4 fallback),
    `test_runtime_hover_parity_invalid_spacing` (S4–S5 fallback),
    `test_validate_malformed_nested_alignment`. All 55 tests passed; no production changes.
    Locked codes match **observed** resolver behavior (differs from architecture matrix for
    M1/M2/M4/S5 — see STEP 6 tech-debt note). Phase 3 (`test_variable_hover.py`) skipped as optional.
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

`test/PYPOST-454-edge-case-expression-tests`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-454/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-454/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-454/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-454/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-454/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`
