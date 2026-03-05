# PYPOST-9: Technical Debt Analysis

## Shortcuts Taken

- No architectural shortcuts were introduced in the save action relocation itself.
- Validation was limited to syntax checks and manual behavior assumptions due to absent
  runnable test suite in current environment (`unittest` discovers zero tests; `pytest`
  is unavailable here).

## Code Quality Issues

- Observability logging in `RequestWidget.on_save` uses key/value text structure instead of a
  dedicated structured logging formatter shared across the project.
- `RequestWidget` continues to contain both UI composition and interaction handling. Future refactor
  could separate action wiring from widget layout for easier testing.

## Missing Tests

- No automated GUI tests for the new `Actions -> Save` path.
- No automated test asserting `Ctrl+S` and menu save both trigger identical save workflow.
- No automated metric assertion for `gui_save_actions_total{source=...}` labels.

## Performance Concerns

- No material performance risk identified for this change.
- Added metric counter increment and single `INFO` log per save action are negligible overhead.

## Follow-up Tasks

- Add UI interaction tests (Qt-level) for:
  - `Actions` menu visibility and `Save` action availability.
  - Save trigger parity between menu action and `Ctrl+S`.
- Add integration test for metrics endpoint verifying `gui_save_actions_total` increments by source.
- Standardize logging format for UI modules to a shared structured logger configuration.
