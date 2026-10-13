# Roadmap: PYPOST-1375

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Create `ai-tasks/PYPOST-1375/00-roadmap.md` and `ai-tasks/PYPOST-1375/10-requirements.md`
  - [x] Gather and document business goals, functional requirements (FR-1 through FR-5), non-functional requirements, constraints, entities, and user stories
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design contract test suite in `tests/test_reference_collection_variable_guidance_contract.py`
  - [x] Specify Google Drive OAuth setup instructions in `examples/collections/google_drive.json`
  - [x] Define end-to-end component structure and sequence diagrams
  - [x] Outline developer / collection author guidance documentation
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_reference_collection_variable_guidance_contract.py` (author automated red repro; verify failure mode)
- [x] **STEP 4: Development**
  - [x] Add OAuth setup markdown guidance (`help_text`) to `google_drive_access_token` in `examples/collections/google_drive.json` adhering to 20-architecture.md
  - [x] Verify contract test suite `tests/test_reference_collection_variable_guidance_contract.py` passes green (5/5 passing)
  - [x] Verify packaging (`tests/test_bundled_examples_packaging.py`) and wizard regression test suites pass
  - [x] Pass all quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis, linting, and formatting checks (`make lint`)
  - [x] Run static type checking (`make typecheck`)
  - [x] Verify test suite passes with explicit timeouts (`make test`)
  - [x] Verify AI task artifacts integrity (`make verify-ai-tasks`)
  - [x] Inspect test and collection files for dead code, unused imports, line lengths, and type annotations
  - [x] Author code cleanup report (`ai-tasks/PYPOST-1375/40-code-cleanup.md`)
- [x] **STEP 6: Observability**
  - [x] Analyze runtime & telemetry observability points (collection loading, schema validation, variable guidance diagnostics)
  - [x] Define strict sensitive field masking rules (zero secret leakage for `google_drive_access_token` and OAuth credentials)
  - [x] Document contract test suite & CI/CD quality gate metrics (`test_reference_collection_variable_guidance_contract.py`, `test_bundled_examples_packaging.py`)
  - [x] Document process observability (Jira traceability across Sprint 2029 child stories: PYPOST-1368, PYPOST-1372, PYPOST-1373, PYPOST-1374, PYPOST-1375, worklog ceil(tokens/100))
  - [x] Draft `ai-tasks/PYPOST-1375/50-observability.md` adhering to `td-50-observability` template
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Review parent epic PYPOST-1284 closure and potential future collection enhancements
  - [x] Author technical debt analysis report in `ai-tasks/PYPOST-1375/60-tech-debt.md`
  - [x] Await review and approval (orchestrator marks [x] after review PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Create developer documentation in `doc/dev/collection_variable_guidance.md` covering `help_text` schema, markdown standards, zero credential leakage, UI presentation, testing contracts, and `google_drive.json` showcase
  - [x] Link documentation to parent epic PYPOST-1284 and story PYPOST-1375
  - [x] Draft `ai-tasks/PYPOST-1375/70-dev-docs.md` capturing developer documentation decisions
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1375/00-roadmap.md`
- `ai-tasks/PYPOST-1375/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1375/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_reference_collection_variable_guidance_contract.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1375/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1375/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1375/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_variable_guidance.md`
- `ai-tasks/PYPOST-1375/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
