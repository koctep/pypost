# PYPOST-453: Technical Debt Analysis

## Shortcuts Taken

- **Declarative constant without runtime branch:** `NESTED_FUNCTION_CALLS_ALLOWED = True` in
  `function_expression_resolver.py` documents the ALLOW policy but is **not** consulted by
  validation logic. Enforcement remains the existing recursive `_validate_expression` /
  `_validate_function_args` path. This matches the architecture decision: no REJECT mode in
  this ticket; the constant + tests guard against accidental recursion removal, not toggleable
  policy.
- **No resolver algorithm changes:** PYPOST-453 aligned docs and added policy-guard tests
  without refactoring parsing or error propagation. `function_name` for nested literal errors
  still reports the **inner** offending function (`urlencode` for
  `{{md5(urlencode('db'))}}`), not the outer call — documented in tests and
  `40-code-cleanup.md`; intentional backward compatibility.
- **Intentional scope limits:** Malformed nesting, spacing variants, and exhaustive
  hover/runtime edge matrices remain deferred to
  [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454). STEP 7 dev-doc polish for
  `FunctionRegistry` overlap stays in
  [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456).

Overall: no temporary hacks were added; this was policy alignment and test/doc hardening on
top of PYPOST-452 behavior.

## Code Quality Issues

- **Policy constant is documentation-only today:** Setting `NESTED_FUNCTION_CALLS_ALLOWED`
  to `False` would not change runtime behavior until validation branches on it. Acceptable for
  a single-mode ALLOW product decision; a future REJECT or depth-cap ticket would need to wire
  the constant (or replace it with a dedicated policy module).
- **Dual policy artifacts:** The nested rule appears in both the module constant name and the
  `FunctionExpressionResolver` class docstring. Intentional per architecture (policy-as-code +
  human-readable contract); not worth deduplicating in this slice.
- **Pre-existing orchestration coupling:** `TemplateService.render_string` still combines
  token counting, validation, render, logging, and metrics in one method — unchanged by this
  ticket; track refactor in
  [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459).
- **Pre-existing parser brittleness:** Regex signature matching plus manual parenthesis-depth
  scanning in `_extract_single_argument` is correct for the current grammar but may not scale
  if the expression surface grows.

None of these are release blockers for nested-policy alignment.

## Missing Tests

**Adequate for PYPOST-453 DoD** — policy-guard coverage added in resolver and
`TemplateService` suites (valid two- and three-level chains, nested unknown function, nested
literal arg, multi-arg inside nested call, runtime/hover parity for valid nested input, nested
observability on hover).

**Still out of scope (tracked elsewhere):**

- Malformed nested expressions, unbalanced depth edge cases, and spacing variants across all
  contexts — [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454).
- Empty-argument calls (`{{md5()}}`), malformed closing-paren patterns, and multi-placeholder
  first-failure stability — [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461)
  (overlaps partially with PYPOST-454).
- Direct `VariableHoverHelper.resolve_text` nested test — optional per architecture;
  `TemplateService` parity test is sufficient for this ticket.
- Test proving `NESTED_FUNCTION_CALLS_ALLOWED = False` rejects nesting — not applicable until
  a REJECT mode exists.

## Performance Concerns

- **Pre-existing duplicate scan:** `re.findall` over `{{ ... }}` runs in both
  `TemplateService._count_placeholder_expressions` (token counting) and
  `FunctionExpressionResolver.validate_content` (validation). Impact is small for typical
  payloads; share one pass via
  [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460) if expression-heavy workloads
  appear.
- **Unbounded recursion depth:** Valid nested chains recurse without a depth cap (per
  requirements). Grammar is catalog-bound and unary-only, so abuse risk is low today; optional
  hardening belongs in a future ticket if untrusted template volume grows.
- **Validate-then-render, no template cache:** Same trade-offs as
  [PYPOST-450](https://pypost.atlassian.net/browse/PYPOST-450) /
  [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455); nested chains do not add new
  hot-path costs beyond slightly deeper recursion on valid chains.

## Follow-up Tasks

- [**PYPOST-454**](https://pypost.atlassian.net/browse/PYPOST-454): Edge-case tests for
  malformed nested expressions, spacing variants, and hover/runtime parity for those forms.
- [**PYPOST-459**](https://pypost.atlassian.net/browse/PYPOST-459): Refactor
  `TemplateService.render_string` into smaller helpers (validation, observability, render).
- [**PYPOST-460**](https://pypost.atlassian.net/browse/PYPOST-460): Single tokenization
  utility shared by render-path counting and resolver validation.
- [**PYPOST-461**](https://pypost.atlassian.net/browse/PYPOST-461): Expand resolver test
  matrix for empty-argument and malformed nested edge cases (coordinate with PYPOST-454).
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Template/expression
  caching if metrics justify it.
- [**PYPOST-456**](https://pypost.atlassian.net/browse/PYPOST-456): STEP 7 dev-doc refresh
  (`FunctionRegistry`, `template_expression_functions.md` polish).
- [**PYPOST-457**](https://pypost.atlassian.net/browse/PYPOST-457): Explicit allow-list vs
  `env.globals` parity test (from PYPOST-451 debt).
- [**PYPOST-458**](https://pypost.atlassian.net/browse/PYPOST-458): `FunctionRegistry` /
  `register_into_env` docstring cleanup (from PYPOST-451 debt).

**Release stance:** No technical debt from PYPOST-453 is treated as a merge or release
blocker. The nested policy mismatch called out in
[PYPOST-450 technical debt](ai-tasks/PYPOST-450/60-tech-debt.md) is **resolved**.

## Notes

- **Resolved debt (PYPOST-450):** Architecture vs implementation nested-call policy mismatch;
  contradictory "Known Deviation" in `doc/dev/template_expression_functions.md`; missing
  policy-guard tests; stale nested-rejection text in `ai-tasks/PYPOST-450/20-architecture.md`.
- **STEP 6 test run:** `./scripts/test.sh tests/test_function_expression_resolver.py
  tests/test_template_service.py` → **49 passed**, 6 subtests passed (2026-06-05).
- Observability: no new log lines or metric counters; two nested metrics tests in STEP 5 confirm
  existing counters cover nested success and validation failure on `render_path=hover`.
