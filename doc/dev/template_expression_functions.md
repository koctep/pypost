# Template Expression Functions (PYPOST-450–PYPOST-453)

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

Edge-case tests (malformed nesting, spacing variants) are tracked in
[PYPOST-454](https://pypost.atlassian.net/browse/PYPOST-454).

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
| 2 | `_count_placeholder_expressions()` | Count `{{ ... }}` tokens for log context |
| 3 | `_validate_template_content()` | Delegate validation to `FunctionExpressionResolver` |
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

## Troubleshooting

Expression does not render and stays unchanged:

- Check expression uses the canonical form: function name and argument inside `{{...}}`.
- Confirm function is allow-listed (`urlencode`, `md5`, `base64`) via `FunctionRegistry`.
- Confirm only one top-level argument is passed.
- Confirm argument is an identifier or a nested allow-listed function expression.

Hover tooltip differs from expectation:

- Ensure `RequestWidget` has called `VariableHoverHelper.set_metrics(...)` and variables are set.
- Plain hidden variables are masked; function-derived outputs are currently shown as resolved text.

Need to inspect failures in detail:

- Check application logs for validation/fallback fields (`code`, `function_name`, `error_type`).
- Inspect Prometheus counters for `validation_error` and `render_error` outcomes.
- If behavior differs between runtime and hover, compare `render_path` labels in logs/metrics.
