# PYPOST-536: Unify UI hover expression pattern with core template tokenizer

## Goals

Hover preview for `{{ ... }}` placeholders must use the same placeholder detection contract
as render and validation so tooltip semantics cannot drift from core template processing.

## User Stories

- As a pypost user, I want hover tooltips on function placeholders to match runtime
  resolution, including nested calls, so preview stays trustworthy.
- As a maintainer, I want one canonical regex for `{{ ... }}` detection, so UI and core paths
  evolve together after PYPOST-460.

## Definition of Done

- Decision recorded: reuse core tokenizer pattern for hover (not a divergent UI regex).
- `VariableHoverHelper` uses the shared pattern from `template_expression_tokenizer`.
- Existing hover tests pass; parity test covers tokenizer alignment.
- No user-visible regression in hover tooltips for function placeholders.

## Task Description

**Problem:** `VariableHoverHelper.EXPRESSION_PATTERN` duplicated placeholder detection with a
different inner capture (`[^{}]+?` vs `.*?`), risking drift from validation.

**Scope:** Export shared compiled pattern; wire hover helper to it; document in dev docs.

**Out of scope:** Changing `VARIABLE_PATTERN` (plain `{{name}}` only); new expression functions.

**Constraints:**

- Implementation language: **Python**.
- Parity contract: `\{\{\s*(.*?)\s*\}\}` from PYPOST-460.
- Hover still returns full tokens with braces for tooltip display.

## Main entities (business view)

- **Template placeholder** — `{{ ... }}` segment in editor text.
- **Hover preview** — tooltip value shown when cursor is over a placeholder.
- **Core tokenizer** — canonical inner-expression extractor for render/validation.

## Q&A

- **Q:** Why keep `EXPRESSION_PATTERN` on `VariableHoverHelper`?
  **A:** Backward-compatible alias to the shared pattern; callers need full-match iteration.
