# Template Expression Functions (PYPOST-450–PYPOST-454)

## Overview

PYPOST-450 adds function expressions to template placeholders in all variable-enabled request
surfaces. Canonical syntax: function calls appear only inside `{{...}}`, for example
`{{urlencode(db)}}`.

PYPOST-451 extracts the function catalog into `pypost/core/function_registry.py`
(`FunctionRegistry`).

PYPOST-452 splits template-function validation responsibilities:

- `FunctionExpressionResolver` owns parsing and validation flow for `{{...}}` expressions.
- `ValidationResult` lives in `pypost/core/template_expression_types.py` as a shared type.
- `TemplateService` orchestrates environment setup, rendering, logging, and metrics, while
  delegating expression validation to the resolver.

PYPOST-453 aligns and documents the nested-function policy: allow-listed function calls may
nest recursively (for example `{{md5(urlencode(db))}}`). Policy is declared by
`NESTED_FUNCTION_CALLS_ALLOWED` in `function_expression_resolver.py` and enforced by the
existing recursive validation path.

PYPOST-454 adds acceptance tests for malformed nested expressions, whitespace-heavy
variants, and runtime/hover parity for those forms. Delivery is tests-only; observed
validation codes and fallback behavior are documented in the edge-case section below.

Implemented behavior is backward compatible:

- Valid expressions are rendered through `TemplateService`.
- Invalid expressions fall back to original content (no hard request-time failure).
- Plain variable placeholders like `{{host}}` continue to work unchanged.

## Architecture

Main components:

- `pypost/core/function_registry.py` (`FunctionRegistry`)
  - Single source of truth for allow-listed template-callable names and implementations:
    `urlencode`, `md5`, `base64`.
  - Exposes `allowed_names()`, `is_allowed()`, `get()`, and `register_into_env(env)` to bind
    those callables onto `jinja2.Environment.globals` (catalog keys only).
- `pypost/core/template_expression_types.py` (`ValidationResult`)
  - Shared validation outcome dataclass with `is_valid`, `code`, and `function_name`.
  - Factory methods: `ValidationResult.valid()` and `ValidationResult.error(...)`.
- `pypost/core/function_expression_resolver.py` (`FunctionExpressionResolver`)
  - Parses and validates expressions inside `{{...}}`.
  - Uses `FunctionRegistry` for allow-list checks at every call node, including nested chains.
  - Exposes `NESTED_FUNCTION_CALLS_ALLOWED` as the declarative nested-call policy constant.
  - Returns `ValidationResult` and does not emit logs or metrics.
- `pypost/core/template_service.py` (`TemplateService`)
  - Owns `jinja2.Environment`, registry wiring, render orchestration, logging, and metrics.
  - Delegates `validate_function_expressions(...)` and render-path validation to
    `FunctionExpressionResolver`.
  - Maps validation codes to user-facing messages only on the render fallback path.
- `pypost/ui/widgets/mixins.py` (`VariableHoverHelper`)
  - Reuses `TemplateService.render_string(..., render_path="hover")` for function hover parity.
  - Keeps hidden-variable masking for plain variables via `HIDDEN_MASK`.
- `pypost/core/metrics.py` (`MetricsManager`)
  - Exposes counters for expression render attempts and validation failures.
- `pypost/core/http_client.py` (`HTTPClient`)
  - Renders URL, header keys/values, param keys/values, and body via
    `TemplateService.render_string` before outbound requests.
- `pypost/core/request_service.py` (`RequestService`)
  - MCP/history paths render URL and body only (headers/params are not in the MCP model).

### Context coverage matrix

Every variable-enabled surface uses the same validation + render pipeline. Header and param
name/value columns are separate render/hover surfaces.

| Context | UI surface | Render path | Hover path |
| --- | --- | --- | --- |
| Request URL | `RequestWidget.url_input` | `HTTPClient` → `render_string(url)` | `VariableAwareLineEdit` → `VariableHoverHelper` |
| Header names | `RequestWidget.headers_table` key column | `render_string(k)` per row | Table cell hover |
| Header values | `RequestWidget.headers_table` value column | `render_string(v)` per row | Table cell hover |
| Param names | `RequestWidget.params_table` key column | `render_string(k)` per row | Table cell hover |
| Param values | `RequestWidget.params_table` value column | `render_string(v)` per row | Table cell hover |
| Request body | `RequestWidget.body_edit` | `render_string(body)` | `CodeEditor` hover mixin |
| Hover preview | All editors above | N/A (preview only) | `VariableHoverHelper.resolve_text` |

