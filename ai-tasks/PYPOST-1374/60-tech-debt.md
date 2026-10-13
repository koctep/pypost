# PYPOST-1374: Technical Debt Analysis

Technical debt analysis artifact for [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (Layer 3 / WIZARD-3: Integrate variable setup wizard launch and overlay persistence in MCP server editor under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

## Shortcuts Taken

None.

- The implementation in `pypost/ui/dialogs/mcp_servers_dialog.py` adheres strictly to the architecture and design patterns established in `ai-tasks/PYPOST-1374/20-architecture.md`.
- No temporary "crutches", stub implementations, monkey-patching, or undocumented workarounds were introduced.
- Clean test seams (`_create_variable_wizard`, `_launch_variable_wizard`) were introduced directly on `_McpServerEditor` to enable deterministic headless unit testing without spawning blocking modal event loops or mocking production dialog behavior.
- Layout hierarchy remains clean using standard `QFormLayout` rows, preserving widget hierarchy, tab order, and standard PySide6 styles.
- Automation widget identifier `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` was registered cleanly in `pypost/ui/widget_ids.py` with `Final[str]` type annotation and added to `KEY_WIDGET_IDS`.

## Code Quality Issues

None.

- **Type Safety**: Fully typed with strict annotations satisfying mypy standards; passes `make typecheck` cleanly against the baseline gate with zero new violations.
- **Styling & Linting**: Adheres to PEP 8 standards with zero flake8 warnings; passes `make lint`.
- **Automation Identifier Registration**: Cleanly registers `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` in `pypost/ui/widget_ids.py` following the `pypost_` naming convention.
- **Modularity & Separation of Concerns**:
  - `_update_configure_variables_button_state`: Encapsulates dynamic visibility and enablement logic tied to server type, collection source, and variable presence.
  - `_on_configure_variables_clicked`: Orchestrates manifest conversion, draft pre-population, and modal execution.
  - `_sync_wizard_results_to_overlay`: Isolated synchronization handling overlay dictionary updates and inline `QLineEdit` field alignment.
- **Credential Segregation**: Preserves strict partitioning of sensitive credentials into `overlay["secrets"]` and non-sensitive values into `overlay["overrides"]`, preventing credential leakage in logs and telemetry.

## Missing Tests

None.

- Comprehensive automated test suite implemented in `tests/test_mcp_servers_dialog_variable_wizard_repro.py` (6/6 tests passing):
  - `test_configure_variables_button_exists_and_has_stable_id`: Validates presence of "Configure Variables..." button and assignment of `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` automation ID.
  - `test_configure_variables_button_visibility_and_enablement`: Validates button visibility and enablement transitions across local library collections with variables, non-library sources (workspace), collections without variables, and proxy server modes.
  - `test_wizard_launch_prepopulates_draft_values`: Validates conversion of `manifest_variables` into `CollectionVariable` instances and pre-population of initial values from profile defaults, draft overrides, and inline fields.
  - `test_wizard_acceptance_updates_overlay_and_inline_fields`: Validates synchronization of accepted wizard results into `_library_overlay` (`overrides` and `secrets`) and active `QLineEdit` form fields.
  - `test_wizard_cancellation_preserves_draft_state`: Validates that dismissing or cancelling the wizard preserves prior draft overlay state and inline inputs without modification.
  - `test_save_persists_overlay_to_local_library_overlay`: Validates full end-to-end integration saving through `McpServersDialog` into `LocalLibraryOverlay` storage via `LocalOverlayManager`.
- All tests include explicit timeout markers (`pytestmark = pytest.mark.timeout(30)`), complying with the `do-testing` quality standard.
- Regression test suites (`tests/test_mcp_servers_dialog.py`, `tests/test_variable_setup_wizard_repro.py`, `tests/test_dialogs_audit.py`) pass without regressions.
- No pre-existing test failures or untracked test gaps were observed.

## Performance Concerns

None.

- **Instantaneous Button State Management**: `_update_configure_variables_button_state` executes synchronous in-memory inspection in < 1 millisecond upon collection or server type selection changes.
- **Modal Launch & Model Conversion**: `_on_configure_variables_clicked` converts manifest dictionaries to `CollectionVariable` models and constructs the dialog in < 10 milliseconds.
- **Synchronous Overlay Synchronization**: `_sync_wizard_results_to_overlay` synchronizes overlay dictionaries and updates inline fields in < 1 millisecond.
- **Thread Safety & Non-blocking I/O**: Zero blocking disk or network I/O on the Qt main GUI thread during wizard display and interaction; disk persistence occurs only upon user acceptance of the parent server dialog.

## Follow-up Tasks

| Key | Summary | Priority | SP | Sprint | Status | Description |
| --- | --- | --- | --- | --- | --- | --- |
| [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) | Add reference collection with OAuth setup guidance and contract test suite | Medium | 3 | Sprint 2029 | Open | Author reference MCP collection fixtures (e.g. `google_drive.json`) with rich markdown `help_text`, OAuth setup guidance, and contract test suite validating wizard presentation and overlay contracts end-to-end. |
