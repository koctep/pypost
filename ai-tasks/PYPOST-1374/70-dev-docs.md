# PYPOST-1374: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (WIZARD-3: Integrate variable setup wizard launch and overlay persistence in MCP server editor under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

## Documentation Updates

1. **Target Document**:
   - [`doc/dev/mcp_server_registry.md`](../../doc/dev/mcp_server_registry.md)

2. **Context & Motivation**:
   - `doc/dev/mcp_server_registry.md` serves as the primary developer reference for MCP server lifecycle, configuration, runtime management, and library integration.
   - Story [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) previously documented the standalone `VariableGuidanceCard` and `VariableSetupWizardDialog` UI components.
   - In [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374), the wizard was integrated into `_McpServerEditor` (`pypost/ui/dialogs/mcp_servers_dialog.py`), enabling users to launch the interactive guidance wizard, review OAuth instructions, pre-populate existing configuration values, and synchronize accepted changes to the draft `LocalLibraryOverlay` and inline editor inputs.
   - Updating `doc/dev/mcp_server_registry.md` ensures engineers maintaining and extending the MCP subsystem or developing downstream fixtures in [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) have clear architectural and operational documentation.

3. **Key Integration Aspects Documented**:
   - **Configure Variables Action Button**:
     - Widget component `_ConfigureVariablesButton` with stable test automation ID `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` (`pypost_mcp_server_configure_variables_button`), registered in `pypost/ui/widget_ids.py` and included in `KEY_WIDGET_IDS`.
     - Layout positioning directly beneath library variable inputs.
   - **Visibility & Enablement Dynamic Binding**:
     - Managed centrally via `_update_configure_variables_button_state()`.
     - Dynamically bound to `is_local and is_library and has_variables` (visible and enabled if and only if the server is local, collection source is library, and the chosen collection defines manifest variables).
     - Bound reactively to server type changes, collection source switching, and library collection selection updates.
   - **Pre-population Hierarchy**:
     - Multi-tier value resolution inside `_on_configure_variables_clicked()`: active profile defaults -> manifest default values -> draft overlay overrides -> draft overlay secrets -> uncommitted inline field inputs.
   - **Modal Acceptance & Result Synchronization**:
     - Acceptance extracts partitioned variable sets via `dialog.get_configured_variables()` (`values`, `overrides`, and `secrets`).
     - `_sync_wizard_results_to_overlay(result)` merges overrides and secrets into `_library_overlay` and updates inline `_library_variable_fields` text while maintaining secret password masking.
     - Operational audit logging via `mcp_server_editor_wizard_applied` recording sanitized counts only.
   - **Cancellation Semantics**:
     - Wizard rejection preserves existing draft overlay state and inline form values without modification.
   - **Overlay Persistence Pipeline**:
     - `library_handoff()` validates candidate overlay state through `LibraryRuntimeResolver.prepare_environment(...)` and packages it into handoff metadata for `McpServerSettingsController.save_library_server(...)` persisting to `~/.pypost/overlays/{library_id}.json`.
   - **Headless Unit Test Seams**:
     - Factory seam `_create_variable_wizard(variables, initial_values, collection_name)` and modal execution seam `_launch_variable_wizard(dialog)` facilitating deterministic headless unit testing without blocking Qt GUI threads.

4. **Traceability**:
   - Parent Epic: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
   - Preceding Story (Schema): [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)
   - Preceding Story (Components): [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)
   - Current Story (Editor Integration): [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)
   - Follow-up Story (Fixtures & Contracts): [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)
