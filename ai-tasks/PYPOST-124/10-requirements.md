# PYPOST-124: Variable highlighting in JsonHighlighter

## Context

- **Jira:** PYPOST-124
- **Origin:** Follow-up from [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13)
  (`40-tech-debt.md`): variable tooltips were implemented; syntax highlighting for
  `{{...}}` placeholders in the JSON body editor was deferred.
- **Type:** Debt (Sprint 442 — Test infra & coverage)

## Problem statement

Request body and response JSON editors use `JsonHighlighter` for keys, strings, numbers, and
literals. Template placeholders such as `{{baseUrl}}` or `{{urlencode(db)}}` inside JSON
string values appear in the same green as ordinary strings, making variables harder to spot
when composing requests with environment variables.

## Goals

- Visually distinguish `{{...}}` template placeholders in JSON body/response editors.
- Align placeholder detection with the canonical tokenizer used by hover and template
  resolution (PYPOST-536).
- Preserve existing JSON element colors for non-placeholder content.

## Scope

### In scope

- Highlight full `{{...}}` tokens (plain variables and function expressions) in
  `JsonHighlighter`.
- Unit tests asserting placeholder foreground color via `QTextLayout` format ranges.
- Developer notes for the highlighter color scheme and rule order.

### Out of scope

- Variable hover tooltips (already implemented via `VariableHoverMixin`).
- Highlighting in URL bar, headers, or params tables.
- Dark-theme-aware colors ([PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)).
- Resolving or validating variables at highlight time.

## User stories

- As a **user**, I want `{{variable}}` placeholders in the JSON request body to stand out
  from normal string values so I can verify templates before sending.
- As a **user**, I want function expressions like `{{urlencode(db)}}` highlighted the same
  way as plain variables for consistent visual scanning.

## Functional requirements

1. **FR-1:** `JsonHighlighter` applies a distinct format to each `{{...}}` match in a line.
2. **FR-2:** Placeholder detection uses `TEMPLATE_PLACEHOLDER_PATTERN` (same as core/hover).
3. **FR-3:** Variable highlighting runs after string/key rules so it overrides green/purple
   where placeholders appear inside quoted JSON strings.
4. **FR-4:** Existing keyword, number, string, and key highlighting behavior is unchanged
   for text without placeholders.

## Acceptance criteria

1. **AC-1:** `{"url": "{{baseUrl}}/api"}` — characters inside `{{baseUrl}}` use the
   variable color (not green).
2. **AC-2:** `{"path": "{{urlencode(db)}}"}` — function expression placeholder is
   highlighted.
3. **AC-3:** `{"enabled": true}` — `true` remains darkblue; keys remain purple; numbers
   remain blue (existing tests pass).
4. **AC-4:** New tests in `tests/test_json_highlighter.py` cover AC-1 and AC-2.

## Risks and assumptions

| Type | Description |
| ---- | ----------- |
| **Assumption** | Placeholders appear primarily inside JSON string values; invalid JSON with bare `{{x}}` may still be highlighted. |
| **Assumption** | `darkorange` + bold is readable on the default light editor background. |
| **Risk** | Low: regex false-positives inside string literals match hover behavior (known PYPOST-113 scope). |

## Programming language

**Python** — PySide6 `QSyntaxHighlighter`, shared `TEMPLATE_PLACEHOLDER_PATTERN`.
