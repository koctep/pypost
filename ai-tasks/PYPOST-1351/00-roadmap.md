# Roadmap: PYPOST-1351

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`; review PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md` (Research, Implementation Plan with failing
    repro test design, Architecture, Q&A); review PASS.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_builtin_startup.py` (failing automated repro covering AC 1-7); review PASS.
- [x] **STEP 4: Development**
  - Added `bundled_library: bool = False` to `McpServerConfiguration` with type validation.
  - Implemented `_BundledLibraryAdapter` in `MCPServerRegistry` backed by `BuiltinCollectionView`.
  - Added view membership check and isolated runtime resolution in
    `MCPServerRegistry._runtime_inputs`.
  - Updated `_missing_reference` to return `"built-in collection"` for missing bundled servers.
  - Verified all 8 tests pass in `tests/test_mcp_builtin_startup.py`.
  - Verified static analysis (`make lint`, `make typecheck`) passes cleanly; review PASS.
- [x] **STEP 5: Code Cleanup**
  - Ran static analysis (`make lint`, `make typecheck`) with zero warnings or errors.
  - Verified line lengths <= 100 characters and absence of unused imports/variables and debug
    prints.
  - Verified all tests in `tests/test_mcp_builtin_startup.py` pass with explicit timeout marker.
  - Generated cleanup report `ai-tasks/PYPOST-1351/40-code-cleanup.md`; review PASS.
- [x] **STEP 6: Observability**
  - Documented structured logging across syslog levels (DEBUG, INFO, WARNING) in
    `MCPServerRegistry`, `BuiltinCollectionView`, and `PredefinedLibraryService`.
  - Documented structured log attributes (instance_id, port, state, library_id, collection_path,
    reason).
  - Documented diagnostics exposure and status message `"missing built-in collection"`.
  - Added test case `test_builtin_server_observability_and_logging` in
    `tests/test_mcp_builtin_startup.py` verifying structured logs and error diagnostics via caplog.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts and code quality: clean implementation, type-annotated, line length <= 100.
  - Evaluated tests: 9 unit/integration/caplog tests with explicit timeouts (`pytestmark = 30s`).
  - Evaluated performance: sub-millisecond in-memory resolution via `BuiltinCollectionView`.
  - Documented non-blocker pre-existing baseline failures: PYPOST-1358, PYPOST-1359, PYPOST-1360.
  - Documented planned follow-up sprint stories: PYPOST-1352 through PYPOST-1356.
  - Generated technical debt report `ai-tasks/PYPOST-1351/60-tech-debt.md`; review PASS;
    blocker review SAFE TO CLOSE.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/predefined_collection_library.md` with Built-in MCP Server Configuration and
    Startup details.
  - Documented `McpServerConfiguration.bundled_library` model field and validation rules.
  - Documented `MCPServerRegistry` bundled adapter (`_BundledLibraryAdapter`), view membership
    validation, runtime isolation, and headless daemon compatibility; review PASS.
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1351/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1351/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1351/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1351/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1351/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/predefined_collection_library.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
