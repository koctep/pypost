# Template Expression Functions (PYPOST-450, PYPOST-451, PYPOST-452)

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
  - Uses `FunctionRegistry` for allow-list checks and preserves current nested-call behavior.
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

### Known Deviation

- Current implementation allows nested function calls (for example `{{md5(urlencode(db))}}`).
- Architecture notes previously marked nested calls as out of scope for this iteration.
- Follow-up alignment task: [PYPOST-453](https://pypost.atlassian.net/browse/PYPOST-453).

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
- Nested function call (currently implemented): `{{md5(urlencode(db))}}`

Supported functions:

- `urlencode(var)` -> URL-encoded string
- `md5(var)` -> hex MD5 digest
- `base64(var)` -> Base64-encoded string

Examples:

- URL field: `/{{host}}/{{urlencode(db)}}`
- Header/param/body values: `{{md5(secret)}}`, `{{base64(path)}}`
- Hover tooltip resolution uses the same render rules as runtime for function placeholders.

Invalid examples (kept as original text due fallback behavior):

- Unknown function: `{{not_allowed(db)}}`
- Multi-argument call: `{{urlencode(db, host)}}`
- Literal argument: `{{urlencode('db')}}`
- Malformed signature: `{{urlencode(db}}`

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