UI propagation: `env_presenter.py` → `tabs_presenter.py` → `RequestWidget` supplies variable
maps and hidden keys to editors. Expression parsing happens only in core modules, not in
presenters.

## Usage/API

Primary API entry points:

- `TemplateService.render_string(content, variables, render_path="runtime")`
  - Validation-first render flow:
    1. Delegate validation to `FunctionExpressionResolver`.
    2. On invalid expression, log and emit validation metrics, then fall back to original
       content.
    3. On valid expression, render through Jinja.
    4. On render exception, emit render error metric and fall back to original content.
- `TemplateService.validate_function_expressions(content) -> ValidationResult`
  - Thin delegate to `FunctionExpressionResolver.validate_content(content)`.
- `FunctionExpressionResolver.validate_content(content) -> ValidationResult`
  - Resolver-level API for expression scanning and validation.
- `FunctionExpressionResolver.validate_expressions(expressions) -> ValidationResult`
  - Validates pre-tokenized inner expression strings (used by render path after a single
    scan).
- `tokenize_template_expressions(content) -> list[str]` (`template_expression_tokenizer`)
  - Canonical extraction of inner text for each `{{ ... }}` placeholder.

Supported validation result codes:

- `unknown_function`
- `invalid_arity`
- `invalid_argument`
- `invalid_syntax`

Supported patterns:

- Plain variable: `{{host}}`
- Function call: `{{urlencode(db)}}`
- Nested function call: `{{md5(urlencode(db))}}`
- Deep chain (no fixed depth limit): `{{base64(md5(urlencode(db)))}}`

Supported functions:

- `urlencode(var)` -> URL-encoded string
- `md5(var)` -> hex MD5 digest
- `base64(var)` -> Base64-encoded string

Examples:

- URL field: `/{{host}}/{{urlencode(db)}}`
- Header/param/body values: `{{md5(secret)}}`, `{{base64(path)}}`
- Hover tooltip resolution uses the same render rules as runtime for function placeholders.
- Nested chain: `{{md5(urlencode(db))}}` with `db="a b"` → MD5 of URL-encoded value.

Invalid examples (kept as original text due fallback behavior):

- Unknown function: `{{not_allowed(db)}}`
- Unknown function nested: `{{md5(bad(db))}}`
- Multi-argument call: `{{urlencode(db, host)}}`
- Multi-argument inside nested call: `{{md5(urlencode(a, b))}}`
- Literal argument: `{{urlencode('db')}}`
- Literal inside nested call: `{{md5(urlencode('db'))}}`
- Malformed signature: `{{urlencode(db}}`

### Invalid expression fallback

On validation or render failure, `render_string` returns the **original field content**
unchanged. This is intentional backward-compatible behavior — one bad expression must not
break unrelated fields or plain `{{var}}` placeholders.

| Path | User-visible outcome | Diagnostics |
| --- | --- | --- |
| Runtime (send) | Entire field kept as typed literal | `INFO` validation + `WARNING` fallback logs;
  `validation_error` metric |
| Hover preview | Tooltip shows original `{{...}}` token | Same render path with `render_path="hover"` |
| Render exception | Original content returned | `WARNING` fallback log; `render_error` metric (non-`ValueError` only) |

There is no inline error UI in PYPOST-450 scope. Structured codes appear in logs and
Prometheus labels via `TemplateService._VALIDATION_MESSAGES` (logging only).

Flow:

```text
validate_content → invalid? → log/metrics → raise ValueError inside try
render_with_jinja → exception? → log/metrics → except handler
except → return original content string unchanged
```

## Security

Function execution is restricted to the catalog in `FunctionRegistry`. Enforcement points:

