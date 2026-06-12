# PYPOST-115: Technical Debt

## Status: SAFE TO CLOSE

## Resolved

- **One-level tooltip vars** (this task): Plain `{{name}}` hover now follows one `{{inner}}`
  reference in the variable value.

## Remaining (non-blockers)

- **Multi-level chains** ([PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13) follow-up):
  Tooltips intentionally stop after one hop; runtime `TemplateService` may resolve deeper.
  Defer unless users request tooltip parity with full rendering.
- **Values with embedded placeholders**: A value like `https://{{host}}/api` is not expanded
  on hover; only values that are exactly `{{name}}` chain.

## Missing tests

None blocking — chain, depth limit, and hidden inner covered in `test_variable_hover.py`.
