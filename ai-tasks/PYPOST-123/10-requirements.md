# PYPOST-123: Recursive variable resolution in tooltips

## Goals

Environment variables can form indirection chains (e.g. `A = {{B}}`, `B = {{C}}`, `C = prod`).
After PYPOST-115, tooltips followed only one hop. Users hovering deep chains still saw
intermediate `{{name}}` tokens instead of the final value, unlike runtime rendering.

This task completes the PYPOST-13 follow-up: expand hover resolution to follow plain
variable chains safely.

## User Stories

- As a pypost user, when I hover a variable that references others, I want to see the
  final resolved value so I can confirm what will be sent.
- As a pypost user, I expect cyclic or excessively deep chains to stop gracefully without
  hanging the UI.
- As a pypost user, I still expect function-style placeholders and hidden-key masking to
  behave as before.

## Definition of Done

| ID | Criterion |
|----|-----------|
| AC-1 | Hovering `{{A}}` when `A→B→C→value` shows `value` |
| AC-2 | Cyclic chains (e.g. `A={{B}}`, `B={{A}}`) stop and show the unresolved reference |
| AC-3 | Depth is bounded to prevent unbounded traversal |
| AC-4 | Hidden-key masking applies at every hop |
| AC-5 | Function-expression tooltips unchanged |
| AC-6 | Unit tests cover multi-hop, cycle, depth limit, and hidden inner |
| AC-7 | Developer docs updated |

## Scope

**In scope:** Multi-hop plain `{{name}}` lookup in `VariableHoverHelper`; cycle detection;
depth bound; tests; dev docs.

**Out of scope:** Resolving placeholders embedded in larger strings (e.g. `prefix {{b}}`);
changes to runtime `TemplateService` / Jinja rendering; tooltip styling.

## Constraints

- Reuse tokenizer helpers (`is_plain_variable_token`, `extract_plain_variable_name`).
- No new metrics for this behavioural extension.

## Programming language

Python
