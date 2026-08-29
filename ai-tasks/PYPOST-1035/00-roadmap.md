# Roadmap: PYPOST-1035

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Create `ai-tasks/PYPOST-1035/00-roadmap.md`
  - [x] Create `ai-tasks/PYPOST-1035/10-requirements.md`
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Create `ai-tasks/PYPOST-1035/20-architecture.md`
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_function_arg_safe_paths.py` created locking catalog functions with safe/unsafe dotted args and nested rendering
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Expand `tests/test_function_expression_resolver.py` with tests validating catalog functions with safe dotted arguments (`urlencode`, `md5`, `base64`, `to_int`, `env`) and rejecting unsafe attribute access paths
  - [x] Expand `tests/test_template_service.py` with tests verifying `render_string` evaluates nested dictionary values when passed as arguments to catalog functions
  - [x] Verified full regression suite across `tests/test_function_arg_safe_paths.py`, `tests/test_function_expression_resolver.py`, and `tests/test_template_service.py`
  - [x] Quality gates passed: `make test`, `make lint`, `make verify-ai-tasks`
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] Create `ai-tasks/PYPOST-1035/40-code-cleanup.md`
  - Step 5 acceptance gate passed (review verdict PASS)

- [x] **STEP 6: Observability**
  - [x] Create `ai-tasks/PYPOST-1035/50-observability.md`
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Create `ai-tasks/PYPOST-1035/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/template_expression_functions.md` referencing function-arg safe path test locks
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1035/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1035/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1035/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1035/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1035/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
