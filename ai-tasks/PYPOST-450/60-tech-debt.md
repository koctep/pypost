# PYPOST-450: Technical Debt Analysis

## Shortcuts Taken

- Kept `_ALLOWED_FUNCTIONS` as an in-class constant in `TemplateService` rather than introducing
  a dedicated `FunctionRegistry` module described in architecture.
- Kept function parsing/validation inside `TemplateService` instead of extracting a
  `FunctionExpressionResolver` contract.
- Preserved backward-compatible fallback behavior (`render_string` returns original content on
  validation/render errors) to avoid changing user-visible behavior in this slice.

## Code Quality Issues

- `TemplateService` currently combines rendering, validation, parsing, allow-list ownership,
  logging, and metrics. This centralization increases coupling and makes future function-catalog
  expansion riskier.
- Nested function support is currently accepted by validation, while architecture documented nested
  calls as out of scope for this iteration. Behavior and architecture documentation are out of
  sync.
- `_extract_single_argument` implements parenthesis-depth parsing manually; this is workable for
  current scope but brittle for future grammar growth.
- Hover helper uses a class-level `TemplateService` instance, which is practical for reuse but
  makes dependency boundaries less explicit than instance-level injection.

## Missing Tests

- No focused tests for deeply nested malformed expressions (e.g. unbalanced depth edge cases) in
  `_extract_single_argument`.
- No explicit tests for whitespace-heavy function formatting variants in all contexts
  (runtime + hover + table cells), such as `{{ md5( db ) }}`.
- No dedicated test asserting architecture intent around nested-call policy (either explicit allow
  or explicit reject) to prevent future drift.

## Performance Concerns

- Each render re-validates expressions and then re-renders through Jinja; there is no cache for
  repeated templates. This is acceptable now, but hot-path repeated renders may pay redundant parse
  and regex costs.
- `re.findall` runs for token counting and validation; combined scans are small today but should be
  profiled if expression-heavy payloads become common.

## Follow-up Tasks

- [**PYPOST-451**](https://pypost.atlassian.net/browse/PYPOST-451): Extract
  `FunctionRegistry` from `TemplateService` and move allow-list ownership
  there; keep `TemplateService` as orchestration boundary.
- [**PYPOST-452**](https://pypost.atlassian.net/browse/PYPOST-452): Introduce
  `FunctionExpressionResolver` module and migrate parsing/validation
  logic out of `TemplateService`.
- [**PYPOST-453**](https://pypost.atlassian.net/browse/PYPOST-453): Resolve
  nested-function policy mismatch (architecture vs implementation), then
  enforce with explicit validation rules and tests.
- [**PYPOST-454**](https://pypost.atlassian.net/browse/PYPOST-454): Add
  edge-case tests for malformed nested expressions, spacing variants, and
  hover/runtime parity for those variants.
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Evaluate
  lightweight template/expression caching for repeated render paths after
  collecting usage metrics from current observability counters.
