# Roadmap: PYPOST-1353

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`; review PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md`.
  - Design covers `_McpServerEditor`, `McpServersDialog`, and `McpControlsPresenter`.
  - Design includes failing repro test design for Step 3 in `tests/test_mcp_builtin_dialog.py`;
    review PASS.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_builtin_dialog.py`
- [x] **STEP 4: Development**
  - [x] Extended `_McpServerEditor` with `builtin_view`, `"Built-in"` source item,
    `_builtin_collection` picker with `(read-only)` markers and tooltips, hidden preset/overlay
    controls, environment validation, bundled configuration emission, and edit preselection.
  - [x] Extended `McpServersDialog` to accept `builtin_view`, pass it to editor, and render
    `"Built-in / <name> (read-only)"` in server overview table.
  - [x] Updated `McpControlsPresenter` to inject `builtin_view` from
    `controller.registry._builtin_view` to `McpServersDialog`.
  - [x] Verified `tests/test_mcp_builtin_dialog.py` and regression test suites pass green;
    review PASS.
- [x] **STEP 5: Code Cleanup**
  - Ran `make lint` and `make typecheck` (all passed, no new warnings or type issues).
  - Verified PEP 8 style, line lengths (strictly <= 100 chars), no unused imports/variables,
    no debug prints across modified/added files (`pypost/ui/dialogs/mcp_servers_dialog.py`,
    `pypost/ui/presenters/mcp_controls_presenter.py`, `tests/test_mcp_builtin_dialog.py`).
  - Verified test suite passes with explicit timeout markers
    (`pytestmark = pytest.mark.timeout(30)`).
  - Generated cleanup report `ai-tasks/PYPOST-1353/40-code-cleanup.md`; review PASS.
  - Verified task artifacts via `make verify-ai-tasks`.
- [x] **STEP 6: Observability**
  - Documented logging events across syslog levels (DEBUG, INFO, WARNING, ERR) in
    `pypost/ui/dialogs/mcp_servers_dialog.py` and `pypost/ui/presenters/mcp_controls_presenter.py`.
  - Documented UI diagnostics (in-place validation messages, error popups, tooltips, overview
    table read-only labels, status bar presentation).
  - Documented metrics integration and test verification coverage in
    `tests/test_mcp_builtin_dialog.py`.
  - Created observability artifact `ai-tasks/PYPOST-1353/50-observability.md`; review PASS.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts taken (none; full Qt component integration with read-only markers,
    tooltips, validation blocks).
  - Evaluated code quality issues (clean, type-annotated, line length strictly <= 100).
  - Evaluated missing tests (none; 6 headless GUI unit/integration tests with explicit timeouts).
  - Evaluated performance concerns (negligible in-memory combo population overhead).
  - Documented pre-existing baseline failures as `NON-BLOCKER — pre-existing`:
    - PYPOST-1358 (native UI environment-list teardown crash)
    - PYPOST-1359 (dev-lock check stale with CI-pinned uv)
    - PYPOST-1360 (install-smoke timeout on clean base)
  - Documented planned upcoming sprint stories:
    - PYPOST-1354 (Editable copy of paired environment for Built-in MCP servers)
    - PYPOST-1355 (Copy for editing a built-in MCP collection)
    - PYPOST-1356 (End-to-end test and user documentation for Built-in MCP source)
  - Generated technical debt artifact `ai-tasks/PYPOST-1353/60-tech-debt.md`; review PASS;
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/predefined_collection_library.md`:
    - Updated child issue tracking table row for PYPOST-1353 to `Implemented`.
    - Documented UI architecture in `_McpServerEditor` and `McpServersDialog`:
      - Third collection source option `"Built-in"` next to `"Workspace collection"` and
        `"Connected library"`.
      - Dynamic picker population via `BuiltinCollectionView.list_entries()` with `(read-only)`
        markers and informational tooltips.
      - Hiding of preset and overlay widgets for Built-in selections.
      - Mandatory workspace environment selection requirement before saving.
      - Emitting `McpServerConfiguration` with `bundled_library=True`,
        `library_id="pypost-examples"`, `manifest_id="pypost-examples"`,
        `library_collection_path`, and `collection_id=None`.
      - Editing preselection for existing bundled rows (`bundled_library=True`).
      - Backward compatibility guard preserving `"Connected library"` for legacy unbundled rows
        pointing to `pypost-examples`.
      - Server overview table displaying `Built-in / <name> (read-only)`.
      - Presenter dependency injection of `builtin_view` from `registry._builtin_view` to
        `McpServersDialog`.
    - Validated all line lengths strictly <= 100 characters and valid markdown syntax.
  - Verified documentation quality gate passes via `make lint`; review PASS.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1353/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1353/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1353/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1353/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1353/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
