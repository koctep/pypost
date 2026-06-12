# PYPOST-113: Technical Debt Analysis

## Shortcuts Taken

- Regex-based plain-variable detection retained (not Jinja AST). False positives inside
  string literals remain a known limitation from PYPOST-13.

## Code Quality Issues

- **Identifier rule divergence:** `PLAIN_VARIABLE_PATTERN` allows digit-leading names;
  `FunctionExpressionResolver._IDENTIFIER_RE` does not. Documented; no behavior change.

## Missing Tests

- None for acceptance criteria. Added `TestPlainVariablePattern` in tokenizer tests.

## Performance Concerns

- None. Same compiled regex object shared by reference.

## Follow-up Tasks

- Align hover plain-variable identifier rules with resolver validation (digit-leading).
  — Jira: TBD if product requires stricter hover matching.

## Blocker review (Phase C)

**Verdict: SAFE TO CLOSE**

- Shared helper exported and documented; hover tests green; no user-visible regression.
