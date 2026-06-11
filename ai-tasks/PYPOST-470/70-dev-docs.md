# PYPOST-470: Dev Docs

## Updates

Updated `doc/dev/variable_validation.md` to reconcile documentation with tested validator
behavior (PYPOST-470 edge-case tests):

- **Unicode policy** — Documented that `str.isalnum()` accepts Unicode letters; added
  accept/reject table with examples from `TestValidateVariableNameUnicode`.
- **Jinja2 divergence** — Clarified PyPost uses `isalnum()`/`isdigit()`, not Jinja2's
  `isidentifier()`; noted known edge-case mismatches without changing rules.
- **Failure-reason precedence** — Documented canonical order (`empty` → `starts_with_digit`
  → `invalid_chars`) aligned with `TestValidateVariableNameMixed`.
- **UI vs core behavior** — Documented whitespace stripping in `EnvPresenter` vs raw-string
  semantics in core validation (`TestValidateVariableNameBoundaries`).
- **Examples** — Added Unicode valid names, Unicode digit starts, emoji/symbol rejects, and
  long/underscore-only boundary cases.
- **Test coverage** — Added test-class table and focused pytest command.
- **Troubleshooting** — Common doc/behavior mismatches and precedence questions.

## Verification

- Doc wording matches `pypost/core/variable_name_validation.py` implementation.
- Examples and tables align with all 47 parametrized cases in
  `tests/test_variable_name_validation.py`.
- No new standalone doc file; existing `variable_validation.md` remains the authoritative
  developer reference (same pattern as PYPOST-478).

## Related

- `ai-tasks/PYPOST-470/60-tech-debt.md` — STEP 7 follow-up item closed.
- PYPOST-477 — baseline tests; PYPOST-478 — shared core module extraction.
