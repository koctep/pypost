# Roadmap: PYPOST-1350

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`; review PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md` (Research, Implementation Plan, Failing Repro Design, Component Architecture, Q&A).
  - Defined catalog schema `examples/builtin-collections.yaml` and domain models `BuiltinCollectionEntry`, `BuiltinCollectionView` in `pypost/core/builtin_collections.py`.
  - Designed structural consistency test contract for paired environments under `tests/test_builtin_collections.py`; review PASS.
- [x] **STEP 3: Failing Repro Test**
  - tests/test_builtin_collections.py (10 failing tests asserting missing pypost.core.builtin_collections and examples/builtin-collections.yaml); review PASS.
- [x] **STEP 4: Development**
  - [x] Create curated catalog `examples/builtin-collections.yaml` with the 3 required entries (`jira-cloud-mcp`, `gitlab-mcp`, `github-mcp`) excluding `collections/mcp.json`.
  - [x] Create `pypost/core/builtin_collections.py` implementing `BuiltinCollectionEntry` and `BuiltinCollectionView` with fresh loading and graceful diagnostics.
  - [x] Validate all 10 tests in `tests/test_builtin_collections.py` pass cleanly.
  - [x] Validate static analysis (`make lint`) and type checking (`make typecheck`) pass cleanly; review PASS.
- [x] **STEP 5: Code Cleanup**
  - Static code analysis and linting (`make lint`, `make typecheck`) passing cleanly.
  - Formatted and enforced line length limit (<= 100 characters) across `examples/builtin-collections.yaml`, `pypost/core/builtin_collections.py`, and `tests/test_builtin_collections.py`.
  - Confirmed no unused imports, unused variables, or debug print statements.
  - All 11 tests in `tests/test_builtin_collections.py` passing with explicit timeout marker (`pytestmark = pytest.mark.timeout(30)`).
  - Created cleanup report `ai-tasks/PYPOST-1350/40-code-cleanup.md`; review PASS.
- [x] **STEP 6: Observability**
  - Documented structured logging across syslog levels (DEBUG, INFO, WARNING) and diagnostic tracking in `50-observability.md`.
  - Added structured logs in `pypost/core/builtin_collections.py` for discovery completion, entry loading, and diagnostic events.
  - Added observability and diagnostic contract test `test_builtin_collections_logging_and_diagnostics` in `tests/test_builtin_collections.py`.
  - Validated all 12 tests in `tests/test_builtin_collections.py` pass cleanly.
  - Verified `make lint` and `make typecheck` pass cleanly; review PASS.
- [x] **STEP 7: Technical Debt Analysis**
  - Documented absence of shortcuts and adherence to fresh loading and graceful diagnostics.
  - Confirmed code quality, strict <= 100 char limit, and full static analysis compliance.
  - Documented 12 comprehensive unit, seeded defect, and caplog contract tests with timeouts.
  - Recorded pre-existing baseline issues (PYPOST-1358, PYPOST-1359, PYPOST-1360) as non-blockers.
  - Documented planned upcoming sprint stories (PYPOST-1351 through PYPOST-1356, PYPOST-1347).
  - Created technical debt artifact `ai-tasks/PYPOST-1350/60-tech-debt.md`; review PASS; blocker review SAFE TO CLOSE.
- [x] **STEP 8: Dev Docs**
  - Updated developer documentation in `doc/dev/predefined_collection_library.md`:
    - Documented curated Built-in catalog format (`examples/builtin-collections.yaml`) specifying Jira Cloud, GitLab, and GitHub MCP collections paired with template environments, noting the explicit exclusion of synthetic test fixture `collections/mcp.json`.
    - Documented `BuiltinCollectionEntry` domain descriptor and its `selection()` identity matching MCP server configuration requirements (`library_id="pypost-examples"`, `path=collection_path`).
    - Documented `BuiltinCollectionView` read-only view layer over `PredefinedLibraryService`, fresh file loading on each call (`load_collection`, `load_paired_environment`), and graceful diagnostics collection without crashing on missing or corrupted definitions.
    - Documented structural consistency testing principles: manifest variable validation, secret hidden keys, non-empty placeholders, and overridable subsets without value comparison.
    - Kept line lengths <= 100 characters and valid markdown formatting.
  - Verified static analysis (`make lint`) and type check (`make typecheck`) pass cleanly.
  - Verified scoped test suite passes (`make test PYTEST_ARGS="tests/test_builtin_collections.py"`).
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1350/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1350/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1350/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1350/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1350/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
