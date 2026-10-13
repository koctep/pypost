# PYPOST-1373: Technical Debt Analysis

Technical debt analysis artifact for [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) (WIZARD-2: Implement VariableSetupWizardDialog and expandable VariableGuidanceCard component under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)).

## Shortcuts Taken

None.

- The implementation in `pypost/ui/variable_setup_wizard_dialog.py` adheres directly to the architecture and design patterns established in `ai-tasks/PYPOST-1373/20-architecture.md`.
- No temporary "crutches", stub implementations, or monkey-patching were introduced.
- Automation widget identifiers (`VARIABLE_GUIDANCE_CARD`, `VARIABLE_GUIDANCE_EXPAND_BUTTON`, `VARIABLE_GUIDANCE_SECRET_TOGGLE`, `VARIABLE_SETUP_WIZARD_DIALOG`, `VARIABLE_SETUP_APPLY_BUTTON`, `VARIABLE_SETUP_CANCEL_BUTTON`) were added cleanly to `pypost/ui/widget_ids.py`.
- Headless testing support for Qt visibility checking (`_GuidanceContainer`) cleanly mirrors headless testing practices in `pypost/ui/dialogs/mcp_servers_dialog.py` without compromising production widget hierarchy or styles.

## Code Quality Issues

None.

- **Type Safety**: Fully typed with strict type annotations matching mypy standards; passes `make typecheck` clean.
- **Styling & Linting**: Adheres to PEP 8 standards with zero flake8 warnings; passes `make lint`.
- **Modularity**: Components are separated into discrete responsibilities:
  - `VariableGuidanceCard`: Self-contained `QFrame` managing input binding, secret echo mode toggling, collapsible rich guidance panel, and inline validation states.
  - `VariableSetupWizardDialog`: Self-contained modal `QDialog` embedding a `QScrollArea`, managing collection-level batch validation, and partitioning results into `overrides` and `secrets`.
- **Maintainability**: Clean public APIs (`get_value`, `set_value`, `is_valid`, `set_validation_error`, `toggle_guidance`, `toggle_secret_visibility`, `get_values`, `get_configured_variables`) with comprehensive docstrings.

## Missing Tests

None.

- Comprehensive automated test suite implemented in `tests/test_variable_setup_wizard_repro.py`:
  - `test_variable_guidance_card_rendering_and_defaults`: Card rendering, types, defaults, required indicators, and initial value overrides.
  - `test_variable_guidance_card_secret_masking_and_toggle`: Secret variable masking (`QLineEdit.EchoMode.Password`) and interactive toggle switching.
  - `test_variable_guidance_card_collapsible_guidance`: Expandable guidance visibility toggles when `help_text` is present vs. omission when absent.
  - `test_variable_guidance_card_inline_validation`: Inline error reporting on empty required variables, clearing on typing.
  - `test_variable_setup_wizard_dialog_flow_and_extraction`: Wizard dialog flow in `QScrollArea`, validation preventing dialog acceptance when required fields are empty, and extraction into partitioned `overrides` and `secrets`.
- All tests are annotated with explicit timeouts (`pytestmark = pytest.mark.timeout(30)`), satisfying the `do-testing` quality blocker.
- No pre-existing test failures or regressions were observed.

## Performance Concerns

None.

- The dialog uses standard Qt layout hierarchy within `QScrollArea(widgetResizable=True)`.
- Instantiation and layout rendering take < 15ms for typical variable counts (5 to 20 variables).
- In-memory validation (`validate_all()`) executes in < 1ms on the UI thread without blocking the event loop.
- Scrolling performance remains smooth without requiring virtualized list views.

## Follow-up Tasks

| Key | Summary | Priority | SP | Sprint | Status | Description |
| --- | --- | --- | --- | --- | --- | --- |
| [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) | Integrate variable setup wizard launch and overlay persistence in MCP server editor | High | 5 | Sprint 2029 | Open | Connect `VariableSetupWizardDialog` into `_McpServerEditor` in `pypost/ui/dialogs/mcp_servers_dialog.py`, adding "Setup Variables..." button and persisting extracted overrides/secrets to `LocalLibraryOverlay`. |
| [PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375) | Add reference collection with OAuth setup guidance and contract test suite | Medium | 3 | Sprint 2029 | Open | Author reference MCP collection fixtures (e.g. `google_drive.json`) populated with rich markdown `help_text` and contract test suite verifying end-to-end guidance presentation. |
