# PYPOST-454: Technical Debt Analysis

## Shortcuts Taken

- **Tests-only delivery:** No production changes in `pypost/core/`. Edge-case behavior is
  documented and locked via acceptance checks; no parity bugs were discovered during STEP 3.
- **Architecture matrix assumed codes, tests lock observed codes:** STEP 2 matrices for M1, M2,
  M4, and S5 predicted `invalid_syntax` (or inner `function_name` for M2) that differ from
  current `FunctionExpressionResolver` behavior. STEP 3 asserted **observed** codes from
  production; `20-architecture.md` matrices were corrected in STEP 6 to match tests.
- **Phase 3 skipped (optional):** No `tests/test_variable_hover.py` or
  `VariableAwareTableWidget` tooltip spot checks. `TemplateService` `render_path="hover"`
  parity satisfies requirements DoD 3 — table cells delegate through the same hover pipeline
  (PYPOST-453 precedent).
- **Shared test-data constant across test modules:** `MALFORMED_NESTED_EXPRESSION_CASES` lives in
  `tests/test_function_expression_resolver.py` and is imported by
  `tests/test_template_service.py` for parity and validation-alignment tests. Acceptable for
  this slice; not promoted to `tests/helpers.py` (reserved for fakes/mocks).
- **Representative observability coverage:** STEP 5 added hover metric tests for M1, S4/S5, and
  S2 only — not every matrix row. Same pipeline applies to M2–M4 and S1/S3; full duplication
  would add little signal.

Overall: no temporary hacks or product behavior changes; this closes PYPOST-450 missing-test
debt with focused acceptance coverage.

## Code Quality Issues

- **Cross-module test import:** `test_template_service.py` imports
  `MALFORMED_NESTED_EXPRESSION_CASES` from `test_function_expression_resolver.py`. Works for
  four shared rows; optional follow-up is a dedicated `tests/expression_case_data.py` if the
  matrix grows (not required for this ticket).
- **Spacing invalid rows not fully deduplicated:** S4–S5 content appears in both
  `test_nested_spacing_variants` and `test_runtime_hover_parity_invalid_spacing` with
  different assertion shapes (resolver codes vs render fallback). Documented in
  `40-code-cleanup.md`; optional `SPACING_VARIANT_CASES` extraction if more rows are added.
- **Pre-existing orchestration coupling:** `TemplateService.render_string` still combines
  token counting, validation, render, logging, and metrics — unchanged; track in
  [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459).
- **Pre-existing parser brittleness:** Regex signature matching plus manual parenthesis-depth
  scanning in `_extract_single_argument` surfaces malformed nesting as `invalid_argument` with
  outer/inner `function_name` depending on where recursive validation fails — not as dedicated
  `invalid_syntax` for all unbalanced nested forms. Tests lock current semantics; grammar
  hardening is out of scope.

None of these are release blockers for edge-case test coverage.

## Missing Tests

**Adequate for PYPOST-454 DoD** — malformed nested M1–M4, spacing S1–S5, runtime/hover parity
for valid spaced nested (S1–S3) and invalid/malformed fallback (M1–M4, S4–S5), resolver ↔
`validate_function_expressions` alignment, and representative hover observability for edge cases.

**Still out of scope (tracked elsewhere):**

- Empty-argument calls (`{{md5()}}`), malformed closing-paren patterns, and multi-placeholder
  first-failure stability —
  [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461).
- Direct `VariableHoverHelper.resolve_text` edge-case test — optional per architecture;
  `TemplateService` hover parity is sufficient for DoD.
- Explicit `VariableAwareTableWidget` tooltip test for spaced/malformed nested cell strings —
  optional hardening; hover pipeline proven at `TemplateService` level.
- Broader spacing matrix expansion beyond S1–S5 — only if new product forms are discovered.

## Performance Concerns

