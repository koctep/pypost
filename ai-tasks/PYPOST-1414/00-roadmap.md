# Roadmap: PYPOST-1414

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Initialized roadmap with task metadata and Python implementation language
  - [x] Gathered requirements from Jira PYPOST-1414 and technical debt context in PYPOST-1411
  - [x] Documented business goals, user stories, scope, functional and non-functional requirements, constraints, business entities, and scenarios in `ai-tasks/PYPOST-1414/10-requirements.md`
  - [x] Review passed and accepted
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Researched existing domain engine (`pypost/core/collection_variable_import.py`), dialog (`pypost/ui/dialogs/import_collection_variables_dialog.py`), tests (`tests/test_workspace_environment_import_repro.py`), and widget IDs (`pypost/ui/widget_ids.py`)
  - [x] Designed per-variable conflict strategy resolution in domain engine (`variable_conflict_strategies: dict[str, ConflictStrategy]`)
  - [x] Designed side-by-side diff inspector table (`Current Value` vs `Candidate Value`), per-row strategy selector, bulk controls, and secret masking
  - [x] Designed Step 3 failing repro tests (core per-variable strategy, UI side-by-side diff, per-row combo, bulk actions, secret masking)
  - [x] Created `ai-tasks/PYPOST-1414/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Automated failing repro tests in `tests/test_workspace_environment_import_diff_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Extended `import_collection_variables_to_environment` in `pypost/core/collection_variable_import.py` to support `variable_conflict_strategies: dict[str, ConflictStrategy] | None`, per-key resolution fallback, and secret masking consistency.
  - [x] Iteration 2: Registered new automation widget IDs in `pypost/ui/widget_ids.py` (`IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON`, `IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON`, `IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX`).
  - [x] Iteration 3: Redesigned `ImportCollectionVariablesDialog` in `pypost/ui/dialogs/import_collection_variables_dialog.py`:
    - 9-column inspection table with side-by-side diff (`Current Value` vs `Candidate Value`).
    - Per-row conflict strategy selection via `QComboBox` for collisions defaulting safely to `Keep Current`.
    - Bulk action controls ("Keep All Collisions", "Overwrite All Collisions") and dynamic preview summary calculation.
    - Dual-source secret masking in comparison columns (`HIDDEN_MASK`).
    - Preserved per-row strategy choices across preset switches and passed per-variable decisions to domain engine on accept.
  - [x] Iteration 4: Verified Step 3 repro tests and existing import tests pass GREEN (`tests/test_workspace_environment_import_diff_repro.py`, `tests/test_workspace_environment_import_repro.py`), and confirmed repository quality gates pass (`make lint`, `make typecheck`, `make verify-ai-tasks`).
- [x] **STEP 5: Code Cleanup**
  - [x] Inspected modified files (`pypost/core/collection_variable_import.py`, `pypost/ui/dialogs/import_collection_variables_dialog.py`, `pypost/ui/widget_ids.py`, `tests/test_workspace_environment_import_diff_repro.py`) for line length <= 100, formatting, unused imports, dead code, and debug prints.
  - [x] Cleaned up provisional try/except import fallback in `tests/test_workspace_environment_import_diff_repro.py` to direct imports.
  - [x] Verified explicit timeout markers (`@pytest.mark.timeout(30)`) on all test functions and module marker.
  - [x] Verified repository quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`).
  - [x] Created `ai-tasks/PYPOST-1414/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - [x] Implemented structured logging for per-variable conflict decisions, bulk strategies, and collision breakdowns
  - [x] Verified zero plaintext secret leakage across all log statements
  - [x] Created `ai-tasks/PYPOST-1414/50-observability.md` documenting observability architecture and metrics
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed shortcuts, code quality issues, missing tests, and performance concerns in `ai-tasks/PYPOST-1414/60-tech-debt.md`
  - [x] Identified pre-existing non-blockers and verified no blockers exist for closing task
- [x] **STEP 8: Dev Docs**
  - [x] Document domain engine per-variable conflict strategy parameter and resolution precedence in `doc/dev/workspace_environment_variable_import.md`
  - [x] Document 9-column side-by-side diff table layout, per-row strategy QComboBox, bulk actions, and dual-source secret masking in `doc/dev/workspace_environment_variable_import.md`
  - [x] Update testing section to reference `tests/test_workspace_environment_import_diff_repro.py`
  - [x] Create `ai-tasks/PYPOST-1414/70-dev-docs.md` summarizing dev docs updates and artifacts
  - [x] Acceptance gate passed
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1414/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1414/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_workspace_environment_import_diff_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1414/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1414/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1414/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/workspace_environment_variable_import.md`
- `ai-tasks/PYPOST-1414/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
