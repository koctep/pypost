# PYPOST-461: Technical Debt Analysis

## Shortcuts Taken

- **Tests-only delivery:** No production changes in `pypost/core/`. Edge-case behavior is
  documented and locked via acceptance checks.
- **No TemplateService integration tests:** First-failure and empty-arg cases are proven at
  resolver level only. Render-path observability for multi-placeholder failures inherits from
  existing `TemplateService` validation delegation (PYPOST-454 precedent for resolver-only
  matrices).
- **Representative empty-arg catalog coverage:** E1–E3 cover `md5`, `urlencode`, and `base64`
  — the full default catalog. No per-function duplication beyond catalog size.

Overall: no temporary hacks or product behavior changes; PYPOST-450 missing-test debt for
empty-args, standalone closing-paren patterns, and multi-placeholder first-failure is **resolved**.

## Code Quality Issues

- **Case constant proliferation in test module:** Four case tables now live in
  `test_function_expression_resolver.py` (`MALFORMED_NESTED_EXPRESSION_CASES` from PYPOST-454
  plus three PYPOST-461 tables). Optional follow-up: `tests/expression_case_data.py` if the
  matrix grows further — not required for this ticket.
- **Pre-existing parser brittleness:** Empty-args map to `invalid_argument` (not `invalid_arity`)
  because `_extract_single_argument` returns `""` and downstream grammar checks fail. Tests lock
  this semantics; dedicated empty-arg error code is out of scope.
- **Pre-existing orchestration coupling:** `TemplateService.render_string` unchanged; track in
  [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459).

None of these are release blockers for PYPOST-461 DoD.

## Missing Tests

**Adequate for PYPOST-461 DoD:**

- Empty-argument calls E1–E3
- Standalone extra-closing-paren P1–P2
- Multi-placeholder first-failure F1–F5 via `validate_content`
- Direct `validate_expressions` contract V1–V2
- Malformed nested M1–M4 retained from PYPOST-454

**Still out of scope (tracked elsewhere):**

- TemplateService render/hover parity for empty-arg or first-failure strings — optional;
  fallback semantics unchanged from single-placeholder invalid forms.
- Full-suite Qt segfault on Python 3.14 in some environments — pre-existing infrastructure
  concern, not introduced by PYPOST-461.

## Performance Concerns

- **Pre-existing duplicate scan:** Tokenization may run in both counting and validation paths —
  [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460).
- First-failure short-circuits after the first invalid expression — no additional cost vs
  validating all placeholders.

## Follow-up Tasks

- [**PYPOST-459**](https://pypost.atlassian.net/browse/PYPOST-459): Refactor
  `TemplateService.render_string` into smaller helpers.
- [**PYPOST-460**](https://pypost.atlassian.net/browse/PYPOST-460): Single tokenization utility
  shared by render-path counting and resolver validation.
- Optional: extract shared expression case data module if matrices continue to grow.

**Release stance:** No technical debt from PYPOST-461 is treated as a merge or release blocker.
PYPOST-450 missing-test items for empty-args, standalone closing-paren patterns, and
multi-placeholder first-failure are **resolved**.

## Notes

- PYPOST-454 `60-tech-debt.md` follow-up link to PYPOST-461 can be considered satisfied.
- Documented first-failure ordering in `doc/dev/template_expression_functions.md`.
