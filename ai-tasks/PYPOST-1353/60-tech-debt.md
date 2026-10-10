# PYPOST-1353: Technical Debt Analysis

## Shortcuts Taken

None. The implementation integrates cleanly into the existing Qt UI components:
- `_McpServerEditor` and `McpServersDialog` add the `"Built-in"` source with read-only
  styling, `(read-only)` markers in collection comboboxes, tooltips, hidden preset/overlay
  controls, and validation blocking when no collection/environment is selected.
- `McpControlsPresenter` passes the `BuiltinCollectionView` from the controller's
  registry view (`controller.registry._builtin_view`) directly into `McpServersDialog`.
- All requirements from `10-requirements.md` and architecture decisions from
  `20-architecture.md` are fulfilled without workarounds or temporary shortcuts.

## Code Quality Issues

None identified.
- Clean separation of presentation and dialog concerns.
- Type annotations across all new methods and parameters.
- PEP 8 compliant, all modified lines strictly within the 100-character line length limit.
- Verified via `make lint` and baseline type checks via `make typecheck`.

## Missing Tests

None.
- Added comprehensive unit and integration tests in `tests/test_mcp_builtin_dialog.py`:
  - `test_builtin_source_populates_combobox_and_sets_tooltips`
  - `test_builtin_source_shows_readonly_marker_and_hides_overlay_preset`
  - `test_builtin_validation_blocks_when_environment_missing`
  - `test_builtin_save_emits_bundled_library_true`
  - `test_overview_table_shows_builtin_readonly_marker`
  - `test_mcp_controls_presenter_passes_builtin_view`
- All tests declare explicit timeout markers (`pytestmark = pytest.mark.timeout(30)`),
  run headlessly via Qt offscreen / fixtures, and pass cleanly.

## Performance Concerns

Negligible.
- Built-in collections are queried from the pre-cached in-memory `BuiltinCollectionView`.
- Populating the dropdown combobox and rendering overview table markers is an O(N)
  in-memory UI operation where N is the small number of shipped built-in collections.

## Follow-up Tasks

### Pre-existing Baseline Failures (NON-BLOCKER — pre-existing)

- **PYPOST-1358**: Native UI environment-list teardown crash during comprehensive suite teardown
  (`NON-BLOCKER — pre-existing`).
- **PYPOST-1359**: Dependency check `make check-lock` fails due to stale pinned uv executable in CI
  environment (`NON-BLOCKER — pre-existing`).
- **PYPOST-1360**: Clean base install smoke test timeout on target platform
  (`NON-BLOCKER — pre-existing`).

### Planned Sprint Stories

- **PYPOST-1354**: Editable copy of the paired environment for Built-in MCP servers (allows cloning
  paired built-in environments to create user-customized variants).
- **PYPOST-1355**: Copy for editing a built-in MCP collection (allows duplicating built-in
  read-only collections into user collections).
- **PYPOST-1356**: End-to-end test and user documentation for Built-in MCP source.
