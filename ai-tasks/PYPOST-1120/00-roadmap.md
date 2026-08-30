# Roadmap: PYPOST-1120

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1120/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1120/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_template_service_strict_provenance.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Add ExpressionFailureProvenance and update ValidationResult with backward-compatible failures tuple and has_strict_failure property
  - [x] Iteration 2: Add is_strict_conversion method and _strict_functions set to FunctionRegistry
  - [x] Iteration 3: Implement structured failure inspection (inspect_failure_provenance), recursive strict detection, and unclosed placeholder handling in FunctionExpressionResolver
  - [x] Iteration 4: Refactor TemplateService to use resolver provenance and dynamic evaluation, removing _DIRECT_TO_INT_CALL_RE and _STARTED_TO_INT_CALL_RE regex attributes
  - [x] Iteration 5: Quality checks (green repro suite tests/test_template_service_strict_provenance.py, regression suites, make lint, make verify-ai-tasks)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1120/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1120/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1120/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/template_failure_provenance.md`
  - [x] `doc/dev/template_expression_functions.md`
  - [x] `doc/dev/template_service.md`
  - [x] `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1120/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1120/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code:
  - `pypost/core/template_expression_types.py`
  - `pypost/core/function_registry.py`
  - `pypost/core/function_expression_resolver.py`
  - `pypost/core/template_service.py`
- Tests:
  - `tests/test_template_service_strict_provenance.py` (7 tests green)
  - `tests/test_template_service.py` (regression green)
  - `tests/test_function_registry.py` (regression green)
  - `tests/test_function_expression_resolver.py` (regression green)
  - `tests/test_function_arg_safe_paths.py` (regression green)
  - `tests/test_http_client.py` (regression green)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1120/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1120/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1120/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/template_failure_provenance.md`
- `doc/dev/template_expression_functions.md`
- `doc/dev/template_service.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
