# PYPOST-31: Technical Debt Analysis


## Shortcuts Taken

- No architectural shortcuts were introduced in the save action relocation itself.
  — [PYPOST-281](https://pypost.atlassian.net/browse/PYPOST-281)
- **Limited validation (no suite)** ([PYPOST-282](https://pypost.atlassian.net/browse/PYPOST-282)):
  Validation was syntax-only with manual behavior assumptions (`unittest` discovers zero tests;
  `pytest` unavailable here).

## Code Quality Issues

- **Unstructured save logging** ([PYPOST-283](https://pypost.atlassian.net/browse/PYPOST-283)):
  `RequestWidget.on_save` uses key/value text instead of a shared structured logging formatter.
- **RequestWidget: UI plus wiring** ([PYPOST-284](https://pypost.atlassian.net/browse/PYPOST-284)):
  UI composition and interaction handling stay together; a later refactor could separate action
  wiring from layout for easier testing.

## Missing Tests

- No automated GUI tests for the new `Actions -> Save` path.
  — [PYPOST-285](https://pypost.atlassian.net/browse/PYPOST-285)
- No automated test asserting `Ctrl+S` and menu save both trigger identical save workflow.
  — [PYPOST-286](https://pypost.atlassian.net/browse/PYPOST-286)
- No automated metric assertion for `gui_save_actions_total{source=...}` labels.
  — [PYPOST-287](https://pypost.atlassian.net/browse/PYPOST-287)

## Performance Concerns

- No material performance risk identified for this change.
  — [PYPOST-288](https://pypost.atlassian.net/browse/PYPOST-288)
- Added metric counter increment and single `INFO` log per save action are negligible overhead.
  — [PYPOST-289](https://pypost.atlassian.net/browse/PYPOST-289)

## Follow-up Tasks

- **Qt UI tests for Save** ([PYPOST-290](https://pypost.atlassian.net/browse/PYPOST-290)):
  - `Actions` menu visibility and `Save` action availability.
  - Save trigger parity between menu action and `Ctrl+S`.
- Add integration test for metrics endpoint verifying `gui_save_actions_total` increments by source.
  — [PYPOST-291](https://pypost.atlassian.net/browse/PYPOST-291)
- Standardize logging format for UI modules to a shared structured logger configuration.
  — [PYPOST-292](https://pypost.atlassian.net/browse/PYPOST-292)
