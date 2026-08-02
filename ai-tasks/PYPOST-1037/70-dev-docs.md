# PYPOST-1037: Developer Documentation

## Scope

PYPOST-1037 adds the allow-listed `to_int(value)` template expression for
converting a supplied ASCII decimal string into an integer-shaped HTTP request
value. This documentation records its grammar, JSON materialization, narrow
fail-closed transport behavior, compatibility boundary, safe operational
signal, and focused regression coverage.

## Documentation Updates

| File | Update |
| --- | --- |
| `doc/dev/template_expression_functions.md` | Added `to_int` syntax and accepted input grammar; URL/parameter/JSON examples; strict HTTP no-dispatch contract; legacy fallback and subclass compatibility boundaries; error event, metrics, and focused test command. |
| `doc/dev/README.md` | Updated the template-expression index entry to include PYPOST-1037. |

## Contract Recorded

- `to_int` accepts exactly one string matching `[+-]?[0-9]+`; it rejects empty,
  non-text, whitespace-padded, fractional, exponent, underscore, boolean, and
  non-ASCII decimal forms.
- It renders decimal text in URL, header, and parameter fields. An unquoted
  JSON-body expression is parsed as a native JSON integer.
- A failed direct `to_int(...)` while `HTTPClient` prepares URL, headers,
  parameters, or body raises `ExecutionError(TEMPLATE)` and prevents
  `session.request`.
- This does not turn every template error into a hard failure: unrelated
  invalid forms retain complete-field literal fallback, including a valid
  `to_int` next to an unrelated invalid token.
- The HTTP boundary logs the safe ERROR event
  `template_integer_conversion_failed` and uses existing bounded template
  metrics; neither logs nor metrics carry failed values or sensitive request
  content.

## Validation

- [x] Examples match `FunctionRegistry._to_int` and `HTTPClient` preparation:
  ASCII decimal string input, decimal URL/parameter output, and native JSON
  integer materialization for unquoted body expressions.
- [x] Failure text distinguishes the normal `TemplateService`/hover fallback
  from strict HTTP preparation and explicitly documents the no-dispatch
  guarantee.
- [x] Compatibility notes cover non-direct `to_int` names, a valid conversion
  beside an unrelated invalid token, and legacy `TemplateService` overrides.
- [x] Observability documentation matches the safe HTTP event, redaction
  boundary, runtime versus validation metric outcomes, and no-new-metric
  decision.
- [x] Focused regression command is documented:
  `PYTEST_ARGS='tests/test_template_service.py tests/test_http_client.py' make test`.
- [x] `git diff --check` passed with no whitespace errors.

## Approval Basis

The sprint runner's autonomous workflow authorizes this Step 8 continuation.
The standing instruction requires independent review; the independent reviewer
returned PASS after verifying the public expression grammar, strict/fallback
boundary, sensitive-log contract, metric outcomes, test scope, and
documentation index before the roadmap step was completed.

## Worklog

```text
role: execution
step: 8
step_name: Dev Docs
actions: documented to_int conversion grammar, HTTP strict failure contract,
         compatibility fallback, safe observability signal, regression scope,
         and index entry
time_spent: 12m
tokens_used: 4100

role: independent_docs_reviewer
step: 8
step_name: Dev Docs Review
verdict: PASS — no findings after amendments
actions: verified syntax and ASCII-decimal grammar, HTTP no-dispatch boundary,
         legacy fallback, sanitized event, metric outcomes, test scope, and index
time_spent: 7m
tokens_used: 2100
```
