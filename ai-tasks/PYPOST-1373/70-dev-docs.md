# PYPOST-1373: Developer Documentation Decisions

Developer documentation decisions and records for [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) (WIZARD-2: Implement VariableSetupWizardDialog and expandable VariableGuidanceCard component under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

## Documentation Updates

1. **Target Document**:
   - [`doc/dev/mcp_server_registry.md`](../../doc/dev/mcp_server_registry.md)

2. **Context & Motivation**:
   - `doc/dev/mcp_server_registry.md` serves as the primary developer reference for MCP server lifecycle, configuration, and library integration.
   - The document previously outlined the planned variable setup wizard under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284).
   - In [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373), the core interactive UI component layer was delivered in `pypost/ui/variable_setup_wizard_dialog.py`.
   - Updating `doc/dev/mcp_server_registry.md` ensures downstream developers implementing [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (wizard integration into `_McpServerEditor`) and [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) (reference collection guidance contracts) have comprehensive API reference, usage patterns, and security semantics readily available.

3. **Key Components Documented**:
   - **`VariableGuidanceCard`**:
     - Visual structure: Name label, type badge, required status indicator (`* Required`), and optional description.
     - Secret masking: Masking via `QLineEdit.EchoMode.Password` by default for secret variables, with an interactive "Show" / "Hide" eye toggle button (`VARIABLE_GUIDANCE_SECRET_TOGGLE`).
     - Expandable instructions: Collapsible guidance panel toggled via "Show Guidance" / "Hide Guidance" (`VARIABLE_GUIDANCE_EXPAND_BUTTON`), rendering rich Markdown/HTML with clickable links (`openExternalLinks=True`). Omitted when `help_text` is empty for compact display.
     - Inline validation: Real-time visual cue (red border) and error text when required inputs are missing, clearing upon user typing.
   - **`VariableSetupWizardDialog`**:
     - Host container: Modal dialog (`VARIABLE_SETUP_WIZARD_DIALOG`) embedding a `QScrollArea` holding variable cards.
     - Instantiation: Constructor signature accepting `variables: list[CollectionVariable]`, `initial_values: Optional[dict[str, Any]]`, and `collection_name: str`.
     - Validation: `accept()` triggers `validate_all()` to block dialog closing when required fields are empty.
     - Value extraction: `get_values()` returning `{var_name: value}` with type coercion, and `get_configured_variables()` partitioning results into `values`, `overrides`, and `secrets`.
     - Automation IDs: Registration of all component IDs in `pypost/ui/widget_ids.py`.

4. **Traceability**:
   - Parent Epic: [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)
   - Preceding Story (Schema): [PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)
   - Current Story (Components): [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)
   - Follow-up Story (Editor Integration): [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)
   - Follow-up Story (Fixtures & Contracts): [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)
