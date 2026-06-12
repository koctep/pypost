# PYPOST-115: Architecture

## Current behaviour

- Plain `{{name}}` tokens in `VariableHoverHelper.resolve_text` call `get_variable_value`,
  which returns the raw dict value.
- Function tokens (`{{urlencode(db)}}`, etc.) already delegate to `TemplateService.render_string`
  with `render_path="hover"`.

## Decision

Add **single-level chained lookup** only in the plain-variable path:

1. `get_variable_value` reads the raw value from the variables dict.
2. If the raw value is exactly a plain `{{inner}}` token (no inner whitespace), resolve
   `inner` once from the same dict.
3. Otherwise return the raw value unchanged.

Expression tokens are unchanged — they already use `TemplateService`.

## Components

| Component | Change |
|-----------|--------|
| `VariableHoverHelper.get_variable_value` | Orchestrate lookup + one-hop follow |
| `VariableHoverHelper._resolve_single_level_reference` | New helper for the hop |
| `tests/test_variable_hover.py` | Chain, depth limit, hidden inner |

## Non-goals

- Recursive resolution (depth > 1).
- Resolving values that embed placeholders in larger strings (e.g. `prefix {{b}}`).