1. `FunctionExpressionResolver` — grammar and catalog membership before render.
2. `FunctionRegistry.register_into_env` — only catalog keys bound to `env.globals`.
3. Jinja `Environment` — not a `SandboxedEnvironment`; security relies on allow-list +
   pre-render validation, not template sandboxing.

Rejected non-catalog Jinja constructs (original content returned):

- Jinja filters: `{{ db|md5 }}`
- Attribute access: `{{ db.__class__ }}`

Negative tests in `tests/test_template_service.py`:

- `test_validate_rejects_jinja_filter_form`
- `test_validate_rejects_attribute_access_form`
- `test_render_jinja_filter_form_returns_original_content`
- `test_render_attribute_access_form_returns_original_content`

## Nested Function Call Policy (PYPOST-453)

| Rule | Behavior |
|------|----------|
| Nested allow-listed calls | **Allowed** — argument is identifier or nested allow-listed call |
| Depth limit | **None** — each level must satisfy catalog + single-argument rules |
| Catalog check | `FunctionRegistry.is_allowed` at every call node, recursively |
| Multi-argument at any level | Rejected (`invalid_arity`; outer may see `invalid_argument`) |
| Literals / arbitrary expressions | Rejected (`invalid_argument` or `invalid_syntax`) |
| Unknown function in chain | Rejected (`unknown_function` on the offending name) |

Policy constant: `NESTED_FUNCTION_CALLS_ALLOWED = True` in
`pypost/core/function_expression_resolver.py`. It is **declarative** (documented intent);
validation logic does not branch on it in the current release.

**`function_name` on nested errors:** inner validation failures propagate with the
**innermost** offending function name (for example `urlencode` for
`{{md5(urlencode('db'))}}`, not `md5`). Only inner `invalid_arity` is remapped to outer
`invalid_argument`.

Edge-case acceptance tests for malformed nesting and spacing variants were added in
[PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454) — see **Edge-Case Expression
Variants (PYPOST-454)** below.

## Edge-Case Expression Variants (PYPOST-454)

PYPOST-454 closes PYPOST-450 missing-test debt with **tests-only** delivery. Acceptance
checks lock observed resolver and render behavior for malformed nested expressions,
whitespace-heavy variants, and runtime/hover parity. No production code changed.

### Malformed nested expressions (M1–M4)

Unbalanced or incomplete nesting at depth (not empty-argument or standalone
closing-paren patterns — see PYPOST-461 boundary below).

| ID | Example | Validation code | `function_name` | Render fallback |
| --- | --- | --- | --- | --- |
| M1 | `{{ md5(urlencode(db) }}` | `invalid_argument` | `md5` | original content |
| M2 | `{{ md5(urlencode(db))) }}` | `invalid_argument` | `urlencode` | original content |
| M3 | `{{ md5((urlencode(db))) }}` | `invalid_argument` | `md5` | original content |
| M4 | `{{ base64(md5(urlencode(db) }}` | `invalid_argument` | `base64` | original content |

Codes are **observed and locked** — the resolver surfaces malformed nesting as
`invalid_argument` with outer or inner `function_name` depending on where recursive
validation fails, not always `invalid_syntax`. Both `runtime` and `hover` render paths
return original content.

### Spacing variants (S1–S5)

Inner delimiter whitespace and argument spacing inside `{{ ... }}` are tolerated when the
grammar accepts the form. Space between function name and opening paren is rejected.

| ID | Example | Valid? | Validation code | `function_name` | Parity expectation |
| --- | --- | --- | --- | --- | --- |
| S1 | `{{  md5( db )  }}` | yes | valid | — | same hash as tight `{{md5(db)}}` |
| S2 | `{{  md5( urlencode( db ) )  }}` | yes | valid | — | same hash as tight nested form |
| S3 | `{{md5( urlencode(db))}}` | yes | valid | — | same hash as tight nested form |
| S4 | `{{ md5 ( urlencode ( db ) ) }}` | no | `invalid_syntax` | — | original content |
| S5 | `{{md5(urlencode (db))}}` | no | `invalid_argument` | `md5` | original content |

### Runtime / hover parity

