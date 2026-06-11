# PYPOST-470: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE for scoped edge-case test coverage. Requirements met: Unicode,
mixed valid/invalid strings, and boundary conditions are now asserted in
`tests/test_variable_name_validation.py` (47 parametrized cases). No production code changes
were required. Residual debt is pre-existing policy/documentation gaps outside this task's
scope.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Unicode accept/reject cases beyond baseline | Met | `TestValidateVariableNameUnicode` |
| Mixed strings with canonical failure reason | Met | `TestValidateVariableNameMixed` |
| Boundary valid/invalid names | Met | `TestValidateVariableNameBoundaries` |
| Baseline PYPOST-477 tests still passing | Met | `TestValidateVariableName` unchanged |
| No silent rule changes | Met | Test-only diff |

## Shortcuts Taken

- **Documented `isalnum()` behavior instead of tightening rules.** The validator uses
  `str.isalnum()` / `str.isdigit()`, which diverges from Jinja2's Python 3 lexer
  (`str.isidentifier()`). Tests encode the current product behavior; aligning rules to
  `isidentifier()` was explicitly out of scope per requirements.
- **Whitespace-only inputs tested at core layer only.** UI flows strip input before
  validation (`EnvPresenter` line ~215); boundary tests pass raw `" "` / `"\t"` into the
  core module to document validator semantics, not end-user dialog behavior.

## Code Quality Issues

- **Inconsistent error-message constants in tests.** New classes use module-level
  `_INVALID_CHARS_MSG` / `_STARTS_WITH_DIGIT_MSG`; baseline `test_invalid_names` still
  inlines full strings. Low impact; could be unified for maintainability.
- **`test_unicode_letters_allowed_by_isalnum_policy` omits `validation_failure_reason`.**
  Newer tests assert the full `(is_valid, error, reason)` triple; the three baseline
  Unicode cases do not — minor inconsistency within the same file.
- **Dev docs still describe ASCII-only names** (`doc/dev/variable_validation.md` lines 11,
  27–28) while tests confirm Unicode letters are accepted. Reconciliation deferred to
  STEP 7.

## Missing Tests

- **`isalnum()` vs `isidentifier()` divergence not exhaustively covered.** Spot checks show
  names such as `x²` are accepted by the validator but fail `isidentifier()` (Jinja2 risk),
  while NFD forms like `key\u0301` are rejected despite being valid identifiers. These edge
  cases are documented in architecture but not asserted — intentional scope limit; exhaustive
  Unicode matrix would be a separate policy/validation task.
- **Presenter and GUI integration paths not re-tested here.** Metrics/logging wiring in
  `EnvPresenter._is_valid_variable_name` remains covered only indirectly via core
  `validation_failure_reason` contract. [PYPOST-475](https://pypost.atlassian.net/browse/PYPOST-475)
  / [PYPOST-480](https://pypost.atlassian.net/browse/PYPOST-480) address integration scope.
- **Manage Environments table validation** (`env_dialog.py` →
  `validate_environment_variable_name`) has no dedicated metrics tests — pre-existing gap
  from PYPOST-163 observability design.

## Performance Concerns

None. Added tests are synchronous parametrized unit tests with bounded inputs (longest case
1000 characters). No production hot-path changes.

## Follow-up Tasks

| Priority | Ticket / step | Description |
| --- | --- | --- |
| High | STEP 7 | Update `doc/dev/variable_validation.md` — Unicode acceptance policy, valid/invalid examples, whitespace trim vs core behavior |
| Medium | New (if product wants Jinja2 parity) | Evaluate switching `validate_variable_name` from `isalnum()` to `isidentifier()`; add regression tests for known divergences (`x²`, NFD combining marks) |
| Low | [PYPOST-472](https://pypost.atlassian.net/browse/PYPOST-472) | Deduplicate error message strings between validation and UI layers |
| Low | [PYPOST-479](https://pypost.atlassian.net/browse/PYPOST-479) | Review validation debug logging verbosity |
| Low | Test hygiene | Unify error-message constants and add `validation_failure_reason` to baseline Unicode test |

Closes PYPOST-163 item 163-1 (edge-case unit test gaps). No new Jira tickets filed for
PYPOST-470 scope.
