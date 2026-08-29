# Roadmap: PYPOST-1151

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1151/00-roadmap.md` created with task metadata
  - [x] `ai-tasks/PYPOST-1151/10-requirements.md` created detailing goals, user stories, requirements, and ACs
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1151/20-architecture.md` created with research, implementation plan, failing repro strategy, architecture diagrams, and traceability matrix
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `ai-tasks/PYPOST-1151/25-failing-repro.md` created documenting pre-existing test defect status, PYPOST-1176 pattern separation, and test execution results
  - [x] Verified `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` via `make test`
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Expanded `tests/test_template_expression_tokenizer.py` with comprehensive strict inner whitespace rejection tests across spaces, tabs, and newlines for `is_plain_variable_token` and `extract_plain_variable_name`.
  - [x] Added unit test coverage for `LOOSE_PLAIN_VARIABLE_PATTERN`, `is_loose_plain_variable_token`, and `extract_loose_plain_variable_name` validating whitespace variation handling and rejection of nested functions and invalid expressions.
  - [x] Verified test suite and static analysis via `make test PYTEST_ARGS="tests/test_template_expression_tokenizer.py -v"`, `make lint`, and `make verify-ai-tasks`.
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1151/40-code-cleanup.md` created documenting lint check, code formatting, code cleanup, and test validation
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1151/50-observability.md` created documenting observability review (pure in-memory parsing requires no new logging/metrics) and explicit 30s timeout marker verification
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1151/60-tech-debt.md` created with shortcuts, code quality issues, missing tests, performance concerns, and tracked pre-existing base issues (PYPOST-1231, 1232, 1233, 1234, 1241)
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/template_expression_functions.md` with plain variable pattern & whitespace handling section
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1151/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1151/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1151/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1151/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1151/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