Edge-case parity is proven at `TemplateService.render_string(..., render_path=...)`.
For each valid spaced row (S1–S3), `runtime` and `hover` produce identical resolved output.
For each malformed nested row (M1–M4) and invalid spacing row (S4–S5), both paths return
**original content** unchanged.

Table-cell tooltips delegate through `VariableAwareTableWidget` →
`VariableHoverHelper.resolve_text` → `TemplateService.render_string(...,
render_path="hover")`. No separate table parsing path; hover-parity at `TemplateService`
satisfies table-cell equivalence (PYPOST-453 precedent).

### Test coverage

**Resolver validation** (`tests/test_function_expression_resolver.py`):

- Catalog, nesting, multi-arg rejection, unknown functions
- `test_malformed_nested_expressions` — M1–M4 matrix
- `test_nested_spacing_variants` — S1–S5 matrix

**Render, parity, security, observability** (`tests/test_template_service.py`):

- Catalog functions, nested chains, fallback on invalid forms
- Jinja filter/attribute rejection (security negatives)
- `test_runtime_hover_parity_*` — valid/malformed/spacing parity (runtime vs hover)
- `test_validate_malformed_nested_alignment` — resolver ↔ delegate codes for M1–M4
- Metrics tests for `success`, `validation_error`, and hover-path labels

**HTTPClient integration** (`tests/test_http_client.py`, class
`TestHTTPClientFunctionExpressions`):

| Test | Surface | What it proves |
| --- | --- | --- |
| `test_function_expression_substituted_in_url` | URL | `urlencode` in outbound URL |
| `test_function_expression_substituted_in_header_value` | Header value | `md5` in header |
| `test_function_expression_substituted_in_param_key_and_value` | Param key + value | `urlencode` key, `base64` value |
| `test_invalid_function_expression_passthrough_in_params` | Param key + value | Invalid expressions kept literal |

**Optional HTTPClient gaps** (same pipeline, thinner end-to-end coverage):

- Request body function expression through `HTTPClient.send_request`
- Header name (key column) function expression through HTTPClient

Body and header-name surfaces are covered at `TemplateService` and hover/widget layers.

**Hover widgets** (`tests/test_variable_hover.py`): URL, body, and table-cell tooltips.

Shared case data: `MALFORMED_NESTED_EXPRESSION_CASES` in
`tests/test_function_expression_resolver.py` (imported by `test_template_service.py`).

Full PYPOST-450 suite (STEP 6, 2026-06-06): 109 passed, 39 subtests across the files above.

### PYPOST-461 boundary

PYPOST-454 owns **nested-structure** malformation and **whitespace-heavy** variants plus
parity for those forms. Remaining out of scope (tracked in
[PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461)):

- Empty-argument calls (`{{md5()}}`)
- Multi-placeholder first-failure stability
- Standalone malformed closing-paren / arity patterns not primarily about nesting or spacing

## Configuration

There are no end-user settings or environment variables for this feature in current scope.

Developer-facing configuration points:

- The default function catalog lives in `FunctionRegistry` (`pypost/core/function_registry.py`).
  To add or rename functions, extend the registry module and keep resolver expectations and
  `TemplateService` wiring in sync.
- Runtime observability is active when `TemplateService` is constructed with
  `metrics=MetricsManager` (wired in `pypost/main.py`).
- Hover-path observability is active when `VariableHoverHelper.set_metrics(metrics)` is called
  (wired from `RequestWidget` initialization).

Observability behavior:

- Logs from `TemplateService`:
  - `INFO`: validation failures (`render_path`, `code`, `function_name`, `token_count`)
  - `DEBUG`: successful render (`render_path`, `token_count`)
  - `WARNING`: fallback to original content (`render_path`, `error_type`, `token_count`)
- Metrics (Prometheus):
  - `template_expression_render_attempts_total{render_path,outcome}`
    - outcomes: `success`, `validation_error`, `render_error`, `empty_content`
  - `template_expression_validation_failures_total{render_path,code,function_name}`
- `FunctionExpressionResolver` remains observability-free by design; it returns structured
  `ValidationResult` only.

## Rendering Orchestration Stages (PYPOST-459)

