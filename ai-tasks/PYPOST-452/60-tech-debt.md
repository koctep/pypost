# PYPOST-452: Technical Debt Analysis

## Shortcuts Taken

- No temporary shortcuts were identified in the current implementation scope.
- Validation behavior and fallback semantics were kept intentionally aligned with existing
  behavior, which limits cleanup opportunities in this task.

## Code Quality Issues

- `TemplateService.render_string` still combines validation orchestration, fallback handling,
  logging, and metrics calls in one method; this is acceptable for parity but remains a
  refactoring opportunity for smaller units.
- `FunctionExpressionResolver` uses regex-based parsing plus manual parenthesis-depth scanning.
  It is correct for current rules, but future grammar growth may reduce maintainability.

## Missing Tests

- Add explicit tests for empty argument calls (for example, `{{md5()}}`) to lock down whether
  they should map to `invalid_argument` or `invalid_arity`.
- Add tests for malformed nested expressions with unmatched closing parenthesis patterns to
  verify error-code stability.
- Add focused tests for multiple placeholders where an invalid expression appears after one or
  more valid expressions to ensure first-failure behavior is intentional and stable.

## Performance Concerns

- Expression scanning currently runs `re.findall` over full content in both
  `TemplateService.render_string` (token counting) and `FunctionExpressionResolver.validate_content`
  (validation scan), causing duplicate linear passes for non-empty templates.
- The impact is likely small for typical payload sizes, but high-volume or very large template
  bodies could benefit from sharing one tokenization pass.

## Follow-up Tasks

- [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459): Refactor
  `TemplateService.render_string` into smaller helpers for validation decision, metrics/log
  emission, and render execution to improve readability and local testability.
- [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460): Evaluate introducing a single
  tokenization utility so render-path token counting and resolver validation can reuse the same
  extracted expressions.
- [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461): Expand resolver test matrix for
  malformed nested expressions and empty-argument edge cases.
- Keep nested-call policy unchanged in this task; track policy changes only via the dedicated
  follow-up ticket.

## Notes

- Update in `doc` is not applicable for STEP 6 in this task because no user-facing behavior or
  operator workflow changed during technical-debt analysis.
- Roadmap status remains unchanged with STEP 6 marked as in progress (`[/]`).
