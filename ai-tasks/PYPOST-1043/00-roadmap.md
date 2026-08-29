# Roadmap: PYPOST-1043

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1043/00-roadmap.md` created with task metadata
  - [x] `ai-tasks/PYPOST-1043/10-requirements.md` created detailing goals, requirements, ACs, and call-site analysis
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1043/20-architecture.md` created with module map, caller migration plan, failing-repro plan, and traceability matrix
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `N/A — no behavioral change` (test-only ergonomic refactoring to `isolated_tree_actions` context manager; teardown already guaranteed via `close_isolated_tree_actions`)
  - [x] Baseline test execution verified across 5 target test suites via `make test`
  - [x] `ai-tasks/PYPOST-1043/25-failing-repro.md` created documenting N/A rationale and target call sites
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Migrated all 22 test methods in `tests/test_collection_tree_actions.py` to `with isolated_tree_actions(...) as harness:` and removed `addCleanup` calls
  - [x] Migrated all 8 test methods in `tests/test_collection_tree_rename_context_menu.py` to `with isolated_tree_actions(...) as harness:` and removed `addCleanup` calls
  - [x] Migrated all 5 test methods in `tests/test_collection_tree_delete_confirmation.py` to `with isolated_tree_actions(...) as harness:` and removed `addCleanup` calls
  - [x] Migrated all 4 test methods in `tests/test_collection_tree_rename_delegate_e2e.py` to `with isolated_tree_actions(..., with_rename_delegate=True) as harness:` and removed `addCleanup` calls
  - [x] Cleaned up unused helper imports (`build_isolated_tree_actions`, `close_isolated_tree_actions`) across all 4 modified test suites
  - [x] Preserved low-level helpers in `tests/helpers/collections_tree.py` and direct unit tests in `tests/test_qt_item_view_teardown.py`
  - [x] Verified tests pass: `make test PYTEST_ARGS="tests/test_collection_tree_actions.py tests/test_collection_tree_rename_context_menu.py tests/test_collection_tree_delete_confirmation.py tests/test_collection_tree_rename_delegate_e2e.py tests/test_qt_item_view_teardown.py"` (5/5 passed in 1.76s)
  - [x] Verified code quality via `make lint` and artifact validation via `make verify-ai-tasks`
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linting: `make lint` and flake8 across all modified test files
  - [x] Fixed unused import `MagicMock` in `tests/test_collection_tree_delete_confirmation.py`
  - [x] Fixed long line (>100 chars) in `tests/test_collection_tree_rename_context_menu.py`
  - [x] Fixed PEP 8 double blank line spacing before `__main__` across modified test files
  - [x] Validated explicit timeout markers across all test suites
  - [x] Verified targeted test suite execution: `make test PYTEST_ARGS="tests/test_collection_tree_actions.py tests/test_collection_tree_rename_context_menu.py tests/test_collection_tree_delete_confirmation.py tests/test_collection_tree_rename_delegate_e2e.py tests/test_qt_item_view_teardown.py"` (5/5 passed)
  - [x] `ai-tasks/PYPOST-1043/40-code-cleanup.md` created
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] Evaluated observability requirements: test-only ergonomics refactoring with no production logging or metric modifications
  - [x] Verified GUI telemetry mock tracking assertions (`track_gui_collection_rename_action`, `track_gui_collection_delete_action`, `track_gui_new_tab_action`) across migrated suites
  - [x] Confirmed bounded test execution with explicit 60s per-module timeouts
  - [x] `ai-tasks/PYPOST-1043/50-observability.md` created
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed implementation for shortcuts, code quality issues, missing tests, and performance concerns (none found)
  - [x] Verified PYPOST-973 TD-1 is resolved and closed forward
  - [x] Recorded pre-existing test/typecheck failures (PYPOST-1231, 1232, 1233, 1234, 1241) as NON-BLOCKER — pre-existing
  - [x] `ai-tasks/PYPOST-1043/60-tech-debt.md` created
  - Left `[/]` — the orchestrator marks `[x]` after review (td-roadmap gate)
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/testing.md` to document the `isolated_tree_actions` context manager pattern as the standard testing pattern for collection tree action suites
  - [x] Noted in `doc/dev/testing.md` that manual `build_isolated_tree_actions` + `addCleanup` is superseded by `with isolated_tree_actions(...) as harness:`
  - [x] Updated `doc/dev/collection_tree_actions.md` test fixtures documentation to list `isolated_tree_actions()`
  - [x] Verified formatting, markdown, and link checks via `make lint`
  - [x] Verified AI task artifact verification via `make verify-ai-tasks`
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

- `ai-tasks/PYPOST-1043/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1043/20-architecture.md`

### STEP 3: Failing Repro

- `ai-tasks/PYPOST-1043/25-failing-repro.md` (N/A — no behavioral change)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1043/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1043/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1043/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