`TemplateService.render_string()` delegates each stage to a private helper method. The stages
execute in this order:

| # | Helper | Responsibility |
|---|--------|---------------|
| 1 | `_record_empty_render_attempt()` | Short-circuit on empty content; emit `empty_content` metric |
| 2 | `tokenize_template_expressions()` | Single scan: token list and `token_count` for logs |
| 3 | `_validate_template_expressions()` | Delegate to `FunctionExpressionResolver.validate_expressions` |
| 4 | `_emit_validation_failure_observability()` | Log + emit `validation_error` metric on invalid input |
| 5 | `_render_with_jinja()` | Execute Jinja2 rendering with provided variables |
| 6 | `_emit_render_success_observability()` | Log + emit `success` metric on successful render |
| 7 | `_fallback_content_after_render_exception()` | On exception: emit `render_error` (non-ValueError only); return original content |

The following are intentionally unchanged by PYPOST-459 (parity contract):

- Metric names, outcome strings, and label values
- Log message formats and fields
- Fallback semantics: `ValueError` (from validation) does not emit `render_error`; all other
  exceptions do
- Token counting regex pattern: `\{\{\s*(.*?)\s*\}\}`
- `FunctionExpressionResolver` contract

## Known gaps and follow-ups

PYPOST-450 is functionally complete. Remaining items are maintainability and optional
hardening — not release blockers.

| Item | Jira | Notes |
| --- | --- | --- |
| Expression/template caching | [PYPOST-455](https://pypost.atlassian.net/browse/PYPOST-455) | No cache today; revisit after usage metrics |
| Registry vs `env.globals` parity test | [PYPOST-457](https://pypost.atlassian.net/browse/PYPOST-457) | Explicit test not yet added |
| Shared tokenization dedup | — | Done in PYPOST-460 (`template_expression_tokenizer`) |
| Empty-arg / multi-placeholder / closing-paren edge cases | [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461) | Boundary with PYPOST-454 M1–M4 matrix |
| Hover regex vs resolver identifier rules | — | Hover `VARIABLE_PATTERN` vs resolver `_IDENTIFIER_RE` mismatch for digit-leading names |
| HTTPClient body / header-name integration | — | Optional; shared `render_string` path already proven |
| Table tooltip malformed/spacing variants | — | Hover pipeline proven at `TemplateService`; table tests cover valid function cells only |
| Class-level hover `TemplateService` | — | `VariableHoverHelper` uses class-level instance via `set_metrics()` |

Completed follow-ups referenced in this doc: PYPOST-451 (registry), PYPOST-452 (resolver),
PYPOST-453 (nested policy), PYPOST-454 (edge-case tests), PYPOST-456 (doc polish),
PYPOST-459 (orchestration stage helpers in `TemplateService`), PYPOST-460 (shared
tokenization).

## Troubleshooting

Expression does not render and stays unchanged:

- Check expression uses the canonical form: function name and argument inside `{{...}}`.
- Confirm function is allow-listed (`urlencode`, `md5`, `base64`) via `FunctionRegistry`.
- Confirm only one top-level argument is passed.
- Confirm argument is an identifier or a nested allow-listed function expression.

Hover tooltip differs from expectation:

- Ensure `RequestWidget` has called `VariableHoverHelper.set_metrics(...)` and variables are set.
- Plain hidden variables are masked; function-derived outputs are currently shown as resolved text.
- Digit-leading plain variables (for example `{{0db}}`) may resolve in hover via the fast
  lookup path but fail resolver validation at runtime — see Known gaps above.

Field unchanged after send but expression looks valid:

- Confirm the function name is in the catalog (`urlencode`, `md5`, `base64`).
- Check logs for `validation_error` with `code` and `function_name` labels.
- Multi-arg calls (`{{urlencode(a, b)}}`) and literal arguments (`{{urlencode('db')}}`)
  are rejected by design.

Need to inspect failures in detail:

- Check application logs for validation/fallback fields (`code`, `function_name`, `error_type`).
- Inspect Prometheus counters for `validation_error` and `render_error` outcomes.
- If behavior differs between runtime and hover, compare `render_path` labels in logs/metrics.
