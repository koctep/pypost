# PYPOST-115: Single-level variable resolution in tooltips

## Goals

Environment variables can reference other variables (e.g. `VAR_A = {{VAR_B}}`). When a user
hovers over `{{VAR_A}}` in a request field, the tooltip should show the resolved value of
`VAR_B`, not the literal `{{VAR_B}}` string. Full recursive resolution belongs to runtime
template rendering; tooltips need at most one follow-up hop for plain variable indirection.

## User Stories

- As a pypost user, when I hover a variable whose value is another variable reference, I want
  to see the referenced variable's value so I can confirm what will be sent.
- As a pypost user, I still expect function-style placeholders (e.g. `{{urlencode(db)}}`) to
  resolve through the existing expression path unchanged.

## Definition of Done

| ID | Criterion |
|----|-----------|
| AC-1 | Hovering `{{VAR_A}}` when `VAR_A = {{VAR_B}}` and `VAR_B` is defined shows `VAR_B`'s value |
| AC-2 | Resolution stops after one hop (no multi-level recursion in tooltips) |
| AC-3 | Hidden-key masking applies to the inner referenced variable |
| AC-4 | Function-expression tooltips behave as before |
| AC-5 | Unit tests cover chain, stop-at-one-level, and hidden inner variable |

## Scope

**In scope:** One-level plain `{{name}}` lookup in `VariableHoverHelper`; tests; dev docs.

**Out of scope:** Multi-level recursive chains, changes to `TemplateEngine` runtime rendering,
tooltip styling.

## Constraints

- Reuse existing tokenizer helpers (`is_plain_variable_token`, `extract_plain_variable_name`).
- No new metrics for this small behavioural fix.

## Programming language

Python
