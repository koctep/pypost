# PYPOST-1352: Technical Debt Analysis

## Shortcuts Taken

No shortcuts or compromises were taken during the implementation of PYPOST-1352:
- Fully isolated execution path for Built-in rows in `MCPServerRegistry.reconcile_references`,
  validating curated catalog presence and environment presence without checking workspace
  collections.
- Fully isolated replacement validation in `MCPServerRegistry._validate_replacement_references`
  for `reconfigure`, decoupling Built-in rows from `collection_id` constraints.
- Complete environment refresh logic in `MCPServerRegistry.refresh_environment` that re-resolves
  runtime inputs through `LibraryRuntimeResolver` and `_BundledLibraryAdapter`, preserving
  manifest defaults for undeclared environment variables.
- Dedicated transactional controller branch in `McpServerSettingsController.upsert_mcp_server`
  that checks curated collection membership prior to mutation, executes with `overlay={}`, writes
  zero overlay files to disk, and isolates the server from external clones or shadowed libraries.
- Clean rollback semantics in `reconfigure` preserving original server execution if replacement
  fails preflight validation or startup.

## Code Quality Issues

No code quality issues or architectural debt were introduced:
- All modifications in `pypost/core/mcp_server_registry.py` and
  `pypost/ui/mcp_server_controller.py` conform strictly to PEP 8, maintain line lengths <= 100
  characters, and provide full type annotations.
- Clean static analysis results (`make lint`, `make typecheck`) with zero regressions against the
  mypy baseline.
- Code responsibilities remain cleanly segregated between core registry lifecycle logic and UI
  controller transaction handling.

## Missing Tests

No missing test coverage. The test suite in `tests/test_mcp_builtin_lifecycle.py` provides 9
comprehensive integration and unit tests covering:
- Built-in server endurance through `reconcile_references` when workspace collections change.
- Server shutdown with appropriate diagnostics (`"cannot run: missing environment"`) when the
  selected environment is deleted.
- Live `reconfigure` of running Built-in rows (e.g., port update) with successful restart.
- Environment variable refresh preserving collection manifest defaults when variables are omitted.
- Complete isolation from external library clones with identical library IDs (`pypost-examples`).
- Overlay write prevention during Built-in server upsert (`save_overlay` is never called).
- Rejection of uncurated collection paths with explicit error handling and state preservation.
- Regression verification for ordinary workspace and library servers.
- Observability and structured logging validation across DEBUG, INFO, WARNING, and ERROR using
  `caplog`.
- All test functions include explicit timeouts via module-level
  `pytestmark = pytest.mark.timeout(30)` in accordance with `do-testing`.

## Performance Concerns

Minimal overhead:
- Curated collection view checks (`_builtin_view.list_entries()`) operate over in-memory cached
  manifest entries.
- Environment reconciliation iterates only over active server configurations and uses set lookups
  for valid environment IDs (`valid_environment_ids`).
- No disk I/O occurs on overlay persistence paths since Built-in rows bypass overlay serialization.

## Follow-up Tasks

### Pre-existing Test Failures (NON-BLOCKER)

Pre-existing test failures identified in the repository baseline (documented as non-blockers):
- `NON-BLOCKER — pre-existing`: PYPOST-1358 (native UI environment-list teardown crash)
  - Failure in UI test environment teardown lifecycle on specific Qt runner environments.
- `NON-BLOCKER — pre-existing`: PYPOST-1359 (dev-lock check stale with CI-pinned uv)
  - Discrepancy between pinned tool versions in CI and dev-lock file generation.
- `NON-BLOCKER — pre-existing`: PYPOST-1360 (install-smoke timeout on clean base)
  - Package installation smoke test exceeds timeout threshold under clean container initialization.

### Generic Library Lifecycle Follow-up (NON-BLOCKER)

- `NON-BLOCKER — pre-existing`: PYPOST-1347 (Generic library MCP rows lifecycle reconciliation)
  - Non-blocking follow-up ticket tracking generic library lifecycle reconciliation improvements.

### Planned Next Steps (Upcoming Sprint Stories)

The following planned sprint stories build upon this foundation under Epic PYPOST-1335:
- **PYPOST-1353**: "Built-in" source with read-only marker in the MCP server dialog
  - Surface the `"Built-in"` source tag in UI dialogs and mark configuration fields read-only.
- **PYPOST-1354**: Editable copy of the paired environment for Built-in MCP servers
  - Provide functionality to clone and customize paired environments for built-in server rows.
- **PYPOST-1355**: Copy for editing a built-in MCP collection
  - Allow users to clone a built-in MCP collection into their workspace for custom editing.
- **PYPOST-1356**: End-to-end test and user documentation for Built-in MCP source
  - Comprehensive end-to-end verification and user documentation covering the built-in MCP server
    feature set.
