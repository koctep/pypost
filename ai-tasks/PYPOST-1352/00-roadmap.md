# Roadmap: PYPOST-1352

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`; review PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md`.
  - Designed registry lifecycle reconciliation, reconfigure, and environment refresh for
    Built-in rows.
  - Designed controller save transaction with `overlay={}` and safe rollback for Built-in rows.
  - Designed 8 acceptance criteria test cases for Step 3 failing repro in
    `tests/test_mcp_builtin_lifecycle.py`; review PASS.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_builtin_lifecycle.py`
- [x] **STEP 4: Development**
  - [x] Implemented Built-in reference reconciliation, reconfigure validation, and environment
    refresh in `pypost/core/mcp_server_registry.py`.
  - [x] Implemented Built-in save branch with curated path check and no-overlay persistence in
    `pypost/ui/mcp_server_controller.py`.
  - [x] Verified all 8 acceptance tests pass green in `tests/test_mcp_builtin_lifecycle.py` and
    all regression suites pass. Lint and typecheck clean; review PASS.
- [x] **STEP 5: Code Cleanup**
  - Static code analysis and linting clean (`make lint`, `make typecheck`).
  - Formatting and strict <= 100 character line length verified across modified files.
  - Test suite passes with explicit timeout markers (`tests/test_mcp_builtin_lifecycle.py`).
  - Documented in `40-code-cleanup.md`; review PASS.
- [x] **STEP 6: Observability**
  - Documented logging events across syslog levels (DEBUG, INFO, WARNING, ERROR).
  - Documented structured log attributes (server_id, library_id, collection_path, environment_id).
  - Documented diagnostics and failure indicators (missing built-in collection / environment).
  - Added test coverage in `tests/test_mcp_builtin_lifecycle.py` with `caplog` assertions.
  - Documented in `50-observability.md`; review PASS.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts taken (none, isolated branch for Built-in rows, zero overlay writes).
  - Evaluated code quality issues (clean, type-annotated, line length <= 100).
  - Evaluated missing tests (none, 9 unit and integration tests including caplog test).
  - Evaluated performance concerns (minimal overhead, in-memory reference reconciliation).
  - Documented pre-existing non-blocker failures (PYPOST-1358, PYPOST-1359, PYPOST-1360).
  - Documented generic library lifecycle follow-up non-blocker (PYPOST-1347).
  - Documented planned next steps under epic PYPOST-1335 (PYPOST-1353 through PYPOST-1356).
  - Documented in `60-tech-debt.md`; review PASS; blocker review SAFE TO CLOSE.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/predefined_collection_library.md` with:
    - `MCPServerRegistry.reconcile_references` decoupling Built-in rows from `collection_id`
      and `valid_collection_ids`, checking curated catalog entries, and stopping only when
      the environment or curated collection is missing.
    - `MCPServerRegistry.reconfigure` dynamic migration and replacement validation against
      curated view entries without requiring `collection_id`.
    - `MCPServerRegistry.refresh_environment` re-resolving runtime configuration via
      `LibraryRuntimeResolver` with `_bundled_adapter` and empty candidate overlay, guaranteeing
      manifest default variables survive when the environment omits them.
    - `McpServerSettingsController.upsert_mcp_server` dedicated Built-in branch preceding generic
      library handling, curated view membership validation, complete overlay isolation
      (`overlay={}`), external library isolation, and transactional rollback.
    - Updated PYPOST-1352 status in the architecture tracking table to Implemented.
    - Verified markdown formatting and strict <= 100 character line length (`make lint`); review PASS.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1352/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1352/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1352/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1352/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1352/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
