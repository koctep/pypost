# PYPOST-450: Technical Debt Analysis

## Functional Completeness (DoD Cross-Check)

| DoD # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Functions in all variable-enabled contexts | **Met** | Same `TemplateService.render_string` path for URL, header/param keys and values, body (HTTPClient), and hover (`VariableHoverHelper`). Integration tests cover URL, header value, param key/value; body and header-name HTTPClient rows rely on shared pipeline + hover/widget tests. |
| 2 | Consistent interaction with variable usage | **Met** | Hover delegates to `render_string(..., render_path="hover")`; plain variables keep direct lookup/masking. |
| 3 | Function arguments supported | **Met** | Single-arg and nested catalog chains (`urlencode`, `md5`, `base64`). |
| 4 | Existing variable scenarios unchanged | **Met** | Fallback returns original content on invalid expressions; plain `{{var}}` tests pass. |
| 5 | Documentation and catalog examples | **Met** | `doc/dev/template_expression_functions.md` (STEP 7). [PYPOST-456](https://pypost.atlassian.net/browse/PYPOST-456) completed. |
| 6 | Acceptance checks across contexts | **Met (layered acceptance)** | 109 tests, 39 subtests (STEP 6 run below); context matrix in architecture doc. Body and header-name rely on shared `render_string` pipeline + `TemplateService`/hover tests; HTTPClient integration for those two surfaces is optional hardening (see Missing Tests). |
| 7 | Single approved UX function-call format | **Met (implementation)** | Canonical `{{func(var)}}` / nested form enforced by resolver; no separate inline error UI (by design). Formal UX sign-off artifact is not recorded in repo — implementation matches approved syntax in requirements/architecture. |
| 8 | Security: approved catalog only | **Met** | `FunctionRegistry` allow-list; resolver pre-check; negative tests for Jinja filters/attributes. |
| 9 | Canonical syntax matches approved format | **Met** | Calls only inside `{{...}}`; multi-arg and non-catalog forms rejected. |

**Release stance:** PYPOST-450 is **functionally complete** for merge/closure. Remaining items below are maintainability, optional hardening, and performance follow-ups — not blockers.

## Shortcuts Taken

- **Backward-compatible fallback:** `render_string` returns original field content on validation or
  render failure rather than surfacing inline errors. Preserves existing variable workflows; logs
  and metrics carry diagnostic codes instead.
- **Class-level hover service:** `VariableHoverHelper` holds a class-level `TemplateService`
  instance, rebuilt via `set_metrics()`. Practical for reuse; less explicit than instance DI
  ([PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459) hover polish).
- **Validate-then-render, no cache:** Every render re-scans and re-validates expressions before
  Jinja. Acceptable for desktop scope; caching deferred to
  [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455) after usage metrics.
- **Regex + manual paren-depth parser:** Resolver uses regex signature matching and
  `_extract_single_argument` depth scanning instead of a formal grammar. Sufficient for three
  catalog functions; brittle if the catalog or grammar grows.

## Code Quality Issues

- **`TemplateService` orchestration density:** Still combines token counting, validation
  delegation, Jinja render, logging, and metrics despite registry/resolver extraction. Track
  refactor in [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459).
- **Duplicate tokenization:** `re.findall(r"\{\{\s*(.*?)\s*\}\}", content)` runs in both
  `TemplateService._count_placeholder_expressions` and
  `FunctionExpressionResolver.validate_content`. Share one pass via
  [PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460).
- **Hover pattern inconsistency:** `VariableHoverHelper.VARIABLE_PATTERN` is
  `\{\{([a-zA-Z0-9_]+)\}\}` (allows digit-leading names such as `{{0db}}`) while resolver
  `_IDENTIFIER_RE` requires `[a-zA-Z_][a-zA-Z0-9_]*` (letter/underscore first). Digit-leading
  plain variables may take the fast hover lookup path but fail resolver validation at runtime.
- **Cross-module test import:** `test_template_service.py` imports
  `MALFORMED_NESTED_EXPRESSION_CASES` from `test_function_expression_resolver.py`. Works for
  current matrix; optional extraction to shared test data if matrices grow (PYPOST-454 note).
- **Pre-existing Qt deprecations:** Hover widget tests emit `QMouseEvent.globalPos()` /
  `pos()` deprecation warnings (PySide6). Unrelated to PYPOST-450 scope.

## Missing Tests

**Adequate for PYPOST-450 closure** — catalog functions, nesting, multi-arg rejection, security
negatives, runtime/hover parity, observability, and HTTPClient integration for URL, header value,
and param key/value.

**Optional integration gaps (same pipeline, thinner HTTPClient coverage):**

- Request **body** function expression through `HTTPClient.send_request` (render path exists;
  covered at `TemplateService` layer only).
- **Header name** (key column) function expression through HTTPClient (param key covered; header
  key not).
- Spaced/malformed nested expressions in `VariableAwareTableWidget` tooltip strings (hover
  pipeline proven at `TemplateService` level; table test covers valid function cell only).

**Tracked in follow-up Jira (not PYPOST-450 blockers):**

- Empty-argument calls, multi-placeholder first-failure, standalone closing-paren patterns —
  [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461).
- Explicit allow-list vs `env.globals` parity —
  [PYPOST-457](https://pypost.atlassian.net/browse/PYPOST-457).

## Performance Concerns

- **No template/expression cache:** Repeated identical renders pay full validate + Jinja cost.
  Acceptable now; revisit via [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455) if
  metrics show hot paths.
- **Duplicate regex scans:** Counting and validation each walk all `{{...}}` tokens
  ([PYPOST-460](https://pypost.atlassian.net/browse/PYPOST-460)).
- **Unbounded nested recursion:** Valid chains recurse without depth cap (PYPOST-453 policy).
  Catalog-bound; low abuse risk for desktop use.

## Resolved Items

- ~~`_ALLOWED_FUNCTIONS` in-class constant~~ — **resolved:** allow-list in
  `FunctionRegistry` (`pypost/core/function_registry.py`).
- ~~Parsing/validation inside `TemplateService`~~ — **resolved:** syntax validation in
  `FunctionExpressionResolver` (`pypost/core/function_expression_resolver.py`).
- ~~Nested function policy mismatch~~ — **resolved** by
  [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453): ALLOW policy codified; docs
  aligned.
- ~~No focused tests for deeply nested malformed expressions~~ — **resolved** by
  [PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454): M1–M4 matrix.
- ~~No whitespace-heavy function formatting variant tests~~ — **resolved** by PYPOST-454: S1–S5
  spacing matrix with runtime/hover parity.
- ~~No HTTPClient integration tests for function expressions~~ — **resolved** (STEP 3 review):
  URL, header value, param key/value, invalid passthrough in `tests/test_http_client.py`.
- ~~No Jinja filter/attribute negative security tests~~ — **resolved** (STEP 3 review):
  `{{ db|md5 }}` and `{{ db.__class__ }}` in `tests/test_template_service.py`.
- ~~Core module split (registry + resolver)~~ — **resolved** by
  [PYPOST-451](https://pypost.atlassian.net/browse/PYPOST-451) /
  [PYPOST-452](https://pypost.atlassian.net/browse/PYPOST-452).

## Follow-up Tasks

- ~~[**PYPOST-451**](https://pypost.atlassian.net/browse/PYPOST-451): Extract
  `FunctionRegistry`.~~ — **completed.**
- ~~[**PYPOST-452**](https://pypost.atlassian.net/browse/PYPOST-452): Introduce
  `FunctionExpressionResolver`.~~ — **completed.**
- ~~[**PYPOST-453**](https://pypost.atlassian.net/browse/PYPOST-453): Resolve nested-function
  policy mismatch.~~ — **completed.**
- ~~[**PYPOST-454**](https://pypost.atlassian.net/browse/PYPOST-454): Edge-case tests for
  malformed nested expressions and spacing variants.~~ — **completed.**
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Evaluate lightweight
  template/expression caching after collecting usage metrics.
- ~~[**PYPOST-456**](https://pypost.atlassian.net/browse/PYPOST-456): Optional dev-doc polish
  beyond `doc/dev/template_expression_functions.md`.~~ — **completed** (Jira: Done).
- [**PYPOST-457**](https://pypost.atlassian.net/browse/PYPOST-457): Explicit registry/globals
  parity test.
- ~~[**PYPOST-459**](https://pypost.atlassian.net/browse/PYPOST-459): Orchestration refactor —
  thin `TemplateService` façade.~~ — **completed** (Jira: Done). Hover DI polish remains
  optional (no dedicated ticket).
- [**PYPOST-460**](https://pypost.atlassian.net/browse/PYPOST-460): Shared tokenization
  deduplication between counting and validation paths.
- [**PYPOST-461**](https://pypost.atlassian.net/browse/PYPOST-461): Empty-argument calls,
  multi-placeholder first-failure, standalone malformed closing-paren patterns (boundary with
  PYPOST-454 documented in `ai-tasks/PYPOST-454/60-tech-debt.md`).

## STEP 6 Validation

Test run (2026-06-06):

```text
.venv/bin/python -m pytest \
  tests/test_template_service.py \
  tests/test_function_expression_resolver.py \
  tests/test_function_registry.py \
  tests/test_variable_hover.py \
  tests/test_http_client.py -q

109 passed, 8 warnings, 39 subtests passed in 0.68s
```

Warnings: 7 pre-existing PySide6 deprecation notices in hover widget tests (`globalPos` /
`pos()`), plus 1 environment `PytestCacheWarning` when cache is not writable. Not PYPOST-450
regressions.
