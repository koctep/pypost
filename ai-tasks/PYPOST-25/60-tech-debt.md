# PYPOST-25: Technical Debt Analysis


## Shortcuts Taken

- No architectural shortcuts were introduced in the save action relocation itself.
  — [PYPOST-182](https://pypost.atlassian.net/browse/PYPOST-182)
- **Limited validation (no suite)** ([PYPOST-183](https://pypost.atlassian.net/browse/PYPOST-183)):
  Validation was syntax-only with manual behavior assumptions (`unittest` discovers zero tests;
  `pytest` unavailable here).

## Code Quality Issues

- **Unstructured save logging** ([PYPOST-184](https://pypost.atlassian.net/browse/PYPOST-184)):
  `RequestWidget.on_save` uses key/value text instead of a shared structured logging formatter.
- **RequestWidget: UI plus wiring** ([PYPOST-185](https://pypost.atlassian.net/browse/PYPOST-185)):
  UI composition and interaction handling stay together; a later refactor could separate action
  wiring from layout for easier testing.

## Missing Tests

- No automated GUI tests for the new `Actions -> Save` path.
  — [PYPOST-186](https://pypost.atlassian.net/browse/PYPOST-186)
- No automated test asserting `Ctrl+S` and menu save both trigger identical save workflow.
  — [PYPOST-187](https://pypost.atlassian.net/browse/PYPOST-187)
- No automated metric assertion for `gui_save_actions_total{source=...}` labels.
  — [PYPOST-188](https://pypost.atlassian.net/browse/PYPOST-188)

## Performance Concerns

- No material performance risk identified for this change.
  — [PYPOST-189](https://pypost.atlassian.net/browse/PYPOST-189)
- Added metric counter increment and single `INFO` log per save action are negligible overhead.
  — [PYPOST-190](https://pypost.atlassian.net/browse/PYPOST-190)

## Follow-up Tasks

- **Qt UI tests for Save** ([PYPOST-191](https://pypost.atlassian.net/browse/PYPOST-191)):
  - `Actions` menu visibility and `Save` action availability.
  - Save trigger parity between menu action and `Ctrl+S`.
- Add integration test for metrics endpoint verifying `gui_save_actions_total` increments by source.
  — [PYPOST-192](https://pypost.atlassian.net/browse/PYPOST-192)
- Standardize logging format for UI modules to a shared structured logger configuration.
  — [PYPOST-193](https://pypost.atlassian.net/browse/PYPOST-193)
