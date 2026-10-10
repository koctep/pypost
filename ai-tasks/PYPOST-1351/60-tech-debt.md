# PYPOST-1351: Technical Debt Analysis

## Shortcuts Taken

No shortcuts or compromises were taken during the implementation of PYPOST-1351.
- Full validation for `bundled_library` was integrated into `McpServerConfiguration` with
  strict type checks and mutual exclusivity validation.
- Complete lifecycle isolation is achieved via `_BundledLibraryAdapter` in `MCPServerRegistry`,
  wrapping `BuiltinCollectionView` without mutating caller construction points or requiring
  `LibraryManagerService`.
- Existing callers of `MCPServerRegistry` and `McpServerSettingsController` were preserved
  without requiring interface changes.

## Code Quality Issues

No major code quality issues or architectural debt were introduced:
- All new and modified code in `pypost/models/settings.py`, `pypost/core/mcp_server_registry.py`,
  and `tests/test_mcp_builtin_startup.py` conforms strictly to PEP 8, maintains line lengths
  <= 100 characters, includes complete type annotations, and passes static analysis (`make lint`,
  `make typecheck`) with zero regressions.
- Adapter encapsulation is cleanly scoped: `_BundledLibraryAdapter` resides privately within
  `pypost.core.mcp_server_registry` and exposes only `get_connection` and `resolve_path`.

## Missing Tests

No missing test coverage. The test suite in `tests/test_mcp_builtin_startup.py` includes 9
focused, end-to-end and unit tests covering:
- Configuration validation (valid configurations, default flags, missing library IDs, invalid
  library IDs, legacy compatibility).
- Live server startup and tool listing via `anyio` and `/mcp` endpoints.
- Dynamic auto-update on shipped collection updates on disk without settings modification.
- Strict isolation from external user library overlays, connection overrides, and environment
  presets.
- View membership diagnostics (`"missing built-in collection"`) when collection paths are not in
  the curated catalog.
- Backward compatibility for workspace servers and custom library servers.
- Headless `DaemonRuntime` startup without requiring `LibraryManagerService`.
- Injected registry usage in `McpServerSettingsController`.
- Observability verification with `caplog` across DEBUG, INFO, WARNING and status diagnostics.
- All test functions declare explicit timeouts via module-level
  `pytestmark = pytest.mark.timeout(30)`.

## Performance Concerns

Minimal overhead:
- Resolution of bundled library paths and curated entries occurs in-memory via
  `BuiltinCollectionView`.
- If the catalog of curated entries grows substantially in future releases, entries listing or view
  membership checking could be memoized, though current measurement shows sub-millisecond lookup
  and no measurable latency during server start/stop.

## Follow-up Tasks

### Pre-existing Test Failures (NON-BLOCKER)

Pre-existing test failures identified in the repository baseline (documented as non-blockers):
- `NON-BLOCKER — pre-existing`: PYPOST-1358 (native UI environment-list teardown crash)
  - Failure in UI test environment teardown lifecycle on specific Qt runner environments.
- `NON-BLOCKER — pre-existing`: PYPOST-1359 (dev-lock check stale with CI-pinned uv)
  - Discrepancy between pinned tool versions in CI and dev-lock file generation.
- `NON-BLOCKER — pre-existing`: PYPOST-1360 (install-smoke timeout on clean base)
  - Package installation smoke test exceeds timeout threshold under clean container initialization.

### Planned Next Steps (Upcoming Sprint Stories)

The following planned sprint stories build upon this foundation under Epic PYPOST-1335:
- **PYPOST-1352**: Built-in rows in MCP registry lifecycle and controller save
  - Persist and manage built-in rows across controller lifecycle operations without treating them
    as user-defined editable rows.
- **PYPOST-1353**: "Built-in" source with read-only marker in the MCP server dialog
  - Surface the `"Built-in"` source tag in UI dialogs and mark configuration fields read-only.
- **PYPOST-1354**: Editable copy of the paired environment for Built-in MCP servers
  - Provide functionality to clone and customize paired environments for built-in server rows.
- **PYPOST-1355**: Copy for editing a built-in MCP collection
  - Allow users to clone a built-in MCP collection into their workspace for custom editing.
- **PYPOST-1356**: End-to-end test and user documentation for Built-in MCP source
  - Comprehensive end-to-end verification and user documentation covering the built-in MCP server
    feature set.
