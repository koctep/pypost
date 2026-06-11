# PYPOST-460: Shared tokenization for template expression validation and counting

## Goals

Template fields with function-style placeholders are scanned more than once during
rendering. This task reduces duplicate work and centralizes placeholder detection so
future expression features evolve in one place without changing user-visible behavior.

## User Stories

- As a pypost user, I want template rendering to behave exactly as before, so existing
  requests and previews stay stable.
- As a maintainer, I want one canonical way to extract `{{ ... }}` inner expressions, so
  counting and validation cannot drift apart.
- As a maintainer, I want the render path to tokenize once per non-empty template, so
  large templates do not pay redundant linear scans.

## Definition of Done

- A shared tokenizer replaces duplicate `re.findall` usage in the render and validation
  paths.
- `token_count` logs and metrics match pre-change behavior for representative inputs.
- Existing template expression tests pass without semantic changes.
- Jira scope for `PYPOST-460` is fully covered and traceable.

## Task Description

**Problem:** Expression scanning runs `re.findall` in both `TemplateService.render_string`
and `FunctionExpressionResolver.validate_content`.

**Scope:** Introduce a shared tokenization utility; wire render counting and resolver
validation through it; use a single tokenization pass on the render path.

**Out of scope:** New expression functions, nested-call policy changes, UI hover regex
unification.

**Constraints and assumptions:**

- Implementation language: **Python**.
- Parity contract: regex semantics `\{\{\s*(.*?)\s*\}\}` unchanged.
- `FunctionExpressionResolver.validate_content` remains the public validation entry for
  string input.

## Main entities (business view)

- **Template placeholder** — `{{ ... }}` segment in user-provided text.
- **Inner expression** — text between delimiters used for validation and counting.
- **Render workflow** — stages that count tokens, validate, and render output.
- **Observability record** — logs and metrics that include `token_count`.

## Q&A

- **Q:** Why not merge UI hover regex in this task?
  **A:** Out of scope; hover uses a different pattern for variable names only.
