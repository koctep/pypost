# PYPOST-116: Technical Debt

## Status: SAFE TO CLOSE

## Resolved

- **Direct variable injection** (this task): Documented intentional push-based
  `set_variables` pattern with presenter-level signal boundary. Entry-point docstrings and
  propagation tests added.

## Remaining (non-blockers)

- **Global variable context / DI** ([PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128)):
  Manual fan-out through `RequestWidget.set_variables` remains; acceptable until UI depth
  warrants a shared observer or property object.
- **Per-widget reactive updates**: Not needed for hover-only reads; revisit only if widgets
  must react to env changes without user interaction (e.g. live highlighted values).

## Missing tests

None blocking — propagation contract covered in `test_tabs_presenter.py`; hover coverage
unchanged in `test_variable_hover.py`.
