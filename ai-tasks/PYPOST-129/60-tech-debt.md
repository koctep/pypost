# PYPOST-129: Technical Debt Analysis

## Shortcuts Taken

- `VariableHoverHelper` facade retained instead of removing it — avoids churn across tests and
  any external imports.

## Code Quality Issues

- None blocking. Plain-reference chain logic remains in `VariableHoverResolver` by design
  (hover-specific masking and depth bounds).

## Missing Tests

- Facade-only callers are covered indirectly; split classes have dedicated tests in
  `TestVariableHoverSplit`.

## Performance Concerns

- None. Delegation adds negligible indirection.

## Follow-up Tasks

- None required for this task. Original PYPOST-15 suggestion to extract into
  `EnvironmentService` is deferred — expression resolution already centralised in
  `TemplateService`.
