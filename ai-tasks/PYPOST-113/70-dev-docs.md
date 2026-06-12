# PYPOST-113: Dev Docs

## Updates

- `doc/dev/template_expression_functions.md`:
  - Document `PLAIN_VARIABLE_PATTERN`, `is_plain_variable_token`,
    `extract_plain_variable_name`.
  - Mark PYPOST-113 plain-pattern centralization as done in follow-ups table.

## Rationale

Developers extending placeholder syntax now have a single module for both full-token and
plain-variable regex contracts; hover imports the shared exports instead of duplicating
patterns locally.
