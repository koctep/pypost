# Roadmap: PYPOST-1036

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1036/10-requirements.md` created
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1036/20-architecture.md` created
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_safe_path_grammar_edge_locks.py` created locking malformed dot rejections, child underscore rejections, and deep navigation
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Grammar boundary rules verified against `_SAFE_PATH_RE` and `FunctionExpressionResolver` implementation
  - [x] Verified test suites across `tests/test_safe_path_grammar_edge_locks.py`, `tests/test_function_arg_safe_paths.py`, `tests/test_function_expression_resolver.py`, and `tests/test_template_service.py`
  - [x] Static analysis (`make lint`) and AI task verification (`make verify-ai-tasks`) passing cleanly
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1036/40-code-cleanup.md` created
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1036/50-observability.md` created
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1036/60-tech-debt.md` created
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/template_expression_functions.md` with grammar edge lock examples table
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1036/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1036/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1036/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1036/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1036/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported in chat only, never written to this file.