- **Pre-existing duplicate scan:** `re.findall` over `{{ ... }}` runs in both
  `TemplateService._count_placeholder_expressions` and
  `FunctionExpressionResolver.validate_content`. Unchanged by this ticket; share one pass via
  [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460) if expression-heavy workloads
  appear.
- **Validate-then-render, no template cache:** Same trade-offs as
  [PYPOST-450](https://pypost.atlassian.net/browse/PYPOST-450) /
  [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455); edge-case matrices do not add
  new hot-path costs.
- **Unbounded recursion depth:** Valid nested chains still recurse without a depth cap (per
  PYPOST-453 policy). Grammar is catalog-bound; abuse risk is low today.

## Follow-up Tasks

- [**PYPOST-461**](https://pypost.atlassian.net/browse/PYPOST-461): Empty-argument calls,
  multi-placeholder first-failure behavior, and standalone malformed closing-paren / arity
  patterns (coordinate boundary with PYPOST-454 nesting/spacing coverage).
- [**PYPOST-459**](https://pypost.atlassian.net/browse/PYPOST-459): Refactor
  `TemplateService.render_string` into smaller helpers (validation, observability, render).
- [**PYPOST-460**](https://pypost.atlassian.net/browse/PYPOST-460): Single tokenization
  utility shared by render-path counting and resolver validation.
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Template/expression
  caching if metrics justify it.
- [**PYPOST-456**](https://pypost.atlassian.net/browse/PYPOST-456): STEP 7 dev-doc refresh
  (`FunctionRegistry`, `template_expression_functions.md` polish).
- [**PYPOST-457**](https://pypost.atlassian.net/browse/PYPOST-457): Explicit allow-list vs
  `env.globals` parity test (from PYPOST-451 debt).
- [**PYPOST-458**](https://pypost.atlassian.net/browse/PYPOST-458): `FunctionRegistry` /
  `register_into_env` docstring cleanup (from PYPOST-451 debt).

**Release stance:** No technical debt from PYPOST-454 is treated as a merge or release blocker.
PYPOST-450 missing-test items for malformed nested expressions and whitespace variants are
**resolved**.

## Notes

- **Resolved debt (PYPOST-450):** Deeply nested malformed expression acceptance checks;
  whitespace-heavy variants across runtime/hover; table-cell parity via hover pipeline
  equivalence. See
  [PYPOST-450 technical debt](ai-tasks/PYPOST-450/60-tech-debt.md) — items struck through and
  PYPOST-454 follow-up marked completed.
- **Resolved deferrals (PYPOST-453):** Malformed nesting, spacing variants, and edge-case
  hover/runtime parity deferred to PYPOST-454 — now covered. See
  [PYPOST-453 technical debt](ai-tasks/PYPOST-453/60-tech-debt.md).
- **Architecture doc drift (corrected in STEP 6):** Observed locked codes differed from STEP 2
  assumptions for four rows:

  | ID | STEP 2 assumption | Observed (locked in tests) |
  | --- | --- | --- |
  | M1 | `invalid_syntax` | `invalid_argument`, `function_name="md5"` |
  | M2 | `invalid_argument`, `function_name="md5"` | `invalid_argument`, `function_name="urlencode"` |
  | M4 | `invalid_syntax` | `invalid_argument`, `function_name="base64"` |
  | S5 | `invalid_syntax` | `invalid_argument`, `function_name="md5"` |

  M3 and S4 matched assumptions. `20-architecture.md` matrices updated to observed codes.
- **STEP 6 test run:** `./scripts/test.sh tests/test_function_expression_resolver.py
  tests/test_template_service.py` → **58 passed**, 39 subtests passed (2026-06-05).
- **No parity bugs found:** Runtime and hover produced identical outcomes for all covered edge
  forms; no Phase 4 production fix required.
- **Observability:** No new logs or metrics; three STEP 5 hover tests confirm existing counters
  cover malformed nested (M1), invalid spacing (S4/S5), and spaced nested success (S2).
