# PYPOST-28: Technical Debt Analysis


## Shortcuts Taken

- No architectural shortcuts were introduced in the save action relocation itself.
  — [PYPOST-237](https://pypost.atlassian.net/browse/PYPOST-237)
- **Limited validation (no suite)** ([PYPOST-238](https://pypost.atlassian.net/browse/PYPOST-238)):
  Validation was syntax-only with manual behavior assumptions (`unittest` discovers zero tests;
  `pytest` unavailable here).

## Code Quality Issues

- **Unstructured save logging** ([PYPOST-239](https://pypost.atlassian.net/browse/PYPOST-239)):
  `RequestWidget.on_save` uses key/value text instead of a shared structured logging formatter.
- **RequestWidget: UI plus wiring** ([PYPOST-240](https://pypost.atlassian.net/browse/PYPOST-240)):
  UI composition and interaction handling stay together; a later refactor could separate action
  wiring from layout for easier testing.

## Missing Tests

- No automated GUI tests for the new `Actions -> Save` path.
  — [PYPOST-241](https://pypost.atlassian.net/browse/PYPOST-241)
- No automated test asserting `Ctrl+S` and menu save both trigger identical save workflow.
  — [PYPOST-242](https://pypost.atlassian.net/browse/PYPOST-242)
- No automated metric assertion for `gui_save_actions_total{source=...}` labels.
  — [PYPOST-243](https://pypost.atlassian.net/browse/PYPOST-243)

## Performance Concerns

- No material performance risk identified for this change.
  — [PYPOST-244](https://pypost.atlassian.net/browse/PYPOST-244)
- Added metric counter increment and single `INFO` log per save action are negligible overhead.
  — [PYPOST-245](https://pypost.atlassian.net/browse/PYPOST-245)

## Follow-up Tasks

- **Qt UI tests for Save** ([PYPOST-246](https://pypost.atlassian.net/browse/PYPOST-246)):
  - `Actions` menu visibility and `Save` action availability.
  - Save trigger parity between menu action and `Ctrl+S`.
- Add integration test for metrics endpoint verifying `gui_save_actions_total` increments by source.
  — [PYPOST-247](https://pypost.atlassian.net/browse/PYPOST-247)
- Standardize logging format for UI modules to a shared structured logger configuration.
  — [PYPOST-248](https://pypost.atlassian.net/browse/PYPOST-248)
