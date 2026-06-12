# PYPOST-113: Centralize plain variable placeholder detection

## Goals

Variable hover used a local regex for plain `{{name}}` tokens while render and validation
already share `template_expression_tokenizer`. Centralizing the plain-variable pattern
reduces drift risk and documents the two-pattern model (full placeholder vs plain name).

## User Stories

- As a pypost user, I want hover tooltips on plain variables to behave as before, so
  editing with `{{host}}` placeholders stays predictable.
- As a maintainer, I want one documented helper for plain-variable detection, so UI and
  core paths do not diverge silently.

## Definition of Done

- Plain `{{name}}` regex lives in `template_expression_tokenizer` with helper functions.
- `VariableHoverHelper` uses the shared export (no local compile).
- Tests cover plain vs function tokens and alias parity with hover helper.
- Dev docs describe `PLAIN_VARIABLE_PATTERN` and its relationship to the full tokenizer.

## Task Description

**Problem:** `VariableHoverHelper` duplicated `\{\{([a-zA-Z0-9_]+)\}\}` inline (from
PYPOST-13 tech debt). Full `{{ ... }}` scanning was unified in PYPOST-536; plain-variable
detection remained separate.

**Scope:** Export shared pattern + helpers; wire hover; document; add tests.

**Out of scope:** Changing identifier rules, recursive tooltip resolution, or replacing
regex with Jinja AST parsing.

**Constraints:**

- Implementation language: **Python**.
- Preserve existing hover behavior for plain and function placeholders.
- Minimal diff — no new expression functions or UI changes.

## Q&A

- **Q:** Why keep two patterns instead of one?
  **A:** Plain `{{name}}` fast path avoids `TemplateService` for simple lookups; full
  `TEMPLATE_PLACEHOLDER_PATTERN` handles function calls and whitespace.
