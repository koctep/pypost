# Roadmap: PYPOST-1373

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Analyze parent epic PYPOST-1284, decomposition notes, architecture specification PYPOST-1368, and CollectionVariable help_text attribute from PYPOST-1372
  - [x] Define functional requirements (FR-1 through FR-5), non-functional requirements, constraints, main entities, and user stories
  - [x] Create `ai-tasks/PYPOST-1373/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research PySide6 / Qt dialog and card patterns, secrets masking, expandable guidance, and headless testing
  - [x] Design failing repro test plan in tests/test_variable_setup_wizard_repro.py for Step 3
  - [x] Design component architecture, module structure, class APIs, and validation feedback
  - [x] Await review and approval (orchestrator marks [x] after review PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_variable_setup_wizard_repro.py` (author automated red repro; verify failure mode)
- [x] **STEP 4: Development**
  - [x] Implement VariableGuidanceCard and VariableSetupWizardDialog in pypost/ui/variable_setup_wizard_dialog.py
  - [x] Add widget identifiers to pypost/ui/widget_ids.py
  - [x] Verify test_variable_setup_wizard_repro.py passes green
  - [x] Verify no regressions across existing test suites (tests/test_mcp_servers_dialog.py, tests/test_collection_variable_guidance_repro.py)
  - [x] Verify quality gates pass (make lint, make typecheck, make verify-ai-tasks)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linters via Make (`make lint`, `make typecheck`, `make verify-ai-tasks`)
  - [x] Run test suite via Make (`make test PYTEST_ARGS="tests/test_variable_setup_wizard_repro.py"`)
  - [x] Inspect code and tests for formatting, typing, docstrings, dead code, and timeout markers
  - [x] Draft `ai-tasks/PYPOST-1373/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Identify product runtime metrics, UI observability events, and secret masking boundaries
  - [x] Detail downstream integration observability for PYPOST-1374 (editor integration)
  - [x] Document process observability (Jira traceability, quality gates, worklog)
  - [x] Author `ai-tasks/PYPOST-1373/50-observability.md` following td-50-observability template
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, code quality, missing tests, and performance concerns
  - [x] Identify follow-up tasks (PYPOST-1374, PYPOST-1375)
  - [x] Draft `ai-tasks/PYPOST-1373/60-tech-debt.md`
  - [x] Await review and approval (orchestrator marks [x] after review PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Document `VariableGuidanceCard` and `VariableSetupWizardDialog` in `doc/dev/mcp_server_registry.md`
  - [x] Link documentation to parent epic PYPOST-1284 and story PYPOST-1373
  - [x] Draft `ai-tasks/PYPOST-1373/70-dev-docs.md` capturing documentation decisions
  - [x] Await review and approval (orchestrator marks [x] after review PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1373/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1373/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1373/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1373/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1373/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
