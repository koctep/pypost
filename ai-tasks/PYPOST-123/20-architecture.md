# PYPOST-123: Architecture

## Current behaviour (PYPOST-115)

- `get_variable_value` followed at most one plain `{{inner}}` hop via
  `_resolve_single_level_reference`.
- Two-hop chains stopped at the inner token text.

## Decision

Replace single-hop helper with **bounded multi-hop resolution**:

1. Start from the hovered variable name.
2. Read its value from the variables dict.
3. If the value is exactly a plain `{{inner}}` token, follow to `inner` unless:
   - `inner` is already in the visited set (cycle) → return the unresolved token;
   - depth reached `TOOLTIP_REFERENCE_MAX_DEPTH` (32) → return the unresolved token;
   - `inner` is hidden → return mask.
4. Otherwise return the literal value.

Expression tokens remain on the `TemplateService.render_string` path — unchanged.

## Components

| Component | Change |
|-----------|--------|
| `TOOLTIP_REFERENCE_MAX_DEPTH` | Module constant (32 hops) |
| `VariableHoverHelper._resolve_plain_reference_chain` | Replaces `_resolve_single_level_reference` |
| `VariableHoverHelper.get_variable_value` | Delegates to chain resolver |
| `tests/test_variable_hover.py` | Multi-hop, cycle, depth, hidden regression |
| `doc/dev/ui_mixins.md` | Document multi-hop behaviour |

## Non-goals

- Expanding values that embed placeholders in larger strings.
- Parity with unbounded Jinja recursion at runtime.
